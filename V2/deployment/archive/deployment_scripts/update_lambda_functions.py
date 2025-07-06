#!/usr/bin/env python3
"""
Lambda Function Update Script for RevOps AI Framework V2

This script updates Lambda functions with the latest code changes,
including enhanced logging and Bedrock Agent compatibility fixes.
"""

import boto3
import zipfile
import os
import json
from pathlib import Path

# Configuration
REGION = 'us-east-1'
PROFILE = 'FireboltSystemAdministrator-740202120544'

# Lambda function configurations
LAMBDA_FUNCTIONS = {
    'revops-web-search': {
        'source_dir': '../tools/web_search',
        'files': ['lambda_function.py'],
        'description': 'Web search Lambda with enhanced logging and Bedrock compatibility'
    },
    'revops-firebolt-query': {
        'source_dir': '../tools/firebolt/query_lambda',
        'files': ['lambda_function.py', 'requirements.txt'],
        'description': 'Firebolt query Lambda function'
    },
    'revops-firebolt-writer': {
        'source_dir': '../tools/firebolt/writer_lambda',
        'files': ['lambda_function.py', 'requirements.txt'],
        'description': 'Firebolt writer Lambda function'
    },
    'revops-gong-retrieval': {
        'source_dir': '../tools/gong/retrieval_lambda',
        'files': ['lambda_function.py', 'requirements.txt'],
        'description': 'Gong retrieval Lambda function'
    },
    'revops-webhook': {
        'source_dir': '../tools/webhook',
        'files': ['lambda_function.py'],
        'description': 'Webhook notification Lambda function'
    }
}

def create_lambda_package(source_dir, files, function_name):
    """Create a ZIP package for Lambda function"""
    package_path = f"/tmp/{function_name}_package.zip"
    source_path = Path(__file__).parent / source_dir
    
    print(f"Creating package for {function_name} from {source_path}")
    
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_name in files:
            file_path = source_path / file_name
            if file_path.exists():
                zipf.write(file_path, file_name)
                print(f"  Added {file_name}")
            else:
                print(f"  Warning: {file_name} not found in {source_path}")
    
    return package_path

def update_lambda_function(lambda_client, function_name, package_path, description):
    """Update Lambda function code"""
    try:
        print(f"Updating {function_name}...")
        
        with open(package_path, 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_file.read()
            )
        
        # Update description if provided
        if description:
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Description=description
            )
        
        print(f"✅ Successfully updated {function_name}")
        print(f"   Version: {response['Version']}")
        print(f"   Last Modified: {response['LastModified']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {function_name}: {str(e)}")
        return False

def main():
    """Main function to update all Lambda functions"""
    print("🚀 Starting Lambda function updates...")
    
    # Initialize AWS clients
    session = boto3.Session(profile_name=PROFILE)
    lambda_client = session.client('lambda', region_name=REGION)
    
    success_count = 0
    total_count = len(LAMBDA_FUNCTIONS)
    
    for function_name, config in LAMBDA_FUNCTIONS.items():
        print(f"\n📦 Processing {function_name}...")
        
        # Create package
        package_path = create_lambda_package(
            config['source_dir'],
            config['files'],
            function_name
        )
        
        if os.path.exists(package_path):
            # Update function
            if update_lambda_function(
                lambda_client,
                function_name,
                package_path,
                config['description']
            ):
                success_count += 1
            
            # Clean up package
            os.remove(package_path)
        else:
            print(f"❌ Failed to create package for {function_name}")
    
    print(f"\n🎯 Update Summary:")
    print(f"   Successfully updated: {success_count}/{total_count} functions")
    
    if success_count == total_count:
        print("✅ All Lambda functions updated successfully!")
        
        # Update deployment status
        try:
            config_path = Path(__file__).parent / 'config.json'
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            config['deployment_status']['last_lambda_update'] = '2025-07-03'
            config['deployment_status']['lambda_update_status'] = 'completed'
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ Updated deployment configuration")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not update config.json: {str(e)}")
    else:
        print("⚠️  Some Lambda functions failed to update. Check the logs above.")

if __name__ == "__main__":
    main()