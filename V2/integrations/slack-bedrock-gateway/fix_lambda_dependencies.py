#!/usr/bin/env python3
"""
Fix Lambda dependencies by creating proper deployment packages with installed requirements
"""
import os
import sys
import tempfile
import zipfile
import subprocess
import shutil
from pathlib import Path
import boto3

# Configuration
AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"
PROJECT_NAME = "revops-slack-bedrock"

def install_dependencies(lambda_dir, temp_dir):
    """Install Python dependencies to temporary directory"""
    requirements_file = lambda_dir / 'requirements.txt'
    
    if not requirements_file.exists():
        print(f"⚠️  No requirements.txt found in {lambda_dir}")
        return False
    
    print(f"📦 Installing dependencies from {requirements_file}")
    
    try:
        # Install dependencies to temp directory
        subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            '-r', str(requirements_file),
            '-t', temp_dir,
            '--no-deps',  # Don't install transitive dependencies
            '--quiet'
        ], check=True)
        
        # Also install main dependencies
        subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            'requests>=2.28.0',
            'boto3>=1.26.0',
            '-t', temp_dir,
            '--quiet'
        ], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_deployment_package(lambda_dir, function_name):
    """Create a proper deployment package with dependencies"""
    print(f"🔧 Creating deployment package for {function_name}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Install dependencies
        if not install_dependencies(lambda_dir, temp_dir):
            return None
        
        # Copy Lambda function files
        for py_file in lambda_dir.glob('*.py'):
            shutil.copy2(py_file, temp_dir)
        
        # Create zip file
        package_path = f"/tmp/{function_name}.zip"
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zip_file.write(file_path, arcname)
        
        print(f"✅ Package created: {package_path}")
        return package_path

def update_lambda_function(function_name, package_path):
    """Update Lambda function with new deployment package"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        
        print(f"🔄 Updating {function_name} Lambda function...")
        
        with open(package_path, 'rb') as f:
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=f.read()
            )
        
        print(f"✅ {function_name} updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {function_name}: {e}")
        return False

def update_lambda_permissions():
    """Update Lambda execution role permissions for Bedrock access"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        iam_client = session.client('iam', region_name=AWS_REGION)
        
        # Get the processor Lambda execution role
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        response = lambda_client.get_function(FunctionName=f"{PROJECT_NAME}-processor")
        role_arn = response['Configuration']['Role']
        role_name = role_arn.split('/')[-1]
        
        print(f"🔐 Updating permissions for role: {role_name}")
        
        # Bedrock access policy
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeAgent",
                        "bedrock:RetrieveAndGenerate",
                        "bedrock:Retrieve"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        # Create or update the policy
        policy_name = "BedrockAgentAccess"
        policy_arn = f"arn:aws:iam::740202120544:policy/{policy_name}"
        
        try:
            # Try to create the policy
            iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(bedrock_policy),
                Description="Allow Lambda to invoke Bedrock agents"
            )
            print(f"✅ Created policy: {policy_name}")
        except iam_client.exceptions.EntityAlreadyExistsException:
            # Policy exists, update it
            iam_client.create_policy_version(
                PolicyArn=policy_arn,
                PolicyDocument=json.dumps(bedrock_policy),
                SetAsDefault=True
            )
            print(f"✅ Updated policy: {policy_name}")
        
        # Attach policy to role
        try:
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"✅ Attached Bedrock policy to role: {role_name}")
        except iam_client.exceptions.LimitExceededException:
            print(f"ℹ️  Policy already attached to role: {role_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating Lambda permissions: {e}")
        return False

def main():
    """Main function to fix Lambda dependencies and permissions"""
    print("🔧 Fixing Slack Lambda Dependencies and Permissions")
    print("=" * 60)
    
    script_dir = Path(__file__).parent
    
    # Update Handler Lambda
    handler_dir = script_dir / 'lambdas' / 'handler'
    handler_package = create_deployment_package(handler_dir, f"{PROJECT_NAME}-handler")
    
    if handler_package:
        if update_lambda_function(f"{PROJECT_NAME}-handler", handler_package):
            os.remove(handler_package)
        else:
            print("❌ Failed to update handler Lambda")
            return False
    else:
        print("❌ Failed to create handler package")
        return False
    
    # Update Processor Lambda
    processor_dir = script_dir / 'lambdas' / 'processor'
    processor_package = create_deployment_package(processor_dir, f"{PROJECT_NAME}-processor")
    
    if processor_package:
        if update_lambda_function(f"{PROJECT_NAME}-processor", processor_package):
            os.remove(processor_package)
        else:
            print("❌ Failed to update processor Lambda")
            return False
    else:
        print("❌ Failed to create processor package")
        return False
    
    # Update Lambda permissions
    if not update_lambda_permissions():
        print("❌ Failed to update Lambda permissions")
        return False
    
    print("\n🎉 Lambda functions fixed successfully!")
    print("✅ Dependencies installed")
    print("✅ Bedrock permissions added")
    print("\n🧪 Run test_integration.py to verify the fixes")
    
    return True

if __name__ == "__main__":
    import json
    success = main()
    sys.exit(0 if success else 1)