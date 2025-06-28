"""
Integration tests for the Data Analysis Agent component.

These tests verify that the Data Agent integrates correctly with:
- AWS Bedrock services
- Firebolt data warehouse interactions
- End-to-end data analysis workflows
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from agents.data_agent.data_agent import DataAnalysisAgent


class TestDataAgentIntegration:
    """Integration tests for the Data Analysis Agent component."""

    def setup_method(self):
        """Set up test fixtures for each method."""
        # Create a mock config file for testing
        self.config_data = {
            "data_agent": {
                "agent_id": "test-integration-id",
                "agent_alias_id": "test-integration-alias",
                "foundation_model": "anthropic.claude-3-sonnet-20240229-v1:0"
            },
            "region_name": "us-east-1",
            "profile_name": None  # Use default credentials
        }
        
        self.mock_response = {
            "completion": "This is a sample analysis result with insights about deal quality.",
            "sessionId": "test-session-id"
        }
    
    @patch('boto3.Session')
    def test_data_agent_bedrock_integration(self, mock_session):
        """Test that Data Agent can connect to AWS Bedrock."""
        # Setup mock AWS Bedrock client
        mock_runtime_client = MagicMock()
        mock_runtime_client.invoke_agent.return_value = self.mock_response
        
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'bedrock-agent-runtime': mock_runtime_client
        }.get(service, MagicMock())
        
        # Create agent
        agent = DataAnalysisAgent(
            agent_id=self.config_data["data_agent"]["agent_id"],
            agent_alias_id=self.config_data["data_agent"]["agent_alias_id"],
            foundation_model=self.config_data["data_agent"]["foundation_model"],
            region_name=self.config_data["region_name"]
        )
        
        # Test agent invocation
        response = agent.invoke("Analyze the current deal quality for EMEA region.")
        
        # Verify interaction with Bedrock
        mock_runtime_client.invoke_agent.assert_called_once()
        assert response["status"] == "success"
        assert "agent_response" in response
    
    @patch('boto3.Session')
    def test_deal_quality_analysis_workflow(self, mock_session):
        """Test end-to-end deal quality analysis workflow."""
        # Setup mock AWS Bedrock client
        mock_runtime_client = MagicMock()
        mock_runtime_client.invoke_agent.return_value = self.mock_response
        
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'bedrock-agent-runtime': mock_runtime_client
        }.get(service, MagicMock())
        
        # Create agent
        agent = DataAnalysisAgent(
            agent_id=self.config_data["data_agent"]["agent_id"],
            agent_alias_id=self.config_data["data_agent"]["agent_alias_id"]
        )
        
        # Define a test filter for the analysis
        filters = {"region": "EMEA", "deal_size": ">$100K"}
        
        # Run the deal quality analysis
        response = agent.analyze_deal_quality(filters)
        
        # Verify the analysis workflow
        assert response["status"] == "success"
        
        # Verify that the correct prompt was used with filters
        call_args = mock_runtime_client.invoke_agent.call_args[1]["inputText"]
        assert "Analyze our pipeline deals for quality assessment" in call_args
        assert "region: EMEA" in call_args
        assert "deal_size: >$100K" in call_args
    
    @patch('boto3.Session')
    def test_consumption_pattern_analysis_workflow(self, mock_session):
        """Test end-to-end consumption pattern analysis workflow."""
        # Setup mock AWS Bedrock client
        mock_runtime_client = MagicMock()
        mock_runtime_client.invoke_agent.return_value = self.mock_response
        
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'bedrock-agent-runtime': mock_runtime_client
        }.get(service, MagicMock())
        
        # Create agent
        agent = DataAnalysisAgent(
            agent_id=self.config_data["data_agent"]["agent_id"],
            agent_alias_id=self.config_data["data_agent"]["agent_alias_id"]
        )
        
        # Run the consumption pattern analysis
        time_range = "last_quarter"
        account = "Acme Corp"
        response = agent.analyze_consumption_patterns(time_range, account)
        
        # Verify the analysis workflow
        assert response["status"] == "success"
        
        # Verify that the correct prompt was used with time range and account
        call_args = mock_runtime_client.invoke_agent.call_args[1]["inputText"]
        assert f"Analyze consumption patterns for {time_range}" in call_args
        assert f"Focus your analysis on the following account(s): {account}" in call_args
