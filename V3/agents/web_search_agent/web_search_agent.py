"""
RevOps AI Framework V2 - WebSearch Agent

This module defines the WebSearch Agent responsible for external intelligence gathering,
company research, and lead assessment through web search capabilities.
"""

import json
import os
import boto3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

class WebSearchAgent:
    """
    WebSearch Agent for the RevOps AI Framework V2 that integrates with Amazon Bedrock.
    Responsible for web search, company research, and lead intelligence gathering.
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
        Initialize the WebSearch Agent with Bedrock Agent configuration.
        
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
        return f"websearch_{timestamp}_{unique_id}"
        
    def invoke(self, input_text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke the WebSearch Agent with a specific input prompt.
        
        Args:
            input_text (str): The prompt or query to send to the agent
            session_id (Optional[str]): Session ID for conversation context
            
        Returns:
            Dict[str, Any]: Agent response
        """
        if not session_id:
            session_id = self._generate_session_id()
        
        try:
            # Invoke the Bedrock Agent using the agent-runtime client
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=input_text,
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
    
    def assess_lead(self, person_name: str, company_name: str, role: Optional[str] = None) -> Dict[str, Any]:
        """
        Assess a lead by researching both the person and company.
        
        Args:
            person_name (str): Name of the person to research
            company_name (str): Name of the company to research
            role (Optional[str]): Role/title of the person (e.g., "CEO", "CTO")
            
        Returns:
            Dict[str, Any]: Lead assessment results
        """
        role_text = f" [{role}]" if role else ""
        prompt = f"I need to assess if {person_name}{role_text} of {company_name} is a good lead. Please research both the company and the person to provide a comprehensive assessment."
        return self.invoke(prompt)
    
    def research_company(self, company_name: str, focus_area: str = "general") -> Dict[str, Any]:
        """
        Research a specific company with focused analysis.
        
        Args:
            company_name (str): Name of company to research
            focus_area (str): Focus area (general, funding, technology, size, news)
            
        Returns:
            Dict[str, Any]: Company research results
        """
        prompt = f"Use your research_company function to research {company_name} with focus on {focus_area}."
        return self.invoke(prompt)
    
    def search_web(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Perform a web search for the given query.
        
        Args:
            query (str): Search query
            num_results (int): Number of results to return
            
        Returns:
            Dict[str, Any]: Search results
        """
        prompt = f"Use your search_web function to search for '{query}' with {num_results} results."
        return self.invoke(prompt)
    
    def market_intelligence(self, topic: str, industry: Optional[str] = None) -> Dict[str, Any]:
        """
        Gather market intelligence on a specific topic or industry.
        
        Args:
            topic (str): Topic to research
            industry (Optional[str]): Specific industry focus
            
        Returns:
            Dict[str, Any]: Market intelligence results
        """
        industry_text = f" in the {industry} industry" if industry else ""
        prompt = f"Provide market intelligence on {topic}{industry_text}. Use your search functions to gather comprehensive information."
        return self.invoke(prompt)
    
    @classmethod
    def from_deployment_config(cls, config_path: str) -> 'WebSearchAgent':
        """
        Create a WebSearchAgent instance from a deployment configuration file.
        
        Args:
            config_path (str): Path to the deployment configuration file
            
        Returns:
            WebSearchAgent: Initialized agent instance
        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return cls(
            agent_id=config.get('web_search_agent', {}).get('agent_id'),
            agent_alias_id=config.get('web_search_agent', {}).get('agent_alias_id'),
            foundation_model=config.get('web_search_agent', {}).get('foundation_model', 
                                       "anthropic.claude-sonnet-4-20250514-v1:0"),
            region_name=config.get('region_name', 'us-east-1'),
            profile_name=config.get('profile_name')
        )