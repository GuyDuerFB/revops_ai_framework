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
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
lambda_client = boto3.client('lambda')

# Environment variables
MANAGER_AGENT_FUNCTION_NAME = os.environ.get('MANAGER_AGENT_FUNCTION_NAME', 'revops-manager-agent-wrapper')
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
S3_BUCKET = os.environ.get('S3_BUCKET', 'revops-ai-framework-kb-740202120544')

def convert_markdown_to_plain_text(markdown_text: str) -> str:
    """Convert markdown text to plain text."""
    if not markdown_text:
        return ""
    
    # Remove markdown formatting
    text = markdown_text
    
    # Remove bold/italic markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'__(.*?)__', r'\1', text)      # Bold alternative
    text = re.sub(r'_(.*?)_', r'\1', text)        # Italic alternative
    
    # Remove headers
    text = re.sub(r'^#+\s*(.*)$', r'\1', text, flags=re.MULTILINE)
    
    # Remove links - keep the text, remove the markdown
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove code blocks
    text = re.sub(r'```[^\n]*\n(.*?)\n```', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Inline code
    
    # Remove list markers
    text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Remove extra blank lines
    text = text.strip()
    
    return text

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

def deliver_webhook(payload: Dict[str, Any], tracking_id: str) -> bool:
    """Deliver payload to webhook URL."""
    if not WEBHOOK_URL:
        logger.error(f"No webhook URL configured", extra={"tracking_id": tracking_id})
        return False
        
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Source': 'revops-ai-framework',
            'X-Tracking-ID': tracking_id
        }
        
        logger.info(f"Delivering webhook", extra={
            "webhook_url": WEBHOOK_URL[:50] + "..." if len(WEBHOOK_URL) > 50 else WEBHOOK_URL,
            "tracking_id": tracking_id,
            "payload_size": len(json.dumps(payload))
        })
        
        response = requests.post(
            WEBHOOK_URL,
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
            "webhook_url": WEBHOOK_URL[:50] + "..." if len(WEBHOOK_URL) > 50 else WEBHOOK_URL,
            "error": str(e)
        })
        return False

def process_webhook_message(message_body: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single webhook message."""
    tracking_id = message_body.get("tracking_id", str(uuid.uuid4()))
    start_time = time.time()
    
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
        
        # Get response text and create plain text version
        response_text = agent_response.get("response", "")
        response_plain = convert_markdown_to_plain_text(response_text)
        
        # Prepare webhook payload
        webhook_payload = {
            "tracking_id": tracking_id,
            "source_system": webhook_request.get("source_system"),
            "source_process": webhook_request.get("source_process"),
            "original_query": webhook_request.get("query"),
            "ai_response": {
                "response": response_text,
                "response_plain": response_plain,
                "session_id": agent_response.get("sessionId"),
                "timestamp": agent_response.get("timestamp")
            },
            "webhook_metadata": {
                "delivered_at": datetime.now(timezone.utc).isoformat(),
                "webhook_url": WEBHOOK_URL
            }
        }
        
        # Deliver webhook
        delivery_success = deliver_webhook(webhook_payload, tracking_id)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Export conversation to S3 with enhanced monitoring
        try:
            from simple_s3_exporter import SimpleS3Exporter
            
            s3_bucket = S3_BUCKET
            exporter = SimpleS3Exporter(s3_bucket)
            
            s3_path = exporter.export_webhook_conversation(
                webhook_request=webhook_request,
                agent_response=agent_response,
                tracking_id=tracking_id,
                processing_time_ms=processing_time_ms
            )
            
            logger.info(f"Webhook conversation exported to S3", extra={
                "tracking_id": tracking_id,
                "s3_path": s3_path,
                "processing_time_ms": processing_time_ms
            })
            
        except Exception as e:
            logger.error(f"Failed to export webhook conversation to S3", extra={
                "tracking_id": tracking_id,
                "error": str(e)
            })
        
        result = {
            "success": delivery_success,
            "tracking_id": tracking_id,
            "webhook_url": WEBHOOK_URL,
            "delivery_success": delivery_success,
            "processing_time_ms": processing_time_ms
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