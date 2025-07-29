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

# Configuration
PROJECT_NAME = "revops-slack-bedrock"
AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"
STACK_NAME = f"{PROJECT_NAME}-stack"

# Bedrock Agent configuration from existing setup
BEDROCK_AGENT_ID = "TCX9CGOKBR"
BEDROCK_AGENT_ALIAS_ID = "BKLREFH3L0"

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

def create_lambda_package(lambda_dir: Path, output_file: str):
    """Create deployment package for Lambda function"""
    try:
        temp_dir = tempfile.mkdtemp()
        package_file = os.path.join(temp_dir, output_file)
        
        with zipfile.ZipFile(package_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add Python files
            for py_file in lambda_dir.glob('*.py'):
                zip_file.write(py_file, py_file.name)
            
            # Add conversation schema from monitoring directory
            monitoring_dir = lambda_dir.parent.parent.parent / 'monitoring'
            schema_file = monitoring_dir / 'conversation_schema.py'
            if schema_file.exists():
                zip_file.write(schema_file, 'conversation_schema.py')
                print(f"✅ Added conversation_schema.py to Lambda package")
            else:
                print(f"⚠️  Warning: conversation_schema.py not found at {schema_file}")
            
            # Add function interceptor
            interceptor_file = monitoring_dir / 'function_interceptor.py'
            if interceptor_file.exists():
                zip_file.write(interceptor_file, 'function_interceptor.py')
                print(f"✅ Added function_interceptor.py to Lambda package")
            
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

def main():
    """Main deployment function"""
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