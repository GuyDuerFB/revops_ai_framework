#!/usr/bin/env python3
"""
Update WebSearch Lambda Function
===============================

Updates the WebSearch Lambda function with improved search capabilities.
"""

import boto3
import json
import logging
import os
import zipfile
import shutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def update_websearch_lambda():
    """Update WebSearch Lambda with improved functionality"""
    
    logger.info("🚀 Updating WebSearch Lambda Function")
    logger.info("=" * 50)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    lambda_client = session.client('lambda')
    
    function_name = "revops-web-search"
    
    # Paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_search_dir = os.path.join(project_root, "tools", "web_search")
    improved_lambda_path = os.path.join(web_search_dir, "lambda_function_improved.py")
    
    # Create deployment package
    deployment_dir = "/tmp/websearch_lambda_deployment"
    if os.path.exists(deployment_dir):
        shutil.rmtree(deployment_dir)
    os.makedirs(deployment_dir)
    
    try:
        # Copy improved Lambda function
        logger.info("📦 Creating deployment package...")
        
        # Copy the improved lambda function as lambda_function.py
        shutil.copy2(improved_lambda_path, os.path.join(deployment_dir, "lambda_function.py"))
        
        # Create ZIP file
        zip_path = "/tmp/websearch_lambda.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(deployment_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, deployment_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"✅ Created deployment package: {zip_path}")
        
        # Update Lambda function
        logger.info("🔄 Updating Lambda function code...")
        
        with open(zip_path, 'rb') as zip_file:
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_file.read()
            )
        
        logger.info(f"✅ Lambda function updated successfully")
        logger.info(f"📊 Function ARN: {response['FunctionArn']}")
        logger.info(f"📊 Runtime: {response['Runtime']}")
        logger.info(f"📊 Code Size: {response['CodeSize']} bytes")
        
        # Test the updated function
        logger.info("🧪 Testing updated Lambda function...")
        
        test_payload = {
            "function": "search_web",
            "actionGroup": "web_search",
            "parameters": [
                {"name": "query", "value": "WINN.AI company information"},
                {"name": "num_results", "value": "3"}
            ]
        }
        
        test_response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        test_result = json.loads(test_response['Payload'].read().decode())
        
        # Extract search results
        if "response" in test_result and "functionResponse" in test_result["response"]:
            func_response = test_result["response"]["functionResponse"]
            if "responseBody" in func_response and "TEXT" in func_response["responseBody"]:
                search_data_json = func_response["responseBody"]["TEXT"]["body"]
                search_data = json.loads(search_data_json)
                
                logger.info(f"📊 Test Results:")
                logger.info(f"  ✅ Success: {search_data.get('success')}")
                logger.info(f"  📝 Query: {search_data.get('query')}")
                logger.info(f"  📊 Results Count: {search_data.get('result_count')}")
                logger.info(f"  🔍 Search Methods: {search_data.get('search_methods')}")
                
                if search_data.get('results'):
                    for i, result in enumerate(search_data['results'][:2]):
                        logger.info(f"    📄 Result {i+1}: {result.get('title')[:50]}...")
                        logger.info(f"       Content: {result.get('content')[:100]}...")
                
                if search_data.get('success') and search_data.get('result_count', 0) > 0:
                    logger.info("🎉 Enhanced Lambda function is working correctly!")
                    return True
                else:
                    logger.warning("⚠️ Lambda function updated but results may need improvement")
                    return True
        else:
            logger.error("❌ Unexpected response format from updated Lambda")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating Lambda function: {e}")
        return False
    
    finally:
        # Cleanup
        if os.path.exists(deployment_dir):
            shutil.rmtree(deployment_dir)
        if os.path.exists(zip_path):
            os.remove(zip_path)

def main():
    success = update_websearch_lambda()
    
    if success:
        logger.info("\n" + "=" * 50)
        logger.info("🎉 WebSearch Lambda Update Completed Successfully!")
        logger.info("📋 Next Steps:")
        logger.info("  1. Test WebSearch Agent with real queries")
        logger.info("  2. Verify enhanced search results quality")
        logger.info("  3. Test lead assessment workflow")
    else:
        logger.error("❌ WebSearch Lambda update failed")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)