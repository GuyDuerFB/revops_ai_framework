"""
RevOps AI Framework V2 - Decision Agent

This module defines the Decision Agent responsible for analyzing business data,
making recommendations, and determining appropriate actions.
"""

import json
import os
import boto3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union

class DecisionAgent:
    """
    Decision Agent for the RevOps AI Framework V2 that integrates with Amazon Bedrock.
    Responsible for advanced reasoning and action planning based on analyzed data.
    """
    
    def __init__(
        self,
        agent_id: str = None,
        agent_alias_id: str = None,
        foundation_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        region_name: str = 'us-east-1',
        profile_name: Optional[str] = None
    ):
        """
        Initialize the Decision Agent with Bedrock Agent configuration.
        
        Args:
            agent_id (str): Bedrock Agent ID (if None, agent will be created during deployment)
            agent_alias_id (str): Bedrock Agent Alias ID
            foundation_model (str): Foundation model to use for the agent
            region_name (str): AWS region name
            profile_name (Optional[str]): AWS profile name
        """
        self.agent_id = agent_id
        self.agent_alias_id = agent_alias_id
        self.foundation_model = foundation_model
        self.region_name = region_name
        self.profile_name = profile_name
        
        # Initialize AWS clients
        self.bedrock_agent_runtime = self._get_bedrock_agent_runtime_client()
        self.bedrock_agent = self._get_bedrock_agent_client()
        
    def _get_bedrock_agent_runtime_client(self):
        """Get Bedrock Agent Runtime client with the specified region and profile."""
        session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
        return session.client('bedrock-agent-runtime')
    
    def _get_bedrock_agent_client(self):
        """Get Bedrock Agent client with the specified region and profile."""
        session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
        return session.client('bedrock-agent')
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for agent invocation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"decision_{timestamp}_{unique_id}"
    
    def _inject_date_context(self, input_text: str) -> str:
        """
        Inject current date and time context into the input text.
        This ensures the agent has temporal awareness for all requests.
        """
        now = datetime.now(timezone.utc)
        
        date_context = f"""
📅 **CURRENT DATE AND TIME CONTEXT:**
- Current Date: {now.strftime('%A, %B %d, %Y')}
- Current Time: {now.strftime('%H:%M UTC')}
- Current Quarter: Q{((now.month - 1) // 3) + 1} {now.year}
- Current Month: {now.strftime('%B %Y')}
- Current Year: {now.year}

**IMPORTANT**: Use this current date information to interpret all time-based references in the request. When interpreting "this quarter", "recent", "last month", etc., calculate these relative to the current date above.

---

**REQUEST:**
{input_text}
"""
        return date_context
        
    def invoke(self, input_text: str, session_id: Optional[str] = None, inject_date_context: bool = True) -> Dict[str, Any]:
        """
        Invoke the Decision Agent with a specific input prompt.
        
        Args:
            input_text (str): The prompt or query to send to the agent
            session_id (Optional[str]): Session ID for conversation context
            inject_date_context (bool): Whether to inject current date context (default: True)
            
        Returns:
            Dict[str, Any]: Agent response
        """
        if not session_id:
            session_id = self._generate_session_id()
        
        # Inject date context if requested
        if inject_date_context:
            enhanced_input = self._inject_date_context(input_text)
        else:
            enhanced_input = input_text
        
        try:
            # Invoke the Bedrock Agent using the agent-runtime client
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=enhanced_input,
                enableTrace=True
            )
            
            # Process response
            return {
                "agent_response": response,
                "session_id": session_id,
                "status": "success"
            }
        except Exception as e:
            return {
                "error": str(e),
                "session_id": session_id,
                "status": "error"
            }
    
    def evaluate_deal_quality(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate deal quality based on analysis data and determine actions.
        
        Args:
            analysis_data (Dict[str, Any]): Data from the Data Analysis Agent
            
        Returns:
            Dict[str, Any]: Evaluation results with recommended actions
        """
        # Convert analysis data to a suitable prompt
        prompt = self._construct_deal_evaluation_prompt(analysis_data)
        return self.invoke(prompt)
    
    def _construct_deal_evaluation_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """
        Construct a prompt for deal quality evaluation.
        
        Args:
            analysis_data (Dict[str, Any]): Analysis data from Data Analysis Agent
            
        Returns:
            str: Constructed prompt
        """
        # Format analysis data as JSON string
        analysis_json = json.dumps(analysis_data, indent=2)
        
        prompt = (
            "Based on the following deal quality analysis data, evaluate the health of our pipeline "
            "and recommend specific actions we should take for each identified issue or opportunity. "
            "Focus on:\n"
            "1. Prioritizing deals based on ICP alignment\n"
            "2. Addressing data quality issues\n"
            "3. Actions to overcome identified blockers\n"
            "4. Opportunities to enhance our pipeline\n\n"
            f"Analysis Data:\n{analysis_json}\n\n"
            "Please provide your evaluation and specific recommended actions."
        )
        return prompt
    
    def evaluate_consumption_patterns(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate consumption patterns and determine actions to take.
        
        Args:
            analysis_data (Dict[str, Any]): Consumption pattern analysis from Data Analysis Agent
            
        Returns:
            Dict[str, Any]: Evaluation with recommended actions
        """
        prompt = self._construct_consumption_evaluation_prompt(analysis_data)
        return self.invoke(prompt)
    
    def _construct_consumption_evaluation_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """
        Construct a prompt for consumption pattern evaluation.
        
        Args:
            analysis_data (Dict[str, Any]): Analysis data from Data Analysis Agent
            
        Returns:
            str: Constructed prompt
        """
        # Format analysis data as JSON string
        analysis_json = json.dumps(analysis_data, indent=2)
        
        prompt = (
            "Based on the following consumption pattern analysis, determine what actions we should take "
            "for each identified pattern. Consider:\n"
            "1. Proactive outreach for accounts with decreasing usage\n"
            "2. Resource allocation for accounts with increasing usage\n"
            "3. Pricing strategy adjustments\n"
            "4. Risk mitigation for identified anomalies\n\n"
            f"Analysis Data:\n{analysis_json}\n\n"
            "Please provide your evaluation and specific recommended actions for each account or pattern."
        )
        return prompt
    
    @classmethod
    def from_deployment_config(cls, config_path: str) -> 'DecisionAgent':
        """
        Create a DecisionAgent instance from a deployment configuration file.
        
        Args:
            config_path (str): Path to the deployment configuration file
            
        Returns:
            DecisionAgent: Initialized agent instance
        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return cls(
            agent_id=config.get('decision_agent', {}).get('agent_id'),
            agent_alias_id=config.get('decision_agent', {}).get('agent_alias_id'),
            foundation_model=config.get('decision_agent', {}).get('foundation_model', 
                                       "anthropic.claude-sonnet-4-20250514-v1:0"),
            region_name=config.get('region_name', 'us-east-1'),
            profile_name=config.get('profile_name')
        )
