"""
Webhook Gateway - Main Lambda Handler
Handles inbound webhook requests and coordinates responses
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
    transform_to_manager_format, 
    extract_webhook_request_data
)
from response_classifier import (
    classify_response_type,
    get_target_webhook_url,
    format_webhook_response
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
lambda_client = boto3.client('lambda')
sqs_client = boto3.client('sqs')

# Environment variables
MANAGER_AGENT_FUNCTION_NAME = os.environ.get('MANAGER_AGENT_FUNCTION_NAME', 'revops-manager-agent')
OUTBOUND_WEBHOOK_QUEUE_URL = os.environ.get('OUTBOUND_WEBHOOK_QUEUE_URL')

def invoke_manager_agent(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke the existing manager agent with transformed request.
    
    Args:
        request_data: Request in manager agent format
        
    Returns:
        Manager agent response
    """
    try:
        logger.info(f"Invoking manager agent", extra={
            "function_name": MANAGER_AGENT_FUNCTION_NAME,
            "conversation_id": request_data.get("correlation_id")
        })
        
        response = lambda_client.invoke(
            FunctionName=MANAGER_AGENT_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(request_data)
        )
        
        # Parse response
        if response['StatusCode'] != 200:
            raise Exception(f"Manager agent invocation failed with status {response['StatusCode']}")
        
        payload = response['Payload'].read().decode('utf-8')
        result = json.loads(payload)
        
        logger.info(f"Manager agent response received", extra={
            "success": result.get("success", False),
            "source": result.get("source", "unknown"),
            "conversation_id": request_data.get("correlation_id")
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error invoking manager agent: {str(e)}")
        raise Exception(f"Manager agent invocation failed: {str(e)}")

def queue_outbound_delivery(webhook_payload: Dict[str, Any], target_webhook_url: str, 
                          conversation_id: str, response_type: str) -> str:
    """
    Queue outbound webhook delivery for async processing.
    
    Args:
        webhook_payload: Formatted webhook payload
        target_webhook_url: Target webhook URL
        conversation_id: Conversation ID for tracking
        response_type: Response type for metrics
        
    Returns:
        Delivery ID for tracking
    """
    try:
        delivery_id = str(uuid.uuid4())
        
        # Create SQS message
        message = {
            "delivery_id": delivery_id,
            "target_webhook_url": target_webhook_url,
            "payload": webhook_payload,
            "attempt": 1,
            "max_attempts": 5,
            "conversation_id": conversation_id
        }
        
        # Send to SQS queue
        if OUTBOUND_WEBHOOK_QUEUE_URL:
            sqs_client.send_message(
                QueueUrl=OUTBOUND_WEBHOOK_QUEUE_URL,
                MessageBody=json.dumps(message),
                MessageAttributes={
                    'delivery_id': {
                        'StringValue': delivery_id,
                        'DataType': 'String'
                    },
                    'webhook_type': {
                        'StringValue': response_type,
                        'DataType': 'String'
                    },
                    'conversation_id': {
                        'StringValue': conversation_id,
                        'DataType': 'String'
                    }
                }
            )
            
            logger.info(f"Queued outbound webhook delivery", extra={
                "delivery_id": delivery_id,
                "webhook_type": response_type,
                "conversation_id": conversation_id,
                "target_url": target_webhook_url[:50] + "..." if len(target_webhook_url) > 50 else target_webhook_url
            })
            
            return delivery_id
        else:
            logger.error("OUTBOUND_WEBHOOK_QUEUE_URL not configured")
            raise Exception("Outbound webhook queue not configured")
            
    except Exception as e:
        logger.error(f"Error queueing outbound delivery: {str(e)}")
        raise Exception(f"Failed to queue webhook delivery: {str(e)}")

def create_error_response(status_code: int, error_message: str, 
                         conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        status_code: HTTP status code
        error_message: Error message
        conversation_id: Optional conversation ID
        
    Returns:
        Error response in API Gateway format
    """
    error_body = {
        "success": False,
        "error": error_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conversation_id": conversation_id
    }
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(error_body)
    }

def create_success_response(ai_response: Dict[str, Any], webhook_delivery: Dict[str, Any],
                          processing_time_ms: int) -> Dict[str, Any]:
    """
    Create standardized success response.
    
    Args:
        ai_response: AI response data
        webhook_delivery: Webhook delivery status
        processing_time_ms: Total processing time
        
    Returns:
        Success response in API Gateway format
    """
    response_body = {
        "success": True,
        "processing_time_ms": processing_time_ms,
        "webhook_delivery": webhook_delivery,
        "ai_response": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat()
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
    Main webhook gateway lambda handler.
    
    Args:
        event: Lambda event containing webhook request
        context: Lambda context
        
    Returns:
        API Gateway compatible response
    """
    start_time = time.time()
    conversation_id = None
    
    try:
        logger.info("Webhook gateway request received", extra={
            "request_id": context.aws_request_id,
            "source_ip": event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        })
        
        # Step 1: Extract and validate webhook request
        webhook_request = extract_webhook_request_data(event)
        is_valid, error_message = validate_webhook_request(event)
        
        if not is_valid:
            logger.warning(f"Invalid webhook request: {error_message}")
            return create_error_response(400, error_message)
        
        # Step 2: Transform to manager agent format
        manager_request = transform_to_manager_format(webhook_request)
        conversation_id = manager_request.get("correlation_id")
        
        # Step 3: Invoke manager agent
        manager_response = invoke_manager_agent(manager_request)
        
        if not manager_response.get("success", False):
            error_msg = manager_response.get("error", "Manager agent processing failed")
            logger.error(f"Manager agent failed: {error_msg}")
            return create_error_response(500, f"AI processing failed: {error_msg}", conversation_id)
        
        # Step 4: Classify response and determine target webhook
        response_type = classify_response_type(manager_response, webhook_request["query"])
        target_webhook_url = get_target_webhook_url(response_type)
        
        if not target_webhook_url:
            logger.error(f"No webhook URL configured for response type: {response_type}")
            return create_error_response(500, f"No webhook configured for {response_type}", conversation_id)
        
        # Step 5: Format webhook payload
        conversation_metadata = {
            "conversation_id": conversation_id,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_system": webhook_request["source_system"],
            "source_process": webhook_request["source_process"],
            "original_timestamp": webhook_request["timestamp"]
        }
        
        webhook_payload = format_webhook_response(manager_response, response_type, conversation_metadata)
        
        # Step 6: Queue outbound delivery (async)
        delivery_status = {"status": "not_queued", "error": None}
        
        try:
            delivery_id = queue_outbound_delivery(
                webhook_payload, 
                target_webhook_url, 
                conversation_id, 
                response_type
            )
            delivery_status = {
                "status": "queued",
                "target_webhook": response_type,
                "delivery_id": delivery_id,
                "target_url": target_webhook_url
            }
        except Exception as delivery_error:
            logger.error(f"Failed to queue outbound delivery: {str(delivery_error)}")
            delivery_status = {
                "status": "queue_failed", 
                "error": str(delivery_error),
                "target_webhook": response_type
            }
        
        # Step 7: Return immediate response
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        ai_response = {
            "header": response_type,
            "response_rich": webhook_payload["response_rich"],
            "response_plain": webhook_payload["response_plain"],
            "agents_used": webhook_payload["agents_used"]
        }
        
        logger.info("Webhook gateway request completed", extra={
            "conversation_id": conversation_id,
            "response_type": response_type,
            "processing_time_ms": processing_time_ms,
            "delivery_status": delivery_status["status"]
        })
        
        return create_success_response(ai_response, delivery_status, processing_time_ms)
        
    except Exception as e:
        logger.error(f"Unhandled error in webhook gateway: {str(e)}", exc_info=True)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return create_error_response(500, f"Internal server error: {str(e)}", conversation_id)

# Health check endpoint
def health_check_handler(event, context):
    """Simple health check for API Gateway health checks"""
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0"
        })
    }