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
    print("Obtaining Firebolt access token...")
    
    client_id = credentials.get('client_id')
    client_secret = credentials.get('client_secret')
    
    if not client_id or not client_secret:
        raise Exception("Missing client_id or client_secret in credentials")
    
    auth_url = "https://id.app.firebolt.io/oauth/token"
    
    # Prepare request data
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'audience': 'https://api.firebolt.io'
    }
    
    form_data = urllib.parse.urlencode(data).encode('ascii')
    
    # Create request with Content-Length header
    req = urllib.request.Request(
        auth_url,
        data=form_data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Content-Length': str(len(form_data))
        },
        method='POST'
    )
    
    try:
        # Send request and get response with timeout
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                token_data = json.loads(response.read().decode('utf-8'))
                if 'access_token' not in token_data:
                    raise Exception("No access_token in response from Firebolt auth endpoint")
                print("✓ Access token obtained successfully")
                return token_data['access_token']
            else:
                raise Exception(f"HTTP {response.status}: {response.read().decode('utf-8')}")
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if hasattr(e, 'read') else "No error details"
        raise Exception(f"Failed to get Firebolt access token - HTTP {e.code}: {error_body}")
    except Exception as e:
        raise Exception(f"Failed to get Firebolt access token: {str(e)}")
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
        print("=== Starting Firebolt Query Execution ===")
        
        # Step 1: Get sensitive credentials from secret
        print("Step 1: Getting Firebolt credentials from secret...")
        credentials = get_firebolt_credentials(secret_name, region_name)
        
        # Step 2: Get configuration from environment variables if not provided
        print("Step 2: Getting configuration from environment variables...")
        account = account_name if account_name else os.environ.get('FIREBOLT_ACCOUNT_NAME')
        engine = engine_name if engine_name else os.environ.get('FIREBOLT_ENGINE_NAME')
        database = os.environ.get('FIREBOLT_DATABASE')
        api_region = os.environ.get('FIREBOLT_API_REGION', 'us-east-1')
        
        # Validate configuration
        if not account:
            raise ValueError("Missing account name. Provide as parameter or set FIREBOLT_ACCOUNT_NAME environment variable.")
        if not engine:
            raise ValueError("Missing engine name. Provide as parameter or set FIREBOLT_ENGINE_NAME environment variable.")
        if not database:
            raise ValueError("Missing database name. Set FIREBOLT_DATABASE environment variable.")
            
        print(f"Using configuration: account={account}, engine={engine}, database={database}")
        
        # Step 3: Get access token
        print("Step 3: Getting access token...")
        token = get_firebolt_access_token(credentials)
        
        # Step 4: Execute query
        print("Step 4: Executing query via REST API...")
        
        # Method 1: Using the v2 REST API (JSON-based)
        # api_url = f"https://api.app.firebolt.io/v2/account/{account}/engine/{engine}/query"
        # headers = {
        #     'Authorization': f'Bearer {token}',
        #     'Content-Type': 'application/json'
        # }
        # payload = {
        #     'query': query,
        #     'database': database
        # }
        # data = json.dumps(payload).encode('utf-8')
        
        # Method 2: Using the direct endpoint (text-based) as shown in the example
        query_url = f"https://{account}-firebolt.api.{api_region}.app.firebolt.io?engine={engine}&database={database}"
        print(f"Making request to: {query_url}")
        
        # Send the SQL query directly as data
        query_data = query.encode('utf-8')
        
        # Create request
        req = urllib.request.Request(
            query_url,
            data=query_data,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'text/plain',
                'Content-Length': str(len(query_data))
            }
        )
        
        # Execute request
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
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
            error_body = e.read().decode('utf-8') if hasattr(e, 'read') else "No error details"
            raise Exception(f"Failed to execute Firebolt query - HTTP {e.code}: {error_body}")
            
    except Exception as e:
        print(f"Error executing Firebolt query: {str(e)}")
        raise Exception(f"Error executing Firebolt query: {str(e)}")
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
        # Print debug info about the raw result structure
        print(f"Raw result type: {type(raw_result)}")
        print(f"Raw result keys: {raw_result.keys() if isinstance(raw_result, dict) else 'not a dict'}")
        
        # Handle error cases first
        if isinstance(raw_result, dict) and 'error' in raw_result:
            return {
                'success': False,
                'error': raw_result.get('error', 'Unknown error'),
                'message': raw_result.get('message', 'Query execution failed'),
                'results': [],
                'columns': []
            }
        
        # Handle the actual response structure from Firebolt
        # New format from our testing: {'meta': [...], 'data': [...], 'rows': 1, 'statistics': {...}}
        if isinstance(raw_result, dict) and 'meta' in raw_result and 'data' in raw_result:
            # Extract columns from meta
            columns = []
            for col in raw_result.get('meta', []):
                columns.append({
                    'name': col.get('name', 'unnamed'),
                    'type': col.get('type', 'unknown')
                })
            
            # Extract the row data
            row_data = raw_result.get('data', [])
            
            # Return in the expected format
            return {
                'success': True,
                'results': row_data,  # Already in dict format
                'columns': columns,
                'row_count': len(row_data),
                'column_count': len(columns)
            }
        
        # Handle the case where we receive an array of result objects
        # For example: [{'meta': [...], 'data': [...], 'rows': 1, 'statistics': {...}}]
        if isinstance(raw_result, list) and len(raw_result) > 0 and isinstance(raw_result[0], dict):
            first_result = raw_result[0]
            
            if 'meta' in first_result and 'data' in first_result:
                # Extract columns from meta
                columns = []
                for col in first_result.get('meta', []):
                    columns.append({
                        'name': col.get('name', 'unnamed'),
                        'type': col.get('type', 'unknown')
                    })
                
                # Extract the row data
                row_data = first_result.get('data', [])
                
                # Return in the expected format
                return {
                    'success': True,
                    'results': row_data,  # Already in dict format
                    'columns': columns,
                    'row_count': len(row_data),
                    'column_count': len(columns)
                }
        
        # Legacy format handling (kept for backward compatibility)
        if isinstance(raw_result, dict) and 'data' in raw_result and isinstance(raw_result['data'], dict):
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
        
        # If we reach here, the format is unrecognized
        print(f"Unrecognized result format: {json.dumps(raw_result)[:500]}...")
        return {
            'success': False,
            'error': 'Invalid response format',
            'message': 'The response from Firebolt does not match any expected structure',
            'results': [],
            'columns': []
        }
        
    except Exception as e:
        # Fallback error handler
        print(f"Error in format_simple_result: {str(e)}")
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
