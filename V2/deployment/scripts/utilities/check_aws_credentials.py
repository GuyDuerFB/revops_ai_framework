#!/usr/bin/env python3
"""
Script to check if AWS credentials are valid
"""

import boto3
import json
import os
import sys

def get_config():
    """Load the config.json file"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def check_aws_credentials():
    """Check if AWS credentials are valid by listing Lambda functions"""
    config = get_config()
    
    # Get profile and region from config
    profile = config.get("profile_name")
    region = config.get("region_name")
    
    print(f"Checking AWS credentials for profile: {profile} in region: {region}")
    
    try:
        # Create session with the profile
        session = boto3.Session(profile_name=profile, region_name=region)
        lambda_client = session.client('lambda')
        
        # List Lambda functions (limited to 5 to keep output manageable)
        response = lambda_client.list_functions(MaxItems=5)
        
        # Print function names that start with 'revops'
        print("\nFound Lambda functions:")
        found_revops = False
        for function in response.get('Functions', []):
            name = function.get('FunctionName')
            if name and name.startswith('revops'):
                print(f"- {name}")
                found_revops = True
        
        if not found_revops:
            print("No 'revops' Lambda functions found in the first 5 results.")
        
        print("\nAWS credentials are valid!")
        return True
    except Exception as e:
        print(f"\nError checking AWS credentials: {str(e)}")
        print("\nPlease refresh your AWS SSO credentials with:")
        print(f"aws sso login --profile {profile}")
        return False

if __name__ == "__main__":
    check_aws_credentials()
