import os
import json
import boto3
import logging
import urllib.request
import traceback
import time
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(log_level)

# Constants
FIREBOLT_CREDENTIALS_SECRET = os.environ.get('FIREBOLT_CREDENTIALS_SECRET', 'firebolt-credentials')
FIREBOLT_API_ENDPOINT = 'https://api.app.firebolt.io'
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
        return credentials
    except ClientError as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise

def get_firebolt_token(username, password):
    """Get OAuth token from Firebolt API"""
    url = f"{FIREBOLT_API_ENDPOINT}/auth/v1/login"
    payload = json.dumps({
        "username": username,
        "password": password
    })
    headers = {
        'Content-Type': 'application/json'
    }
    
    req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            expires_in = response_data.get('expires_in', 3600)
            expiry_time = time.time() + expires_in - TOKEN_EXPIRY_BUFFER
            return response_data['access_token'], expiry_time
    except Exception as e:
        logger.error(f"Error getting Firebolt token: {str(e)}")
        raise

# Cache for Firebolt token
token_cache = {
    'access_token': None,
    'expiry_time': 0
}

def get_cached_token(credentials):
    """Get a cached token or request a new one if expired"""
    current_time = time.time()
    if token_cache['access_token'] is None or current_time >= token_cache['expiry_time']:
        token, expiry_time = get_firebolt_token(credentials['username'], credentials['password'])
        token_cache['access_token'] = token
        token_cache['expiry_time'] = expiry_time
    
    return token_cache['access_token']

def execute_firebolt_query(token, account_id, engine_name, query):
    """Execute a query against Firebolt REST API"""
    url = f"{FIREBOLT_API_ENDPOINT}/query/v1/accounts/{account_id}/engines/{engine_name}/query"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload = json.dumps({
        "query": query
    })
    
    req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise

def get_database_metadata(token, account_id, engine_name, database):
    """Get metadata for a specific database"""
    query = f"""
    SELECT table_schema, table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_catalog = '{database}'
    ORDER BY table_schema, table_name, ordinal_position
    """
    
    result = execute_firebolt_query(token, account_id, engine_name, query)
    
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

def get_table_statistics(token, account_id, engine_name, database, schema, table):
    """Get statistics for a specific table"""
    query = f"""
    SELECT COUNT(*) as row_count FROM {database}.{schema}.{table}
    """
    
    result = execute_firebolt_query(token, account_id, engine_name, query)
    
    # Extract row count
    row_count = 0
    if result.get('data') and len(result['data']) > 0:
        row_count = result['data'][0][0]
    
    return {
        "row_count": row_count
    }

def describe_table_schema(token, account_id, engine_name, database, schema, table):
    """Describe the schema of a specific table"""
    query = f"""
    DESCRIBE {database}.{schema}.{table}
    """
    
    result = execute_firebolt_query(token, account_id, engine_name, query)
    
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

def list_databases(token, account_id, engine_name):
    """List all databases accessible by the engine"""
    query = """
    SELECT database_name FROM information_schema.databases
    ORDER BY database_name
    """
    
    result = execute_firebolt_query(token, account_id, engine_name, query)
    
    # Extract database names
    databases = []
    for row in result.get('data', []):
        databases.append(row[0])
    
    return databases

def list_tables_in_database(token, account_id, engine_name, database):
    """List all tables in a specific database"""
    query = f"""
    SELECT table_schema, table_name 
    FROM {database}.information_schema.tables
    WHERE table_type = 'BASE TABLE'
    ORDER BY table_schema, table_name
    """
    
    result = execute_firebolt_query(token, account_id, engine_name, query)
    
    # Process table information
    tables = {}
    for row in result.get('data', []):
        schema = row[0]
        table = row[1]
        
        if schema not in tables:
            tables[schema] = []
        
        tables[schema].append(table)
    
    return tables

def handler(event, context):
    """Lambda handler function"""
    start_time = time.time()
    
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract parameters
        body = event
        if isinstance(event, str):
            body = json.loads(event)
        elif 'body' in event and event['body']:
            body = json.loads(event['body'])
        
        operation = body.get('operation')
        
        # Get Firebolt credentials
        credentials = get_firebolt_credentials()
        account_id = body.get('account_id') or credentials.get('account_id', '')
        engine_name = body.get('engine_name') or credentials.get('engine_name', '')
        
        # Get authentication token
        token = get_cached_token(credentials)
        
        # Process based on operation
        result = {}
        
        if operation == 'list_databases':
            result = list_databases(token, account_id, engine_name)
        
        elif operation == 'list_tables':
            database = body.get('database')
            if not database:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'Missing required parameter: database'
                    })
                }
            result = list_tables_in_database(token, account_id, engine_name, database)
        
        elif operation == 'get_database_metadata':
            database = body.get('database')
            if not database:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'Missing required parameter: database'
                    })
                }
            result = get_database_metadata(token, account_id, engine_name, database)
        
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
            
            result = describe_table_schema(token, account_id, engine_name, database, schema, table)
        
        elif operation == 'get_table_statistics':
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
            
            result = get_table_statistics(token, account_id, engine_name, database, schema, table)
        
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
