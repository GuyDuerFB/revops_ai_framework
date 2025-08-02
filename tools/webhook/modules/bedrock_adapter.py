"""
RevOps AI Framework V2 - Bedrock Agent Adapter Module

AWS Bedrock Agent function calling format compatibility layer.
Handles parsing requests and formatting responses according to
Bedrock Agent function specifications.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union, List

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

class BedrockAgentAdapter:
    """
    Adapter for AWS Bedrock Agent function calling format.
    Handles request parsing, response formatting, and payload enrichment.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Bedrock Agent adapter.
        
        Args:
            config: Configuration dictionary with Bedrock settings
        """
        self.config = config
        self.bedrock_config = config.get("features", {}).get("bedrock_agent_compatibility", {})
        self.enrichment_config = config.get("features", {}).get("payload_enrichment", {})
        
    def is_bedrock_request(self, event: Dict[str, Any]) -> bool:
        """
        Check if an event is from a Bedrock Agent function call.
        
        Args:
            event: Event to check
            
        Returns:
            True if the event is a Bedrock Agent function call, False otherwise
        """
        # Bedrock Agent function calls have a specific structure
        return (
            isinstance(event, dict) and
            "messageVersion" in event and
            "name" in event.get("action", {})
        )
        
    def parse_bedrock_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Bedrock Agent function calling format request.
        
        Args:
            event: Bedrock Agent function call event
            
        Returns:
            Parsed webhook request
        """
        # Extract function details
        action = event.get("action", {})
        function_name = action.get("name", "")
        parameters = action.get("parameters", [])
        
        # Convert parameters array to dictionary
        webhook_request = {}
        for param in parameters:
            webhook_request[param.get("name")] = param.get("value")
            
        # Add request context for tracking
        webhook_request["_context"] = {
            "source": "bedrock_agent",
            "function_name": function_name,
            "request_id": event.get("requestId", str(uuid.uuid4()))
        }
        
        return webhook_request
        
    def format_bedrock_response(self, result: Dict[str, Any], success: bool = True) -> Dict[str, Any]:
        """
        Format a response in Bedrock Agent function calling format.
        
        Args:
            result: Webhook execution result
            success: Whether the function execution was successful
            
        Returns:
            Response formatted for Bedrock Agent
        """
        # Prepare response according to Bedrock Agent format
        response = {
            "messageVersion": "1.0",
            "response": {
                "actionGroup": "webhook",
                "apiPath": "trigger"
            }
        }
        
        if success:
            # Success response
            response["response"]["httpStatus"] = 200
            response["response"]["responseBody"] = {
                "application/json": {
                    "success": True,
                    "message": result.get("message", "Webhook triggered successfully"),
                    "status_code": result.get("status_code"),
                    "data": result
                }
            }
        else:
            # Error response
            response["response"]["httpStatus"] = 400
            response["response"]["responseBody"] = {
                "application/json": {
                    "success": False,
                    "error": result.get("message", "Webhook execution failed"),
                    "details": result
                }
            }
            
        return response
        
    def enrich_payload(self, payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enrich webhook payload with additional metadata.
        
        Args:
            payload: Original payload to enrich
            context: Optional execution context information
            
        Returns:
            Enriched payload
        """
        # Skip enrichment if not enabled
        if not self.enrichment_config.get("enabled", True):
            return payload
            
        # Create a copy to avoid modifying the original
        enriched = payload.copy() if payload else {}
        
        # Add timestamp if configured
        if self.enrichment_config.get("add_timestamp", True):
            timestamp = datetime.utcnow().isoformat() + "Z"
            enriched["_timestamp"] = timestamp
            
        # Add request ID if configured
        if self.enrichment_config.get("add_request_id", True):
            request_id = str(uuid.uuid4())
            if context and "request_id" in context:
                request_id = context["request_id"]
            enriched["_request_id"] = request_id
            
        # Add context information if configured
        if self.enrichment_config.get("add_context", True) and context:
            enriched["_context"] = context
            
        return enriched
