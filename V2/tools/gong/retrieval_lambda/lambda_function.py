"""
RevOps AI Framework V2 - Gong Data Retrieval Lambda

This Lambda function retrieves conversation data from Gong and returns structured results
for use by the Data Analysis Agent.
Compatible with AWS Bedrock Agent function calling format.
"""

import json
import boto3
import os
import urllib.request
import urllib.error
import urllib.parse
import base64
import hmac
import hashlib
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional, Union
import re

# Utility functions
def parse_date_range_string(date_range_str: str) -> Dict[str, str]:
    """
    Parse a date range string (e.g., "7d", "30d", "1w") into from/to dates.
    
    Args:
        date_range_str (str): Date range string like "7d", "30d", "1w", "3m"
        
    Returns:
        Dict[str, str]: Dictionary with 'from' and 'to' date strings in ISO format
    """
    # Remove any whitespace
    date_range_str = date_range_str.strip().lower()
    
    # Parse the number and unit
    match = re.match(r'^(\d+)([dwmy])$', date_range_str)
    if not match:
        # Default to 7 days if invalid format
        amount = 7
        unit = 'd'
    else:
        amount = int(match.group(1))
        unit = match.group(2)
    
    # Calculate the date range
    now = datetime.utcnow()
    
    if unit == 'd':  # days
        from_date = now - timedelta(days=amount)
    elif unit == 'w':  # weeks
        from_date = now - timedelta(weeks=amount)
    elif unit == 'm':  # months (approximate as 30 days)
        from_date = now - timedelta(days=amount * 30)
    elif unit == 'y':  # years (approximate as 365 days)
        from_date = now - timedelta(days=amount * 365)
    else:
        # Default to days
        from_date = now - timedelta(days=amount)
    
    # Format as ISO strings
    return {
        'from': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': now.strftime('%Y-%m-%dT%H:%M:%SZ')
    }

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

def get_gong_credentials(secret_name: str, region_name: str = "us-east-1") -> Dict[str, str]:
    """
    Get Gong API credentials from AWS Secrets Manager.
    
    Args:
        secret_name (str): Name of the secret containing Gong credentials
        region_name (str): AWS region where the secret is stored
        
    Returns:
        Dict[str, str]: Dictionary with Gong API credentials
    """
    credentials = get_aws_secret(secret_name, region_name)
    
    # Verify required fields
    required_fields = ['access_key', 'access_key_secret']
    missing_fields = [field for field in required_fields if field not in credentials]
    
    if missing_fields:
        raise Exception(f"Missing required fields in credentials: {', '.join(missing_fields)}")
    
    return credentials

# Gong API Request Handling
def generate_gong_headers(access_key: str, access_key_secret: str) -> Dict[str, str]:
    """
    Generate headers for Gong API authentication.
    
    Args:
        access_key (str): Gong Access Key
        access_key_secret (str): Gong Access Key Secret
        
    Returns:
        Dict[str, str]: Headers for Gong API requests
    """
    # Current timestamp for the request
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    
    # Generate the signature
    message = f"{access_key}{timestamp}"
    signature = hmac.new(
        access_key_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Encode credentials for Basic authentication
    import base64
    auth_string = f"{access_key}:{access_key_secret}"
    encoded_auth = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    # Return headers
    return {
        'Authorization': f"Basic {encoded_auth}",
        'X-API-Signature': signature,
        'X-API-Timestamp': str(timestamp),
        'Content-Type': 'application/json'
    }

def make_gong_request(
    endpoint: str, 
    method: str, 
    credentials: Dict[str, str],
    body: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make a request to the Gong API.
    
    Args:
        endpoint (str): API endpoint to call
        method (str): HTTP method to use
        credentials (Dict[str, str]): Gong API credentials
        body (Optional[Dict[str, Any]]): Request body for POST requests
        
    Returns:
        Dict[str, Any]: Response from the Gong API
    """
    base_url = "https://api.gong.io/v2"
    url = f"{base_url}/{endpoint}"
    
    # Generate headers with authentication
    headers = generate_gong_headers(
        credentials.get('access_key', ''),
        credentials.get('access_key_secret', '')
    )
    
    # Prepare request data if needed
    data = None
    if body and method in ['POST', 'PUT', 'PATCH']:
        data = json.dumps(body).encode('utf-8')
    
    # Create request
    print(f"DEBUG: Making request to {url} with method {method}")
    print(f"DEBUG: Request headers: {headers}")
    if data:
        print(f"DEBUG: Request body: {data.decode('utf-8')}")
    
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )
    
    try:
        # Send request and get response
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
        return response_data
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"Gong API error: {e.code}, Response: {error_body}")

# Data processing functions
def clean_gong_response(raw_data: Dict[str, Any], query_type: str) -> Dict[str, Any]:
    """
    Process and clean Gong API response based on query type.
    
    Args:
        raw_data (Dict[str, Any]): Raw response data from Gong
        query_type (str): Type of query made (calls, topics, keywords, etc.)
        
    Returns:
        Dict[str, Any]: Cleaned and processed data
    """
    if not raw_data:
        return {
            "success": False,
            "error": "Empty response from Gong API",
            "results": []
        }
    
    try:
        # For debugging
        print(f"DEBUG: Raw Gong API response for {query_type}: {json.dumps(raw_data)[:500]}...")
        
        if query_type == 'calls':
            # Process call data - handle different possible response formats
            calls = []
            
            # The new Gong API returns calls directly in the response
            if isinstance(raw_data, list):
                calls = raw_data
            # Standard format with 'calls' key
            elif 'calls' in raw_data and isinstance(raw_data['calls'], list):
                calls = raw_data['calls']
            # Format with records wrapper
            elif 'records' in raw_data and 'calls' in raw_data:
                calls = raw_data['calls']
                
            result = []
            
            for call in calls:
                # Handle both string and dict types for call
                if not isinstance(call, dict):
                    continue
                    
                # Extract and format key call data
                processed_call = {
                    "id": call.get('id'),
                    "title": call.get('title'),
                    "date": call.get('date')
                }
                
                # Add optional fields if they exist
                if 'content' in call and isinstance(call['content'], dict):
                    processed_call["duration"] = call['content'].get('duration')
                
                # Add speakers if they exist
                speakers = []
                if 'speakers' in call and isinstance(call['speakers'], list):
                    for speaker in call['speakers']:
                        if isinstance(speaker, dict):
                            speaker_info = {
                                "name": speaker.get('name'),
                                "email": speaker.get('emailAddress')
                            }
                            
                            if 'isCompanyEmployee' in speaker:
                                speaker_info["role"] = "internal" if speaker.get('isCompanyEmployee') else "external"
                            
                            if 'speakingTime' in speaker:
                                speaker_info["talk_time"] = speaker.get('speakingTime')
                                
                            speakers.append(speaker_info)
                
                processed_call["speakers"] = speakers
                
                # Add media info if it exists
                if 'media' in call and isinstance(call['media'], dict):
                    processed_call["transcript_url"] = call['media'].get('transcriptUrl')
                    processed_call["recording_url"] = call['media'].get('recordingUrl')
                
                result.append(processed_call)
                
            return {
                "success": True,
                "results": result,
                "count": len(result)
            }
            
        elif query_type == 'topics':
            # Process topic data
            topics = raw_data.get('topics', [])
            return {
                "success": True,
                "results": topics,
                "count": len(topics)
            }
            
        elif query_type == 'stats':
            # Process statistics data
            stats = raw_data.get('stats', {})
            return {
                "success": True,
                "results": stats
            }
            
        else:
            # Default processing
            return {
                "success": True,
                "results": raw_data
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error processing Gong response: {str(e)}",
            "results": []
        }

# Main functions for different Gong API endpoints
def get_calls(credentials: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve call data from Gong API.
    
    Args:
        credentials (Dict[str, str]): Gong API credentials
        params (Dict[str, Any]): Parameters for call retrieval
        
    Returns:
        Dict[str, Any]: Structured call data
    """
    # Build query parameters for the endpoint
    query_params = []
    
    # Add date range if provided
    if params.get('from_date'):
        query_params.append(f"from={params.get('from_date')}")
    
    if params.get('to_date'):
        query_params.append(f"to={params.get('to_date')}")
    
    # Add limit if provided
    if params.get('limit'):
        query_params.append(f"limit={params.get('limit')}")
    
    # Construct endpoint with query params
    endpoint = "calls"
    if query_params:
        endpoint = f"{endpoint}?{'&'.join(query_params)}"
    
    # Make the GET request
    response = make_gong_request(
        endpoint=endpoint,
        method="GET",
        credentials=credentials
    )
    
    # Process the response
    return clean_gong_response(response, 'calls')

def get_call_topics(credentials: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve topic data for calls from Gong.
    
    Args:
        credentials (Dict[str, str]): Gong API credentials
        params (Dict[str, Any]): Parameters for topic retrieval
        
    Returns:
        Dict[str, Any]: Structured topic data
    """
    # Need call ID for this endpoint
    call_id = params.get('call_id')
    if not call_id:
        return {
            "success": False,
            "error": "call_id is required for topic retrieval",
            "results": []
        }
    
    # Make the request
    response = make_gong_request(
        endpoint=f"calls/{call_id}/topics",
        method="GET",
        credentials=credentials
    )
    
    # Process the response
    return clean_gong_response(response, 'topics')

def get_call_stats(credentials: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve statistics for calls from Gong.
    
    Args:
        credentials (Dict[str, str]): Gong API credentials
        params (Dict[str, Any]): Parameters for stats retrieval
        
    Returns:
        Dict[str, Any]: Structured stats data
    """
    # Format date range for the request
    from_date = params.get('from_date')
    to_date = params.get('to_date')
    
    # Default date range if not specified (last 30 days)
    if not from_date:
        to_date_obj = datetime.now()
        from_date_obj = to_date_obj - timedelta(days=30)
        from_date = from_date_obj.strftime("%Y-%m-%d")
        to_date = to_date_obj.strftime("%Y-%m-%d")
    elif not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    
    # Prepare request body
    body = {
        "filter": {
            "fromDateTime": f"{from_date}T00:00:00.000Z",
            "toDateTime": f"{to_date}T23:59:59.999Z"
        },
        "metricType": params.get('metric_type', 'callsCount')
    }
    
    # Add grouping if specified
    if params.get('group_by'):
        body['groupBy'] = params.get('group_by')
    
    # Add additional filters if provided
    if params.get('user_ids'):
        body['filter']['userIds'] = params.get('user_ids')
    
    # Make the request
    response = make_gong_request(
        endpoint="stats/activity",
        method="POST",
        credentials=credentials,
        body=body
    )
    
    # Process the response
    return clean_gong_response(response, 'stats')

# Main Lambda handler function
def get_gong_data(
    query_type: str = 'calls',
    date_range: Dict[str, str] = None,
    filters: Dict[str, Any] = None,
    call_id: str = None,
    debug: bool = False
) -> Dict[str, Any]:
    """
    Main function to retrieve data from Gong based on query type.
    Matches the Bedrock Agent function schema signature.
    
    Args:
        query_type (str): Type of data to retrieve (calls, topics, stats)
        date_range (Dict[str, str]): Time range for data retrieval
        filters (Dict[str, Any]): Additional filters to apply
        call_id (str): Specific call ID for detailed queries
        
    Returns:
        Dict[str, Any]: Structured data from Gong
    """
    try:
        # Set up default values
        if date_range is None:
            date_range = {}
        
        if filters is None:
            filters = {}
        
        # Handle string date_range (e.g., "7d", "30d", "1w")
        if isinstance(date_range, str):
            # Convert string date range to proper from/to format
            date_range = parse_date_range_string(date_range)
        
        # Use environment variables or defaults for these values
        secret_name = os.environ.get('GONG_CREDENTIALS_SECRET', 'gong-credentials')
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Get Gong credentials
        credentials = get_gong_credentials(secret_name, region_name)
        
        # Combine parameters
        params = {
            'from_date': date_range.get('from') if isinstance(date_range, dict) else None,
            'to_date': date_range.get('to') if isinstance(date_range, dict) else None,
            'call_id': call_id,
            **filters
        }
        
        # Call appropriate function based on query type
        if query_type == 'calls':
            return get_calls(credentials, params)
            
        elif query_type == 'topics':
            return get_call_topics(credentials, params)
            
        elif query_type == 'stats':
            return get_call_stats(credentials, params)
            
        else:
            return {
                "success": False,
                "error": f"Unknown query_type: {query_type}",
                "message": "Supported query types are: calls, topics, stats"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve data from Gong"
        }

def lambda_handler(event, context):
    """
    AWS Lambda handler for Gong data retrieval.
    Compatible with Bedrock Agent function calling format.
    
    Also supports a debug mode for troubleshooting credential issues.
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Handle Bedrock Agent invocation
        if 'actionGroup' in event and event.get('actionGroup') == 'gong_retrieval':
            action_name = event.get('action')
            
            if action_name == 'get_gong_data':
                body = event.get('body', {})
                parameters = body.get('parameters', {})
                
                # Extract parameters
                query_type = parameters.get('query_type', 'calls')
                date_range = parameters.get('date_range', {})
                filters = parameters.get('filters', {})
                call_id = parameters.get('call_id')
                
                # Call our function
                return get_gong_data(query_type, date_range, filters, call_id)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action_name}",
                    "message": "This Lambda only supports the 'get_gong_data' action."
                }
                
        # Handle direct invocation
        elif 'query_type' in event:
            # Direct Lambda invocation
            query_type = event.get('query_type', 'calls')
            date_range = event.get('date_range', {})
            filters = event.get('filters', {})
            call_id = event.get('call_id')
            debug = event.get('debug', False)
            
            # Special debug mode for credential troubleshooting
            if query_type == 'debug_credentials' and debug:
                try:
                    # Get environment variables
                    secret_name = os.environ.get('GONG_CREDENTIALS_SECRET', 'gong-credentials')
                    region_name = os.environ.get('AWS_REGION', 'us-east-1')
                    
                    # Try to get credentials
                    try:
                        credentials = get_gong_credentials(secret_name, region_name)
                        # Generate headers but mask the sensitive parts
                        headers = generate_gong_headers(credentials['access_key'], credentials['access_key_secret'])
                        masked_headers = headers.copy()
                        if 'Authorization' in masked_headers:
                            masked_headers['Authorization'] = masked_headers['Authorization'][:12] + '****'
                        if 'X-API-Signature' in masked_headers:
                            masked_headers['X-API-Signature'] = masked_headers['X-API-Signature'][:8] + '****'
                            
                        return {
                            'success': True,
                            'debug_info': {
                                'secret_name': secret_name,
                                'region_name': region_name,
                                'credentials_found': True,
                                'access_key_exists': 'access_key' in credentials,
                                'access_key_secret_exists': 'access_key_secret' in credentials,
                                'access_key_prefix': credentials.get('access_key', '')[:4] + '****' if 'access_key' in credentials else None,
                                'access_key_secret_prefix': credentials.get('access_key_secret', '')[:4] + '****' if 'access_key_secret' in credentials else None,
                                'generated_headers': masked_headers,
                                'environment_variables': {
                                    'GONG_CREDENTIALS_SECRET': os.environ.get('GONG_CREDENTIALS_SECRET', 'not_set'),
                                    'AWS_REGION': os.environ.get('AWS_REGION', 'not_set')
                                }
                            }
                        }
                    except Exception as cred_error:
                        return {
                            'success': False,
                            'error': str(cred_error),
                            'debug_info': {
                                'secret_name': secret_name,
                                'region_name': region_name,
                                'error_type': type(cred_error).__name__,
                                'environment_variables': {
                                    'GONG_CREDENTIALS_SECRET': os.environ.get('GONG_CREDENTIALS_SECRET', 'not_set'),
                                    'AWS_REGION': os.environ.get('AWS_REGION', 'not_set')
                                }
                            }
                        }
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'debug_info': {
                            'error_type': type(e).__name__
                        }
                    }
            
            # Normal operation
            return get_gong_data(query_type, date_range, filters, call_id)
            
        # Legacy parameter format for backward compatibility
        elif 'parameters' in event and isinstance(event['parameters'], list):
            params = {param.get('name'): param.get('value') for param in event['parameters']}
            query_type = params.get('query_type', 'calls')
            date_range = params.get('date_range', {})
            filters = params.get('filters', {})
            call_id = params.get('call_id')
            
            return get_gong_data(query_type, date_range, filters, call_id)
        
        # No recognizable format
        else:
            return {
                'success': False,
                'error': 'Invalid request format',
                'message': 'Request format not recognized. Please provide required parameters.'
            }
            
    except Exception as e:
        # Log the full error for debugging
        print(f"Lambda handler error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Return error response
        return {
            'success': False,
            'error': str(e),
            'message': 'An error occurred processing the Gong data request'
        }
