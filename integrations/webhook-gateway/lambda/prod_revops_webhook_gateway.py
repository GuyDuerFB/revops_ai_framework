"""
Webhook Gateway - Asynchronous Lambda Handler
Handles inbound webhook requests and immediately queues for processing
Returns 200 response with tracking ID without waiting for AI processing
"""

import json
import os
import boto3
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from request_transformer import (
    validate_webhook_request, 
    extract_webhook_request_data
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
sqs_client = boto3.client('sqs')

# Environment variables
OUTBOUND_WEBHOOK_QUEUE_URL = os.environ.get('OUTBOUND_WEBHOOK_QUEUE_URL')

def queue_request_for_processing(webhook_request: Dict[str, Any], tracking_id: str) -> str:
    """
    Queue webhook request for asynchronous AI processing.
    
    Args:
        webhook_request: Original webhook request data
        tracking_id: Unique tracking ID for this request
        
    Returns:
        Tracking ID for request tracking
    """
    try:
        # Create processing message for SQS queue
        processing_message = {
            "message_type": "webhook_processing_request",
            "tracking_id": tracking_id,
            "webhook_request": webhook_request,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "attempt": 1,
            "max_attempts": 3
        }
        
        # Send to SQS queue for processing
        if OUTBOUND_WEBHOOK_QUEUE_URL:
            sqs_client.send_message(
                QueueUrl=OUTBOUND_WEBHOOK_QUEUE_URL,
                MessageBody=json.dumps(processing_message),
                MessageAttributes={
                    'message_type': {
                        'StringValue': 'webhook_processing_request',
                        'DataType': 'String'
                    },
                    'tracking_id': {
                        'StringValue': tracking_id,
                        'DataType': 'String'
                    },
                    'source_system': {
                        'StringValue': webhook_request.get('source_system', 'unknown'),
                        'DataType': 'String'
                    }
                }
            )
            
            logger.info(f"Queued webhook request for processing", extra={
                "tracking_id": tracking_id,
                "source_system": webhook_request.get('source_system'),
                "source_process": webhook_request.get('source_process'),
                "query_length": len(webhook_request.get('query', ''))
            })
            
            return tracking_id
        else:
            logger.error("OUTBOUND_WEBHOOK_QUEUE_URL not configured")
            raise Exception("Processing queue not configured")
            
    except Exception as e:
        logger.error(f"Error queueing request for processing: {str(e)}")
        raise Exception(f"Failed to queue request: {str(e)}")

def create_error_response(status_code: int, error_message: str, 
                         tracking_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        status_code: HTTP status code
        error_message: Error message
        tracking_id: Optional tracking ID
        
    Returns:
        Error response in API Gateway format
    """
    error_body = {
        "success": False,
        "error": error_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tracking_id": tracking_id
    }
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(error_body)
    }

def create_queued_response(tracking_id: str) -> Dict[str, Any]:
    """
    Create response indicating request was successfully queued.
    
    Args:
        tracking_id: Unique tracking ID
        
    Returns:
        Success response in API Gateway format
    """
    response_body = {
        "success": True,
        "message": "Request queued for processing",
        "tracking_id": tracking_id,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "status": "queued"
    }
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(response_body)
    }

def lambda_handler(event, context):
    """
    Asynchronous webhook gateway lambda handler.
    Immediately queues requests and returns 200 response with tracking ID.
    
    Args:
        event: Lambda event containing webhook request
        context: Lambda context
        
    Returns:
        API Gateway compatible response with tracking ID
    """
    start_time = time.time()
    tracking_id = str(uuid.uuid4())
    
    try:
        logger.info("Webhook gateway request received", extra={
            "request_id": context.aws_request_id,
            "tracking_id": tracking_id,
            "source_ip": event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        })
        
        # Step 1: Extract and validate webhook request
        webhook_request = extract_webhook_request_data(event)
        is_valid, error_message = validate_webhook_request(event)
        
        if not is_valid:
            logger.warning(f"Invalid webhook request: {error_message}", extra={
                "tracking_id": tracking_id
            })
            return create_error_response(400, error_message, tracking_id)
        
        # Step 2: Immediately queue for asynchronous processing
        try:
            queue_request_for_processing(webhook_request, tracking_id)
        except Exception as queue_error:
            logger.error(f"Failed to queue request: {str(queue_error)}", extra={
                "tracking_id": tracking_id
            })
            return create_error_response(503, "Service temporarily unavailable", tracking_id)
        
        # Step 3: Return immediate success response
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info("Webhook request queued successfully", extra={
            "tracking_id": tracking_id,
            "processing_time_ms": processing_time_ms,
            "source_system": webhook_request.get('source_system'),
            "query_preview": webhook_request.get('query', '')[:100]
        })
        
        return create_queued_response(tracking_id)
        
    except Exception as e:
        logger.error(f"Unhandled error in webhook gateway: {str(e)}", extra={
            "tracking_id": tracking_id
        }, exc_info=True)
        
        return create_error_response(500, f"Internal server error: {str(e)}", tracking_id)

# Health check endpoint
def health_check_handler(event, context):
    """Simple health check for API Gateway health checks"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0-async"
        })
    }