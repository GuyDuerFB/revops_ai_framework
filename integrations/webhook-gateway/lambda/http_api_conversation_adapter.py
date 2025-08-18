"""
HTTP API Conversation Adapter
Provides full conversation tracking and tracing for HTTP API interactions similar to Slack handler
"""

import json
import boto3
import os
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import traceback
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class APIConversationMetadata:
    """Metadata for API-based conversations"""
    conversation_id: str
    correlation_id: str
    api_endpoint: str
    http_method: str
    request_headers: Dict[str, str]
    client_identifier: Optional[str]
    request_timestamp: str
    response_timestamp: Optional[str]
    response_status: Optional[int]
    processing_time_ms: Optional[int]
    webhook_delivery_status: Optional[str]
    user_query: str
    final_response: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class APITraceEvent:
    """Individual trace event in API conversation"""
    event_id: str
    event_type: str  # request_received, agent_invoked, tool_executed, response_generated
    timestamp: str
    duration_ms: Optional[int]
    details: Dict[str, Any]
    agent_context: Optional[Dict[str, Any]]
    error_details: Optional[str]

class HTTPAPIConversationAdapter:
    """Adapter to provide full conversation tracing for HTTP API calls"""
    
    def __init__(self, s3_bucket: Optional[str] = None):
        self.s3_client = boto3.client('s3') if s3_bucket else None
        self.s3_bucket = s3_bucket
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
        
        # Import conversation monitoring components
        try:
            from system_prompt_manager import SystemPromptStripper
            from agent_attribution_engine import AgentAttributionEngine
            from tool_execution_normalizer import ToolExecutionNormalizer
            from message_parser import MessageParser
            from reasoning_parser import ReasoningTextParser
            from conversation_transformer import ConversationTransformer
            from conversation_exporter import ConversationExporter
            
            self.system_prompt_stripper = SystemPromptStripper(s3_bucket)
            self.agent_attribution_engine = AgentAttributionEngine()
            self.tool_normalizer = ToolExecutionNormalizer()
            self.message_parser = MessageParser()
            self.reasoning_parser = ReasoningTextParser()
            self.conversation_transformer = ConversationTransformer()
            self.conversation_exporter = ConversationExporter(s3_bucket) if s3_bucket else None
            
            logger.info("Initialized HTTP API Conversation Adapter with full monitoring components")
            
        except ImportError as e:
            logger.warning(f"Could not import some monitoring components: {e}")
            # Initialize with None values - basic functionality only
            self.system_prompt_stripper = None
            self.agent_attribution_engine = None
            self.tool_normalizer = None
            self.message_parser = None
            self.reasoning_parser = None
            self.conversation_transformer = None
            self.conversation_exporter = None
    
    def create_api_conversation_context(self, event: Dict[str, Any], correlation_id: str) -> APIConversationMetadata:
        """Create conversation context from API Gateway event"""
        
        # Extract request metadata
        request_context = event.get('requestContext', {})
        headers = event.get('headers', {})
        
        # Generate conversation ID
        conversation_id = f"api_{correlation_id}_{int(time.time())}"
        
        # Extract user query from request body or query parameters
        user_query = self._extract_user_query_from_request(event)
        
        # Extract client identifier
        client_identifier = self._extract_client_identifier(headers, request_context)
        
        api_metadata = APIConversationMetadata(
            conversation_id=conversation_id,
            correlation_id=correlation_id,
            api_endpoint=event.get('path', '/unknown'),
            http_method=event.get('httpMethod', 'POST'),
            request_headers={k: v for k, v in headers.items() if not k.lower().startswith('authorization')},  # Exclude auth headers
            client_identifier=client_identifier,
            request_timestamp=datetime.now(timezone.utc).isoformat(),
            response_timestamp=None,
            response_status=None,
            processing_time_ms=None,
            webhook_delivery_status=None,
            user_query=user_query,
            final_response=""
        )
        
        logger.info(f"Created API conversation context: {conversation_id} for endpoint {api_metadata.api_endpoint}")
        
        return api_metadata
    
    def trace_bedrock_agent_invocation(
        self, 
        api_metadata: APIConversationMetadata, 
        agent_id: str, 
        agent_alias_id: str, 
        user_message: str
    ) -> Tuple[Dict[str, Any], List[APITraceEvent]]:
        """
        Invoke Bedrock agent with full tracing similar to Slack handler
        Returns (agent_response, trace_events)
        """
        trace_events = []
        start_time = time.time()
        
        # Generate session ID for this conversation
        session_id = f"{api_metadata.conversation_id}_{int(start_time)}"
        
        try:
            # Trace: Agent invocation started
            trace_events.append(APITraceEvent(
                event_id=f"trace_{len(trace_events)}",
                event_type="agent_invocation_started",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=None,
                details={
                    "agent_id": agent_id,
                    "agent_alias_id": agent_alias_id,
                    "session_id": session_id,
                    "user_message_length": len(user_message),
                    "correlation_id": api_metadata.correlation_id
                },
                agent_context={
                    "conversation_id": api_metadata.conversation_id,
                    "api_endpoint": api_metadata.api_endpoint,
                    "client_identifier": api_metadata.client_identifier
                },
                error_details=None
            ))
            
            # Invoke Bedrock Agent with streaming
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=user_message,
                enableTrace=True  # Enable detailed tracing
            )
            
            # Process streaming response with full trace capture
            agent_response, bedrock_traces = self._process_bedrock_streaming_response(response, trace_events)
            
            invocation_time = int((time.time() - start_time) * 1000)
            
            # Trace: Agent invocation completed
            trace_events.append(APITraceEvent(
                event_id=f"trace_{len(trace_events)}",
                event_type="agent_invocation_completed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=invocation_time,
                details={
                    "session_id": session_id,
                    "response_length": len(str(agent_response)),
                    "trace_events_captured": len(bedrock_traces),
                    "total_processing_time_ms": invocation_time
                },
                agent_context={
                    "conversation_id": api_metadata.conversation_id,
                    "final_response_preview": str(agent_response)[:200] + "..." if len(str(agent_response)) > 200 else str(agent_response)
                },
                error_details=None
            ))
            
            # Create comprehensive conversation data similar to Slack handler
            conversation_data = self._create_conversation_data_from_traces(
                api_metadata, bedrock_traces, agent_response, trace_events
            )
            
            # Apply full processing pipeline
            if self.system_prompt_stripper:
                conversation_data, stripping_stats = self.system_prompt_stripper.preprocess_conversation_data(conversation_data)
                
                # Trace: System prompt processing
                trace_events.append(APITraceEvent(
                    event_id=f"trace_{len(trace_events)}",
                    event_type="system_prompt_processing",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    duration_ms=None,
                    details=stripping_stats,
                    agent_context=None,
                    error_details=None
                ))
            
            # Apply agent attribution
            if self.agent_attribution_engine:
                conversation_data = self._apply_agent_attribution(conversation_data, trace_events)
            
            # Apply tool normalization
            if self.tool_normalizer and 'conversation' in conversation_data and 'agent_flow' in conversation_data['conversation']:
                normalized_flow, tool_stats = self.tool_normalizer.normalize_tool_executions(
                    conversation_data['conversation']['agent_flow']
                )
                conversation_data['conversation']['agent_flow'] = normalized_flow
                
                # Trace: Tool normalization
                trace_events.append(APITraceEvent(
                    event_id=f"trace_{len(trace_events)}",
                    event_type="tool_normalization",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    duration_ms=None,
                    details=asdict(tool_stats),
                    agent_context=None,
                    error_details=None
                ))
            
            # Export conversation to S3 with multiple formats
            if self.conversation_exporter:
                export_urls = self.conversation_exporter.export_conversation(
                    conversation_data,
                    formats=['enhanced_structured_json', 'llm_readable', 'metadata_only']
                )
                
                # Trace: Conversation export
                trace_events.append(APITraceEvent(
                    event_id=f"trace_{len(trace_events)}",
                    event_type="conversation_export",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    duration_ms=None,
                    details={
                        "export_urls": export_urls,
                        "formats_exported": list(export_urls.keys())
                    },
                    agent_context=None,
                    error_details=None
                ))
            
            return agent_response, trace_events
            
        except Exception as e:
            error_time = int((time.time() - start_time) * 1000)
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
                "processing_time_ms": error_time
            }
            
            # Trace: Agent invocation failed
            trace_events.append(APITraceEvent(
                event_id=f"trace_{len(trace_events)}",
                event_type="agent_invocation_failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=error_time,
                details=error_details,
                agent_context={
                    "conversation_id": api_metadata.conversation_id,
                    "session_id": session_id if 'session_id' in locals() else "unknown"
                },
                error_details=str(e)
            ))
            
            logger.error(f"Bedrock agent invocation failed: {e}")
            raise
    
    def _process_bedrock_streaming_response(
        self, 
        response: Dict[str, Any], 
        trace_events: List[APITraceEvent]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Process streaming response from Bedrock with full trace capture"""
        
        completion_text = ""
        bedrock_traces = []
        
        try:
            event_stream = response['completion']
            
            for event in event_stream:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        chunk_text = chunk['bytes'].decode('utf-8')
                        completion_text += chunk_text
                        
                        # Trace each chunk for detailed monitoring
                        trace_events.append(APITraceEvent(
                            event_id=f"trace_{len(trace_events)}",
                            event_type="response_chunk_received",
                            timestamp=datetime.now(timezone.utc).isoformat(),
                            duration_ms=None,
                            details={
                                "chunk_length": len(chunk_text),
                                "cumulative_length": len(completion_text)
                            },
                            agent_context=None,
                            error_details=None
                        ))
                
                elif 'trace' in event:
                    trace_data = event['trace']
                    bedrock_traces.append(trace_data)
                    
                    # Process trace for detailed agent activity
                    processed_trace = self._process_bedrock_trace_event(trace_data)
                    
                    trace_events.append(APITraceEvent(
                        event_id=f"trace_{len(trace_events)}",
                        event_type="bedrock_trace_captured",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        duration_ms=None,
                        details={
                            "trace_type": processed_trace.get("trace_type", "unknown"),
                            "agent_step": processed_trace.get("agent_step", "unknown"),
                            "trace_size_bytes": len(json.dumps(trace_data, default=str))
                        },
                        agent_context=processed_trace.get("agent_context"),
                        error_details=processed_trace.get("error_details")
                    ))
                
                elif 'internalServerException' in event:
                    error_details = str(event['internalServerException'])
                    trace_events.append(APITraceEvent(
                        event_id=f"trace_{len(trace_events)}",
                        event_type="bedrock_internal_error",
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        duration_ms=None,
                        details={"error": error_details},
                        agent_context=None,
                        error_details=error_details
                    ))
                    
                elif 'validationException' in event:
                    error_details = str(event['validationException'])
                    trace_events.append(APITraceEvent(
                        event_id=f"trace_{len(trace_events)}",
                        event_type="bedrock_validation_error", 
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        duration_ms=None,
                        details={"error": error_details},
                        agent_context=None,
                        error_details=error_details
                    ))
        
        except Exception as e:
            logger.error(f"Error processing Bedrock streaming response: {e}")
            trace_events.append(APITraceEvent(
                event_id=f"trace_{len(trace_events)}",
                event_type="response_processing_error",
                timestamp=datetime.now(timezone.utc).isoformat(),
                duration_ms=None,
                details={"error": str(e)},
                agent_context=None,
                error_details=str(e)
            ))
        
        return completion_text, bedrock_traces
    
    def _process_bedrock_trace_event(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual Bedrock trace event for detailed analysis"""
        
        processed = {
            "trace_type": "unknown",
            "agent_step": "unknown",
            "agent_context": {},
            "tool_executions": [],
            "knowledge_base_queries": [],
            "agent_communications": [],
            "error_details": None
        }
        
        try:
            # Extract trace type and step information
            if 'agentId' in trace_data:
                processed["agent_context"]["agent_id"] = trace_data['agentId']
            
            if 'agentAliasId' in trace_data:
                processed["agent_context"]["agent_alias_id"] = trace_data['agentAliasId']
            
            # Process different trace event types
            if 'modelInvocationInput' in trace_data:
                processed["trace_type"] = "model_invocation"
                processed["agent_step"] = "reasoning"
                
                # Extract model input details (after system prompt filtering)
                model_input = trace_data['modelInvocationInput']
                if self.message_parser:
                    parsed_input = self.message_parser.parse_message_content(str(model_input))
                    processed["agent_context"]["parsed_input"] = parsed_input
            
            elif 'observation' in trace_data:
                processed["trace_type"] = "observation"
                processed["agent_step"] = "tool_result_processing"
                
                observation = trace_data['observation']
                if self.message_parser:
                    parsed_observation = self.message_parser.parse_message_content(str(observation))
                    processed["tool_executions"] = parsed_observation.get("tool_results", [])
                    processed["agent_communications"] = parsed_observation.get("agent_communications", [])
            
            elif 'knowledgeBaseLookupOutput' in trace_data:
                processed["trace_type"] = "knowledge_base_query"
                processed["agent_step"] = "knowledge_retrieval"
                
                kb_output = trace_data['knowledgeBaseLookupOutput']
                processed["knowledge_base_queries"].append({
                    "retrieved_references": len(kb_output.get('retrievedReferences', [])),
                    "knowledge_base_id": kb_output.get('knowledgeBaseId', 'unknown')
                })
            
            elif 'actionGroupInvocationOutput' in trace_data:
                processed["trace_type"] = "action_group_invocation"
                processed["agent_step"] = "tool_execution"
                
                action_output = trace_data['actionGroupInvocationOutput']
                processed["tool_executions"].append({
                    "action_group": action_output.get('actionGroupName', 'unknown'),
                    "text_response": action_output.get('text', '')[:200] + "..." if len(action_output.get('text', '')) > 200 else action_output.get('text', '')
                })
            
        except Exception as e:
            processed["error_details"] = f"Error processing trace event: {str(e)}"
            logger.warning(f"Error processing Bedrock trace event: {e}")
        
        return processed
    
    def _create_conversation_data_from_traces(
        self, 
        api_metadata: APIConversationMetadata,
        bedrock_traces: List[Dict[str, Any]],
        agent_response: str,
        trace_events: List[APITraceEvent]
    ) -> Dict[str, Any]:
        """Create comprehensive conversation data structure from traces"""
        
        # Build agent flow from Bedrock traces
        agent_flow = []
        current_step = None
        step_counter = 0
        
        for trace in bedrock_traces:
            # Create agent step if needed
            if current_step is None or self._should_create_new_step(trace, current_step):
                if current_step:
                    agent_flow.append(current_step)
                
                current_step = {
                    "agent_name": "unknown",  # Will be determined by attribution engine
                    "agent_id": trace.get('agentId', api_metadata.correlation_id),
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "end_time": datetime.now(timezone.utc).isoformat(),
                    "reasoning_text": "",
                    "bedrock_trace_content": {},
                    "tools_used": [],
                    "data_operations": [],
                    "timing": {
                        "start_time": datetime.now(timezone.utc).isoformat(),
                        "end_time": datetime.now(timezone.utc).isoformat(),
                        "duration_ms": 0
                    }
                }
                step_counter += 1
            
            # Add trace content to current step
            self._add_trace_to_step(current_step, trace)
        
        # Add final step
        if current_step:
            agent_flow.append(current_step)
        
        # Create full conversation structure similar to Slack handler
        conversation_data = {
            "export_metadata": {
                "format": "enhanced_structured_json",
                "version": "2.0",
                "exported_at": datetime.utcnow().isoformat(),
                "source": "http_api",
                "correlation_id": api_metadata.correlation_id,
                "conversation_type": "api_conversation"
            },
            "conversation": {
                "conversation_id": api_metadata.conversation_id,
                "session_id": api_metadata.correlation_id,
                "user_id": api_metadata.client_identifier or "api_user",
                "channel": f"api:{api_metadata.api_endpoint}",
                "start_timestamp": api_metadata.request_timestamp,
                "end_timestamp": datetime.now(timezone.utc).isoformat(),
                "user_query": api_metadata.user_query,
                "temporal_context": f"API Request to {api_metadata.api_endpoint} at {api_metadata.request_timestamp}",
                "agents_involved": [],  # Will be populated by attribution engine
                "agent_flow": agent_flow,
                "final_response": agent_response,
                "collaboration_map": {},
                "function_audit": {
                    "total_function_calls": len([e for e in trace_events if e.event_type in ["tool_executed", "bedrock_trace_captured"]]),
                    "api_trace_events": [asdict(event) for event in trace_events]
                },
                "success": True,
                "processing_time_ms": api_metadata.processing_time_ms or 0,
                "api_metadata": api_metadata.to_dict()
            }
        }
        
        return conversation_data
    
    def _should_create_new_step(self, trace: Dict[str, Any], current_step: Dict[str, Any]) -> bool:
        """Determine if a new agent step should be created"""
        # Create new step for different agents
        if trace.get('agentId') != current_step.get('agent_id'):
            return True
        
        # Create new step for significant trace type changes
        current_traces = current_step.get('bedrock_trace_content', {})
        if 'modelInvocationInput' in trace and current_traces.get('modelInvocationInput'):
            return True  # New reasoning cycle
        
        return False
    
    def _add_trace_to_step(self, step: Dict[str, Any], trace: Dict[str, Any]):
        """Add trace data to agent step"""
        trace_content = step['bedrock_trace_content']
        
        # Add different trace types to step
        if 'modelInvocationInput' in trace:
            trace_content['modelInvocationInput'] = trace['modelInvocationInput']
            # Extract reasoning text if available
            if isinstance(trace['modelInvocationInput'], str):
                step['reasoning_text'] += trace['modelInvocationInput'] + "\n"
        
        if 'observation' in trace:
            trace_content['observation'] = trace['observation']
            
            # Parse tools from observation
            if self.message_parser:
                parsed_obs = self.message_parser.parse_message_content(str(trace['observation']))
                step['tools_used'].extend(parsed_obs.get('tool_results', []))
        
        if 'knowledgeBaseLookupOutput' in trace:
            trace_content['knowledgeBaseLookupOutput'] = trace['knowledgeBaseLookupOutput']
        
        if 'actionGroupInvocationOutput' in trace:
            trace_content['actionGroupInvocationOutput'] = trace['actionGroupInvocationOutput']
            
            # Add to tools_used
            action_output = trace['actionGroupInvocationOutput']
            step['tools_used'].append({
                'tool_name': action_output.get('actionGroupName', 'unknown_action'),
                'execution_time_ms': 0,  # Not available in trace
                'success': True,
                'result_summary': action_output.get('text', '')[:200] + "..." if len(action_output.get('text', '')) > 200 else action_output.get('text', '')
            })
        
        # Update step timing
        step['end_time'] = datetime.now(timezone.utc).isoformat()
        step['timing']['end_time'] = step['end_time']
    
    def _apply_agent_attribution(self, conversation_data: Dict[str, Any], trace_events: List[APITraceEvent]) -> Dict[str, Any]:
        """Apply agent attribution to conversation data"""
        if not self.agent_attribution_engine:
            return conversation_data
        
        conversation = conversation_data.get('conversation', {})
        agent_flow = conversation.get('agent_flow', [])
        
        agents_involved = set()
        handoffs_detected = []
        
        # Apply attribution to each step
        for step in agent_flow:
            attribution = self.agent_attribution_engine.detect_agent_from_multiple_sources(step)
            
            # Update step with attribution
            step['agent_name'] = attribution.attributed_agent
            step['agent_attribution'] = {
                'confidence_score': attribution.confidence_score,
                'evidence_sources': attribution.evidence_sources,
                'detection_methods': attribution.detection_methods,
                'original_agent': attribution.original_agent,
                'handoff_detected': attribution.handoff_detected
            }
            
            agents_involved.add(attribution.attributed_agent)
            
            if attribution.collaboration_indicators:
                step['collaboration_indicators'] = attribution.collaboration_indicators
        
        # Detect handoffs across conversation
        handoffs = self.agent_attribution_engine.detect_agent_handoffs_in_conversation(agent_flow)
        
        # Update conversation with attribution results
        conversation['agents_involved'] = list(agents_involved)
        conversation['detected_agent_handovers'] = [asdict(handoff) for handoff in handoffs]
        
        # Add attribution trace event
        trace_events.append(APITraceEvent(
            event_id=f"trace_{len(trace_events)}",
            event_type="agent_attribution_applied",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_ms=None,
            details={
                "agents_identified": list(agents_involved),
                "handoffs_detected": len(handoffs),
                "attribution_methods_used": list(set().union(*[step.get('agent_attribution', {}).get('detection_methods', []) for step in agent_flow]))
            },
            agent_context=None,
            error_details=None
        ))
        
        return conversation_data
    
    def _extract_user_query_from_request(self, event: Dict[str, Any]) -> str:
        """Extract user query from API request"""
        # Try body first
        body = event.get('body', '')
        if body:
            try:
                if isinstance(body, str):
                    body_data = json.loads(body)
                else:
                    body_data = body
                
                # Common field names for user input
                for field in ['user_message', 'message', 'query', 'input', 'question', 'text']:
                    if field in body_data:
                        return str(body_data[field])
                
                # If no specific field, return entire body (truncated)
                body_str = json.dumps(body_data) if not isinstance(body, str) else body
                return body_str[:1000] + "..." if len(body_str) > 1000 else body_str
                
            except json.JSONDecodeError:
                return body[:1000] + "..." if len(body) > 1000 else body
        
        # Try query parameters
        query_params = event.get('queryStringParameters', {})
        if query_params:
            for field in ['q', 'query', 'message', 'input']:
                if field in query_params:
                    return query_params[field]
        
        # Try path parameters
        path_params = event.get('pathParameters', {})
        if path_params:
            return json.dumps(path_params)
        
        return f"API request to {event.get('path', 'unknown')} via {event.get('httpMethod', 'unknown')}"
    
    def _extract_client_identifier(self, headers: Dict[str, str], request_context: Dict[str, Any]) -> Optional[str]:
        """Extract client identifier from request"""
        
        # Try common client identification headers
        client_id_headers = ['x-client-id', 'client-id', 'x-api-key', 'user-agent', 'x-user-id']
        for header in client_id_headers:
            if header.lower() in {k.lower(): v for k, v in headers.items()}:
                return headers.get(header) or headers.get(header.lower())
        
        # Try request context
        identity = request_context.get('identity', {})
        if identity.get('sourceIp'):
            return f"ip:{identity['sourceIp']}"
        
        # Try API Gateway source
        if request_context.get('requestId'):
            return f"request:{request_context['requestId']}"
        
        return None
    
    def complete_api_conversation(
        self, 
        api_metadata: APIConversationMetadata, 
        final_response: str, 
        trace_events: List[APITraceEvent],
        response_status: int = 200,
        webhook_delivery_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete API conversation tracking"""
        
        # Update metadata
        api_metadata.response_timestamp = datetime.now(timezone.utc).isoformat()
        api_metadata.response_status = response_status
        api_metadata.final_response = final_response
        api_metadata.webhook_delivery_status = webhook_delivery_status
        
        # Calculate processing time
        if api_metadata.request_timestamp and api_metadata.response_timestamp:
            request_time = datetime.fromisoformat(api_metadata.request_timestamp.replace('Z', '+00:00'))
            response_time = datetime.fromisoformat(api_metadata.response_timestamp.replace('Z', '+00:00'))
            api_metadata.processing_time_ms = int((response_time - request_time).total_seconds() * 1000)
        
        # Final trace event
        trace_events.append(APITraceEvent(
            event_id=f"trace_{len(trace_events)}",
            event_type="api_conversation_completed",
            timestamp=api_metadata.response_timestamp,
            duration_ms=api_metadata.processing_time_ms,
            details={
                "conversation_id": api_metadata.conversation_id,
                "correlation_id": api_metadata.correlation_id,
                "response_status": response_status,
                "final_response_length": len(final_response),
                "total_trace_events": len(trace_events),
                "webhook_delivery_status": webhook_delivery_status
            },
            agent_context={
                "api_endpoint": api_metadata.api_endpoint,
                "client_identifier": api_metadata.client_identifier,
                "processing_time_ms": api_metadata.processing_time_ms
            },
            error_details=None
        ))
        
        # Create comprehensive summary
        conversation_summary = {
            "api_metadata": api_metadata.to_dict(),
            "trace_events": [asdict(event) for event in trace_events],
            "summary_stats": {
                "total_trace_events": len(trace_events),
                "processing_time_ms": api_metadata.processing_time_ms,
                "response_status": response_status,
                "success": response_status < 400,
                "agent_invocation_events": len([e for e in trace_events if e.event_type.startswith('agent_')]),
                "bedrock_trace_events": len([e for e in trace_events if e.event_type == 'bedrock_trace_captured']),
                "error_events": len([e for e in trace_events if e.error_details is not None])
            }
        }
        
        logger.info(f"Completed API conversation tracking for {api_metadata.conversation_id}: {len(trace_events)} trace events, {api_metadata.processing_time_ms}ms processing time")
        
        return conversation_summary