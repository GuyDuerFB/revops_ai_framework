#!/usr/bin/env python3
"""
Test Lambda Function Directly
============================

Test the WebSearch Lambda function directly to see what it's returning.
"""

import boto3
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_lambda_direct():
    """Test Lambda function directly"""
    
    logger.info("🧪 Testing WebSearch Lambda Function Directly")
    logger.info("=" * 60)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    lambda_client = session.client('lambda')
    
    function_name = "revops-web-search"
    
    # Test with Bedrock Agent format
    test_payload = {
        "function": "search_web",
        "actionGroup": "web_search_v3", 
        "parameters": [
            {"name": "query", "type": "string", "value": "WINN.AI company"},
            {"name": "num_results", "type": "string", "value": "3"}
        ]
    }
    
    try:
        logger.info("📞 Invoking Lambda function...")
        logger.info(f"📋 Payload: {json.dumps(test_payload, indent=2)}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        # Read the response
        response_payload = response['Payload'].read().decode()
        result = json.loads(response_payload)
        
        logger.info(f"📊 Lambda response status: {response.get('StatusCode')}")
        logger.info(f"📋 Full Lambda response: {json.dumps(result, indent=2)}")
        
        # Check if there are actual search results
        if "response" in result and "functionResponse" in result["response"]:
            func_response = result["response"]["functionResponse"]
            if "responseBody" in func_response and "TEXT" in func_response["responseBody"]:
                response_body = func_response["responseBody"]["TEXT"]["body"]
                search_data = json.loads(response_body)
                
                logger.info(f"\n📊 Search Results Analysis:")
                logger.info(f"   Success: {search_data.get('success')}")
                logger.info(f"   Query: {search_data.get('query')}")
                logger.info(f"   Result count: {search_data.get('result_count')}")
                logger.info(f"   Search methods: {search_data.get('search_methods')}")
                
                if search_data.get('results'):
                    logger.info(f"   First result title: {search_data['results'][0].get('title')}")
                    logger.info(f"   First result content: {search_data['results'][0].get('content')[:200]}...")
                    logger.info(f"   First result URL: {search_data['results'][0].get('url')}")
                else:
                    logger.warning("❌ No search results found!")
                
                return search_data.get('success', False) and search_data.get('result_count', 0) > 0
        else:
            logger.error("❌ Unexpected Lambda response format")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing Lambda: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_different_formats():
    """Test Lambda with different input formats"""
    
    logger.info("\n🔄 Testing Different Input Formats")
    logger.info("=" * 50)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    lambda_client = session.client('lambda')
    
    function_name = "revops-web-search"
    
    # Try different payload formats
    formats = [
        {
            "name": "Bedrock Agent Format 1",
            "payload": {
                "function": "search_web",
                "parameters": [
                    {"name": "query", "value": "WINN.AI company"},
                    {"name": "num_results", "value": "3"}
                ]
            }
        },
        {
            "name": "Bedrock Agent Format 2", 
            "payload": {
                "actionGroup": "web_search_v3",
                "function": "search_web",
                "parameters": [
                    {"name": "query", "type": "string", "value": "WINN.AI company"},
                    {"name": "num_results", "type": "string", "value": "3"}
                ]
            }
        },
        {
            "name": "Direct Format",
            "payload": {
                "query": "WINN.AI company",
                "num_results": "3"
            }
        }
    ]
    
    for fmt in formats:
        try:
            logger.info(f"\n🧪 Testing {fmt['name']}...")
            
            response = lambda_client.invoke(
                FunctionName=function_name,
                Payload=json.dumps(fmt['payload'])
            )
            
            response_payload = response['Payload'].read().decode()
            result = json.loads(response_payload)
            
            logger.info(f"   Status: {response.get('StatusCode')}")
            
            # Quick analysis
            if "error" in result:
                logger.error(f"   ❌ Error: {result['error']}")
            elif "response" in result:
                logger.info(f"   ✅ Got response structure")
            else:
                logger.info(f"   📋 Response keys: {list(result.keys())}")
                
        except Exception as e:
            logger.error(f"   ❌ Failed: {e}")

def main():
    success = test_lambda_direct()
    
    if success:
        logger.info("\n🎉 Lambda function is working and returning search results!")
        logger.info("The issue may be in how the agent processes the results.")
    else:
        logger.error("\n❌ Lambda function is not returning valid search results")
        logger.info("This explains why the agent provides generic responses.")
    
    # Test different formats to understand the issue better
    test_different_formats()
    
    return success

if __name__ == "__main__":
    main()