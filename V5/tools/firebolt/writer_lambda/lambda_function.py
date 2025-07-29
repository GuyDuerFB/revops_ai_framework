"""
RevOps AI Framework V2 - Firebolt Writer Lambda

This Lambda function writes data back to Firebolt data warehouse
and returns execution results for use by the Execution Agent.
Compatible with AWS Bedrock Agent function calling format.

Supports specialized operations for the RevOps AI Insights table,
with handling for VARIANT data types and complex JSON payloads.
"""

import json
import boto3
import os
import re
import uuid
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union, Set

# Authentication and credential management
# Helper functions for data type handling
def format_value_for_sql(value: Any) -> str:
    """
    Format a value for inclusion in SQL based on its data type.
    Handles special types like dates, timestamps, booleans, and JSON.
    
    Args:
        value: The value to format
        
    Returns:
        str: SQL-formatted representation of the value
    """
    if value is None:
        return "NULL"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, (datetime, date)):
        return f"'{value.isoformat()}'"
    elif isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    elif isinstance(value, (dict, list)):
        # JSON data in Firebolt is stored as TEXT
        # Convert to properly formatted JSON string
        json_str = json.dumps(value, ensure_ascii=False).replace("'", "''")
        return f"'{json_str}'"
    else:
        # Escape string values
        escaped_value = str(value).replace("'", "''")
        return f"'{escaped_value}'"

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
        'client_secret': client_secret,
        'audience': 'https://api.firebolt.io'
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
    Handles complex data types including VARIANT JSON.
    
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
    
    # Process values and format properly using our helper
    for key in columns:
        values.append(format_value_for_sql(data[key]))
    
    # Construct SQL
    columns_str = ", ".join(columns)
    values_str = ", ".join(values)
    
    return f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str})"

def generate_update_sql(table_name: str, data: Dict[str, Any], where_clause: str) -> str:
    """
    Generate SQL UPDATE statement from data.
    Handles complex data types including VARIANT JSON.
    
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
        formatted_value = format_value_for_sql(value)
        set_clauses.append(f"{key} = {formatted_value}")
    
    # Construct SQL
    set_clause_str = ", ".join(set_clauses)
    
    return f"UPDATE {table_name} SET {set_clause_str} WHERE {where_clause}"

def generate_upsert_sql(table_name: str, data: Dict[str, Any], key_columns: List[str]) -> str:
    """
    Generate SQL for upsert operation using MERGE syntax.
    Handles complex data types including VARIANT JSON.
    
    Args:
        table_name (str): Target table name
        data (Dict[str, Any]): Data to insert or update
        key_columns (List[str]): Columns that identify unique records
        
    Returns:
        str: SQL for UPSERT operation using MERGE
    """
    if not data:
        raise ValueError("No data provided for UPSERT")
    
    if not key_columns or not all(col in data for col in key_columns):
        raise ValueError("Missing key columns for UPSERT")
    
    # Generate the insert and on-conflict clauses
    columns = list(data.keys())
    values = []
    
    # Process values and format properly using our helper
    for key in columns:
        values.append(format_value_for_sql(data[key]))
    
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
        # Get Firebolt credentials from Secrets Manager using environment variable
        secret_name = os.environ.get('FIREBOLT_CREDENTIALS_SECRET', 'firebolt-credentials')
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
        
        print(f"Getting Firebolt credentials from secret: {secret_name} in region: {region_name}")
        credentials = get_firebolt_credentials(secret_name, region_name)
        
        # Get access token using OAuth
        print("Getting Firebolt access token")
        token = get_firebolt_access_token(credentials)
        print("Successfully obtained Firebolt access token")
        
        # Get account/engine configuration - use same env vars as query Lambda
        firebolt_account = account_name or os.environ.get('FIREBOLT_ACCOUNT_NAME', 'firebolt-dwh')
        firebolt_engine = engine_name or os.environ.get('FIREBOLT_ENGINE_NAME', 'dwh_prod_analytics')
        firebolt_database = os.environ.get('FIREBOLT_DATABASE', 'dwh_prod')
        firebolt_api_region = os.environ.get('FIREBOLT_API_REGION', 'us-east-1')
        
        # Build query URL using the format that works in query Lambda
        query_url = f"https://{firebolt_account}-firebolt.api.{firebolt_api_region}.app.firebolt.io?engine={firebolt_engine}&database={firebolt_database}"
        
        # Send the SQL query directly as data, like in the query Lambda
        data = query.encode('utf-8')
        
        # Create request with text/plain content type as in query Lambda
        req = urllib.request.Request(
            query_url,
            data=data,
            headers={
                'Content-Type': 'text/plain',
                'Authorization': f'Bearer {token}'
            }
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

# Specialized functions for RevOps AI Insights table
def validate_insight_data(insight_data: Dict[str, Any]) -> Dict[str, Union[bool, str]]:
    """
    Validate insight data against schema requirements.
    Allows both string-encoded JSON and JSON-serializable objects for TEXT fields.
    
    Args:
        insight_data (Dict[str, Any]): Insight data to validate
        
    Returns:
        Dict[str, Union[bool, str]]: Validation result with status and optional error message
    """
    if not isinstance(insight_data, dict):
        return {"valid": False, "error": "Insight data must be a dictionary"}
    
    # Required fields validation
    required_fields = ['insight_category', 'insight_type', 'source_agent', 'insight_title', 'insight_description']
    
    # For updates, we don't require all fields
    missing_fields = [field for field in required_fields if field not in insight_data]
    if missing_fields:
        return {"valid": False, "error": f"Missing required fields: {', '.join(missing_fields)}"}
    
    # Validate categorical fields using allowed values
    status_types = ['new', 'acknowledged', 'in_progress', 'resolved', 'dismissed']
    if 'status' in insight_data and insight_data['status'] not in status_types:
        return {"valid": False, "error": f"Invalid status: {insight_data['status']}. Must be one of: {', '.join(status_types)}"}
    
    # Validate insight category and type combinations
    category_types = {
        'deal_quality': [
            'icp_alignment', 'technical_fit', 'commercial_fit', 'competitive_threat', 'data_quality',
            'icp_misalignment', 'missing_data', 'company_size_mismatch'
        ],
        'consumption_pattern': [
            'usage_trend', 'feature_adoption', 'query_optimization', 'resource_utilization', 
            'performance_degradation', 'quota_approaching', 'usage_decline'
        ],
        'churn_risk': [
            'engagement_drop', 'support_escalation', 'contract_approaching', 'usage_anomaly'
        ],
        'pipeline_health': [
            'conversion_rate_decline', 'velocity_slowdown', 'coverage_gap'
        ],
        'growth_opportunity': [
            'expansion_opportunity', 'upsell_candidate', 'cross_sell_potential'
        ]
    }
    
    if 'insight_category' in insight_data and 'insight_type' in insight_data:
        category = insight_data['insight_category']
        if category not in category_types:
            return {"valid": False, "error": f"Invalid insight_category: {category}. Must be one of: {', '.join(category_types.keys())}"}
        insight_type = insight_data['insight_type']
        if insight_type not in category_types[category]:
            return {"valid": False, "error": f"Invalid insight_type '{insight_type}' for category '{category}'. Must be one of: {', '.join(category_types[category])}"}
    
    # Format validation for specific fields
    if 'confidence_score' in insight_data:
        try:
            score = float(insight_data['confidence_score'])
            if score < 0.0 or score > 1.0:
                return {"valid": False, "error": "confidence_score must be between 0.0 and 1.0"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "confidence_score must be a float between 0.0 and 1.0"}
    
    if 'impact_score' in insight_data:
        try:
            score = float(insight_data['impact_score'])
            if score < 0.0 or score > 1.0:
                return {"valid": False, "error": "impact_score must be between 0.0 and 1.0"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "impact_score must be a float between 0.0 and 1.0"}
    
    if 'urgency_score' in insight_data:
        try:
            score = float(insight_data['urgency_score'])
            if score < 0.0 or score > 1.0:
                return {"valid": False, "error": "urgency_score must be between 0.0 and 1.0"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "urgency_score must be a float between 0.0 and 1.0"}
    
    if 'priority_level' in insight_data:
        valid_priorities = ['critical', 'high', 'medium', 'low']
        if insight_data['priority_level'] not in valid_priorities:
            return {
                "valid": False,
                "error": f"Invalid priority_level: {insight_data['priority_level']}. Must be one of: {', '.join(valid_priorities)}"
            }
    
    # Validate that JSON fields are properly formatted
    json_fields = ['insight_payload', 'evidence_data', 'recommended_actions', 'actions_taken', 'tags']
    for field in json_fields:
        if field in insight_data:
            # Allow both string-encoded JSON and JSON-serializable objects
            if insight_data[field] is None:
                # None is allowed
                continue
            elif isinstance(insight_data[field], (dict, list)):
                # Valid JSON-serializable object
                continue
            elif isinstance(insight_data[field], str):
                # Validate that the string is a valid JSON if provided as string
                try:
                    json.loads(insight_data[field])
                except json.JSONDecodeError:
                    return {"valid": False, "error": f"Field '{field}' contains invalid JSON string"}
            else:
                return {"valid": False, "error": f"Field '{field}' must be NULL, a valid JSON object, or a JSON string"}
    
    return {"valid": True}

def generate_insight_id() -> str:
    """
    Generate a unique insight ID with timestamp and UUID.
    
    Returns:
        str: A unique insight ID
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_suffix = uuid.uuid4().hex[:8]
    return f"insight_{timestamp}_{random_suffix}"

def write_insight(query_type: str, insight_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """
    Specialized function for writing insights to the revops_ai_insights table.
    Performs validation and proper formatting of insight data.
    Converts JSON fields to properly formatted TEXT strings for Firebolt.
    
    Args:
        query_type (str): Operation type (insert, update, delete)
        insight_data (Dict[str, Any]): Insight data to write
        **kwargs: Additional arguments for the operation
        
    Returns:
        Dict[str, Any]: Operation result
    """
    # Make a copy of the input data to avoid modifying the original
    insight_data = insight_data.copy()
    
    # Validate the insight data
    validation = validate_insight_data(insight_data)
    if not validation["valid"]:
        return {
            "success": False, 
            "error": "Invalid insight data",
            "message": validation["error"]
        }
    
    # For INSERT, generate an insight_id if not provided
    if query_type.lower() == 'insert' and 'insight_id' not in insight_data:
        insight_data['insight_id'] = generate_insight_id()
    
    # Set created_at timestamp for new insights
    if query_type.lower() == 'insert' and 'created_at' not in insight_data:
        insight_data['created_at'] = datetime.utcnow().isoformat()
    
    # Set default status for new insights
    if query_type.lower() == 'insert' and 'status' not in insight_data:
        insight_data['status'] = 'new'
    
    # Handle JSON fields - explicitly convert to JSON strings for TEXT storage
    json_fields = ['insight_payload', 'evidence_data', 'recommended_actions', 'actions_taken', 'tags']
    for field in json_fields:
        if field in insight_data and isinstance(insight_data[field], (dict, list)):
            # Convert JSON objects directly to strings to store as TEXT
            # format_value_for_sql will still be applied later but this ensures proper typing
            insight_data[field] = json.dumps(insight_data[field])
    
    # Set timestamps for status changes
    if query_type.lower() == 'update' and 'status' in insight_data:
        if insight_data['status'] == 'acknowledged' and 'acknowledged_at' not in insight_data:
            insight_data['acknowledged_at'] = datetime.utcnow().isoformat()
        elif insight_data['status'] == 'resolved' and 'resolved_at' not in insight_data:
            insight_data['resolved_at'] = datetime.utcnow().isoformat()
    
    # Use the general write function
    table_name = "revops_ai_insights"
    
    # Handle delete operation
    if query_type.lower() == 'delete':
        where_clause = kwargs.get('where_clause')
        if not where_clause:
            return {
                "success": False,
                "error": "WHERE clause is required for DELETE operations",
                "message": "Please provide a where_clause parameter"
            }
        sql = generate_delete_sql(table_name, where_clause)
        result = execute_firebolt_query(sql, kwargs.get('account_name'), kwargs.get('engine_name'))
        return result
    
    return write_to_firebolt(query_type, table_name, insight_data, **kwargs)

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
        
        # Log debug info
        print(f"Write operation: {query_type} to table: {table_name}")
        print(f"Data: {json.dumps(data, default=str)}")
        
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
            account_name=account_name,
            engine_name=engine_name
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

def generate_delete_sql(table_name: str, where_clause: str) -> str:
    """
    Generate SQL DELETE statement.
    
    Args:
        table_name (str): Target table name
        where_clause (str): WHERE clause to identify records to delete
        
    Returns:
        str: SQL DELETE statement
    """
    if not where_clause:
        raise ValueError("WHERE clause is required for DELETE operation")
    
    return f"DELETE FROM {table_name} WHERE {where_clause}"

def lambda_handler(event, context):
    """
    AWS Lambda handler for Firebolt write operations - simplified for direct SQL execution
    """
    try:
        print(f"WRITER LAMBDA: Received event: {json.dumps(event)}")
        
        # Direct SQL query execution - assume this is the primary purpose
        if 'query' in event:
            query = event.get('query')
            print(f"Processing direct SQL query: {query}")
            
            # Get parameters with defaults from env vars
            account_name = event.get('account_name') or os.environ.get('FIREBOLT_ACCOUNT_NAME')
            engine_name = event.get('engine_name') or os.environ.get('FIREBOLT_ENGINE_NAME')
            
            # Get secret name and region from environment variables
            secret_name = os.environ.get('FIREBOLT_CREDENTIALS_SECRET')
            region_name = os.environ.get('AWS_REGION', 'us-east-1')
            
            print(f"Using account: {account_name}, engine: {engine_name}")
            print(f"Secret: {secret_name}, Region: {region_name}")
            print(f"Query to execute: {query}")
            
            # Execute the query directly
            try:
                # Direct execution with SQL query
                result = execute_firebolt_query(
                    query,
                    account_name=account_name,
                    engine_name=engine_name
                )
                print("Query executed successfully")
                return {
                    'success': True,
                    'message': "SQL query executed successfully",
                    'result': result
                }
            except Exception as query_error:
                print(f"Error executing query: {str(query_error)}")
                return {
                    'success': False,
                    'error': str(query_error),
                    'message': "Error executing direct SQL query."
                }
        else:
            print("No query parameter found in event")
            return {
                'success': False,
                'error': "Missing required parameter", 
                'message': "Please provide a 'query' parameter with your SQL statement"
            }

        # 1. Check if this is a Bedrock Agent invocation
        if 'actionGroup' in event and event.get('actionGroup') == 'firebolt_writer':
            # This is a Bedrock Agent invocation
            action_name = event.get('action')
            body = event.get('body', {})
            parameters = body.get('parameters', {})
            
            # Special handling for insights operations
            if action_name == 'write_insight':
                query_type = parameters.get('query_type')
                insight_data = parameters.get('data', {})
                where_clause = parameters.get('where_clause')
                key_columns = parameters.get('key_columns')
                account_name = parameters.get('account_name')
                engine_name = parameters.get('engine_name')
                
                return write_insight(
                    query_type,
                    insight_data,
                    where_clause=where_clause,
                    key_columns=key_columns,
                    account_name=account_name,
                    engine_name=engine_name
                )
            
            # Standard Firebolt write operations
            elif action_name == 'write_to_firebolt':
                query_type = parameters.get('query_type')
                table_name = parameters.get('table_name')
                data = parameters.get('data', {})
                where_clause = parameters.get('where_clause')
                key_columns = parameters.get('key_columns')
                account_name = parameters.get('account_name')
                engine_name = parameters.get('engine_name')
                
                # Special handling for revops_ai_insights table
                if table_name == 'revops_ai_insights':
                    return write_insight(
                        query_type,
                        data,
                        where_clause=where_clause,
                        key_columns=key_columns,
                        account_name=account_name,
                        engine_name=engine_name
                    )
                
                # General write operations
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
                    "message": "Supported actions are 'write_to_firebolt' and 'write_insight'"
                }
                
        # 2. Check for special insight operation in direct invocation
        if 'operation' in event and event['operation'] == 'insight':
            query_type = event.get('query_type')
            insight_data = event.get('data', {})
            where_clause = event.get('where_clause')
            key_columns = event.get('key_columns')
            account_name = event.get('account_name')
            engine_name = event.get('engine_name')
            
            return write_insight(
                query_type, 
                insight_data, 
                where_clause=where_clause,
                key_columns=key_columns,
                account_name=account_name,
                engine_name=engine_name
            )
                
        # 3. Check if this is a direct invocation with parameters
        # Support both old format (query_type/table_name) and new format (operation/table)
        if ('query_type' in event and 'table_name' in event) or ('operation' in event and 'table' in event):
            # Direct invocation - handle both parameter formats
            query_type = event.get('query_type') or event.get('operation')
            table_name = event.get('table_name') or event.get('table')
            data = event.get('data', {})
            where_clause = event.get('where_clause')
            key_columns = event.get('key_columns')
            account_name = event.get('account_name')
            engine_name = event.get('engine_name')
            
            print(f"Using parameters: operation={query_type}, table={table_name}")
            print(f"Data: {json.dumps(data, default=str)}")
            
            # Special handling for revops_ai_insights table
            if table_name == 'revops_ai_insights':
                return write_insight(
                    query_type,
                    data,
                    where_clause=where_clause,
                    key_columns=key_columns,
                    account_name=account_name,
                    engine_name=engine_name
                )
            
            return write_to_firebolt(
                query_type, 
                table_name, 
                data, 
                where_clause, 
                key_columns, 
                account_name, 
                engine_name
            )
            
        # 4. Legacy parameter format for backward compatibility
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
            
            # Special handling for insights table
            if table_name == 'revops_ai_insights':
                return write_insight(
                    query_type,
                    data,
                    where_clause=where_clause,
                    key_columns=key_columns,
                    account_name=account_name,
                    engine_name=engine_name
                )
            
            return write_to_firebolt(
                query_type, 
                table_name, 
                data, 
                where_clause, 
                key_columns, 
                account_name, 
                engine_name
            )
        
        # 5. No recognizable format
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