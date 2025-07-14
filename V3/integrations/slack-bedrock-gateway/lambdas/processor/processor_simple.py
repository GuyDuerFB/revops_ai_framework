"""
Simplified Slack-Bedrock Processor - Working Version
Removes agent_tracer dependency that was causing startup failures.
"""

import json
import boto3
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import sys
import os

# Try to import requests, install if missing
try:
    import requests
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--target", "/tmp"])
    sys.path.insert(0, "/tmp")
    import requests

class SimpleSlackBedrockProcessor:
    """Simplified processor without tracing dependencies"""
    
    def __init__(self):
        from botocore.config import Config
        
        AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Configure extended timeouts for Bedrock Agent
        bedrock_config = Config(
            region_name=AWS_REGION,
            read_timeout=240,  # 4 minutes for complex analysis
            connect_timeout=60,
            retries={'max_attempts': 2}
        )
        
        self.secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)
        self.bedrock_agent = boto3.client('bedrock-agent-runtime', config=bedrock_config)
        
        # Agent configuration
        self.decision_agent_id = os.environ.get('BEDROCK_AGENT_ID', 'TCX9CGOKBR')
        self.decision_agent_alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'RSYE8T5V96')
        
        # Cache for secrets
        self._secrets_cache = {}
        self._cache_timestamp = 0
        
    def process_slack_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack event with temporal context injection"""
        
        try:
            print(f"Processing Slack event: {json.dumps(event)[:200]}...")
            
            # Extract event details
            if 'Records' in event and len(event['Records']) > 0:
                # SQS message format
                slack_event = json.loads(event['Records'][0]['body'])
            else:
                # Direct invocation
                slack_event = event
                
            user_query = slack_event.get('text', '')
            user_id = slack_event.get('user', '')
            channel = slack_event.get('channel', '')
            ts = slack_event.get('ts', '')
            
            print(f"User query: {user_query}")
            
            # Create correlation ID
            correlation_id = f"slack_{ts}_{user_id}" if ts and user_id else f"slack_{int(time.time())}"
            
            # Add temporal context to query
            current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            enhanced_query = f"""Current date: {current_date}

User Query: {user_query}

Please process this query following the comprehensive workflows and provide detailed analysis."""
            
            print(f"Enhanced query with temporal context: {enhanced_query[:100]}...")
            
            # Call Bedrock Agent
            response = self._invoke_bedrock_agent(enhanced_query, correlation_id)
            
            print(f"Bedrock response received: {len(str(response))} characters")
            
            # Send response to Slack (placeholder - actual implementation would use Slack API)
            agent_response = response.get('output', {}).get('text', 'I encountered an issue processing your request.')
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'success',
                    'correlation_id': correlation_id,
                    'response': agent_response[:100] + '...' if len(agent_response) > 100 else agent_response
                })
            }
            
        except Exception as e:
            print(f"Error processing Slack event: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'error',
                    'error': str(e)
                })
            }
    
    def _invoke_bedrock_agent(self, query: str, correlation_id: str) -> Dict[str, Any]:
        """Invoke Bedrock agent"""
        
        try:
            print(f"Invoking Bedrock agent {self.decision_agent_id} with query")
            
            response = self.bedrock_agent.invoke_agent(
                agentId=self.decision_agent_id,
                agentAliasId=self.decision_agent_alias_id,
                sessionId=correlation_id,
                inputText=query
            )
            
            # Process streaming response
            output_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk_data = event['chunk'].get('bytes', b'')
                    if chunk_data:
                        try:
                            chunk_json = json.loads(chunk_data.decode('utf-8'))
                            if 'outputText' in chunk_json:
                                output_text += chunk_json['outputText']
                        except json.JSONDecodeError:
                            # Handle non-JSON chunks
                            output_text += chunk_data.decode('utf-8', errors='ignore')
            
            print(f"Agent response length: {len(output_text)} characters")
            
            return {
                'output': {'text': output_text},
                'sessionId': correlation_id
            }
            
        except Exception as e:
            print(f"Error invoking Bedrock agent: {str(e)}")
            raise

def lambda_handler(event, context):
    """Lambda handler"""
    print(f"Lambda invoked with event: {json.dumps(event)[:500]}...")
    
    processor = SimpleSlackBedrockProcessor()
    return processor.process_slack_event(event)