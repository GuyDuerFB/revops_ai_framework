"""
Slack Events Handler Lambda - AWS Best Practices
Handles Slack events, validates signatures, and sends to SQS for processing
"""
import json
import os
import boto3
import hashlib
import hmac
import time
import logging
from urllib.parse import parse_qs

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')
sqs_client = boto3.client('sqs')

# Environment variables
SECRETS_ARN = os.environ['SECRETS_ARN']
PROCESSING_QUEUE_URL = os.environ['PROCESSING_QUEUE_URL']

# Cache for secrets to avoid repeated API calls
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

def verify_slack_signature(body, signature, timestamp):
    """Verify Slack request signature"""
    try:
        secrets = get_slack_secrets()
        signing_secret = secrets.get('signing_secret')
        
        if not signing_secret:
            logger.error("Signing secret not found in secrets")
            return False
        
        # Check timestamp (prevent replay attacks)
        if abs(time.time() - int(timestamp)) > 300:  # 5 minutes
            logger.warning("Request timestamp too old")
            return False
        
        # Create signature
        sig_basestring = f'v0:{timestamp}:{body}'
        expected_signature = 'v0=' + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return hmac.compare_digest(expected_signature, signature)
        
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False

def send_to_processing_queue(event_data):
    """Send Slack event to SQS for async processing"""
    try:
        message_body = json.dumps(event_data)
        
        response = sqs_client.send_message(
            QueueUrl=PROCESSING_QUEUE_URL,
            MessageBody=message_body,
            MessageAttributes={
                'EventType': {
                    'StringValue': event_data.get('type', 'unknown'),
                    'DataType': 'String'
                },
                'Timestamp': {
                    'StringValue': str(int(time.time())),
                    'DataType': 'String'
                }
            }
        )
        
        logger.info(f"Sent message to SQS: {response['MessageId']}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending to SQS: {e}")
        return False

def send_immediate_slack_response(channel_id, user_id, thread_ts=None, message="👋 Hey there! I'm on it - analyzing your data now..."):
    """Send immediate acknowledgment to Slack, optionally in a thread"""
    try:
        secrets = get_slack_secrets()
        bot_token = secrets.get('bot_token')
        
        if not bot_token:
            logger.error("Bot token not found in secrets")
            return False
        
        # Use urllib instead of requests (built-in Python library)
        import urllib.request
        import urllib.parse
        import json
        
        # Build the message payload
        payload = {
            'channel': channel_id,
            'text': message,
            'mrkdwn': True
        }
        
        # Add thread_ts if this is a thread reply
        if thread_ts:
            payload['thread_ts'] = thread_ts
            logger.info(f"Sending immediate response in thread {thread_ts}")
        else:
            logger.info(f"Sending immediate response to channel {channel_id}")
        
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
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode('utf-8'))
        
        if response_data.get('ok'):
            logger.info(f"Sent immediate response to channel {channel_id}")
            return response_data.get('ts')  # Return message timestamp for updates
        else:
            logger.error(f"Slack API error: {response_data.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending immediate response: {e}")
        return False

def lambda_handler(event, context):
    """Main Lambda handler following AWS best practices"""
    try:
        logger.info(f"Received event: {json.dumps(event, default=str)}")
        
        # Parse the incoming request
        body = event.get('body', '')
        headers = event.get('headers', {})
        
        # Get Slack signature headers (case-insensitive)
        signature = headers.get('x-slack-signature') or headers.get('X-Slack-Signature', '')
        timestamp = headers.get('x-slack-request-timestamp') or headers.get('X-Slack-Request-Timestamp', '')
        
        logger.info(f"Processing Slack request, signature present: {bool(signature)}")
        
        # Parse JSON body first to check for challenge
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            # Try form-encoded data
            if 'application/x-www-form-urlencoded' in headers.get('content-type', ''):
                parsed_data = parse_qs(body)
                payload = parsed_data.get('payload', [''])[0]
                if payload:
                    data = json.loads(payload)
                else:
                    data = {}
            else:
                logger.error(f"Could not parse request body: {body[:200]}...")
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid request body'})
                }
        
        # Handle URL verification (Slack app setup) - no signature needed
        if data.get('type') == 'url_verification':
            challenge = data.get('challenge', '')
            logger.info(f"Handling URL verification with challenge: {challenge}")
            return {
                'statusCode': 200,
                'body': challenge,
                'headers': {
                    'Content-Type': 'text/plain'
                }
            }
        
        # Verify Slack signature for all other requests
        if not verify_slack_signature(body, signature, timestamp):
            logger.warning("Invalid Slack signature")
            return {
                'statusCode': 401,
                'body': json.dumps({'error': 'Unauthorized'})
            }
        
        # Handle event callback
        if data.get('type') == 'event_callback':
            event_data = data.get('event', {})
            logger.info(f"Received event_callback with event type: {event_data.get('type')}")
            
            # Only process app mentions
            if event_data.get('type') == 'app_mention':
                user_id = event_data.get('user')
                channel_id = event_data.get('channel')
                text = event_data.get('text', '')
                thread_ts = event_data.get('thread_ts')  # Extract thread timestamp
                ts = event_data.get('ts')  # Message timestamp
                
                logger.info(f"App mention details - User: {user_id}, Channel: {channel_id}, Thread: {thread_ts}, Original text: {text}")
                
                # Remove bot mention from text (any bot mention pattern)
                import re
                user_message = re.sub(r'<@U[A-Z0-9]+>', '', text).strip()
                logger.info(f"Processed message text: '{user_message}'")
                
                if user_message:
                    logger.info(f"Processing app mention from {user_id} in {channel_id}")
                    
                    # Determine if this is a thread reply
                    # If thread_ts exists, reply in thread. If not, this becomes the thread root
                    reply_thread_ts = thread_ts if thread_ts else ts
                    
                    # Send immediate acknowledgment to Slack (in thread if applicable)
                    message_ts = send_immediate_slack_response(channel_id, user_id, reply_thread_ts, "👋 Hey there! I'm diving into your data right now...")
                    
                    # Prepare data for processor
                    processing_data = {
                        'type': 'app_mention',
                        'user_id': user_id,
                        'channel_id': channel_id,
                        'message_text': user_message,
                        'thread_ts': reply_thread_ts,  # Thread timestamp for replies
                        'original_event': event_data,
                        'response_message_ts': message_ts,  # For updating the message later
                        'timestamp': int(time.time())
                    }
                    
                    # Send to processing queue
                    if send_to_processing_queue(processing_data):
                        return {
                            'statusCode': 200,
                            'body': json.dumps({'status': 'queued'})
                        }
                    else:
                        return {
                            'statusCode': 500,
                            'body': json.dumps({'error': 'Failed to queue message'})
                        }
                else:
                    logger.info("Empty message after removing bot mention")
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'status': 'ignored_empty'})
                    }
            else:
                logger.info(f"Ignoring event type: {event_data.get('type')}")
                return {
                    'statusCode': 200,
                    'body': json.dumps({'status': 'ignored'})
                }
        
        # Handle other event types
        logger.info(f"Unhandled event type: {data.get('type')}")
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }