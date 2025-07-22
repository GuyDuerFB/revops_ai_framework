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
        self.decision_agent_id = "PVWGKOWSOT"
        self.decision_agent_alias_id = "LH87RBMCUQ"
        
    def process_slack_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack event with enhanced tracing"""
        
        # Extract event details
        slack_event = json.loads(event.get('Records', [{}])[0].get('body', '{}'))
        user_query = slack_event.get('message_text', '')
        user_id = slack_event.get('user_id', '')
        channel = slack_event.get('channel_id', '')
        ts = slack_event.get('thread_ts', '')
        response_message_ts = slack_event.get('response_message_ts', ts)  # Timestamp of initial message to update
        
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
            
            # Call Bedrock Agent with real-time updates
            response = self._invoke_bedrock_agent_with_updates(enhanced_query, correlation_id, channel, response_message_ts)
            
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
            
            # Format response for Slack and send
            formatted_response = self._format_response_for_slack(agent_response)
            self._update_slack_message(channel, formatted_response, response_message_ts)
            
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
            error_message = "❌ I encountered an error processing your request. Please try again or contact support."
            self._update_slack_message(channel, error_message, response_message_ts)
            
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
    
    def _invoke_bedrock_agent_legacy(self, query: str, correlation_id: str) -> Dict[str, Any]:
        """Invoke Bedrock agent with shorter timeout and better error handling"""
        
        try:
            # Use a shorter timeout for the agent invocation
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(540)  # Set 540 second timeout (9 minutes)
            
            response = self.bedrock_agent.invoke_agent(
                agentId=self.decision_agent_id,
                agentAliasId=self.decision_agent_alias_id,
                sessionId=correlation_id,
                inputText=query
            )
            
            # Process streaming response with timeout protection
            output_text = ""
            chunk_count = 0
            start_time = time.time()
            
            try:
                for event in response['completion']:
                    # Check for overall timeout (540 seconds max)
                    if time.time() - start_time > 540:
                        print("Agent processing timeout reached")
                        break
                    
                    chunk_count += 1
                    if chunk_count % 10 == 0:  # Log every 10 chunks
                        print(f"Processing chunk {chunk_count}, elapsed: {time.time() - start_time:.1f}s")
                    
                    if 'chunk' in event:
                        chunk_data = event['chunk'].get('bytes', b'')
                        if chunk_data:
                            try:
                                chunk_json = json.loads(chunk_data.decode('utf-8'))
                                
                                # Handle different chunk types
                                if 'outputText' in chunk_json:
                                    output_text += chunk_json['outputText']
                                elif 'text' in chunk_json:
                                    output_text += chunk_json['text']
                                elif isinstance(chunk_json, str):
                                    output_text += chunk_json
                                    
                            except json.JSONDecodeError:
                                # Handle non-JSON chunks - might be plain text
                                chunk_text = chunk_data.decode('utf-8', errors='ignore')
                                output_text += chunk_text
                                
                    elif 'trace' in event:
                        # Handle trace events (for debugging)
                        print(f"Trace event received")
                        
                    elif 'returnControl' in event:
                        # Handle return control events
                        print(f"Return control event received")
                        
            except Exception as stream_error:
                print(f"Error processing stream: {stream_error}")
                # If streaming fails, try to get any partial response
                if not output_text:
                    output_text = "I encountered an error processing your request. Please try again in a moment, or try rephrasing your question."
                    
        except Exception as invoke_error:
            print(f"Error invoking agent: {invoke_error}")
            output_text = "The agent is currently unavailable. Please try your request again in a moment."
            
        finally:
            # Restore original timeout
            if 'original_timeout' in locals():
                socket.setdefaulttimeout(original_timeout)
        
        print(f"Final output text length: {len(output_text)}")
        print(f"Final output text preview: {output_text[:200]}...")
        
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
    
    def _invoke_bedrock_agent_with_updates(self, query: str, correlation_id: str, channel: str, thread_ts: str) -> Dict[str, Any]:
        """Invoke Bedrock agent with real-time Slack updates"""
        
        # Update initial message to show thinking
        print(f"Updating message with thinking status: {thread_ts}")
        self._update_slack_message(channel, "🤔 *Analyzing your request...*", thread_ts)
        
        # Use the simpler legacy method with timeout handling
        print(f"Calling legacy bedrock agent method")
        try:
            # Set a shorter internal timeout and handle deal queries specially
            if 'deal' in query.lower() or 'ugro' in query.lower() or 'ixis' in query.lower() or 'status' in query.lower():
                # For deal queries, provide intermediate updates and use a simplified approach
                self._update_slack_message(channel, "🔍 *Analyzing deal data...*", thread_ts)
                time.sleep(1)
                self._update_slack_message(channel, "📊 *Gathering deal metrics...*", thread_ts)
                
                # Try with a more direct query approach with simplified context
                simplified_query = f"Current date: 2025-07-20. {query}"
                response = self._invoke_bedrock_agent_legacy(simplified_query, correlation_id)
            else:
                # For non-deal queries, use basic query
                simple_query = f"Current date: 2025-07-20. {query}"
                response = self._invoke_bedrock_agent_legacy(simple_query, correlation_id)
                
        except Exception as e:
            print(f"Bedrock agent error: {e}")
            # If the complex query fails, try a fallback approach
            if 'deal' in query.lower() or 'ixis' in query.lower():
                fallback_response = "I'm having difficulty accessing the detailed IXIS deal analysis at the moment. Let me try a simplified approach - could you specify what specific aspect of the IXIS deal you'd like to know about? (e.g., current stage, deal amount, timeline, or owner)"
                return {
                    'output': {'text': fallback_response},
                    'sessionId': correlation_id
                }
            else:
                return {
                    'output': {'text': 'I encountered an issue processing your request. Please try again or rephrase your question.'},
                    'sessionId': correlation_id
                }
        
        # Extract the output text
        output_text = response.get('output', {}).get('text', '')
        
        # Show progress update before final response
        if len(output_text) > 0:
            self._update_slack_message(channel, "✨ *Finalizing response...*", thread_ts)
            time.sleep(1)  # Brief pause to show the status
        
        return response
    
    def _format_response_for_slack(self, response_text: str) -> str:
        """Format response text for optimal Slack display"""
        
        # Basic Slack formatting improvements
        formatted_text = response_text
        
        # Convert markdown headers to Slack format
        formatted_text = formatted_text.replace('## ', '*')
        formatted_text = formatted_text.replace('# ', '*')
        
        # Ensure proper bullet formatting
        formatted_text = formatted_text.replace('• ', '• ')
        formatted_text = formatted_text.replace('- ', '• ')
        
        # Add proper line breaks for readability
        lines = formatted_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.strip():
                # Add spacing around headers
                if line.startswith('*') and line.endswith('*'):
                    formatted_lines.append('')
                    formatted_lines.append(line)
                    formatted_lines.append('')
                else:
                    formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        # Remove excessive blank lines
        result = '\n'.join(formatted_lines)
        while '\n\n\n' in result:
            result = result.replace('\n\n\n', '\n\n')
        
        return result.strip()
    
    def _update_slack_message(self, channel: str, message: str, thread_ts: str):
        """Update existing Slack message instead of sending new one"""
        try:
            secrets = self.secrets_client.get_secret_value(
                SecretId='arn:aws:secretsmanager:us-east-1:740202120544:secret:revops-slack-bedrock-secrets-372buh'
            )
            slack_secrets = json.loads(secrets['SecretString'])
            bot_token = slack_secrets.get('bot_token')
            
            if not bot_token:
                print("Error: Bot token not found in secrets")
                return False
            
            import urllib.request
            import urllib.parse
            
            # Build the message payload for updating
            payload = {
                'channel': channel,
                'text': message,
                'ts': thread_ts,  # Use the original timestamp to update the message
                'mrkdwn': True
            }
            
            print(f"Updating message {thread_ts} in channel {channel}")
            
            # Prepare the request for chat.update
            url = 'https://slack.com/api/chat.update'
            headers = {
                'Authorization': f'Bearer {bot_token}',
                'Content-Type': 'application/json'
            }
            
            data = json.dumps(payload).encode('utf-8')
            
            # Create the request
            req = urllib.request.Request(url, data=data, headers=headers)
            
            # Send the request
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
            
            if response_data.get('ok'):
                print(f"Successfully updated message in channel {channel}")
                return response_data.get('ts')
            else:
                print(f"Slack API error: {response_data.get('error')}")
                # Fallback to posting new message if update fails  
                return self._send_new_slack_message(channel, message, thread_ts)
                
        except Exception as e:
            print(f"Error updating Slack message: {e}")
            # Fallback to posting new message if update fails
            return self._send_new_slack_message(channel, message, thread_ts)

    def _send_new_slack_message(self, channel: str, message: str, thread_ts: str):
        """Send response to Slack"""
        try:
            secrets = self.secrets_client.get_secret_value(
                SecretId='arn:aws:secretsmanager:us-east-1:740202120544:secret:revops-slack-bedrock-secrets-372buh'
            )
            slack_secrets = json.loads(secrets['SecretString'])
            bot_token = slack_secrets.get('bot_token')
            
            if not bot_token:
                print("Error: Bot token not found in secrets")
                return False
            
            import urllib.request
            import urllib.parse
            
            # Build the message payload
            payload = {
                'channel': channel,
                'text': message,
                'mrkdwn': True
            }
            
            # Add thread_ts if this is a thread reply
            if thread_ts:
                payload['thread_ts'] = thread_ts
                print(f"Sending response in thread {thread_ts}")
            else:
                print(f"Sending response to channel {channel}")
            
            # Prepare the request
            url = 'https://slack.com/api/chat.postMessage'
            headers = {
                'Authorization': f'Bearer {bot_token}',
                'Content-Type': 'application/json'
            }
            
            data = json.dumps(payload).encode('utf-8')
            
            # Create the request
            req = urllib.request.Request(url, data=data, headers=headers)
            
            # Send the request
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
            
            if response_data.get('ok'):
                print(f"Successfully sent response to channel {channel}")
                return response_data.get('ts')
            else:
                print(f"Slack API error: {response_data.get('error')}")
                return False
                
        except Exception as e:
            print(f"Error sending Slack response: {e}")
            return False

def lambda_handler(event, context):
    """Lambda handler with enhanced tracing"""
    processor = EnhancedSlackBedrockProcessor()
    return processor.process_slack_event(event)