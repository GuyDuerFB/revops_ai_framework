"""
Enhanced Slack-Bedrock Processor with Agent Tracing
Integrates structured tracing for debugging agent chain-of-thought.
"""

import json
import boto3
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import sys
import os

# Add monitoring directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'monitoring'))

try:
    from agent_tracer import AgentTracer, create_tracer, trace_conversation_start, trace_error
except ImportError:
    # Fallback if agent_tracer is not available
    print("Warning: agent_tracer not available, using fallback logging")
    
    class AgentTracer:
        def __init__(self, correlation_id=None):
            self.correlation_id = correlation_id
        def trace_conversation_start(self, *args, **kwargs): pass
        def trace_conversation_end(self, *args, **kwargs): pass
        def trace_agent_invocation(self, *args, **kwargs): pass
        def trace_temporal_context(self, *args, **kwargs): pass
        def trace_error(self, *args, **kwargs): pass
    
    def create_tracer(correlation_id=None): return AgentTracer(correlation_id)
    def trace_conversation_start(*args, **kwargs): pass
    def trace_error(*args, **kwargs): pass

class EnhancedSlackBedrockProcessor:
    """Enhanced processor with comprehensive agent tracing"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        self.secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
        
        # Agent configuration
        self.decision_agent_id = "TCX9CGOKBR"
        self.decision_agent_alias_id = "BKLREFH3L0"
        
    def process_slack_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack event with enhanced tracing"""
        
        # Extract event details
        slack_event = json.loads(event.get('Records', [{}])[0].get('body', '{}'))
        user_query = slack_event.get('text', '')
        user_id = slack_event.get('user', '')
        channel = slack_event.get('channel', '')
        ts = slack_event.get('ts', '')
        
        # Create tracer with correlation ID based on Slack timestamp
        correlation_id = f"slack_{ts}_{user_id}"
        tracer = create_tracer(correlation_id)
        
        start_time = time.time()
        
        try:
            # Extract temporal context
            current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            temporal_context = f"Current date: {current_date}"
            
            # Trace conversation start
            tracer.trace_conversation_start(
                user_query=user_query,
                user_id=user_id, 
                channel=channel,
                temporal_context=temporal_context
            )
            
            # Trace temporal context injection
            tracer.trace_temporal_context(
                current_date=current_date,
                time_references=self._extract_time_references(user_query),
                temporal_adjustments={"timezone": "UTC", "context_injected": True}
            )
            
            # Prepare enhanced query with tracing context
            enhanced_query = self._prepare_enhanced_query(user_query, temporal_context, correlation_id)
            
            # Invoke Decision Agent with tracing
            tracer.trace_agent_invocation(
                source_agent="SlackProcessor",
                target_agent="DecisionAgent", 
                collaboration_type="CONVERSATION_PROCESSING",
                reasoning="User query received from Slack, invoking supervisor agent"
            )
            
            # Call Bedrock Agent
            response = self._invoke_bedrock_agent(enhanced_query, correlation_id)
            
            # Extract response details for tracing
            agent_response = response.get('output', {}).get('text', '')
            processing_time = int((time.time() - start_time) * 1000)
            
            # Trace conversation end
            tracer.trace_conversation_end(
                response_summary=agent_response[:200] + "..." if len(agent_response) > 200 else agent_response,
                total_agents_used=self._count_agents_in_response(response),
                processing_time_ms=processing_time,
                success=True
            )
            
            # Send response to Slack
            self._send_slack_response(channel, agent_response, ts)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'success',
                    'correlation_id': correlation_id,
                    'processing_time_ms': processing_time
                })
            }
            
        except Exception as e:
            # Trace error
            tracer.trace_error(
                error_type=type(e).__name__,
                error_message=str(e),
                agent_context="SlackProcessor.process_slack_event",
                recovery_attempted=False
            )
            
            # Send error response to Slack
            error_message = "I encountered an error processing your request. Please try again or contact support."
            self._send_slack_response(channel, error_message, ts)
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'error',
                    'correlation_id': correlation_id,
                    'error': str(e)
                })
            }
    
    def _prepare_enhanced_query(self, user_query: str, temporal_context: str, correlation_id: str) -> str:
        """Prepare query with enhanced context for tracing"""
        
        enhanced_query = f"""
{temporal_context}

User Query: {user_query}

TRACING_CONTEXT:
- Correlation ID: {correlation_id}
- Enable detailed logging for debugging
- Include reasoning for all agent collaborations
- Log data sources accessed and operations performed
- Track temporal context usage in analysis

Please process this query following the comprehensive workflows and provide detailed analysis.
        """.strip()
        
        return enhanced_query
    
    def _invoke_bedrock_agent(self, query: str, correlation_id: str) -> Dict[str, Any]:
        """Invoke Bedrock agent with tracing context"""
        
        response = self.bedrock_agent.invoke_agent(
            agentId=self.decision_agent_id,
            agentAliasId=self.decision_agent_alias_id,
            sessionId=correlation_id,  # Use correlation ID as session ID for continuity
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
        
        return {
            'output': {'text': output_text},
            'sessionId': correlation_id
        }
    
    def _extract_time_references(self, query: str) -> list:
        """Extract time references from query for tracing"""
        time_words = ['today', 'yesterday', 'last', 'this', 'recent', 'current', 
                     'quarter', 'month', 'week', 'year', 'Q1', 'Q2', 'Q3', 'Q4']
        
        found_references = []
        query_lower = query.lower()
        
        for word in time_words:
            if word in query_lower:
                found_references.append(word)
        
        return found_references
    
    def _count_agents_in_response(self, response: Dict[str, Any]) -> int:
        """Count agents involved in response for tracing"""
        # Simple heuristic - could be enhanced to parse actual agent invocations
        response_text = response.get('output', {}).get('text', '').lower()
        
        agent_count = 1  # Always includes Decision Agent
        
        if 'data' in response_text or 'query' in response_text:
            agent_count += 1  # Data Agent
        if 'research' in response_text or 'company' in response_text:
            agent_count += 1  # WebSearch Agent  
        if 'action' in response_text or 'execute' in response_text:
            agent_count += 1  # Execution Agent
            
        return agent_count
    
    def _send_slack_response(self, channel: str, message: str, thread_ts: str):
        """Send response to Slack"""
        # Implementation would use Slack Web API
        # For now, this is a placeholder
        print(f"Sending to Slack channel {channel}: {message[:100]}...")

def lambda_handler(event, context):
    """Lambda handler with enhanced tracing"""
    processor = EnhancedSlackBedrockProcessor()
    return processor.process_slack_event(event)