import json
import boto3
import os
from pathlib import Path

# Load config and secrets
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def load_secrets():
    with open('secrets.json', 'r') as f:
        return json.load(f)

# Set up AWS environment
def setup_aws_env(config, secrets):
    os.environ['AWS_REGION'] = config.get('region', 'us-east-1')
    os.environ['AWS_PROFILE'] = secrets.get('aws_profile', 'FireboltSystemAdministrator-740202120544')
    print(f"Set AWS_REGION={os.environ['AWS_REGION']} and AWS_PROFILE={os.environ['AWS_PROFILE']}")

# Test the firebolt_writer lambda with a valid query
def test_firebolt_writer():
    # Load config and secrets
    config = load_config()
    secrets = load_secrets()
    
    # Set up AWS environment
    setup_aws_env(config, secrets)
    
    # Get Lambda function name
    lambda_functions = config.get('lambda_functions', {})
    writer_lambda = lambda_functions.get('firebolt_writer', {})
    function_name = writer_lambda.get('function_name', 'revops-firebolt-writer')
    
    # Create Lambda client
    lambda_client = boto3.client('lambda')
    
    # Test payload with a simplified but valid query
    payload = {
        "query": """
INSERT INTO revops_ai_insights (
    insight_id,
    lead_id,
    sf_account_id,
    sf_opportunity_id,
    customer_id, 
    contact_id,
    insight_category,
    insight_type,
    insight_subtype,
    source_agent,
    workflow_name,
    workflow_execution_id,
    priority_level,
    status,
    assigned_to,
    insight_title,
    insight_description,
    insight_payload,
    evidence_data,
    confidence_score,
    impact_score,
    urgency_score,
    created_at,
    event_timestamp,
    expires_at,
    acknowledged_at,
    resolved_at,
    tags,
    source_system,
    geographic_region,
    customer_segment,
    deal_amount,
    customer_arr,
    usage_metric_value,
    recommended_actions,
    actions_taken,
    outcome_status,
    outcome_notes,
    data_version,
    source_query_hash,
    last_updated_at
) VALUES (
    'insight_test_' || GEN_RANDOM_UUID_TEXT(),
    'lead_test_' || GEN_RANDOM_UUID_TEXT(),
    '0013000001XYZ123',
    '0063000001ABC456',
    'cust_test_' || GEN_RANDOM_UUID_TEXT(),
    'contact_test_' || GEN_RANDOM_UUID_TEXT(),
    'deal_quality',
    'technical_fit',
    'product_requirements',
    'lambda_test',
    'test_workflow',
    'exec_' || GEN_RANDOM_UUID_TEXT(),
    'medium',
    'new',
    'test_user',
    'Test SQL Insert',
    'This is a test insight using updated SQL schema',
    '{"test": "payload"}',
    '{"test": "evidence"}',
    0.85,
    0.75,
    0.65,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP - INTERVAL '1' HOUR,
    CURRENT_TIMESTAMP + INTERVAL '30' DAY,
    NULL,
    NULL,
    '["test", "lambda"]',
    'test_system',
    'us_west',
    'smb',
    10000.00,
    50000.00,
    0.5,
    '["action1", "action2"]',
    '[]',
    NULL,
    NULL,
    'v1.0',
    'hash_test_' || GEN_RANDOM_UUID_TEXT(),
    CURRENT_TIMESTAMP
)
        """
    }
    
    # Convert payload to JSON string
    payload_json = json.dumps(payload)
    
    # Invoke Lambda function
    print(f"Testing {function_name} with valid schema query...")
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=payload_json.encode('utf-8')
    )
    
    # Read the response
    response_payload = response['Payload'].read().decode('utf-8')
    
    # Save response to a file
    response_file = f"{function_name}_response.json"
    with open(response_file, 'w') as f:
        f.write(response_payload)
    
    print(f"Raw response: {response_payload}")
    print(f"Response saved to {response_file}")
    
    # Parse and print the response
    parsed_response = json.loads(response_payload) if response_payload else {}
    print("Parsed response:")
    print(json.dumps(parsed_response, indent=2))
    
    return parsed_response

if __name__ == "__main__":
    test_firebolt_writer()
