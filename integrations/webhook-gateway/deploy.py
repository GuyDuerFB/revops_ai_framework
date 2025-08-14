#!/usr/bin/env python3
"""
Webhook Gateway Deployment Script
Updates the RevOps AI Framework Webhook Gateway Lambda functions
Note: Infrastructure is managed manually via AWS CLI
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
from typing import Dict, Any

class WebhookGatewayDeployer:
    """Updates webhook gateway Lambda functions"""
    
    def __init__(self, aws_profile: str = None):
        """
        Initialize deployer.
        
        Args:
            aws_profile: AWS profile to use for deployment
        """
        self.aws_profile = aws_profile
        
        # Initialize AWS clients
        self.session = boto3.Session(profile_name=aws_profile) if aws_profile else boto3.Session()
        self.lambda_client = self.session.client('lambda')
        self.sts = self.session.client('sts')
        self.bedrock_agent = self.session.client('bedrock-agent')
        
        # Get AWS account info
        self.account_info = self.sts.get_caller_identity()
        self.account_id = self.account_info['Account']
        self.region = self.session.region_name or 'us-east-1'
        
        print(f"Updating Lambda functions in account {self.account_id} region {self.region}")
    
    def validate_prerequisites(self) -> bool:
        """Validate that prerequisites are met."""
        print("Validating deployment prerequisites...")
        
        try:
            # Check if Bedrock Agent exists
            bedrock_agent_id = "PVWGKOWSOT"
            try:
                self.bedrock_agent.get_agent(agentId=bedrock_agent_id)
                print(f"✓ Bedrock Agent '{bedrock_agent_id}' found")
            except Exception as e:
                print(f"✗ Bedrock Agent '{bedrock_agent_id}' not found: {str(e)}")
                return False
            
            # Check if Lambda functions exist
            functions_to_check = [
                'prod-revops-webhook-gateway',
                'revops-webhook', 
                'revops-manager-agent-wrapper'
            ]
            
            for func_name in functions_to_check:
                try:
                    self.lambda_client.get_function(FunctionName=func_name)
                    print(f"✓ Lambda function '{func_name}' found")
                except Exception as e:
                    print(f"✗ Lambda function '{func_name}' not found: {str(e)}")
                    return False
            
            print("✓ Prerequisites validation passed")
            return True
            
        except Exception as e:
            print(f"✗ Prerequisites validation failed: {str(e)}")
            return False
    
    def package_lambda_functions(self) -> Dict[str, str]:
        """Package Lambda function code into zip files."""
        print("Packaging Lambda functions...")
        
        lambda_dir = os.path.join(os.path.dirname(__file__), 'lambda')
        temp_dir = tempfile.mkdtemp()
        zip_paths = {}
        
        try:
            # Package webhook gateway (webhook_handler.py + request_transformer.py)
            gateway_zip = os.path.join(temp_dir, 'webhook-gateway.zip')
            with zipfile.ZipFile(gateway_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(os.path.join(lambda_dir, 'webhook_handler.py'), 'webhook_handler.py')
                zipf.write(os.path.join(lambda_dir, 'request_transformer.py'), 'request_transformer.py')
            zip_paths['webhook_gateway'] = gateway_zip
            
            # Package queue processor (lambda_function.py)
            processor_zip = os.path.join(temp_dir, 'queue-processor.zip')
            with zipfile.ZipFile(processor_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(os.path.join(lambda_dir, 'lambda_function.py'), 'lambda_function.py')
            zip_paths['queue_processor'] = processor_zip
            
            # Package manager agent wrapper (manager_agent_wrapper.py)
            wrapper_zip = os.path.join(temp_dir, 'manager-wrapper.zip')
            with zipfile.ZipFile(wrapper_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(os.path.join(lambda_dir, 'manager_agent_wrapper.py'), 'manager_agent_wrapper.py')
            zip_paths['manager_wrapper'] = wrapper_zip
            
            print(f"✓ Lambda functions packaged successfully")
            return zip_paths
            
        except Exception as e:
            print(f"✗ Failed to package Lambda functions: {str(e)}")
            raise
    
    def update_lambda_function(self, function_name: str, zip_path: str) -> None:
        """Update Lambda function code."""
        print(f"Updating Lambda function: {function_name}")
        
        try:
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            response = self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            # Wait for update to complete
            waiter = self.lambda_client.get_waiter('function_updated')
            waiter.wait(
                FunctionName=function_name,
                WaiterConfig={'Delay': 2, 'MaxAttempts': 60}
            )
            
            print(f"✓ {function_name} updated successfully")
            
        except Exception as e:
            print(f"✗ Failed to update {function_name}: {str(e)}")
            raise
    
    def deploy(self) -> None:
        """Execute Lambda function updates."""
        print("=== Starting Webhook Gateway Lambda Updates ===")
        
        try:
            # Step 1: Validate prerequisites
            if not self.validate_prerequisites():
                raise Exception("Prerequisites validation failed")
            
            # Step 2: Package Lambda functions
            zip_paths = self.package_lambda_functions()
            
            # Step 3: Update Lambda functions
            function_mappings = {
                'prod-revops-webhook-gateway': zip_paths['webhook_gateway'],
                'revops-webhook': zip_paths['queue_processor'],
                'revops-manager-agent-wrapper': zip_paths['manager_wrapper']
            }
            
            for function_name, zip_path in function_mappings.items():
                self.update_lambda_function(function_name, zip_path)
            
            # Step 4: Cleanup
            for zip_path in zip_paths.values():
                os.remove(zip_path)
            
            print("=== Lambda Function Updates Completed Successfully ===")
            print("\nDeployed Functions:")
            print("  • prod-revops-webhook-gateway (webhook gateway)")
            print("  • revops-webhook (queue processor)")  
            print("  • revops-manager-agent-wrapper (bedrock agent wrapper)")
            print(f"\nWebhook Endpoint: https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook")
            
        except Exception as e:
            print(f"=== Deployment Failed ===")
            print(f"Error: {str(e)}")
            raise

def main():
    """Main deployment entry point"""
    parser = argparse.ArgumentParser(description='Update RevOps AI Webhook Gateway Lambda Functions')
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
    
    try:
        deployer = WebhookGatewayDeployer(args.profile)
        
        if args.validate_only:
            if deployer.validate_prerequisites():
                print("✓ Validation passed - ready for deployment")
                sys.exit(0)
            else:
                print("✗ Validation failed")
                sys.exit(1)
        else:
            deployer.deploy()
            
    except Exception as e:
        print(f"Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()