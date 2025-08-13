"""
RevOps AI Framework V2 - Outbound Webhook Delivery Module
Handles asynchronous webhook delivery with retry logic and status tracking
"""

import json
import time
import logging
import requests
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import random
import math

logger = logging.getLogger(__name__)

class OutboundDeliveryHandler:
    """Handles outbound webhook delivery with retry logic"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize outbound delivery handler.
        
        Args:
            config: Configuration dictionary with delivery settings
        """
        self.config = config
        self.retry_config = config.get("features", {}).get("queue_processing", {}).get("retries", {})
        self.max_attempts = self.retry_config.get("max_attempts", 5)
        self.base_delay_seconds = self.retry_config.get("base_delay_seconds", 1)
        self.max_delay_seconds = self.retry_config.get("max_delay_seconds", 300)
        self.backoff_multiplier = self.retry_config.get("backoff_multiplier", 2)
        self.jitter = self.retry_config.get("jitter", True)
        
        # Initialize CloudWatch for metrics
        self.cloudwatch = boto3.client('cloudwatch')
        
    def process_outbound_delivery(self, sqs_event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process SQS messages for outbound webhook delivery.
        
        Args:
            sqs_event: SQS event with Records
            
        Returns:
            List of processing results
        """
        results = []
        
        for record in sqs_event.get("Records", []):
            try:
                # Parse SQS message
                message_body = json.loads(record.get("body", "{}"))
                message_attributes = record.get("messageAttributes", {})
                
                # Extract delivery data
                delivery_id = message_body.get("delivery_id")
                target_webhook_url = message_body.get("target_webhook_url")
                payload = message_body.get("payload")
                attempt = message_body.get("attempt", 1)
                max_attempts = message_body.get("max_attempts", self.max_attempts)
                conversation_id = message_body.get("conversation_id")
                
                logger.info(f"Processing outbound delivery", extra={
                    "delivery_id": delivery_id,
                    "target_url": target_webhook_url[:50] + "..." if target_webhook_url and len(target_webhook_url) > 50 else target_webhook_url,
                    "attempt": attempt,
                    "conversation_id": conversation_id
                })
                
                # Attempt delivery
                delivery_result = self.deliver_webhook_with_retry(
                    webhook_data={
                        "delivery_id": delivery_id,
                        "target_webhook_url": target_webhook_url,
                        "payload": payload,
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "conversation_id": conversation_id
                    }
                )
                
                results.append({
                    "record_id": record.get("messageId"),
                    "delivery_id": delivery_id,
                    "success": delivery_result["success"],
                    "message": delivery_result["message"],
                    "attempt": attempt,
                    "status_code": delivery_result.get("status_code"),
                    "retry_scheduled": delivery_result.get("retry_scheduled", False)
                })
                
            except Exception as e:
                logger.error(f"Error processing SQS record: {str(e)}")
                results.append({
                    "record_id": record.get("messageId"),
                    "success": False,
                    "message": f"Error processing record: {str(e)}"
                })
                
        return results
    
    def deliver_webhook_with_retry(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver webhook with retry logic and status tracking.
        
        Args:
            webhook_data: Webhook delivery data
            
        Returns:
            Delivery result
        """
        delivery_id = webhook_data.get("delivery_id")
        target_webhook_url = webhook_data.get("target_webhook_url")
        payload = webhook_data.get("payload")
        attempt = webhook_data.get("attempt", 1)
        max_attempts = webhook_data.get("max_attempts", self.max_attempts)
        conversation_id = webhook_data.get("conversation_id")
        
        start_time = time.time()
        
        try:
            # Attempt webhook delivery
            success, status_code, response_text, error_message = self._make_webhook_request(
                target_webhook_url, payload
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if success:
                # Record successful delivery
                self._record_delivery_metric("Success", {
                    "webhook_type": payload.get("header", "unknown"),
                    "attempt": attempt
                }, duration_ms)
                
                self._update_delivery_status(delivery_id, "delivered", {
                    "status_code": status_code,
                    "response": response_text[:200] if response_text else None,
                    "attempt": attempt,
                    "duration_ms": duration_ms
                })
                
                logger.info(f"Webhook delivered successfully", extra={
                    "delivery_id": delivery_id,
                    "status_code": status_code,
                    "attempt": attempt,
                    "duration_ms": duration_ms
                })
                
                return {
                    "success": True,
                    "message": "Webhook delivered successfully",
                    "status_code": status_code,
                    "duration_ms": duration_ms
                }
                
            else:
                # Handle delivery failure
                if attempt < max_attempts:
                    # Schedule retry
                    retry_scheduled = self._schedule_retry(webhook_data)
                    
                    self._record_delivery_metric("Retry", {
                        "webhook_type": payload.get("header", "unknown"),
                        "attempt": attempt,
                        "status_code": status_code
                    }, duration_ms)
                    
                    self._update_delivery_status(delivery_id, "retry_scheduled", {
                        "status_code": status_code,
                        "error": error_message,
                        "attempt": attempt,
                        "next_attempt": attempt + 1,
                        "duration_ms": duration_ms
                    })
                    
                    logger.warning(f"Webhook delivery failed, retry scheduled", extra={
                        "delivery_id": delivery_id,
                        "status_code": status_code,
                        "attempt": attempt,
                        "next_attempt": attempt + 1,
                        "error": error_message
                    })
                    
                    return {
                        "success": False,
                        "message": f"Delivery failed, retry scheduled (attempt {attempt}/{max_attempts})",
                        "status_code": status_code,
                        "retry_scheduled": retry_scheduled,
                        "duration_ms": duration_ms
                    }
                    
                else:
                    # All retries exhausted
                    self._record_delivery_metric("Failed", {
                        "webhook_type": payload.get("header", "unknown"),
                        "attempt": attempt,
                        "status_code": status_code
                    }, duration_ms)
                    
                    self._update_delivery_status(delivery_id, "failed", {
                        "status_code": status_code,
                        "error": error_message,
                        "attempt": attempt,
                        "duration_ms": duration_ms,
                        "final_failure": True
                    })
                    
                    logger.error(f"Webhook delivery failed permanently", extra={
                        "delivery_id": delivery_id,
                        "status_code": status_code,
                        "attempt": attempt,
                        "error": error_message
                    })
                    
                    return {
                        "success": False,
                        "message": f"Delivery failed permanently after {attempt} attempts",
                        "status_code": status_code,
                        "duration_ms": duration_ms
                    }
                    
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.error(f"Error in webhook delivery: {str(e)}")
            
            self._record_delivery_metric("Error", {
                "webhook_type": payload.get("header", "unknown"),
                "attempt": attempt
            }, duration_ms)
            
            self._update_delivery_status(delivery_id, "error", {
                "error": str(e),
                "attempt": attempt,
                "duration_ms": duration_ms
            })
            
            return {
                "success": False,
                "message": f"Delivery error: {str(e)}",
                "duration_ms": duration_ms
            }
    
    def _make_webhook_request(self, url: str, payload: Dict[str, Any]) -> Tuple[bool, Optional[int], Optional[str], Optional[str]]:
        """
        Make HTTP request to webhook URL.
        
        Args:
            url: Webhook URL
            payload: JSON payload to send
            
        Returns:
            Tuple of (success, status_code, response_text, error_message)
        """
        try:
            logger.debug(f"Making webhook request to {url}")
            
            response = requests.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "RevOps-AI-Framework/2.0"
                },
                timeout=30  # 30 second timeout
            )
            
            # Consider 2xx status codes as success
            success = 200 <= response.status_code < 300
            
            return success, response.status_code, response.text, None
            
        except requests.exceptions.Timeout:
            return False, None, None, "Request timed out"
        except requests.exceptions.ConnectionError:
            return False, None, None, "Connection error"
        except requests.exceptions.RequestException as e:
            return False, None, None, f"Request failed: {str(e)}"
        except Exception as e:
            return False, None, None, f"Unexpected error: {str(e)}"
    
    def _schedule_retry(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Schedule retry by sending message back to SQS with delay.
        
        Args:
            webhook_data: Original webhook data
            
        Returns:
            True if retry was scheduled successfully
        """
        try:
            # Calculate delay with exponential backoff and jitter
            attempt = webhook_data.get("attempt", 1)
            delay_seconds = min(
                self.base_delay_seconds * (self.backoff_multiplier ** (attempt - 1)),
                self.max_delay_seconds
            )
            
            # Add jitter to prevent thundering herd
            if self.jitter:
                jitter_amount = delay_seconds * 0.1  # 10% jitter
                delay_seconds += random.uniform(-jitter_amount, jitter_amount)
            
            delay_seconds = max(0, int(delay_seconds))
            
            # Create retry message
            retry_message = webhook_data.copy()
            retry_message["attempt"] = attempt + 1
            retry_message["retry_scheduled_at"] = datetime.now(timezone.utc).isoformat()
            
            # Send to SQS with delay
            sqs = boto3.client('sqs')
            queue_url = os.environ.get('OUTBOUND_WEBHOOK_QUEUE_URL')
            
            if queue_url:
                sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(retry_message),
                    DelaySeconds=min(delay_seconds, 900),  # SQS max delay is 15 minutes
                    MessageAttributes={
                        'delivery_id': {
                            'StringValue': webhook_data.get("delivery_id", "unknown"),
                            'DataType': 'String'
                        },
                        'attempt': {
                            'StringValue': str(attempt + 1),
                            'DataType': 'Number'
                        },
                        'retry': {
                            'StringValue': 'true',
                            'DataType': 'String'
                        }
                    }
                )
                
                logger.info(f"Retry scheduled", extra={
                    "delivery_id": webhook_data.get("delivery_id"),
                    "next_attempt": attempt + 1,
                    "delay_seconds": delay_seconds
                })
                
                return True
            else:
                logger.error("Cannot schedule retry: OUTBOUND_WEBHOOK_QUEUE_URL not configured")
                return False
                
        except Exception as e:
            logger.error(f"Error scheduling retry: {str(e)}")
            return False
    
    def _update_delivery_status(self, delivery_id: str, status: str, details: Dict[str, Any]) -> None:
        """
        Update delivery status in CloudWatch logs.
        
        Args:
            delivery_id: Delivery ID
            status: New status
            details: Status details
        """
        try:
            logger.info("DELIVERY_STATUS_UPDATE", extra={
                "delivery_id": delivery_id,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **details
            })
        except Exception as e:
            logger.error(f"Error updating delivery status: {str(e)}")
    
    def _record_delivery_metric(self, metric_name: str, dimensions: Dict[str, Any], duration_ms: int) -> None:
        """
        Record delivery metrics in CloudWatch.
        
        Args:
            metric_name: Metric name (Success, Failed, Retry, Error)
            dimensions: Metric dimensions
            duration_ms: Duration in milliseconds
        """
        try:
            # Record count metric
            self.cloudwatch.put_metric_data(
                Namespace='RevOpsAI/WebhookDelivery',
                MetricData=[
                    {
                        'MetricName': f'{metric_name}.Count',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'WebhookType',
                                'Value': dimensions.get('webhook_type', 'unknown')
                            },
                            {
                                'Name': 'Attempt',
                                'Value': str(dimensions.get('attempt', 1))
                            }
                        ]
                    },
                    {
                        'MetricName': f'{metric_name}.Duration',
                        'Value': duration_ms,
                        'Unit': 'Milliseconds',
                        'Dimensions': [
                            {
                                'Name': 'WebhookType',
                                'Value': dimensions.get('webhook_type', 'unknown')
                            }
                        ]
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Error recording metric: {str(e)}")

def format_outbound_payload(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the outbound webhook payload according to specification.
    
    Args:
        response_data: Response data from AI processing
        
    Returns:
        Formatted webhook payload
    """
    return {
        "header": response_data.get("header", "general"),
        "response_rich": response_data.get("response_rich", ""),
        "response_plain": response_data.get("response_plain", ""),
        "agents_used": response_data.get("agents_used", []),
        "metadata": response_data.get("metadata", {})
    }