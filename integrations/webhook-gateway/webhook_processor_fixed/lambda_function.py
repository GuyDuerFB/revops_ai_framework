"""
Simplified Queue Processor for Webhook Gateway
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
    """Transform webhook request to manager agent format."""
    correlation_id = str(uuid.uuid4())
    
    return {
        "query": webhook_request["query"],
        "correlation_id": correlation_id,
        "webhook_metadata": {
            "source_system": webhook_request.get("source_system", "webhook"),
            "source_process": webhook_request.get("source_process", "api"),
            "original_timestamp": webhook_request.get("timestamp"),
            "webhook_timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

def invoke_manager_agent(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke the manager agent with transformed request."""
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
    """Classify the response to determine webhook type."""
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
    
    return 'general'

def get_target_webhook_url(response_type: str) -> Optional[str]:
    """Get target webhook URL based on response type."""
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
    """Format the response for webhook delivery."""
    response_text = (
        manager_response.get("response") or
        manager_response.get("result") or
        manager_response.get("message") or
        str(manager_response)
    )
    
    return {
        "header": response_type,
        "response_rich": response_text,
        "response_plain": response_text,
        "agents_used": ["ManagerAgent"],
        "metadata": {
            "tracking_id": tracking_id,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_system": "revops_ai_framework",
            "source_process": "webhook_gateway"
        }
    }

def simple_webhook_delivery(target_url: str, payload: Dict[str, Any], delivery_id: str) -> Dict[str, Any]:
    """Simple webhook delivery."""
    try:
        import requests
        
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
        logger.error(f"Webhook delivery failed", extra={
            "delivery_id": delivery_id,
            "error": str(e)
        })
        return {
            "success": False,
            "delivery_id": delivery_id,
            "error": str(e)
        }

def process_webhook_request(message: Dict[str, Any]) -> Dict[str, Any]:
    """Process a webhook request by invoking the manager agent."""
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
        
        # Deliver webhook directly
        delivery_id = str(uuid.uuid4())
        delivery_result = simple_webhook_delivery(target_webhook_url, webhook_payload, delivery_id)
        
        logger.info(f"Webhook request processed successfully", extra={
            "tracking_id": tracking_id,
            "response_type": response_type,
            "delivery_id": delivery_id,
            "delivery_success": delivery_result.get("success", False),
            "processing_time_ms": processing_time_ms
        })
        
        return {
            "success": True,
            "tracking_id": tracking_id,
            "delivery_id": delivery_id,
            "response_type": response_type,
            "processing_time_ms": processing_time_ms,
            "delivery_success": delivery_result.get("success", False)
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

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Enhanced queue processor Lambda handler."""
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
                    result = process_webhook_request(message_body)
                elif message_type == 'outbound_delivery':
                    # Handle outbound delivery if needed
                    delivery_id = message_body.get("delivery_id")
                    target_url = message_body.get("target_webhook_url")
                    payload = message_body.get("payload")
                    result = simple_webhook_delivery(target_url, payload, delivery_id)
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