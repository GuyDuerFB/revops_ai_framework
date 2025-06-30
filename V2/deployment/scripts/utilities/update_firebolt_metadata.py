import os
import json
import time
import boto3
import shutil
import tempfile
import subprocess
import sys
from pathlib import Path

def load_config():
    """Load configuration from config.json file."""
    with open('config.json', 'r') as f:
        return json.load(f)

def load_secrets():
    """Load secrets from secrets.json file."""
    with open('secrets.json', 'r') as f:
        return json.load(f)

def setup_aws_env(config, secrets):
    """Set up AWS environment variables."""
    os.environ['AWS_REGION'] = config.get('region', 'us-east-1')
    os.environ['AWS_PROFILE'] = secrets.get('aws_profile', 'FireboltSystemAdministrator-740202120544')
    print(f"Set AWS_REGION={os.environ['AWS_REGION']} and AWS_PROFILE={os.environ['AWS_PROFILE']}")

def create_lambda_package(source_dir, include_reqs=True, deps_dir=None):
    """Create a Lambda deployment package."""
    print(f"Packaging Lambda function from {source_dir}")
    
    # Create a temporary directory for the package
    tmp_dir = tempfile.mkdtemp()
    
    try:
        # Copy the source code to the temporary directory
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(tmp_dir, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)
        
        # If requirements.txt exists and include_reqs is True, install dependencies
        req_file = os.path.join(source_dir, 'requirements.txt')
        if os.path.exists(req_file) and include_reqs:
            print("Installing dependencies from requirements.txt")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 
                                 '-r', req_file, '--target', tmp_dir])
        
        # If deps_dir is provided, copy its contents to the package
        if deps_dir and os.path.exists(deps_dir):
            for item in os.listdir(deps_dir):
                s = os.path.join(deps_dir, item)
                d = os.path.join(tmp_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
                    
        # Create a zip file from the temporary directory
        output_file = tempfile.mktemp(suffix='.zip')
        shutil.make_archive(output_file[:-4], 'zip', tmp_dir)
        
        print(f"Lambda package created: {output_file}")
        return output_file
    
    finally:
        # Clean up the temporary directory
        shutil.rmtree(tmp_dir)

def update_lambda_function(config, lambda_name):
    """Update a specific Lambda function."""
    lambda_config = config["lambda_functions"].get(lambda_name)
    
    if not lambda_config:
        print(f"Lambda function {lambda_name} not found in configuration.")
        return False
    
    lambda_client = boto3.client('lambda')
    function_name = lambda_config.get("function_name", f"revops-{lambda_name}")
    
    # Create the Lambda package
    source_dir = lambda_config.get("source_dir", "")
    if not source_dir:
        print(f"Source directory not specified for {lambda_name}.")
        return False
    
    package_file = create_lambda_package(source_dir, include_reqs=True)
    
    # Update the Lambda function code
    with open(package_file, 'rb') as f:
        function_zip = f.read()
    
    try:
        print(f"Updating Lambda function {function_name}...")
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=function_zip,
            Publish=True
        )
        print(f"Updated code for Lambda function {function_name}")
        
        # Wait for function to be active
        print(f"Waiting for Lambda function {function_name} to be ready...")
        for i in range(30):  # Try for up to 150 seconds (5 seconds * 30 attempts)
            time.sleep(5)
            function_info = lambda_client.get_function(FunctionName=function_name)
            state = function_info['Configuration']['State']
            last_update_status = function_info['Configuration'].get('LastUpdateStatus')
            
            if state == 'Active' and last_update_status in ['Successful', None]:
                print(f"Lambda function {function_name} is now active and ready.")
                return True
            
            print(f"Lambda state: {state}, update status: {last_update_status}. Waiting...")
        
        print(f"Timeout waiting for Lambda function {function_name} to be ready.")
        return False
        
    except Exception as e:
        print(f"Error updating Lambda function: {str(e)}")
        return False
    finally:
        # Clean up temporary zip file
        if os.path.exists(package_file):
            os.remove(package_file)

def main():
    """Main function to update the firebolt_metadata Lambda function."""
    print("=== Updating Firebolt Metadata Lambda ===")
    
    # Base directory path
    base_dir = Path('/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V2')
    
    # Load configuration and secrets
    config = load_config()
    secrets = load_secrets()
    
    # Fix the source directory path for firebolt_metadata
    metadata_lambda_path = str(base_dir / 'tools' / 'firebolt' / 'metadata_lambda')
    config['lambda_functions']['firebolt_metadata']['source_dir'] = metadata_lambda_path
    print(f"Using source directory: {metadata_lambda_path}")
    
    # Set up AWS environment
    setup_aws_env(config, secrets)
    
    # Update the firebolt_metadata Lambda function
    result = update_lambda_function(config, "firebolt_metadata")
    
    if result:
        print("Successfully updated firebolt_metadata Lambda function!")
    else:
        print("Failed to update firebolt_metadata Lambda function.")

if __name__ == "__main__":
    main()
