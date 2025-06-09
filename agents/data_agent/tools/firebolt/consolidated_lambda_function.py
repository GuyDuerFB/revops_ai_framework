"""
Consolidated Firebolt Query Executor Lambda function.
Simple implementation that returns all data as an array.
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

def lambda_handler(event, context):
    """
    AWS Lambda handler for Firebolt queries using REST API
    Returns all data as a simple array without chunking
    """
    try:
        # Extract parameters from the event
        query = event.get('query')
        secret_name = event.get('secret_name', 'firebolt-credentials')
        region_name = event.get('region_name', 'eu-north-1')
        
        # Validate required parameters
        if not query:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required parameter: query'
                })
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
        
        # Return successful response
        return {
            'statusCode': 200,
            'body': json.dumps(result, default=str)  # Handle any datetime objects
        }
        
    except Exception as e:
        # Log the full error for debugging
        print(f"Lambda handler error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Return error response
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'results': [],
                'columns': []
            })
        }

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
        max_rows_per_chunk (int): Maximum number of rows per chunk
        chunk_index (int): Which chunk to return (0 = first chunk or metadata)
        
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
        # Format: https://{account_name}-firebolt.api.{api_region}.app.firebolt.io?engine={engine_name}&database={database}
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

def format_simple_result(
    raw_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Format the raw query result into a simple structured response.
    Returns all data as an array without chunking.
    
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
    
    # Prepare base result
    result = {
        'success': True,
        'columns': columns,
        'total_rows': total_rows
    }
    
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
                    if isinstance(value, (datetime, date)):
                        row_dict[col_name] = value.isoformat()
                    else:
                        row_dict[col_name] = value
        elif isinstance(row, (list, tuple)):
            # If row is a list/tuple, map by index
            for i, col in enumerate(columns):
                if i < len(row):
                    value = row[i]
                    if isinstance(value, (datetime, date)):
                        row_dict[col['name']] = value.isoformat()
                    else:
                        row_dict[col['name']] = value
        else:
            # If row is neither dict nor list, convert to string
            row_dict = {"value": str(row)}
            
        formatted_rows.append(row_dict)
    
    result['results'] = formatted_rows
    
    return result

# The get_query_chunk function has been removed as we no longer need chunking functionality
