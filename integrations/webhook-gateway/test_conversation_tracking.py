"""
End-to-End Test for Phase 3 Webhook Conversation Tracking
Tests all conversation tracking components in isolation and integration
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
import tempfile

# Add lambda directory to path
sys.path.append('./lambda')

try:
    from webhook_conversation_schema import (
        WebhookConversationUnit, 
        WebhookMetadata,
        create_webhook_conversation_id,
        create_webhook_session_id
    )
    from webhook_conversation_tracker import WebhookConversationTracker
    from webhook_cloudwatch_logger import WebhookCloudWatchLogger, WebhookEventType
    from webhook_s3_integration import WebhookS3Exporter
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to run this test from the webhook-gateway directory")
    sys.exit(1)

class TestWebhookConversationSchema(unittest.TestCase):
    """Test webhook conversation schema components"""
    
    def test_webhook_metadata_creation(self):
        """Test WebhookMetadata creation and serialization"""
        
        metadata = WebhookMetadata(
            source_system="test_system",
            source_process="test_process",
            webhook_type="deal_analysis",
            target_webhook_url="https://example.com/webhook",
            delivery_status="pending"
        )
        
        self.assertEqual(metadata.source_system, "test_system")
        self.assertEqual(metadata.webhook_type, "deal_analysis")
        self.assertEqual(metadata.delivery_status, "pending")
        self.assertEqual(metadata.delivery_attempts, 0)
        
        # Test serialization
        metadata_dict = metadata.to_dict()
        self.assertIsInstance(metadata_dict, dict)
        self.assertEqual(metadata_dict["source_system"], "test_system")
        self.assertEqual(metadata_dict["webhook_type"], "deal_analysis")
    
    def test_conversation_id_generation(self):
        """Test conversation ID generation"""
        
        conv_id = create_webhook_conversation_id("test-system", "test_process")
        
        # Should follow pattern: webhook_YYYYMMDD_HHMMSS_system_process_uuid
        self.assertTrue(conv_id.startswith("webhook_"))
        self.assertIn("testsystem", conv_id)  # Cleaned system name
        # Note: process name may be truncated to 10 chars, so check for partial match
        self.assertTrue("testproces" in conv_id or "testprocess" in conv_id)  # Cleaned process name (may be truncated)
        
        # Should be unique
        conv_id2 = create_webhook_conversation_id("test-system", "test_process")
        self.assertNotEqual(conv_id, conv_id2)
    
    def test_webhook_conversation_unit_creation(self):
        """Test WebhookConversationUnit creation and methods"""
        
        metadata = WebhookMetadata(
            source_system="test_system",
            source_process="test_process"
        )
        
        conversation = WebhookConversationUnit(
            conversation_id="test_conv_123",
            session_id="test_session_123",
            user_query="Test query about deals",
            webhook_metadata=metadata
        )
        
        self.assertEqual(conversation.conversation_id, "test_conv_123")
        self.assertEqual(conversation.channel, "webhook")
        self.assertEqual(conversation.user_id, "webhook_user")
        self.assertIsNotNone(conversation.webhook_metadata)
        
        # Test structured JSON conversion
        structured_json = conversation.to_webhook_structured_json()
        self.assertIn("metadata", structured_json)
        self.assertIn("webhook_context", structured_json)
        self.assertIn("conversation", structured_json)
        
        # Test compact logging format
        compact_log = conversation.to_compact_webhook_log()
        self.assertEqual(compact_log["event_type"], "WEBHOOK_CONVERSATION_COMPLETE")
        self.assertEqual(compact_log["channel"], "webhook")

class TestWebhookConversationTracker(unittest.TestCase):
    """Test webhook conversation tracker functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.tracker = WebhookConversationTracker(
            s3_bucket="test-bucket",
            enable_export=False  # Disable for unit tests
        )
    
    def test_start_conversation(self):
        """Test conversation initialization"""
        
        webhook_request = {
            "query": "What deals are closing this quarter?",
            "source_system": "test_crm",
            "source_process": "quarterly_review",
            "timestamp": "2025-08-13T10:30:00Z"
        }
        
        conversation_id = self.tracker.start_conversation(
            webhook_request=webhook_request,
            enhanced_query="Enhanced query with date context",
            temporal_context="Current date context"
        )
        
        self.assertIsNotNone(conversation_id)
        self.assertTrue(conversation_id.startswith("webhook_"))
        
        # Check conversation unit was created
        self.assertIsNotNone(self.tracker.conversation_unit)
        self.assertEqual(self.tracker.conversation_unit.conversation_id, conversation_id)
        self.assertEqual(self.tracker.conversation_unit.user_query, webhook_request["query"])
        self.assertEqual(self.tracker.conversation_unit.channel, "webhook")
        
        # Check webhook metadata
        metadata = self.tracker.conversation_unit.webhook_metadata
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.source_system, "test_crm")
        self.assertEqual(metadata.source_process, "quarterly_review")
    
    def test_track_manager_agent_response(self):
        """Test tracking manager agent response"""
        
        # Start conversation first
        webhook_request = {
            "query": "Test query",
            "source_system": "test",
            "source_process": "test",
            "timestamp": "2025-08-13T10:30:00Z"
        }
        self.tracker.start_conversation(webhook_request, "enhanced", "context")
        
        # Track manager agent response
        manager_response = {
            "success": True,
            "response": "This is the AI response about deals",
            "sessionId": "test_session_123"
        }
        
        self.tracker.track_manager_agent_response(
            manager_response=manager_response,
            processing_time_ms=2500,
            agents_used=["ManagerAgent", "DealAnalysisAgent"]
        )
        
        # Check tracking was applied
        conversation = self.tracker.conversation_unit
        self.assertEqual(conversation.final_response, manager_response["response"])
        self.assertTrue(conversation.success)
        self.assertEqual(conversation.processing_time_ms, 2500)
        self.assertEqual(conversation.agents_involved, ["ManagerAgent", "DealAnalysisAgent"])
        self.assertEqual(len(conversation.agent_flow), 1)
    
    def test_track_webhook_classification(self):
        """Test webhook classification tracking"""
        
        # Start conversation
        webhook_request = {"query": "test", "source_system": "test", "source_process": "test", "timestamp": "2025-08-13T10:30:00Z"}
        self.tracker.start_conversation(webhook_request, "enhanced", "context")
        
        # Track classification
        self.tracker.track_webhook_classification(
            webhook_type="deal_analysis",
            target_webhook_url="https://example.com/deals",
            confidence_score=0.92
        )
        
        # Check classification was tracked
        metadata = self.tracker.conversation_unit.webhook_metadata
        self.assertEqual(metadata.webhook_type, "deal_analysis")
        self.assertEqual(metadata.target_webhook_url, "https://example.com/deals")
    
    def test_track_outbound_delivery(self):
        """Test outbound delivery tracking"""
        
        # Start conversation
        webhook_request = {"query": "test", "source_system": "test", "source_process": "test", "timestamp": "2025-08-13T10:30:00Z"}
        self.tracker.start_conversation(webhook_request, "enhanced", "context")
        
        # Track delivery
        self.tracker.track_outbound_delivery(
            delivery_id="delivery_123",
            delivery_status="delivered",
            http_status_code=200,
            payload_size=1024
        )
        
        # Check delivery tracking
        metadata = self.tracker.conversation_unit.webhook_metadata
        self.assertEqual(metadata.delivery_id, "delivery_123")
        self.assertEqual(metadata.delivery_status, "delivered")
        self.assertEqual(metadata.http_status_code, 200)
        self.assertEqual(metadata.outbound_payload_size, 1024)
        self.assertEqual(metadata.delivery_attempts, 1)
    
    def test_complete_conversation(self):
        """Test conversation completion and export"""
        
        # Start and populate conversation
        webhook_request = {"query": "test", "source_system": "test", "source_process": "test", "timestamp": "2025-08-13T10:30:00Z"}
        self.tracker.start_conversation(webhook_request, "enhanced", "context")
        
        manager_response = {"success": True, "response": "Test response"}
        self.tracker.track_manager_agent_response(manager_response, 1500, ["ManagerAgent"])
        
        # Complete conversation
        conversation_data, s3_url = self.tracker.complete_conversation()
        
        # Check completion
        self.assertIsNotNone(conversation_data)
        self.assertIn("metadata", conversation_data)
        self.assertIn("webhook_context", conversation_data)
        self.assertIsNone(s3_url)  # Export disabled for test
        
        # Check end timestamp was set
        self.assertIsNotNone(self.tracker.conversation_unit.end_timestamp)

class TestWebhookCloudWatchLogger(unittest.TestCase):
    """Test CloudWatch logging functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.logger = WebhookCloudWatchLogger()
    
    @patch('webhook_cloudwatch_logger.boto3.client')
    def test_log_webhook_event(self, mock_boto_client):
        """Test basic webhook event logging"""
        
        self.logger.log_webhook_event(
            event_type=WebhookEventType.REQUEST_RECEIVED,
            conversation_id="test_conv_123",
            additional_data={"source_system": "test"},
            metrics={"processing_time": 1500}
        )
        
        # Should not raise any exceptions
        self.assertTrue(True)
    
    def test_convenience_logging_functions(self):
        """Test convenience logging functions"""
        
        # These should not raise exceptions
        self.logger.log_request_received(
            conversation_id="test_123",
            source_system="test_system",
            source_process="test_process",
            query_length=50,
            has_timestamp=True,
            request_size_bytes=200
        )
        
        self.logger.log_manager_agent_response(
            conversation_id="test_123",
            success=True,
            processing_time_ms=2000,
            response_length=500,
            agents_used=["ManagerAgent"]
        )
        
        self.logger.log_response_classification(
            conversation_id="test_123",
            webhook_type="deal_analysis",
            target_webhook_url="https://example.com/webhook"
        )
        
        # Should complete without errors
        self.assertTrue(True)

class TestWebhookS3Integration(unittest.TestCase):
    """Test S3 export integration"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock S3 exporter
        with patch('boto3.client'):
            self.exporter = WebhookS3Exporter(
                s3_bucket="test-bucket",
                s3_prefix="test-conversations/"
            )
    
    def test_s3_path_generation(self):
        """Test S3 path generation"""
        
        conversation = WebhookConversationUnit(
            conversation_id="webhook_20250813_103045_testsystem_testprocess_abc123",
            session_id="test_session",
            start_timestamp="2025-08-13T10:30:45.123456+00:00"
        )
        
        path = self.exporter._get_webhook_s3_path(conversation)
        
        # Should follow pattern: test-conversations/2025/08/13/webhook_timestamp_id/
        self.assertTrue(path.startswith("test-conversations/2025/08/13/"))
        self.assertTrue(path.endswith("/"))
        self.assertIn("webhook_", path)
    
    def test_export_formats(self):
        """Test different export formats"""
        
        metadata = WebhookMetadata(
            source_system="test_system",
            source_process="test_process",
            webhook_type="deal_analysis",
            delivery_status="delivered"
        )
        
        conversation = WebhookConversationUnit(
            conversation_id="test_conv_123",
            session_id="test_session",
            user_query="Test query about deals",
            final_response="Test response about deals",
            webhook_metadata=metadata,
            start_timestamp="2025-08-13T10:30:45.123456+00:00",
            end_timestamp="2025-08-13T10:30:47.123456+00:00"
        )
        
        # Test webhook structured JSON format
        json_content = self.exporter._to_webhook_structured_json(conversation)
        parsed = json.loads(json_content)
        
        self.assertIn("export_metadata", parsed)
        self.assertIn("conversation", parsed)
        self.assertEqual(parsed["export_metadata"]["format"], "webhook_structured_json")
        
        # Test metadata only format
        metadata_content = self.exporter._to_metadata_only(conversation)
        parsed_metadata = json.loads(metadata_content)
        
        self.assertIn("conversation_metadata", parsed_metadata)
        self.assertIn("webhook_metadata", parsed_metadata)
        
        # Test compact summary
        summary_content = self.exporter._to_compact_summary(conversation)
        parsed_summary = json.loads(summary_content)
        
        self.assertIn("id", parsed_summary)
        self.assertIn("webhook_type", parsed_summary)
        self.assertEqual(parsed_summary["webhook_type"], "deal_analysis")

class TestEndToEndIntegration(unittest.TestCase):
    """Test complete end-to-end conversation tracking flow"""
    
    def test_complete_workflow(self):
        """Test the complete conversation tracking workflow"""
        
        # 1. Initialize tracker
        tracker = WebhookConversationTracker(enable_export=False)
        logger = WebhookCloudWatchLogger()
        
        # 2. Start conversation
        webhook_request = {
            "query": "What are the top 5 deals closing this quarter?",
            "source_system": "salesforce_integration", 
            "source_process": "quarterly_pipeline_review",
            "timestamp": "2025-08-13T10:30:00Z"
        }
        
        conversation_id = tracker.start_conversation(
            webhook_request=webhook_request,
            enhanced_query=f"DATE CONTEXT: Today is August 13, 2025\n\n{webhook_request['query']}",
            temporal_context="Q3 2025, August"
        )
        
        # Log request received
        logger.log_request_received(
            conversation_id=conversation_id,
            source_system=webhook_request["source_system"],
            source_process=webhook_request["source_process"],
            query_length=len(webhook_request["query"]),
            has_timestamp=True,
            request_size_bytes=len(json.dumps(webhook_request))
        )
        
        # 3. Simulate manager agent processing
        manager_response = {
            "success": True,
            "response": "Here are the top 5 deals closing this quarter: 1) ACME Corp - $150k, 2) TechStart Inc - $95k, 3) Global Solutions - $200k, 4) Innovation Labs - $75k, 5) Future Systems - $120k",
            "sessionId": "webhook_session_20250813_103000"
        }
        
        tracker.track_manager_agent_response(
            manager_response=manager_response,
            processing_time_ms=3500,
            agents_used=["ManagerAgent", "DealAnalysisAgent", "DataAgent"]
        )
        
        logger.log_manager_agent_response(
            conversation_id=conversation_id,
            success=True,
            processing_time_ms=3500,
            response_length=len(manager_response["response"]),
            agents_used=["ManagerAgent", "DealAnalysisAgent", "DataAgent"]
        )
        
        # 4. Simulate response classification
        webhook_type = "deal_analysis"  # Would be classified based on content
        target_url = "https://salesforce-integration.company.com/webhook/deal-analysis"
        
        tracker.track_webhook_classification(
            webhook_type=webhook_type,
            target_webhook_url=target_url,
            confidence_score=0.94
        )
        
        logger.log_response_classification(
            conversation_id=conversation_id,
            webhook_type=webhook_type,
            target_webhook_url=target_url,
            classification_confidence=0.94
        )
        
        # 5. Simulate outbound delivery
        delivery_id = "delivery_20250813_103005_abc123"
        
        # Queue for delivery
        logger.log_outbound_queued(
            conversation_id=conversation_id,
            delivery_id=delivery_id,
            webhook_type=webhook_type,
            target_url=target_url,
            payload_size=len(json.dumps(manager_response))
        )
        
        # Simulate successful delivery
        tracker.track_outbound_delivery(
            delivery_id=delivery_id,
            delivery_status="delivered",
            http_status_code=200,
            payload_size=len(json.dumps(manager_response))
        )
        
        logger.log_delivery_attempt(
            conversation_id=conversation_id,
            delivery_id=delivery_id,
            attempt_number=1,
            target_url=target_url,
            http_status=200,
            success=True,
            response_time_ms=450
        )
        
        # 6. Complete conversation
        conversation_data, s3_url = tracker.complete_conversation()
        
        logger.log_conversation_completed(
            conversation_id=conversation_id,
            total_time_ms=4500,
            success=True,
            webhook_metadata=conversation_data.get("webhook_context", {}),
            agents_involved=["ManagerAgent", "DealAnalysisAgent", "DataAgent"],
            final_response_length=len(manager_response["response"])
        )
        
        # 7. Validate final state
        self.assertIsNotNone(conversation_data)
        self.assertIn("metadata", conversation_data)
        self.assertIn("webhook_context", conversation_data)
        
        # Check webhook context
        webhook_context = conversation_data["webhook_context"]
        self.assertEqual(webhook_context["source_system"], "salesforce_integration")
        self.assertEqual(webhook_context["webhook_type"], "deal_analysis")
        self.assertEqual(webhook_context["delivery_status"], "delivered")
        self.assertEqual(webhook_context["delivery_attempts"], 1)
        
        # Check conversation metadata
        metadata = conversation_data["metadata"]
        self.assertEqual(metadata["conversation_id"], conversation_id)
        self.assertTrue(metadata["performance"]["success"])
        self.assertEqual(metadata["agents_count"], 3)
        
        print(f"✅ End-to-end test completed successfully!")
        print(f"📋 Conversation ID: {conversation_id}")
        print(f"📊 Webhook Type: {webhook_type}")
        print(f"🚀 Delivery Status: delivered")
        print(f"⏱️  Total Processing: 4.5 seconds")

def run_comprehensive_tests():
    """Run all Phase 3 conversation tracking tests"""
    
    test_classes = [
        TestWebhookConversationSchema,
        TestWebhookConversationTracker,
        TestWebhookCloudWatchLogger,
        TestWebhookS3Integration,
        TestEndToEndIntegration
    ]
    
    total_tests = 0
    total_failures = 0
    
    print("🧪 Starting Phase 3 Webhook Conversation Tracking Tests\n")
    
    for test_class in test_classes:
        print(f"Running {test_class.__name__}...")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures) + len(result.errors)
        
        if result.failures or result.errors:
            print(f"❌ {test_class.__name__}: {len(result.failures + result.errors)} failures")
            for failure in result.failures + result.errors:
                print(f"   - {failure[0]}: {failure[1].split('AssertionError:')[-1].strip() if 'AssertionError:' in failure[1] else failure[1]}")
        else:
            print(f"✅ {test_class.__name__}: All tests passed")
        
        print()
    
    print(f"📊 Test Summary:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {total_tests - total_failures}")
    print(f"   Failed: {total_failures}")
    
    if total_failures == 0:
        print("\n🎉 All Phase 3 conversation tracking tests passed!")
        return True
    else:
        print(f"\n⚠️  {total_failures} test(s) failed. Please review the failures above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)