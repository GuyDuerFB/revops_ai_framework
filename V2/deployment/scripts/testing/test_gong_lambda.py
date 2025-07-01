#!/usr/bin/env python3
"""
Test script for the Gong Lambda function.
This script invokes the Lambda function to retrieve a call transcript from Gong.
"""

import boto3
import json
import os
import sys
import time
from datetime import datetime, timedelta

# Add parent directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_config():
    """Load the deployment configuration from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.json")
    with open(config_path, 'r') as f:
        return json.load(f)

def test_gong_lambda():
    """Test the Gong Lambda function by retrieving a call transcript"""
    # Load config to get AWS credentials and Lambda ARN
    config = load_config()
    
    # Get profile and region from config
    profile = config["profile_name"]
    region = config["region_name"]
    
    # Get Lambda ARN from config
    lambda_name = "gong_retrieval"
    lambda_arn = config["lambda_functions"][lambda_name].get("lambda_arn")
    function_name = config["lambda_functions"][lambda_name].get("function_name")
    
    if not lambda_arn:
        print(f"Lambda ARN not found in config for {lambda_name}")
        # Try to construct it from function name
        if function_name:
            lambda_arn = f"arn:aws:lambda:{region}:740202120544:function:{function_name}"
            print(f"Using constructed ARN: {lambda_arn}")
        else:
            print("Error: Could not find Lambda function ARN or name")
            return
    
    print(f"Testing Gong Lambda function: {function_name}")
    
    # Create AWS session with the profile
    session = boto3.Session(profile_name=profile, region_name=region)
    lambda_client = session.client('lambda')
    
    # Create payload for Lambda - get calls from the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    payload = {
        "query_type": "calls",
        "date_range": {
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d")
        },
        "filters": {
            "limit": 1  # Limit to 1 call for testing
        }
    }
    
    # Use direct Lambda invocation format (not Bedrock agent format)
    # This matches the 'elif "query_type" in event:' branch in the Lambda handler
    
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Invoke Lambda function with direct invocation format
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',  # Synchronous invocation
            Payload=json.dumps(payload)
        )
        
        # Read response payload
        response_payload = json.loads(response['Payload'].read().decode('utf-8'))
        
        # Check for errors
        if 'errorMessage' in response_payload:
            print(f"Error from Lambda: {response_payload['errorMessage']}")
            if 'stackTrace' in response_payload:
                print("Stack trace:")
                for line in response_payload['stackTrace']:
                    print(f"  {line}")
            return
        
        # Parse response content
        if isinstance(response_payload, str):
            response_content = json.loads(response_payload)
        else:
            response_content = response_payload
            
        # Check for Bedrock agent response format
        if 'content' in response_content:
            response_content = json.loads(response_content['content'])
            
        # Print call details
        print("\nGong Call Details:")
        print(json.dumps(response_content, indent=2))
        
        # If calls were found, try to get transcript for the first call
        if response_content and 'calls' in response_content and response_content['calls']:
            call = response_content['calls'][0]
            call_id = call.get('id')
            
            if call_id:
                print(f"\nRetrieving transcript for call ID: {call_id}")
                
                # Create payload for transcript retrieval
                transcript_payload = {
                    "query_type": "transcript",
                    "call_id": call_id
                }
                
                # Use direct Lambda invocation format for transcript retrieval
                
                # Invoke Lambda function for transcript
                transcript_response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(transcript_payload)
                )
                
                # Read transcript response payload
                transcript_payload = json.loads(transcript_response['Payload'].read().decode('utf-8'))
                
                # Parse response content
                if isinstance(transcript_payload, str):
                    transcript_content = json.loads(transcript_payload)
                else:
                    transcript_content = transcript_payload
                    
                # Check for Bedrock agent response format
                if 'content' in transcript_content:
                    transcript_content = json.loads(transcript_content['content'])
                
                print("\nCall Transcript:")
                print(json.dumps(transcript_content, indent=2))
            else:
                print("No call ID found in response")
        else:
            print("No calls found in the response")
            
    except Exception as e:
        print(f"Error invoking Lambda: {str(e)}")

if __name__ == "__main__":
    test_gong_lambda()
