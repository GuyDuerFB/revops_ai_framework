"""
Unit tests for the webhook functionality component.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import the module under test
from tools.webhook.webhook_handler import (
    WebhookHandler,
    load_webhook_config,
    validate_webhook_payload,
    format_webhook_response
)

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
            },
            "zapier": {
                "url": "https://hooks.zapier.com/hooks/catch/1234/abcd/",
                "headers": {}
            }
        }
        
        config_file = tmp_path / "webhook_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        return str(config_file)
    
    def test_load_webhook_config_success(self, sample_webhook_config):
        """Test successfully loading webhook configuration."""
        config = load_webhook_config(sample_webhook_config)
        
        assert "slack" in config
        assert "jira" in config
        assert "zapier" in config
        assert config["slack"]["url"] == "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
        assert "Content-Type" in config["slack"]["headers"]
        assert "Authorization" in config["jira"]["headers"]
    
    def test_load_webhook_config_file_not_found(self):
        """Test handling non-existent webhook configuration file."""
        with pytest.raises(FileNotFoundError):
            load_webhook_config("/path/to/nonexistent/config.json")
    
    def test_load_webhook_config_invalid_json(self, tmp_path):
        """Test handling invalid JSON in webhook configuration file."""
        # Create a file with invalid JSON
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{this is not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            load_webhook_config(str(invalid_file))
    
    def test_validate_webhook_payload_valid(self):
        """Test validation of valid webhook payload."""
        payload = {"message": "Test message", "channel": "general"}
        
        # This should not raise an exception
        validate_webhook_payload(payload)
    
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
    
    def test_webhook_handler_initialization_with_config(self, sample_webhook_config):
        """Test initializing WebhookHandler with configuration."""
        handler = WebhookHandler(config_file=sample_webhook_config)
        
        assert len(handler.webhooks) == 3
        assert "slack" in handler.webhooks
        assert "jira" in handler.webhooks
    
    def test_webhook_handler_initialization_with_dict(self):
        """Test initializing WebhookHandler with dict configuration."""
        config = {
            "test_webhook": {
                "url": "https://example.com/webhook",
                "headers": {"X-API-Key": "test-key"}
            }
        }
        
        handler = WebhookHandler(config=config)
        
        assert len(handler.webhooks) == 1
        assert "test_webhook" in handler.webhooks
        assert handler.webhooks["test_webhook"]["url"] == "https://example.com/webhook"
        assert handler.webhooks["test_webhook"]["headers"]["X-API-Key"] == "test-key"
    
    def test_webhook_handler_no_config(self):
        """Test initializing WebhookHandler with no configuration."""
        handler = WebhookHandler()
        
        assert handler.webhooks == {}
    
    @patch('requests.post')
    def test_trigger_webhook_by_url_success(self, mock_post):
        """Test triggering webhook by direct URL."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Webhook executed"
        mock_post.return_value = mock_response
        
        handler = WebhookHandler()
        payload = {"message": "Test message"}
        url = "https://example.com/webhook"
        headers = {"Content-Type": "application/json"}
        
        result = handler.trigger_webhook_by_url(url, payload, headers)
        
        # Verify the request
        mock_post.assert_called_once_with(
            url=url,
            json=payload,
            headers=headers
        )
        
        # Verify the result
        assert result["status"] == "success"
        assert result["response_code"] == 200
        assert result["response_body"] == "Webhook executed"
    
    @patch('requests.post')
    def test_trigger_webhook_by_url_error(self, mock_post):
        """Test handling errors when triggering webhook by URL."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.reason = "Server Error"
        mock_post.return_value = mock_response
        
        handler = WebhookHandler()
        payload = {"message": "Test message"}
        url = "https://example.com/webhook"
        
        result = handler.trigger_webhook_by_url(url, payload)
        
        # Verify the result
        assert result["status"] == "error"
        assert result["response_code"] == 500
        assert result["response_body"] == "Internal server error"
        assert "Server Error" in result["error"]
    
    @patch('requests.post')
    def test_trigger_webhook_by_url_exception(self, mock_post):
        """Test handling exceptions when triggering webhook by URL."""
        # Mock request exception
        mock_post.side_effect = Exception("Connection error")
        
        handler = WebhookHandler()
        payload = {"message": "Test message"}
        url = "https://example.com/webhook"
        
        result = handler.trigger_webhook_by_url(url, payload)
        
        # Verify the result
        assert result["status"] == "error"
        assert "Connection error" in result["error"]
    
    @patch('requests.post')
    def test_trigger_named_webhook_success(self, mock_post, sample_webhook_config):
        """Test triggering a named webhook from configuration."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Message sent to Slack"
        mock_post.return_value = mock_response
        
        handler = WebhookHandler(config_file=sample_webhook_config)
        payload = {"text": "Alert: System notification"}
        
        result = handler.trigger_named_webhook("slack", payload)
        
        # Verify the request
        mock_post.assert_called_once_with(
            url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Verify the result
        assert result["status"] == "success"
        assert result["response_code"] == 200
        assert result["response_body"] == "Message sent to Slack"
    
    def test_trigger_named_webhook_not_found(self, sample_webhook_config):
        """Test triggering a non-existent named webhook."""
        handler = WebhookHandler(config_file=sample_webhook_config)
        payload = {"message": "Test message"}
        
        result = handler.trigger_named_webhook("nonexistent", payload)
        
        # Verify the result
        assert result["status"] == "error"
        assert "Webhook 'nonexistent' not found" in result["error"]
    
    def test_list_available_webhooks(self, sample_webhook_config):
        """Test listing available webhooks from configuration."""
        handler = WebhookHandler(config_file=sample_webhook_config)
        
        result = handler.list_available_webhooks()
        
        # Verify the result
        assert len(result) == 3
        assert "slack" in result
        assert "jira" in result
        assert "zapier" in result
    
    @patch('tools.webhook.webhook_handler.load_webhook_config')
    @patch('tools.webhook.webhook_handler.WebhookHandler.trigger_webhook_by_url')
    @patch('tools.webhook.webhook_handler.WebhookHandler.trigger_named_webhook')
    def test_lambda_handler_direct_url(self, mock_trigger_named, mock_trigger_url, mock_load_config):
        """Test lambda_handler with direct URL webhook."""
        # Set up mocks
        mock_trigger_url.return_value = {
            "status": "success",
            "response_code": 200,
            "response_body": "Success"
        }
        
        # Import lambda_handler locally to avoid circular import
        from tools.webhook.lambda_function import lambda_handler
        
        # Test event for direct URL
        event = {
            "url": "https://example.com/webhook",
            "payload": {"message": "Test message"},
            "headers": {"X-API-Key": "test-key"}
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result["status"] == "success"
        assert result["response_code"] == 200
        
        # Check that the correct method was called
        mock_trigger_url.assert_called_once_with(
            event["url"],
            event["payload"],
            event["headers"]
        )
        mock_trigger_named.assert_not_called()
    
    @patch('tools.webhook.webhook_handler.load_webhook_config')
    @patch('tools.webhook.webhook_handler.WebhookHandler.trigger_webhook_by_url')
    @patch('tools.webhook.webhook_handler.WebhookHandler.trigger_named_webhook')
    def test_lambda_handler_named_webhook(self, mock_trigger_named, mock_trigger_url, mock_load_config):
        """Test lambda_handler with named webhook."""
        # Set up mocks
        mock_trigger_named.return_value = {
            "status": "success",
            "response_code": 200,
            "response_body": "Success"
        }
        
        # Import lambda_handler locally to avoid circular import
        from tools.webhook.lambda_function import lambda_handler
        
        # Test event for named webhook
        event = {
            "webhook_name": "slack",
            "payload": {"text": "Alert message"}
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result
        assert result["status"] == "success"
        assert result["response_code"] == 200
        
        # Check that the correct method was called
        mock_trigger_named.assert_called_once_with(
            event["webhook_name"],
            event["payload"]
        )
        mock_trigger_url.assert_not_called()
    
    @patch('tools.webhook.webhook_handler.load_webhook_config')
    def test_lambda_handler_missing_parameters(self, mock_load_config):
        """Test lambda_handler with missing required parameters."""
        # Import lambda_handler locally to avoid circular import
        from tools.webhook.lambda_function import lambda_handler
        
        # Test event missing both URL and webhook_name
        event = {
            "payload": {"message": "Test message"}
        }
        
        result = lambda_handler(event, {})
        
        # Verify the result indicates an error
        assert result["status"] == "error"
        assert "Either 'url' or 'webhook_name' must be provided" in result["error"]
