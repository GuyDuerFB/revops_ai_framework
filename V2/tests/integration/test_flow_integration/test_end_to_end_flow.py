"""
End-to-end integration tests for the RevOps AI Framework V2 flow.

This test file simulates the complete workflow of the RevOps AI Framework,
testing the integration between agents, tools, and AWS services.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from agents.data_agent.data_agent import DataAnalysisAgent
from agents.decision_agent.decision_agent import DecisionAgent
from agents.execution_agent.execution_agent import ExecutionAgent
from flows.orchestration import RevOpsOrchestrator


class TestEndToEndFlow:
    """Tests for the end-to-end workflow of the RevOps AI Framework."""
    
    @pytest.fixture
    def mock_environment(self, monkeypatch):
        """Setup mock environment variables required for testing."""
        monkeypatch.setenv("FIREBOLT_QUERY_LAMBDA", "test-query-lambda")
        monkeypatch.setenv("FIREBOLT_METADATA_LAMBDA", "test-metadata-lambda")
        monkeypatch.setenv("FIREBOLT_WRITER_LAMBDA", "test-writer-lambda")
        monkeypatch.setenv("GONG_SECRET_NAME", "test-gong-secret")
        monkeypatch.setenv("FIREBOLT_SECRET_NAME", "test-firebolt-secret")
        monkeypatch.setenv("WEBHOOK_CONFIG_PATH", "/path/to/webhook_config.json")
        monkeypatch.setenv("NOTIFICATION_EMAIL", "alerts@example.com")
    
    @pytest.fixture
    def mock_config_file(self, tmp_path):
        """Create a mock configuration file for testing."""
        config = {
            "data_agent": {
                "agent_id": "test-data-agent-id",
                "agent_alias_id": "test-data-agent-alias"
            },
            "decision_agent": {
                "agent_id": "test-decision-agent-id",
                "agent_alias_id": "test-decision-agent-alias"
            },
            "execution_agent": {
                "agent_id": "test-execution-agent-id",
                "agent_alias_id": "test-execution-agent-alias"
            },
            "region_name": "us-east-1",
            "environment": "test"
        }
        
        config_path = tmp_path / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        return str(config_path)
    
    @pytest.fixture
    def mock_agents(self, mock_bedrock_client):
        """Mock all agents for testing the orchestrator."""
        data_agent_mock = MagicMock(spec=DataAnalysisAgent)
        decision_agent_mock = MagicMock(spec=DecisionAgent)
        execution_agent_mock = MagicMock(spec=ExecutionAgent)
        
        # Set up return values for data agent methods
        data_agent_mock.analyze_deal_quality.return_value = {
            "status": "success",
            "agent_response": {
                "completion": json.dumps({
                    "icp_alignment": {
                        "Acme Corp": 0.85,
                        "XYZ Inc": 0.62
                    },
                    "risk_factors": ["budget constraints", "competitive situation"],
                    "recommendations": ["Focus on value proposition for Acme Corp"]
                }),
                "stopReason": "COMPLETE"
            },
            "session_id": "data_12345"
        }
        
        data_agent_mock.analyze_consumption_patterns.return_value = {
            "status": "success",
            "agent_response": {
                "completion": json.dumps({
                    "accounts": {
                        "Acme Corp": {"trend": "decreasing", "risk_level": "high"},
                        "Globex Corp": {"trend": "increasing", "opportunity": "upsell"}
                    },
                    "anomalies": [{"account": "Acme Corp", "type": "sudden_drop"}]
                }),
                "stopReason": "COMPLETE"
            },
            "session_id": "data_67890"
        }
        
        # Set up return values for decision agent methods
        decision_agent_mock.evaluate_deal_quality.return_value = {
            "status": "success",
            "agent_response": {
                "completion": json.dumps({
                    "priority_deals": ["Acme Corp"],
                    "actions": [
                        {
                            "type": "notification",
                            "parameters": {
                                "channel": "email",
                                "subject": "Deal Priority Alert",
                                "message": "Acme Corp deal should be prioritized",
                                "recipients": ["sales@example.com"]
                            }
                        }
                    ]
                }),
                "stopReason": "COMPLETE"
            },
            "session_id": "decision_12345"
        }
        
        decision_agent_mock.evaluate_consumption_patterns.return_value = {
            "status": "success",
            "agent_response": {
                "completion": json.dumps({
                    "recommendations": [
                        {
                            "account": "Acme Corp",
                            "action": "Immediate outreach",
                            "rationale": "High risk of churn due to decreasing usage"
                        }
                    ],
                    "actions": [
                        {
                            "type": "webhook",
                            "parameters": {
                                "url": "https://example.com/webhook",
                                "payload": {
                                    "account": "Acme Corp",
                                    "action": "create_task"
                                }
                            }
                        }
                    ]
                }),
                "stopReason": "COMPLETE"
            },
            "session_id": "decision_67890"
        }
        
        # Set up return values for execution agent methods
        execution_agent_mock.execute_actions.return_value = {
            "status": "success",
            "executed_actions": [
                {
                    "action_type": "notification",
                    "status": "success",
                    "message": "Email notification sent"
                }
            ],
            "failed_actions": []
        }
        
        return {
            "data_agent": data_agent_mock,
            "decision_agent": decision_agent_mock,
            "execution_agent": execution_agent_mock
        }
    
    @patch('flows.orchestration.DataAnalysisAgent')
    @patch('flows.orchestration.DecisionAgent')
    @patch('flows.orchestration.ExecutionAgent')
    def test_deal_quality_flow(self, mock_execution_agent, mock_decision_agent, 
                              mock_data_agent, mock_agents, mock_config_file):
        """Test the deal quality analysis workflow from end to end."""
        # Set up the agent class mocks to return our mock instances
        mock_data_agent.from_deployment_config.return_value = mock_agents["data_agent"]
        mock_decision_agent.from_deployment_config.return_value = mock_agents["decision_agent"]
        mock_execution_agent.from_deployment_config.return_value = mock_agents["execution_agent"]
        
        # Create the orchestrator
        orchestrator = RevOpsOrchestrator(config_path=mock_config_file)
        
        # Run the deal quality workflow
        result = orchestrator.run_deal_quality_flow()
        
        # Verify that each agent was called in sequence with the correct data
        mock_agents["data_agent"].analyze_deal_quality.assert_called_once()
        
        data_analysis_response = json.loads(
            mock_agents["data_agent"].analyze_deal_quality.return_value["agent_response"]["completion"]
        )
        
        mock_agents["decision_agent"].evaluate_deal_quality.assert_called_once_with(
            data_analysis_response
        )
        
        decision_response = json.loads(
            mock_agents["decision_agent"].evaluate_deal_quality.return_value["agent_response"]["completion"]
        )
        
        mock_agents["execution_agent"].execute_actions.assert_called_once_with(
            {"actions": decision_response["actions"]}
        )
        
        # Verify the final result
        assert result["status"] == "success"
        assert "data_analysis" in result
        assert "decision" in result
        assert "execution" in result
    
    @patch('flows.orchestration.DataAnalysisAgent')
    @patch('flows.orchestration.DecisionAgent')
    @patch('flows.orchestration.ExecutionAgent')
    def test_consumption_patterns_flow(self, mock_execution_agent, mock_decision_agent, 
                                     mock_data_agent, mock_agents, mock_config_file):
        """Test the consumption patterns workflow from end to end."""
        # Set up the agent class mocks to return our mock instances
        mock_data_agent.from_deployment_config.return_value = mock_agents["data_agent"]
        mock_decision_agent.from_deployment_config.return_value = mock_agents["decision_agent"]
        mock_execution_agent.from_deployment_config.return_value = mock_agents["execution_agent"]
        
        # Create the orchestrator
        orchestrator = RevOpsOrchestrator(config_path=mock_config_file)
        
        # Run the consumption patterns workflow
        result = orchestrator.run_consumption_patterns_flow(timeframe="last_30_days")
        
        # Verify that each agent was called in sequence with the correct data
        mock_agents["data_agent"].analyze_consumption_patterns.assert_called_once_with("last_30_days")
        
        data_analysis_response = json.loads(
            mock_agents["data_agent"].analyze_consumption_patterns.return_value["agent_response"]["completion"]
        )
        
        mock_agents["decision_agent"].evaluate_consumption_patterns.assert_called_once_with(
            data_analysis_response
        )
        
        decision_response = json.loads(
            mock_agents["decision_agent"].evaluate_consumption_patterns.return_value["agent_response"]["completion"]
        )
        
        mock_agents["execution_agent"].execute_actions.assert_called_once_with(
            {"actions": decision_response["actions"]}
        )
        
        # Verify the final result
        assert result["status"] == "success"
        assert "data_analysis" in result
        assert "decision" in result
        assert "execution" in result
    
    @patch('flows.orchestration.DataAnalysisAgent')
    def test_data_agent_error_handling(self, mock_data_agent, mock_agents, mock_config_file):
        """Test error handling when the data agent fails."""
        # Set up the data agent to return an error
        mock_agents["data_agent"].analyze_deal_quality.return_value = {
            "status": "error",
            "error": "Failed to analyze deal quality",
            "session_id": "data_error_123"
        }
        mock_data_agent.from_deployment_config.return_value = mock_agents["data_agent"]
        
        # Create the orchestrator
        orchestrator = RevOpsOrchestrator(config_path=mock_config_file)
        
        # Run the deal quality workflow
        result = orchestrator.run_deal_quality_flow()
        
        # Verify the error is propagated
        assert result["status"] == "error"
        assert "Failed to analyze deal quality" in result["error"]
        assert "data_analysis" in result
        assert "decision" not in result  # Decision agent should not be called
        assert "execution" not in result  # Execution agent should not be called
    
    @patch('flows.orchestration.DataAnalysisAgent')
    @patch('flows.orchestration.DecisionAgent')
    def test_decision_agent_error_handling(self, mock_decision_agent, mock_data_agent, 
                                          mock_agents, mock_config_file):
        """Test error handling when the decision agent fails."""
        # Set up the data agent to return success
        mock_data_agent.from_deployment_config.return_value = mock_agents["data_agent"]
        
        # Set up the decision agent to return an error
        mock_agents["decision_agent"].evaluate_consumption_patterns.return_value = {
            "status": "error",
            "error": "Failed to evaluate consumption patterns",
            "session_id": "decision_error_123"
        }
        mock_decision_agent.from_deployment_config.return_value = mock_agents["decision_agent"]
        
        # Create the orchestrator
        orchestrator = RevOpsOrchestrator(config_path=mock_config_file)
        
        # Run the consumption patterns workflow
        result = orchestrator.run_consumption_patterns_flow(timeframe="last_30_days")
        
        # Verify the error is propagated
        assert result["status"] == "error"
        assert "Failed to evaluate consumption patterns" in result["error"]
        assert "data_analysis" in result
        assert "decision" in result
        assert "execution" not in result  # Execution agent should not be called
    
    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client for testing."""
        with patch('boto3.client') as mock_boto_client:
            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3
            yield mock_s3
    
    @patch('flows.orchestration.DataAnalysisAgent')
    @patch('flows.orchestration.DecisionAgent')
    @patch('flows.orchestration.ExecutionAgent')
    def test_result_storage(self, mock_execution_agent, mock_decision_agent, 
                           mock_data_agent, mock_agents, mock_config_file, mock_s3_client):
        """Test that workflow results are properly stored to S3."""
        # Set up the agent class mocks
        mock_data_agent.from_deployment_config.return_value = mock_agents["data_agent"]
        mock_decision_agent.from_deployment_config.return_value = mock_agents["decision_agent"]
        mock_execution_agent.from_deployment_config.return_value = mock_agents["execution_agent"]
        
        # Create the orchestrator with result storage enabled
        orchestrator = RevOpsOrchestrator(config_path=mock_config_file)
        orchestrator.enable_result_storage("test-bucket", "results/")
        
        # Run the deal quality workflow
        result = orchestrator.run_deal_quality_flow()
        
        # Verify S3 client was called to store the results
        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args[1]
        assert call_args["Bucket"] == "test-bucket"
        assert call_args["Key"].startswith("results/deal_quality_")
        assert "Body" in call_args
        
        # Verify content of the stored data
        stored_data = json.loads(call_args["Body"])
        assert stored_data["status"] == "success"
        assert "data_analysis" in stored_data
        assert "decision" in stored_data
        assert "execution" in stored_data
