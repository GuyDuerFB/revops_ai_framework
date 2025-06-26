"""
Integration tests for the complete agent workflow.

This test demonstrates how the three agents (Data, Decision, Execution)
interact with each other in an end-to-end workflow.
"""

import json
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from agents.data_agent.data_agent import DataAnalysisAgent
from agents.decision_agent.decision_agent import DecisionAgent
from agents.execution_agent.execution_agent import ExecutionAgent

class TestAgentWorkflow:
    """Test cases for the end-to-end agent workflow."""
    
    @pytest.fixture
    def mock_firebolt_data(self):
        """Sample data that would be returned by Firebolt queries."""
        return {
            "deal_data": {
                "deals": [
                    {
                        "id": "d-001",
                        "company": "Acme Corp",
                        "industry": "Technology",
                        "deal_size": 150000,
                        "use_case": "Data Warehousing",
                        "region": "AMER",
                        "stage": "Negotiation"
                    },
                    {
                        "id": "d-002",
                        "company": "XYZ Inc",
                        "industry": "Healthcare",
                        "deal_size": 85000,
                        "use_case": "Business Intelligence",
                        "region": "EMEA",
                        "stage": "Discovery"
                    }
                ]
            },
            "consumption_data": {
                "accounts": [
                    {
                        "account_id": "a-001",
                        "company": "Acme Corp",
                        "last_month_usage": 1250,
                        "this_month_usage": 950,
                        "trend": "decreasing",
                        "percent_change": -24
                    },
                    {
                        "account_id": "a-002",
                        "company": "Globex Corp",
                        "last_month_usage": 875,
                        "this_month_usage": 1350,
                        "trend": "increasing",
                        "percent_change": 54
                    }
                ]
            }
        }
    
    @pytest.fixture
    def setup_agents(self, mock_bedrock_client, tmp_path):
        """Set up the three agents for testing."""
        # Create a config file for the agents
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
            "region_name": "us-east-1"
        }
        
        config_path = tmp_path / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Create the agents
        data_agent = DataAnalysisAgent.from_deployment_config(config_path)
        decision_agent = DecisionAgent.from_deployment_config(config_path)
        execution_agent = ExecutionAgent.from_deployment_config(config_path)
        
        return {
            "data_agent": data_agent,
            "decision_agent": decision_agent,
            "execution_agent": execution_agent,
            "config_path": config_path
        }
    
    def test_deal_quality_workflow(self, setup_agents, mock_bedrock_client, mock_firebolt_data):
        """Test the deal quality analysis workflow across all three agents."""
        # Extract the agents
        data_agent = setup_agents["data_agent"]
        decision_agent = setup_agents["decision_agent"]
        execution_agent = setup_agents["execution_agent"]
        
        # Mock the Bedrock Agent responses for each agent
        mock_responses = {
            # Data agent response with analysis
            "test-data-agent-id": {
                "completion": json.dumps({
                    "icp_alignment": {
                        "Acme Corp": 0.85,
                        "XYZ Inc": 0.62
                    },
                    "data_quality": {
                        "completeness": 0.78,
                        "issues": ["Missing contact information for 2 deals"]
                    },
                    "use_cases": ["Data Warehousing", "Business Intelligence"],
                    "blockers": ["Budget constraints for XYZ Inc"]
                }),
                "stopReason": "COMPLETE"
            },
            # Decision agent response with recommendations
            "test-decision-agent-id": {
                "completion": json.dumps({
                    "priority_deals": ["d-001"],
                    "recommendations": [
                        {
                            "deal_id": "d-001",
                            "action": "Accelerate",
                            "rationale": "High ICP alignment and advanced stage"
                        },
                        {
                            "deal_id": "d-002",
                            "action": "Gather more information",
                            "rationale": "Lower ICP alignment, early stage"
                        }
                    ],
                    "actions": [
                        {
                            "type": "notification",
                            "parameters": {
                                "channel": "email",
                                "subject": "Deal Prioritization Update",
                                "message": "Acme Corp deal should be prioritized",
                                "recipients": ["sales@example.com"]
                            }
                        }
                    ]
                }),
                "stopReason": "COMPLETE"
            },
            # Execution agent response with action results
            "test-execution-agent-id": {
                "completion": json.dumps({
                    "executed_actions": [
                        {
                            "action_type": "notification",
                            "status": "success",
                            "message": "Email notification sent to sales@example.com"
                        }
                    ],
                    "summary": "All actions executed successfully"
                }),
                "stopReason": "COMPLETE"
            }
        }

        # Configure mock to return different responses based on agent ID
        def mock_invoke_side_effect(**kwargs):
            agent_id = kwargs.get('agentId')
            return mock_responses.get(agent_id, {
                "completion": "Default mock response",
                "stopReason": "COMPLETE"
            })
        
        mock_bedrock_client.invoke_agent.side_effect = mock_invoke_side_effect
        
        # 1. Execute the Data Analysis Agent
        data_analysis_result = data_agent.analyze_deal_quality()
        assert data_analysis_result["status"] == "success"
        
        # Extract the data analysis results
        data_analysis_response = json.loads(data_analysis_result["agent_response"]["completion"])
        
        # 2. Pass the results to the Decision Agent
        decision_result = decision_agent.evaluate_deal_quality(data_analysis_response)
        assert decision_result["status"] == "success"
        
        # Extract the decision results
        decision_response = json.loads(decision_result["agent_response"]["completion"])
        
        # 3. Pass the actions to the Execution Agent
        execution_result = execution_agent.execute_actions({"actions": decision_response["actions"]})
        
        # 4. Verify the complete workflow
        assert "executed_actions" in execution_result
        assert len(execution_result["executed_actions"]) > 0
        assert execution_result["status"] == "success"
        
        # 5. Verify that each agent was called with the correct parameters
        assert mock_bedrock_client.invoke_agent.call_count == 3
        
    def test_consumption_patterns_workflow(self, setup_agents, mock_bedrock_client, mock_firebolt_data):
        """Test the consumption pattern analysis workflow across all three agents."""
        # Extract the agents
        data_agent = setup_agents["data_agent"]
        decision_agent = setup_agents["decision_agent"]
        execution_agent = setup_agents["execution_agent"]
        
        # Mock the Bedrock Agent responses for each agent
        mock_responses = {
            # Data agent response with analysis
            "test-data-agent-id": {
                "completion": json.dumps({
                    "accounts": {
                        "Acme Corp": {
                            "trend": "decreasing",
                            "change_percent": -24,
                            "risk_level": "high"
                        },
                        "Globex Corp": {
                            "trend": "increasing",
                            "change_percent": 54,
                            "opportunity": "upsell"
                        }
                    },
                    "anomalies": [
                        {
                            "account": "Acme Corp",
                            "type": "sudden_drop",
                            "severity": "high"
                        }
                    ]
                }),
                "stopReason": "COMPLETE"
            },
            # Decision agent response with recommendations
            "test-decision-agent-id": {
                "completion": json.dumps({
                    "recommendations": [
                        {
                            "account": "Acme Corp",
                            "action": "Immediate outreach",
                            "rationale": "High risk of churn due to decreasing usage"
                        },
                        {
                            "account": "Globex Corp",
                            "action": "Schedule expansion discussion",
                            "rationale": "Potential upsell opportunity"
                        }
                    ],
                    "actions": [
                        {
                            "type": "webhook",
                            "parameters": {
                                "url": "https://example.com/webhook",
                                "payload": {
                                    "account": "Acme Corp",
                                    "action": "create_task",
                                    "priority": "high",
                                    "assignee": "customer_success_team"
                                }
                            }
                        },
                        {
                            "type": "firebolt_write",
                            "parameters": {
                                "table": "insights",
                                "operation": "insert",
                                "data": {
                                    "account_id": "a-001",
                                    "insight_type": "churn_risk",
                                    "priority": "high",
                                    "created_at": "2025-06-26"
                                }
                            }
                        }
                    ]
                }),
                "stopReason": "COMPLETE"
            }
        }

        # Configure mock to return different responses based on agent ID
        def mock_invoke_side_effect(**kwargs):
            agent_id = kwargs.get('agentId')
            return mock_responses.get(agent_id, {
                "completion": "Default mock response",
                "stopReason": "COMPLETE"
            })
        
        mock_bedrock_client.invoke_agent.side_effect = mock_invoke_side_effect
        
        # Mock the execution agent's webhook and firebolt_write methods
        execution_agent.trigger_webhook = MagicMock(return_value={
            "status": "success",
            "response_code": 200,
            "response_body": "Webhook executed"
        })
        
        execution_agent.write_to_firebolt = MagicMock(return_value={
            "status": "success",
            "lambda_response": {"rows_affected": 1}
        })
        
        # 1. Execute the Data Analysis Agent
        data_analysis_result = data_agent.analyze_consumption_patterns("last_30_days")
        assert data_analysis_result["status"] == "success"
        
        # Extract the data analysis results
        data_analysis_response = json.loads(data_analysis_result["agent_response"]["completion"])
        
        # 2. Pass the results to the Decision Agent
        decision_result = decision_agent.evaluate_consumption_patterns(data_analysis_response)
        assert decision_result["status"] == "success"
        
        # Extract the decision results
        decision_response = json.loads(decision_result["agent_response"]["completion"])
        
        # 3. Pass the actions to the Execution Agent
        execution_result = execution_agent.execute_actions({"actions": decision_response["actions"]})
        
        # 4. Verify the complete workflow
        assert execution_result["status"] == "success"
        assert len(execution_result["executed_actions"]) == 2
        assert len(execution_result["failed_actions"]) == 0
        
        # 5. Verify the execution methods were called correctly
        execution_agent.trigger_webhook.assert_called_once()
        execution_agent.write_to_firebolt.assert_called_once()
        
        # Verify webhook payload
        webhook_call = execution_agent.trigger_webhook.call_args[0][0]
        assert webhook_call["url"] == "https://example.com/webhook"
        assert webhook_call["payload"]["account"] == "Acme Corp"
        
        # Verify Firebolt write data
        firebolt_call = execution_agent.write_to_firebolt.call_args[0][0]
        assert firebolt_call["table"] == "insights"
        assert firebolt_call["data"]["account_id"] == "a-001"
