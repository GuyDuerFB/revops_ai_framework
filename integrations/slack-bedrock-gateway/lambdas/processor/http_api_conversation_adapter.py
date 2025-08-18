"""
HTTP API Conversation Adapter
Provides full conversation tracking for HTTP API calls with same fidelity as Slack integration
"""

import json
import boto3
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal

# Initialize AWS clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
s3_client = boto3.client('s3')

@dataclass
class APIConversationMetadata:
    """Metadata for API conversation tracking"""
    conversation_id: str
    api_endpoint: str
    client_identifier: str
    correlation_id: str
    start_time: float
    original_query: str
    user_agent: Optional[str] = None
    source_ip: Optional[str] = None

@dataclass 
class APITraceEvent:
    """Individual trace event in API conversation"""
    event_type: str
    timestamp: float
    event_data: Dict[str, Any]
    correlation_id: str

class HTTPAPIConversationAdapter:
    """
    Adapter that provides full conversation tracing for HTTP API calls
    with the same fidelity as Slack integration
    """
    
    def __init__(self, s3_bucket: Optional[str] = None):
        self.s3_bucket = s3_bucket or os.environ.get('S3_BUCKET')
        self.conversation_exporter = None
        
        # Try to initialize conversation exporter if available
        try:
            from conversation_exporter import ConversationExporter
            if self.s3_bucket:
                self.conversation_exporter = ConversationExporter(self.s3_bucket)
        except ImportError:
            pass
    
    def create_api_conversation_context(self, event: Dict[str, Any], correlation_id: str) -> APIConversationMetadata:
        """
        Create conversation context for API request
        
        Args:
            event: Lambda event containing the API request
            correlation_id: Unique correlation ID for tracking
            
        Returns:
            API conversation metadata
        """
        return APIConversationMetadata(
            conversation_id=f"api-{correlation_id}",
            api_endpoint="manager-agent-wrapper",
            client_identifier=event.get("client_id", "webhook"),
            correlation_id=correlation_id,
            start_time=time.time(),
            original_query=event.get("query", ""),
            user_agent=event.get("user_agent"),
            source_ip=event.get("source_ip")
        )
    
    def trace_bedrock_agent_invocation(self, 
                                     api_metadata: APIConversationMetadata,
                                     agent_id: str, 
                                     agent_alias_id: str, 
                                     user_message: str) -> Tuple[str, List[APITraceEvent]]:
        """
        Trace Bedrock agent invocation with full monitoring
        
        Args:
            api_metadata: API conversation metadata
            agent_id: Bedrock agent ID
            agent_alias_id: Bedrock agent alias ID
            user_message: User message to process
            
        Returns:
            Tuple of (response_text, trace_events)
        """
        trace_events = []
        session_id = f"{api_metadata.conversation_id}_{int(api_metadata.start_time)}"
        
        # Add current date context to query
        now = datetime.now(timezone.utc)
        date_context = f"""
📅 **CURRENT DATE AND TIME CONTEXT:**
- Current Date: {now.strftime('%A, %B %d, %Y')}
- Current Time: {now.strftime('%H:%M UTC')}
- Current Quarter: Q{((now.month - 1) // 3) + 1} {now.year}
- Current Month: {now.strftime('%B %Y')}
- Current Year: {now.year}

**IMPORTANT**: Use this current date information to interpret all time-based references in the user's request.

----

"""
        enhanced_query = f"{date_context}**USER REQUEST:**\n{user_message}"
        
        # Trace event: Agent invocation started
        trace_events.append(APITraceEvent(
            event_type="agent_invocation_started",
            timestamp=time.time(),
            event_data={
                "agent_id": agent_id,
                "agent_alias_id": agent_alias_id,
                "session_id": session_id,
                "query_length": len(enhanced_query),
                "has_date_context": True
            },
            correlation_id=api_metadata.correlation_id
        ))
        
        try:
            start_time = time.time()
            
            # Invoke Bedrock Agent with streaming
            response = bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=enhanced_query,
                enableTrace=True
            )
            
            # Process the response stream
            response_text = ""
            bedrock_traces = []
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        chunk_text = chunk['bytes'].decode('utf-8')
                        response_text += chunk_text
                        
                        # Trace event: Response chunk received
                        trace_events.append(APITraceEvent(
                            event_type="response_chunk_received",
                            timestamp=time.time(),
                            event_data={
                                "chunk_length": len(chunk_text),
                                "total_length": len(response_text)
                            },
                            correlation_id=api_metadata.correlation_id
                        ))
                        
                elif 'trace' in event:
                    bedrock_traces.append(event['trace'])
                    
                    # Trace event: Bedrock trace captured
                    trace_events.append(APITraceEvent(
                        event_type="bedrock_trace_captured",
                        timestamp=time.time(),
                        event_data={
                            "trace_type": list(event['trace'].keys())[0] if event['trace'] else "unknown",
                            "trace_id": event['trace'].get('traceId', 'unknown')
                        },
                        correlation_id=api_metadata.correlation_id
                    ))
            
            execution_time = time.time() - start_time
            
            # Trace event: Agent invocation completed
            trace_events.append(APITraceEvent(
                event_type="agent_invocation_completed",
                timestamp=time.time(),
                event_data={
                    "success": True,
                    "response_length": len(response_text),
                    "trace_count": len(bedrock_traces),
                    "execution_time_seconds": execution_time
                },
                correlation_id=api_metadata.correlation_id
            ))
            
            # Trace event: Processing completed
            trace_events.append(APITraceEvent(
                event_type="processing_completed",
                timestamp=time.time(),
                event_data={
                    "total_trace_events": len(trace_events),
                    "conversation_id": api_metadata.conversation_id,
                    "session_id": session_id
                },
                correlation_id=api_metadata.correlation_id
            ))
            
            return response_text, trace_events
            
        except Exception as e:
            # Trace event: Agent invocation failed
            trace_events.append(APITraceEvent(
                event_type="agent_invocation_failed",
                timestamp=time.time(),
                event_data={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                correlation_id=api_metadata.correlation_id
            ))
            
            raise e
    
    def complete_api_conversation(self,
                                api_metadata: APIConversationMetadata,
                                final_response: str,
                                trace_events: List[APITraceEvent],
                                response_status: int = 200) -> Dict[str, Any]:
        """
        Complete API conversation tracking and export to S3
        
        Args:
            api_metadata: API conversation metadata
            final_response: Final response text
            trace_events: List of trace events
            response_status: HTTP response status code
            
        Returns:
            Conversation summary with export information
        """
        conversation_duration = time.time() - api_metadata.start_time
        
        # Create comprehensive conversation structure
        conversation_data = {
            "export_metadata": {
                "format": "http_api_conversation",
                "version": "3.0", 
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "source": "http_api_conversation_adapter",
                "full_tracing_enabled": True,
                "enhanced_monitoring": True
            },
            "conversation": {
                "conversation_id": api_metadata.conversation_id,
                "session_id": f"{api_metadata.conversation_id}_{int(api_metadata.start_time)}",
                "user_id": api_metadata.client_identifier,
                "channel": api_metadata.api_endpoint,
                "start_timestamp": datetime.fromtimestamp(api_metadata.start_time, tz=timezone.utc).isoformat(),
                "end_timestamp": datetime.now(timezone.utc).isoformat(),
                "user_query": api_metadata.original_query,
                "temporal_context": f"Q{((datetime.now().month - 1) // 3) + 1} {datetime.now().year}",
                "agents_involved": ["Manager"],
                "agent_flow": [{
                    "agent_name": "Manager",
                    "agent_id": "PVWGKOWSOT",
                    "start_time": datetime.fromtimestamp(api_metadata.start_time, tz=timezone.utc).isoformat(),
                    "end_time": datetime.now(timezone.utc).isoformat(),
                    "reasoning_text": f"API request processing for query: {api_metadata.original_query}",
                    "bedrock_trace_content": {
                        "total_trace_events": len(trace_events),
                        "trace_event_types": list(set([event.event_type for event in trace_events]))
                    },
                    "tools_used": [],  # Would be populated by tool execution normalizer
                    "data_operations": [],
                    "api_metadata": {
                        "endpoint": api_metadata.api_endpoint,
                        "correlation_id": api_metadata.correlation_id,
                        "user_agent": api_metadata.user_agent,
                        "source_ip": api_metadata.source_ip
                    },
                    "trace_events": [asdict(event) for event in trace_events]
                }],
                "final_response": final_response,
                "collaboration_map": {},
                "function_audit": {},
                "success": response_status < 400,
                "processing_time_ms": int(conversation_duration * 1000),
                "api_response_metadata": {
                    "status_code": response_status,
                    "response_length": len(final_response),
                    "trace_events_count": len(trace_events)
                }
            }
        }
        
        # Export to S3 if conversation exporter is available
        export_path = None
        if self.conversation_exporter:
            try:
                export_path = self.conversation_exporter.export_conversation_to_s3(conversation_data)
                print(f"✅ Successfully exported HTTP API conversation to S3: {export_path}")
            except Exception as e:
                print(f"❌ Failed to export HTTP API conversation to S3: {e}")
                import traceback
                traceback.print_exc()
        else:
            # Try to initialize simple S3 exporter with S3 bucket
            try:
                from simple_s3_exporter import SimpleS3Exporter
                if self.s3_bucket:
                    simple_exporter = SimpleS3Exporter(self.s3_bucket)
                    export_path = simple_exporter.export_api_conversation(
                        conversation_data, 
                        api_metadata.conversation_id,
                        "api"
                    )
                    print(f"✅ Successfully exported HTTP API conversation to S3 (simple): {export_path}")
                else:
                    print("❌ No S3 bucket configured for HTTP API conversation export")
            except Exception as e:
                print(f"❌ Simple S3 export failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Return summary statistics
        summary_stats = {
            "conversation_id": api_metadata.conversation_id,
            "duration_seconds": conversation_duration,
            "trace_events_count": len(trace_events),
            "response_length": len(final_response),
            "success": response_status < 400,
            "export_path": export_path,
            "enhanced_monitoring_applied": True
        }
        
        return {
            "conversation_data": conversation_data,
            "summary_stats": summary_stats,
            "export_path": export_path
        }
    
    def _serialize_trace_data(self, obj: Any) -> Any:
        """
        Serialize complex trace data for JSON export
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable representation
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return str(obj)
        return str(obj)