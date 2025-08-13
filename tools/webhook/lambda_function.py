"""
RevOps AI Framework V2 - Consolidated Webhook Lambda

Unified webhook handler supporting three modes of operation:
1. Direct webhook invocation - Basic mode for simple webhook calls
2. SQS queue processing - For asynchronous webhook handling with retries
3. Bedrock Agent compatibility - For integration with AWS Bedrock Agents

Features:
- Configuration-driven with feature flags
- Support for named webhooks from configuration
- Support for direct webhook URLs
- Optional queue processing with retry logic
- Optional Bedrock Agent function calling format
- Optional payload enrichment
- Comprehensive logging and metrics

Environment Variables:
- WEBHOOK_CONFIG_PATH: Path to webhook configuration file
- WEBHOOK_URL_SECRET: AWS Secrets Manager secret for webhook URLs
- WEBHOOK_QUEUE_URL: SQS queue URL for async processing
- LOG_LEVEL: Logging level (default: INFO)
- WEBHOOK_RETRIES_ENABLED: Enable/disable retry logic
- WEBHOOK_MAX_RETRIES: Maximum retry attempts
- WEBHOOK_ENABLE_BEDROCK: Enable Bedrock Agent compatibility
"""

import json
import logging
import os
import traceback
from typing import Dict, Any, Optional, Union, List

# Import modules
from modules.core import CoreWebhookHandler
from modules.queue_processor import QueueProcessor
from modules.bedrock_adapter import BedrockAgentAdapter
from modules.outbound_delivery import OutboundDeliveryHandler

# Import utilities
from utils.config_loader import load_configuration
from utils.secret_manager import SecretManager

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

# Initialize secret manager
secret_manager = SecretManager()

def determine_execution_mode(event: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    Determine the execution mode based on event structure.
    
    Args:
        event: Lambda event
        config: Configuration dictionary
        
    Returns:
        Execution mode: 'bedrock_agent', 'sqs_message', 'outbound_delivery', or 'direct'
    """
    # Check if it's an outbound webhook delivery SQS event
    if is_outbound_delivery_event(event):
        return "outbound_delivery"
    
    # Initialize modules based on configuration
    bedrock_enabled = config.get("features", {}).get("bedrock_agent_compatibility", {}).get("enabled", False)
    queue_enabled = config.get("features", {}).get("queue_processing", {}).get("enabled", False)
    
    # Check if it's a Bedrock Agent function call
    if bedrock_enabled:
        bedrock_adapter = BedrockAgentAdapter(config)
        if bedrock_adapter.is_bedrock_request(event):
            return "bedrock_agent"
    
    # Check if it's an SQS message
    if queue_enabled:
        queue_processor = QueueProcessor(config)
        if queue_processor.is_sqs_event(event):
            return "sqs_message"
    
    # Default to direct invocation
    return "direct"

def is_outbound_delivery_event(event: Dict[str, Any]) -> bool:
    """
    Check if the event is an outbound webhook delivery SQS event.
    
    Args:
        event: Lambda event
        
    Returns:
        True if this is an outbound delivery event
    """
    # Check if it's an SQS event
    if 'Records' not in event or not isinstance(event['Records'], list):
        return False
    
    # Check if any record has the outbound delivery characteristics
    for record in event.get('Records', []):
        if record.get('eventSource') == 'aws:sqs':
            try:
                # Check message body for delivery_id (unique to outbound delivery)
                body = json.loads(record.get('body', '{}'))
                if 'delivery_id' in body and 'target_webhook_url' in body:
                    return True
            except (json.JSONDecodeError, KeyError):
                continue
    
    return False

def process_direct_request(event: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a direct webhook invocation.
    
    Args:
        event: Lambda event containing webhook request
        config: Configuration dictionary
        
    Returns:
        Response dictionary
    """
    # Initialize modules
    core_handler = CoreWebhookHandler(config)
    bedrock_enabled = config.get("features", {}).get("bedrock_agent_compatibility", {}).get("enabled", False)
    bedrock_adapter = BedrockAgentAdapter(config) if bedrock_enabled else None
    queue_enabled = config.get("features", {}).get("queue_processing", {}).get("enabled", False)
    queue_processor = QueueProcessor(config) if queue_enabled else None

    try:
        # Extract request data from event
        request_data = event
        if isinstance(event, dict) and 'body' in event:
            # Handle API Gateway proxy integration
            if isinstance(event['body'], str):
                request_data = json.loads(event['body'])
            else:
                request_data = event['body']
                
        # Validate request
        validation = core_handler.validate_webhook_request(request_data)
        if not validation["valid"]:
            error_response = {
                "success": False,
                "message": validation["error"]
            }
            
            # Format for Bedrock Agent if needed
            if bedrock_enabled and bedrock_adapter:
                return bedrock_adapter.format_bedrock_response(error_response, success=False)
                
            return error_response
            
        # Check if we should queue this request
        if queue_enabled and queue_processor and request_data.get("queue", False):
            queue_result = queue_processor.send_to_queue(request_data)
            
            # Format for Bedrock Agent if needed
            if bedrock_enabled and bedrock_adapter:
                return bedrock_adapter.format_bedrock_response(queue_result)
                
            return queue_result
            
        # Process the webhook directly
        webhook_name = request_data.get("webhook_name")
        webhook_url = request_data.get("webhook_url")
        
        # If webhook_url is from a secret, resolve it
        if webhook_url and webhook_url.startswith("secret:"):
            secret_name = webhook_url.replace("secret:", "", 1)
            webhook_url = secret_manager.get_webhook_url(secret_name)
            
        # Get payload and enrich if configured
        payload = request_data.get("payload", {})
        if bedrock_enabled and bedrock_adapter:
            context = request_data.get("_context", {})
            payload = bedrock_adapter.enrich_payload(payload, context)
            
        # Trigger webhook
        result = core_handler.trigger_webhook(
            webhook_name=webhook_name,
            webhook_url=webhook_url,
            payload=payload
        )
        
        # Format for Bedrock Agent if needed
        if bedrock_enabled and bedrock_adapter:
            return bedrock_adapter.format_bedrock_response(result, success=result["success"])
            
        return result
        
    except Exception as e:
        logger.error(f"Error processing direct request: {str(e)}")
        logger.error(traceback.format_exc())
        
        error_response = {
            "success": False,
            "message": f"Error processing webhook: {str(e)}"
        }
        
        # Format for Bedrock Agent if needed
        if bedrock_enabled and bedrock_adapter:
            return bedrock_adapter.format_bedrock_response(error_response, success=False)
            
        return error_response

def process_queue_message(event: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an SQS queue message.
    
    Args:
        event: SQS event with Records
        config: Configuration dictionary
        
    Returns:
        Processing results
    """
    # Initialize modules
    core_handler = CoreWebhookHandler(config)
    queue_processor = QueueProcessor(config)
    
    try:
        # Process queue messages
        results = queue_processor.process_queue_message(event)
        processed = []
        
        for result in results:
            if result["status"] == "processed":
                # Extract webhook request from queue message
                webhook_request = result["webhook_request"]
                
                # Validate request
                validation = core_handler.validate_webhook_request(webhook_request)
                if not validation["valid"]:
                    processed.append({
                        "record_id": result["record_id"],
                        "success": False,
                        "message": validation["error"]
                    })
                    continue
                    
                # Process the webhook
                webhook_name = webhook_request.get("webhook_name")
                webhook_url = webhook_request.get("webhook_url")
                payload = webhook_request.get("payload", {})
                
                # If webhook_url is from a secret, resolve it
                if webhook_url and webhook_url.startswith("secret:"):
                    secret_name = webhook_url.replace("secret:", "", 1)
                    webhook_url = secret_manager.get_webhook_url(secret_name)
                
                # Trigger webhook
                trigger_result = core_handler.trigger_webhook(
                    webhook_name=webhook_name,
                    webhook_url=webhook_url,
                    payload=payload
                )
                
                # Handle retry if needed
                if not trigger_result["success"]:
                    attempt = webhook_request.get("attempt", 1)
                    retry_config = config.get("features", {}).get("queue_processing", {}).get("retries", {})
                    max_attempts = retry_config.get("max_attempts", 3)
                    
                    if attempt < max_attempts:
                        retry_result = queue_processor.implement_retry(webhook_request)
                        trigger_result["retry"] = retry_result
                
                processed.append({
                    "record_id": result["record_id"],
                    "success": trigger_result["success"],
                    "message": trigger_result["message"],
                    "retry": trigger_result.get("retry", {})
                })
            else:
                # Pass through error results
                processed.append(result)
        
        return {
            "success": True,
            "message": f"Processed {len(processed)} messages",
            "results": processed
        }
        
    except Exception as e:
        logger.error(f"Error processing queue messages: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "success": False,
            "message": f"Error processing queue messages: {str(e)}"
        }

def process_bedrock_agent_request(event: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a Bedrock Agent function call.
    
    Args:
        event: Bedrock Agent function call event
        config: Configuration dictionary
        
    Returns:
        Response formatted for Bedrock Agent
    """
    # Initialize modules
    bedrock_adapter = BedrockAgentAdapter(config)
    
    try:
        # Parse Bedrock request into webhook request
        webhook_request = bedrock_adapter.parse_bedrock_request(event)
        
        # Process as direct request but ensure Bedrock formatting
        result = process_direct_request(webhook_request, config)
        
        # If result is already formatted for Bedrock Agent, return as is
        if isinstance(result, dict) and "messageVersion" in result:
            return result
            
        # Otherwise, format it
        return bedrock_adapter.format_bedrock_response(result, success=result.get("success", True))
        
    except Exception as e:
        logger.error(f"Error processing Bedrock Agent request: {str(e)}")
        logger.error(traceback.format_exc())
        
        error_response = {
            "success": False,
            "message": f"Error processing Bedrock Agent request: {str(e)}"
        }
        
        return bedrock_adapter.format_bedrock_response(error_response, success=False)

def process_outbound_delivery(event: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process outbound webhook delivery SQS messages.
    
    Args:
        event: SQS event with delivery Records
        config: Configuration dictionary
        
    Returns:
        Processing results
    """
    # Initialize outbound delivery handler
    outbound_handler = OutboundDeliveryHandler(config)
    
    try:
        # Process outbound delivery
        results = outbound_handler.process_outbound_delivery(event)
        
        successful_deliveries = sum(1 for r in results if r["success"])
        total_deliveries = len(results)
        
        logger.info(f"Outbound delivery batch completed", extra={
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": total_deliveries - successful_deliveries
        })
        
        return {
            "success": True,
            "message": f"Processed {total_deliveries} webhook deliveries",
            "results": results,
            "summary": {
                "total": total_deliveries,
                "successful": successful_deliveries,
                "failed": total_deliveries - successful_deliveries
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing outbound deliveries: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "success": False,
            "message": f"Error processing outbound deliveries: {str(e)}"
        }

def lambda_handler(event, context):
    """
    Unified webhook handler supporting direct invocation, SQS processing,
    and Bedrock Agent function calling format.
    
    Configuration-driven functionality with feature flags to enable/disable:
    - Queue processing
    - Retry logic
    - Payload enrichment
    - Bedrock Agent compatibility
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Response based on execution mode
    """
    try:
        # Initialize configuration
        config = load_configuration()
        
        # Set log level from configuration
        log_level = config.get("logging", {}).get("level", "INFO")
        logger.setLevel(log_level)
        
        # Log the event if in debug mode
        if log_level == "DEBUG":
            logger.debug(f"Event: {json.dumps(event)}")
        
        # Determine execution mode
        mode = determine_execution_mode(event, config)
        logger.info(f"Execution mode: {mode}")
        
        # Process according to mode
        if mode == "bedrock_agent":
            return process_bedrock_agent_request(event, config)
        elif mode == "outbound_delivery":
            return process_outbound_delivery(event, config)
        elif mode == "sqs_message":
            return process_queue_message(event, config)
        else:  # direct invocation
            return process_direct_request(event, config)
            
    except Exception as e:
        logger.error(f"Unhandled error in webhook lambda: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            "success": False,
            "message": f"Unhandled error in webhook lambda: {str(e)}"
        }
