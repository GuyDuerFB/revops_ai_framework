"""
RevOps AI Framework V2 - Webhook Handler

This module provides functionality to trigger webhook endpoints for notifications and integrations.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional


def load_webhook_config(config_file: str) -> Dict[str, Dict[str, Any]]:
    """
    Load webhook configuration from a JSON file.
    
    Args:
        config_file: Path to the webhook configuration file
        
    Returns:
        Dictionary of webhook configurations indexed by webhook name
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        JSONDecodeError: If the config file contains invalid JSON
    """
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Webhook configuration file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        return json.load(f)


def validate_webhook_payload(payload: Any) -> bool:
    """
    Validate webhook payload data.
    
    Args:
        payload: The payload to validate
        
    Returns:
        True if the payload is valid
        
    Raises:
        ValueError: If the payload is invalid
    """
    if payload is None:
        raise ValueError("Webhook payload cannot be None")
    
    if not isinstance(payload, dict):
        raise ValueError("Webhook payload must be a dictionary")
    
    return True


def format_webhook_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format webhook response for the caller.
    
    Args:
        response: The raw webhook response data
        
    Returns:
        Formatted response with status, response_code, and error if applicable
    """
    if response.get("status_code", 0) >= 400 or "error" in response:
        return {
            "status": "error",
            "response_code": response.get("status_code", 500),
            "response_body": response.get("body", ""),
            "error": response.get("error", "Unknown error")
        }
    
    return {
        "status": "success",
        "response_code": response.get("status_code", 200),
        "response_body": response.get("body", "")
    }


class WebhookHandler:
    """
    Handler for managing and triggering various webhook endpoints.
    """
    
    def __init__(self, config: Dict[str, Dict[str, Any]] = None, config_file: str = None):
        """
        Initialize the webhook handler.
        
        Args:
            config: Dictionary containing webhook configurations
            config_file: Path to a webhook configuration file
            
        Note:
            If both config and config_file are provided, config takes precedence.
            If neither is provided, an empty configuration is used.
        """
        if config is not None:
            self.webhooks = config
        elif config_file is not None:
            self.webhooks = load_webhook_config(config_file)
        else:
            self.webhooks = {}
    
    def trigger_webhook_by_url(
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Trigger a webhook by directly providing the URL and payload.
        
        Args:
            url: The webhook URL to call
            payload: The data to send in the webhook
            headers: Optional HTTP headers to include
            
        Returns:
            Response data with status and any error information
        """
        if not url:
            return {"status": "error", "error": "URL is required"}
        
        try:
            # Validate payload
            validate_webhook_payload(payload)
            
            # Use empty dict if headers not provided
            headers = headers or {}
            
            # Make the request
            response = requests.post(url=url, json=payload, headers=headers)
            
            # Prepare response data
            response_data = {
                "status_code": response.status_code,
                "body": response.text,
            }
            
            # Add error information if the request failed
            if response.status_code >= 400:
                response_data["error"] = f"Request failed with status {response.status_code}: {response.reason}"
            
            return format_webhook_response(response_data)
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to trigger webhook: {str(e)}"
            }
    
    def trigger_named_webhook(self, webhook_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a predefined webhook using its name from the configuration.
        
        Args:
            webhook_name: Name of the webhook as defined in the configuration
            payload: The data to send in the webhook
            
        Returns:
            Response data with status and any error information
        """
        if webhook_name not in self.webhooks:
            return {"status": "error", "error": f"Webhook '{webhook_name}' not found"}
        
        webhook_config = self.webhooks[webhook_name]
        url = webhook_config.get("url")
        headers = webhook_config.get("headers", {})
        
        return self.trigger_webhook_by_url(url, payload, headers)
    
    def list_available_webhooks(self) -> List[str]:
        """
        List all available webhook names in the configuration.
        
        Returns:
            List of webhook names
        """
        return list(self.webhooks.keys())
