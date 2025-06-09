"""
RevOps AI Framework V2 - Flow Orchestrator

This module defines the Flow Orchestrator responsible for coordinating the
execution of multi-agent flows for different RevOps scenarios.
"""

import json
import os
import boto3
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Agent imports
from ..agents.data_agent.data_agent import DataAnalysisAgent
from ..agents.decision_agent.decision_agent import DecisionAgent
from ..agents.execution_agent.execution_agent import ExecutionAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FlowOrchestrator:
    """
    Flow Orchestrator for the RevOps AI Framework V2.
    Coordinates multi-agent flows for different business scenarios.
    """
    
    def __init__(
        self,
        config_path: str,
        region_name: str = 'us-east-1',
        profile_name: Optional[str] = None
    ):
        """
        Initialize the Flow Orchestrator.
        
        Args:
            config_path (str): Path to the configuration file
            region_name (str): AWS region name
            profile_name (Optional[str]): AWS profile name
        """
        self.region_name = region_name
        self.profile_name = profile_name
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize agents
        self.data_agent = DataAnalysisAgent.from_deployment_config(config_path)
        self.decision_agent = DecisionAgent.from_deployment_config(config_path)
        self.execution_agent = ExecutionAgent.from_deployment_config(config_path)
        
        # Initialize AWS clients
        self.bedrock_agent_runtime = self._get_bedrock_agent_runtime_client()
        
    def _get_bedrock_agent_runtime_client(self):
        """Get Bedrock Agent Runtime client with the specified region and profile."""
        session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
        return session.client('bedrock-agent-runtime')
    
    def _generate_flow_id(self) -> str:
        """Generate a unique flow ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"flow_{timestamp}_{unique_id}"
    
    def execute_deal_quality_flow(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the Deal Quality assessment flow.
        
        Args:
            filters (Optional[Dict[str, Any]]): Filters to apply to the analysis
            
        Returns:
            Dict[str, Any]: Flow execution results
        """
        flow_id = self._generate_flow_id()
        logger.info(f"Starting Deal Quality flow with ID: {flow_id}")
        
        results = {
            "flow_id": flow_id,
            "status": "success",
            "steps": []
        }
        
        try:
            # Step 1: Data Analysis
            logger.info(f"Flow {flow_id}: Executing Data Analysis step")
            data_analysis = self.data_agent.analyze_deal_quality(filters)
            
            results["steps"].append({
                "step_name": "data_analysis",
                "status": data_analysis.get("status", "unknown"),
                "timestamp": datetime.now().isoformat()
            })
            
            if data_analysis.get("status") != "success":
                results["status"] = "error"
                results["error"] = f"Data Analysis failed: {data_analysis.get('error', 'Unknown error')}"
                return results
            
            # Step 2: Decision Making
            logger.info(f"Flow {flow_id}: Executing Decision Making step")
            decision = self.decision_agent.evaluate_deal_quality(data_analysis.get("agent_response", {}))
            
            results["steps"].append({
                "step_name": "decision_making",
                "status": decision.get("status", "unknown"),
                "timestamp": datetime.now().isoformat()
            })
            
            if decision.get("status") != "success":
                results["status"] = "error"
                results["error"] = f"Decision Making failed: {decision.get('error', 'Unknown error')}"
                return results
            
            # Step 3: Execution
            logger.info(f"Flow {flow_id}: Executing Action step")
            execution = self.execution_agent.execute_actions(decision.get("agent_response", {}))
            
            results["steps"].append({
                "step_name": "execution",
                "status": execution.get("status", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "actions_executed": len(execution.get("executed_actions", [])),
                "actions_failed": len(execution.get("failed_actions", []))
            })
            
            # Add summary
            results["summary"] = {
                "total_actions_executed": len(execution.get("executed_actions", [])),
                "total_actions_failed": len(execution.get("failed_actions", [])),
                "completion_time": datetime.now().isoformat()
            }
            
            # Log completion
            logger.info(f"Completed Deal Quality flow {flow_id} with status: {results['status']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Deal Quality flow {flow_id}: {str(e)}")
            results["status"] = "error"
            results["error"] = str(e)
            return results
    
    def execute_consumption_pattern_flow(self, time_range: str, account_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the Consumption Pattern analysis flow.
        
        Args:
            time_range (str): Time range for analysis (e.g. "last_30_days", "last_quarter")
            account_filter (Optional[str]): Filter to specific account(s)
            
        Returns:
            Dict[str, Any]: Flow execution results
        """
        flow_id = self._generate_flow_id()
        logger.info(f"Starting Consumption Pattern flow with ID: {flow_id}")
        
        results = {
            "flow_id": flow_id,
            "status": "success",
            "steps": []
        }
        
        try:
            # Step 1: Data Analysis
            logger.info(f"Flow {flow_id}: Executing Data Analysis step")
            data_analysis = self.data_agent.analyze_consumption_patterns(time_range, account_filter)
            
            results["steps"].append({
                "step_name": "data_analysis",
                "status": data_analysis.get("status", "unknown"),
                "timestamp": datetime.now().isoformat()
            })
            
            if data_analysis.get("status") != "success":
                results["status"] = "error"
                results["error"] = f"Data Analysis failed: {data_analysis.get('error', 'Unknown error')}"
                return results
            
            # Step 2: Decision Making
            logger.info(f"Flow {flow_id}: Executing Decision Making step")
            decision = self.decision_agent.evaluate_consumption_patterns(data_analysis.get("agent_response", {}))
            
            results["steps"].append({
                "step_name": "decision_making",
                "status": decision.get("status", "unknown"),
                "timestamp": datetime.now().isoformat()
            })
            
            if decision.get("status") != "success":
                results["status"] = "error"
                results["error"] = f"Decision Making failed: {decision.get('error', 'Unknown error')}"
                return results
            
            # Step 3: Execution
            logger.info(f"Flow {flow_id}: Executing Action step")
            execution = self.execution_agent.execute_actions(decision.get("agent_response", {}))
            
            results["steps"].append({
                "step_name": "execution",
                "status": execution.get("status", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "actions_executed": len(execution.get("executed_actions", [])),
                "actions_failed": len(execution.get("failed_actions", []))
            })
            
            # Add summary
            results["summary"] = {
                "total_actions_executed": len(execution.get("executed_actions", [])),
                "total_actions_failed": len(execution.get("failed_actions", [])),
                "completion_time": datetime.now().isoformat()
            }
            
            # Log completion
            logger.info(f"Completed Consumption Pattern flow {flow_id} with status: {results['status']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in Consumption Pattern flow {flow_id}: {str(e)}")
            results["status"] = "error"
            results["error"] = str(e)
            return results
    
    def create_bedrock_flow(self, flow_name: str, flow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Bedrock Flow using the AWS Bedrock API.
        
        Args:
            flow_name (str): Name of the flow
            flow_definition (Dict[str, Any]): Flow definition
            
        Returns:
            Dict[str, Any]: Created flow details
        """
        try:
            # Get bedrock agent client
            session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
            bedrock_client = session.client('bedrock')
            
            # Create the flow
            response = bedrock_client.create_flow(
                name=flow_name,
                definition=flow_definition,
                executionRoleArn=self.config.get("flow_execution_role_arn")
            )
            
            return {
                "status": "success",
                "flow_id": response.get("flowId"),
                "flow_version": response.get("flowVersion")
            }
            
        except Exception as e:
            logger.error(f"Error creating Bedrock flow: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    def generate_deal_quality_flow_definition() -> Dict[str, Any]:
        """
        Generate a Bedrock Flow definition for the Deal Quality assessment flow.
        
        Returns:
            Dict[str, Any]: Flow definition
        """
        flow_definition = {
            "nodes": [
                {
                    "id": "data_analysis",
                    "type": "agent",
                    "configuration": {
                        "agentId": "${data_agent_id}",
                        "agentAliasId": "${data_agent_alias_id}"
                    },
                    "inputs": {
                        "prompt": "Analyze our deal quality based on the following filters: ${filters}"
                    }
                },
                {
                    "id": "decision_making",
                    "type": "agent",
                    "configuration": {
                        "agentId": "${decision_agent_id}",
                        "agentAliasId": "${decision_agent_alias_id}"
                    },
                    "inputs": {
                        "prompt": "Evaluate the deal quality based on this analysis: ${data_analysis.output}"
                    }
                },
                {
                    "id": "execution",
                    "type": "agent",
                    "configuration": {
                        "agentId": "${execution_agent_id}",
                        "agentAliasId": "${execution_agent_alias_id}"
                    },
                    "inputs": {
                        "prompt": "Execute the following actions: ${decision_making.output}"
                    }
                }
            ],
            "connections": [
                {
                    "source": "data_analysis",
                    "target": "decision_making"
                },
                {
                    "source": "decision_making",
                    "target": "execution"
                }
            ],
            "variables": [
                {
                    "name": "filters",
                    "type": "string"
                },
                {
                    "name": "data_agent_id",
                    "type": "string"
                },
                {
                    "name": "data_agent_alias_id",
                    "type": "string"
                },
                {
                    "name": "decision_agent_id",
                    "type": "string"
                },
                {
                    "name": "decision_agent_alias_id",
                    "type": "string"
                },
                {
                    "name": "execution_agent_id",
                    "type": "string"
                },
                {
                    "name": "execution_agent_alias_id",
                    "type": "string"
                }
            ]
        }
        
        return flow_definition
    
    @staticmethod
    def generate_consumption_pattern_flow_definition() -> Dict[str, Any]:
        """
        Generate a Bedrock Flow definition for the Consumption Pattern analysis flow.
        
        Returns:
            Dict[str, Any]: Flow definition
        """
        flow_definition = {
            "nodes": [
                {
                    "id": "data_analysis",
                    "type": "agent",
                    "configuration": {
                        "agentId": "${data_agent_id}",
                        "agentAliasId": "${data_agent_alias_id}"
                    },
                    "inputs": {
                        "prompt": "Analyze consumption patterns for ${time_range} ${account_filter_prompt}"
                    }
                },
                {
                    "id": "decision_making",
                    "type": "agent",
                    "configuration": {
                        "agentId": "${decision_agent_id}",
                        "agentAliasId": "${decision_agent_alias_id}"
                    },
                    "inputs": {
                        "prompt": "Evaluate these consumption patterns and recommend actions: ${data_analysis.output}"
                    }
                },
                {
                    "id": "execution",
                    "type": "agent",
                    "configuration": {
                        "agentId": "${execution_agent_id}",
                        "agentAliasId": "${execution_agent_alias_id}"
                    },
                    "inputs": {
                        "prompt": "Execute the following actions: ${decision_making.output}"
                    }
                }
            ],
            "connections": [
                {
                    "source": "data_analysis",
                    "target": "decision_making"
                },
                {
                    "source": "decision_making",
                    "target": "execution"
                }
            ],
            "variables": [
                {
                    "name": "time_range",
                    "type": "string"
                },
                {
                    "name": "account_filter_prompt",
                    "type": "string"
                },
                {
                    "name": "data_agent_id",
                    "type": "string"
                },
                {
                    "name": "data_agent_alias_id",
                    "type": "string"
                },
                {
                    "name": "decision_agent_id",
                    "type": "string"
                },
                {
                    "name": "decision_agent_alias_id",
                    "type": "string"
                },
                {
                    "name": "execution_agent_id",
                    "type": "string"
                },
                {
                    "name": "execution_agent_alias_id",
                    "type": "string"
                }
            ]
        }
        
        return flow_definition
