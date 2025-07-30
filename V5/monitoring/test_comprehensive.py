#!/usr/bin/env python3
"""
Comprehensive test suite for RevOps AI Framework V5 monitoring components
Consolidates prompt deduplication and S3 export functionality tests
"""
import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from moto import mock_aws
import boto3

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from prompt_deduplicator import PromptDeduplicator, PromptReference
    from conversation_exporter import ConversationExporter
    from conversation_schema import ConversationUnit, AgentFlowStep, BedrockTraceContent, ToolExecution, DataOperation
except ImportError as e:
    print(f"Warning: Could not import monitoring modules: {e}")
    PromptDeduplicator = None
    ConversationExporter = None

class TestPromptDeduplication(unittest.TestCase):
    """Test prompt deduplication functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if PromptDeduplicator is None:
            self.skipTest("Prompt deduplication modules not available")
        
        self.deduplicator = PromptDeduplicator()
        self.sample_system_prompt = '''# Manager Agent Instructions - RevOps AI Framework V4

## Agent Purpose
You are the **Manager Agent** and **SUPERVISOR** for Firebolt's RevOps AI Framework V4. You serve as the intelligent router and coordinator, determining the best approach for each user request and orchestrating specialized agents to deliver comprehensive revenue operations analysis.

## Your Role as SUPERVISOR & Router

You are the primary entry point for all user requests. Your responsibilities include:

1. **Intent Recognition**: Analyze user queries to determine the appropriate workflow
2. **Agent Routing**: Route specialized requests to dedicated agents for optimal results
3. **General Processing**: Handle non-specialized requests using your full capabilities
4. **Response Coordination**: Ensure consistent formatting and quality across all responses
5. **Context Management**: Maintain conversation context and follow-up handling'''
        
    def test_prompt_extraction(self):
        """Test system prompt extraction from modelInvocationInput"""
        model_input = json.dumps({
            "system": self.sample_system_prompt,
            "messages": [{"role": "user", "content": "test message"}],
            "temperature": 0.7
        })
        
        extracted = self.deduplicator._extract_system_prompt(model_input)
        self.assertIsNotNone(extracted)
        
        system_prompt, remaining_input = extracted
        self.assertEqual(system_prompt, self.sample_system_prompt)
        
        # Verify remaining input doesn't contain system prompt
        remaining_data = json.loads(remaining_input)
        self.assertNotIn('system', remaining_data)
        self.assertIn('system_prompt_ref', remaining_data)
        self.assertEqual(remaining_data['system_prompt_ref'], "PLACEHOLDER")
        
    def test_prompt_caching(self):
        """Test prompt caching and ID generation"""
        prompt_id = self.deduplicator._cache_prompt(self.sample_system_prompt)
        
        # Verify prompt ID format
        self.assertTrue(prompt_id.startswith('prompt_'))
        self.assertEqual(len(prompt_id), 15)  # "prompt_" + 8 char hash
        
        # Verify prompt is cached
        self.assertIn(prompt_id, self.deduplicator.prompt_cache)
        self.assertIn(prompt_id, self.deduplicator.prompt_store)
        
        # Verify cached prompt data
        cached_ref = self.deduplicator.prompt_cache[prompt_id]
        self.assertEqual(cached_ref.prompt_id, prompt_id)
        self.assertEqual(cached_ref.usage_count, 1)
        self.assertEqual(cached_ref.prompt_length, len(self.sample_system_prompt))
        
        # Verify stored prompt
        stored_prompt = self.deduplicator.prompt_store[prompt_id]
        self.assertEqual(stored_prompt, self.sample_system_prompt)
        
    def test_duplicate_prompt_detection(self):
        """Test that identical prompts get same ID"""
        # Cache the same prompt twice
        prompt_id_1 = self.deduplicator._cache_prompt(self.sample_system_prompt)
        prompt_id_2 = self.deduplicator._cache_prompt(self.sample_system_prompt)
        
        # Should return the same ID
        self.assertEqual(prompt_id_1, prompt_id_2)
        
        # Usage count should be incremented
        cached_ref = self.deduplicator.prompt_cache[prompt_id_1]
        self.assertEqual(cached_ref.usage_count, 2)
        
        # Should only have one entry in cache
        self.assertEqual(len(self.deduplicator.prompt_cache), 1)

class TestS3Export(unittest.TestCase):
    """Test S3 conversation export functionality"""
    
    def setUp(self):
        """Set up test fixtures with mocked S3"""
        if ConversationExporter is None:
            self.skipTest("S3 export modules not available")
        
        self.bucket_name = 'test-conversations-bucket'
        
        # Create sample conversation for testing
        self.sample_conversation = self._create_sample_conversation()
        
    def _create_sample_conversation(self):
        """Create a sample conversation for testing"""
        
        # Create trace content
        trace_content = BedrockTraceContent(
            modelInvocationInput='{"system": "test prompt", "messages": []}',
            observation="Test observation result"
        )
        
        # Create tools and data operations
        tool_execution = ToolExecution(
            tool_name="test_tool",
            parameters={"param1": "value1"},
            execution_time_ms=150,
            result_summary="Tool executed successfully",
            full_result="Full tool result",
            success=True
        )
        
        data_operation = DataOperation(
            operation="SQL_QUERY",
            target="test_table",
            query="SELECT * FROM test_table WHERE condition = 'test'",
            result_count=5,
            execution_time_ms=200,
            full_response="Full query response"
        )
        
        # Create agent step
        agent_step = AgentFlowStep(
            agent_name="TestAgent",
            agent_id="TEST123",
            start_time=datetime.now(timezone.utc).isoformat(),
            end_time=datetime.now(timezone.utc).isoformat(),
            reasoning_text="This is the agent reasoning text",
            bedrock_trace_content=trace_content,
            tools_used=[tool_execution],
            data_operations=[data_operation]
        )
        
        # Create conversation unit
        conversation = ConversationUnit(
            conversation_id="test-export-123",
            session_id="session-456",
            user_id="U123456",
            channel="C789012",
            start_timestamp="2025-07-29T12:00:00+00:00",
            end_timestamp="2025-07-29T12:05:00+00:00",
            user_query="Test export query for S3 functionality",
            temporal_context="Test context",
            agents_involved=["TestAgent"],
            agent_flow=[agent_step],
            final_response="Test response for export functionality",
            collaboration_map={"TestAgent": {"status": "completed"}},
            function_audit={"total_functions_called": 1},
            success=True,
            processing_time_ms=5000
        )
        
        return conversation
    
    @mock_aws
    def test_structured_json_export(self):
        """Test structured JSON export format"""
        
        # Set up S3 mock
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket=self.bucket_name)
        exporter = ConversationExporter(self.bucket_name)
        
        # Export in structured JSON format
        exported_urls = exporter.export_conversation(self.sample_conversation, ['structured_json'])
        
        # Verify export result
        self.assertIn('structured_json', exported_urls)
        self.assertTrue(exported_urls['structured_json'].startswith('s3://'))
        
        # Verify file was created in S3
        expected_key = "conversations/2025-07-29/test-export-123/conversation.json"
        
        response = s3_client.get_object(Bucket=self.bucket_name, Key=expected_key)
        content = response['Body'].read().decode('utf-8')
        
        # Verify JSON structure
        data = json.loads(content)
        self.assertIn('export_metadata', data)
        self.assertIn('conversation', data)
        self.assertEqual(data['export_metadata']['format'], 'structured_json')
        
    @mock_aws
    def test_multiple_format_export(self):
        """Test exporting multiple formats simultaneously"""
        
        # Set up S3 mock
        s3_client = boto3.client('s3', region_name='us-east-1')
        s3_client.create_bucket(Bucket=self.bucket_name)
        exporter = ConversationExporter(self.bucket_name)
        
        # Export multiple formats
        formats = ['structured_json', 'llm_readable', 'metadata_only']
        exported_urls = exporter.export_conversation(self.sample_conversation, formats)
        
        # Verify all formats were exported
        for format_name in formats:
            self.assertIn(format_name, exported_urls)
            self.assertTrue(exported_urls[format_name].startswith('s3://'))

def run_tests():
    """Run all comprehensive tests"""
    print("Running comprehensive monitoring tests...")
    
    # Create test loader
    loader = unittest.TestLoader()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPromptDeduplication))
    suite.addTests(loader.loadTestsFromTestCase(TestS3Export))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)