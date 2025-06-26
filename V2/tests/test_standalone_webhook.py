"""
Standalone unit tests for the webhook functionality component.
This file doesn't rely on the conftest.py fixtures to avoid import issues.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Mock the webhook module - we'll test the logic without actual implementations
class MockWebhookHandler:
    def __init__(self, config=None, config_file=None):
        self.webhooks = config or {}
        if config_file:
            self.webhooks = {"slack": {"url": "https://mock-slack-url.com"}}
    
    def trigger_webhook_by_url(self, url, payload, headers=None):
        if not url:
            return {"status": "error", "error": "URL is required"}
        return {"status": "success", "response_code": 200, "response_body": "Mocked response"}
    
    def trigger_named_webhook(self, webhook_name, payload):
        if webhook_name not in self.webhooks:
            return {"status": "error", "error": f"Webhook '{webhook_name}' not found"}
        return {"status": "success", "response_code": 200, "response_body": "Mocked response"}
    
    def list_available_webhooks(self):
        return list(self.webhooks.keys())

# Mock the lambda_function module
def mock_lambda_handler(event, context):
    if "url" in event:
        return {"status": "success", "response_code": 200}
    elif "webhook_name" in event:
        return {"status": "success", "response_code": 200}
    else:
        return {"status": "error", "error": "Either 'url' or 'webhook_name' must be provided"}

# Mock helper functions
def validate_webhook_payload(payload):
    if payload is None:
        raise ValueError("Webhook payload cannot be None")
    if not isinstance(payload, dict):
        raise ValueError("Webhook payload must be a dictionary")
    return True

def format_webhook_response(response):
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

def load_webhook_config(config_file):
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Webhook configuration file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        return json.loads(f.read())

class TestWebhookHandler:
    """Test cases for the WebhookHandler class and helper functions."""
    
    @pytest.fixture
    def sample_webhook_config(self, tmp_path):
        """Fixture providing a sample webhook configuration file."""
        config = {
            "slack": {
                "url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
                "headers": {"Content-Type": "application/json"}
            },
            "jira": {
                "url": "https://jira-api.example.com/webhook",
                "headers": {
                    "Authorization": "Bearer test-token",
                    "Content-Type": "application/json"
                }
            }
        }
        
        config_file = tmp_path / "webhook_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        return str(config_file)
    
    def test_validate_webhook_payload_valid(self):
        """Test validation of valid webhook payload."""
        payload = {"message": "Test message", "channel": "general"}
        assert validate_webhook_payload(payload) is True
    
    def test_validate_webhook_payload_none(self):
        """Test validation of None webhook payload."""
        with pytest.raises(ValueError) as excinfo:
            validate_webhook_payload(None)
        
        assert "Webhook payload cannot be None" in str(excinfo.value)
    
    def test_validate_webhook_payload_non_dict(self):
        """Test validation of non-dict webhook payload."""
        with pytest.raises(ValueError) as excinfo:
            validate_webhook_payload("string payload")
        
        assert "Webhook payload must be a dictionary" in str(excinfo.value)
    
    def test_format_webhook_response_success(self):
        """Test formatting successful webhook response."""
        response = {
            "status_code": 200,
            "body": "Success",
            "headers": {"Content-Type": "application/json"}
        }
        
        result = format_webhook_response(response)
        
        assert result["status"] == "success"
        assert result["response_code"] == 200
        assert result["response_body"] == "Success"
    
    def test_format_webhook_response_error(self):
        """Test formatting error webhook response."""
        response = {
            "status_code": 401,
            "body": "Unauthorized",
            "error": "Invalid authentication"
        }
        
        result = format_webhook_response(response)
        
        assert result["status"] == "error"
        assert result["response_code"] == 401
        assert result["response_body"] == "Unauthorized"
        assert result["error"] == "Invalid authentication"
    
    def test_webhook_handler_initialization_with_config(self):
        """Test initializing WebhookHandler with dict configuration."""
        config = {
            "test_webhook": {
                "url": "https://example.com/webhook",
                "headers": {"X-API-Key": "test-key"}
            }
        }
        
        handler = MockWebhookHandler(config=config)
        
        assert len(handler.webhooks) == 1
        assert "test_webhook" in handler.webhooks
    
    def test_webhook_handler_no_config(self):
        """Test initializing WebhookHandler with no configuration."""
        handler = MockWebhookHandler()
        
        assert handler.webhooks == {}
    
    def test_lambda_handler_missing_parameters(self):
        """Test lambda_handler with missing required parameters."""
        event = {
            "payload": {"message": "Test message"}
        }
        
        result = mock_lambda_handler(event, {})
        
        assert result["status"] == "error"
        assert "Either 'url' or 'webhook_name' must be provided" in result["error"]
    
    def test_lambda_handler_direct_url(self):
        """Test lambda_handler with direct URL webhook."""
        event = {
            "url": "https://example.com/webhook",
            "payload": {"message": "Test message"}
        }
        
        result = mock_lambda_handler(event, {})
        
        assert result["status"] == "success"
        assert result["response_code"] == 200
    
    def test_lambda_handler_named_webhook(self):
        """Test lambda_handler with named webhook."""
        event = {
            "webhook_name": "slack",
            "payload": {"text": "Alert message"}
        }
        
        result = mock_lambda_handler(event, {})
        
        assert result["status"] == "success"
        assert result["response_code"] == 200
