"""
Webhook Conversation Tracker
Tracks webhook conversations and integrates with existing S3 export pipeline
"""

import json
import logging
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from webhook_conversation_schema import (
    WebhookConversationUnit, 
    WebhookMetadata,
    create_webhook_conversation_id,
    create_webhook_session_id
)

# Set up logging
logger = logging.getLogger(__name__)

class WebhookConversationTracker:
    """Tracks webhook conversations from start to completion"""
    
    def __init__(self, s3_bucket: Optional[str] = None, enable_export: bool = True):
        self.conversation_unit: Optional[WebhookConversationUnit] = None
        self.s3_bucket = s3_bucket
        self.enable_export = enable_export
        self.cloudwatch_logger = logging.getLogger('webhook_conversations')
        
        # Initialize S3 client if export is enabled
        if self.enable_export and self.s3_bucket:
            self.s3_client = boto3.client('s3')
        else:
            self.s3_client = None
    
    def start_conversation(
        self, 
        webhook_request: Dict[str, Any], 
        enhanced_query: str,
        temporal_context: str = ""
    ) -> str:
        """
        Initialize webhook conversation tracking
        
        Args:
            webhook_request: Original webhook request data
            enhanced_query: Query with date context added
            temporal_context: Current date/time context
            
        Returns:
            conversation_id: Generated conversation ID for tracking
        """
        
        # Generate IDs
        conversation_id = create_webhook_conversation_id(
            webhook_request.get("source_system", "unknown"),
            webhook_request.get("source_process", "unknown")
        )
        session_id = create_webhook_session_id(conversation_id)
        
        # Create webhook metadata
        webhook_metadata = WebhookMetadata(
            source_system=webhook_request.get("source_system", "unknown"),
            source_process=webhook_request.get("source_process", "unknown"),
            delivery_status="pending"
        )
        
        # Initialize conversation unit
        self.conversation_unit = WebhookConversationUnit(
            conversation_id=conversation_id,
            session_id=session_id,
            user_id="webhook_user",
            channel="webhook",
            start_timestamp=datetime.now(timezone.utc).isoformat(),
            user_query=webhook_request.get("query", ""),
            temporal_context=temporal_context,
            webhook_metadata=webhook_metadata
        )
        
        # Log conversation start
        logger.info("WEBHOOK_CONVERSATION_STARTED", extra={
            "conversation_id": conversation_id,
            "source_system": webhook_request.get("source_system"),
            "source_process": webhook_request.get("source_process"),
            "query_length": len(webhook_request.get("query", "")),
            "has_temporal_context": bool(temporal_context)
        })
        
        return conversation_id
    
    def track_manager_agent_response(
        self, 
        manager_response: Dict[str, Any],
        processing_time_ms: int,
        agents_used: List[str] = None
    ) -> None:
        """
        Track the manager agent response and processing details
        
        Args:
            manager_response: Response from manager agent
            processing_time_ms: Time taken for processing
            agents_used: List of agents involved in processing
        """
        
        if not self.conversation_unit:
            logger.error("Cannot track manager agent response - conversation not started")
            return
        
        # Update conversation with response
        self.conversation_unit.final_response = manager_response.get("response", "")
        self.conversation_unit.success = manager_response.get("success", False)
        self.conversation_unit.processing_time_ms = processing_time_ms
        
        # Track agents involved
        if agents_used:
            self.conversation_unit.agents_involved = agents_used
        
        # Add agent flow step (simplified for webhook - we don't have detailed trace data)
        if manager_response.get("success"):
            from webhook_conversation_schema import AgentFlowStep, BedrockTraceContent
            
            agent_step = AgentFlowStep(
                agent_name="ManagerAgent",
                agent_id=manager_response.get("sessionId", "unknown"),
                start_time=self.conversation_unit.start_timestamp,
                end_time=datetime.now(timezone.utc).isoformat(),
                reasoning_text="Manager agent processed webhook request successfully",
                bedrock_trace_content=BedrockTraceContent(),
                tools_used=[],
                data_operations=[]
            )
            self.conversation_unit.agent_flow.append(agent_step)
        
        # Log processing completion
        logger.info("WEBHOOK_MANAGER_AGENT_PROCESSED", extra={
            "conversation_id": self.conversation_unit.conversation_id,
            "success": manager_response.get("success", False),
            "processing_time_ms": processing_time_ms,
            "response_length": len(manager_response.get("response", "")),
            "agents_used": agents_used or []
        })
    
    def track_webhook_classification(
        self, 
        webhook_type: str, 
        target_webhook_url: str,
        confidence_score: float = None
    ) -> None:
        """
        Track webhook response classification
        
        Args:
            webhook_type: Classified type (deal_analysis, data_analysis, etc.)
            target_webhook_url: Target webhook URL for delivery
            confidence_score: Classification confidence (optional)
        """
        
        if not self.conversation_unit or not self.conversation_unit.webhook_metadata:
            logger.error("Cannot track classification - conversation not initialized")
            return
        
        # Update webhook metadata
        self.conversation_unit.webhook_metadata.webhook_type = webhook_type
        self.conversation_unit.webhook_metadata.target_webhook_url = target_webhook_url
        
        # Log classification
        logger.info("WEBHOOK_RESPONSE_CLASSIFIED", extra={
            "conversation_id": self.conversation_unit.conversation_id,
            "webhook_type": webhook_type,
            "target_webhook_url": target_webhook_url,
            "confidence_score": confidence_score
        })
    
    def track_outbound_delivery(
        self, 
        delivery_id: str, 
        delivery_status: str,
        http_status_code: Optional[int] = None,
        error_details: Optional[Dict[str, Any]] = None,
        payload_size: Optional[int] = None
    ) -> None:
        """
        Track outbound webhook delivery status
        
        Args:
            delivery_id: Unique delivery identifier
            delivery_status: Current delivery status
            http_status_code: HTTP response code (if delivered)
            error_details: Error information (if failed)
            payload_size: Size of delivered payload
        """
        
        if not self.conversation_unit or not self.conversation_unit.webhook_metadata:
            logger.error("Cannot track delivery - conversation not initialized")
            return
        
        # Update delivery information
        self.conversation_unit.webhook_metadata.delivery_id = delivery_id
        self.conversation_unit.webhook_metadata.delivery_status = delivery_status
        self.conversation_unit.webhook_metadata.http_status_code = http_status_code
        self.conversation_unit.webhook_metadata.outbound_payload_size = payload_size
        self.conversation_unit.webhook_metadata.error_details = error_details
        
        # Increment delivery attempts
        if delivery_status in ["delivered", "failed", "retrying"]:
            self.conversation_unit.webhook_metadata.delivery_attempts += 1
        
        # Log delivery tracking
        logger.info("WEBHOOK_DELIVERY_TRACKED", extra={
            "conversation_id": self.conversation_unit.conversation_id,
            "delivery_id": delivery_id,
            "delivery_status": delivery_status,
            "http_status_code": http_status_code,
            "payload_size": payload_size,
            "delivery_attempts": self.conversation_unit.webhook_metadata.delivery_attempts,
            "has_errors": bool(error_details)
        })
    
    def complete_conversation(self) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Complete conversation tracking and prepare for export
        
        Returns:
            Tuple of (conversation_data, s3_url) - s3_url is None if export disabled
        """
        
        if not self.conversation_unit:
            logger.error("Cannot complete conversation - not initialized")
            return {}, None
        
        # Set end timestamp
        self.conversation_unit.end_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Generate conversation data for export
        conversation_data = self.conversation_unit.to_webhook_structured_json()
        
        # Log to CloudWatch
        self.cloudwatch_logger.info(
            "WEBHOOK_CONVERSATION_COMPLETE",
            extra=self.conversation_unit.to_compact_webhook_log()
        )
        
        # Export to S3 if enabled
        s3_url = None
        if self.enable_export and self.s3_client and self.s3_bucket:
            try:
                s3_url = self._export_to_s3(conversation_data)
                logger.info("WEBHOOK_CONVERSATION_EXPORTED", extra={
                    "conversation_id": self.conversation_unit.conversation_id,
                    "s3_url": s3_url,
                    "export_size_bytes": len(json.dumps(conversation_data))
                })
            except Exception as e:
                logger.error(f"Failed to export webhook conversation to S3: {e}", extra={
                    "conversation_id": self.conversation_unit.conversation_id,
                    "error": str(e)
                })
        
        return conversation_data, s3_url
    
    def _export_to_s3(self, conversation_data: Dict[str, Any]) -> str:
        """
        Export conversation data to S3 using existing path structure
        
        Args:
            conversation_data: Processed conversation data
            
        Returns:
            S3 URL of exported conversation
        """
        
        # Generate S3 path following existing patterns
        timestamp = self.conversation_unit.start_timestamp
        date_str = timestamp[:10]  # YYYY-MM-DD
        year, month, day = date_str.split('-')
        
        # Clean timestamp for directory name
        timestamp_dir = timestamp.replace(':', '-').split('.')[0]
        if '+' in timestamp_dir:
            timestamp_dir = timestamp_dir.split('+')[0]
        
        # Create S3 key
        s3_key = f"conversation-history/{year}/{month}/{day}/{timestamp_dir}/conversation.json"
        
        # Prepare export metadata
        export_data = {
            "export_metadata": {
                "format": "webhook_structured_json",
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "channel": "webhook",
                "source": "webhook_gateway",
                "conversation_type": "webhook_interaction"
            },
            "conversation": conversation_data
        }
        
        # Upload to S3
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_key,
            Body=json.dumps(export_data, indent=2, default=str),
            ContentType='application/json',
            Metadata={
                'conversation-id': self.conversation_unit.conversation_id,
                'export-timestamp': datetime.utcnow().isoformat(),
                'channel': 'webhook',
                'webhook-type': self.conversation_unit.webhook_metadata.webhook_type or 'unknown',
                'source-system': self.conversation_unit.webhook_metadata.source_system,
                'delivery-status': self.conversation_unit.webhook_metadata.delivery_status
            }
        )
        
        return f"s3://{self.s3_bucket}/{s3_key}"
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get current conversation summary for logging/monitoring"""
        
        if not self.conversation_unit:
            return {"status": "not_initialized"}
        
        return {
            "conversation_id": self.conversation_unit.conversation_id,
            "status": "active" if not self.conversation_unit.end_timestamp else "completed",
            "success": self.conversation_unit.success,
            "processing_time_ms": self.conversation_unit.processing_time_ms,
            "webhook_metadata": self.conversation_unit.webhook_metadata.to_dict() if self.conversation_unit.webhook_metadata else {},
            "agents_involved": self.conversation_unit.agents_involved,
            "response_length": len(self.conversation_unit.final_response)
        }