"""
Simple Queue Processor for Webhook Gateway
Handles SQS messages from webhook gateway and processes them
"""

import json
import os
import boto3
import logging
import time
import uuid
import requests
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
lambda_client = boto3.client('lambda')

# Environment variables
MANAGER_AGENT_FUNCTION_NAME = os.environ.get('MANAGER_AGENT_FUNCTION_NAME', 'revops-manager-agent-wrapper')
DEAL_ANALYSIS_WEBHOOK_URL = os.environ.get('DEAL_ANALYSIS_WEBHOOK_URL', '')
DATA_ANALYSIS_WEBHOOK_URL = os.environ.get('DATA_ANALYSIS_WEBHOOK_URL', '')
LEAD_ANALYSIS_WEBHOOK_URL = os.environ.get('LEAD_ANALYSIS_WEBHOOK_URL', '')
GENERAL_WEBHOOK_URL = os.environ.get('GENERAL_WEBHOOK_URL', '')

def classify_response_type(response_text: str, query: str) -> str:
    """Classify the response to determine webhook routing."""
    response_lower = response_text.lower()
    query_lower = query.lower()
    
    # Deal analysis keywords
    deal_keywords = ['deal', 'opportunity', 'sales', 'close', 'pipeline', 'prospect', 'meddpicc', 'closing']
    if any(keyword in response_lower or keyword in query_lower for keyword in deal_keywords):
        return "deal_analysis"
    
    # Data analysis keywords  
    data_keywords = ['revenue', 'forecast', 'metrics', 'analytics', 'data', 'report', 'dashboard']
    if any(keyword in response_lower or keyword in query_lower for keyword in data_keywords):
        return "data_analysis"
    
    # Lead analysis keywords
    lead_keywords = ['lead', 'qualification', 'outreach', 'contact', 'prospect']
    if any(keyword in response_lower or keyword in query_lower for keyword in lead_keywords):
        return "lead_analysis"
    
    return "general"

def get_webhook_url(webhook_type: str) -> str:
    """Get the webhook URL for the specified type."""
    webhook_urls = {
        "deal_analysis": DEAL_ANALYSIS_WEBHOOK_URL,
        "data_analysis": DATA_ANALYSIS_WEBHOOK_URL,
        "lead_analysis": LEAD_ANALYSIS_WEBHOOK_URL,
        "general": GENERAL_WEBHOOK_URL
    }
    return webhook_urls.get(webhook_type, GENERAL_WEBHOOK_URL)

def invoke_manager_agent(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke the manager agent with the request."""
    try:
        logger.info(f"Invoking manager agent", extra={
            "function_name": MANAGER_AGENT_FUNCTION_NAME,
            "correlation_id": request_data.get("correlation_id")
        })
        
        # Invoke manager agent
        response = lambda_client.invoke(
            FunctionName=MANAGER_AGENT_FUNCTION_NAME,
            InvocationType='RequestResponse',
            Payload=json.dumps(request_data)
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        if response.get('FunctionError'):
            logger.error(f"Manager agent returned error: {payload}")
            return {
                "success": False,
                "error": f"Manager agent error: {payload.get('errorMessage', 'Unknown error')}",
                "details": payload
            }
        
        logger.info(f"Manager agent response received", extra={
            "success": payload.get("success", False),
            "response_length": len(payload.get("response", ""))
        })
        
        return payload
        
    except Exception as e:
        logger.error(f"Error invoking manager agent: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to invoke manager agent: {str(e)}"
        }

def deliver_webhook(webhook_url: str, payload: Dict[str, Any], tracking_id: str) -> bool:
    """Deliver payload to webhook URL."""
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Source': 'revops-ai-framework',
            'X-Tracking-ID': tracking_id
        }
        
        logger.info(f"Delivering webhook", extra={
            "webhook_url": webhook_url[:50] + "..." if len(webhook_url) > 50 else webhook_url,
            "tracking_id": tracking_id,
            "payload_size": len(json.dumps(payload))
        })
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        success = response.status_code in [200, 201, 202]
        
        logger.info(f"Webhook delivery result", extra={
            "tracking_id": tracking_id,
            "status_code": response.status_code,
            "success": success,
            "response_size": len(response.text)
        })
        
        return success
        
    except Exception as e:
        logger.error(f"Webhook delivery failed", extra={
            "tracking_id": tracking_id,
            "webhook_url": webhook_url[:50] + "..." if len(webhook_url) > 50 else webhook_url,
            "error": str(e)
        })
        return False

def process_webhook_message(message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single webhook message."""
    tracking_id = message_body.get("tracking_id", str(uuid.uuid4()))
    
    try:
        logger.info(f"Processing webhook message", extra={
            "tracking_id": tracking_id,
            "message_type": message_body.get("message_type")
        })
        
        # Extract webhook request
        webhook_request = message_body.get("webhook_request", {})
        
        # Prepare manager agent request
        manager_request = {
            "query": webhook_request.get("query", ""),
            "correlation_id": tracking_id,
            "webhook_metadata": {
                "source_system": webhook_request.get("source_system", "webhook"),
                "source_process": webhook_request.get("source_process", "api"),
                "timestamp": webhook_request.get("timestamp")
            }
        }
        
        # Invoke manager agent
        agent_response = invoke_manager_agent(manager_request)
        
        if not agent_response.get("success", False):
            logger.error(f"Manager agent failed", extra={
                "tracking_id": tracking_id,
                "error": agent_response.get("error")
            })
            return {
                "success": False,
                "tracking_id": tracking_id,
                "error": "Manager agent processing failed",
                "details": agent_response
            }
        
        # Classify response for webhook routing
        response_text = agent_response.get("response", "")
        webhook_type = classify_response_type(response_text, webhook_request.get("query", ""))
        webhook_url = get_webhook_url(webhook_type)
        
        # Prepare webhook payload
        webhook_payload = {
            "tracking_id": tracking_id,
            "source_system": webhook_request.get("source_system"),
            "source_process": webhook_request.get("source_process"),
            "original_query": webhook_request.get("query"),
            "ai_response": {
                "response": response_text,
                "session_id": agent_response.get("sessionId"),
                "timestamp": agent_response.get("timestamp"),
                "classification": webhook_type
            },
            "webhook_metadata": {
                "delivered_at": datetime.now(timezone.utc).isoformat(),
                "webhook_type": webhook_type,
                "webhook_url": webhook_url
            }
        }
        
        # Deliver webhook
        delivery_success = deliver_webhook(webhook_url, webhook_payload, tracking_id)
        
        result = {
            "success": delivery_success,
            "tracking_id": tracking_id,
            "webhook_type": webhook_type,
            "webhook_url": webhook_url,
            "delivery_success": delivery_success
        }
        
        if delivery_success:
            logger.info(f"Webhook processing completed successfully", extra=result)
        else:
            logger.error(f"Webhook delivery failed", extra=result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing webhook message", extra={
            "tracking_id": tracking_id,
            "error": str(e)
        })
        return {
            "success": False,
            "tracking_id": tracking_id,
            "error": f"Processing error: {str(e)}"
        }

def lambda_handler(event, context):
    """Main Lambda handler for SQS messages."""
    
    logger.info(f"Queue processor invoked", extra={
        "records_count": len(event.get("Records", []))
    })
    
    results = []
    
    for record in event.get("Records", []):
        try:
            # Parse SQS message
            message_body = json.loads(record["body"])
            
            # Process the message
            result = process_webhook_message(message_body)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing SQS record: {str(e)}")
            results.append({
                "success": False,
                "error": f"Record processing error: {str(e)}"
            })
    
    # Return results
    success_count = sum(1 for r in results if r.get("success", False))
    total_count = len(results)
    
    logger.info(f"Queue processing completed", extra={
        "total_records": total_count,
        "successful": success_count,
        "failed": total_count - success_count
    })
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "processed": total_count,
            "successful": success_count,
            "failed": total_count - success_count,
            "results": results
        })
    }