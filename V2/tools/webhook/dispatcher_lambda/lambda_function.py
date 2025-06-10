import os
import json
import boto3
import logging
import urllib.request
import urllib.error
import traceback
import time
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

# Constants
WEBHOOK_URL_SECRET = os.environ.get('WEBHOOK_URL_SECRET', 'webhook-urls')
WEBHOOK_QUEUE_URL = os.environ.get('WEBHOOK_QUEUE_URL')
MAX_RETRIES = 5
RETRY_BASE_DELAY_MS = 100  # Base delay for exponential backoff

# Initialize AWS clients
secretsmanager = boto3.client('secretsmanager')
sqs = boto3.client('sqs')
cloudwatch = boto3.client('cloudwatch')

# Initialize metrics
metrics = {
    'service': 'webhook-dispatcher-lambda',
    'successful_requests': 0,
    'failed_requests': 0,
    'retry_attempts': 0,
    'latency_ms': 0
}

def get_webhook_urls():
    """Retrieve webhook URLs from AWS Secrets Manager"""
    try:
        logger.info(f"Retrieving webhook URLs from secret: {WEBHOOK_URL_SECRET}")
        response = secretsmanager.get_secret_value(SecretId=WEBHOOK_URL_SECRET)
        secret_string = response['SecretString']
        webhook_urls = json.loads(secret_string)
        return webhook_urls
    except ClientError as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise

def post_to_webhook(url, data, retry_count=0):
    """Post data to webhook URL with retry logic"""
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as response:
            if response.status in (200, 201, 202):
                response_data = response.read().decode('utf-8')
                logger.info(f"Successfully posted to webhook: {url}")
                return True, response_data
            else:
                logger.warning(f"Webhook returned non-success status: {response.status}")
                return False, f"HTTP Status: {response.status}"
    
    except urllib.error.HTTPError as e:
        if retry_count < MAX_RETRIES and e.code >= 500:
            # Calculate exponential backoff with jitter
            delay = (RETRY_BASE_DELAY_MS * (2 ** retry_count)) / 1000.0
            metrics['retry_attempts'] += 1
            logger.warning(f"HTTP error {e.code}, retrying in {delay:.2f}s (attempt {retry_count + 1}/{MAX_RETRIES})")
            time.sleep(delay)
            return post_to_webhook(url, data, retry_count + 1)
        else:
            logger.error(f"HTTP error posting to webhook: {e.code} - {e.reason}")
            return False, f"HTTP Error: {e.code} - {e.reason}"
    
    except Exception as e:
        logger.error(f"Error posting to webhook: {str(e)}")
        return False, str(e)

def send_to_queue(webhook_type, payload):
    """Send a message to the SQS queue"""
    if not WEBHOOK_QUEUE_URL:
        raise ValueError("WEBHOOK_QUEUE_URL environment variable not set")
    
    try:
        message_body = json.dumps({
            'webhook_type': webhook_type,
            'payload': payload,
            'timestamp': time.time()
        })
        
        response = sqs.send_message(
            QueueUrl=WEBHOOK_QUEUE_URL,
            MessageBody=message_body
        )
        
        logger.info(f"Message sent to queue with ID: {response['MessageId']}")
        return response['MessageId']
    
    except Exception as e:
        logger.error(f"Error sending message to queue: {str(e)}")
        raise

def process_queue_message(message):
    """Process a message from the queue"""
    try:
        message_body = json.loads(message['Body'])
        webhook_type = message_body.get('webhook_type')
        payload = message_body.get('payload')
        
        if not webhook_type or not payload:
            logger.error(f"Invalid message format: {message_body}")
            return False
        
        webhook_urls = get_webhook_urls()
        
        if webhook_type not in webhook_urls:
            logger.error(f"No webhook URL configured for type: {webhook_type}")
            return False
        
        url = webhook_urls[webhook_type]
        success, response = post_to_webhook(url, payload)
        
        if success:
            logger.info(f"Successfully processed webhook for type: {webhook_type}")
            
            # Publish success metric
            cloudwatch.put_metric_data(
                Namespace='RevOpsAI/Webhooks',
                MetricData=[{
                    'MetricName': 'SuccessfulWebhook',
                    'Dimensions': [{'Name': 'WebhookType', 'Value': webhook_type}],
                    'Value': 1,
                    'Unit': 'Count'
                }]
            )
            
            return True
        else:
            logger.error(f"Failed to process webhook for type: {webhook_type} - {response}")
            
            # Publish failure metric
            cloudwatch.put_metric_data(
                Namespace='RevOpsAI/Webhooks',
                MetricData=[{
                    'MetricName': 'FailedWebhook',
                    'Dimensions': [{'Name': 'WebhookType', 'Value': webhook_type}],
                    'Value': 1,
                    'Unit': 'Count'
                }]
            )
            
            return False
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def handler(event, context):
    """Lambda handler function"""
    start_time = time.time()
    
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Determine execution mode: direct invocation or SQS trigger
        if 'Records' in event and event['Records'] and 'eventSource' in event['Records'][0] and event['Records'][0]['eventSource'] == 'aws:sqs':
            # SQS trigger mode - process queue messages
            successful_messages = 0
            failed_messages = 0
            
            for record in event['Records']:
                if process_queue_message(record):
                    successful_messages += 1
                    metrics['successful_requests'] += 1
                else:
                    failed_messages += 1
                    metrics['failed_requests'] += 1
            
            # Calculate overall success/failure metrics
            metrics['latency_ms'] = int((time.time() - start_time) * 1000)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'successful_messages': successful_messages,
                    'failed_messages': failed_messages,
                    'total_messages': len(event['Records']),
                    'metrics': metrics
                })
            }
        
        else:
            # Direct invocation mode - handle webhook dispatch request
            body = event
            if isinstance(event, str):
                body = json.loads(event)
            elif 'body' in event and event['body']:
                body = json.loads(event['body'])
            
            operation = body.get('operation')
            
            if operation == 'send_webhook':
                webhook_type = body.get('webhook_type')
                payload = body.get('payload')
                
                if not webhook_type or not payload:
                    return {
                        'statusCode': 400,
                        'body': json.dumps({
                            'error': 'Missing required parameters: webhook_type, payload'
                        })
                    }
                
                # Handle based on dispatch mode
                dispatch_mode = body.get('dispatch_mode', 'direct')
                
                if dispatch_mode == 'queue':
                    # Queue the webhook for asynchronous processing
                    message_id = send_to_queue(webhook_type, payload)
                    
                    metrics['successful_requests'] += 1
                    metrics['latency_ms'] = int((time.time() - start_time) * 1000)
                    
                    return {
                        'statusCode': 202,
                        'body': json.dumps({
                            'status': 'queued',
                            'message_id': message_id,
                            'metrics': metrics
                        })
                    }
                else:
                    # Process webhook directly
                    webhook_urls = get_webhook_urls()
                    
                    if webhook_type not in webhook_urls:
                        return {
                            'statusCode': 400,
                            'body': json.dumps({
                                'error': f'No webhook URL configured for type: {webhook_type}'
                            })
                        }
                    
                    url = webhook_urls[webhook_type]
                    success, response = post_to_webhook(url, payload)
                    
                    if success:
                        metrics['successful_requests'] += 1
                    else:
                        metrics['failed_requests'] += 1
                    
                    metrics['latency_ms'] = int((time.time() - start_time) * 1000)
                    
                    return {
                        'statusCode': 200 if success else 500,
                        'body': json.dumps({
                            'success': success,
                            'response': response,
                            'metrics': metrics
                        })
                    }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': f'Unsupported operation: {operation}'
                    })
                }
    
    except Exception as e:
        # Record metrics
        metrics['failed_requests'] += 1
        metrics['latency_ms'] = int((time.time() - start_time) * 1000)
        
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'metrics': metrics
            })
        }
