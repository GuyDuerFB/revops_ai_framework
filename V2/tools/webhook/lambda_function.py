"""
RevOps AI Framework V2 - Webhook Lambda Handler

This module provides the AWS Lambda handler for webhook integration.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

from .webhook_handler import WebhookHandler

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get webhook configuration file from environment variable or use default path
WEBHOOK_CONFIG_PATH = os.environ.get("WEBHOOK_CONFIG_PATH", "/opt/webhooks.json")


def validate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize the incoming Lambda event.
    
    Args:
        event: The Lambda event object
        
    Returns:
        Normalized event data
        
    Raises:
        ValueError: If the event is invalid
    """
    # Check if we have a valid payload
    payload = event.get("payload")
    if not payload:
        raise ValueError("Event must include a 'payload' field")
    
    # Check if we have either a URL or a webhook name
    url = event.get("url")
    webhook_name = event.get("webhook_name")
    
    if not url and not webhook_name:
        raise ValueError("Either 'url' or 'webhook_name' must be provided")
    
    return event


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for webhook invocation.
    
    Args:
        event: Lambda event dictionary with webhook details:
              - url: Direct webhook URL (optional if webhook_name provided)
              - webhook_name: Name of predefined webhook (optional if url provided)
              - payload: Data to send to webhook (required)
              - headers: HTTP headers to include (optional, only used with url)
        context: Lambda context object
        
    Returns:
        Dictionary with status and response/error information
    """
    try:
        # Log the incoming event
        logger.info(f"Received webhook event: {json.dumps(event, default=str)}")
        
        # Validate the event
        event = validate_event(event)
        
        # Extract parameters
        url = event.get("url")
        webhook_name = event.get("webhook_name")
        payload = event.get("payload", {})
        headers = event.get("headers", {})
        config_path = event.get("webhook_config_path", WEBHOOK_CONFIG_PATH)
        
        # Initialize the webhook handler
        webhook_handler = WebhookHandler(config_file=config_path)
        
        # Invoke the appropriate webhook method based on the provided parameters
        if url:
            logger.info(f"Triggering webhook by URL: {url}")
            response = webhook_handler.trigger_webhook_by_url(url, payload, headers)
        else:
            logger.info(f"Triggering named webhook: {webhook_name}")
            response = webhook_handler.trigger_named_webhook(webhook_name, payload)
        
        logger.info(f"Webhook response: {json.dumps(response, default=str)}")
        return response
        
    except Exception as e:
        logger.error(f"Error in webhook lambda: {str(e)}")
        return {
            "status": "error",
            "error": f"Webhook lambda error: {str(e)}"
        }
