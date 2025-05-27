"""
Database utilities for connecting to and querying Firebolt.
"""

import os
import json
import boto3
from datetime import datetime, date
from firebolt.client import ClientCredentials
from firebolt.db import connect
from typing import Dict, List, Union, Tuple, Any, Optional

# AWS Secrets Manager utilities
def get_aws_secret(secret_name: str, region_name: str = "us-west-2") -> Dict[str, str]:
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
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        raise Exception(f"Failed to retrieve secret {secret_name}: {str(e)}")
    
    # Parse and return secret
    if 'SecretString' in get_secret_value_response:
        return json.loads(get_secret_value_response['SecretString'])
    else:
        raise Exception("Secret is not in string format")

def get_firebolt_credentials(secret_name: str, region_name: str = "us-west-2") -> Dict[str, str]:
    """
    Get Firebolt credentials from AWS Secrets Manager.
    
    Args:
        secret_name (str): Name of the secret containing Firebolt credentials
        region_name (str): AWS region where the secret is stored
        
    Returns:
        Dict[str, str]: Dictionary with Firebolt connection parameters
    """
    secret = get_aws_secret(secret_name, region_name)
    
    required_keys = ["client_id", "client_secret", "engine_name", "database", "account_name"]
    if not all(key in secret for key in required_keys):
        missing_keys = [key for key in required_keys if key not in secret]
        raise ValueError(f"Missing required Firebolt credentials: {', '.join(missing_keys)}")
    
    return secret

def get_firebolt_connection(secret_name: str, region_name: str = "us-west-2"):
    """
    Get a connection to Firebolt using AWS Secrets Manager.
    
    Args:
        secret_name (str): Name of the secret containing Firebolt credentials
        region_name (str): AWS region where the secret is stored
        
    Returns:
        Connection: Firebolt database connection
    """
    credentials = get_firebolt_credentials(secret_name, region_name)
    
    return connect(
        auth=ClientCredentials(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"]
        ),
        engine_name=credentials["engine_name"],
        database=credentials["database"],
        account_name=credentials["account_name"],
        api_endpoint=credentials.get("api_endpoint", "api.app.firebolt.io")
    )

def execute_firebolt_query(
    query: str, 
    secret_name: str, 
    region_name: str = "us-west-2"
) -> Dict[str, Any]:
    """
    Execute a SQL query against Firebolt and return results in JSON format.
    
    Args:
        query (str): The SQL query to execute
        secret_name (str): Name of the AWS secret containing Firebolt credentials
        region_name (str): AWS region where the secret is stored
        
    Returns:
        Dict[str, Any]: A dictionary with query results in JSON-serializable format
    """
    try:
        # Get connection using AWS secrets
        connection = get_firebolt_connection(secret_name, region_name)
        cursor = connection.cursor()
        
        # Execute the query
        cursor.execute(query)
        
        # Get column names from cursor description
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Fetch all results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries and handle date serialization
        formatted_results = []
        for row in results:
            result_row = {}
            for i, val in enumerate(row):
                # Handle date/datetime objects for JSON serialization
                if isinstance(val, (datetime, date)):
                    result_row[columns[i]] = val.isoformat()
                elif val is None:
                    result_row[columns[i]] = None
                else:
                    result_row[columns[i]] = val
            formatted_results.append(result_row)
        
        # Create response dictionary
        response = {
            "success": True,
            "count": len(formatted_results),
            "results": formatted_results,
            "columns": columns
        }
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        return response
        
    except Exception as e:
        error_message = f"Error executing Firebolt query: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "results": [],
            "columns": []
        }
