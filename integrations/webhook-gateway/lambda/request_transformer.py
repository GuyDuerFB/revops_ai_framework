"""
Webhook Gateway - Request Transformer
Transforms inbound webhook requests to manager agent format
"""

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def validate_webhook_request(event: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate incoming webhook request format.
    
    Args:
        event: Lambda event containing webhook request
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Parse body if it's a string (API Gateway format)
        if isinstance(event.get('body'), str):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                return False, "Invalid JSON in request body"
        else:
            body = event.get('body', event)
        
        # Required fields validation
        required_fields = ['query', 'timestamp', 'source_system', 'source_process']
        missing_fields = [field for field in required_fields if field not in body or not body[field]]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate query is not empty
        if not body['query'].strip():
            return False, "Query cannot be empty"
        
        # Validate timestamp format
        try:
            datetime.fromisoformat(body['timestamp'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return False, "Invalid timestamp format. Expected ISO format (YYYY-MM-DDTHH:MM:SSZ)"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating webhook request: {str(e)}")
        return False, f"Request validation error: {str(e)}"

def generate_conversation_id() -> str:
    """
    Generate a unique conversation ID for webhook requests.
    Format: webhook_YYYYMMDD_HHMMSS_uuid
    
    Returns:
        Unique conversation ID string
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    unique_suffix = uuid.uuid4().hex[:8]
    return f"webhook_{timestamp}_{unique_suffix}"

def transform_to_manager_format(webhook_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform webhook request to manager agent format.
    
    Args:
        webhook_request: Validated webhook request data
        
    Returns:
        Request in manager agent format
    """
    try:
        conversation_id = generate_conversation_id()
        
        # Create manager agent compatible request
        manager_request = {
            "query": webhook_request["query"],
            "user_query": webhook_request["query"],  # Manager agent expects this field
            "sessionId": conversation_id,
            "userId": webhook_request.get("source_system", "webhook_user"),
            "channel": "webhook",
            "correlation_id": conversation_id,
            # Webhook-specific metadata for tracking
            "webhook_metadata": {
                "source_system": webhook_request["source_system"],
                "source_process": webhook_request["source_process"],
                "original_timestamp": webhook_request["timestamp"],
                "conversation_id": conversation_id,
                "user_context": webhook_request.get("user_context", {}),
                "session_id": webhook_request.get("session_id")
            }
        }
        
        logger.info(f"Transformed webhook request to manager format", extra={
            "conversation_id": conversation_id,
            "source_system": webhook_request["source_system"],
            "source_process": webhook_request["source_process"],
            "query_length": len(webhook_request["query"])
        })
        
        return manager_request
        
    except Exception as e:
        logger.error(f"Error transforming webhook request: {str(e)}")
        raise Exception(f"Request transformation failed: {str(e)}")

def extract_webhook_request_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract webhook request data from Lambda event.
    
    Args:
        event: Lambda event
        
    Returns:
        Webhook request data
    """
    # Handle API Gateway format
    if 'body' in event:
        if isinstance(event['body'], str):
            return json.loads(event['body'])
        else:
            return event['body']
    
    # Handle direct invocation format
    return event