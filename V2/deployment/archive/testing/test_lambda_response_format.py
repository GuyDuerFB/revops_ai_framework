#!/usr/bin/env python3
"""
Test Lambda Response Format
==========================

Tests the exact response format from Lambda and compares with Bedrock expectations.
"""

import boto3
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_lambda_response_formats():
    """Test different Lambda response formats"""
    
    logger.info("🧪 Testing Lambda Response Formats")
    logger.info("=" * 50)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    lambda_client = session.client('lambda')
    
    function_name = "revops-web-search"
    
    # Test different payload formats
    test_payloads = [
        {
            "name": "Bedrock Agent New Format",
            "payload": {
                "function": "search_web",
                "actionGroup": "web_search",
                "parameters": [
                    {"name": "query", "value": "WINN.AI test"},
                    {"name": "num_results", "value": "3"}
                ]
            }
        },
        {
            "name": "Bedrock Agent Old Format", 
            "payload": {
                "actionGroup": "web_search",
                "action": "search_web",
                "body": {
                    "parameters": {
                        "query": "WINN.AI test",
                        "num_results": "3"
                    }
                }
            }
        },
        {
            "name": "Direct Query Format",
            "payload": {
                "query": "WINN.AI test",
                "num_results": "3"
            }
        }
    ]
    
    for test in test_payloads:
        logger.info(f"\n🔍 Testing: {test['name']}")
        logger.info(f"📤 Payload: {json.dumps(test['payload'], indent=2)}")
        
        try:
            response = lambda_client.invoke(
                FunctionName=function_name,
                Payload=json.dumps(test['payload'])
            )
            
            result = json.loads(response['Payload'].read().decode())
            
            logger.info(f"📥 Response Status: {response['StatusCode']}")
            logger.info(f"📥 Response Preview: {json.dumps(result, indent=2)[:500]}...")
            
            # Analyze response structure
            response_analysis = {
                "has_messageVersion": "messageVersion" in result,
                "has_response": "response" in result,
                "has_actionGroup": "actionGroup" in result.get("response", {}),
                "has_function": "function" in result.get("response", {}),
                "has_functionResponse": "functionResponse" in result.get("response", {}),
                "has_responseBody": "responseBody" in result.get("response", {}).get("functionResponse", {}),
                "has_TEXT": "TEXT" in result.get("response", {}).get("functionResponse", {}).get("responseBody", {}),
                "has_body": "body" in result.get("response", {}).get("functionResponse", {}).get("responseBody", {}).get("TEXT", {})
            }
            
            logger.info(f"📊 Response Structure Analysis:")
            for key, value in response_analysis.items():
                status = "✅" if value else "❌"
                logger.info(f"  {status} {key}: {value}")
            
            # Check if response follows correct Bedrock format
            is_correct_format = all([
                response_analysis["has_messageVersion"],
                response_analysis["has_response"], 
                response_analysis["has_functionResponse"],
                response_analysis["has_responseBody"]
            ])
            
            logger.info(f"🎯 Correct Bedrock Format: {'✅ YES' if is_correct_format else '❌ NO'}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    # Check what the actual search data looks like
    logger.info(f"\n🔍 Testing Actual Search Data Extraction")
    
    try:
        test_payload = {
            "function": "search_web",
            "actionGroup": "web_search",
            "parameters": [
                {"name": "query", "value": "WINN.AI company"},
                {"name": "num_results", "value": "3"}
            ]
        }
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read().decode())
        
        # Extract the actual search data
        if "response" in result and "functionResponse" in result["response"]:
            func_response = result["response"]["functionResponse"]
            if "responseBody" in func_response and "TEXT" in func_response["responseBody"]:
                search_data_json = func_response["responseBody"]["TEXT"]["body"]
                search_data = json.loads(search_data_json)
                
                logger.info(f"📊 Extracted Search Data:")
                logger.info(f"  Success: {search_data.get('success')}")
                logger.info(f"  Query: {search_data.get('query')}")
                logger.info(f"  Results Count: {search_data.get('result_count')}")
                logger.info(f"  Results: {len(search_data.get('results', []))}")
                
                if search_data.get('results'):
                    for i, result_item in enumerate(search_data['results'][:2]):
                        logger.info(f"    Result {i+1}: {result_item.get('title')[:50]}...")
                
                logger.info(f"✅ Search function is working and returning data!")
                
    except Exception as e:
        logger.error(f"❌ Error extracting search data: {e}")

def main():
    test_lambda_response_formats()

if __name__ == "__main__":
    main()