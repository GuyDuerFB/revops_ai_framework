"""
Unit tests for the Decision Agent component.
"""

import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from agents.decision_agent.decision_agent import DecisionAgent

class TestDecisionAgent:
    """Test cases for the DecisionAgent class."""
    
    def test_initialization(self):
        """Test that agent initializes with default and custom parameters."""
        # Test with default parameters
        agent = DecisionAgent()
        assert agent.agent_id is None
        assert agent.foundation_model == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert agent.region_name == 'us-east-1'
        
        # Test with custom parameters
        agent = DecisionAgent(
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
        agent = DecisionAgent()
        session_id = agent._generate_session_id()
        
        # Assert it follows the expected format
        assert session_id.startswith("decision_")
        assert len(session_id) > 20  # Ensure adequate length
        
        # Generate another and ensure uniqueness
        another_session_id = agent._generate_session_id()
        assert session_id != another_session_id
    
    def test_construct_deal_evaluation_prompt(self):
        """Test prompt construction for deal evaluation."""
        agent = DecisionAgent()
        analysis_data = {
            "deal_quality": {
                "icp_alignment": 0.85,
                "data_completeness": 0.75,
                "top_use_cases": ["Data Warehousing", "Real-time Analytics"]
            },
            "deals_by_region": {
                "EMEA": 12,
                "AMER": 8,
                "APAC": 5
            }
        }
        
        prompt = agent._construct_deal_evaluation_prompt(analysis_data)
        
        # Check prompt content
        assert "Based on the following deal quality analysis data" in prompt
        assert "Prioritizing deals based on ICP alignment" in prompt
        assert json.dumps(analysis_data, indent=2) in prompt
    
    def test_construct_consumption_evaluation_prompt(self):
        """Test prompt construction for consumption pattern evaluation."""
        agent = DecisionAgent()
        analysis_data = {
            "accounts": {
                "Acme Corp": {
                    "trend": "decreasing",
                    "change_percent": -15.5,
                    "risk_level": "high"
                },
                "XYZ Inc": {
                    "trend": "increasing",
                    "change_percent": 22.3,
                    "opportunity": "upsell"
                }
            },
            "overall_trends": {
                "avg_change": 3.2,
                "anomalies_detected": 2
            }
        }
        
        prompt = agent._construct_consumption_evaluation_prompt(analysis_data)
        
        # Check prompt content
        assert "Based on the following consumption pattern analysis" in prompt
        assert "Proactive outreach for accounts with decreasing usage" in prompt
        assert json.dumps(analysis_data, indent=2) in prompt
    
    def test_invoke_success(self, mock_bedrock_client):
        """Test successful invocation of the agent."""
        agent = DecisionAgent(agent_id="test-id", agent_alias_id="test-alias")
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
        agent = DecisionAgent(agent_id="test-id", agent_alias_id="test-alias")
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
        
        agent = DecisionAgent(agent_id="test-id", agent_alias_id="test-alias")
        response = agent.invoke("Test prompt")
        
        # Check error response
        assert response["status"] == "error"
        assert "error" in response
        assert "Test error" in response["error"]
    
    def test_evaluate_deal_quality(self):
        """Test the evaluate_deal_quality method."""
        agent = DecisionAgent()
        
        # Mock the invoke method
        agent.invoke = MagicMock(return_value={"status": "success", "mocked": True})
        
        # Test with sample analysis data
        analysis_data = {
            "icp_alignment": 0.78,
            "deals": [{"id": "D123", "score": 85}, {"id": "D456", "score": 62}]
        }
        
        response = agent.evaluate_deal_quality(analysis_data)
        assert response["status"] == "success"
        assert response["mocked"] is True
        
        # Check that invoke was called with the correct prompt
        agent.invoke.assert_called_once()
        call_args = agent.invoke.call_args[0][0]
        assert "Based on the following deal quality analysis data" in call_args
        assert json.dumps(analysis_data, indent=2) in call_args
    
    def test_evaluate_consumption_patterns(self):
        """Test the evaluate_consumption_patterns method."""
        agent = DecisionAgent()
        
        # Mock the invoke method
        agent.invoke = MagicMock(return_value={"status": "success", "mocked": True})
        
        # Test with sample analysis data
        analysis_data = {
            "accounts": {
                "TestCo": {"trend": "flat"},
                "BigCorp": {"trend": "decreasing"}
            }
        }
        
        response = agent.evaluate_consumption_patterns(analysis_data)
        assert response["status"] == "success"
        assert response["mocked"] is True
        
        # Check that invoke was called with the correct prompt
        agent.invoke.assert_called_once()
        call_args = agent.invoke.call_args[0][0]
        assert "Based on the following consumption pattern analysis" in call_args
        assert json.dumps(analysis_data, indent=2) in call_args
    
    def test_from_deployment_config(self):
        """Test creating an agent from a deployment config file."""
        # Create a temporary config file
        config_data = {
            "decision_agent": {
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
            agent = DecisionAgent.from_deployment_config(temp_path)
            
            # Verify configuration was loaded correctly
            assert agent.agent_id == "config-test-id"
            assert agent.agent_alias_id == "config-test-alias"
            assert agent.foundation_model == "config-test-model"
            assert agent.region_name == "us-west-1"
            assert agent.profile_name == "config-test-profile"
        finally:
            # Clean up temp file
            os.unlink(temp_path)
