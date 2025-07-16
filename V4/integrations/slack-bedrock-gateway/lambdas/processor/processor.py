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

# Enhanced AgentTracer for comprehensive monitoring
class EventType(Enum):
    """Types of events to trace"""
    CONVERSATION_START = "CONVERSATION_START"
    CONVERSATION_END = "CONVERSATION_END"
    AGENT_INVOKE = "AGENT_INVOKE"
    AGENT_RESPONSE = "AGENT_RESPONSE"
    AGENT_REASONING = "AGENT_REASONING"
    AGENT_TOOL_USE = "AGENT_TOOL_USE"
    DATA_OPERATION = "DATA_OPERATION"
    DECISION_LOGIC = "DECISION_LOGIC"
    ERROR = "ERROR"
    TEMPORAL_CONTEXT = "TEMPORAL_CONTEXT"
    WORKFLOW_SELECTION = "WORKFLOW_SELECTION"
    SLACK_INCOMING = "SLACK_INCOMING"
    SLACK_OUTGOING = "SLACK_OUTGOING"
    BEDROCK_REQUEST = "BEDROCK_REQUEST"
    BEDROCK_RESPONSE = "BEDROCK_RESPONSE"
    ROUTING_DECISION = "ROUTING_DECISION"
    TOOL_EXECUTION = "TOOL_EXECUTION"

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
    
    def trace_slack_incoming(self, message_content: str, user_id: str, channel: str, 
                           message_ts: str, event_type: str = "app_mention"):
        """Trace incoming Slack messages with full context"""
        event_data = {
            "event_type": EventType.SLACK_INCOMING.value,
            "correlation_id": self.correlation_id,
            "message_content": message_content,
            "user_id": user_id,
            "channel": channel,
            "message_ts": message_ts,
            "slack_event_type": event_type,
            "message_length": len(message_content),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contains_deal_keywords": self._contains_deal_keywords(message_content),
            "extracted_entities": self._extract_entities(message_content)
        }
        self.conversation_logger.info(json.dumps(event_data))
    
    def trace_slack_outgoing(self, response_content: str, channel: str, 
                           response_type: str, processing_time_ms: int):
        """Trace outgoing Slack responses"""
        event_data = {
            "event_type": EventType.SLACK_OUTGOING.value,
            "correlation_id": self.correlation_id,
            "response_content": response_content[:500] + "..." if len(response_content) > 500 else response_content,
            "response_length": len(response_content),
            "channel": channel,
            "response_type": response_type,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.conversation_logger.info(json.dumps(event_data))
    
    def trace_bedrock_request(self, agent_id: str, agent_alias_id: str, 
                            session_id: str, input_text: str, request_metadata: dict = None):
        """Trace Bedrock agent invocation requests"""
        event_data = {
            "event_type": EventType.BEDROCK_REQUEST.value,
            "correlation_id": self.correlation_id,
            "agent_id": agent_id,
            "agent_alias_id": agent_alias_id,
            "session_id": session_id,
            "input_text": input_text,
            "input_length": len(input_text),
            "request_metadata": request_metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.collaboration_logger.info(json.dumps(event_data))
    
    def trace_bedrock_response(self, agent_id: str, response_text: str, 
                             response_metadata: dict, processing_time_ms: int):
        """Trace Bedrock agent responses"""
        event_data = {
            "event_type": EventType.BEDROCK_RESPONSE.value,
            "correlation_id": self.correlation_id,
            "agent_id": agent_id,
            "response_text": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
            "response_length": len(response_text),
            "response_metadata": response_metadata,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.collaboration_logger.info(json.dumps(event_data))
    
    def trace_agent_reasoning(self, agent_id: str, reasoning_step: str, 
                            thought_process: str, decision_factors: dict = None):
        """Trace agent reasoning and thought process"""
        event_data = {
            "event_type": EventType.AGENT_REASONING.value,
            "correlation_id": self.correlation_id,
            "agent_id": agent_id,
            "reasoning_step": reasoning_step,
            "thought_process": thought_process,
            "decision_factors": decision_factors or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.decision_logger.info(json.dumps(event_data))
    
    def trace_routing_decision(self, router_agent: str, target_agent: str, 
                             routing_reason: str, query_classification: str):
        """Trace agent routing decisions"""
        event_data = {
            "event_type": EventType.ROUTING_DECISION.value,
            "correlation_id": self.correlation_id,
            "router_agent": router_agent,
            "target_agent": target_agent,
            "routing_reason": routing_reason,
            "query_classification": query_classification,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.decision_logger.info(json.dumps(event_data))
    
    def trace_tool_execution(self, agent_id: str, tool_name: str, 
                           tool_input: dict, tool_output: dict, execution_time_ms: int):
        """Trace tool execution by agents"""
        event_data = {
            "event_type": EventType.TOOL_EXECUTION.value,
            "correlation_id": self.correlation_id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "tool_input": str(tool_input)[:500] + "..." if len(str(tool_input)) > 500 else tool_input,
            "tool_output": str(tool_output)[:500] + "..." if len(str(tool_output)) > 500 else tool_output,
            "execution_time_ms": execution_time_ms,
            "success": "error" not in str(tool_output).lower(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.data_logger.info(json.dumps(event_data))
    
    def _contains_deal_keywords(self, text: str) -> bool:
        """Check if text contains deal analysis keywords"""
        deal_keywords = [
            "status of", "deal with", "deal for", "analyze the", "review the", 
            "about the", "opportunity", "deal", "assessment", "MEDDPICC", 
            "probability", "IXIS", "ACME", "Microsoft", "Salesforce"
        ]
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in deal_keywords)
    
    def _extract_entities(self, text: str) -> dict:
        """Extract entities from text for monitoring"""
        import re
        entities = {
            "company_names": [],
            "monetary_amounts": [],
            "time_references": [],
            "keywords": []
        }
        
        # Extract potential company names (capitalized words)
        company_pattern = r'\b[A-Z][a-zA-Z]+\b'
        entities["company_names"] = list(set(re.findall(company_pattern, text)))
        
        # Extract monetary amounts
        money_pattern = r'\$[\d,.]+'
        entities["monetary_amounts"] = re.findall(money_pattern, text)
        
        # Extract time references
        time_pattern = r'\b(Q[1-4]|quarter|month|year|week|day|today|yesterday|tomorrow)\b'
        entities["time_references"] = list(set(re.findall(time_pattern, text, re.IGNORECASE)))
        
        return entities
    
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
        # V4 Manager Agent - intelligent router for specialized agent architecture
        # Using Manager Agent with full collaboration capabilities
        self.decision_agent_id = os.environ.get('BEDROCK_AGENT_ID', 'PVWGKOWSOT')
        self.decision_agent_alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID', '9MVRKEHMHX')
        
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
            
            # Trace incoming Slack message with comprehensive details
            self.tracer.trace_slack_incoming(
                message_content=user_query,
                user_id=user_id,
                channel=channel_id,
                message_ts=thread_ts or response_message_ts or str(int(time.time())),
                event_type="app_mention"
            )
            
            # Trace conversation start
            self.tracer.trace_conversation_start(
                user_query=user_query,
                user_id=user_id,
                channel=channel_id,
                temporal_context=current_date
            )
            
            # Create session ID for Bedrock (minimum 2 characters required)
            session_id = f"{user_id or 'user'}:{channel_id or 'channel'}:{thread_ts or 'main'}" if thread_ts else f"{user_id or 'user'}:{channel_id or 'channel'}"
            
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
            # Calculate actual agents used from response traces
            agents_used = self._count_agents_used(response)
            self.tracer.trace_conversation_end(
                response_summary=agent_response[:200],
                total_agents_used=agents_used,
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
            
            # Trace Bedrock request
            bedrock_start_time = time.time()
            if self.tracer:
                self.tracer.trace_bedrock_request(
                    agent_id=self.decision_agent_id,
                    agent_alias_id=self.decision_agent_alias_id,
                    session_id=session_id,
                    input_text=query,
                    request_metadata={
                        "channel_id": channel_id,
                        "message_ts": message_ts,
                        "thread_ts": thread_ts,
                        "agent_type": "V4_Manager_Agent"
                    }
                )
                
                # Trace agent invocation
                self.tracer.trace_agent_invocation(
                    source_agent="SlackProcessor",
                    target_agent=f"ManagerAgent-V4({self.decision_agent_id})",
                    collaboration_type="USER_QUERY_PROCESSING",
                    reasoning="Processing user query through V4 Manager Agent for intelligent routing and collaboration"
                )
            
            # Send initial progress update
            if message_ts and channel_id:
                self._send_progress_update(channel_id, message_ts, "🧠 *V4 Manager Agent analyzing* - determining best approach", thread_ts)
            
            response = self.bedrock_agent.invoke_agent(
                agentId=self.decision_agent_id,
                agentAliasId=self.decision_agent_alias_id,
                sessionId=session_id,
                inputText=query,
                enableTrace=True
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
                
                # Parse orchestration traces for detailed monitoring and progress
                if 'trace' in event:
                    trace_data = event['trace']
                    
                    # Detailed trace logging for monitoring
                    if self.tracer:
                        self._trace_detailed_agent_activity(trace_data)
                    
                    # Send progress updates
                    if message_ts:
                        progress_msg = self._parse_trace_to_progress(trace_data)
                        if progress_msg:
                            self._send_progress_update(channel_id, message_ts, progress_msg, thread_ts)
            
            # Calculate processing time and trace response
            bedrock_processing_time = int((time.time() - bedrock_start_time) * 1000)
            
            print(f"Agent response length: {len(output_text)} characters")
            print(f"Bedrock processing time: {bedrock_processing_time}ms")
            
            # Trace Bedrock response
            if self.tracer:
                self.tracer.trace_bedrock_response(
                    agent_id=self.decision_agent_id,
                    response_text=output_text,
                    response_metadata={
                        "session_id": session_id,
                        "response_length": len(output_text),
                        "processing_time_ms": bedrock_processing_time,
                        "agent_type": "V4_Manager_Agent"
                    },
                    processing_time_ms=bedrock_processing_time
                )
            
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
    
    def _count_agents_used(self, response: Dict[str, Any]) -> int:
        """Count the number of agents used based on response traces"""
        try:
            agents_invoked = set(['DecisionAgent'])  # Always includes the main agent
            
            # Parse through completion traces to find agent invocations
            if 'completion' in response:
                for event in response['completion']:
                    if 'trace' in event and 'orchestrationTrace' in event['trace']:
                        orch_trace = event['trace']['orchestrationTrace']
                        
                        # Check for collaborator invocations
                        if 'invocationInput' in orch_trace:
                            invocation = orch_trace['invocationInput']
                            if 'collaboratorInvocationInput' in invocation:
                                collab = invocation['collaboratorInvocationInput']
                                agent_name = collab.get('collaboratorName', '')
                                if agent_name:
                                    agents_invoked.add(agent_name)
                                    
                                    # Trace the collaboration
                                    if self.tracer:
                                        self.tracer.trace_agent_invocation(
                                            source_agent="DecisionAgent",
                                            target_agent=agent_name,
                                            collaboration_type="AGENT_COLLABORATION",
                                            reasoning=f"Decision Agent calling {agent_name} for specialized task"
                                        )
            
            return len(agents_invoked)
            
        except Exception as e:
            print(f"Error counting agents used: {e}")
            return 1  # Default to 1 if counting fails
    
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
    
    def _trace_detailed_agent_activity(self, trace_data: dict):
        """Parse and trace detailed agent activity from Bedrock traces"""
        try:
            if not self.tracer:
                return
                
            # Parse orchestration traces
            if 'orchestrationTrace' in trace_data:
                orch_trace = trace_data['orchestrationTrace']
                
                # Trace reasoning steps
                if 'rationale' in orch_trace:
                    rationale = orch_trace['rationale']
                    if 'text' in rationale:
                        self.tracer.trace_agent_reasoning(
                            agent_id=self.decision_agent_id,
                            reasoning_step="rationale",
                            thought_process=rationale['text'],
                            decision_factors={"trace_type": "orchestration_rationale"}
                        )
                
                # Trace invocation inputs
                if 'invocationInput' in orch_trace:
                    inv_input = orch_trace['invocationInput']
                    if 'invocationType' in inv_input:
                        invocation_type = inv_input['invocationType']
                        
                        # Trace routing decisions for agent collaborations
                        if invocation_type == "AGENT_COLLABORATOR":
                            collaborator_name = inv_input.get('collaboratorName', 'Unknown')
                            input_text = inv_input.get('inputText', '')
                            
                            self.tracer.trace_routing_decision(
                                router_agent=f"ManagerAgent-V4({self.decision_agent_id})",
                                target_agent=collaborator_name,
                                routing_reason=f"Manager Agent routing to {collaborator_name}",
                                query_classification=self._classify_query_for_routing(input_text)
                            )
                        
                        # Trace tool invocations
                        elif invocation_type == "ACTION_GROUP":
                            action_group = inv_input.get('actionGroupName', 'Unknown')
                            function_name = inv_input.get('function', '')
                            parameters = inv_input.get('parameters', {})
                            
                            self.tracer.trace_tool_execution(
                                agent_id=self.decision_agent_id,
                                tool_name=f"{action_group}.{function_name}",
                                tool_input=parameters,
                                tool_output={"status": "invoked"},
                                execution_time_ms=0  # Will be updated when response comes
                            )
                
                # Trace model invocation details
                if 'modelInvocationInput' in orch_trace:
                    model_input = orch_trace['modelInvocationInput']
                    if 'text' in model_input:
                        # This is the actual prompt sent to the model
                        self.tracer.trace_agent_reasoning(
                            agent_id=self.decision_agent_id,
                            reasoning_step="model_prompt",
                            thought_process=model_input['text'][:1000] + "..." if len(model_input['text']) > 1000 else model_input['text'],
                            decision_factors={
                                "trace_type": "model_invocation_input",
                                "prompt_length": len(model_input['text'])
                            }
                        )
                
                # Trace model responses
                if 'modelInvocationOutput' in orch_trace:
                    model_output = orch_trace['modelInvocationOutput']
                    if 'rawResponse' in model_output:
                        response_content = model_output['rawResponse'].get('content', [])
                        if response_content and len(response_content) > 0:
                            response_text = response_content[0].get('text', '')
                            
                            self.tracer.trace_agent_reasoning(
                                agent_id=self.decision_agent_id,
                                reasoning_step="model_response",
                                thought_process=response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                                decision_factors={
                                    "trace_type": "model_invocation_output",
                                    "response_length": len(response_text)
                                }
                            )
                
                # Trace observation details (tool results)
                if 'observation' in orch_trace:
                    observation = orch_trace['observation']
                    if 'actionGroupInvocationOutput' in observation:
                        action_output = observation['actionGroupInvocationOutput']
                        tool_response = action_output.get('text', '')
                        
                        self.tracer.trace_tool_execution(
                            agent_id=self.decision_agent_id,
                            tool_name=observation.get('type', 'unknown_tool'),
                            tool_input={"observation": True},
                            tool_output={"response": tool_response[:500] + "..." if len(tool_response) > 500 else tool_response},
                            execution_time_ms=0
                        )
                    
                    elif 'collaboratorInvocationOutput' in observation:
                        collab_output = observation['collaboratorInvocationOutput']
                        collaborator_response = collab_output.get('text', '')
                        
                        # Use the agent_response method if it exists, otherwise add it
                        if hasattr(self.tracer, 'trace_agent_response'):
                            self.tracer.trace_agent_response(
                                agent_id=collab_output.get('collaboratorName', 'Unknown'),
                                response_content=collaborator_response[:1000] + "..." if len(collaborator_response) > 1000 else collaborator_response,
                                response_metadata={
                                    "trace_type": "collaborator_response",
                                    "response_length": len(collaborator_response)
                                }
                            )
                        else:
                            # Fallback to reasoning trace
                            self.tracer.trace_agent_reasoning(
                                agent_id=collab_output.get('collaboratorName', 'Unknown'),
                                reasoning_step="collaborator_response",
                                thought_process=collaborator_response[:1000] + "..." if len(collaborator_response) > 1000 else collaborator_response,
                                decision_factors={
                                    "trace_type": "collaborator_response",
                                    "response_length": len(collaborator_response)
                                }
                            )
                        
        except Exception as e:
            print(f"Error tracing detailed agent activity: {str(e)}")
    
    def _classify_query_for_routing(self, query_text: str) -> str:
        """Classify query type for routing decisions"""
        query_lower = query_text.lower()
        
        # Deal analysis keywords
        deal_keywords = ["status of", "deal with", "deal for", "analyze the", "review the", "about the", "opportunity", "deal", "assessment", "meddpicc"]
        if any(keyword in query_lower for keyword in deal_keywords):
            return "deal_analysis"
        
        # Data analysis keywords  
        data_keywords = ["consumption", "usage", "trends", "revenue", "pipeline", "forecast", "analytics"]
        if any(keyword in query_lower for keyword in data_keywords):
            return "data_analysis"
        
        # Research keywords
        research_keywords = ["research", "company", "competitor", "market", "intelligence"]
        if any(keyword in query_lower for keyword in research_keywords):
            return "external_research"
        
        return "general_query"
    
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
        response_start_time = time.time()
        
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
            success = False
            response_type = "update"
            if message_ts:
                success = self._update_slack_message(channel_id, message_ts, formatted_response)
                if success:
                    response_type = "message_update"
                    
            if not success:
                # Fallback: send new message
                success = self._send_new_slack_message(channel_id, formatted_response, thread_ts)
                response_type = "new_message"
            
            # Trace outgoing Slack response
            processing_time_ms = int((time.time() - response_start_time) * 1000)
            if self.tracer:
                self.tracer.trace_slack_outgoing(
                    response_content=response_text,
                    channel=channel_id,
                    response_type=response_type,
                    processing_time_ms=processing_time_ms
                )
            
            return success
                
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
        message_start_time = time.time()
        
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
            success = response_data.get('ok', False)
            
            # Trace the new message send
            processing_time_ms = int((time.time() - message_start_time) * 1000)
            if self.tracer:
                self.tracer.trace_slack_outgoing(
                    response_content=formatted_response,
                    channel=channel_id,
                    response_type="new_message_standalone",
                    processing_time_ms=processing_time_ms
                )
            
            return success
            
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