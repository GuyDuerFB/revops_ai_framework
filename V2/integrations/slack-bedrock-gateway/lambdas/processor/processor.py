"""
Slack Message Processor Lambda - AWS Best Practices
Processes messages from SQS, invokes Bedrock Agent, and sends responses to Slack
"""
import json
import os
import boto3
import time
import logging
import requests
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients with explicit region and extended timeouts
from botocore.config import Config

AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Configure extended timeouts for Bedrock Agent (complex analyses can take 3-4 minutes)
bedrock_config = Config(
    region_name=AWS_REGION,
    read_timeout=240,  # 4 minutes for complex revenue analysis
    connect_timeout=60,
    retries={'max_attempts': 2}
)

secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', config=bedrock_config)

# Environment variables
SECRETS_ARN = os.environ['SECRETS_ARN']
BEDROCK_AGENT_ID = os.environ['BEDROCK_AGENT_ID']
BEDROCK_AGENT_ALIAS_ID = os.environ['BEDROCK_AGENT_ALIAS_ID']

# Cache for secrets
_secrets_cache = {}
_cache_timestamp = 0
CACHE_TTL = 300  # 5 minutes

def get_slack_secrets():
    """Get Slack secrets from cache or Secrets Manager"""
    global _secrets_cache, _cache_timestamp
    
    current_time = time.time()
    if current_time - _cache_timestamp > CACHE_TTL:
        try:
            response = secrets_client.get_secret_value(SecretId=SECRETS_ARN)
            _secrets_cache = json.loads(response['SecretString'])
            _cache_timestamp = current_time
            logger.info("Refreshed secrets cache")
        except Exception as e:
            logger.error(f"Error retrieving secrets: {e}")
            raise
    
    return _secrets_cache

def send_progress_update(channel_id: str, message_ts: str, progress_text: str) -> bool:
    """Send a progress update to Slack by updating the message"""
    try:
        secrets = get_slack_secrets()
        bot_token = secrets.get('bot_token')
        
        if not bot_token:
            logger.error("Bot token not found in secrets")
            return False
        
        
        # Format with progress indicator
        formatted_message = f"*RevOps Analysis:* 🤔\n\n{progress_text}"
        
        response = requests.post(
            'https://slack.com/api/chat.update',
            headers={
                'Authorization': f'Bearer {bot_token}',
                'Content-Type': 'application/json'
            },
            json={
                'channel': channel_id,
                'ts': message_ts,
                'text': formatted_message,
                'mrkdwn': True
            },
            timeout=10
        )
        
        response_data = response.json()
        if response_data.get('ok'):
            logger.debug(f"Sent progress update: {progress_text[:50]}...")
            return True
        else:
            logger.warning(f"Failed to send progress update: {response_data.get('error')}")
            return False
            
    except Exception as e:
        logger.warning(f"Error sending progress update: {e}")
        return False

def parse_trace_to_progress(trace_event: dict) -> Optional[str]:
    """Convert Bedrock Agent orchestration trace to human-readable progress message"""
    try:
        if 'orchestrationTrace' not in trace_event:
            return None
            
        orch_trace = trace_event['orchestrationTrace']
        
        # Agent thinking/reasoning (highest priority)
        if 'rationale' in orch_trace:
            rationale = orch_trace['rationale'].get('text', '')
            if rationale and len(rationale.strip()) > 10:
                # Clean up the rationale text
                clean_rationale = rationale.replace('\n', ' ').strip()
                return f"💭 *Thinking:* {clean_rationale[:180]}{'...' if len(clean_rationale) > 180 else ''}"
        
        # Pre-processing or planning phase
        if 'modelInvocationInput' in orch_trace:
            model_input = orch_trace['modelInvocationInput']
            if model_input and 'text' in model_input:
                # This indicates the agent is processing the user's request
                return "🧠 *Planning my approach* - breaking down your request into actionable steps"
        
        # Collaborator agent calls
        if 'invocationInput' in orch_trace:
            invocation = orch_trace['invocationInput']
            
            # Check for collaborator invocation
            if 'collaboratorInvocationInput' in invocation:
                collab = invocation['collaboratorInvocationInput']
                agent_name = collab.get('collaboratorName', 'agent')
                input_text = collab.get('input', '')
                
                # Map agent names to user-friendly descriptions
                agent_descriptions = {
                    'DataAgent': '📊 *Calling Data Agent* to query Firebolt Data Warehouse and analyze revenue data',
                    'WebSearchAgent': '🔍 *Calling Research Agent* to gather external company intelligence',
                    'ExecutionAgent': '⚡ *Calling Execution Agent* to perform actions and send notifications'
                }
                
                base_message = agent_descriptions.get(agent_name, f'🤖 *Calling {agent_name}*')
                
                # Add context from the input if it provides insight
                if 'revenue' in input_text.lower() or 'billing' in input_text.lower():
                    return f"{base_message} - analyzing revenue trends and patterns"
                elif 'query' in input_text.lower() or 'sql' in input_text.lower():
                    return f"{base_message} - executing database queries"
                elif 'customer' in input_text.lower() or 'account' in input_text.lower():
                    return f"{base_message} - analyzing customer data and segmentation"
                elif 'opportunit' in input_text.lower() or 'pipeline' in input_text.lower():
                    return f"{base_message} - analyzing sales pipeline and opportunities"
                else:
                    return base_message
            
            # Function calling within agents
            elif 'actionGroupInvocationInput' in invocation:
                action = invocation['actionGroupInvocationInput']
                action_group = action.get('actionGroupName', '')
                function_name = action.get('function', '')
                
                # Map function calls to progress messages
                if function_name == 'query_fire':
                    return "🔍 *Running SQL query* on Firebolt Data Warehouse to retrieve data"
                elif function_name == 'get_gong_data':
                    return "📞 *Retrieving conversation data* from Gong to analyze customer interactions"
                elif function_name == 'search_web':
                    return "🌐 *Searching the web* for company intelligence and market information"
                elif function_name == 'research_company':
                    return "🏢 *Researching company details* and business intelligence"
                elif action_group and function_name:
                    return f"⚙️ *Executing {function_name}* in {action_group}"
        
        # Observation/results processing - capture different types
        if 'observation' in orch_trace:
            observation = orch_trace['observation']
            
            # Function execution results
            if 'actionGroupInvocationOutput' in observation:
                output = observation['actionGroupInvocationOutput']
                if 'text' in output:
                    return "📈 *Processing query results* - analyzing the data patterns and trends"
            
            # Collaborator responses
            elif 'collaboratorInvocationOutput' in observation:
                collab_output = observation['collaboratorInvocationOutput']
                if 'text' in collab_output:
                    return "🧠 *Analyzing findings* from specialist agent and preparing insights"
            
            # Model processing results
            elif 'modelInvocationOutput' in observation:
                return "⚡ *Synthesizing information* - combining data to create comprehensive analysis"
        
        # Final processing phase
        if 'modelInvocationOutput' in orch_trace:
            return "📝 *Finalizing analysis* - preparing comprehensive summary and recommendations"
        
        return None
        
    except Exception as e:
        logger.warning(f"Error parsing trace: {e}")
        return None

def invoke_bedrock_agent(user_message: str, session_id: str, channel_id: str = None, message_ts: str = None) -> str:
    """
    Invoke Bedrock Agent with session management for conversation continuity
    Following AWS best practices for direct agent invocation
    """
    try:
        logger.info(f"Invoking Bedrock Agent for session: {session_id}")
        logger.info(f"Message preview: {user_message[:100]}...")
        
        # Send initial progress update
        if channel_id and message_ts:
            send_progress_update(channel_id, message_ts, "🤔 *Processing your request* - I'm understanding what you need and planning my approach...")
        
        # Direct agent invocation with streaming support
        response = bedrock_agent_runtime.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id,  # This maintains conversation context automatically
            inputText=user_message
        )
        
        # Process the response stream
        agent_response = ""
        completion_events = []
        last_progress_time = time.time()
        progress_throttle = 2  # Minimum seconds between progress updates (reduced for more granular traces)
        
        # Stream processing for real-time response building
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    agent_response += chunk_text
                    logger.debug(f"Received chunk: {chunk_text[:50]}...")
            
            elif 'trace' in event:
                # Parse trace for progress updates
                trace = event['trace']
                current_time = time.time()
                
                # Debug: Log trace structure to understand what we're getting
                logger.debug(f"Trace event keys: {list(trace.keys())}")
                if 'orchestrationTrace' in trace:
                    orch_keys = list(trace['orchestrationTrace'].keys())
                    logger.debug(f"Orchestration trace keys: {orch_keys}")
                
                # Throttle progress updates to avoid spam
                if current_time - last_progress_time >= progress_throttle:
                    progress_message = parse_trace_to_progress(trace)
                    if progress_message and channel_id and message_ts:
                        logger.info(f"Sending progress update: {progress_message}")
                        if send_progress_update(channel_id, message_ts, progress_message):
                            last_progress_time = current_time
                
                # Log trace information for debugging
                if 'orchestrationTrace' in trace:
                    orch_trace = trace['orchestrationTrace']
                    if 'invocationInput' in orch_trace:
                        logger.info(f"Agent invocation: {orch_trace['invocationInput'].get('actionGroupInvocationInput', {}).get('actionGroupName', 'unknown')}")
                    if 'observation' in orch_trace:
                        logger.info("Agent observation received")
            
            elif 'returnControl' in event:
                # Handle any return control events
                return_control = event['returnControl']
                logger.info(f"Return control event: {return_control.get('invocationId')}")
            
            completion_events.append(event)
        
        if not agent_response.strip():
            logger.warning("Empty response from Bedrock Agent")
            agent_response = "I apologize, but I couldn't generate a response to your request. Please try rephrasing your question."
        
        logger.info(f"Agent response length: {len(agent_response)} characters")
        return agent_response.strip()
        
    except Exception as e:
        logger.error(f"Error invoking Bedrock Agent: {str(e)}", exc_info=True)
        return f"I apologize, but I encountered an error processing your request. Please try again later."

def update_slack_message(channel_id: str, message_ts: str, new_text: str) -> bool:
    """Update an existing Slack message with the agent response"""
    try:
        secrets = get_slack_secrets()
        bot_token = secrets.get('bot_token')
        
        if not bot_token:
            logger.error("Bot token not found in secrets")
            return False
        
        
        # Format the response with RevOps branding and completion indicator
        formatted_response = f"*RevOps Analysis:* ✅\n\n{new_text}"
        
        response = requests.post(
            'https://slack.com/api/chat.update',
            headers={
                'Authorization': f'Bearer {bot_token}',
                'Content-Type': 'application/json'
            },
            json={
                'channel': channel_id,
                'ts': message_ts,
                'text': formatted_response,
                'mrkdwn': True
            },
            timeout=30
        )
        
        response_data = response.json()
        if response_data.get('ok'):
            logger.info(f"Updated message in channel {channel_id}")
            return True
        else:
            logger.error(f"Failed to update Slack message: {response_data.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating Slack message: {e}")
        return False

def send_slack_message(channel_id: str, text: str) -> bool:
    """Send a new message to Slack (fallback if update fails)"""
    try:
        secrets = get_slack_secrets()
        bot_token = secrets.get('bot_token')
        
        if not bot_token:
            logger.error("Bot token not found in secrets")
            return False
        
        
        formatted_response = f"*RevOps Analysis:* ✅\n\n{text}"
        
        response = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers={
                'Authorization': f'Bearer {bot_token}',
                'Content-Type': 'application/json'
            },
            json={
                'channel': channel_id,
                'text': formatted_response,
                'mrkdwn': True
            },
            timeout=30
        )
        
        response_data = response.json()
        if response_data.get('ok'):
            logger.info(f"Sent new message to channel {channel_id}")
            return True
        else:
            logger.error(f"Failed to send Slack message: {response_data.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Slack message: {e}")
        return False

def process_app_mention(event_data: Dict[str, Any]) -> bool:
    """Process an app mention event"""
    try:
        user_id = event_data['user_id']
        channel_id = event_data['channel_id']
        message_text = event_data['message_text']
        response_message_ts = event_data.get('response_message_ts')
        
        logger.info(f"Processing mention from user {user_id} in channel {channel_id}")
        
        # Create session ID for conversation continuity
        # Format: user_id:channel_id for consistent sessions
        session_id = f"{user_id}:{channel_id}"
        
        # Invoke Bedrock Agent with session management and progress tracking
        agent_response = invoke_bedrock_agent(
            user_message=message_text, 
            session_id=session_id,
            channel_id=channel_id,
            message_ts=response_message_ts
        )
        
        # Send response back to Slack
        success = False
        if response_message_ts:
            # Try to update the existing "processing" message
            success = update_slack_message(channel_id, response_message_ts, agent_response)
        
        if not success:
            # Fallback: send a new message
            success = send_slack_message(channel_id, agent_response)
        
        if success:
            logger.info(f"Successfully sent response to channel {channel_id}")
        else:
            logger.error(f"Failed to send response to channel {channel_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing app mention: {str(e)}", exc_info=True)
        return False

def lambda_handler(event, context):
    """Main Lambda handler for SQS events"""
    try:
        logger.info(f"Processor Lambda invoked with {len(event.get('Records', []))} records")
        
        success_count = 0
        failure_count = 0
        
        # Process each SQS record
        for record in event.get('Records', []):
            try:
                # Parse the message body
                message_body = json.loads(record['body'])
                event_type = message_body.get('type')
                
                logger.info(f"Processing event type: {event_type}")
                
                if event_type == 'app_mention':
                    if process_app_mention(message_body):
                        success_count += 1
                    else:
                        failure_count += 1
                        logger.error(f"Failed to process app mention: {record['messageId']}")
                else:
                    logger.info(f"Ignoring event type: {event_type}")
                    success_count += 1  # Count as success since we handled it appropriately
                
            except Exception as e:
                failure_count += 1
                logger.error(f"Error processing record {record.get('messageId', 'unknown')}: {str(e)}", exc_info=True)
        
        logger.info(f"Processing complete: {success_count} successful, {failure_count} failed")
        
        # Return success if all records processed successfully
        if failure_count == 0:
            return {'statusCode': 200, 'processedRecords': success_count}
        else:
            # Partial failures will cause the failed messages to be retried
            raise Exception(f"Failed to process {failure_count} out of {len(event.get('Records', []))} records")
        
    except Exception as e:
        logger.error(f"Error in processor lambda_handler: {str(e)}", exc_info=True)
        raise  # Re-raise to trigger SQS retry mechanism