"""
Complete Slack-Bedrock Processor with Full Tracing
Combines working Slack integration with comprehensive agent tracing functionality.
"""

import json
import boto3
import time
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from contextlib import contextmanager
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

# Embedded AgentTracer to avoid import issues
class EventType(Enum):
    """Types of events to trace"""
    CONVERSATION_START = "CONVERSATION_START"
    CONVERSATION_END = "CONVERSATION_END"
    AGENT_INVOKE = "AGENT_INVOKE"
    AGENT_RESPONSE = "AGENT_RESPONSE"
    DATA_OPERATION = "DATA_OPERATION"
    DECISION_LOGIC = "DECISION_LOGIC"
    ERROR = "ERROR"
    TEMPORAL_CONTEXT = "TEMPORAL_CONTEXT"
    WORKFLOW_SELECTION = "WORKFLOW_SELECTION"

class AgentTracer:
    """Enhanced tracing for agent interactions and decisions"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.session_start = datetime.now(timezone.utc)
        self._setup_loggers()
        
    def _setup_loggers(self):
        """Setup structured loggers for different trace categories"""
        self.conversation_logger = logging.getLogger('revops-ai.conversation-trace')
        self.collaboration_logger = logging.getLogger('revops-ai.agent-collaboration')
        self.data_logger = logging.getLogger('revops-ai.data-operations')
        self.decision_logger = logging.getLogger('revops-ai.decision-logic') 
        self.error_logger = logging.getLogger('revops-ai.error-analysis')
        
        for logger in [self.conversation_logger, self.collaboration_logger, 
                      self.data_logger, self.decision_logger, self.error_logger]:
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
    
    def trace_conversation_start(self, user_query: str, user_id: str, channel: str, 
                                temporal_context: Optional[str] = None):
        """Trace the start of a conversation"""
        event_data = {
            "event_type": EventType.CONVERSATION_START.value,
            "correlation_id": self.correlation_id,
            "user_query": user_query,
            "user_id": user_id,
            "channel": channel,
            "temporal_context": temporal_context,
            "session_start": self.session_start.isoformat(),
            "query_length": len(user_query),
            "query_type": self._classify_query_type(user_query)
        }
        self.conversation_logger.info(json.dumps(event_data))
        
    def trace_conversation_end(self, response_summary: str, total_agents_used: int,
                              processing_time_ms: int, success: bool):
        """Trace the end of a conversation"""
        event_data = {
            "event_type": EventType.CONVERSATION_END.value,
            "correlation_id": self.correlation_id,
            "response_summary": response_summary[:200] + "..." if len(response_summary) > 200 else response_summary,
            "total_agents_used": total_agents_used,
            "processing_time_ms": processing_time_ms,
            "success": success,
            "session_duration_ms": int((datetime.now(timezone.utc) - self.session_start).total_seconds() * 1000)
        }
        self.conversation_logger.info(json.dumps(event_data))
    
    def trace_agent_invocation(self, source_agent: str, target_agent: str, 
                              collaboration_type: str, reasoning: str):
        """Trace agent-to-agent collaboration"""
        event_data = {
            "event_type": EventType.AGENT_INVOKE.value,
            "correlation_id": self.correlation_id,
            "source_agent": source_agent,
            "target_agent": target_agent,
            "collaboration_type": collaboration_type,
            "reasoning": reasoning,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.collaboration_logger.info(json.dumps(event_data))
        
    def trace_data_operation(self, operation_type: str, data_source: str, 
                           query_summary: str, result_count: Optional[int] = None,
                           execution_time_ms: Optional[int] = None, 
                           error_message: Optional[str] = None):
        """Trace data retrieval operations"""
        event_data = {
            "event_type": EventType.DATA_OPERATION.value,
            "correlation_id": self.correlation_id,
            "operation_type": operation_type,
            "data_source": data_source,
            "query_summary": query_summary,
            "result_count": result_count,
            "execution_time_ms": execution_time_ms,
            "success": error_message is None,
            "error_message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.data_logger.info(json.dumps(event_data))
    
    def trace_error(self, error_type: str, error_message: str, 
                   agent_context: str, stack_trace: Optional[str] = None):
        """Trace errors for analysis"""
        event_data = {
            "event_type": EventType.ERROR.value,
            "correlation_id": self.correlation_id,
            "error_type": error_type,
            "error_message": error_message,
            "agent_context": agent_context,
            "stack_trace": stack_trace,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.error_logger.error(json.dumps(event_data))
    
    def _classify_query_type(self, query: str) -> str:
        """Classify query type for analysis"""
        query_lower = query.lower()
        if any(word in query_lower for word in ['deal', 'opportunity', 'status', 'probability']):
            return 'DEAL_ANALYSIS'
        elif any(word in query_lower for word in ['lead', 'assess', 'qualify']):
            return 'LEAD_ASSESSMENT'
        elif any(word in query_lower for word in ['consumption', 'usage', 'fbu', 'revenue']):
            return 'CONSUMPTION_ANALYSIS'
        elif any(word in query_lower for word in ['churn', 'risk', 'health']):
            return 'RISK_ASSESSMENT'
        elif any(word in query_lower for word in ['call', 'conversation', 'gong']):
            return 'CALL_ANALYSIS'
        else:
            return 'GENERAL_QUERY'

class CompleteSlackBedrockProcessor:
    """Complete processor with working Slack integration and full tracing"""
    
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
        self.CACHE_TTL = 300  # 5 minutes
        
        # Environment variables for Slack integration
        self.secrets_arn = os.environ.get('SECRETS_ARN', 'arn:aws:secretsmanager:us-east-1:740202120544:secret:revops-slack-bedrock-secrets-372buh')
        
        # Tracer for this session
        self.tracer = None
    
    def get_current_date_context(self) -> str:
        """Get current date and time context for agents"""
        now = datetime.now(timezone.utc)
        
        date_context = f"""
📅 **CURRENT DATE AND TIME CONTEXT:**
- Current Date: {now.strftime('%A, %B %d, %Y')}
- Current Time: {now.strftime('%H:%M UTC')}
- Current Quarter: Q{((now.month - 1) // 3) + 1} {now.year}
- Current Month: {now.strftime('%B %Y')}
- Current Year: {now.year}

**IMPORTANT**: Use this current date information to interpret all time-based references in the user's request.

---

"""
        return date_context

    def process_slack_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack event with full tracing and working Slack responses"""
        
        start_time = time.time()
        
        try:
            print(f"Processing Slack event: {json.dumps(event)[:200]}...")
            
            # Extract event details - handle both SQS and direct formats
            if 'Records' in event and len(event['Records']) > 0:
                slack_event = json.loads(event['Records'][0]['body'])
            else:
                slack_event = event
                
            user_query = slack_event.get('message_text') or slack_event.get('text', '')
            user_id = slack_event.get('user_id') or slack_event.get('user', '')
            channel_id = slack_event.get('channel_id') or slack_event.get('channel', '')
            thread_ts = slack_event.get('thread_ts')
            response_message_ts = slack_event.get('response_message_ts')
            
            print(f"Extracted: user={user_id}, channel={channel_id}, thread={thread_ts}")
            
            # Create correlation ID and tracer
            correlation_id = f"slack_{thread_ts or int(time.time())}_{user_id}" if user_id else f"slack_{int(time.time())}"
            self.tracer = AgentTracer(correlation_id)
            
            # Add temporal context to query
            current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            date_context = self.get_current_date_context()
            enhanced_query = f"{date_context}**USER REQUEST:**\n{user_query}"
            
            print(f"Enhanced query with temporal context: {enhanced_query[:100]}...")
            
            # Trace conversation start
            self.tracer.trace_conversation_start(
                user_query=user_query,
                user_id=user_id,
                channel=channel_id,
                temporal_context=current_date
            )
            
            # Create session ID for Bedrock
            session_id = f"{user_id}:{channel_id}:{thread_ts}" if thread_ts else f"{user_id}:{channel_id}"
            
            # Call Bedrock Agent with progress updates
            response = self._invoke_bedrock_agent_with_progress(
                enhanced_query, 
                session_id,
                channel_id,
                response_message_ts,
                thread_ts
            )
            
            agent_response = response.get('output', {}).get('text', 'I encountered an issue processing your request.')
            print(f"Bedrock response received: {len(str(response))} characters")
            
            # Send final response back to Slack
            success = self._send_final_slack_response(slack_event, agent_response, response_message_ts)
            
            # Trace conversation end
            processing_time_ms = int((time.time() - start_time) * 1000)
            self.tracer.trace_conversation_end(
                response_summary=agent_response[:200],
                total_agents_used=1,  # At minimum, the Decision Agent
                processing_time_ms=processing_time_ms,
                success=success
            )
            
            if success:
                print(f"Successfully sent response to Slack")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'success',
                        'correlation_id': correlation_id,
                        'processing_time_ms': processing_time_ms,
                        'response_sent': True
                    })
                }
            else:
                print(f"Failed to send response to Slack")
                return {
                    'statusCode': 200,  # Still 200 since processing succeeded
                    'body': json.dumps({
                        'status': 'success',
                        'correlation_id': correlation_id,
                        'processing_time_ms': processing_time_ms,
                        'response_sent': False,
                        'response': agent_response[:100] + '...' if len(agent_response) > 100 else agent_response
                    })
                }
            
        except Exception as e:
            print(f"Error processing Slack event: {str(e)}")
            import traceback
            stack_trace = traceback.format_exc()
            print(f"Full traceback: {stack_trace}")
            
            # Trace error
            if self.tracer:
                self.tracer.trace_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    agent_context="SlackBedrockProcessor.process_slack_event",
                    stack_trace=stack_trace
                )
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'error',
                    'error': str(e)
                })
            }
    
    def _invoke_bedrock_agent_with_progress(self, query: str, session_id: str, 
                                          channel_id: str, message_ts: str, thread_ts: str) -> Dict[str, Any]:
        """Invoke Bedrock agent with progress updates"""
        
        try:
            print(f"Invoking Bedrock agent {self.decision_agent_id} with session {session_id}")
            
            # Trace agent invocation
            if self.tracer:
                self.tracer.trace_agent_invocation(
                    source_agent="SlackProcessor",
                    target_agent="DecisionAgent",
                    collaboration_type="USER_QUERY_PROCESSING",
                    reasoning="Processing user query through decision agent workflow"
                )
            
            # Send initial progress update
            if message_ts and channel_id:
                self._send_progress_update(channel_id, message_ts, "🧠 *Planning my approach* - analyzing your request", thread_ts)
            
            response = self.bedrock_agent.invoke_agent(
                agentId=self.decision_agent_id,
                agentAliasId=self.decision_agent_alias_id,
                sessionId=session_id,
                inputText=query
            )
            
            # Process streaming response with progress updates
            output_text = ""
            progress_sent = False
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk_data = event['chunk'].get('bytes', b'')
                    if chunk_data:
                        try:
                            chunk_json = json.loads(chunk_data.decode('utf-8'))
                            if 'outputText' in chunk_json:
                                output_text += chunk_json['outputText']
                                
                                # Send progress update if we have substantial content
                                if not progress_sent and len(output_text) > 50 and message_ts:
                                    self._send_progress_update(channel_id, message_ts, "📊 *Analyzing data* - gathering insights", thread_ts)
                                    progress_sent = True
                                    
                        except json.JSONDecodeError:
                            output_text += chunk_data.decode('utf-8', errors='ignore')
                
                # Parse orchestration traces for more detailed progress
                if 'trace' in event and message_ts:
                    progress_msg = self._parse_trace_to_progress(event['trace'])
                    if progress_msg:
                        self._send_progress_update(channel_id, message_ts, progress_msg, thread_ts)
            
            print(f"Agent response length: {len(output_text)} characters")
            
            return {
                'output': {'text': output_text},
                'sessionId': session_id
            }
            
        except Exception as e:
            print(f"Error invoking Bedrock agent: {str(e)}")
            if self.tracer:
                self.tracer.trace_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    agent_context="BedrockAgentInvocation"
                )
            raise
    
    def _parse_trace_to_progress(self, trace_event: dict) -> Optional[str]:
        """Convert Bedrock Agent orchestration trace to progress message"""
        try:
            if 'orchestrationTrace' not in trace_event:
                return None
                
            orch_trace = trace_event['orchestrationTrace']
            
            # Agent thinking/reasoning
            if 'rationale' in orch_trace:
                rationale = orch_trace['rationale'].get('text', '')
                if rationale and len(rationale.strip()) > 10:
                    clean_rationale = rationale.replace('\n', ' ').strip()
                    return f"💭 *Thinking:* {clean_rationale[:150]}{'...' if len(clean_rationale) > 150 else ''}"
            
            # Collaborator agent calls
            if 'invocationInput' in orch_trace:
                invocation = orch_trace['invocationInput']
                
                if 'collaboratorInvocationInput' in invocation:
                    collab = invocation['collaboratorInvocationInput']
                    agent_name = collab.get('collaboratorName', 'agent')
                    
                    agent_descriptions = {
                        'DataAgent': '📊 *Calling Data Agent* - querying Firebolt for insights',
                        'WebSearchAgent': '🔍 *Calling Research Agent* - gathering external intelligence',
                        'ExecutionAgent': '⚡ *Calling Execution Agent* - performing actions'
                    }
                    
                    return agent_descriptions.get(agent_name, f'🤖 *Calling {agent_name}*')
            
            return None
            
        except Exception as e:
            print(f"Error parsing trace: {e}")
            return None
    
    def _send_progress_update(self, channel_id: str, message_ts: str, progress_text: str, thread_ts: str = None) -> bool:
        """Send a progress update to Slack by updating the message"""
        try:
            secrets = self._get_slack_secrets()
            bot_token = secrets.get('bot_token')
            
            if not bot_token:
                print("Bot token not found in secrets")
                return False
            
            formatted_message = f"*RevOps Analysis:* 🔍\n\n{progress_text}"
            
            payload = {
                'channel': channel_id,
                'ts': message_ts,
                'text': formatted_message,
                'mrkdwn': True
            }
            
            response = requests.post(
                'https://slack.com/api/chat.update',
                headers={
                    'Authorization': f'Bearer {bot_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=10
            )
            
            response_data = response.json()
            if response_data.get('ok'):
                return True
            else:
                print(f"Failed to send progress update: {response_data.get('error')}")
                return False
                
        except Exception as e:
            print(f"Error sending progress update: {e}")
            return False
    
    def _send_final_slack_response(self, slack_event: Dict[str, Any], response_text: str, message_ts: str = None) -> bool:
        """Send final response back to Slack (update existing or send new)"""
        try:
            secrets = self._get_slack_secrets()
            bot_token = secrets.get('bot_token')
            
            if not bot_token:
                print("Bot token not found in secrets")
                return False
            
            channel_id = slack_event.get('channel_id') or slack_event.get('channel')
            thread_ts = slack_event.get('thread_ts')
            
            if not channel_id:
                print("No channel ID found in slack event")
                return False
            
            formatted_response = f"*RevOps Analysis:* ✨\n\n{response_text}"
            
            # Try to update existing message first
            if message_ts:
                success = self._update_slack_message(channel_id, message_ts, formatted_response)
                if success:
                    return True
            
            # Fallback: send new message
            return self._send_new_slack_message(channel_id, formatted_response, thread_ts)
                
        except Exception as e:
            print(f"Error sending final Slack response: {e}")
            return False
    
    def _update_slack_message(self, channel_id: str, message_ts: str, formatted_response: str) -> bool:
        """Update an existing Slack message"""
        try:
            secrets = self._get_slack_secrets()
            bot_token = secrets.get('bot_token')
            
            payload = {
                'channel': channel_id,
                'ts': message_ts,
                'text': formatted_response,
                'mrkdwn': True
            }
            
            response = requests.post(
                'https://slack.com/api/chat.update',
                headers={
                    'Authorization': f'Bearer {bot_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=30
            )
            
            response_data = response.json()
            return response_data.get('ok', False)
            
        except Exception as e:
            print(f"Error updating Slack message: {e}")
            return False
    
    def _send_new_slack_message(self, channel_id: str, formatted_response: str, thread_ts: str = None) -> bool:
        """Send a new message to Slack"""
        try:
            secrets = self._get_slack_secrets()
            bot_token = secrets.get('bot_token')
            
            payload = {
                'channel': channel_id,
                'text': formatted_response,
                'mrkdwn': True
            }
            
            if thread_ts:
                payload['thread_ts'] = thread_ts
            
            response = requests.post(
                'https://slack.com/api/chat.postMessage',
                headers={
                    'Authorization': f'Bearer {bot_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=30
            )
            
            response_data = response.json()
            return response_data.get('ok', False)
            
        except Exception as e:
            print(f"Error sending new Slack message: {e}")
            return False
    
    def _get_slack_secrets(self) -> Dict[str, Any]:
        """Get Slack secrets from cache or Secrets Manager"""
        current_time = time.time()
        if current_time - self._cache_timestamp > self.CACHE_TTL:
            try:
                response = self.secrets_client.get_secret_value(SecretId=self.secrets_arn)
                self._secrets_cache = json.loads(response['SecretString'])
                self._cache_timestamp = current_time
                print("Refreshed secrets cache")
            except Exception as e:
                print(f"Error retrieving secrets: {e}")
                raise
        
        return self._secrets_cache

def lambda_handler(event, context):
    """Lambda handler with SQS support"""
    print(f"Lambda invoked with event: {json.dumps(event)[:500]}...")
    
    processor = CompleteSlackBedrockProcessor()
    
    # Handle SQS events (multiple records)
    if 'Records' in event:
        print(f"Processing {len(event['Records'])} SQS records")
        
        success_count = 0
        failure_count = 0
        
        for record in event['Records']:
            try:
                # Process each SQS record
                record_event = {'Records': [record]}
                result = processor.process_slack_event(record_event)
                
                if result['statusCode'] == 200:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                failure_count += 1
                print(f"Error processing record {record.get('messageId', 'unknown')}: {str(e)}")
        
        print(f"Processing complete: {success_count} successful, {failure_count} failed")
        
        if failure_count == 0:
            return {'statusCode': 200, 'processedRecords': success_count}
        else:
            raise Exception(f"Failed to process {failure_count} records")
    
    # Handle direct invocation
    else:
        return processor.process_slack_event(event)