"""
RevOps AI Framework V2 - Core Webhook Handler Module

Core webhook functionality shared across all modes (direct invocation,
SQS queue processing, and Bedrock Agent integration).
"""

import json
import os
import logging
import requests
from typing import Dict, Any, Optional, Union, List

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

class CoreWebhookHandler:
    """
    Core webhook functionality shared across all execution modes.
    Handles loading webhook configurations, validating requests,
    and triggering webhooks either by name or direct URL.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the core webhook handler.
        
        Args:
            config: Configuration dictionary with webhook settings
        """
        self.config = config
        self.webhook_config_path = config.get("webhooks", {}).get("path", 
                                             os.environ.get("WEBHOOK_CONFIG_PATH"))
        self.allow_direct_url = config.get("webhooks", {}).get("allow_direct_url", True)
        self.webhooks = self._load_webhooks()
    
    def _load_webhooks(self) -> Dict[str, Any]:
        """
        Load webhook configurations from the specified file path.
        
        Returns:
            Dict containing webhook configurations
        """
        if not self.webhook_config_path:
            logger.warning("No webhook configuration path specified")
            return {}
            
        try:
            with open(self.webhook_config_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading webhook config: {str(e)}")
            return {}
    
    def validate_webhook_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate incoming webhook request.
        
        Args:
            request_data: Request data to validate
            
        Returns:
            Dict with validation result and optional error message
        """
        result = {"valid": True, "error": None}
        
        # Validate webhook name or URL is present
        if "webhook_name" not in request_data and "webhook_url" not in request_data:
            result["valid"] = False
            result["error"] = "Missing required parameter: webhook_name or webhook_url"
            return result
            
        # If using webhook_name, validate it exists
        if "webhook_name" in request_data:
            webhook_name = request_data["webhook_name"]
            if webhook_name not in self.webhooks:
                result["valid"] = False
                result["error"] = f"Webhook not found: {webhook_name}"
                return result
                
        # If using webhook_url, validate direct URL is allowed
        if "webhook_url" in request_data and not self.allow_direct_url:
            result["valid"] = False
            result["error"] = "Direct webhook URLs are not allowed"
            return result
            
        # Validate payload if present
        if "payload" in request_data and not isinstance(request_data["payload"], dict):
            result["valid"] = False
            result["error"] = "Payload must be a valid JSON object"
            
        return result
    
    def trigger_webhook(self, webhook_name: Optional[str] = None, 
                      webhook_url: Optional[str] = None, 
                      payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Trigger webhook by name or direct URL.
        
        Args:
            webhook_name: Name of the webhook to trigger (from config)
            webhook_url: Direct webhook URL to call
            payload: Data payload to include in the request
            
        Returns:
            Dict with webhook call results
        """
        # Use empty dict if payload is None
        if payload is None:
            payload = {}
            
        # Get URL either from config or direct parameter
        url = None
        headers = {}
        method = "POST"
        
        if webhook_name:
            if webhook_name not in self.webhooks:
                return {
                    "success": False,
                    "status_code": None,
                    "message": f"Webhook not found: {webhook_name}",
                    "response": None
                }
                
            webhook_config = self.webhooks[webhook_name]
            url = webhook_config.get("url")
            headers = webhook_config.get("headers", {})
            method = webhook_config.get("method", "POST").upper()
            
        elif webhook_url:
            if not self.allow_direct_url:
                return {
                    "success": False,
                    "status_code": None,
                    "message": "Direct webhook URLs are not allowed",
                    "response": None
                }
                
            url = webhook_url
        
        if not url:
            return {
                "success": False,
                "status_code": None,
                "message": "No webhook URL specified",
                "response": None
            }
            
        try:
            # Make HTTP request based on configured method
            if method == "GET":
                response = requests.get(url, params=payload, headers=headers)
            else:
                response = requests.post(url, json=payload, headers=headers)
                
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "Webhook triggered successfully",
                "response": response.text
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error triggering webhook: {str(e)}")
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
            
            return {
                "success": False,
                "status_code": status_code,
                "message": f"Error triggering webhook: {str(e)}",
                "response": e.response.text if hasattr(e, 'response') and e.response else None
            }
