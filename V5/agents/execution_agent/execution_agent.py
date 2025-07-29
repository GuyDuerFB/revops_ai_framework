"""
RevOps AI Framework V2 - Execution Agent

This module defines the Execution Agent responsible for taking actions
based on decisions, including API calls, webhook triggers, and data updates.
"""

import json
import os
import boto3
import requests
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExecutionAgent:
    """
    Execution Agent for the RevOps AI Framework V2 that integrates with Amazon Bedrock.
    Responsible for taking actions based on decision agent outputs.
    """
    
    def __init__(
        self,
        agent_id: str = None,
        agent_alias_id: str = None,
        foundation_model: str = "anthropic.claude-sonnet-4-20250514-v1:0",
        region_name: str = 'us-east-1',
        profile_name: Optional[str] = None,
        webhook_config_path: Optional[str] = None
    ):
        """
        Initialize the Execution Agent with Bedrock Agent configuration.
        
        Args:
            agent_id (str): Bedrock Agent ID (if None, agent will be created during deployment)
            agent_alias_id (str): Bedrock Agent Alias ID
            foundation_model (str): Foundation model to use for the agent
            region_name (str): AWS region name
            profile_name (Optional[str]): AWS profile name
            webhook_config_path (Optional[str]): Path to webhook configuration file
        """
        self.agent_id = agent_id
        self.agent_alias_id = agent_alias_id
        self.foundation_model = foundation_model
        self.region_name = region_name
        self.profile_name = profile_name
        
        # Load webhook configurations if provided
        self.webhook_config = {}
        if webhook_config_path and os.path.exists(webhook_config_path):
            with open(webhook_config_path, 'r') as f:
                self.webhook_config = json.load(f)
        
        # Initialize AWS clients
        self.bedrock_agent_runtime = self._get_bedrock_agent_runtime_client()
        self.bedrock_agent = self._get_bedrock_agent_client()
        self.lambda_client = self._get_lambda_client()
        
    def _get_bedrock_agent_runtime_client(self):
        """Get Bedrock Agent Runtime client with the specified region and profile."""
        session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
        return session.client('bedrock-agent-runtime')
    
    def _get_bedrock_agent_client(self):
        """Get Bedrock Agent client with the specified region and profile."""
        session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
        return session.client('bedrock-agent')
    
    def _get_lambda_client(self):
        """Get Lambda client with the specified region and profile."""
        session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
        return session.client('lambda')
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID for agent invocation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"execution_{timestamp}_{unique_id}"
        
    def invoke(self, input_text: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke the Execution Agent with a specific input prompt.
        
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
            logger.error(f"Error invoking agent: {str(e)}")
            return {
                "error": str(e),
                "session_id": session_id,
                "status": "error"
            }
    
    def execute_actions(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute actions based on the action plan provided by the Decision Agent.
        
        Args:
            action_plan (Dict[str, Any]): Action plan from Decision Agent
            
        Returns:
            Dict[str, Any]: Execution results
        """
        results = {
            "executed_actions": [],
            "failed_actions": [],
            "status": "success"
        }
        
        try:
            # Process each action in the plan
            if 'actions' in action_plan:
                for action in action_plan['actions']:
                    action_type = action.get('type')
                    action_params = action.get('parameters', {})
                    
                    if action_type == 'webhook':
                        result = self.trigger_webhook(action_params)
                    elif action_type == 'firebolt_write':
                        result = self.write_to_firebolt(action_params)
                    elif action_type == 'zapier_integration':
                        result = self.trigger_zapier(action_params)
                    elif action_type == 'notification':
                        result = self.send_notification(action_params)
                    else:
                        result = {
                            "status": "error",
                            "message": f"Unknown action type: {action_type}"
                        }
                    
                    if result.get('status') == 'success':
                        results['executed_actions'].append({
                            "action": action,
                            "result": result
                        })
                    else:
                        results['failed_actions'].append({
                            "action": action,
                            "error": result.get('error', 'Unknown error')
                        })
            
            return results
        except Exception as e:
            logger.error(f"Error executing actions: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "executed_actions": results['executed_actions'],
                "failed_actions": results['failed_actions']
            }
    
    def trigger_webhook(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a webhook with the specified parameters.
        
        Args:
            parameters (Dict[str, Any]): Webhook parameters including URL and payload
            
        Returns:
            Dict[str, Any]: Webhook response
        """
        webhook_name = parameters.get('webhook_name')
        payload = parameters.get('payload', {})
        custom_url = parameters.get('url')
        
        try:
            # Get webhook URL from configuration or use custom URL
            webhook_url = None
            if webhook_name and webhook_name in self.webhook_config:
                webhook_url = self.webhook_config[webhook_name].get('url')
                # Merge configured headers if available
                headers = self.webhook_config[webhook_name].get('headers', {})
            else:
                webhook_url = custom_url
                headers = {"Content-Type": "application/json"}
            
            if not webhook_url:
                return {
                    "status": "error",
                    "error": f"No webhook URL found for {webhook_name}"
                }
            
            # Make the webhook request
            response = requests.post(webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            
            return {
                "status": "success",
                "response_code": response.status_code,
                "response_body": response.text
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook error: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def write_to_firebolt(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write data to Firebolt using Lambda function.
        
        Args:
            parameters (Dict[str, Any]): Parameters for Firebolt write operation
            
        Returns:
            Dict[str, Any]: Write operation result
        """
        try:
            # Get the Firebolt writer Lambda function name
            lambda_name = os.environ.get('FIREBOLT_WRITER_LAMBDA', 'firebolt-writer-lambda')
            
            # Invoke Lambda function
            response = self.lambda_client.invoke(
                FunctionName=lambda_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(parameters)
            )
            
            # Process Lambda response
            if response['StatusCode'] >= 200 and response['StatusCode'] < 300:
                payload = json.loads(response['Payload'].read())
                return {
                    "status": "success",
                    "lambda_response": payload
                }
            else:
                return {
                    "status": "error",
                    "error": f"Lambda invocation failed with status {response['StatusCode']}"
                }
        except Exception as e:
            logger.error(f"Firebolt write error: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def trigger_zapier(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a Zapier integration.
        
        Args:
            parameters (Dict[str, Any]): Zapier parameters including zap ID and data
            
        Returns:
            Dict[str, Any]: Zapier trigger result
        """
        zap_webhook_url = parameters.get('webhook_url')
        payload = parameters.get('payload', {})
        
        try:
            if not zap_webhook_url:
                return {
                    "status": "error",
                    "error": "No Zapier webhook URL provided"
                }
                
            # Make the Zapier webhook request
            response = requests.post(zap_webhook_url, json=payload)
            response.raise_for_status()
            
            return {
                "status": "success",
                "response_code": response.status_code,
                "response_body": response.text
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Zapier trigger error: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def send_notification(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send notification via configured channels.
        
        Args:
            parameters (Dict[str, Any]): Notification parameters
            
        Returns:
            Dict[str, Any]: Notification result
        """
        channel = parameters.get('channel', 'email')
        subject = parameters.get('subject', 'RevOps AI Framework Notification')
        message = parameters.get('message', '')
        recipients = parameters.get('recipients', [])
        
        try:
            if channel == 'email':
                return self._send_email_notification(subject, message, recipients)
            elif channel == 'slack':
                return self._send_slack_notification(message, parameters.get('slack_channel'))
            else:
                return {
                    "status": "error",
                    "error": f"Unknown notification channel: {channel}"
                }
        except Exception as e:
            logger.error(f"Notification error: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _send_email_notification(self, subject: str, message: str, recipients: List[str]) -> Dict[str, Any]:
        """
        Send email notification using AWS SES.
        
        Args:
            subject (str): Email subject
            message (str): Email message
            recipients (List[str]): List of email recipients
            
        Returns:
            Dict[str, Any]: Email send result
        """
        try:
            # Get SES client
            session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
            ses_client = session.client('ses')
            
            # Send email
            response = ses_client.send_email(
                Source=os.environ.get('EMAIL_SENDER', 'noreply@firebolt.io'),
                Destination={
                    'ToAddresses': recipients
                },
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': message}}
                }
            )
            
            return {
                "status": "success",
                "message_id": response['MessageId']
            }
        except Exception as e:
            logger.error(f"Email notification error: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _send_slack_notification(self, message: str, slack_channel: str) -> Dict[str, Any]:
        """
        Send Slack notification.
        
        Args:
            message (str): Message to send
            slack_channel (str): Slack channel
            
        Returns:
            Dict[str, Any]: Slack send result
        """
        try:
            # Get webhook URL from environment or config
            webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
            if not webhook_url and 'slack' in self.webhook_config:
                webhook_url = self.webhook_config['slack'].get('url')
                
            if not webhook_url:
                return {
                    "status": "error",
                    "error": "No Slack webhook URL configured"
                }
                
            # Send message to Slack
            payload = {
                "channel": slack_channel,
                "text": message
            }
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            return {
                "status": "success",
                "response_code": response.status_code
            }
        except Exception as e:
            logger.error(f"Slack notification error: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @classmethod
    def from_deployment_config(cls, config_path: str) -> 'ExecutionAgent':
        """
        Create an ExecutionAgent instance from a deployment configuration file.
        
        Args:
            config_path (str): Path to the deployment configuration file
            
        Returns:
            ExecutionAgent: Initialized agent instance
        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return cls(
            agent_id=config.get('execution_agent', {}).get('agent_id'),
            agent_alias_id=config.get('execution_agent', {}).get('agent_alias_id'),
            foundation_model=config.get('execution_agent', {}).get('foundation_model', 
                                       "anthropic.claude-sonnet-4-20250514-v1:0"),
            region_name=config.get('region_name', 'us-east-1'),
            profile_name=config.get('profile_name'),
            webhook_config_path=config.get('webhook_config_path')
        )
