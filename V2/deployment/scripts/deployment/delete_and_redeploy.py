#!/usr/bin/env python3
"""
Delete and redeploy Lambda functions for the RevOps AI Framework

This script first deletes existing Lambda functions and then redeploys them
to avoid conflicts during the update process.
"""

import json
import os
from lambda_deployer import delete_lambda_function

def load_config_file(file_path):
    """Load configuration from a JSON file"""
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    """Main entry point for the script."""
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = load_config_file(config_path)
    
    print("=== Deleting existing Lambda functions ===")
    # Get region and profile from config
    region_name = config.get("region_name")
    profile_name = config.get("profile_name")
    
    print(f"Using AWS region: {region_name} and profile: {profile_name}")
    
    # Set environment variable for AWS profile
    if profile_name:
        os.environ['AWS_PROFILE'] = profile_name
    
    # Delete existing Lambda functions
    for lambda_name, lambda_config in config.get("lambda_functions", {}).items():
        function_name = lambda_config.get("function_name")
        if function_name:
            # Pass region name to delete_lambda_function
            delete_lambda_function(function_name, region_name)
            
            # Remove the function_arn from config if it exists
            if "function_arn" in lambda_config:
                del lambda_config["function_arn"]
                
            # Remove the iam_role from config if it's not null
            if lambda_config.get("iam_role"):
                lambda_config["iam_role"] = None
    
    # Save the updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n=== Now run the deployment script to redeploy all Lambda functions ===")
    print("Run: python deploy.py --deploy lambda")

if __name__ == "__main__":
    main()
