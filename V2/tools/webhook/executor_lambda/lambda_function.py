"""
RevOps AI Framework V2 - Webhook Executor Lambda

This Lambda function executes webhooks to integrate with external systems like Zapier.
It supports predefined webhooks from configuration as well as direct URL calls.
Compatible with AWS Bedrock Agent function calling format.
"""

import json
import boto3
import os
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Load webhook configuration
def load_webhook_config(bucket: Optional[str] = None, key: Optional[str] = None) -> Dict[str, Any]:
    """
    Load webhook configuration either from S3 or from local file.
    
    Args:
        bucket (Optional[str]): S3 bucket name
        key (Optional[str]): S3 object key
        
    Returns:
        Dict[str, Any]: Webhook configuration dictionary
    """
    try:
        # Try to load from S3 if bucket and key are provided
        if bucket and key:
            s3 = boto3.client('s3')
            response = s3.get_object(Bucket=bucket, Key=key)
            config_content = response['Body'].read().decode('utf-8')
            return json.loads(config_content)
        
        # Otherwise, try to load from environment variable
        config_path = os.environ.get('WEBHOOK_CONFIG_PATH')
        if config_path:
            with open(config_path, 'r') as f:
                return json.loads(f.read())
                
        # Default configuration if none found
        return {
            "webhooks": {
                "zapier_default": {
                    "url": os.environ.get('ZAPIER_WEBHOOK_URL', ''),
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "description": "Default Zapier webhook"
                }
            }
        }
        
    except Exception as e:
        print(f"Error loading webhook config: {str(e)}")
        # Return empty config on error
        return {"webhooks": {}}

# Secret management for webhook credentials
def get_aws_secret(secret_name: str, region_name: str = "us-east-1") -> Dict[str, str]:
    """
    Retrieve a secret from AWS Secrets Manager.
    
    Args:
        secret_name (str): Name of the secret
        region_name (str): AWS region where the secret is stored
        
    Returns:
        Dict[str, str]: Dictionary containing the secret key-value pairs
    """
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        raise Exception(f"Failed to retrieve secret {secret_name}: {str(e)}")
    
    if 'SecretString' in get_secret_value_response:
        return json.loads(get_secret_value_response['SecretString'])
    else:
        raise Exception("Secret is not in string format")

def enrich_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich webhook payload with additional metadata.
    
    Args:
        payload (Dict[str, Any]): Original payload
        
    Returns:
        Dict[str, Any]: Enriched payload
    """
    # Create a copy to avoid modifying the original
    enriched = payload.copy()
    
    # Add metadata if it doesn't exist
    if '_metadata' not in enriched:
        enriched['_metadata'] = {}
    
    # Add timestamp
    enriched['_metadata']['timestamp'] = datetime.utcnow().isoformat()
    
    # Add source identifier
    enriched['_metadata']['source'] = "revops_ai_framework_v2"
    
    return enriched

# Webhook execution
def execute_webhook(
    webhook_config: Dict[str, Any],
    payload: Dict[str, Any],
    additional_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Execute a webhook with the provided configuration and payload.
    
    Args:
        webhook_config (Dict[str, Any]): Webhook configuration
        payload (Dict[str, Any]): Payload to send
        additional_headers (Optional[Dict[str, str]]): Additional headers to include
        
    Returns:
        Dict[str, Any]: Webhook execution result
    """
    url = webhook_config.get('url')
    if not url:
        return {
            "success": False,
            "error": "Missing URL in webhook configuration"
        }
    
    # Get method or default to POST
    method = webhook_config.get('method', 'POST')
    
    # Combine base headers with additional headers
    headers = webhook_config.get('headers', {})
    if additional_headers:
        headers.update(additional_headers)
    
    # Ensure Content-Type if not specified
    if 'Content-Type' not in headers:
        headers['Content-Type'] = 'application/json'
    
    # Prepare data
    data = json.dumps(payload).encode('utf-8')
    
    # Create request
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )
    
    try:
        # Execute webhook
        with urllib.request.urlopen(req) as response:
            response_content = response.read().decode('utf-8')
            
            # Try to parse JSON response if possible
            try:
                response_data = json.loads(response_content)
            except json.JSONDecodeError:
                response_data = response_content
            
        # Return success response
        return {
            "success": True,
            "status_code": response.status,
            "response": response_data
        }
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_json = json.loads(error_body)
        except json.JSONDecodeError:
            error_json = {"raw_error": error_body}
            
        return {
            "success": False,
            "status_code": e.code,
            "error": f"HTTP Error: {e.code}",
            "response": error_json
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 0
        }

# Main function
def trigger_webhook(
    webhook_name: Optional[str] = None,
    url: Optional[str] = None,
    payload: Dict[str, Any] = None,
    headers: Optional[Dict[str, str]] = None,
    method: str = 'POST'
) -> Dict[str, Any]:
    """
    Trigger a webhook either by name (from config) or by direct URL.
    Matches the Bedrock Agent function schema signature.
    
    Args:
        webhook_name (Optional[str]): Name of predefined webhook
        url (Optional[str]): Direct webhook URL if not using predefined webhook
        payload (Dict[str, Any]): JSON payload to send
        headers (Optional[Dict[str, str]]): Additional headers
        method (str): HTTP method to use (default: POST)
        
    Returns:
        Dict[str, Any]: Webhook execution result
    """
    try:
        # Validate that we have either webhook_name or direct URL
        if not webhook_name and not url:
            return {
                "success": False,
                "error": "Either webhook_name or url must be provided"
            }
        
        # Ensure we have a payload
        if not payload:
            return {
                "success": False,
                "error": "Payload is required"
            }
        
        # Load webhook configuration
        webhook_config = load_webhook_config()
        
        # If webhook_name provided, look up in config
        if webhook_name:
            if webhook_name not in webhook_config.get('webhooks', {}):
                return {
                    "success": False,
                    "error": f"Webhook '{webhook_name}' not found in configuration"
                }
            
            # Use configuration from webhook config
            webhook_def = webhook_config['webhooks'][webhook_name]
        else:
            # Create configuration from provided parameters
            webhook_def = {
                "url": url,
                "method": method,
                "headers": headers or {}
            }
        
        # Enrich payload with metadata
        enriched_payload = enrich_payload(payload)
        
        # Execute the webhook
        result = execute_webhook(webhook_def, enriched_payload, headers)
        
        # Add request details to the result for tracking
        result["request"] = {
            "webhook_name": webhook_name,
            "url": webhook_def.get('url', url),
            "method": webhook_def.get('method', method),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return result
        
    except Exception as e:
        print(f"Error in trigger_webhook: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to trigger webhook"
        }

def lambda_handler(event, context):
    """
    AWS Lambda handler for webhook execution.
    Compatible with Bedrock Agent function calling format.
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Handle Bedrock Agent invocation
        if 'actionGroup' in event and event.get('actionGroup') == 'webhook_executor':
            action_name = event.get('action')
            
            if action_name == 'trigger_webhook':
                body = event.get('body', {})
                parameters = body.get('parameters', {})
                
                # Extract parameters
                webhook_name = parameters.get('webhook_name')
                url = parameters.get('url')
                payload = parameters.get('payload', {})
                headers = parameters.get('headers')
                method = parameters.get('method', 'POST')
                
                # Call our function
                return trigger_webhook(webhook_name, url, payload, headers, method)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action_name}",
                    "message": "This Lambda only supports the 'trigger_webhook' action."
                }
                
        # Handle direct invocation
        elif 'payload' in event:
            # Direct Lambda invocation
            webhook_name = event.get('webhook_name')
            url = event.get('url')
            payload = event.get('payload', {})
            headers = event.get('headers')
            method = event.get('method', 'POST')
            
            return trigger_webhook(webhook_name, url, payload, headers, method)
            
        # Legacy parameter format for backward compatibility
        elif 'parameters' in event and isinstance(event['parameters'], list):
            params = {param.get('name'): param.get('value') for param in event['parameters']}
            webhook_name = params.get('webhook_name')
            url = params.get('url')
            payload = params.get('payload', {})
            headers = params.get('headers')
            method = params.get('method', 'POST')
            
            return trigger_webhook(webhook_name, url, payload, headers, method)
        
        # No recognizable format
        else:
            return {
                'success': False,
                'error': 'Invalid request format',
                'message': 'Request format not recognized. Please provide webhook name or URL and payload.'
            }
            
    except Exception as e:
        # Log the full error for debugging
        print(f"Lambda handler error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Return error response
        return {
            'success': False,
            'error': str(e),
            'message': 'An error occurred processing the webhook request'
        }
