#!/usr/bin/env python3
"""
Webhook Gateway Deployment Script
Deploys the RevOps AI Framework Webhook Gateway infrastructure and Lambda function
"""

import boto3
import json
import os
import sys
import zipfile
import tempfile
import shutil
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

class WebhookGatewayDeployer:
    """Deploys webhook gateway infrastructure and Lambda function"""
    
    def __init__(self, config_path: str, aws_profile: str = None):
        """
        Initialize deployer with configuration.
        
        Args:
            config_path: Path to deployment configuration file
            aws_profile: AWS profile to use for deployment
        """
        self.config_path = config_path
        self.aws_profile = aws_profile
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize AWS clients
        self.session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
        self.cloudformation = self.session.client('cloudformation')
        self.lambda_client = self.session.client('lambda')
        self.sts = self.session.client('sts')
        self.bedrock_agent = self.session.client('bedrock-agent')
        
        # Get AWS account info
        self.account_info = self.sts.get_caller_identity()
        self.account_id = self.account_info['Account']
        self.region = self.session.region_name or self.config.get('region', 'us-east-1')
        
        print(f"Deploying to account {self.account_id} in region {self.region}")
    
    def validate_prerequisites(self) -> bool:
        """
        Validate that prerequisites are met before deployment.
        
        Returns:
            True if prerequisites are met, False otherwise
        """
        print("Validating deployment prerequisites...")
        
        try:
            # Check if Bedrock Agent exists
            bedrock_agent_id = self.config.get('bedrock_agent_id')
            if bedrock_agent_id:
                try:
                    self.bedrock_agent.get_agent(agentId=bedrock_agent_id)
                    print(f"✓ Bedrock Agent '{bedrock_agent_id}' found")
                except Exception as e:
                    print(f"✗ Bedrock Agent '{bedrock_agent_id}' not found: {str(e)}")
                    return False
            else:
                print("⚠ No Bedrock Agent ID configured")
            
            # Validate webhook URLs if provided
            webhook_urls = self.config.get('webhook_urls', {})
            configured_webhooks = [k for k, v in webhook_urls.items() if v]
            if configured_webhooks:
                print(f"✓ Webhook URLs configured for: {', '.join(configured_webhooks)}")
            else:
                print("⚠ No webhook URLs configured - you'll need to update them after deployment")
            
            print("✓ Prerequisites validation passed")
            return True
            
        except Exception as e:
            print(f"✗ Prerequisites validation failed: {str(e)}")
            return False
    
    def package_lambda_function(self) -> str:
        """
        Package Lambda function code into a zip file.
        
        Returns:
            Path to the created zip file
        """
        print("Packaging Lambda function...")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        lambda_dir = os.path.join(os.path.dirname(__file__), 'lambda')
        
        try:
            # Copy lambda files to temp directory
            for file in os.listdir(lambda_dir):
                if file.endswith('.py'):
                    shutil.copy2(
                        os.path.join(lambda_dir, file),
                        os.path.join(temp_dir, file)
                    )
            
            # Create zip file
            zip_path = os.path.join(temp_dir, 'webhook-gateway-lambda.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
            
            print(f"✓ Lambda function packaged: {zip_path}")
            return zip_path
            
        except Exception as e:
            print(f"✗ Failed to package Lambda function: {str(e)}")
            raise
    
    def deploy_infrastructure(self) -> Dict[str, Any]:
        """
        Deploy CloudFormation infrastructure.
        
        Returns:
            Stack outputs dictionary
        """
        print("Deploying CloudFormation infrastructure...")
        
        stack_name = self.config['cloudformation']['stack_name']
        template_file = os.path.join(
            os.path.dirname(__file__),
            self.config['cloudformation']['template_file']
        )
        
        try:
            # Read CloudFormation template
            with open(template_file, 'r') as f:
                template_body = f.read()
            
            # Prepare parameters
            parameters = [
                {
                    'ParameterKey': 'EnvironmentName',
                    'ParameterValue': self.config['environment_name']
                },
                {
                    'ParameterKey': 'ManagerAgentFunctionName',
                    'ParameterValue': self.config['manager_agent_function_name']
                },
                {
                    'ParameterKey': 'LogLevel',
                    'ParameterValue': self.config['log_level']
                },
                {
                    'ParameterKey': 'BedrockAgentId',
                    'ParameterValue': self.config.get('bedrock_agent_id', 'PVWGKOWSOT')
                },
                {
                    'ParameterKey': 'BedrockAgentAliasId',
                    'ParameterValue': self.config.get('bedrock_agent_alias_id', 'TSTALIASID')
                }
            ]
            
            # Add webhook URL parameters
            webhook_urls = self.config.get('webhook_urls', {})
            webhook_params = {
                'DealAnalysisWebhookUrl': webhook_urls.get('deal_analysis', ''),
                'DataAnalysisWebhookUrl': webhook_urls.get('data_analysis', ''),
                'LeadAnalysisWebhookUrl': webhook_urls.get('lead_analysis', ''),
                'GeneralWebhookUrl': webhook_urls.get('general', '')
            }
            
            for param_key, param_value in webhook_params.items():
                parameters.append({
                    'ParameterKey': param_key,
                    'ParameterValue': param_value
                })
            
            # Check if stack exists
            try:
                self.cloudformation.describe_stacks(StackName=stack_name)
                operation = 'UPDATE'
                print(f"Updating existing stack: {stack_name}")
            except self.cloudformation.exceptions.ClientError:
                operation = 'CREATE'
                print(f"Creating new stack: {stack_name}")
            
            # Deploy stack
            if operation == 'CREATE':
                response = self.cloudformation.create_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=parameters,
                    Capabilities=['CAPABILITY_NAMED_IAM'],
                    Tags=[
                        {'Key': 'Application', 'Value': 'RevOpsAI'},
                        {'Key': 'Component', 'Value': 'WebhookGateway'},
                        {'Key': 'Environment', 'Value': self.config['environment_name']},
                        {'Key': 'DeployedBy', 'Value': self.account_info.get('Arn', 'unknown')},
                        {'Key': 'DeployedAt', 'Value': datetime.utcnow().isoformat()}
                    ]
                )
            else:
                response = self.cloudformation.update_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Parameters=parameters,
                    Capabilities=['CAPABILITY_NAMED_IAM']
                )
            
            # Wait for stack completion
            print("Waiting for stack deployment to complete...")
            waiter = self.cloudformation.get_waiter(f'stack_{operation.lower()}_complete')
            waiter.wait(
                StackName=stack_name,
                WaiterConfig={'Delay': 10, 'MaxAttempts': 180}  # 30 minutes max
            )
            
            # Get stack outputs
            stack_info = self.cloudformation.describe_stacks(StackName=stack_name)
            outputs = {}
            for output in stack_info['Stacks'][0].get('Outputs', []):
                outputs[output['OutputKey']] = output['OutputValue']
            
            print(f"✓ CloudFormation stack {operation.lower()}d successfully")
            return outputs
            
        except Exception as e:
            print(f"✗ CloudFormation deployment failed: {str(e)}")
            raise
    
    def update_lambda_function(self, function_name: str, zip_path: str) -> None:
        """
        Update Lambda function code.
        
        Args:
            function_name: Name of Lambda function to update
            zip_path: Path to zip file containing function code
        """
        print(f"Updating Lambda function code: {function_name}")
        
        try:
            # Read zip file
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            # Update function code
            response = self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            # Wait for update to complete
            waiter = self.lambda_client.get_waiter('function_updated')
            waiter.wait(
                FunctionName=function_name,
                WaiterConfig={'Delay': 5, 'MaxAttempts': 60}  # 5 minutes max
            )
            
            print(f"✓ Lambda function updated successfully")
            
        except Exception as e:
            print(f"✗ Lambda function update failed: {str(e)}")
            raise
    
    def deploy(self) -> Dict[str, Any]:
        """
        Execute complete deployment.
        
        Returns:
            Deployment results including endpoints and function names
        """
        print("=== Starting Webhook Gateway Deployment ===")
        
        try:
            # Step 1: Validate prerequisites
            if not self.validate_prerequisites():
                raise Exception("Prerequisites validation failed")
            
            # Step 2: Package Lambda function
            zip_path = self.package_lambda_function()
            
            # Step 3: Deploy infrastructure
            outputs = self.deploy_infrastructure()
            
            # Step 4: Update Lambda function codes
            webhook_function_name = outputs.get('WebhookGatewayFunctionName')
            manager_function_name = self.config['manager_agent_function_name']
            
            if webhook_function_name:
                self.update_lambda_function(webhook_function_name, zip_path)
                self.update_lambda_function(manager_function_name, zip_path)
            else:
                raise Exception("Could not get function name from CloudFormation outputs")
            
            # Step 5: Cleanup temporary files
            os.remove(zip_path)
            
            print("=== Deployment Completed Successfully ===")
            print(f"Webhook Endpoint: {outputs.get('WebhookEndpoint', 'Not available')}")
            print(f"Health Check: {outputs.get('HealthCheckEndpoint', 'Not available')}")
            print(f"Function Name: {outputs.get('WebhookGatewayFunctionName', 'Not available')}")
            
            return outputs
            
        except Exception as e:
            print(f"=== Deployment Failed ===")
            print(f"Error: {str(e)}")
            raise

def main():
    """Main deployment entry point"""
    parser = argparse.ArgumentParser(description='Deploy RevOps AI Webhook Gateway')
    parser.add_argument(
        '--config',
        default='config/deployment-config.json',
        help='Path to deployment configuration file'
    )
    parser.add_argument(
        '--profile',
        default='FireboltSystemAdministrator-740202120544',
        help='AWS profile to use for deployment'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate prerequisites, do not deploy'
    )
    
    args = parser.parse_args()
    
    # Get config path relative to script directory
    config_path = os.path.join(os.path.dirname(__file__), args.config)
    
    try:
        deployer = WebhookGatewayDeployer(config_path, args.profile)
        
        if args.validate_only:
            if deployer.validate_prerequisites():
                print("✓ Validation passed - ready for deployment")
                sys.exit(0)
            else:
                print("✗ Validation failed")
                sys.exit(1)
        else:
            results = deployer.deploy()
            print("\nDeployment results:")
            for key, value in results.items():
                print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()