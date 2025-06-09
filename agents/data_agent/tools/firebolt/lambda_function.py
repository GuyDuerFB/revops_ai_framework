import json
from query_executor import execute_firebolt_query

def lambda_handler(event, context):
    """
    AWS Lambda handler for Firebolt queries using REST API
    """
    try:
        # Extract parameters from the event
        query = event.get('query')
        secret_name = event.get('secret_name', 'firebolt-api-credentials')
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
        
        # Log execution details
        print(f"Executing Firebolt query: {query[:100]}...")  # Log first 100 chars
        print(f"Using secret: {secret_name}")
        print(f"Region: {region_name}")
        
        # Execute the query using REST API
        # Configuration will come from environment variables
        result = execute_firebolt_query(query, secret_name, region_name)
        
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