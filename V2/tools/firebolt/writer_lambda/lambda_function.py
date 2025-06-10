"""
RevOps AI Framework V2 - Firebolt Writer Lambda

This Lambda function writes data back to Firebolt data warehouse
and returns execution results for use by the Execution Agent.
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
# SQL Generation for write operations
def generate_insert_sql(table_name: str, data: Dict[str, Any]) -> str:
    """
    Generate SQL INSERT statement from data.
    
    Args:
        table_name (str): Target table name
        data (Dict[str, Any]): Data to insert
        
    Returns:
        str: SQL INSERT statement
    """
    if not data:
        raise ValueError("No data provided for INSERT")
    
    # Extract column names and values
    columns = list(data.keys())
    values = []
    
    # Process values and format properly
    for key in columns:
        value = data[key]
        
        # Format value based on type
        if value is None:
            values.append("NULL")
        elif isinstance(value, (int, float)):
            values.append(str(value))
        elif isinstance(value, (datetime, date)):
            values.append(f"'{value.isoformat()}'")
        elif isinstance(value, bool):
            values.append("TRUE" if value else "FALSE")
        else:
            # Escape string values
            escaped_value = str(value).replace("'", "''")
            values.append(f"'{escaped_value}'")
    
    # Construct SQL
    columns_str = ", ".join(columns)
    values_str = ", ".join(values)
    
    return f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str})"

def generate_update_sql(table_name: str, data: Dict[str, Any], where_clause: str) -> str:
    """
    Generate SQL UPDATE statement from data.
    
    Args:
        table_name (str): Target table name
        data (Dict[str, Any]): Data to update
        where_clause (str): WHERE clause to identify records
        
    Returns:
        str: SQL UPDATE statement
    """
    if not data:
        raise ValueError("No data provided for UPDATE")
    
    if not where_clause:
        raise ValueError("WHERE clause is required for UPDATE")
    
    # Generate SET clauses
    set_clauses = []
    
    for key, value in data.items():
        # Format value based on type
        if value is None:
            set_clauses.append(f"{key} = NULL")
        elif isinstance(value, (int, float)):
            set_clauses.append(f"{key} = {value}")
        elif isinstance(value, (datetime, date)):
            set_clauses.append(f"{key} = '{value.isoformat()}'")
        elif isinstance(value, bool):
            set_clauses.append(f"{key} = {'TRUE' if value else 'FALSE'}")
        else:
            # Escape string values
            escaped_value = str(value).replace("'", "''")
            set_clauses.append(f"{key} = '{escaped_value}'")
    
    # Construct SQL
    set_clause_str = ", ".join(set_clauses)
    
    return f"UPDATE {table_name} SET {set_clause_str} WHERE {where_clause}"

def generate_upsert_sql(table_name: str, data: Dict[str, Any], key_columns: List[str]) -> str:
    """
    Generate SQL for upsert operation using INSERT OR UPDATE pattern.
    
    Args:
        table_name (str): Target table name
        data (Dict[str, Any]): Data to insert or update
        key_columns (List[str]): Columns that identify unique records
        
    Returns:
        str: SQL for UPSERT operation
    """
    if not data:
        raise ValueError("No data provided for UPSERT")
    
    if not key_columns or not all(col in data for col in key_columns):
        raise ValueError("Missing key columns for UPSERT")
    
    # Generate the insert and on-conflict clauses
    columns = list(data.keys())
    values = []
    
    # Process values and format properly
    for key in columns:
        value = data[key]
        
        # Format value based on type
        if value is None:
            values.append("NULL")
        elif isinstance(value, (int, float)):
            values.append(str(value))
        elif isinstance(value, (datetime, date)):
            values.append(f"'{value.isoformat()}'")
        elif isinstance(value, bool):
            values.append("TRUE" if value else "FALSE")
        else:
            # Escape string values
            escaped_value = str(value).replace("'", "''")
            values.append(f"'{escaped_value}'")
    
    # Construct the INSERT part
    columns_str = ", ".join(columns)
    values_str = ", ".join(values)
    
    # Construct the UPDATE part for conflict resolution
    update_clauses = []
    for col in columns:
        if col not in key_columns:
            update_clauses.append(f"{col} = EXCLUDED.{col}")
    
    update_clause_str = ", ".join(update_clauses)
    key_columns_str = ", ".join(key_columns)
    
    # Firebolt supports MERGE syntax for upserts
    # Create a temporary table with the new values
    temp_table = f"temp_{table_name}_upsert"
    key_condition = " AND ".join([f"t.{col} = s.{col}" for col in key_columns])
    update_set = ", ".join([f"t.{col} = s.{col}" for col in columns if col not in key_columns])
    
    # Build the MERGE statement
    merge_sql = f"""
    MERGE INTO {table_name} t
    USING (SELECT {columns_str} FROM (VALUES {values_str}) as s({columns_str})) as s
    ON {key_condition}
    WHEN MATCHED THEN
        UPDATE SET {update_set}
    WHEN NOT MATCHED THEN
        INSERT ({columns_str}) VALUES ({', '.join([f's.{col}' for col in columns])})
    """
    
    return merge_sql

# Execute query against Firebolt
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
            
        # For write operations, a simple success/rows affected response is usually sufficient
        return {
            'success': True,
            'message': f"Query executed successfully against {firebolt_engine}",
            'raw_response': raw_result
        }
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return {
            'success': False,
            'error': f"Firebolt query error: {e.code}",
            'message': error_body
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': "Failed to execute query against Firebolt"
        }

# Main function for Firebolt write operations
def write_to_firebolt(
    query_type: str,
    table_name: str,
    data: Dict[str, Any],
    where_clause: Optional[str] = None,
    key_columns: Optional[List[str]] = None,
    account_name: Optional[str] = None,
    engine_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Write data to Firebolt based on operation type.
    Matches the Bedrock Agent function schema signature.
    
    Args:
        query_type (str): Type of operation (insert, update, upsert)
        table_name (str): Target table for the operation
        data (Dict[str, Any]): Data to write
        where_clause (Optional[str]): WHERE clause for updates
        key_columns (Optional[List[str]]): Key columns for upsert operations
        account_name (Optional[str]): Firebolt account name to use (overrides env variable)
        engine_name (Optional[str]): Firebolt engine name to use (overrides env variable)
    
    Returns:
        Dict[str, Any]: Operation result
    """
    try:
        # Validate parameters
        if not table_name:
            return {
                "success": False,
                "error": "Table name is required",
                "message": "Please provide a valid table name"
            }
        
        if not data:
            return {
                "success": False,
                "error": "Data is required",
                "message": "Please provide data to write"
            }
        
        # Use environment variables or defaults for these values
        secret_name = os.environ.get('FIREBOLT_CREDENTIALS_SECRET', 'firebolt-credentials')
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Generate SQL based on operation type
        if query_type.lower() == 'insert':
            query = generate_insert_sql(table_name, data)
        elif query_type.lower() == 'update':
            if not where_clause:
                return {
                    "success": False,
                    "error": "WHERE clause is required for UPDATE operations",
                    "message": "Please provide a where_clause parameter"
                }
            query = generate_update_sql(table_name, data, where_clause)
        elif query_type.lower() == 'upsert':
            if not key_columns:
                return {
                    "success": False,
                    "error": "Key columns are required for UPSERT operations",
                    "message": "Please provide key_columns parameter"
                }
            query = generate_upsert_sql(table_name, data, key_columns)
        else:
            return {
                "success": False,
                "error": f"Unsupported operation: {query_type}",
                "message": "Supported operations are: insert, update, upsert"
            }
        
        # Log the generated query for debugging
        print(f"Executing query: {query}")
        
        # Execute the query
        result = execute_firebolt_query(
            query, 
            secret_name, 
            region_name,
            account_name,
            engine_name
        )
        
        # Include metadata in response
        result.update({
            "operation": query_type,
            "table": table_name,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return result
        
    except Exception as e:
        print(f"Error in write_to_firebolt: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute write operation"
        }

def lambda_handler(event, context):
    """
    AWS Lambda handler for Firebolt write operations.
    Compatible with Bedrock Agent function calling format.
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # 1. Check if this is a Bedrock Agent invocation
        if 'actionGroup' in event and event.get('actionGroup') == 'firebolt_writer':
            # This is a Bedrock Agent invocation
            action_name = event.get('action')
            
            if action_name == 'write_to_firebolt':
                body = event.get('body', {})
                parameters = body.get('parameters', {})
                
                # Extract parameters
                query_type = parameters.get('query_type')
                table_name = parameters.get('table_name')
                data = parameters.get('data', {})
                where_clause = parameters.get('where_clause')
                key_columns = parameters.get('key_columns')
                account_name = parameters.get('account_name')
                engine_name = parameters.get('engine_name')
                
                # Call our dedicated function
                return write_to_firebolt(
                    query_type, 
                    table_name, 
                    data, 
                    where_clause, 
                    key_columns, 
                    account_name, 
                    engine_name
                )
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action_name}",
                    "message": "This Lambda only supports the 'write_to_firebolt' action."
                }
                
        # 2. Check if this is a direct invocation with parameters
        if 'query_type' in event and 'table_name' in event:
            # Direct invocation
            query_type = event.get('query_type')
            table_name = event.get('table_name')
            data = event.get('data', {})
            where_clause = event.get('where_clause')
            key_columns = event.get('key_columns')
            account_name = event.get('account_name')
            engine_name = event.get('engine_name')
            
            return write_to_firebolt(
                query_type, 
                table_name, 
                data, 
                where_clause, 
                key_columns, 
                account_name, 
                engine_name
            )
            
        # 3. Legacy parameter format for backward compatibility
        elif 'parameters' in event and isinstance(event['parameters'], list):
            # Handle Bedrock agent parameter format (older versions)
            params = {param.get('name'): param.get('value') for param in event['parameters']}
            query_type = params.get('query_type')
            table_name = params.get('table_name')
            data = params.get('data', {})
            where_clause = params.get('where_clause')
            key_columns = params.get('key_columns')
            account_name = params.get('account_name')
            engine_name = params.get('engine_name')
            
            return write_to_firebolt(
                query_type, 
                table_name, 
                data, 
                where_clause, 
                key_columns, 
                account_name, 
                engine_name
            )
        
        # 4. No recognizable format
        return {
            'success': False,
            'error': 'Invalid request format',
            'message': 'Request format not recognized. Please provide required parameters.',
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
            'message': 'An error occurred processing the write operation'
        }
        print(f"Returning error response: {json.dumps(error_response)}")
        return error_response