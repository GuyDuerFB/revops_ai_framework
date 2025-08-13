"""
Enhanced Queue Processor for Webhook Gateway
Handles both AI processing requests and outbound webhook delivery
"""

import json
import os
import boto3
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Initialize AWS clients
lambda_client = boto3.client('lambda')
sqs_client = boto3.client('sqs')

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Environment variables
MANAGER_AGENT_FUNCTION_NAME = os.environ.get('MANAGER_AGENT_FUNCTION_NAME', 'revops-manager-agent-wrapper')
OUTBOUND_WEBHOOK_QUEUE_URL = os.environ.get('OUTBOUND_WEBHOOK_QUEUE_URL')
DEAL_ANALYSIS_WEBHOOK_URL = os.environ.get('DEAL_ANALYSIS_WEBHOOK_URL', '')
DATA_ANALYSIS_WEBHOOK_URL = os.environ.get('DATA_ANALYSIS_WEBHOOK_URL', '')
LEAD_ANALYSIS_WEBHOOK_URL = os.environ.get('LEAD_ANALYSIS_WEBHOOK_URL', '')
GENERAL_WEBHOOK_URL = os.environ.get('GENERAL_WEBHOOK_URL', '')

def transform_to_manager_format(webhook_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform webhook request to manager agent format.
    
    Args:
        webhook_request: Original webhook request
        
    Returns:
        Request in manager agent format
    """
    correlation_id = str(uuid.uuid4())
    
    return {
        "user_message": webhook_request["query"],
        "correlation_id": correlation_id,
        "metadata": {
            "source_system": webhook_request.get("source_system", "webhook"),
            "source_process": webhook_request.get("source_process", "api"),
            "original_timestamp": webhook_request.get("timestamp"),
            "webhook_timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

def invoke_manager_agent(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke the manager agent with transformed request.
    
    Args:
        request_data: Request in manager agent format
        
    Returns:
        Manager agent response
    """
    try:
        logger.info(f"Invoking manager agent", extra={
            "function_name": MANAGER_AGENT_FUNCTION_NAME,
            "correlation_id": request_data.get("correlation_id")
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
            "correlation_id": request_data.get("correlation_id")
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error invoking manager agent: {str(e)}")
        raise Exception(f"Manager agent invocation failed: {str(e)}")

def classify_response_type(manager_response: Dict[str, Any], query: str) -> str:
    """
    Classify the response to determine webhook type.
    
    Args:
        manager_response: Response from manager agent
        query: Original query for context
        
    Returns:
        Response type (deal_analysis, data_analysis, lead_analysis, general)
    """
    # Simple classification logic - can be enhanced
    response_text = manager_response.get("response", "").lower()
    query_text = query.lower()
    
    # Deal analysis keywords
    if any(keyword in response_text or keyword in query_text for keyword in 
           ['deal', 'opportunity', 'pipeline', 'forecast', 'closing', 'negotiation', 'contract']):
        return 'deal_analysis'
    
    # Data analysis keywords
    if any(keyword in response_text or keyword in query_text for keyword in 
           ['data', 'analysis', 'query', 'report', 'metrics', 'dashboard']):
        return 'data_analysis'
    
    # Lead analysis keywords
    if any(keyword in response_text or keyword in query_text for keyword in 
           ['lead', 'prospect', 'customer', 'outreach', 'conversion', 'icp']):
        return 'lead_analysis'
    
    # Default to general
    return 'general'

def get_target_webhook_url(response_type: str) -> Optional[str]:
    """
    Get target webhook URL based on response type.
    
    Args:
        response_type: Classification of the response
        
    Returns:
        Target webhook URL or None if not configured
    """
    webhook_mapping = {
        'deal_analysis': DEAL_ANALYSIS_WEBHOOK_URL,
        'data_analysis': DATA_ANALYSIS_WEBHOOK_URL,
        'lead_analysis': LEAD_ANALYSIS_WEBHOOK_URL,
        'general': GENERAL_WEBHOOK_URL
    }
    
    url = webhook_mapping.get(response_type, GENERAL_WEBHOOK_URL)
    return url if url and url.strip() else None

def format_webhook_response(manager_response: Dict[str, Any], response_type: str, 
                          tracking_id: str, processing_time_ms: int) -> Dict[str, Any]:
    """
    Format the response for webhook delivery.
    
    Args:
        manager_response: Response from manager agent
        response_type: Classified response type
        tracking_id: Original tracking ID
        processing_time_ms: Processing time
        
    Returns:
        Formatted webhook payload
    """
    # Extract response text (may be in different formats)
    response_text = (
        manager_response.get("response") or
        manager_response.get("result") or
        manager_response.get("message") or
        str(manager_response)
    )
    
    return {
        "header": response_type,
        "response_rich": response_text,
        "response_plain": response_text,  # Could add markdown stripping here
        "agents_used": ["ManagerAgent"],
        "metadata": {
            "tracking_id": tracking_id,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_system": "revops_ai_framework",
            "source_process": "webhook_gateway"
        }
    }

def queue_outbound_delivery(webhook_payload: Dict[str, Any], target_webhook_url: str, 
                          tracking_id: str, response_type: str) -> str:
    """
    Queue outbound webhook delivery.
    
    Args:
        webhook_payload: Formatted webhook payload
        target_webhook_url: Target webhook URL
        tracking_id: Tracking ID for correlation
        response_type: Response type for metrics
        
    Returns:
        Delivery ID for tracking
    """
    try:
        delivery_id = str(uuid.uuid4())
        
        # Create delivery message
        delivery_message = {
            "message_type": "outbound_delivery",
            "delivery_id": delivery_id,
            "target_webhook_url": target_webhook_url,
            "payload": webhook_payload,
            "attempt": 1,
            "max_attempts": 5,
            "tracking_id": tracking_id
        }
        
        # Send to same SQS queue with different message type
        if OUTBOUND_WEBHOOK_QUEUE_URL:
            sqs_client.send_message(
                QueueUrl=OUTBOUND_WEBHOOK_QUEUE_URL,
                MessageBody=json.dumps(delivery_message),
                MessageAttributes={
                    'message_type': {
                        'StringValue': 'outbound_delivery',
                        'DataType': 'String'
                    },
                    'delivery_id': {
                        'StringValue': delivery_id,
                        'DataType': 'String'
                    },
                    'webhook_type': {
                        'StringValue': response_type,
                        'DataType': 'String'
                    },
                    'tracking_id': {
                        'StringValue': tracking_id,
                        'DataType': 'String'
                    }
                }
            )
            
            logger.info(f"Queued outbound delivery", extra={
                "delivery_id": delivery_id,
                "tracking_id": tracking_id,
                "webhook_type": response_type,
                "target_url": target_webhook_url[:50] + "..." if len(target_webhook_url) > 50 else target_webhook_url
            })
            
            return delivery_id
        else:
            logger.error("OUTBOUND_WEBHOOK_QUEUE_URL not configured")
            raise Exception("Outbound webhook queue not configured")
            
    except Exception as e:
        logger.error(f"Error queueing outbound delivery: {str(e)}")
        raise Exception(f"Failed to queue webhook delivery: {str(e)}")

def process_webhook_request(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a webhook request by invoking the manager agent.
    
    Args:
        message: SQS message containing webhook request
        
    Returns:
        Processing result
    """
    tracking_id = message.get("tracking_id")
    webhook_request = message.get("webhook_request")
    
    start_time = time.time()
    
    try:
        logger.info(f"Processing webhook request", extra={
            "tracking_id": tracking_id,
            "source_system": webhook_request.get("source_system")
        })
        
        # Transform to manager agent format
        manager_request = transform_to_manager_format(webhook_request)
        
        # Invoke manager agent
        manager_response = invoke_manager_agent(manager_request)
        
        if not manager_response.get("success", False):
            error_msg = manager_response.get("error", "Manager agent processing failed")
            logger.error(f"Manager agent failed", extra={
                "tracking_id": tracking_id,
                "error": error_msg
            })
            raise Exception(f"AI processing failed: {error_msg}")
        
        # Classify response and get target webhook
        response_type = classify_response_type(manager_response, webhook_request["query"])
        target_webhook_url = get_target_webhook_url(response_type)
        
        if not target_webhook_url:
            logger.error(f"No webhook URL configured for response type: {response_type}", extra={
                "tracking_id": tracking_id,
                "response_type": response_type
            })
            # Continue without delivery rather than failing
            return {
                "success": True,
                "tracking_id": tracking_id,
                "message": f"Processing completed but no webhook configured for {response_type}"
            }
        
        # Format webhook payload
        processing_time_ms = int((time.time() - start_time) * 1000)
        webhook_payload = format_webhook_response(
            manager_response, response_type, tracking_id, processing_time_ms
        )
        
        # Queue outbound delivery
        delivery_id = queue_outbound_delivery(
            webhook_payload, target_webhook_url, tracking_id, response_type
        )
        
        logger.info(f"Webhook request processed successfully", extra={
            "tracking_id": tracking_id,
            "response_type": response_type,
            "delivery_id": delivery_id,
            "processing_time_ms": processing_time_ms
        })
        
        return {
            "success": True,
            "tracking_id": tracking_id,
            "delivery_id": delivery_id,
            "response_type": response_type,
            "processing_time_ms": processing_time_ms
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook request", extra={
            "tracking_id": tracking_id,
            "error": str(e)
        })
        return {
            "success": False,
            "tracking_id": tracking_id,
            "error": str(e)
        }

def process_outbound_delivery(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an outbound webhook delivery.
    
    Args:
        message: SQS message containing delivery request
        
    Returns:
        Delivery result
    """
    # Import the existing outbound delivery module
    try:
        from outbound_delivery import OutboundDeliveryHandler
        
        # Load config for the handler
        config = {
            "features": {
                "queue_processing": {
                    "enabled": True,
                    "retries": {
                        "max_attempts": message.get("max_attempts", 5),
                        "base_delay_seconds": 1,
                        "max_delay_seconds": 300,
                        "backoff_multiplier": 2,
                        "jitter": True
                    }
                }
            }
        }
        
        handler = OutboundDeliveryHandler(config)
        
        # Use existing delivery logic
        result = handler.deliver_webhook_with_retry(message)
        
        return {
            "success": result.get("success", False),
            "delivery_id": message.get("delivery_id"),
            "message": result.get("message", ""),
            "status_code": result.get("status_code")
        }
        
    except ImportError:
        logger.warning("OutboundDeliveryHandler not available, using simple delivery")
        return simple_webhook_delivery(message)
    except Exception as e:
        logger.error(f"Error in outbound delivery: {str(e)}")
        return {
            "success": False,
            "delivery_id": message.get("delivery_id"),
            "error": str(e)
        }

def simple_webhook_delivery(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple webhook delivery fallback.
    
    Args:
        message: Delivery message
        
    Returns:
        Delivery result
    """
    try:
        import requests
        
        delivery_id = message.get("delivery_id")
        target_url = message.get("target_webhook_url")
        payload = message.get("payload")
        
        logger.info(f"Delivering webhook", extra={
            "delivery_id": delivery_id,
            "target_url": target_url[:50] + "..." if len(target_url) > 50 else target_url
        })
        
        response = requests.post(
            target_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        success = 200 <= response.status_code < 300
        
        logger.info(f"Webhook delivery {'succeeded' if success else 'failed'}", extra={
            "delivery_id": delivery_id,
            "status_code": response.status_code,
            "response_size": len(response.text)
        })
        
        return {
            "success": success,
            "delivery_id": delivery_id,
            "status_code": response.status_code,
            "message": f"Delivery {'completed' if success else 'failed'}"
        }
        
    except Exception as e:
        logger.error(f"Simple webhook delivery failed", extra={
            "delivery_id": message.get("delivery_id"),
            "error": str(e)
        })
        return {
            "success": False,
            "delivery_id": message.get("delivery_id"),
            "error": str(e)
        }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Enhanced queue processor Lambda handler.
    Processes both webhook requests and outbound delivery.
    
    Args:
        event: Lambda event containing SQS records
        context: Lambda context object
        
    Returns:
        Processing results
    """
    logger.info("Queue processor starting", extra={
        "record_count": len(event.get("Records", []))
    })
    
    results = {
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'details': []
    }
    
    try:
        records = event.get('Records', [])
        
        for record in records:
            try:
                # Parse message body
                message_body = json.loads(record['body'])
                message_type = message_body.get('message_type', 'unknown')
                
                logger.info(f"Processing message", extra={
                    "message_type": message_type,
                    "record_id": record.get('messageId')
                })
                
                if message_type == 'webhook_processing_request':
                    # Process webhook request
                    result = process_webhook_request(message_body)
                elif message_type == 'outbound_delivery':
                    # Process outbound delivery
                    result = process_outbound_delivery(message_body)
                else:
                    logger.warning(f"Unknown message type: {message_type}")
                    result = {
                        "success": False,
                        "error": f"Unknown message type: {message_type}"
                    }
                
                results['processed'] += 1
                
                if result.get('success', False):
                    results['successful'] += 1
                    results['details'].append({
                        'message_type': message_type,
                        'status': 'success',
                        'tracking_id': result.get('tracking_id'),
                        'delivery_id': result.get('delivery_id')
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'message_type': message_type,
                        'status': 'failed',
                        'error': result.get('error'),
                        'tracking_id': result.get('tracking_id'),
                        'delivery_id': result.get('delivery_id')
                    })
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'status': 'failed',
                    'error': f'JSON parse error: {str(e)}'
                })
            except Exception as e:
                logger.error(f"Error processing record: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'status': 'failed',
                    'error': str(e)
                })
        
        logger.info("Queue processing completed", extra={
            "processed": results['processed'],
            "successful": results['successful'],
            "failed": results['failed']
        })
        
        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Queue processor error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Queue processor failed',
                'message': str(e)
            })
        }