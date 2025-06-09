"""
Consolidated Firebolt Query Executor Lambda function.
Fixed for Bedrock Agent compatibility.
"""

import json
import boto3
import os
import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import urlencode
import urllib.error

def extract_sql_from_markdown(input_text):
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

def query_fire(query=None):
    """
    Execute SQL queries against Firebolt data warehouse and return structured results.
    Matches the Bedrock Agent function schema signature.
    
    Args:
        query (str): The SQL query to execute against Firebolt. Can be provided as plain SQL
                     or wrapped in markdown code blocks (```sql ... ```).
    
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
        region_name = os.environ.get('AWS_REGION', 'eu-north-1')
        
        # Execute the query
        result = execute_firebolt_query(query, secret_name, region_name)
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
    AWS Lambda handler for Firebolt queries using REST API
    Fixed for Bedrock Agent compatibility - returns direct JSON response
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # 1. Check if this is a Bedrock Agent invocation
        if 'actionGroup' in event and event.get('actionGroup') == 'firebolt_function':
            # This is a Bedrock Agent invocation
            action_name = event.get('action')
            
            if action_name == 'query_fire':
                api_path = event.get('apiPath')
                body = event.get('body', {})
                parameters = body.get('parameters', {})
                query = parameters.get('query')
                
                # Call our dedicated function
                return query_fire(query)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action_name}",
                    "message": "This Lambda only supports the 'query_fire' action."
                }
                
        # 2. Check if this is a direct invocation with parameters
        if 'query' in event:
            query = event.get('query')
        elif 'parameters' in event and isinstance(event['parameters'], list):
            # Handle Bedrock agent parameter format (older versions)
            params = {param.get('name'): param.get('value') for param in event['parameters']}
            query = params.get('query')
        else:
            query = None
            
        secret_name = event.get('secret_name', 'firebolt-credentials')
        region_name = event.get('region_name', 'eu-north-1')
        
        # Validate required parameters
        if not query:
            print("Error: Missing required parameter: query")
            return {
                'success': False,
                'error': 'Missing required parameter: query',
                'results': [],
                'columns': []
            }
        
        # Extract SQL from markdown if needed
        query = extract_sql_from_markdown(query)
        
        # Log execution details
        print(f"Executing Firebolt query: {query[:100]}...")
        print(f"Using secret: {secret_name}")
        print(f"Region: {region_name}")
        
        # Execute query
        result = execute_firebolt_query(
            query=query, 
            secret_name=secret_name, 
            region_name=region_name
        )
        
        print(f"Query execution successful, returning result with {len(result.get('results', []))} rows")
        
        # Return direct JSON response for Bedrock agent
        return result
        
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

def get_aws_secret(secret_name: str, region_name: str = "eu-north-1") -> Dict[str, str]:
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

def get_firebolt_credentials(secret_name: str, region_name: str = "eu-north-1") -> Dict[str, str]:
    """
    Get Firebolt credentials from AWS Secrets Manager.
    Only requires client_id and client_secret in the secret.
    
    Args:
        secret_name (str): Name of the secret containing client_id and client_secret
        region_name (str): AWS region where the secret is stored
        
    Returns:
        Dict[str, str]: Dictionary with client credentials
    """
    secret = get_aws_secret(secret_name, region_name)
    
    # Only require sensitive credentials from the secret
    required_keys = ["client_id", "client_secret"]
    missing_keys = [key for key in required_keys if key not in secret]
    
    if missing_keys:
        raise ValueError(f"Missing required Firebolt credentials in secret: {', '.join(missing_keys)}")
    
    print("✓ Retrieved client credentials from secret")
    return secret

def get_firebolt_access_token(credentials: Dict[str, str]) -> str:
    """
    Get access token from Firebolt using client credentials OAuth flow.
    Uses urllib instead of requests to avoid external dependencies.
    
    Args:
        credentials (Dict[str, str]): Firebolt credentials containing client_id and client_secret
        
    Returns:
        str: Access token for Firebolt API calls
    """
    print("Obtaining Firebolt access token...")
    
    auth_url = "https://id.app.firebolt.io/oauth/token"
    
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': credentials['client_id'],
        'client_secret': credentials['client_secret'],
        'audience': 'https://api.firebolt.io'
    }
    
    # URL-encode the form data
    form_data = urlencode(auth_data).encode('ascii')
    
    # Create request
    req = Request(
        auth_url,
        data=form_data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(form_data))
        }
    )
    
    try:
        with urlopen(req, timeout=10) as response:
            if response.status == 200:
                token_data = json.loads(response.read().decode('utf-8'))
                if 'access_token' not in token_data:
                    raise Exception("No access_token in response from Firebolt auth endpoint")
                print("✓ Access token obtained successfully")
                return token_data['access_token']
            else:
                raise Exception(f"HTTP {response.status}: {response.read().decode('utf-8')}")
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else "No error details"
        raise Exception(f"Failed to get Firebolt access token - HTTP {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"Failed to get Firebolt access token: {str(e)}")

def execute_firebolt_query(
    query: str, 
    secret_name: str, 
    region_name: str = "eu-north-1"
) -> Dict[str, Any]:
    """
    Execute a SQL query against Firebolt using REST API.
    Gets configuration from environment variables and credentials from Secrets Manager.
    
    Args:
        query (str): The SQL query to execute
        secret_name (str): Name of the AWS secret containing client_id and client_secret
        region_name (str): AWS region where the secret is stored
        
    Returns:
        Dict[str, Any]: A dictionary with query results in JSON-serializable format
    """
    try:
        print("=== Starting Firebolt Query Execution ===")
        
        # Step 1: Get sensitive credentials from secret
        print("Step 1: Getting Firebolt credentials from secret...")
        credentials = get_firebolt_credentials(secret_name, region_name)
        
        # Step 2: Get configuration from environment variables
        print("Step 2: Getting configuration from environment variables...")
        engine_name = os.environ.get('FIREBOLT_ENGINE_NAME')
        database = os.environ.get('FIREBOLT_DATABASE')
        account_name = os.environ.get('FIREBOLT_ACCOUNT_NAME')
        api_region = os.environ.get('FIREBOLT_API_REGION', 'us-east-1')
        
        # Validate required configuration
        if not engine_name:
            raise ValueError("FIREBOLT_ENGINE_NAME environment variable is required")
        if not database:
            raise ValueError("FIREBOLT_DATABASE environment variable is required")
        if not account_name:
            raise ValueError("FIREBOLT_ACCOUNT_NAME environment variable is required")
        
        print(f"Using configuration: account={account_name}, engine={engine_name}, database={database}")
        
        # Step 3: Get access token
        print("Step 3: Getting access token...")
        access_token = get_firebolt_access_token(credentials)
        
        # Step 4: Execute query
        print("Step 4: Executing query via REST API...")
        # Construct the query URL using the environment variables
        query_url = f"https://{account_name}-firebolt.api.{api_region}.app.firebolt.io?engine={engine_name}&database={database}"
        print(f"Making request to: {query_url}")
        
        # Send the SQL query directly as data
        query_data = query.encode('utf-8')
        
        # Create request
        req = Request(
            query_url,
            data=query_data,
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'text/plain',
                'Content-Length': str(len(query_data))
            }
        )
        
        # Execute request
        try:
            with urlopen(req, timeout=30) as response:
                if response.status == 200:
                    response_body_str = response.read().decode('utf-8')
                    result = json.loads(response_body_str)
                    print("✓ Query executed successfully")
                    
                    # Format response to a simple structure with all data
                    formatted_result = format_simple_result(result)
                    
                    return formatted_result
                else:
                    raise Exception(f"HTTP {response.status}: {response.read().decode('utf-8')}")
                    
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else "No error details"
            raise Exception(f"Failed to execute Firebolt query - HTTP {e.code}: {error_body}")
            
    except Exception as e:
        print(f"Error executing Firebolt query: {str(e)}")
        raise e

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

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
    # Basic structure validation
    if 'data' not in raw_result or 'meta' not in raw_result:
        raise ValueError(f"Invalid response format from Firebolt API. Got: {str(raw_result)[:200]}")
    
    # Extract column information
    columns = []
    for col in raw_result['meta']:
        columns.append({
            'name': col['name'],
            'type': col['type']
        })
    
    # Print debug info about the data structure
    all_rows = raw_result['data']
    total_rows = len(all_rows)
    print(f"Total rows: {total_rows}")
    if total_rows > 0:
        print(f"Row data type: {type(all_rows[0])}")
        print(f"Sample row: {str(all_rows[0])[:100]}")
    
    # Handle both list-like and dict-like row structures
    formatted_rows = []
    for row in all_rows:
        row_dict = {}
        
        # Determine if row is a dict, list, or something else
        if isinstance(row, dict):
            # If row is already a dict, use as is or transform if needed
            for col in columns:
                col_name = col['name']
                if col_name in row:
                    value = row[col_name]
                    # Handle datetime objects properly
                    if isinstance(value, (datetime, date)):
                        row_dict[col_name] = value.isoformat()
                    else:
                        row_dict[col_name] = value
        elif isinstance(row, (list, tuple)):
            # If row is a list/tuple, map by index
            for i, col in enumerate(columns):
                if i < len(row):
                    value = row[i]
                    # Handle datetime objects properly
                    if isinstance(value, (datetime, date)):
                        row_dict[col['name']] = value.isoformat()
                    else:
                        row_dict[col['name']] = value
        else:
            # If row is neither dict nor list, convert to string
            row_dict = {"value": str(row)}
            
        formatted_rows.append(row_dict)
    
    # Prepare final result - ensure it's JSON serializable
    result = {
        'success': True,
        'columns': [col['name'] for col in columns],  # Simplified column format
        'results': formatted_rows,
        'total_rows': total_rows,
        'query_info': {
            'columns_details': columns  # Keep detailed info here if needed
        }
    }
    
    # Test JSON serialization to catch issues early
    try:
        json.dumps(result, default=json_serializer)
        print("✓ Result is JSON serializable")
    except Exception as e:
        print(f"⚠️ JSON serialization issue: {str(e)}")
        # Fallback to string representation for problematic data
        result['results'] = [str(row) for row in formatted_rows]
    
    return result