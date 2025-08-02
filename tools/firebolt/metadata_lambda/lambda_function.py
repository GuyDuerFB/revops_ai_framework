import os
import json
import logging
import datetime
import time
import socket
import traceback
from typing import Dict, Any, List, Optional
import boto3

# Always import urllib as fallback
import urllib.request
import urllib.parse
import urllib.error

# Use requests library for better HTTP handling if available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

# Constants
FIREBOLT_CREDENTIALS_SECRET = os.environ.get('FIREBOLT_CREDENTIALS_SECRET', 'firebolt-credentials')
FIREBOLT_ACCOUNT_NAME = os.environ.get('FIREBOLT_ACCOUNT_NAME', 'firebolt-dwh')
FIREBOLT_ENGINE_NAME = os.environ.get('FIREBOLT_ENGINE_NAME', 'dwh_prod_analytics')
FIREBOLT_DATABASE = os.environ.get('FIREBOLT_DATABASE', 'dwh_prod')
FIREBOLT_API_REGION = os.environ.get('FIREBOLT_API_REGION', 'us-east-1')
FIREBOLT_AUTH_ENDPOINT = 'https://id.app.firebolt.io/oauth/token'
TOKEN_EXPIRY_BUFFER = 300  # 5 minutes buffer before token expiry

# Initialize AWS clients
secretsmanager = boto3.client('secretsmanager')

# Initialize metrics
metrics = {
    'service': 'firebolt-metadata-lambda',
    'successful_requests': 0,
    'failed_requests': 0,
    'latency_ms': 0
}

def get_firebolt_credentials():
    """Retrieve Firebolt credentials from AWS Secrets Manager"""
    try:
        logger.info(f"Retrieving Firebolt credentials from secret: {FIREBOLT_CREDENTIALS_SECRET}")
        response = secretsmanager.get_secret_value(SecretId=FIREBOLT_CREDENTIALS_SECRET)
        secret_string = response['SecretString']
        credentials = json.loads(secret_string)
        
        # Verify required fields
        required_fields = ['client_id', 'client_secret']
        missing_fields = [field for field in required_fields if field not in credentials]
        
        if missing_fields:
            raise Exception(f"Missing required fields in credentials: {', '.join(missing_fields)}")
            
        return credentials
    except ClientError as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise

def get_firebolt_token(client_id, client_secret):
    """Get OAuth token from Firebolt API using client credentials flow"""
    logger.info("Getting Firebolt token using client credentials flow")
    url = FIREBOLT_AUTH_ENDPOINT
    
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
        url,
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
        
        # Extract token and expiry
        token = response_data.get('access_token')
        expires_in = response_data.get('expires_in', 3600)
        expiry_time = time.time() + expires_in - TOKEN_EXPIRY_BUFFER
        
        if not token:
            raise Exception("No access token in response")
        
        logger.info("Successfully obtained Firebolt token")
        return token, expiry_time
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if hasattr(e, 'read') else "No error details"
        error_msg = f"Failed to get Firebolt token - HTTP {e.code}: {error_body}"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Failed to get Firebolt token: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

# Cache for Firebolt token
token_cache = {
    'access_token': None,
    'expiry_time': 0
}

def get_cached_token(credentials):
    """Get a cached token or request a new one if expired"""
    current_time = time.time()
    if token_cache['access_token'] is None or current_time >= token_cache['expiry_time']:
        token, expiry_time = get_firebolt_token(credentials['client_id'], credentials['client_secret'])
        token_cache['access_token'] = token
        token_cache['expiry_time'] = expiry_time
    
    return token_cache['access_token']

def execute_firebolt_query(token, account_name=None, engine_name=None, database=None, query=None):
    """Execute a query against Firebolt REST API with retry and better error handling"""
    # Use provided values or fall back to environment variables
    account = account_name or FIREBOLT_ACCOUNT_NAME
    engine = engine_name or FIREBOLT_ENGINE_NAME
    db = database or FIREBOLT_DATABASE
    
    # Define all possible endpoint formats to try
    endpoints = [
        # Standard API endpoints
        f"https://{account}-api.app.firebolt.io/query?engine={engine}&database={db}",
        f"https://{account}.app.firebolt.io/query?engine={engine}&database={db}",
        
        # Region-specific endpoints
        f"https://api.{FIREBOLT_API_REGION}.app.firebolt.io/query?engine={engine}&database={db}",
        f"https://{account}-api.{FIREBOLT_API_REGION}.app.firebolt.io/query?engine={engine}&database={db}",
        
        # Legacy endpoint formats
        f"https://{account}-firebolt.api.{FIREBOLT_API_REGION}.app.firebolt.io/query?engine={engine}&database={db}",
        f"https://{account}.{FIREBOLT_API_REGION}.app.firebolt.io/query?engine={engine}&database={db}",
        
        # Additional variations that might work
        f"https://api.app.firebolt.io/query?engine={engine}&database={db}",
        f"https://api.firebolt.io/query?engine={engine}&database={db}"
    ]
    
    logger.info(f"Starting query execution against Firebolt")
    logger.info(f"Query: {query}")
    logger.info(f"Engine: {engine}, Database: {db}")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Send the SQL query directly as text/plain (like the working writer Lambda)
    query_data = query.encode('utf-8')
    
    # Update the headers to use text/plain content type
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'text/plain'
    }
    
    # Set up retry parameters
    max_attempts = 3
    retry_delay = 2  # seconds
    timeout = 20  # seconds
    
    # Try each endpoint with retry logic
    last_error = None
    
    for endpoint in endpoints:
        logger.info(f"Trying endpoint: {endpoint}")
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_attempts} for {endpoint}")
                
                if REQUESTS_AVAILABLE:
                    # Use requests library if available
                    logger.info(f"Using requests library to connect to {endpoint}")
                    response = requests.post(
                        endpoint, 
                        data=query_data,  # Send raw SQL as text/plain
                        headers=headers,
                        timeout=timeout
                    )
                    
                    # Check if the request was successful
                    response.raise_for_status()
                    
                    logger.info(f"Query successful with status code: {response.status_code}")
                    return response.json()
                
                else:
                    # Fall back to urllib if requests is not available
                    logger.info(f"Using urllib to connect to {endpoint}")
                    req = urllib.request.Request(
                        endpoint, 
                        data=query_data,  # Send raw SQL as text/plain
                        headers=headers
                    )
                    
                    with urllib.request.urlopen(req, timeout=timeout) as response:
                        response_data = response.read().decode('utf-8')
                        logger.info(f"Query successful with urllib")
                        return json.loads(response_data)
                    
            except requests.exceptions.RequestException as e:
                if REQUESTS_AVAILABLE:
                    logger.error(f"Requests error with URL {endpoint}: {str(e)}")
                    
                    # Don't retry certain client errors
                    if hasattr(e, 'response') and e.response is not None:
                        if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                            last_error = f"HTTP Error {e.response.status_code}: {e.response.text}"
                            break
                    
                    last_error = f"Connection error: {str(e)}"
                    
            except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout) as e:
                if not REQUESTS_AVAILABLE:
                    logger.error(f"URLlib error with URL {endpoint}: {str(e)}")
                    
                    if isinstance(e, urllib.error.HTTPError):
                        error_body = e.read().decode('utf-8') if hasattr(e, 'read') else "No error details"
                        if e.code < 500 and e.code != 429:
                            last_error = f"HTTP Error {e.code}: {error_body}"
                            break
                    
                    last_error = f"Connection error: {str(e)}"
                
            except Exception as e:
                logger.error(f"Unexpected error with URL {endpoint}: {str(e)}")
                last_error = f"Error: {str(e)}"
            
            # Wait before retrying (if not the last attempt)
            if attempt < max_attempts - 1:
                retry_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {retry_time} seconds...")
                time.sleep(retry_time)
    
    # If we get here, all endpoints and retries failed
    error_msg = f"All Firebolt API endpoints failed after multiple attempts. Last error: {last_error}"
    logger.error(error_msg)
    raise Exception(error_msg)

def get_database_metadata(token, account_name, engine_name, database):
    """Get metadata for a specific database"""
    query = f"""
    SELECT table_schema, table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_catalog = '{database}'
    ORDER BY table_schema, table_name, ordinal_position
    """
    
    result = execute_firebolt_query(token, account_name, engine_name, database, query)
    
    # Process and structure the metadata
    metadata = {}
    for row in result.get('data', []):
        schema = row[0]
        table = row[1]
        column = row[2]
        data_type = row[3]
        
        if schema not in metadata:
            metadata[schema] = {}
        
        if table not in metadata[schema]:
            metadata[schema][table] = {}
            
        metadata[schema][table][column] = data_type
    
    return metadata

def get_table_statistics(token, account_name, engine_name, database, schema, table):
    """Get statistics for a specific table"""
    query = f"""
    SELECT COUNT(*) as row_count FROM {database}.{schema}.{table}
    """
    
    result = execute_firebolt_query(token, account_name, engine_name, database, query)
    
    # Extract row count
    row_count = 0
    if result.get('data') and len(result['data']) > 0:
        row_count = result['data'][0][0]
    
    return {
        "row_count": row_count
    }

def describe_table_schema(token, account_name, engine_name, database, schema, table):
    """Describe the schema of a specific table"""
    query = f"""
    DESCRIBE {database}.{schema}.{table}
    """
    
    result = execute_firebolt_query(token, account_name, engine_name, database, query)
    
    # Process column information
    columns = []
    for row in result.get('data', []):
        columns.append({
            "name": row[0],
            "type": row[1],
            "nullable": row[2] == "NULL",
            "default": row[3]
        })
    
    return columns

def list_databases(token, account_name, engine_name):
    """List all databases accessible by the engine"""
    query = """
    SELECT database_name FROM information_schema.databases
    ORDER BY database_name
    """
    
    result = execute_firebolt_query(token, account_name, engine_name, FIREBOLT_DATABASE, query)
    
    # Extract database names
    databases = []
    for row in result.get('data', []):
        databases.append(row[0])
    
    return databases

def list_tables_in_database(token, account_name, engine_name, database):
    """List all tables in a specific database"""
    query = f"""
    SELECT table_schema, table_name 
    FROM {database}.information_schema.tables
    WHERE table_type = 'BASE TABLE'
    ORDER BY table_schema, table_name
    """
    
    result = execute_firebolt_query(token, account_name, engine_name, database, query)
    
    # Process table information
    tables = {}
    for row in result.get('data', []):
        schema = row[0]
        table = row[1]
        
        if schema not in tables:
            tables[schema] = []
        
        tables[schema].append(table)
    
    return tables

def lambda_handler(event, context):
    """Lambda handler function focused solely on direct SQL execution"""
    start_time = time.time()
    
    try:
        logger.info(f"METADATA LAMBDA: Received event: {json.dumps(event)}")
        
        # Direct SQL query execution - assume this is the primary purpose
        if 'query' in event:
            query = event.get('query')
            logger.info(f"Processing direct SQL query: {query}")
            
            # Get credentials and token
            credentials = get_firebolt_credentials()
            token = get_cached_token(credentials)
            
            # Get parameters with defaults from env vars
            account_name = event.get('account_name', FIREBOLT_ACCOUNT_NAME)
            engine_name = event.get('engine_name', FIREBOLT_ENGINE_NAME)
            database = event.get('database', FIREBOLT_DATABASE)
            
            logger.info(f"Using account: {account_name}, engine: {engine_name}, database: {database}")
            
            try:
                result = execute_firebolt_query(token, account_name, engine_name, database, query)
                logger.info(f"Query executed successfully: {json.dumps(result)}")
                
                metrics['successful_requests'] += 1
                metrics['latency_ms'] = int((time.time() - start_time) * 1000)
                
                return result
            except Exception as query_error:
                error_msg = str(query_error)
                logger.error(f"Error executing query: {error_msg}")
                metrics['failed_requests'] += 1
                metrics['latency_ms'] = int((time.time() - start_time) * 1000)
                
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'error': error_msg,
                        'metrics': metrics
                    })
                }
        else:
            logger.error("No query parameter found in event")
            metrics['failed_requests'] += 1
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': "Missing required 'query' parameter"
                })
            }
        
        # Get Firebolt credentials
        credentials = get_firebolt_credentials()
        
        # Use environment variables for connection details or override from request
        account_name = body.get('account_name') or FIREBOLT_ACCOUNT_NAME
        engine_name = body.get('engine_name') or FIREBOLT_ENGINE_NAME
        
        # Get authentication token
        token = get_cached_token(credentials)
        
        # Process based on operation
        result = {}
        
        # Simple test connection operation
        if operation == 'test_connection':
            logger.info("Testing connection to Firebolt API")
            # Use a simple query to test the connection
            query = "SELECT 1"
            
            try:
                result = execute_firebolt_query(token, account_name, engine_name, FIREBOLT_DATABASE, query)
                logger.info(f"Test connection response: {json.dumps(result)}")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'success': True,
                        'message': 'Connection test successful',
                        'raw_response': result
                    })
                }
            except Exception as e:
                logger.error(f"Test connection failed: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({
                        'success': False,
                        'error': str(e),
                        'message': 'Connection test failed'
                    })
                }
        
        elif operation == 'list_databases':
            result = list_databases(token, account_name, engine_name)
        
        elif operation == 'list_tables':
            database = body.get('database') or FIREBOLT_DATABASE
            if not database:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'Missing required parameter: database'
                    })
                }
            result = list_tables_in_database(token, account_name, engine_name, database)
        
        elif operation == 'get_database_metadata':
            database = body.get('database') or FIREBOLT_DATABASE
            if not database:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'Missing required parameter: database'
                    })
                }
            result = get_database_metadata(token, account_name, engine_name, database)
        
        elif operation == 'describe_table':
            database = body.get('database')
            schema = body.get('schema')
            table = body.get('table')
            
            if not all([database, schema, table]):
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'Missing required parameters: database, schema, table'
                    })
                }
            
            result = describe_table_schema(token, account_name, engine_name, database, schema, table)
        
        elif operation == 'get_table_stats':
            database = body.get('database')
            schema = body.get('schema')
            table = body.get('table')
            
            if not all([database, schema, table]):
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'Missing required parameters: database, schema, table'
                    })
                }
            
            result = get_table_statistics(token, account_name, engine_name, database, schema, table)
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unsupported operation: {operation}'
                })
            }
        
        # Record metrics
        metrics['successful_requests'] += 1
        metrics['latency_ms'] = int((time.time() - start_time) * 1000)
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'operation': operation,
                'result': result,
                'metrics': metrics
            })
        }
    
    except Exception as e:
        # Record metrics
        metrics['failed_requests'] += 1
        metrics['latency_ms'] = int((time.time() - start_time) * 1000)
        
        logger.error(f"Error processing request: {str(e)}")
        logger.error(traceback.format_exc())
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'metrics': metrics
            })
        }
