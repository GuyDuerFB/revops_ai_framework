#!/usr/bin/env python3
"""
Test Enhanced System
===================

Test the enhanced RevOps AI Framework with business logic and knowledge base integration.

Author: Claude (Anthropic)
Version: 1.0
"""

import boto3
import json
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_data_agent():
    """Test the enhanced Data Agent with business logic integration"""
    
    profile_name = "revops-dev-profile"
    aws_region = "us-east-1"
    
    session = boto3.Session(profile_name=profile_name, region_name=aws_region)
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load configuration
    config_path = "config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('data_agent', {}).get('agent_id')
    agent_alias_id = config.get('data_agent', {}).get('agent_alias_id')
    
    if not agent_id or not agent_alias_id:
        logger.error("❌ Data Agent configuration not found")
        return False
    
    logger.info(f"🧪 Testing enhanced Data Agent: {agent_id}")
    
    # Test query that should use business logic
    test_query = """
    I need a revenue analysis for Q3 2025 with proper temporal analysis. 
    Please provide customer segmentation by type (Commit, PLG, Prospect) 
    and account for the fact that Q3 2025 only has 4 days of data so far.
    """
    
    try:
        logger.info("📤 Sending test query to Data Agent...")
        
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=f"test-enhanced-{int(time.time())}",
            inputText=test_query
        )
        
        # Collect response
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    full_response += chunk['bytes'].decode('utf-8')
        
        logger.info("📥 Received response from Data Agent")
        logger.info(f"📊 Response preview: {full_response[:500]}...")
        
        # Check if response includes expected business logic elements
        expected_elements = [
            "customer_type",
            "temporal",
            "daily_rate",
            "Q3 2025",
            "4 days"
        ]
        
        found_elements = []
        for element in expected_elements:
            if element.lower() in full_response.lower():
                found_elements.append(element)
        
        logger.info(f"✅ Found {len(found_elements)}/{len(expected_elements)} expected business logic elements")
        logger.info(f"📋 Found elements: {found_elements}")
        
        return len(found_elements) >= 3  # At least 3 elements indicate proper integration
        
    except Exception as e:
        logger.error(f"❌ Error testing Data Agent: {e}")
        return False

def test_knowledge_base():
    """Test knowledge base query functionality"""
    
    profile_name = "revops-dev-profile"
    aws_region = "us-east-1"
    
    session = boto3.Session(profile_name=profile_name, region_name=aws_region)
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load configuration
    config_path = "config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    kb_id = config.get('knowledge_base', {}).get('knowledge_base_id')
    
    if not kb_id:
        logger.error("❌ Knowledge base configuration not found")
        return False
    
    logger.info(f"🧪 Testing enhanced Knowledge Base: {kb_id}")
    
    try:
        # Test knowledge base retrieval
        response = bedrock_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                'text': 'customer classification types commit PLG prospect'
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 5
                }
            }
        )
        
        results = response.get('retrievalResults', [])
        logger.info(f"📋 Knowledge base returned {len(results)} results")
        
        if results:
            for i, result in enumerate(results[:3]):  # Show first 3 results
                content_preview = result.get('content', {}).get('text', '')[:200]
                score = result.get('score', 0)
                logger.info(f"📄 Result {i+1} (score: {score:.3f}): {content_preview}...")
        
        return len(results) > 0
        
    except Exception as e:
        logger.error(f"❌ Error testing Knowledge Base: {e}")
        return False

def main():
    """Run comprehensive tests"""
    logger.info("🚀 Starting Enhanced RevOps AI Framework Tests")
    logger.info("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Data Agent with enhanced instructions
    logger.info("🧪 Test 1: Enhanced Data Agent")
    if test_data_agent():
        logger.info("✅ Data Agent test PASSED")
        tests_passed += 1
    else:
        logger.error("❌ Data Agent test FAILED")
    
    logger.info("-" * 40)
    
    # Test 2: Knowledge Base integration
    logger.info("🧪 Test 2: Enhanced Knowledge Base")
    if test_knowledge_base():
        logger.info("✅ Knowledge Base test PASSED")
        tests_passed += 1
    else:
        logger.error("❌ Knowledge Base test FAILED")
    
    logger.info("=" * 60)
    logger.info(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        logger.info("🎉 ALL TESTS PASSED - Enhanced system is working!")
    else:
        logger.warning(f"⚠️ {total_tests - tests_passed} test(s) failed - check configuration")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)