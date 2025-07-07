"""
Slack Message Processor Lambda - AWS Best Practices
Processes messages from SQS, invokes Bedrock Agent, and sends responses to Slack
"""
import json
import os
import boto3
import time
import logging
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

def invoke_bedrock_agent(user_message: str, session_id: str) -> str:
    """
    Invoke Bedrock Agent with session management for conversation continuity
    Following AWS best practices for direct agent invocation
    """
    try:
        logger.info(f"Invoking Bedrock Agent for session: {session_id}")
        logger.info(f"Message preview: {user_message[:100]}...")
        
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
        
        # Stream processing for real-time response building
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    agent_response += chunk_text
                    logger.debug(f"Received chunk: {chunk_text[:50]}...")
            
            elif 'trace' in event:
                # Log trace information for debugging
                trace = event['trace']
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
        
        import requests
        
        # Format the response with RevOps branding
        formatted_response = f"*RevOps Analysis:*\n\n{new_text}"
        
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
        
        import requests
        
        formatted_response = f"*RevOps Analysis:*\n\n{text}"
        
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
        
        # Invoke Bedrock Agent with session management
        agent_response = invoke_bedrock_agent(message_text, session_id)
        
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