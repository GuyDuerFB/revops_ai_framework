"""
Test Thread Behavior for Slack Integration
Tests the new thread-based conversation functionality
"""

import json
import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import our Lambda functions
from lambdas.handler import handler as slack_handler
from lambdas.processor import processor as slack_processor

class TestThreadBehavior(unittest.TestCase):
    """Test suite for thread-based conversation behavior"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_secrets = {
            'bot_token': 'xoxb-test-token',
            'signing_secret': 'test-signing-secret'
        }
        
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'SECRETS_ARN': 'arn:aws:secretsmanager:us-east-1:123456789:secret:test',
            'PROCESSING_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789/test-queue',
            'BEDROCK_AGENT_ID': 'test-agent-id',
            'BEDROCK_AGENT_ALIAS_ID': 'test-alias-id',
            'LOG_LEVEL': 'DEBUG'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests"""
        self.env_patcher.stop()

    def test_thread_detection_in_handler(self):
        """Test that handler correctly extracts thread_ts from Slack events"""
        
        # Mock AWS clients
        with patch('lambdas.handler.handler.secrets_client') as mock_secrets_client, \
             patch('lambdas.handler.handler.sqs_client') as mock_sqs_client, \
             patch('lambdas.handler.handler.requests') as mock_requests:
            
            # Mock secrets retrieval
            mock_secrets_client.get_secret_value.return_value = {
                'SecretString': json.dumps(self.mock_secrets)
            }
            
            # Mock Slack API response
            mock_requests.post.return_value.json.return_value = {
                'ok': True,
                'ts': '1234567890.123456'
            }
            
            # Mock SQS send
            mock_sqs_client.send_message.return_value = {
                'MessageId': 'test-message-id'
            }
            
            # Create test event - app mention in a thread
            test_event = {
                'body': json.dumps({
                    'type': 'event_callback',
                    'event': {
                        'type': 'app_mention',
                        'user': 'U123456789',
                        'channel': 'C123456789',
                        'text': '<@U094GD826SD> What are our Q4 revenue numbers?',
                        'ts': '1234567890.123456',
                        'thread_ts': '1234567890.000000'  # This indicates it's in a thread
                    }
                }),
                'headers': {
                    'x-slack-signature': 'v0=test-signature',
                    'x-slack-request-timestamp': str(int(1234567890))
                }
            }
            
            # Mock signature verification
            with patch('lambdas.handler.handler.verify_slack_signature', return_value=True):
                # Call the handler
                response = slack_handler.lambda_handler(test_event, None)
                
                # Verify response
                self.assertEqual(response['statusCode'], 200)
                
                # Check that SQS message was sent with thread_ts
                mock_sqs_client.send_message.assert_called_once()
                sent_message = json.loads(mock_sqs_client.send_message.call_args[1]['MessageBody'])
                
                # Verify thread_ts is preserved
                self.assertEqual(sent_message['thread_ts'], '1234567890.000000')
                self.assertEqual(sent_message['type'], 'app_mention')

    def test_new_thread_creation_in_handler(self):
        """Test handler behavior when creating a new thread (no existing thread_ts)"""
        
        with patch('lambdas.handler.handler.secrets_client') as mock_secrets_client, \
             patch('lambdas.handler.handler.sqs_client') as mock_sqs_client, \
             patch('lambdas.handler.handler.requests') as mock_requests:
            
            # Mock secrets retrieval
            mock_secrets_client.get_secret_value.return_value = {
                'SecretString': json.dumps(self.mock_secrets)
            }
            
            # Mock Slack API response
            mock_requests.post.return_value.json.return_value = {
                'ok': True,
                'ts': '1234567890.123456'
            }
            
            # Mock SQS send
            mock_sqs_client.send_message.return_value = {
                'MessageId': 'test-message-id'
            }
            
            # Create test event - app mention NOT in a thread
            test_event = {
                'body': json.dumps({
                    'type': 'event_callback',
                    'event': {
                        'type': 'app_mention',
                        'user': 'U123456789',
                        'channel': 'C123456789',
                        'text': '<@U094GD826SD> What are our Q4 revenue numbers?',
                        'ts': '1234567890.123456'
                        # No thread_ts - this creates a new thread
                    }
                }),
                'headers': {
                    'x-slack-signature': 'v0=test-signature',
                    'x-slack-request-timestamp': str(int(1234567890))
                }
            }
            
            # Mock signature verification
            with patch('lambdas.handler.handler.verify_slack_signature', return_value=True):
                # Call the handler
                response = slack_handler.lambda_handler(test_event, None)
                
                # Verify response
                self.assertEqual(response['statusCode'], 200)
                
                # Check that SQS message was sent with thread_ts set to the message ts
                mock_sqs_client.send_message.assert_called_once()
                sent_message = json.loads(mock_sqs_client.send_message.call_args[1]['MessageBody'])
                
                # Verify thread_ts is set to the message timestamp (creating new thread)
                self.assertEqual(sent_message['thread_ts'], '1234567890.123456')
                self.assertEqual(sent_message['type'], 'app_mention')

    def test_thread_session_management(self):
        """Test that processor creates thread-specific session IDs"""
        
        with patch('lambdas.processor.processor.secrets_client') as mock_secrets_client, \
             patch('lambdas.processor.processor.bedrock_agent_runtime') as mock_bedrock, \
             patch('lambdas.processor.processor.requests') as mock_requests:
            
            # Mock secrets retrieval
            mock_secrets_client.get_secret_value.return_value = {
                'SecretString': json.dumps(self.mock_secrets)
            }
            
            # Mock Bedrock Agent response
            mock_bedrock.invoke_agent.return_value = {
                'completion': [
                    {
                        'chunk': {
                            'bytes': b'Test response from agent'
                        }
                    }
                ]
            }
            
            # Mock Slack API response
            mock_requests.post.return_value.json.return_value = {
                'ok': True,
                'ts': '1234567890.123456'
            }
            
            # Test event data with thread_ts
            event_data = {
                'user_id': 'U123456789',
                'channel_id': 'C123456789',
                'message_text': 'What are our Q4 revenue numbers?',
                'thread_ts': '1234567890.000000',
                'response_message_ts': '1234567890.123456'
            }
            
            # Process the app mention
            result = slack_processor.process_app_mention(event_data)
            
            # Verify it succeeded
            self.assertTrue(result)
            
            # Verify Bedrock was called with thread-specific session ID
            mock_bedrock.invoke_agent.assert_called_once()
            call_args = mock_bedrock.invoke_agent.call_args[1]
            expected_session_id = f"U123456789:C123456789:1234567890.000000"
            self.assertEqual(call_args['sessionId'], expected_session_id)

    def test_thread_slack_message_sending(self):
        """Test that messages are sent to threads correctly"""
        
        with patch('lambdas.processor.processor.get_slack_secrets') as mock_get_secrets, \
             patch('lambdas.processor.processor.requests') as mock_requests:
            
            # Mock secrets
            mock_get_secrets.return_value = self.mock_secrets
            
            # Mock successful Slack API response
            mock_requests.post.return_value.json.return_value = {
                'ok': True,
                'ts': '1234567890.789012'
            }
            
            # Test sending message in thread
            result = slack_processor.send_slack_message(
                channel_id='C123456789',
                text='Test response',
                thread_ts='1234567890.000000'
            )
            
            # Verify it succeeded
            self.assertTrue(result)
            
            # Verify the API call included thread_ts
            mock_requests.post.assert_called_once()
            call_args = mock_requests.post.call_args[1]
            json_payload = call_args['json']
            
            self.assertEqual(json_payload['channel'], 'C123456789')
            self.assertEqual(json_payload['thread_ts'], '1234567890.000000')
            self.assertIn('Test response', json_payload['text'])

    def test_multiple_users_in_thread(self):
        """Test that multiple users can participate in the same thread"""
        
        with patch('lambdas.processor.processor.secrets_client') as mock_secrets_client, \
             patch('lambdas.processor.processor.bedrock_agent_runtime') as mock_bedrock, \
             patch('lambdas.processor.processor.requests') as mock_requests:
            
            # Mock secrets retrieval
            mock_secrets_client.get_secret_value.return_value = {
                'SecretString': json.dumps(self.mock_secrets)
            }
            
            # Mock Bedrock Agent response
            mock_bedrock.invoke_agent.return_value = {
                'completion': [
                    {
                        'chunk': {
                            'bytes': b'Response for user'
                        }
                    }
                ]
            }
            
            # Mock Slack API response
            mock_requests.post.return_value.json.return_value = {
                'ok': True,
                'ts': '1234567890.123456'
            }
            
            thread_ts = '1234567890.000000'
            channel_id = 'C123456789'
            
            # First user mentions bot in thread
            event_data_user1 = {
                'user_id': 'U123456789',
                'channel_id': channel_id,
                'message_text': 'What are our Q4 revenue numbers?',
                'thread_ts': thread_ts,
                'response_message_ts': '1234567890.123456'
            }
            
            # Second user mentions bot in same thread
            event_data_user2 = {
                'user_id': 'U987654321',
                'channel_id': channel_id,
                'message_text': 'Can you also show Q3 numbers?',
                'thread_ts': thread_ts,
                'response_message_ts': '1234567890.789012'
            }
            
            # Process both mentions
            result1 = slack_processor.process_app_mention(event_data_user1)
            result2 = slack_processor.process_app_mention(event_data_user2)
            
            # Both should succeed
            self.assertTrue(result1)
            self.assertTrue(result2)
            
            # Verify both calls used different session IDs (user-specific)
            self.assertEqual(mock_bedrock.invoke_agent.call_count, 2)
            
            call1_session = mock_bedrock.invoke_agent.call_args_list[0][1]['sessionId']
            call2_session = mock_bedrock.invoke_agent.call_args_list[1][1]['sessionId']
            
            expected_session1 = f"U123456789:{channel_id}:{thread_ts}"
            expected_session2 = f"U987654321:{channel_id}:{thread_ts}"
            
            self.assertEqual(call1_session, expected_session1)
            self.assertEqual(call2_session, expected_session2)

    def test_thread_vs_channel_session_isolation(self):
        """Test that thread sessions are isolated from channel sessions"""
        
        with patch('lambdas.processor.processor.secrets_client') as mock_secrets_client, \
             patch('lambdas.processor.processor.bedrock_agent_runtime') as mock_bedrock, \
             patch('lambdas.processor.processor.requests') as mock_requests:
            
            # Mock secrets retrieval
            mock_secrets_client.get_secret_value.return_value = {
                'SecretString': json.dumps(self.mock_secrets)
            }
            
            # Mock Bedrock Agent response
            mock_bedrock.invoke_agent.return_value = {
                'completion': [
                    {
                        'chunk': {
                            'bytes': b'Response from agent'
                        }
                    }
                ]
            }
            
            # Mock Slack API response
            mock_requests.post.return_value.json.return_value = {
                'ok': True,
                'ts': '1234567890.123456'
            }
            
            user_id = 'U123456789'
            channel_id = 'C123456789'
            thread_ts = '1234567890.000000'
            
            # Message in thread
            event_data_thread = {
                'user_id': user_id,
                'channel_id': channel_id,
                'message_text': 'Thread message',
                'thread_ts': thread_ts,
                'response_message_ts': '1234567890.123456'
            }
            
            # Message in channel (no thread_ts)
            event_data_channel = {
                'user_id': user_id,
                'channel_id': channel_id,
                'message_text': 'Channel message',
                'response_message_ts': '1234567890.789012'
            }
            
            # Process both messages
            result1 = slack_processor.process_app_mention(event_data_thread)
            result2 = slack_processor.process_app_mention(event_data_channel)
            
            # Both should succeed
            self.assertTrue(result1)
            self.assertTrue(result2)
            
            # Verify different session IDs were used
            self.assertEqual(mock_bedrock.invoke_agent.call_count, 2)
            
            call1_session = mock_bedrock.invoke_agent.call_args_list[0][1]['sessionId']
            call2_session = mock_bedrock.invoke_agent.call_args_list[1][1]['sessionId']
            
            expected_thread_session = f"{user_id}:{channel_id}:{thread_ts}"
            expected_channel_session = f"{user_id}:{channel_id}"
            
            self.assertEqual(call1_session, expected_thread_session)
            self.assertEqual(call2_session, expected_channel_session)

if __name__ == '__main__':
    print("Running thread behavior tests...")
    unittest.main(verbosity=2)