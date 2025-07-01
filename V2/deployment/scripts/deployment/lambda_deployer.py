#!/usr/bin/env python3
"""
RevOps AI Framework V2 - Lambda Deployer

This script deploys Lambda functions defined in the configuration file.
It handles packaging dependencies, creating IAM roles, and deploying the functions.

Special handling is included for the Gong Lambda function which requires specific
source directory path resolution and environment variable configuration.
"""

import os
import json
import shutil
import subprocess
import tempfile
import time
import boto3
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# V2 root directory (one level up from deployment directory)
V2_ROOT = os.path.dirname(PROJECT_ROOT)


def create_lambda_role(role_name: str, trust_policy_file: Optional[str] = None) -> str:
    """
    Create an IAM role for Lambda functions with appropriate policies
    
    Args:
        role_name: Name of the IAM role
        trust_policy_file: Path to trust policy JSON file (optional)
    
    Returns:
        Role ARN
    """
    # Default trust policy for Lambda
    default_trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    # Load custom trust policy if provided
    trust_policy = default_trust_policy
    if trust_policy_file and os.path.exists(trust_policy_file):
        with open(trust_policy_file, 'r') as f:
            trust_policy = json.load(f)
    
    # Create IAM client
    iam = boto3.client('iam')
    
    try:
        # Check if role already exists
        try:
            response = iam.get_role(RoleName=role_name)
            print(f"IAM role {role_name} already exists")
            return response['Role']['Arn']
        except iam.exceptions.NoSuchEntityException:
            # Create the role
            response = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Role for RevOps AI Framework {role_name} Lambda function"
            )
            print(f"Created IAM role {role_name}")
            
            # Attach basic Lambda execution policy
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            print(f"Attached AWSLambdaBasicExecutionRole policy to {role_name}")
            
            # Attach Secrets Manager access policy
            iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/SecretsManagerReadWrite'
            )
            print(f"Attached SecretsManagerReadWrite policy to {role_name}")
            
            # Wait for role to be available
            print("Waiting for IAM role to be available...")
            time.sleep(10)
            
            return response['Role']['Arn']
            
    except ClientError as e:
        print(f"Error creating IAM role: {e}")
        raise


def package_lambda_function(source_dir: str, output_zip: str, install_dependencies: bool = True) -> str:
    """
    Package a Lambda function from source directory into a ZIP file
    
    Args:
        source_dir: Source directory containing Lambda code
        output_zip: Path to output ZIP file
        install_dependencies: Whether to install dependencies from requirements.txt
    
    Returns:
        Path to the created ZIP file
    """
    print(f"Packaging Lambda function from {source_dir}")
    
    # Create a temporary directory for packaging
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy source files to temp directory
        for item in os.listdir(source_dir):
            src = os.path.join(source_dir, item)
            dst = os.path.join(temp_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        # Install dependencies if requirements.txt exists
        requirements_file = os.path.join(source_dir, "requirements.txt")
        if install_dependencies and os.path.exists(requirements_file):
            print("Installing dependencies from requirements.txt")
            subprocess.check_call([
                "pip", "install", 
                "-r", requirements_file,
                "-t", temp_dir
            ])
        
        # Create the ZIP file
        shutil.make_archive(output_zip.replace('.zip', ''), 'zip', temp_dir)
        
    print(f"Lambda package created: {output_zip}")
    return output_zip


def wait_for_lambda_ready(function_name, max_attempts=30, delay=5):
    """
    Wait for a Lambda function to become ready for configuration updates
    
    Args:
        function_name: Name of the Lambda function
        max_attempts: Maximum number of attempts before giving up
        delay: Delay in seconds between attempts
    """
    lambda_client = boto3.client('lambda')
    
    print(f"Waiting for Lambda function {function_name} to be ready (up to {max_attempts*delay} seconds)...")
    for attempt in range(max_attempts):
        try:
            # First wait before trying, since we know there's an update in progress
            if attempt > 0:
                print(f"Attempt {attempt+1}/{max_attempts}...")
            time.sleep(delay)
            
            # Try to update the configuration with the same configuration
            # This will fail with ResourceConflictException if the function is still updating
            current_config = lambda_client.get_function_configuration(FunctionName=function_name)
            # Try a minor configuration update
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Description=current_config.get('Description', '')
            )
            # If we get here, the function is ready
            print(f"Lambda function {function_name} is now ready for configuration updates.")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                # Still updating, continue waiting
                continue
            else:
                # If any other error occurs, raise it
                raise
    
    print(f"WARNING: Lambda function {function_name} is still not ready after {max_attempts} attempts ({max_attempts*delay} seconds).")
    return False


def deploy_lambda_function(lambda_config: Dict[str, Any], role_arn: str) -> Dict[str, Any]:
    """
    Deploy a Lambda function to AWS
    
    Args:
        lambda_config: Lambda function configuration
        role_arn: IAM role ARN
    
    Returns:
        Lambda function information including ARN
    """
    function_name = lambda_config["function_name"]
    source_dir = lambda_config["source_dir"]
    handler = lambda_config["handler"]
    runtime = lambda_config["runtime"]
    timeout = lambda_config.get("timeout", 30)
    memory_size = lambda_config.get("memory_size", 128)
    env_vars = lambda_config.get("environment_variables", {})
    layers = lambda_config.get("layers", [])
    
    # Resolve source directory path
    if not os.path.isabs(source_dir):
        source_dir = os.path.join(PROJECT_ROOT, source_dir)
    
    # Create temp zip file
    zip_file = os.path.join(tempfile.gettempdir(), f"{function_name}.zip")
    package_lambda_function(source_dir, zip_file)
    
    # Read zip file
    with open(zip_file, 'rb') as f:
        zip_content = f.read()
    
    # Create Lambda client
    lambda_client = boto3.client('lambda')
    
    try:
        # Check if function already exists
        try:
            lambda_client.get_function(FunctionName=function_name)
            print(f"Lambda function {function_name} already exists. Updating...")
            
            # Update function code
            try:
                lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content,
                    Publish=True
                )
                print(f"Updated code for Lambda function {function_name}")
            except ClientError as e:
                print(f"Error updating Lambda function code: {e}")
                raise
            
            # Wait for the function to be ready for configuration updates
            if wait_for_lambda_ready(function_name):
                try:
                    # Update function configuration
                    response = lambda_client.update_function_configuration(
                        FunctionName=function_name,
                        Role=role_arn,
                        Handler=handler,
                        Runtime=runtime,  # Add runtime parameter for updates
                        Timeout=timeout,
                        MemorySize=memory_size,
                        Environment={
                            'Variables': env_vars
                        },
                        Layers=layers
                    )
                    print(f"Updated configuration for Lambda function {function_name}")
                except ClientError as e:
                    print(f"Error updating Lambda function configuration: {e}")
                    raise
            else:
                print(f"Warning: Timed out waiting for {function_name} to be ready for configuration updates. Skipping configuration update.")
                # Get the current function info to return
                response = lambda_client.get_function(FunctionName=function_name)['Configuration']
            
        except lambda_client.exceptions.ResourceNotFoundException:
            # Create new function
            print(f"Creating new Lambda function {function_name}...")
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime=runtime,
                Role=role_arn,
                Handler=handler,
                Code={
                    'ZipFile': zip_content
                },
                Timeout=timeout,
                MemorySize=memory_size,
                Environment={
                    'Variables': env_vars
                },
                Layers=layers
            )
        
        function_arn = response['FunctionArn']
        print(f"Lambda function deployed: {function_name} (ARN: {function_arn})")
        
        # Add permission for Bedrock to invoke the function
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId='AllowBedrockInvoke',
                Action='lambda:InvokeFunction',
                Principal='bedrock.amazonaws.com'
            )
            print(f"Added permission for Bedrock to invoke {function_name}")
        except lambda_client.exceptions.ResourceConflictException:
            # Permission already exists
            print(f"Bedrock invoke permission already exists for {function_name}")
        
        return {"function_name": function_name, "function_arn": function_arn}
        
    except ClientError as e:
        print(f"Error deploying Lambda function: {e}")
        raise


def deploy_gong_lambda(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Special function to deploy only the Gong retrieval Lambda function
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Updated configuration with ARNs
    """
    # Get AWS credentials
    region = config["region_name"]
    profile = config["profile_name"]
    
    print(f"\nDeploying Gong Lambda function with profile: {profile} and region: {region}")
    
    # Use AWS CLI directly to handle expired tokens better
    os.environ["AWS_PROFILE"] = profile
    os.environ["AWS_REGION"] = region
    
    lambda_name = "gong_retrieval"
    lambda_config = config["lambda_functions"][lambda_name]
    
    print(f"Deploying Gong Lambda function: {lambda_config['function_name']}")
    
    # Fix source_dir path to be relative to project root, not deployment directory
    source_dir = os.path.join(V2_ROOT, lambda_config["source_dir"])
    lambda_config["source_dir"] = source_dir
    print(f"Using source directory: {source_dir}")
    
    # Create or get IAM role
    role_name = f"revops-{lambda_name}-lambda-role"
    role_arn = lambda_config.get("iam_role")
    if not role_arn:
        print(f"Creating IAM role: {role_name}")
        role_arn = create_lambda_role(role_name)
        lambda_config["iam_role"] = role_arn
    
    # Deploy the Lambda function
    result = deploy_lambda_function(lambda_config, role_arn)
    
    # Debug the result
    print("Lambda deployment result:")
    print(result)
    
    # Get the function ARN - extract from the result if available or query it if necessary
    function_arn = None
    if isinstance(result, dict) and "FunctionArn" in result:
        function_arn = result["FunctionArn"]
    elif isinstance(result, dict) and "function_name" in result:
        # If we have the function name but not the ARN, query it
        function_name = result.get("function_name") or lambda_config["function_name"]
        print(f"Querying ARN for function: {function_name}")
        try:
            session = boto3.Session(profile_name=config["profile_name"], region_name=config["region_name"])
            lambda_client = session.client('lambda')
            response = lambda_client.get_function(FunctionName=function_name)
            function_arn = response["Configuration"]["FunctionArn"]
        except Exception as e:
            print(f"Error getting Lambda ARN: {str(e)}")
    
    if not function_arn:
        function_arn = f"arn:aws:lambda:{config['region_name']}:740202120544:function:{lambda_config['function_name']}"
        print(f"Using constructed ARN: {function_arn}")
    
    # Update config with ARN
    config["lambda_functions"][lambda_name]["lambda_arn"] = function_arn
    
    # Also update action group ARN if it exists
    for agent_type in ["data_agent", "decision_agent", "execution_agent"]:
        if agent_type in config:
            for action_group in config[agent_type].get("action_groups", []):
                if action_group.get("name") == lambda_name:
                    action_group["lambda_arn"] = function_arn
    
    print(f"Gong Lambda function deployed successfully: {function_arn}")
    return config


def deploy_lambda_functions(config: Dict[str, Any], secrets: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deploy all Lambda functions defined in the configuration
    
    Args:
        config: Configuration dictionary
        secrets: Secrets dictionary
    
    Returns:
        Updated configuration with ARNs
    """
    print("\nDeploying Lambda functions...")
    
    lambda_functions = config.get("lambda_functions", {})
    
    for lambda_name, lambda_config in lambda_functions.items():
        print(f"\nProcessing Lambda function: {lambda_name}")
        
        # Skip if marked to skip
        if lambda_config.get("skip_deployment", False):
            print(f"Skipping deployment of {lambda_name} as requested in config")
            continue
            
        # Special handling for Gong Lambda
        if lambda_name == "gong_retrieval":
            print("Using specialized Gong Lambda deployment logic")
            # Deploy Gong Lambda with special handling and update the config
            config = deploy_gong_lambda(config)
            continue
        
        # Create or get IAM role
        role_name = f"revops-{lambda_name}-lambda-role"
        role_arn = lambda_config.get("iam_role")
        if not role_arn:
            print(f"Creating IAM role: {role_name}")
            role_arn = create_lambda_role(role_name)
            lambda_config["iam_role"] = role_arn
        
        # Deploy the Lambda function
        result = deploy_lambda_function(lambda_config, role_arn)
        
        # Get the function ARN
        if isinstance(result, dict) and "FunctionArn" in result:
            function_arn = result["FunctionArn"]
            lambda_config["lambda_arn"] = function_arn
            
            # Also update action group ARN if it exists
            for agent_type in ["data_agent", "decision_agent", "execution_agent"]:
                if agent_type in config:
                    for action_group in config[agent_type].get("action_groups", []):
                        if action_group.get("name") == lambda_name:
                            action_group["lambda_arn"] = function_arn
    
    return {"config": config}


def delete_lambda_function(function_name, region_name=None):
    """
    Delete a Lambda function
    
    Args:
        function_name: Name of the Lambda function to delete
        region_name: AWS region name
        
    Returns:
        True if deleted successfully, False if function doesn't exist
    """
    lambda_client = boto3.client('lambda', region_name=region_name) if region_name else boto3.client('lambda')
    
    try:
        print(f"Deleting Lambda function {function_name}...")
        lambda_client.delete_function(FunctionName=function_name)
        print(f"Successfully deleted Lambda function {function_name}")
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Lambda function {function_name} doesn't exist, nothing to delete")
        return False
    except ClientError as e:
        print(f"Error deleting Lambda function {function_name}: {e}")
        raise


def test_lambda_function(lambda_name: str, lambda_config: Dict[str, Any]) -> None:
    """
    Test a Lambda function by invoking it with test data
    
    Args:
        lambda_name: Name of the Lambda function
        lambda_config: Lambda function configuration
    """
    function_name = lambda_config["function_name"]
    
    # Create Lambda client
    lambda_client = boto3.client('lambda')
    
    # Create test payload based on Lambda function
    test_payload = {}
    
    if lambda_name == "firebolt_query":
        # Exact test payload format from the working Lambda example
        test_payload = {
            "query": "select 1"
        }
    elif lambda_name == "gong_retrieval":
        # Test payload for gong_retrieval with proper structure
        test_payload = {
            "parameters": {
                "call_id": "test-call-id",
                "data_type": "call_metadata",
                "limit": 1
            },
            "secret_name": "gong-credentials" # Explicitly provide the secret name
        }
    elif lambda_name == "webhook":
        # Test payload for webhook
        test_payload = {
            "method": "POST",
            "webhook_url": "https://hooks.zapier.com/hooks/catch/16566961/uy6pi1l/",
            "payload": {"message": "Test message from RevOps AI Framework", "source": "Lambda test"}
        }
    elif lambda_name == "firebolt_metadata":
        # Test payload for firebolt_metadata with required operation
        test_payload = {
            "operation": "list_tables",
            "database": "dwh_prod"
            # No need for other parameters as they're provided via environment variables
        }
    elif lambda_name == "firebolt_writer":
        # Test payload for firebolt_writer with expected format
        import uuid
        from datetime import datetime
        # json is already imported at the top level
        test_payload = {
            "operation": "insert",  
            "table": "revops_ai_insights",  
            "data": {
                "insight_id": str(uuid.uuid4()),
                "correlation_id": str(uuid.uuid4()),
                "insight_category": "deal_quality",
                "insight_type": "technical_fit",
                "source_agent": "lambda_test",
                "insight_title": "Test Insight",
                "insight_description": "This is a test insight from the Lambda deployer",
                "insight_details": json.dumps({"test": True, "timestamp": datetime.now().isoformat()}),
                "timestamp": datetime.now().isoformat(),
                "status": "new"
            }
        }
    
    # Invoke Lambda function
    try:
        print(f"Invoking Lambda function: {function_name}")
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload).encode()
        )
        
        # Process response
        if response['StatusCode'] == 200:
            payload = json.loads(response['Payload'].read().decode())
            print(f"Lambda function {function_name} invocation successful")
            print(f"Response: {json.dumps(payload, indent=2)}")
        else:
            print(f"Lambda function {function_name} invocation failed with status: {response['StatusCode']}")
            
    except ClientError as e:
        print(f"Error invoking Lambda function {function_name}: {e}")


if __name__ == "__main__":
    # This script is not meant to be run directly
    print("This script is meant to be imported by deploy.py")
    print("To deploy the Gong Lambda function, use: python deploy.py --deploy lambda --lambda_name gong_retrieval")
