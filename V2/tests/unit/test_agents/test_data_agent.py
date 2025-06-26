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

from agents.data_agent.data_agent import DataAnalysisAgent

class TestDataAnalysisAgent:
    """Test cases for the DataAnalysisAgent class."""
    
    def test_initialization(self):
        """Test that agent initializes with default and custom parameters."""
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
        assert "account" not in prompt.lower()  # Should not mention specific accounts
    
    def test_construct_consumption_pattern_prompt_with_account(self):
        """Test prompt construction for consumption patterns with account filter."""
        agent = DataAnalysisAgent()
        prompt = agent._construct_consumption_pattern_prompt("last_quarter", "Acme Corp")
        
        # Check prompt content
        assert "Analyze consumption patterns for last_quarter" in prompt
        assert "Focus your analysis on the following account(s): Acme Corp" in prompt
    
    def test_invoke_success(self, mock_bedrock_client):
        """Test successful invocation of the agent."""
        agent = DataAnalysisAgent(agent_id="test-id", agent_alias_id="test-alias")
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
    
    def test_invoke_with_session_id(self, mock_bedrock_client):
        """Test invoking the agent with a provided session ID."""
        agent = DataAnalysisAgent(agent_id="test-id", agent_alias_id="test-alias")
        session_id = "test-session-123"
        response = agent.invoke("Test prompt", session_id=session_id)
        
        # Check the session ID is used
        assert response["session_id"] == session_id
        mock_bedrock_client.invoke_agent.assert_called_once_with(
            agentId="test-id",
            agentAliasId="test-alias",
            sessionId=session_id,
            inputText="Test prompt",
            enableTrace=True
        )
    
    def test_invoke_error_handling(self, mock_bedrock_client):
        """Test error handling during agent invocation."""
        # Set up the mock to raise an exception
        mock_bedrock_client.invoke_agent.side_effect = Exception("Test error")
        
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
    
    def test_from_deployment_config(self):
        """Test creating an agent from a deployment config file."""
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
