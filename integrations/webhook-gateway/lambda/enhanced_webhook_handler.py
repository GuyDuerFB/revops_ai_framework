"""
Enhanced Webhook Handler with Phase 3 Conversation Tracking
Integrates all Phase 3 monitoring features into the webhook gateway
"""

import json
import os
import boto3
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Phase 3 imports
from webhook_conversation_tracker import WebhookConversationTracker
from webhook_cloudwatch_logger import webhook_logger, WebhookEventType
from webhook_s3_integration import get_s3_export_config

# Phase 2 imports (existing functionality)
import sys
sys.path.append('.')
from lambda_simple_processor import (
    transform_to_manager_format,
    invoke_manager_agent,
    classify_response_type,
    get_target_webhook_url,
    queue_outbound_delivery
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Environment variables
MANAGER_AGENT_FUNCTION_NAME = os.environ.get('MANAGER_AGENT_FUNCTION_NAME', 'revops-manager-agent-wrapper')
CONVERSATION_EXPORT_ENABLED = os.environ.get('ENABLE_CONVERSATION_EXPORT', 'true').lower() == 'true'

class EnhancedWebhookGateway:
    """Enhanced webhook gateway with Phase 3 conversation tracking"""
    
    def __init__(self):
        # Initialize conversation tracking
        s3_bucket, export_enabled = get_s3_export_config()
        self.conversation_tracker = WebhookConversationTracker(
            s3_bucket=s3_bucket,
            enable_export=export_enabled and CONVERSATION_EXPORT_ENABLED
        )
        
        # AWS clients
        self.lambda_client = boto3.client('lambda')
        
        # Performance tracking
        self.start_time = None
    
    def process_webhook_request(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Process webhook request with full Phase 3 conversation tracking
        
        Args:
            event: AWS Lambda event
            context: AWS Lambda context
            
        Returns:
            Response dictionary with tracking ID and processing status
        """
        
        self.start_time = time.time()
        conversation_id = None
        
        try:
            # 1. Extract and validate webhook request
            webhook_request = self._extract_webhook_request(event)
            
            # 2. Start conversation tracking (Phase 3)
            conversation_id = self.conversation_tracker.start_conversation(
                webhook_request=webhook_request,
                enhanced_query=webhook_request["query"],
                temporal_context=self._get_current_date_context()
            )
            
            # Log request received
            webhook_logger.log_request_received(
                conversation_id=conversation_id,
                source_system=webhook_request.get("source_system", "unknown"),
                source_process=webhook_request.get("source_process", "unknown"),
                query_length=len(webhook_request.get("query", "")),
                has_timestamp=bool(webhook_request.get("timestamp")),
                request_size_bytes=len(json.dumps(webhook_request))
            )
            
            # 3. Transform request for manager agent
            manager_request = transform_to_manager_format(webhook_request)
            
            webhook_logger.log_manager_agent_invocation(
                conversation_id=conversation_id,
                agent_function_name=MANAGER_AGENT_FUNCTION_NAME,
                enhanced_query_length=len(manager_request.get("query", "")),
                has_date_context=True
            )
            
            # 4. Invoke manager agent
            start_agent_time = time.time()
            manager_response = invoke_manager_agent(manager_request)
            agent_processing_time = int((time.time() - start_agent_time) * 1000)
            
            # Track manager agent response
            self.conversation_tracker.track_manager_agent_response(
                manager_response=manager_response,
                processing_time_ms=agent_processing_time,
                agents_used=["ManagerAgent"]  # Could be extracted from response
            )
            
            webhook_logger.log_manager_agent_response(
                conversation_id=conversation_id,
                success=manager_response.get("success", False),
                processing_time_ms=agent_processing_time,
                response_length=len(manager_response.get("response", "")),
                agents_used=["ManagerAgent"],
                session_id=manager_response.get("sessionId")
            )
            
            if not manager_response.get("success", False):
                raise Exception(f"Manager agent failed: {manager_response.get('error', 'Unknown error')}")
            
            # 5. Classify response type
            start_classification_time = time.time()
            webhook_type = classify_response_type(manager_response["response"], webhook_request["query"])
            target_webhook_url = get_target_webhook_url(webhook_type)
            classification_time = int((time.time() - start_classification_time) * 1000)
            
            # Track classification
            self.conversation_tracker.track_webhook_classification(
                webhook_type=webhook_type,
                target_webhook_url=target_webhook_url,
                confidence_score=0.85  # Placeholder - could be calculated
            )
            
            webhook_logger.log_response_classification(
                conversation_id=conversation_id,
                webhook_type=webhook_type,
                target_webhook_url=target_webhook_url,
                classification_confidence=0.85,
                classification_time_ms=classification_time
            )
            
            # 6. Queue outbound delivery
            delivery_id = str(uuid.uuid4())
            payload_size = len(json.dumps(manager_response))
            
            queue_start_time = time.time()
            queue_outbound_delivery(
                response_data=manager_response,
                webhook_type=webhook_type,
                target_webhook_url=target_webhook_url,
                conversation_id=conversation_id,
                delivery_id=delivery_id
            )
            queue_time = int((time.time() - queue_start_time) * 1000)
            
            # Track delivery queuing
            self.conversation_tracker.track_outbound_delivery(
                delivery_id=delivery_id,
                delivery_status="queued",
                payload_size=payload_size
            )
            
            webhook_logger.log_outbound_queued(
                conversation_id=conversation_id,
                delivery_id=delivery_id,
                webhook_type=webhook_type,
                target_url=target_webhook_url,
                payload_size=payload_size,
                queue_time_ms=queue_time
            )
            
            # 7. Complete conversation tracking
            total_processing_time = int((time.time() - self.start_time) * 1000)
            conversation_data, s3_url = self.conversation_tracker.complete_conversation()
            
            # Log conversation completion
            webhook_logger.log_conversation_completed(
                conversation_id=conversation_id,
                total_time_ms=total_processing_time,
                success=True,
                webhook_metadata=conversation_data.get("webhook_context", {}),
                agents_involved=["ManagerAgent"],
                final_response_length=len(manager_response.get("response", ""))
            )
            
            # Log S3 export if enabled
            if s3_url:
                webhook_logger.log_conversation_exported(
                    conversation_id=conversation_id,
                    s3_url=s3_url,
                    export_formats=["webhook_structured_json"],
                    export_size_bytes=len(json.dumps(conversation_data))
                )
            
            # 8. Return immediate response with tracking information
            return self._create_success_response(
                conversation_id=conversation_id,
                delivery_id=delivery_id,
                webhook_type=webhook_type,
                processing_time_ms=total_processing_time,
                manager_response=manager_response
            )
            
        except Exception as e:
            # Handle errors with tracking
            error_response = self._handle_error(e, conversation_id, event)
            return error_response
    
    def _extract_webhook_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate webhook request from Lambda event"""
        
        try:
            # Handle both direct invocation and API Gateway
            if 'body' in event:
                # API Gateway event
                body = event['body']
                if isinstance(body, str):
                    request_data = json.loads(body)
                else:
                    request_data = body
            else:
                # Direct Lambda invocation
                request_data = event
            
            # Validate required fields
            required_fields = ['query', 'source_system', 'source_process', 'timestamp']
            missing_fields = [field for field in required_fields if not request_data.get(field)]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Validate timestamp format
            timestamp = request_data.get('timestamp')
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                raise ValueError("Invalid timestamp format. Expected ISO format (YYYY-MM-DDTHH:MM:SSZ)")
            
            return request_data
            
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in request body")
        except Exception as e:
            raise ValueError(f"Request validation failed: {str(e)}")
    
    def _get_current_date_context(self) -> str:
        """Get current date context for agent processing"""
        now = datetime.now(timezone.utc)
        
        return f"""
📅 **CURRENT DATE AND TIME CONTEXT:**
- Current Date: {now.strftime('%A, %B %d, %Y')}
- Current Time: {now.strftime('%H:%M UTC')}
- Current Quarter: Q{((now.month - 1) // 3) + 1} {now.year}
- Current Month: {now.strftime('%B %Y')}
- Current Year: {now.year}

**IMPORTANT**: Use this current date information to interpret all time-based references in the user's request.

----

"""
    
    def _create_success_response(
        self,
        conversation_id: str,
        delivery_id: str,
        webhook_type: str,
        processing_time_ms: int,
        manager_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create successful response with tracking information"""
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "X-Conversation-ID": conversation_id,
                "X-Delivery-ID": delivery_id
            },
            "body": json.dumps({
                "success": True,
                "message": "Request processed successfully",
                "tracking": {
                    "conversation_id": conversation_id,
                    "delivery_id": delivery_id,
                    "webhook_type": webhook_type,
                    "processing_time_ms": processing_time_ms,
                    "queued_at": datetime.now(timezone.utc).isoformat(),
                    "estimated_delivery_time": "30-60 seconds"
                },
                "ai_response": {
                    "response": manager_response.get("response", ""),
                    "session_id": manager_response.get("sessionId"),
                    "agents_used": ["ManagerAgent"],
                    "classification": webhook_type
                },
                "delivery_status": {
                    "status": "queued",
                    "target_webhook_type": webhook_type,
                    "delivery_id": delivery_id
                }
            })
        }
    
    def _handle_error(
        self,
        error: Exception,
        conversation_id: Optional[str],
        event: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle errors with proper tracking and logging"""
        
        error_id = str(uuid.uuid4())
        
        # Log error details
        if conversation_id:
            webhook_logger.log_error(
                conversation_id=conversation_id,
                error_type=type(error).__name__,
                error_message=str(error),
                error_context={
                    "error_id": error_id,
                    "event_type": event.get("httpMethod", "unknown"),
                    "processing_time_ms": int((time.time() - self.start_time) * 1000) if self.start_time else 0
                }
            )
        else:
            logger.error(f"Webhook error without conversation ID: {error}", extra={
                "error_id": error_id,
                "error_type": type(error).__name__
            })
        
        # Complete conversation tracking with error
        if conversation_id and self.conversation_tracker.conversation_unit:
            self.conversation_tracker.conversation_unit.success = False
            self.conversation_tracker.conversation_unit.error_details = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "error_id": error_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.conversation_tracker.complete_conversation()
        
        # Return error response
        status_code = 400 if isinstance(error, ValueError) else 500
        
        return {
            "statusCode": status_code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "success": False,
                "error": str(error),
                "error_id": error_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        }

# Lambda handler function
def lambda_handler(event, context):
    """Enhanced Lambda handler with Phase 3 conversation tracking"""
    
    # Initialize enhanced gateway
    gateway = EnhancedWebhookGateway()
    
    # Health check endpoint
    if event.get('httpMethod') == 'GET' and event.get('path') == '/health':
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "3.0-with-conversation-tracking",
                "features": {
                    "conversation_tracking": True,
                    "s3_export": CONVERSATION_EXPORT_ENABLED,
                    "cloudwatch_logging": True,
                    "async_delivery": True
                }
            })
        }
    
    # Process webhook request
    return gateway.process_webhook_request(event, context)