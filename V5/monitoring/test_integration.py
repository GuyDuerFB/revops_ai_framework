#!/usr/bin/env python3
"""
Integration test suite for RevOps AI Framework V5 monitoring components
Consolidates conversation tracking and full integration functionality tests
"""
import sys
import os
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import time

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from conversation_schema import ConversationUnit, AgentFlowStep, BedrockTraceContent, ToolExecution, DataOperation
    from conversation_tracker import ConversationTracker
except ImportError as e:
    print(f"Warning: Could not import integration modules: {e}")
    ConversationTracker = None

class TestConversationTracking(unittest.TestCase):
    """Test conversation tracking functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if ConversationTracker is None:
            self.skipTest("Conversation tracking modules not available")
        
        self.tracker = ConversationTracker()
        
    def test_conversation_unit_creation(self):
        """Test creation of conversation units"""
        conversation_id = "test-123"
        user_id = "U123456"
        channel = "C789012"
        user_query = "Test query for conversation tracking"
        
        conversation = self.tracker.start_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            channel=channel,
            user_query=user_query
        )
        
        self.assertIsInstance(conversation, ConversationUnit)
        self.assertEqual(conversation.conversation_id, conversation_id)
        self.assertEqual(conversation.user_id, user_id)
        self.assertEqual(conversation.channel, channel)
        self.assertEqual(conversation.user_query, user_query)
        
    def test_agent_flow_tracking(self):
        """Test tracking of agent flow steps"""
        conversation = self.tracker.start_conversation(
            conversation_id="test-flow-123",
            user_id="U123456",
            channel="C789012",
            user_query="Test agent flow tracking"
        )
        
        # Add an agent step
        trace_content = BedrockTraceContent(
            modelInvocationInput='{"system": "test prompt", "messages": []}',
            observation="Test observation"
        )
        
        agent_step = AgentFlowStep(
            agent_name="TestAgent",
            agent_id="TEST123",
            start_time=datetime.now(timezone.utc).isoformat(),
            end_time=datetime.now(timezone.utc).isoformat(),
            reasoning_text="Test reasoning",
            bedrock_trace_content=trace_content,
            tools_used=[],
            data_operations=[]
        )
        
        conversation.add_agent_step(agent_step)
        
        self.assertEqual(len(conversation.agent_flow), 1)
        self.assertIn("TestAgent", conversation.agents_involved)
        
    def test_function_audit_tracking(self):
        """Test function call audit tracking"""
        conversation = self.tracker.start_conversation(
            conversation_id="test-audit-123",
            user_id="U123456",
            channel="C789012",
            user_query="Test function audit"
        )
        
        # Track function calls
        conversation.track_function_call("test_function", {})
        conversation.track_function_call("another_function", {"param": "value"})
        
        self.assertEqual(conversation.function_audit["total_functions_called"], 2)
        self.assertIn("test_function", conversation.function_audit)
        self.assertIn("another_function", conversation.function_audit)

class TestFullIntegration(unittest.TestCase):
    """Test full integration functionality"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        if ConversationTracker is None:
            self.skipTest("Integration modules not available")
        
        self.tracker = ConversationTracker()
        
    def test_end_to_end_conversation_flow(self):
        """Test complete conversation flow from start to finish"""
        # Start conversation
        conversation = self.tracker.start_conversation(
            conversation_id="integration-test-123",
            user_id="U123456",
            channel="C789012",
            user_query="Comprehensive integration test query"
        )
        
        # Add multiple agent steps to simulate complex flow
        for i in range(3):
            trace_content = BedrockTraceContent(
                modelInvocationInput=f'{{"system": "agent {i} prompt", "messages": []}}',
                observation=f"Agent {i} observation"
            )
            
            tool_execution = ToolExecution(
                tool_name=f"tool_{i}",
                parameters={"step": i},
                execution_time_ms=100 + i * 50,
                result_summary=f"Tool {i} result",
                full_result=f"Full result for tool {i}",
                success=True
            )
            
            data_operation = DataOperation(
                operation="SQL_QUERY",
                target=f"table_{i}",
                query=f"SELECT * FROM table_{i}",
                result_count=10 + i,
                execution_time_ms=150 + i * 25,
                full_response=f"Query result for table_{i}"
            )
            
            agent_step = AgentFlowStep(
                agent_name=f"Agent{i}",
                agent_id=f"AGENT{i:03d}",
                start_time=datetime.now(timezone.utc).isoformat(),
                end_time=datetime.now(timezone.utc).isoformat(),
                reasoning_text=f"Step {i} reasoning and decision making",
                bedrock_trace_content=trace_content,
                tools_used=[tool_execution],
                data_operations=[data_operation]
            )
            
            conversation.add_agent_step(agent_step)
            conversation.track_function_call(f"function_{i}", {"step": i})
        
        # Complete conversation
        conversation.complete_conversation(
            final_response="Integration test completed successfully",
            success=True
        )
        
        # Verify conversation state
        self.assertEqual(len(conversation.agent_flow), 3)
        self.assertEqual(len(conversation.agents_involved), 3)
        self.assertEqual(conversation.function_audit["total_functions_called"], 3)
        self.assertTrue(conversation.success)
        self.assertIsNotNone(conversation.final_response)
        self.assertIsNotNone(conversation.end_timestamp)
        
    def test_error_handling_integration(self):
        """Test error handling in integration scenarios"""
        conversation = self.tracker.start_conversation(
            conversation_id="error-test-123",
            user_id="U123456",
            channel="C789012",
            user_query="Error handling test"
        )
        
        # Add a failed agent step
        trace_content = BedrockTraceContent(
            modelInvocationInput='{"system": "error test prompt", "messages": []}',
            observation="Error occurred during processing"
        )
        
        failed_tool = ToolExecution(
            tool_name="failing_tool",
            parameters={"test": "error"},
            execution_time_ms=50,
            result_summary="Tool execution failed",
            full_result="Error: Tool failed to execute",
            success=False
        )
        
        agent_step = AgentFlowStep(
            agent_name="ErrorAgent",
            agent_id="ERROR001",
            start_time=datetime.now(timezone.utc).isoformat(),
            end_time=datetime.now(timezone.utc).isoformat(),
            reasoning_text="Attempted to process request but encountered error",
            bedrock_trace_content=trace_content,
            tools_used=[failed_tool],
            data_operations=[]
        )
        
        conversation.add_agent_step(agent_step)
        
        # Complete with failure
        conversation.complete_conversation(
            final_response="Unable to complete request due to errors",
            success=False
        )
        
        # Verify error state
        self.assertFalse(conversation.success)
        self.assertIn("Unable to complete", conversation.final_response)

def run_tests():
    """Run all integration tests"""
    print("Running integration monitoring tests...")
    
    # Create test loader
    loader = unittest.TestLoader()
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConversationTracking))
    suite.addTests(loader.loadTestsFromTestCase(TestFullIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)