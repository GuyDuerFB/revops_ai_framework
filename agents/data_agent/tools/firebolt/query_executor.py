"""
Firebolt Query Executor module for executing SQL queries against Firebolt databases.
"""

import json
import boto3
import os
from datetime import datetime, date
from typing import Dict, Any, List
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import urlencode
import urllib.error

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
        api_endpoint = os.environ.get('FIREBOLT_API_ENDPOINT', 'api.app.firebolt.io')
        
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
        query_url = f"https://{engine_name}.{api_endpoint}/query?database={database}"
        
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
        
        print(f"Making request to: {query_url}")
        
        # Execute request
        try:
            with urlopen(req, timeout=30) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    print("✓ Query executed successfully")
                    
                    # Format response to match expected structure
                    if 'data' in result and 'meta' in result:
                        columns = [col['name'] for col in result['meta']]
                        rows = result['data']
                        
                        formatted_results = []
                        for row in rows:
                            result_row = {}
                            for i, val in enumerate(row):
                                if isinstance(val, (datetime, date)):
                                    result_row[columns[i]] = val.isoformat()
                                else:
                                    result_row[columns[i]] = val
                            formatted_results.append(result_row)
                        
                        print(f"✓ Returning {len(formatted_results)} rows with columns: {columns}")
                        return {
                            "success": True,
                            "count": len(formatted_results),
                            "results": formatted_results,
                            "columns": columns
                        }
                    else:
                        # Handle different response format
                        print("✓ Query executed but no standard data/meta format")
                        return {
                            "success": True,
                            "count": 0,
                            "results": [],
                            "columns": [],
                            "raw_response": result
                        }
                        
                else:
                    error_msg = response.read().decode('utf-8')
                    print(f"✗ Query failed with HTTP {response.status}: {error_msg}")
                    return {
                        "success": False,
                        "error": f"Query execution failed - HTTP {response.status}: {error_msg}",
                        "results": [],
                        "columns": []
                    }
                    
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else "No error details"
            error_message = f"HTTP {e.code}: {error_body}"
            print(f"✗ HTTP error during query execution: {error_message}")
            return {
                "success": False,
                "error": f"Query execution failed: {error_message}",
                "results": [],
                "columns": []
            }
            
    except Exception as e:
        error_message = f"Error executing Firebolt query: {str(e)}"
        print(f"✗ {error_message}")
        return {
            "success": False,
            "error": error_message,
            "results": [],
            "columns": []
        }

# Legacy compatibility functions
def get_firebolt_connection(*args, **kwargs):
    """Legacy function - not used in REST API approach"""
    raise NotImplementedError("Use execute_firebolt_query directly with REST API approach")