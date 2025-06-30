#!/usr/bin/env python3
"""
Simple script to test Lambda functions directly using boto3
"""

import boto3
import json
import uuid
from datetime import datetime

# Create a boto3 session with the proper profile
session = boto3.Session(profile_name='FireboltSystemAdministrator-740202120544', region_name='us-east-1')

# Initialize Lambda client from the session
lambda_client = session.client('lambda')

def test_lambda(function_name, payload):
    """Test a Lambda function with the given payload"""
    print(f"Testing {function_name}...")
    print(f"Payload: {json.dumps(payload, default=str)}", flush=True)
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode()
        )
        
        # Read and parse the response
        response_payload = response['Payload'].read().decode()
        print(f"Raw response: {response_payload}", flush=True)
        
        # Save response to file for inspection
        with open(f"{function_name}_response.json", 'w') as f:
            f.write(response_payload)
            
        print(f"Response saved to {function_name}_response.json", flush=True)
        
        try:
            parsed_response = json.loads(response_payload)
            print(f"Parsed response: {json.dumps(parsed_response, indent=2)}", flush=True)
            return parsed_response
        except json.JSONDecodeError:
            print(f"Could not parse response as JSON: {response_payload}", flush=True)
            return response_payload
    except Exception as e:
        print(f"Error invoking Lambda {function_name}: {str(e)}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)
        return {"error": str(e)}

# Test the Firebolt query Lambda
print("\n=== Testing firebolt_query ===")
query_response = test_lambda(
    "revops-firebolt-query", 
    {"query": "SELECT 1"}
)

# Test the Firebolt metadata Lambda with a direct SQL query
print("\n=== Testing firebolt_metadata ===")
metadata_response = test_lambda(
    "revops-firebolt-metadata", 
    {"query": "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' LIMIT 10"}
)

# Test the Firebolt writer Lambda with direct SQL INSERT
print("\n=== Testing firebolt_writer ===")
sql_insert = """
INSERT INTO revops_ai_insights (
    insight_id,
    correlation_id,
    insight_category,
    insight_type,
    source_agent,
    insight_title,
    insight_description,
    status
) VALUES (
    'insight_test_' || GEN_RANDOM_UUID_TEXT(),
    'corr_test_' || GEN_RANDOM_UUID_TEXT(),
    'deal_quality',
    'technical_fit',
    'lambda_test',
    'Test SQL Insert',
    'This is a test insight using direct SQL insert',
    'new'
)"""

writer_response = test_lambda(
    "revops-firebolt-writer", 
    {"query": sql_insert}
)
