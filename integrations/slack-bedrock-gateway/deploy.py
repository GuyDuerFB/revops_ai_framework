#!/usr/bin/env python3
"""
AWS Best Practices Deployment Script for Slack-Bedrock Gateway
Deploys the complete architecture using CloudFormation and updates Lambda code
"""
import json
import boto3
import os
import sys
import zipfile
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

# Configuration
PROJECT_NAME = "revops-slack-bedrock"
AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"
STACK_NAME = f"{PROJECT_NAME}-stack"

# Bedrock Agent configuration from existing setup
BEDROCK_AGENT_ID = "PVWGKOWSOT"
BEDROCK_AGENT_ALIAS_ID = "LH87RBMCUQ"

def load_slack_secrets():
    """Load Slack secrets from existing configuration"""
    try:
        # Try to get from existing secrets first
        session = boto3.Session(profile_name=AWS_PROFILE)
        secrets_client = session.client('secretsmanager', region_name=AWS_REGION)
        
        try:
            response = secrets_client.get_secret_value(SecretId='revops-slack-bot-secrets')
            existing_secrets = json.loads(response['SecretString'])
            return {
                'signing_secret': existing_secrets.get('signing_secret'),
                'bot_token': existing_secrets.get('bot_token', 'PLACEHOLDER_UPDATE_AFTER_DEPLOYMENT')
            }
        except secrets_client.exceptions.ResourceNotFoundException:
            pass
        
        # Fallback to local secrets file
        script_dir = Path(__file__).parent
        secrets_file = script_dir.parent / "tools" / "slack" / "slack_secrets.json"
        
        if secrets_file.exists():
            with open(secrets_file, 'r') as f:
                local_secrets = json.load(f)
                return {
                    'signing_secret': local_secrets.get('signing_secret'),
                    'bot_token': 'PLACEHOLDER_UPDATE_AFTER_DEPLOYMENT'
                }
        
        # Default values if no secrets found
        print("⚠️  No existing secrets found. You'll need to update them after deployment.")
        return {
            'signing_secret': 'PLACEHOLDER_UPDATE_AFTER_DEPLOYMENT',
            'bot_token': 'PLACEHOLDER_UPDATE_AFTER_DEPLOYMENT'
        }
        
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return {
            'signing_secret': 'PLACEHOLDER_UPDATE_AFTER_DEPLOYMENT',
            'bot_token': 'PLACEHOLDER_UPDATE_AFTER_DEPLOYMENT'
        }

def validate_monitoring_modules(zip_file_path: str) -> Dict[str, bool]:
    """Validate monitoring modules are correctly packaged in Lambda zip"""
    validation_results = {}
    required_files = [
        'conversation_schema.py',
        'prompt_deduplicator.py', 
        'conversation_exporter.py',
        'function_interceptor.py'
    ]
    
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            zip_contents = zf.namelist()
            
            for required_file in required_files:
                is_present = required_file in zip_contents
                validation_results[required_file] = is_present
                status = "✅" if is_present else "❌"
                print(f"   {status} {required_file}: {'Present' if is_present else 'MISSING'}")
            
            # Check for any orphaned .pyc files that might cause import issues
            pyc_files = [f for f in zip_contents if f.endswith('.pyc')]
            if pyc_files:
                print(f"   ⚠️  Found {len(pyc_files)} .pyc files that may cause import conflicts")
                
        return validation_results
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return {file: False for file in required_files}

def create_lambda_package(lambda_dir: Path, output_file: str):
    """Create deployment package for Lambda function with validation"""
    try:
        temp_dir = tempfile.mkdtemp()
        package_file = os.path.join(temp_dir, output_file)
        
        with zipfile.ZipFile(package_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add Python files
            for py_file in lambda_dir.glob('*.py'):
                zip_file.write(py_file, py_file.name)
            
            # Add conversation schema from monitoring directory  
            # Use absolute path to ensure we get the correct monitoring directory
            script_dir = Path(__file__).parent
            monitoring_dir = script_dir.parent.parent / 'monitoring'
            schema_file = monitoring_dir / 'conversation_schema.py'
            if schema_file.exists():
                zip_file.write(schema_file, 'conversation_schema.py')
                print(f"✅ Added conversation_schema.py to Lambda package")
            else:
                print(f"⚠️  Warning: conversation_schema.py not found at {schema_file}")
            
            # Add prompt deduplicator
            deduplicator_file = monitoring_dir / 'prompt_deduplicator.py'
            if deduplicator_file.exists():
                zip_file.write(deduplicator_file, 'prompt_deduplicator.py')
                print(f"✅ Added prompt_deduplicator.py to Lambda package")
            else:
                print(f"⚠️  Warning: prompt_deduplicator.py not found at {deduplicator_file}")
            
            # Add conversation exporter
            exporter_file = monitoring_dir / 'conversation_exporter.py'
            if exporter_file.exists():
                zip_file.write(exporter_file, 'conversation_exporter.py')
                print(f"✅ Added conversation_exporter.py to Lambda package")
            else:
                print(f"⚠️  Warning: conversation_exporter.py not found at {exporter_file}")
            
            # Add function interceptor
            interceptor_file = monitoring_dir / 'function_interceptor.py'
            if interceptor_file.exists():
                zip_file.write(interceptor_file, 'function_interceptor.py')
                print(f"✅ Added function_interceptor.py to Lambda package")
            else:
                print(f"⚠️  Warning: function_interceptor.py not found at {interceptor_file}")
            
            # Add requirements if present (in real deployment, would install to package)
            requirements_file = lambda_dir / 'requirements.txt'
            if requirements_file.exists():
                zip_file.write(requirements_file, 'requirements.txt')
        
        return package_file
    except Exception as e:
        print(f"❌ Error creating Lambda package: {e}")
        return None

def deploy_cloudformation_stack(secrets):
    """Deploy the CloudFormation stack"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        cf_client = session.client('cloudformation', region_name=AWS_REGION)
        
        # Read CloudFormation template
        script_dir = Path(__file__).parent
        template_file = script_dir / 'infrastructure' / 'slack-bedrock-gateway.yaml'
        
        with open(template_file, 'r') as f:
            template_body = f.read()
        
        # Stack parameters
        parameters = [
            {'ParameterKey': 'ProjectName', 'ParameterValue': PROJECT_NAME},
            {'ParameterKey': 'BedrockAgentId', 'ParameterValue': BEDROCK_AGENT_ID},
            {'ParameterKey': 'BedrockAgentAliasId', 'ParameterValue': BEDROCK_AGENT_ALIAS_ID},
            {'ParameterKey': 'SlackSigningSecret', 'ParameterValue': secrets['signing_secret']},
            {'ParameterKey': 'SlackBotToken', 'ParameterValue': secrets['bot_token']}
        ]
        
        print(f"🚀 Deploying CloudFormation stack: {STACK_NAME}")
        
        try:
            # Check if stack exists
            cf_client.describe_stacks(StackName=STACK_NAME)
            print("📝 Updating existing stack...")
            
            # Update stack
            response = cf_client.update_stack(
                StackName=STACK_NAME,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_NAMED_IAM']
            )
            
        except cf_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                print("🆕 Creating new stack...")
                
                # Create stack
                response = cf_client.create_stack(
                    StackName=STACK_NAME,
                    TemplateBody=template_body,
                    Parameters=parameters,
                    Capabilities=['CAPABILITY_NAMED_IAM'],
                    Tags=[
                        {'Key': 'Project', 'Value': 'RevOps-AI-Framework'},
                        {'Key': 'Component', 'Value': 'Slack-Bedrock-Gateway'},
                        {'Key': 'Architecture', 'Value': 'AWS-Best-Practices'}
                    ]
                )
            else:
                raise
        
        print("⏳ Waiting for stack deployment to complete...")
        
        # Wait for stack completion
        waiter = cf_client.get_waiter('stack_create_complete')
        try:
            waiter.wait(
                StackName=STACK_NAME,
                WaiterConfig={'MaxAttempts': 60, 'Delay': 30}
            )
        except:
            # Try update waiter if create fails
            waiter = cf_client.get_waiter('stack_update_complete')
            waiter.wait(
                StackName=STACK_NAME,
                WaiterConfig={'MaxAttempts': 60, 'Delay': 30}
            )
        
        # Get stack outputs
        stack_response = cf_client.describe_stacks(StackName=STACK_NAME)
        outputs = {}
        for output in stack_response['Stacks'][0].get('Outputs', []):
            outputs[output['OutputKey']] = output['OutputValue']
        
        print("✅ CloudFormation stack deployed successfully!")
        return outputs
        
    except Exception as e:
        print(f"❌ Error deploying CloudFormation stack: {e}")
        return None

def update_lambda_code(stack_outputs):
    """Update Lambda function code with the actual implementations"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        
        script_dir = Path(__file__).parent
        
        # Update Handler Lambda
        print("📦 Packaging Handler Lambda...")
        handler_dir = script_dir / 'lambdas' / 'handler'
        handler_package = create_lambda_package(handler_dir, 'handler.zip')
        
        if handler_package:
            # Validate handler package before deployment
            print("🔍 Validating Handler Lambda package...")
            handler_validation = validate_monitoring_modules(handler_package)
            if not all(handler_validation.values()):
                print("⚠️  Warning: Some monitoring modules missing from Handler Lambda")
            
            print("🔄 Updating Handler Lambda code...")
            with open(handler_package, 'rb') as f:
                lambda_client.update_function_code(
                    FunctionName=f"{PROJECT_NAME}-handler",
                    ZipFile=f.read()
                )
            os.remove(handler_package)
            print("✅ Handler Lambda updated")
        
        # Update Processor Lambda
        print("📦 Packaging Processor Lambda...")
        processor_dir = script_dir / 'lambdas' / 'processor'
        processor_package = create_lambda_package(processor_dir, 'processor.zip')
        
        if processor_package:
            # Validate processor package before deployment (CRITICAL for monitoring)
            print("🔍 Validating Processor Lambda package...")
            processor_validation = validate_monitoring_modules(processor_package)
            missing_files = [f for f, present in processor_validation.items() if not present]
            
            if missing_files:
                print(f"❌ CRITICAL: Missing monitoring files in Processor Lambda: {missing_files}")
                print("❌ Deployment aborted - monitoring will not work without these files")
                return False
            else:
                print("✅ All monitoring modules validated in Processor Lambda")
            
            print("🔄 Updating Processor Lambda code...")
            with open(processor_package, 'rb') as f:
                lambda_client.update_function_code(
                    FunctionName=f"{PROJECT_NAME}-processor",
                    ZipFile=f.read()
                )
            os.remove(processor_package)
            print("✅ Processor Lambda updated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda code: {e}")
        return False

def cleanup_old_resources():
    """Clean up old Lambda function and resources"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        
        # List of old resources to clean up
        old_function_name = 'revops-slack-bot'
        
        try:
            # Delete old function if it exists
            lambda_client.delete_function(FunctionName=old_function_name)
            print(f"🗑️  Deleted old Lambda function: {old_function_name}")
        except lambda_client.exceptions.ResourceNotFoundException:
            print(f"ℹ️  Old Lambda function {old_function_name} not found (already cleaned up)")
        except Exception as e:
            print(f"⚠️  Could not delete old function {old_function_name}: {e}")
        
        # Clean up old DynamoDB table
        try:
            dynamodb = session.client('dynamodb', region_name=AWS_REGION)
            dynamodb.delete_table(TableName='revops-slack-conversations')
            print("🗑️  Deleted old DynamoDB table: revops-slack-conversations")
        except dynamodb.exceptions.ResourceNotFoundException:
            print("ℹ️  Old DynamoDB table not found (already cleaned up)")
        except Exception as e:
            print(f"⚠️  Could not delete old DynamoDB table: {e}")
        
    except Exception as e:
        print(f"⚠️  Error during cleanup: {e}")

def test_lambda_monitoring_import():
    """Test Lambda function can import monitoring modules"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        
        print("🧪 Testing Processor Lambda monitoring import...")
        
        # Invoke Lambda with test payload to check import status
        test_payload = {
            "test": True,
            "validate_imports": True
        }
        
        response = lambda_client.invoke(
            FunctionName=f"{PROJECT_NAME}-processor",
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        # Check CloudWatch logs for import status
        logs_client = session.client('logs', region_name=AWS_REGION)
        
        # Wait a moment for logs to appear
        import time
        time.sleep(5)
        
        # Get recent log events
        log_events = logs_client.filter_log_events(
            logGroupName=f'/aws/lambda/{PROJECT_NAME}-processor',
            startTime=int((datetime.now().timestamp() - 300) * 1000),  # Last 5 minutes
            filterPattern='schema'
        )
        
        # Look for schema import success/failure messages
        for event in log_events.get('events', []):
            message = event['message']
            if '✅ Successfully imported conversation tracking schema' in message:
                print("✅ Schema import test PASSED")
                return True
            elif '❌ WARNING: conversation_schema import failed' in message:
                print("❌ Schema import test FAILED")
                print(f"Error details: {message}")
                return False
        
        print("⚠️  Schema import status unclear from logs")
        return None
        
    except Exception as e:
        print(f"❌ Error testing Lambda monitoring import: {e}")
        return False

def main():
    """Main deployment function with enhanced monitoring validation"""
    print("🚀 RevOps Slack-Bedrock Gateway - AWS Best Practices Deployment")
    print("=" * 80)
    
    # Load Slack secrets
    print("🔐 Loading Slack secrets...")
    secrets = load_slack_secrets()
    
    if secrets['signing_secret'] == 'PLACEHOLDER_UPDATE_AFTER_DEPLOYMENT':
        print("⚠️  Using placeholder secrets. Update them after deployment.")
    else:
        print("✅ Loaded existing Slack secrets")
    
    # Deploy CloudFormation stack
    stack_outputs = deploy_cloudformation_stack(secrets)
    if not stack_outputs:
        print("❌ Failed to deploy CloudFormation stack")
        sys.exit(1)
    
    # Update Lambda code
    if not update_lambda_code(stack_outputs):
        print("❌ Failed to update Lambda code")
        sys.exit(1)
    
    # Clean up old resources
    print("🧹 Cleaning up old resources...")
    cleanup_old_resources()
    
    # Post-deployment monitoring validation
    print("\\n🔍 VALIDATING MONITORING SYSTEM...")
    print("=" * 80)
    monitoring_test_result = test_lambda_monitoring_import()
    
    if monitoring_test_result is True:
        print("✅ MONITORING VALIDATION PASSED - Full conversation tracking enabled")
    elif monitoring_test_result is False:
        print("❌ MONITORING VALIDATION FAILED - Review Lambda logs")
        print("⚠️  Conversation tracking will be limited to basic format")
    else:
        print("⚠️  MONITORING VALIDATION INCONCLUSIVE - Manual verification recommended")
    
    print("\\n🎉 DEPLOYMENT COMPLETED!")
    print("=" * 80)
    print("📋 Stack Outputs:")
    for key, value in stack_outputs.items():
        print(f"   {key}: {value}")
    
    print("\\n🔧 NEXT STEPS:")
    print("=" * 80)
    print("1. Configure Slack App Event Subscriptions:")
    print(f"   - Request URL: {stack_outputs.get('ApiGatewayUrl', 'Check CloudFormation outputs')}")
    print("   - Subscribe to: app_mention")
    print("\\n2. Update Bot Token in Secrets Manager:")
    print(f"   - Secret ARN: {stack_outputs.get('SecretsArn', 'Check CloudFormation outputs')}")
    print("   - Add your Slack Bot User OAuth Token")
    print("\\n3. Test the integration:")
    print("   - Mention @RevBot in a Slack channel")
    print("   - Monitor CloudWatch logs for both Lambda functions")
    
    print("\\n📊 Architecture:")
    print("Slack → API Gateway → Handler Lambda → SQS → Processor Lambda → Bedrock Agent → Response")

if __name__ == "__main__":
    main()