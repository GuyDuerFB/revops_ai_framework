"""
Firebolt Query Executor module for executing SQL queries against Firebolt databases.
"""

import json
import boto3
import os
import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import urlencode
import urllib.error
from io import BytesIO

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
    region_name: str = "eu-north-1",
    max_rows_per_chunk: int = 1000,  # Default chunk size for large result sets
    chunk_index: int = 0  # Which chunk to return (0 = first chunk or metadata)
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
        # Updated URL structure based on working Zapier implementation
        # Format: https://firebolt-dwh-firebolt.api.us-east-1.app.firebolt.io?engine=dwh_prod_analytics&database=dwh_prod
        api_region = os.environ.get('FIREBOLT_API_REGION', 'us-east-1')
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
        
        print(f"Making request to: {query_url}")
        
        # Execute request
        try:
            with urlopen(req, timeout=30) as response:
                if response.status == 200:
                    response_body_str = response.read().decode('utf-8')
                    result = json.loads(response_body_str)
                    print("✓ Query executed successfully")
                    
                    # Format response to match expected structure
                    if 'data' in result and 'meta' in result:
                        # Extract column metadata
                        columns = [col['name'] for col in result['meta']]
                        
                        # Extract results
                        rows = result['data']
                        
                        # Process results
                        formatted_results = []
                        for row in rows:
                            result_row = {}
                            for i, val in enumerate(row):
                                if isinstance(val, (datetime, date)):
                                    result_row[columns[i]] = val.isoformat()
                                else:
                                    result_row[columns[i]] = val
                            formatted_results.append(result_row)
                        
                        # Determine if we need to chunk the results based on row count
                        total_rows = len(formatted_results)
                        total_chunks = (total_rows + max_rows_per_chunk - 1) // max_rows_per_chunk  # Ceiling division
                        
                        print(f"Total rows: {total_rows}, chunks: {total_chunks} (max {max_rows_per_chunk} rows per chunk)")
                        
                        # If requesting chunk 0 or there's only one chunk, return metadata or all results
                        if chunk_index == 0 or total_chunks == 1:
                            if total_chunks > 1:
                                # This is a large result set - return metadata and first chunk
                                first_chunk = formatted_results[:max_rows_per_chunk]
                                print(f"✓ Query executed successfully: {total_rows} total rows, returning metadata and first chunk ({len(first_chunk)} rows)")
                                
                                return {
                                    "success": True,
                                    "error": None,
                                    "chunked": True,
                                    "chunk_index": 0,
                                    "total_chunks": total_chunks,
                                    "total_rows": total_rows,
                                    "rows_per_chunk": max_rows_per_chunk,
                                    "columns": columns,
                                    "results": first_chunk,
                                    "query_info": {
                                        "query": query,
                                        "secret_name": secret_name,
                                        "region_name": region_name
                                    }
                                }
                            else:
                                # Small result set - return everything
                                print(f"✓ Query executed successfully: {total_rows} rows returned (single chunk)")
                                return {
                                    "success": True,
                                    "error": None,
                                    "chunked": False,
                                    "columns": columns,
                                    "results": formatted_results
                                }
                        else:
                            # Return the requested chunk
                            if chunk_index >= total_chunks:
                                return {
                                    "success": False,
                                    "error": f"Requested chunk {chunk_index} exceeds available chunks ({total_chunks})",
                                    "chunked": True,
                                    "total_chunks": total_chunks
                                }
                            
                            # Calculate start and end indices for the requested chunk
                            start_idx = chunk_index * max_rows_per_chunk
                            end_idx = min(start_idx + max_rows_per_chunk, total_rows)
                            chunk_data = formatted_results[start_idx:end_idx]
                            
                            print(f"✓ Returning chunk {chunk_index} of {total_chunks} ({len(chunk_data)} rows)")
                            return {
                                "success": True,
                                "error": None,
                                "chunked": True,
                                "chunk_index": chunk_index,
                                "total_chunks": total_chunks,
                                "total_rows": total_rows,
                                "columns": columns,
                                "results": chunk_data
                            }
                    else:
                        # Handle different response format
                        print("✓ Query executed but no standard data/meta format")
                        return {
                            "success": True,
                            "error": None,
                            "results": [],
                            "columns": []
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

def get_query_chunk(
    query: str,
    secret_name: str,
    region_name: str = "eu-north-1",
    chunk_index: int = 1,  # 1-based chunk indexing (chunk 0 is metadata)
    max_rows_per_chunk: int = 1000,
    query_execution_id: str = None
) -> Dict[str, Any]:
    """
    Get a specific chunk of a large query result. If query_execution_id is provided,
    this will retrieve the chunk from the original query results. Otherwise, it will
    execute the query and return the specified chunk.
    
    Args:
        query (str): The SQL query to execute
        secret_name (str): Name of the AWS secret containing client_id and client_secret
        region_name (str): AWS region where the secret is stored
        chunk_index (int): Index of the chunk to retrieve (1-based)
        max_rows_per_chunk (int): Maximum number of rows per chunk
        query_execution_id (str): Optional ID from a previous query execution
        
    Returns:
        Dict[str, Any]: The requested chunk of query results
    """
    # For now, just execute the original query and return the specified chunk
    # In a production implementation, you'd want to cache results temporarily
    return execute_firebolt_query(
        query=query,
        secret_name=secret_name,
        region_name=region_name,
        max_rows_per_chunk=max_rows_per_chunk,
        chunk_index=chunk_index
    )

# Legacy compatibility functions
def get_firebolt_connection(*args, **kwargs):
    """Legacy function - not used in REST API approach"""
    raise NotImplementedError("Use execute_firebolt_query directly with REST API approach")