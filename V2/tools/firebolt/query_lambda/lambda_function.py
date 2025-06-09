"""
RevOps AI Framework V2 - Firebolt Query Lambda

This Lambda function executes SQL queries against Firebolt data warehouse
and returns structured results for use by the Data Analysis Agent.
Compatible with AWS Bedrock Agent function calling format.
"""

import json
import boto3
import os
import re
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union

# Helpers for query parsing and validation
def extract_sql_from_markdown(input_text: str) -> str:
    """
    Extract SQL query from markdown code blocks if present.
    Supports both ```sql and ``` formats.
    
    Args:
        input_text (str): Input text that might contain SQL in markdown code blocks
        
    Returns:
        str: Extracted SQL query or the original text if no code blocks found
    """
    if not input_text:
        return input_text
        
    # Look for ```sql ... ``` pattern
    sql_pattern = r'```sql\s*\n([\s\S]*?)\n\s*```'
    match = re.search(sql_pattern, input_text)
    
    if match:
        return match.group(1).strip()
    
    # Look for ``` ... ``` pattern (without explicit sql tag)
    code_pattern = r'```\s*\n([\s\S]*?)\n\s*```'
    match = re.search(code_pattern, input_text)
    
    if match:
        return match.group(1).strip()
    
    # Return original if no code blocks found
    return input_text

# Authentication and credential management
def get_aws_secret(secret_name: str, region_name: str = "us-east-1") -> Dict[str, str]:
    """
    Retrieve a secret from AWS Secrets Manager.
    
    Args:
        secret_name (str): Name of the secret
        region_name (str): AWS region where the secret is stored
        
    Returns:
        Dict[str, str]: Dictionary containing the secret key-value pairs
    """
    print(f"Retrieving secret: {secret_name} from region: {region_name}")
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        raise Exception(f"Failed to retrieve secret {secret_name}: {str(e)}")
    
    if 'SecretString' in get_secret_value_response:
        return json.loads(get_secret_value_response['SecretString'])
    else:
        raise Exception("Secret is not in string format")

def get_firebolt_credentials(secret_name: str, region_name: str = "us-east-1") -> Dict[str, str]:
    """
    Get Firebolt credentials from AWS Secrets Manager.
    Only requires client_id and client_secret in the secret.
    
    Args:
        secret_name (str): Name of the secret containing client_id and client_secret
        region_name (str): AWS region where the secret is stored
        
    Returns:
        Dict[str, str]: Dictionary with client credentials
    """
    credentials = get_aws_secret(secret_name, region_name)
    
    # Verify required fields
    required_fields = ['client_id', 'client_secret']
    missing_fields = [field for field in required_fields if field not in credentials]
    
    if missing_fields:
        raise Exception(f"Missing required fields in credentials: {', '.join(missing_fields)}")
    
    return credentials

# OAuth authentication
def get_firebolt_access_token(credentials: Dict[str, str]) -> str:
    """
    Get access token from Firebolt using client credentials OAuth flow.
    Uses urllib instead of requests to avoid external dependencies.
    
    Args:
        credentials (Dict[str, str]): Firebolt credentials containing client_id and client_secret
        
    Returns:
        str: Access token for Firebolt API calls
    """
    client_id = credentials.get('client_id')
    client_secret = credentials.get('client_secret')
    
    if not client_id or not client_secret:
        raise Exception("Missing client_id or client_secret in credentials")
    
    auth_url = "https://id.app.firebolt.io/oauth/token"
    
    # Prepare request data
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    data = urllib.parse.urlencode(data).encode('ascii')
    
    # Create request
    req = urllib.request.Request(
        auth_url,
        data=data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        method='POST'
    )
    
    try:
        # Send request and get response
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
        # Extract token
        token = response_data.get('access_token')
        if not token:
            raise Exception("No access token in response")
            
        return token
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"Failed to get Firebolt token. Status: {e.code}, Response: {error_body}")

# Query execution
def execute_firebolt_query(
    query: str, 
    secret_name: str, 
    region_name: str = "us-east-1",
    account_name: Optional[str] = None,
    engine_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a SQL query against Firebolt using REST API.
    Gets configuration from environment variables and credentials from Secrets Manager.
    
    Args:
        query (str): The SQL query to execute
        secret_name (str): Name of the AWS secret containing client_id and client_secret
        region_name (str): AWS region where the secret is stored
        account_name (Optional[str]): Firebolt account name to use (overrides env variable)
        engine_name (Optional[str]): Firebolt engine name to use (overrides env variable)
        
    Returns:
        Dict[str, Any]: A dictionary with query results in JSON-serializable format
    """
    try:
        # Get Firebolt credentials from Secrets Manager
        credentials = get_firebolt_credentials(secret_name, region_name)
        
        # Get access token using OAuth
        token = get_firebolt_access_token(credentials)
        
        # Get account/engine configuration
        firebolt_account = account_name or os.environ.get('FIREBOLT_ACCOUNT', 'firebolt')
        firebolt_engine = engine_name or os.environ.get('FIREBOLT_ENGINE', 'revops')
        
        # Build query URL
        query_url = f"https://api.app.firebolt.io/query/{firebolt_account}/{firebolt_engine}"
        
        # Prepare request data
        data = {
            'query': query
        }
        
        data = json.dumps(data).encode('utf-8')
        
        # Create request
        req = urllib.request.Request(
            query_url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            },
            method='POST'
        )
        
        # Execute query
        with urllib.request.urlopen(req) as response:
            raw_result = json.loads(response.read().decode('utf-8'))
            
        # Format the result into a simplified structure
        result = format_simple_result(raw_result)
        
        return result
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {
            'success': False,
            'error': f"Firebolt query error: {e.code}",
            'message': error_body,
            'results': [],
            'columns': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': "Failed to execute query against Firebolt",
            'results': [],
            'columns': []
        }

# JSON serialization helpers
def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def format_simple_result(raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the raw query result into a simple structured response.
    Returns all data as an array without chunking.
    Ensures all data is JSON serializable.
    
    Args:
        raw_result (Dict[str, Any]): Raw result from Firebolt API
        
    Returns:
        Dict[str, Any]: Formatted result with all data
    """
    try:
        # Handle error cases first
        if 'error' in raw_result:
            return {
                'success': False,
                'error': raw_result.get('error', 'Unknown error'),
                'message': raw_result.get('message', 'Query execution failed'),
                'results': [],
                'columns': []
            }
            
        # Check for expected structure
        if 'data' not in raw_result or not isinstance(raw_result['data'], dict):
            return {
                'success': False,
                'error': 'Invalid response format',
                'message': 'The response from Firebolt does not contain expected data structure',
                'results': [],
                'columns': []
            }
                
        # Extract metadata and rows
        metadata = raw_result['data'].get('metadata', [])
        rows = raw_result['data'].get('rows', [])
        
        # Extract column names from metadata
        columns = []
        for col in metadata:
            columns.append({
                'name': col.get('name', 'unnamed'),
                'type': col.get('type', 'unknown')
            })
        
        column_names = [col['name'] for col in columns]
        
        # Process each row, making sure all values are JSON serializable
        processed_rows = []
        for row in rows:
            # Convert any non-serializable types
            processed_row = {}
            for i, value in enumerate(row):
                if i < len(column_names):
                    col_name = column_names[i]
                    # Handle special types
                    if isinstance(value, (datetime, date)):
                        processed_row[col_name] = value.isoformat()
                    else:
                        processed_row[col_name] = value
            processed_rows.append(processed_row)
        
        # Construct final response
        return {
            'success': True,
            'results': processed_rows,
            'columns': columns,
            'row_count': len(processed_rows),
            'column_count': len(columns)
        }
        
    except Exception as e:
        # Fallback error handler
        return {
            'success': False,
            'error': f'Error formatting results: {str(e)}',
            'message': 'Failed to format query results',
            'results': [],
            'columns': []
        }

# Main Lambda handlers
def query_fire(query=None, account_name=None, engine_name=None):
    """
    Execute SQL queries against Firebolt data warehouse and return structured results.
    Matches the Bedrock Agent function schema signature.
    
    Args:
        query (str): The SQL query to execute against Firebolt. Can be provided as plain SQL
                     or wrapped in markdown code blocks (```sql ... ```).
        account_name (str, optional): Firebolt account name to use (overrides env variable)
        engine_name (str, optional): Firebolt engine name to use (overrides env variable)
    
    Returns:
        dict: Results from the Firebolt query in a structured format
    """
    try:
        if not query:
            return {
                "success": False,
                "error": "No SQL query provided",
                "message": "Please provide a valid SQL query to execute"
            }
        
        # Extract SQL from markdown if needed
        query = extract_sql_from_markdown(query)
        
        # Use environment variables or defaults for these values
        secret_name = os.environ.get('FIREBOLT_CREDENTIALS_SECRET', 'firebolt-credentials')
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Execute the query
        result = execute_firebolt_query(
            query, 
            secret_name, 
            region_name,
            account_name,
            engine_name
        )
        
        return result
        
    except Exception as e:
        print(f"Error in query_fire: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute query against Firebolt"
        }

def lambda_handler(event, context):
    """
    AWS Lambda handler for Firebolt queries
    Compatible with Bedrock Agent function calling format
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # 1. Check if this is a Bedrock Agent invocation
        if 'actionGroup' in event and event.get('actionGroup') == 'firebolt_query':
            # This is a Bedrock Agent invocation
            action_name = event.get('action')
            
            if action_name == 'query_fire':
                api_path = event.get('apiPath')
                body = event.get('body', {})
                parameters = body.get('parameters', {})
                
                # Extract parameters
                query = parameters.get('query')
                account_name = parameters.get('account_name')
                engine_name = parameters.get('engine_name')
                
                # Call our dedicated function
                return query_fire(query, account_name, engine_name)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action_name}",
                    "message": "This Lambda only supports the 'query_fire' action."
                }
                
        # 2. Check if this is a direct invocation with parameters
        if 'query' in event:
            # Direct invocation
            query = event.get('query')
            account_name = event.get('account_name')
            engine_name = event.get('engine_name')
            
            return query_fire(query, account_name, engine_name)
            
        # 3. Legacy parameter format for backward compatibility
        elif 'parameters' in event and isinstance(event['parameters'], list):
            # Handle Bedrock agent parameter format (older versions)
            params = {param.get('name'): param.get('value') for param in event['parameters']}
            query = params.get('query')
            account_name = params.get('account_name')
            engine_name = params.get('engine_name')
            
            return query_fire(query, account_name, engine_name)
        
        # 4. No recognizable format
        return {
            'success': False,
            'error': 'Invalid request format',
            'message': 'Request format not recognized. Please provide a query parameter.',
            'results': [],
            'columns': []
        }
        
    except Exception as e:
        # Log the full error for debugging
        print(f"Lambda handler error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Return error response in the expected format
        error_response = {
            'success': False,
            'error': str(e),
            'results': [],
            'columns': []
        }
        print(f"Returning error response: {json.dumps(error_response)}")
        return error_response
