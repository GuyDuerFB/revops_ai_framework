#!/usr/bin/env python3
"""
Integration tests for Slack-Bedrock Gateway
Tests the complete AWS best practices architecture
"""
import json
import boto3
import requests
import time
import hashlib
import hmac
from datetime import datetime

# Configuration
AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"
STACK_NAME = "revops-slack-bedrock-stack"

def get_stack_outputs():
    """Get CloudFormation stack outputs"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        cf_client = session.client('cloudformation', region_name=AWS_REGION)
        
        response = cf_client.describe_stacks(StackName=STACK_NAME)
        outputs = {}
        
        for output in response['Stacks'][0].get('Outputs', []):
            outputs[output['OutputKey']] = output['OutputValue']
        
        return outputs
    except Exception as e:
        print(f"❌ Error getting stack outputs: {e}")
        return {}

def test_api_gateway_url_verification():
    """Test API Gateway URL verification (Slack challenge)"""
    try:
        outputs = get_stack_outputs()
        api_url = outputs.get('ApiGatewayUrl')
        
        if not api_url:
            print("❌ API Gateway URL not found in stack outputs")
            return False
        
        print(f"🧪 Testing URL verification: {api_url}")
        
        # Test challenge request
        challenge_data = {
            "type": "url_verification",
            "challenge": "test_challenge_12345"
        }
        
        response = requests.post(
            api_url,
            json=challenge_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200 and response.text == "test_challenge_12345":
            print("✅ URL verification test passed")
            return True
        else:
            print(f"❌ URL verification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ URL verification test error: {e}")
        return False

def test_lambda_functions():
    """Test Lambda function deployment and configuration"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        
        functions = [
            'revops-slack-bedrock-handler',
            'revops-slack-bedrock-processor'
        ]
        
        results = {}
        
        for function_name in functions:
            try:
                response = lambda_client.get_function(FunctionName=function_name)
                config = response['Configuration']
                
                results[function_name] = {
                    'state': config['State'],
                    'last_update_status': config['LastUpdateStatus'],
                    'runtime': config['Runtime'],
                    'handler': config['Handler'],
                    'timeout': config['Timeout'],
                    'memory_size': config['MemorySize']
                }
                
                print(f"✅ {function_name}: {config['State']} - {config['LastUpdateStatus']}")
                
            except lambda_client.exceptions.ResourceNotFoundException:
                print(f"❌ {function_name}: Not found")
                results[function_name] = {'error': 'Not found'}
        
        return results
        
    except Exception as e:
        print(f"❌ Lambda function test error: {e}")
        return {}

def test_sqs_queue():
    """Test SQS queue configuration"""
    try:
        outputs = get_stack_outputs()
        queue_url = outputs.get('ProcessingQueueUrl')
        
        if not queue_url:
            print("❌ SQS Queue URL not found in stack outputs")
            return False
        
        session = boto3.Session(profile_name=AWS_PROFILE)
        sqs_client = session.client('sqs', region_name=AWS_REGION)
        
        # Get queue attributes
        response = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )
        
        attributes = response['Attributes']
        
        print(f"✅ SQS Queue configured:")
        print(f"   Visibility Timeout: {attributes.get('VisibilityTimeout')} seconds")
        print(f"   Message Retention: {attributes.get('MessageRetentionPeriod')} seconds")
        print(f"   Redrive Policy: {attributes.get('RedrivePolicy', 'None')}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQS queue test error: {e}")
        return False

def test_secrets_manager():
    """Test Secrets Manager configuration"""
    try:
        outputs = get_stack_outputs()
        secrets_arn = outputs.get('SecretsArn')
        
        if not secrets_arn:
            print("❌ Secrets ARN not found in stack outputs")
            return False
        
        session = boto3.Session(profile_name=AWS_PROFILE)
        secrets_client = session.client('secretsmanager', region_name=AWS_REGION)
        
        # Test secret retrieval
        response = secrets_client.get_secret_value(SecretId=secrets_arn)
        
        if 'SecretString' in response:
            secrets = json.loads(response['SecretString'])
            has_signing_secret = bool(secrets.get('signing_secret'))
            has_bot_token = bool(secrets.get('bot_token'))
            
            print(f"✅ Secrets Manager configured:")
            print(f"   Signing Secret: {'✅' if has_signing_secret else '❌'}")
            print(f"   Bot Token: {'✅' if has_bot_token else '❌'}")
            
            return has_signing_secret and has_bot_token
        else:
            print("❌ No SecretString in response")
            return False
            
    except Exception as e:
        print(f"❌ Secrets Manager test error: {e}")
        return False

def test_bedrock_agent_access():
    """Test Bedrock Agent accessibility"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        bedrock_runtime = session.client('bedrock-agent-runtime', region_name=AWS_REGION)
        
        # Test agent invocation
        test_session_id = f"test-session-{int(time.time())}"
        
        response = bedrock_runtime.invoke_agent(
            agentId='TCX9CGOKBR',
            agentAliasId='RSYE8T5V96',
            sessionId=test_session_id,
            inputText="Test: Can you confirm you're working?"
        )
        
        # Process response
        agent_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    agent_response += chunk['bytes'].decode('utf-8')
        
        if agent_response:
            print(f"✅ Bedrock Agent accessible and responding")
            print(f"   Response preview: {agent_response[:100]}...")
            return True
        else:
            print("❌ Bedrock Agent not responding")
            return False
            
    except Exception as e:
        print(f"❌ Bedrock Agent test error: {e}")
        return False

def test_cloudwatch_logs():
    """Test CloudWatch logs configuration"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        logs_client = session.client('logs', region_name=AWS_REGION)
        
        log_groups = [
            '/aws/lambda/revops-slack-bedrock-handler',
            '/aws/lambda/revops-slack-bedrock-processor'
        ]
        
        for log_group in log_groups:
            try:
                response = logs_client.describe_log_groups(
                    logGroupNamePrefix=log_group
                )
                
                if response['logGroups']:
                    group = response['logGroups'][0]
                    print(f"✅ {log_group}: {group.get('retentionInDays', 'Never')} days retention")
                else:
                    print(f"❌ {log_group}: Not found")
                    
            except Exception as e:
                print(f"❌ {log_group}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ CloudWatch logs test error: {e}")
        return False

def run_comprehensive_test():
    """Run all integration tests"""
    print("🧪 RevOps Slack-Bedrock Gateway - Integration Tests")
    print("=" * 70)
    
    tests = [
        ("Stack Outputs", lambda: bool(get_stack_outputs())),
        ("API Gateway URL Verification", test_api_gateway_url_verification),
        ("Lambda Functions", lambda: bool(test_lambda_functions())),
        ("SQS Queue", test_sqs_queue),
        ("Secrets Manager", test_secrets_manager),
        ("Bedrock Agent Access", test_bedrock_agent_access),
        ("CloudWatch Logs", test_cloudwatch_logs)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\\n🔍 Testing {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\\n" + "=" * 70)
    print("🎯 TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print(f"\\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\\n🎉 ALL TESTS PASSED!")
        print("The Slack-Bedrock Gateway is ready for use.")
    else:
        print(f"\\n⚠️  {total - passed} TESTS FAILED!")
        print("Please check the errors above and fix any issues.")
    
    # Next steps
    if passed == total:
        outputs = get_stack_outputs()
        print("\\n📋 READY FOR SLACK CONFIGURATION:")
        print("=" * 70)
        print(f"API Gateway URL: {outputs.get('ApiGatewayUrl', 'Check CloudFormation outputs')}")
        print("\\n1. Configure Slack App Event Subscriptions with the API Gateway URL")
        print("2. Subscribe to 'app_mention' events") 
        print("3. Install the app to your workspace")
        print("4. Update bot token in Secrets Manager if needed")
        print("5. Test with @RevBot mentions in Slack")

if __name__ == "__main__":
    run_comprehensive_test()