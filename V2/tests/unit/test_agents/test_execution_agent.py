"""
Unit tests for the Execution Agent component.
"""

import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
import os
import sys
import requests

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from agents.execution_agent.execution_agent import ExecutionAgent

class TestExecutionAgent:
    """Test cases for the ExecutionAgent class."""
    
    def test_initialization(self):
        """Test that agent initializes with default and custom parameters."""
        # Test with default parameters
        agent = ExecutionAgent()
        assert agent.agent_id is None
        assert agent.foundation_model == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert agent.region_name == 'us-east-1'
        assert agent.webhook_config == {}
        
        # Test with custom parameters
        agent = ExecutionAgent(
            agent_id="custom-id",
            agent_alias_id="custom-alias",
            foundation_model="custom-model",
            region_name="us-west-2",
            profile_name="test-profile"
        )
        assert agent.agent_id == "custom-id"
        assert agent.agent_alias_id == "custom-alias"
        assert agent.foundation_model == "custom-model"
        assert agent.region_name == "us-west-2"
        assert agent.profile_name == "test-profile"
    
    def test_initialization_with_webhook_config(self, tmp_path):
        """Test initialization with webhook configuration."""
        # Create a temporary webhook config file
        webhook_config = {
            "slack": {
                "url": "https://hooks.slack.com/services/test",
                "headers": {"Content-Type": "application/json"}
            },
            "jira": {
                "url": "https://jira-api.example.com/webhook",
                "headers": {"Authorization": "Bearer test-token"}
            }
        }
        
        webhook_config_path = tmp_path / "webhook_config.json"
        with open(webhook_config_path, 'w') as f:
            json.dump(webhook_config, f)
        
        # Initialize agent with webhook config
        agent = ExecutionAgent(webhook_config_path=str(webhook_config_path))
        
        # Verify webhook config was loaded
        assert agent.webhook_config == webhook_config
    
    def test_generate_session_id(self):
        """Test the session ID generation functionality."""
        agent = ExecutionAgent()
        session_id = agent._generate_session_id()
        
        # Assert it follows the expected format
        assert session_id.startswith("execution_")
        assert len(session_id) > 20  # Ensure adequate length
        
        # Generate another and ensure uniqueness
        another_session_id = agent._generate_session_id()
        assert session_id != another_session_id
    
    def test_invoke_success(self, mock_bedrock_client):
        """Test successful invocation of the agent."""
        agent = ExecutionAgent(agent_id="test-id", agent_alias_id="test-alias")
        response = agent.invoke("Test prompt")
        
        # Check that bedrock was called correctly
        mock_bedrock_client.invoke_agent.assert_called_once_with(
            agentId="test-id",
            agentAliasId="test-alias",
            sessionId=response["session_id"],
            inputText="Test prompt",
            enableTrace=True
        )
        
        # Check response structure
        assert response["status"] == "success"
        assert "agent_response" in response
        assert "session_id" in response
    
    def test_invoke_error_handling(self, mock_bedrock_client):
        """Test error handling during agent invocation."""
        # Set up the mock to raise an exception
        mock_bedrock_client.invoke_agent.side_effect = Exception("Test error")
        
        agent = ExecutionAgent(agent_id="test-id", agent_alias_id="test-alias")
        response = agent.invoke("Test prompt")
        
        # Check error response
        assert response["status"] == "error"
        assert "error" in response
        assert "Test error" in response["error"]
    
    def test_execute_actions_empty_plan(self):
        """Test executing an empty action plan."""
        agent = ExecutionAgent()
        action_plan = {}
        
        result = agent.execute_actions(action_plan)
        
        # Should return success but no actions executed
        assert result["status"] == "success"
        assert len(result["executed_actions"]) == 0
        assert len(result["failed_actions"]) == 0
    
    def test_execute_actions_unknown_action_type(self):
        """Test handling of unknown action types."""
        agent = ExecutionAgent()
        action_plan = {
            "actions": [
                {
                    "type": "unknown_action_type",
                    "parameters": {"param1": "value1"}
                }
            ]
        }
        
        result = agent.execute_actions(action_plan)
        
        # Should have one failed action
        assert len(result["executed_actions"]) == 0
        assert len(result["failed_actions"]) == 1
        assert result["failed_actions"][0]["action"]["type"] == "unknown_action_type"
        assert "Unknown action type" in result["failed_actions"][0]["error"]
    
    def test_trigger_webhook_success(self, requests_mock):
        """Test successful webhook triggering."""
        # Set up mock for webhook request
        requests_mock.post(
            "https://webhook.example.com/endpoint",
            status_code=200,
            text="Success"
        )
        
        # Initialize agent with webhook config
        agent = ExecutionAgent()
        
        # Define webhook parameters
        parameters = {
            "url": "https://webhook.example.com/endpoint",
            "payload": {"key": "value"}
        }
        
        # Trigger webhook
        result = agent.trigger_webhook(parameters)
        
        # Verify result
        assert result["status"] == "success"
        assert result["response_code"] == 200
        assert result["response_body"] == "Success"
        
        # Verify request was made correctly
        assert requests_mock.called
        assert requests_mock.last_request.json() == {"key": "value"}
    
    def test_trigger_webhook_from_config(self, requests_mock):
        """Test triggering a webhook using configuration."""
        # Set up mock for webhook request
        requests_mock.post(
            "https://hooks.slack.com/services/test",
            status_code=200,
            text="Success"
        )
        
        # Create webhook config
        webhook_config = {
            "slack_notification": {
                "url": "https://hooks.slack.com/services/test",
                "headers": {"X-Custom-Header": "test-value"}
            }
        }
        
        # Initialize agent with webhook config
        agent = ExecutionAgent()
        agent.webhook_config = webhook_config
        
        # Define webhook parameters using named webhook
        parameters = {
            "webhook_name": "slack_notification",
            "payload": {"text": "Test message"}
        }
        
        # Trigger webhook
        result = agent.trigger_webhook(parameters)
        
        # Verify result
        assert result["status"] == "success"
        assert result["response_code"] == 200
        
        # Verify request was made correctly
        assert requests_mock.called
        assert requests_mock.last_request.json() == {"text": "Test message"}
        assert requests_mock.last_request.headers["X-Custom-Header"] == "test-value"
    
    def test_trigger_webhook_error(self, requests_mock):
        """Test webhook triggering with error response."""
        # Set up mock for webhook request
        requests_mock.post(
            "https://webhook.example.com/endpoint",
            status_code=500,
            reason="Internal Server Error"
        )
        
        # Initialize agent
        agent = ExecutionAgent()
        
        # Define webhook parameters
        parameters = {
            "url": "https://webhook.example.com/endpoint",
            "payload": {"key": "value"}
        }
        
        # Trigger webhook
        result = agent.trigger_webhook(parameters)
        
        # Verify error result
        assert result["status"] == "error"
        assert "error" in result
        assert "500" in result["error"]  # Error should mention the status code
    
    def test_write_to_firebolt(self, monkeypatch):
        """Test writing to Firebolt via Lambda function."""
        # Mock the Lambda client
        mock_lambda = MagicMock()
        mock_lambda.invoke.return_value = {
            'StatusCode': 200,
            'Payload': MagicMock()
        }
        mock_lambda.invoke.return_value['Payload'].read.return_value = json.dumps({
            "success": True,
            "rows_affected": 5
        })
        
        # Patch the environment variable
        monkeypatch.setenv("FIREBOLT_WRITER_LAMBDA", "test-lambda-function")
        
        # Patch the _get_lambda_client method
        agent = ExecutionAgent()
        agent.lambda_client = mock_lambda
        
        # Define parameters for Firebolt write
        parameters = {
            "table": "insights",
            "operation": "insert",
            "data": [{"id": 1, "value": "test"}]
        }
        
        # Execute write operation
        result = agent.write_to_firebolt(parameters)
        
        # Verify Lambda was invoked correctly
        mock_lambda.invoke.assert_called_once_with(
            FunctionName="test-lambda-function",
            InvocationType="RequestResponse",
            Payload=json.dumps(parameters)
        )
        
        # Verify result
        assert result["status"] == "success"
        assert "lambda_response" in result
        assert result["lambda_response"]["success"] is True
    
    def test_write_to_firebolt_error(self, monkeypatch):
        """Test error handling when writing to Firebolt."""
        # Mock the Lambda client
        mock_lambda = MagicMock()
        mock_lambda.invoke.side_effect = Exception("Lambda invocation failed")
        
        # Patch the _get_lambda_client method
        agent = ExecutionAgent()
        agent.lambda_client = mock_lambda
        
        # Define parameters for Firebolt write
        parameters = {
            "table": "insights",
            "operation": "insert",
            "data": [{"id": 1, "value": "test"}]
        }
        
        # Execute write operation
        result = agent.write_to_firebolt(parameters)
        
        # Verify error result
        assert result["status"] == "error"
        assert "error" in result
        assert "Lambda invocation failed" in result["error"]
    
    def test_execute_actions_multiple(self, requests_mock):
        """Test executing multiple actions in a plan."""
        # Set up mock for webhook request
        requests_mock.post(
            "https://webhook1.example.com/endpoint",
            status_code=200,
            text="Success 1"
        )
        requests_mock.post(
            "https://webhook2.example.com/endpoint",
            status_code=500,
            reason="Internal Server Error"
        )
        
        # Mock the lambda client method
        agent = ExecutionAgent()
        agent.write_to_firebolt = MagicMock(return_value={
            "status": "success",
            "lambda_response": {"rows_affected": 3}
        })
        
        # Create action plan with multiple actions
        action_plan = {
            "actions": [
                {
                    "type": "webhook",
                    "parameters": {
                        "url": "https://webhook1.example.com/endpoint",
                        "payload": {"action": "notify"}
                    }
                },
                {
                    "type": "webhook",
                    "parameters": {
                        "url": "https://webhook2.example.com/endpoint",
                        "payload": {"action": "update"}
                    }
                },
                {
                    "type": "firebolt_write",
                    "parameters": {
                        "table": "test_table",
                        "operation": "insert",
                        "data": [{"id": 1}]
                    }
                }
            ]
        }
        
        # Execute actions
        result = agent.execute_actions(action_plan)
        
        # Verify results
        assert len(result["executed_actions"]) == 2  # First webhook and Firebolt write succeeded
        assert len(result["failed_actions"]) == 1    # Second webhook failed
        
        # Check that the Firebolt write was called with correct parameters
        agent.write_to_firebolt.assert_called_once_with(
            action_plan["actions"][2]["parameters"]
        )
