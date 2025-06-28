"""
Unit tests for the Data Analysis Agent component.
"""

import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
import os
import sys
import uuid
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Create patchers before importing to avoid boto3 credential issues
boto3_session_patcher = patch('boto3.Session')
mock_boto3_session = boto3_session_patcher.start()
mock_session_instance = MagicMock()
mock_boto3_session.return_value = mock_session_instance

# Setup mock clients
mock_bedrock_runtime = MagicMock()
mock_bedrock_agent = MagicMock()
mock_session_instance.client.side_effect = lambda service, **kwargs: {
    'bedrock-agent-runtime': mock_bedrock_runtime,
    'bedrock-agent': mock_bedrock_agent
}.get(service, MagicMock())

from agents.data_agent.data_agent import DataAnalysisAgent

# Stop patchers after imports
boto3_session_patcher.stop()

class TestDataAnalysisAgent:
    """Test cases for the DataAnalysisAgent class."""
    
    @patch('boto3.Session')
    def test_initialization(self, mock_session):
        """Test that agent initializes with default and custom parameters."""
        # Set up mock session and clients
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()
        
        # Test with default parameters
        agent = DataAnalysisAgent()
        assert agent.agent_id is None
        assert agent.foundation_model == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert agent.region_name == 'us-east-1'
        
        # Test with custom parameters
        agent = DataAnalysisAgent(
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
    
    def test_generate_session_id(self):
        """Test the session ID generation functionality."""
        agent = DataAnalysisAgent()
        session_id = agent._generate_session_id()
        
        # Assert it follows the expected format
        assert session_id.startswith("data_analysis_")
        assert len(session_id) > 20  # Ensure adequate length
        
        # Generate another and ensure uniqueness
        another_session_id = agent._generate_session_id()
        assert session_id != another_session_id
    
    def test_construct_deal_quality_prompt_no_filters(self):
        """Test prompt construction for deal quality without filters."""
        agent = DataAnalysisAgent()
        prompt = agent._construct_deal_quality_prompt(None)
        
        # Check prompt content
        assert "Analyze our pipeline deals for quality assessment." in prompt
        assert "1. How our current pipeline aligns with our Ideal Customer Profile (ICP)" in prompt
        assert "filters" not in prompt.lower()  # Should not mention filters
    
    def test_construct_deal_quality_prompt_with_filters(self):
        """Test prompt construction for deal quality with filters."""
        agent = DataAnalysisAgent()
        filters = {"region": "EMEA", "deal_size": ">$100K"}
        prompt = agent._construct_deal_quality_prompt(filters)
        
        # Check prompt content
        assert "Analyze our pipeline deals for quality assessment." in prompt
        assert "Apply the following filters to your analysis:" in prompt
        assert "- region: EMEA" in prompt
        assert "- deal_size: >$100K" in prompt
    
    def test_construct_consumption_pattern_prompt_basic(self):
        """Test prompt construction for consumption patterns with basic params."""
        agent = DataAnalysisAgent()
        prompt = agent._construct_consumption_pattern_prompt("last_30_days", None)
        
        # Check prompt content
        assert "Analyze consumption patterns for last_30_days" in prompt
        assert "1. Significant changes in consumption patterns" in prompt
        # This assertion was incorrect, as 'account' appears in multiple contexts in the prompt
        # For example, "Accounts with decreasing usage" would cause this to fail
        # Let's verify that it doesn't contain specific account filtering instead
        assert "Focus your analysis on the following account" not in prompt
    
    def test_construct_consumption_pattern_prompt_with_account(self):
        """Test prompt construction for consumption patterns with account filter."""
        agent = DataAnalysisAgent()
        prompt = agent._construct_consumption_pattern_prompt("last_quarter", "Acme Corp")
        
        # Check prompt content
        assert "Analyze consumption patterns for last_quarter" in prompt
        assert "Focus your analysis on the following account(s): Acme Corp" in prompt
    
    @patch('boto3.Session')
    def test_invoke_success(self, mock_session):
        """Test successful invocation of the agent."""
        # Setup mock session and bedrock client
        mock_runtime_client = MagicMock()
        mock_runtime_client.invoke_agent.return_value = {"completion": "Test response"}
        
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'bedrock-agent-runtime': mock_runtime_client
        }.get(service, MagicMock())
        
        # Create agent and invoke
        agent = DataAnalysisAgent(agent_id="test-id", agent_alias_id="test-alias")
        response = agent.invoke("Test prompt")
        
        # Check that bedrock was called correctly
        mock_runtime_client.invoke_agent.assert_called_once_with(
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
    
    @patch('boto3.Session')
    def test_invoke_with_session_id(self, mock_session):
        """Test invoking the agent with a provided session ID."""
        # Setup mock session and bedrock client
        mock_runtime_client = MagicMock()
        mock_runtime_client.invoke_agent.return_value = {"completion": "Test response"}
        
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'bedrock-agent-runtime': mock_runtime_client
        }.get(service, MagicMock())
        
        # Create agent and invoke with session ID
        agent = DataAnalysisAgent(agent_id="test-id", agent_alias_id="test-alias")
        session_id = "test-session-123"
        response = agent.invoke("Test prompt", session_id=session_id)
        
        # Check the session ID is used
        assert response["session_id"] == session_id
        mock_runtime_client.invoke_agent.assert_called_once_with(
            agentId="test-id",
            agentAliasId="test-alias",
            sessionId=session_id,
            inputText="Test prompt",
            enableTrace=True
        )
    
    @patch('boto3.Session')
    def test_invoke_error_handling(self, mock_session):
        """Test error handling during agent invocation."""
        # Setup mock session and bedrock client
        mock_runtime_client = MagicMock()
        mock_runtime_client.invoke_agent.side_effect = Exception("Test error")
        
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'bedrock-agent-runtime': mock_runtime_client
        }.get(service, MagicMock())
        
        agent = DataAnalysisAgent(agent_id="test-id", agent_alias_id="test-alias")
        response = agent.invoke("Test prompt")
        
        # Check error response
        assert response["status"] == "error"
        assert "error" in response
        assert "Test error" in response["error"]
    
    def test_analyze_deal_quality(self):
        """Test the analyze_deal_quality method."""
        agent = DataAnalysisAgent()
        
        # Mock the invoke method
        agent.invoke = MagicMock(return_value={"status": "success", "mocked": True})
        
        # Test without filters
        response = agent.analyze_deal_quality()
        assert response["status"] == "success"
        assert response["mocked"] is True
        
        # Check that invoke was called with the correct prompt
        agent.invoke.assert_called_once()
        call_args = agent.invoke.call_args[0][0]
        assert "Analyze our pipeline deals" in call_args
    
    def test_analyze_consumption_patterns(self):
        """Test the analyze_consumption_patterns method."""
        agent = DataAnalysisAgent()
        
        # Mock the invoke method
        agent.invoke = MagicMock(return_value={"status": "success", "mocked": True})
        
        # Test with time range and account filter
        response = agent.analyze_consumption_patterns("last_60_days", "Test Account")
        assert response["status"] == "success"
        assert response["mocked"] is True
        
        # Check that invoke was called with the correct prompt
        agent.invoke.assert_called_once()
        call_args = agent.invoke.call_args[0][0]
        assert "Analyze consumption patterns for last_60_days" in call_args
        assert "Focus your analysis on the following account(s): Test Account" in call_args
    
    @patch('boto3.Session')
    def test_from_deployment_config(self, mock_session):
        """Test creating an agent from a deployment config file."""
        # Setup mock session
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()
        
        # Create a temporary config file
        config_data = {
            "data_agent": {
                "agent_id": "config-test-id",
                "agent_alias_id": "config-test-alias",
                "foundation_model": "config-test-model"
            },
            "region_name": "us-west-1",
            "profile_name": "config-test-profile"
        }
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            json.dump(config_data, temp)
            temp_path = temp.name
        
        try:
            # Create agent from config
            agent = DataAnalysisAgent.from_deployment_config(temp_path)
            
            # Verify configuration was loaded correctly
            assert agent.agent_id == "config-test-id"
            assert agent.agent_alias_id == "config-test-alias"
            assert agent.foundation_model == "config-test-model"
            assert agent.region_name == "us-west-1"
            assert agent.profile_name == "config-test-profile"
        finally:
            # Clean up temp file
            os.unlink(temp_path)
