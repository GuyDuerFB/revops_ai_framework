#!/usr/bin/env python3
import boto3
import json
import os

# AWS Profile to use
AWS_PROFILE = "FireboltSystemAdministrator-740202120544"

# Environment variables for Firebolt Lambda functions using values from the working example
FIREBOLT_ENV_VARS = {
    "FIREBOLT_ACCOUNT_NAME": "firebolt-dwh",        # From working Lambda
    "FIREBOLT_ENGINE_NAME": "dwh_prod_analytics",  # From working Lambda
    "FIREBOLT_DATABASE": "dwh_prod",              # From working Lambda
    "FIREBOLT_API_REGION": "us-east-1",           # Default API region
    "FIREBOLT_CREDENTIALS_SECRET": "firebolt-credentials"  # Name of the secret we created
}

# Lambda function names
FIREBOLT_LAMBDA_FUNCTIONS = [
    "revops-firebolt-query",
    "revops-firebolt-metadata",
    "revops-firebolt-writer"
]

# Set up the AWS session with the profile
session = boto3.Session(profile_name=AWS_PROFILE)
lambda_client = session.client('lambda')

# Update Lambda environment variables
for function_name in FIREBOLT_LAMBDA_FUNCTIONS:
    print(f"Updating environment variables for {function_name}...")
    try:
        # Get current configuration
        response = lambda_client.get_function_configuration(
            FunctionName=function_name
        )
        
        # Extract current environment variables or initialize empty dict
        current_vars = response.get('Environment', {}).get('Variables', {})
        
        # Update with new environment variables
        updated_vars = {**current_vars, **FIREBOLT_ENV_VARS}
        
        # Update Lambda configuration
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': updated_vars
            }
        )
        print(f"Successfully updated environment variables for {function_name}")
    except Exception as e:
        print(f"Error updating {function_name}: {e}")

print("Environment variable update completed!")
