#!/usr/bin/env python3
"""
RevOps AI Framework - Infrastructure Deployment Manager
======================================================
Enhanced CloudFormation management with validation and deployment status tracking.

Usage:
    python infrastructure/deploy-infrastructure.py --stack-name revops-slack-bedrock
    python infrastructure/deploy-infrastructure.py --validate-only
    python infrastructure/deploy-infrastructure.py --check-status
"""

import os
import sys
import json
import boto3
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class InfrastructureDeployer:
    """Enhanced CloudFormation deployment manager"""
    
    def __init__(self, profile_name: str = None, region: str = 'us-east-1'):
        self.profile_name = profile_name
        self.region = region
        self.session = None
        self.cf_client = None
        self.deployment_log = []
        
        # Load configuration
        self._load_configuration()
        self._initialize_aws_session()
        
    def _load_configuration(self):
        """Load deployment configuration"""
        config_path = Path("deployment/config.json")
        if not config_path.exists():
            self._error("Configuration file not found: deployment/config.json")
        
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.profile_name = self.profile_name or self.config.get('profile_name')
        self.region = self.region or self.config.get('region_name', 'us-east-1')
        
    def _initialize_aws_session(self):
        """Initialize AWS session with SSO"""
        try:
            if self.profile_name:
                self.session = boto3.Session(profile_name=self.profile_name)
            else:
                self.session = boto3.Session()
                
            self.cf_client = self.session.client('cloudformation', region_name=self.region)
            
            # Test connection
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ Connected to AWS as: {identity.get('Arn')}")
            
        except Exception as e:
            self._error(f"AWS connection failed: {e}")
    
    def validate_templates(self) -> bool:
        """Validate all CloudFormation templates"""
        print("\n🔍 Validating CloudFormation Templates...")
        
        template_paths = [
            "integrations/slack-bedrock-gateway/infrastructure/slack-bedrock-gateway.yaml"
        ]
        
        validation_success = True
        
        for template_path in template_paths:
            if not Path(template_path).exists():
                print(f"  ❌ Template not found: {template_path}")
                validation_success = False
                continue
                
            try:
                with open(template_path, 'r') as f:
                    template_body = f.read()
                
                # Validate template syntax
                response = self.cf_client.validate_template(TemplateBody=template_body)
                
                print(f"  ✅ Template valid: {template_path}")
                print(f"    Description: {response.get('Description', 'No description')}")
                print(f"    Parameters: {len(response.get('Parameters', []))}")
                print(f"    Capabilities: {response.get('Capabilities', [])}")
                
            except Exception as e:
                print(f"  ❌ Template validation failed: {template_path}")
                print(f"    Error: {e}")
                validation_success = False
        
        return validation_success
    
    def check_stack_status(self, stack_name: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Check CloudFormation stack status"""
        try:
            response = self.cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            status = stack['StackStatus']
            outputs = {output['OutputKey']: output['OutputValue'] 
                      for output in stack.get('Outputs', [])}
            
            return status, outputs
            
        except self.cf_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                return None, None
            raise e
    
    def deploy_infrastructure(self, stack_name: str, template_path: str, parameters: Dict[str, str] = None) -> bool:
        """Deploy CloudFormation infrastructure"""
        print(f"\n🚀 Deploying Infrastructure: {stack_name}")
        
        if not Path(template_path).exists():
            self._error(f"Template not found: {template_path}")
        
        try:
            with open(template_path, 'r') as f:
                template_body = f.read()
            
            # Check if stack exists
            current_status, current_outputs = self.check_stack_status(stack_name)
            
            # Prepare parameters
            cf_parameters = []
            if parameters:
                for key, value in parameters.items():
                    cf_parameters.append({
                        'ParameterKey': key,
                        'ParameterValue': value
                    })
            
            if current_status is None:
                print(f"  📦 Creating new stack: {stack_name}")
                operation = 'CREATE'
                
                self.cf_client.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=cf_parameters,
                    Capabilities=['CAPABILITY_NAMED_IAM']
                )
            else:
                print(f"  🔄 Updating existing stack: {stack_name} (current status: {current_status})")
                operation = 'UPDATE'
                
                try:
                    self.cf_client.update_stack(
                        StackName=stack_name,
                        TemplateBody=template_body,
                        Parameters=cf_parameters,
                        Capabilities=['CAPABILITY_NAMED_IAM']
                    )
                except self.cf_client.exceptions.ClientError as e:
                    if 'No updates are to be performed' in str(e):
                        print("  ✅ Stack is already up to date")
                        return True
                    raise e
            
            # Wait for completion
            return self._wait_for_stack_completion(stack_name, operation)
            
        except Exception as e:
            print(f"  ❌ Deployment failed: {e}")
            return False
    
    def _wait_for_stack_completion(self, stack_name: str, operation: str) -> bool:
        """Wait for CloudFormation operation to complete"""
        print(f"  ⏳ Waiting for {operation} to complete...")
        
        success_statuses = {
            'CREATE': 'CREATE_COMPLETE',
            'UPDATE': 'UPDATE_COMPLETE'
        }
        
        failure_statuses = {
            'CREATE': ['CREATE_FAILED', 'ROLLBACK_COMPLETE', 'ROLLBACK_FAILED'],
            'UPDATE': ['UPDATE_FAILED', 'UPDATE_ROLLBACK_COMPLETE', 'UPDATE_ROLLBACK_FAILED']
        }
        
        success_status = success_statuses[operation]
        fail_statuses = failure_statuses[operation]
        
        start_time = time.time()
        max_wait_time = 1800  # 30 minutes
        
        while time.time() - start_time < max_wait_time:
            try:
                status, outputs = self.check_stack_status(stack_name)
                
                if status == success_status:
                    print(f"  ✅ {operation} completed successfully!")
                    self._display_stack_outputs(outputs)
                    return True
                elif status in fail_statuses:
                    print(f"  ❌ {operation} failed with status: {status}")
                    self._display_stack_events(stack_name, limit=10)
                    return False
                elif status.endswith('_IN_PROGRESS'):
                    print(f"    Status: {status}...")
                    time.sleep(30)
                else:
                    print(f"    Unexpected status: {status}")
                    time.sleep(30)
                    
            except Exception as e:
                print(f"  ❌ Error checking stack status: {e}")
                return False
        
        print(f"  ⏰ Timeout waiting for {operation} to complete")
        return False
    
    def _display_stack_outputs(self, outputs: Dict[str, str]):
        """Display CloudFormation stack outputs"""
        if not outputs:
            return
            
        print("\n📋 Stack Outputs:")
        for key, value in outputs.items():
            print(f"  {key}: {value}")
    
    def _display_stack_events(self, stack_name: str, limit: int = 10):
        """Display recent CloudFormation stack events"""
        try:
            response = self.cf_client.describe_stack_events(StackName=stack_name)
            events = response['StackEvents'][:limit]
            
            print("\n📝 Recent Stack Events:")
            for event in events:
                timestamp = event['Timestamp'].strftime('%H:%M:%S')
                resource_type = event.get('ResourceType', 'Unknown')
                status = event.get('ResourceStatus', 'Unknown')
                reason = event.get('ResourceStatusReason', '')
                
                print(f"  [{timestamp}] {resource_type}: {status}")
                if reason:
                    print(f"    Reason: {reason}")
                    
        except Exception as e:
            print(f"❌ Error retrieving stack events: {e}")
    
    def get_deployment_parameters(self) -> Dict[str, str]:
        """Get deployment parameters from configuration"""
        slack_config = self.config.get('integrations', {}).get('slack_bedrock_gateway', {})
        manager_agent = self.config.get('manager_agent', {})
        
        # Get parameters from environment or prompt user
        parameters = {
            'ProjectName': 'revops-slack-bedrock',
            'BedrockAgentId': manager_agent.get('agent_id', 'TCX9CGOKBR'),
            'BedrockAgentAliasId': manager_agent.get('agent_alias_id', 'BKLREFH3L0')
        }
        
        # Get Slack credentials (should be set as environment variables for security)
        slack_signing_secret = os.getenv('SLACK_SIGNING_SECRET')
        slack_bot_token = os.getenv('SLACK_BOT_TOKEN')
        
        if not slack_signing_secret:
            print("⚠️  SLACK_SIGNING_SECRET environment variable not set")
            slack_signing_secret = input("Enter Slack Signing Secret: ").strip()
        
        if not slack_bot_token:
            print("⚠️  SLACK_BOT_TOKEN environment variable not set")
            slack_bot_token = input("Enter Slack Bot Token: ").strip()
        
        parameters['SlackSigningSecret'] = slack_signing_secret
        parameters['SlackBotToken'] = slack_bot_token
        
        return parameters
    
    def update_config_with_outputs(self, stack_outputs: Dict[str, str]):
        """Update configuration file with deployment outputs"""
        if not stack_outputs:
            return
            
        # Update Slack integration configuration
        slack_config = self.config.setdefault('integrations', {}).setdefault('slack_bedrock_gateway', {})
        
        if 'ApiGatewayUrl' in stack_outputs:
            slack_config['api_gateway_url'] = stack_outputs['ApiGatewayUrl']
            slack_config['status'] = 'deployed'
            slack_config['last_deployed'] = datetime.now().isoformat()
        
        # Update lambda function configurations
        lambda_functions = self.config.setdefault('lambda_functions', {})
        
        if 'HandlerLambdaArn' in stack_outputs:
            lambda_functions.setdefault('slack_handler', {})['function_arn'] = stack_outputs['HandlerLambdaArn']
        
        if 'ProcessorLambdaArn' in stack_outputs:
            lambda_functions.setdefault('slack_processor', {})['function_arn'] = stack_outputs['ProcessorLambdaArn']
        
        # Save updated configuration
        config_path = Path("deployment/config.json")
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        
        print("✅ Configuration updated with deployment outputs")
    
    def _log(self, message: str):
        """Log deployment action"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.deployment_log.append(log_entry)
    
    def _error(self, message: str):
        """Handle deployment error"""
        print(f"❌ ERROR: {message}")
        sys.exit(1)

def main():
    """Main infrastructure deployment entry point"""
    parser = argparse.ArgumentParser(description='RevOps AI Framework Infrastructure Deployment')
    parser.add_argument('--stack-name', default='revops-slack-bedrock',
                       help='CloudFormation stack name')
    parser.add_argument('--template-path', 
                       default='integrations/slack-bedrock-gateway/infrastructure/slack-bedrock-gateway.yaml',
                       help='Path to CloudFormation template')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate templates, do not deploy')
    parser.add_argument('--check-status', action='store_true',
                       help='Check current deployment status')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    # Create deployer
    deployer = InfrastructureDeployer(
        profile_name=args.profile,
        region=args.region
    )
    
    # Validate templates
    if not deployer.validate_templates():
        sys.exit(1)
    
    if args.validate_only:
        print("✅ Template validation completed successfully!")
        return
    
    # Check status only
    if args.check_status:
        status, outputs = deployer.check_stack_status(args.stack_name)
        if status:
            print(f"Stack Status: {status}")
            deployer._display_stack_outputs(outputs)
        else:
            print("Stack does not exist")
        return
    
    # Deploy infrastructure
    parameters = deployer.get_deployment_parameters()
    
    success = deployer.deploy_infrastructure(
        stack_name=args.stack_name,
        template_path=args.template_path,
        parameters=parameters
    )
    
    if success:
        # Update configuration with outputs
        _, outputs = deployer.check_stack_status(args.stack_name)
        deployer.update_config_with_outputs(outputs)
        print("\n✅ Infrastructure deployment completed successfully!")
    else:
        print("\n❌ Infrastructure deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()