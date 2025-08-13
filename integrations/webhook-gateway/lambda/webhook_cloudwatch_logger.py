"""
Enhanced CloudWatch Logging for Webhook Conversations
Provides structured logging compatible with existing monitoring infrastructure
"""

import json
import logging
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum

class WebhookEventType(Enum):
    """Webhook event types for structured logging"""
    REQUEST_RECEIVED = "WEBHOOK_REQUEST_RECEIVED"
    REQUEST_VALIDATED = "WEBHOOK_REQUEST_VALIDATED"
    REQUEST_TRANSFORMED = "WEBHOOK_REQUEST_TRANSFORMED"
    MANAGER_AGENT_INVOKED = "WEBHOOK_MANAGER_AGENT_INVOKED"
    MANAGER_AGENT_RESPONSE = "WEBHOOK_MANAGER_AGENT_RESPONSE"
    RESPONSE_CLASSIFIED = "WEBHOOK_RESPONSE_CLASSIFIED"
    OUTBOUND_QUEUED = "WEBHOOK_OUTBOUND_QUEUED"
    DELIVERY_ATTEMPTED = "WEBHOOK_DELIVERY_ATTEMPTED"
    DELIVERY_SUCCESS = "WEBHOOK_DELIVERY_SUCCESS"
    DELIVERY_FAILED = "WEBHOOK_DELIVERY_FAILED"
    CONVERSATION_COMPLETED = "WEBHOOK_CONVERSATION_COMPLETED"
    CONVERSATION_EXPORTED = "WEBHOOK_CONVERSATION_EXPORTED"
    ERROR_OCCURRED = "WEBHOOK_ERROR_OCCURRED"

class WebhookCloudWatchLogger:
    """Enhanced CloudWatch logger for webhook conversations"""
    
    def __init__(self, log_group: str = "/aws/lambda/webhook-conversations"):
        self.logger = logging.getLogger('webhook_structured_logger')
        self.logger.setLevel(logging.INFO)
        
        # Create CloudWatch handler if not exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        self.log_group = log_group
        
        # Metrics client for custom metrics
        try:
            self.cloudwatch = boto3.client('cloudwatch')
        except:
            self.cloudwatch = None
    
    def log_webhook_event(
        self,
        event_type: WebhookEventType,
        conversation_id: str,
        additional_data: Dict[str, Any] = None,
        metrics: Dict[str, float] = None
    ) -> None:
        """
        Log a structured webhook event
        
        Args:
            event_type: Type of webhook event
            conversation_id: Conversation identifier for tracking
            additional_data: Additional event-specific data
            metrics: Metrics to publish to CloudWatch (optional)
        """
        
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
            "conversation_id": conversation_id,
            "source": "webhook_gateway",
            "version": "1.0"
        }
        
        # Add additional data if provided
        if additional_data:
            log_entry.update(additional_data)
        
        # Log structured event
        self.logger.info(json.dumps(log_entry, default=str))
        
        # Publish metrics if provided
        if metrics and self.cloudwatch:
            self._publish_metrics(event_type, metrics)
    
    def log_request_received(
        self,
        conversation_id: str,
        source_system: str,
        source_process: str,
        query_length: int,
        has_timestamp: bool,
        request_size_bytes: int
    ) -> None:
        """Log webhook request received event"""
        
        self.log_webhook_event(
            WebhookEventType.REQUEST_RECEIVED,
            conversation_id,
            {
                "source_system": source_system,
                "source_process": source_process,
                "query_length": query_length,
                "has_timestamp": has_timestamp,
                "request_size_bytes": request_size_bytes
            },
            {
                "request_size": request_size_bytes,
                "query_length": query_length
            }
        )
    
    def log_request_validation(
        self,
        conversation_id: str,
        validation_success: bool,
        validation_errors: List[str] = None,
        validation_time_ms: int = 0
    ) -> None:
        """Log request validation results"""
        
        self.log_webhook_event(
            WebhookEventType.REQUEST_VALIDATED,
            conversation_id,
            {
                "validation_success": validation_success,
                "validation_errors": validation_errors or [],
                "validation_time_ms": validation_time_ms,
                "error_count": len(validation_errors) if validation_errors else 0
            },
            {
                "validation_time": validation_time_ms
            }
        )
    
    def log_manager_agent_invocation(
        self,
        conversation_id: str,
        agent_function_name: str,
        enhanced_query_length: int,
        has_date_context: bool
    ) -> None:
        """Log manager agent invocation"""
        
        self.log_webhook_event(
            WebhookEventType.MANAGER_AGENT_INVOKED,
            conversation_id,
            {
                "agent_function_name": agent_function_name,
                "enhanced_query_length": enhanced_query_length,
                "has_date_context": has_date_context
            }
        )
    
    def log_manager_agent_response(
        self,
        conversation_id: str,
        success: bool,
        processing_time_ms: int,
        response_length: int,
        agents_used: List[str] = None,
        session_id: str = None,
        error_details: str = None
    ) -> None:
        """Log manager agent response"""
        
        self.log_webhook_event(
            WebhookEventType.MANAGER_AGENT_RESPONSE,
            conversation_id,
            {
                "success": success,
                "processing_time_ms": processing_time_ms,
                "response_length": response_length,
                "agents_used": agents_used or [],
                "agents_count": len(agents_used) if agents_used else 0,
                "session_id": session_id,
                "error_details": error_details
            },
            {
                "agent_processing_time": processing_time_ms,
                "response_size": response_length
            }
        )
    
    def log_response_classification(
        self,
        conversation_id: str,
        webhook_type: str,
        target_webhook_url: str,
        classification_confidence: float = None,
        classification_time_ms: int = 0
    ) -> None:
        """Log response classification results"""
        
        self.log_webhook_event(
            WebhookEventType.RESPONSE_CLASSIFIED,
            conversation_id,
            {
                "webhook_type": webhook_type,
                "target_webhook_url": target_webhook_url,
                "classification_confidence": classification_confidence,
                "classification_time_ms": classification_time_ms
            },
            {
                "classification_time": classification_time_ms
            }
        )
    
    def log_outbound_queued(
        self,
        conversation_id: str,
        delivery_id: str,
        webhook_type: str,
        target_url: str,
        payload_size: int,
        queue_time_ms: int = 0
    ) -> None:
        """Log outbound webhook queued for delivery"""
        
        self.log_webhook_event(
            WebhookEventType.OUTBOUND_QUEUED,
            conversation_id,
            {
                "delivery_id": delivery_id,
                "webhook_type": webhook_type,
                "target_url": target_url,
                "payload_size": payload_size,
                "queue_time_ms": queue_time_ms
            },
            {
                "outbound_payload_size": payload_size,
                "queue_time": queue_time_ms
            }
        )
    
    def log_delivery_attempt(
        self,
        conversation_id: str,
        delivery_id: str,
        attempt_number: int,
        target_url: str,
        http_status: int = None,
        success: bool = False,
        error_message: str = None,
        response_time_ms: int = 0
    ) -> None:
        """Log webhook delivery attempt"""
        
        event_type = WebhookEventType.DELIVERY_SUCCESS if success else WebhookEventType.DELIVERY_FAILED
        
        self.log_webhook_event(
            event_type,
            conversation_id,
            {
                "delivery_id": delivery_id,
                "attempt_number": attempt_number,
                "target_url": target_url,
                "http_status": http_status,
                "success": success,
                "error_message": error_message,
                "response_time_ms": response_time_ms
            },
            {
                "delivery_response_time": response_time_ms
            }
        )
    
    def log_conversation_completed(
        self,
        conversation_id: str,
        total_time_ms: int,
        success: bool,
        webhook_metadata: Dict[str, Any],
        agents_involved: List[str],
        final_response_length: int
    ) -> None:
        """Log conversation completion"""
        
        self.log_webhook_event(
            WebhookEventType.CONVERSATION_COMPLETED,
            conversation_id,
            {
                "total_time_ms": total_time_ms,
                "success": success,
                "webhook_metadata": webhook_metadata,
                "agents_involved": agents_involved,
                "agents_count": len(agents_involved),
                "final_response_length": final_response_length
            },
            {
                "total_conversation_time": total_time_ms,
                "final_response_size": final_response_length
            }
        )
    
    def log_conversation_exported(
        self,
        conversation_id: str,
        s3_url: str,
        export_formats: List[str],
        export_size_bytes: int,
        export_time_ms: int = 0
    ) -> None:
        """Log conversation export to S3"""
        
        self.log_webhook_event(
            WebhookEventType.CONVERSATION_EXPORTED,
            conversation_id,
            {
                "s3_url": s3_url,
                "export_formats": export_formats,
                "export_size_bytes": export_size_bytes,
                "export_time_ms": export_time_ms,
                "formats_count": len(export_formats)
            },
            {
                "export_size": export_size_bytes,
                "export_time": export_time_ms
            }
        )
    
    def log_error(
        self,
        conversation_id: str,
        error_type: str,
        error_message: str,
        error_context: Dict[str, Any] = None,
        stack_trace: str = None
    ) -> None:
        """Log webhook error"""
        
        self.log_webhook_event(
            WebhookEventType.ERROR_OCCURRED,
            conversation_id,
            {
                "error_type": error_type,
                "error_message": error_message,
                "error_context": error_context or {},
                "stack_trace": stack_trace,
                "severity": "error"
            }
        )
    
    def _publish_metrics(self, event_type: WebhookEventType, metrics: Dict[str, float]) -> None:
        """Publish custom metrics to CloudWatch"""
        
        try:
            metric_data = []
            
            for metric_name, value in metrics.items():
                metric_data.append({
                    'MetricName': f'Webhook.{metric_name}',
                    'Value': value,
                    'Unit': 'Count' if 'count' in metric_name.lower() else 'Milliseconds' if 'time' in metric_name.lower() else 'Bytes' if 'size' in metric_name.lower() else 'None',
                    'Dimensions': [
                        {
                            'Name': 'EventType',
                            'Value': event_type.value
                        },
                        {
                            'Name': 'Source',
                            'Value': 'webhook_gateway'
                        }
                    ]
                })
            
            # Publish metrics in batches of 20 (CloudWatch limit)
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i+20]
                self.cloudwatch.put_metric_data(
                    Namespace='RevOps/WebhookGateway',
                    MetricData=batch
                )
                
        except Exception as e:
            self.logger.warning(f"Failed to publish metrics: {e}")
    
    def create_conversation_dashboard_data(self, conversation_id: str) -> Dict[str, Any]:
        """Generate data for conversation monitoring dashboard"""
        
        # This would integrate with existing dashboard infrastructure
        return {
            "conversation_id": conversation_id,
            "dashboard_url": f"https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups/log-group/{self.log_group.replace('/', '%2F')}/log-events$3FfilterPattern$3D{conversation_id}",
            "metrics_namespace": "RevOps/WebhookGateway",
            "log_group": self.log_group
        }

# Global logger instance
webhook_logger = WebhookCloudWatchLogger()

# Convenience functions for common logging patterns
def log_webhook_request(conversation_id: str, source_system: str, source_process: str, query_length: int) -> None:
    """Convenience function for logging webhook requests"""
    webhook_logger.log_request_received(
        conversation_id=conversation_id,
        source_system=source_system,
        source_process=source_process,
        query_length=query_length,
        has_timestamp=True,  # Assuming timestamp validation passed
        request_size_bytes=len(json.dumps({"source_system": source_system, "source_process": source_process}))
    )

def log_manager_agent_success(conversation_id: str, processing_time_ms: int, response_length: int, agents_used: List[str]) -> None:
    """Convenience function for logging successful manager agent responses"""
    webhook_logger.log_manager_agent_response(
        conversation_id=conversation_id,
        success=True,
        processing_time_ms=processing_time_ms,
        response_length=response_length,
        agents_used=agents_used
    )

def log_delivery_success(conversation_id: str, delivery_id: str, webhook_type: str, http_status: int, response_time_ms: int) -> None:
    """Convenience function for logging successful webhook deliveries"""
    webhook_logger.log_delivery_attempt(
        conversation_id=conversation_id,
        delivery_id=delivery_id,
        attempt_number=1,  # This would be tracked properly in practice
        target_url="webhook_endpoint",
        http_status=http_status,
        success=True,
        response_time_ms=response_time_ms
    )