"""
RevOps AI Framework V2 - Data Analysis Agent

This module defines the Data Analysis Agent responsible for retrieving and analyzing
data from various sources including Firebolt DWH, Gong, and Slack.
"""

import json
import os
import sys
import boto3
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union

# Add monitoring directory for tracer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'monitoring'))
from agent_tracer import AgentTracer, create_tracer, trace_agent_invocation, trace_data_operation, trace_error

class DataAnalysisAgent:
    """
    Data Analysis Agent for the RevOps AI Framework V2 that integrates with Amazon Bedrock.
    Responsible for retrieving and analyzing data from various sources with schema awareness.
    """
    
    def __init__(
        self,
        agent_id: str = None,
        agent_alias_id: str = None,
        foundation_model: str = "anthropic.claude-3-7-sonnet-20250219-v1:0",
        region_name: str = 'us-east-1',
        profile_name: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Initialize the Data Analysis Agent with Bedrock Agent configuration.
        
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
        
        # Initialize tracer
        self.tracer = create_tracer(correlation_id)
        
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
        return f"data_analysis_{timestamp}_{unique_id}"
    
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
        Invoke the Data Analysis Agent with a specific input prompt.
        
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
    
    def analyze_deal_quality(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze deal quality based on ICP alignment and other factors.
        
        Args:
            filters (Optional[Dict[str, Any]]): Filters to apply to the analysis
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        prompt = self._construct_deal_quality_prompt(filters)
        return self.invoke(prompt)
    
    def _construct_deal_quality_prompt(self, filters: Optional[Dict[str, Any]]) -> str:
        """
        Construct a prompt for deal quality analysis.
        
        Args:
            filters (Optional[Dict[str, Any]]): Filters to apply to the analysis
            
        Returns:
            str: Constructed prompt
        """
        base_prompt = (
            "Analyze our pipeline deals for quality assessment. "
            "Please provide insights on: "
            "1. How our current pipeline aligns with our Ideal Customer Profile (ICP) "
            "2. Quality of deal data (completeness and accuracy) "
            "3. Major use cases identified in the deals "
            "4. Potential blockers to deal progression\n\n"
        )
        
        if filters:
            filter_text = "Apply the following filters to your analysis:\n"
            for key, value in filters.items():
                filter_text += f"- {key}: {value}\n"
            base_prompt += filter_text
        
        return base_prompt
    
    def analyze_consumption_patterns(self, time_range: str, account_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze consumption patterns with anomaly detection.
        
        Args:
            time_range (str): Time range for analysis (e.g. "last_30_days", "last_quarter")
            account_filter (Optional[str]): Filter to specific account(s)
            
        Returns:
            Dict[str, Any]: Analysis results with identified patterns
        """
        prompt = self._construct_consumption_pattern_prompt(time_range, account_filter)
        return self.invoke(prompt)
    
    def _construct_consumption_pattern_prompt(self, time_range: str, account_filter: Optional[str]) -> str:
        """
        Construct a prompt for consumption pattern analysis.
        
        Args:
            time_range (str): Time range for analysis
            account_filter (Optional[str]): Filter to specific account(s)
            
        Returns:
            str: Constructed prompt
        """
        base_prompt = (
            f"Analyze consumption patterns for {time_range}. "
            "Please identify: "
            "1. Significant changes in consumption patterns "
            "2. Accounts with decreasing usage (potential churn risk) "
            "3. Accounts with unexpected spikes in usage "
            "4. Recommended actions for each identified pattern\n\n"
        )
        
        if account_filter:
            base_prompt += f"Focus your analysis on the following account(s): {account_filter}\n"
        
        return base_prompt
    
    @classmethod
    def from_deployment_config(cls, config_path: str) -> 'DataAnalysisAgent':
        """
        Create a DataAnalysisAgent instance from a deployment configuration file.
        
        Args:
            config_path (str): Path to the deployment configuration file
            
        Returns:
            DataAnalysisAgent: Initialized agent instance
        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return cls(
            agent_id=config.get('data_agent', {}).get('agent_id'),
            agent_alias_id=config.get('data_agent', {}).get('agent_alias_id'),
            foundation_model=config.get('data_agent', {}).get('foundation_model', 
                                       "anthropic.claude-sonnet-4-20250514-v1:0"),
            region_name=config.get('region_name', 'us-east-1'),
            profile_name=config.get('profile_name')
        )
