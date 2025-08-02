"""
RevOps AI Framework V2 - Queue Processor Module

SQS integration for asynchronous webhook processing with retry logic.
Extracted from the dispatcher_lambda implementation.
"""

import json
import boto3
import logging
import os
import time
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

class QueueProcessor:
    """
    SQS integration for asynchronous webhook processing.
    Handles sending webhook requests to queue and processing queue messages.
    Implements retry logic with exponential backoff.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the queue processor.
        
        Args:
            config: Configuration dictionary with queue settings
        """
        self.config = config
        self.queue_config = config.get("features", {}).get("queue_processing", {})
        
        # Set up SQS client
        self.sqs_client = boto3.client('sqs')
        
        # Get queue URL from config or environment
        self.queue_url = self.queue_config.get("queue_url", 
                                            os.environ.get("WEBHOOK_QUEUE_URL"))
        
        # Get retry configuration
        self.retry_config = self.queue_config.get("retries", {})
        self.max_retries = self.retry_config.get("max_attempts", 3)
        self.backoff_base = self.retry_config.get("backoff_base", 2)
    
    def is_sqs_event(self, event: Dict[str, Any]) -> bool:
        """
        Check if an event is an SQS message.
        
        Args:
            event: Event to check
            
        Returns:
            True if the event is an SQS message, False otherwise
        """
        # Check for SQS Records structure
        return (
            isinstance(event, dict) and
            "Records" in event and
            isinstance(event["Records"], list) and
            len(event["Records"]) > 0 and
            "eventSource" in event["Records"][0] and
            event["Records"][0]["eventSource"] == "aws:sqs"
        )
    
    def process_queue_message(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process SQS queue messages containing webhook requests.
        
        Args:
            event: SQS event with Records
            
        Returns:
            List of processing results for each record
        """
        results = []
        
        for record in event.get("Records", []):
            try:
                # Extract message body
                body = record.get("body", "{}")
                webhook_request = json.loads(body)
                
                # Process the request
                logger.info(f"Processing queue message: {webhook_request}")
                
                # Extract retry information
                attempt = webhook_request.get("attempt", 1)
                
                # This will be processed by the main handler using the core module
                results.append({
                    "record_id": record.get("messageId"),
                    "webhook_request": webhook_request,
                    "attempt": attempt,
                    "status": "processed"
                })
                
            except Exception as e:
                logger.error(f"Error processing queue message: {str(e)}")
                results.append({
                    "record_id": record.get("messageId") if "messageId" in record else "unknown",
                    "error": str(e),
                    "status": "error"
                })
                
        return results
    
    def send_to_queue(self, webhook_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send webhook request to SQS queue for asynchronous processing.
        
        Args:
            webhook_request: Webhook request to queue
            
        Returns:
            Dict with queueing result
        """
        if not self.queue_url:
            return {
                "success": False,
                "message": "Queue URL not configured"
            }
            
        try:
            # Ensure request has attempt number
            if "attempt" not in webhook_request:
                webhook_request["attempt"] = 1
                
            # Send message to SQS
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(webhook_request)
            )
            
            return {
                "success": True,
                "message": "Request queued successfully",
                "message_id": response.get("MessageId")
            }
            
        except Exception as e:
            logger.error(f"Error sending to queue: {str(e)}")
            return {
                "success": False,
                "message": f"Error sending to queue: {str(e)}"
            }
    
    def implement_retry(self, failed_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement exponential backoff retry for failed requests.
        
        Args:
            failed_request: Failed webhook request
            
        Returns:
            Dict with retry result
        """
        # Get attempt number, default to 1
        attempt = failed_request.get("attempt", 1)
        
        # Check if max retries reached
        if attempt >= self.max_retries:
            return {
                "success": False,
                "retried": False,
                "message": f"Max retries ({self.max_retries}) reached"
            }
            
        # Increment attempt counter
        failed_request["attempt"] = attempt + 1
        
        # Calculate backoff delay using exponential backoff
        # Formula: base ^ attempt (e.g., 2^1=2s, 2^2=4s, 2^3=8s)
        delay_seconds = self.backoff_base ** attempt
        
        try:
            # Send to queue with delay
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(failed_request),
                DelaySeconds=min(delay_seconds, 900)  # AWS SQS max delay is 900 seconds (15 minutes)
            )
            
            return {
                "success": True,
                "retried": True,
                "message": f"Request queued for retry (attempt {attempt + 1})",
                "message_id": response.get("MessageId"),
                "delay_seconds": delay_seconds
            }
            
        except Exception as e:
            logger.error(f"Error queuing retry: {str(e)}")
            return {
                "success": False,
                "retried": False,
                "message": f"Error queuing retry: {str(e)}"
            }
