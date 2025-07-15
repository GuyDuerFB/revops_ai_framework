#!/usr/bin/env python3
"""
Test script to verify inference profile creation for Claude 3.7
"""

import boto3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_inference_profile_creation():
    """Test inference profile creation"""
    
    # Initialize AWS clients
    profile_name = "FireboltSystemAdministrator-740202120544"
    region_name = "us-east-1"
    
    session = boto3.Session(profile_name=profile_name)
    bedrock_client = session.client('bedrock', region_name=region_name)
    
    inference_profile_name = "claude-3-7-revops-profile"
    model_id = "anthropic.claude-3-7-sonnet-20250219-v1:0"
    
    try:
        # Check if inference profile already exists
        logger.info(f"Checking if inference profile '{inference_profile_name}' exists...")
        
        try:
            response = bedrock_client.get_inference_profile(
                inferenceProfileIdentifier=inference_profile_name
            )
            logger.info(f"✅ Inference profile already exists: {response['inferenceProfileId']}")
            return True
        except bedrock_client.exceptions.ResourceNotFoundException:
            logger.info("❌ Inference profile does not exist, would need to create it")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error checking inference profile: {str(e)}")
        return False

def test_model_availability():
    """Test if Claude 3.7 model is available"""
    
    profile_name = "FireboltSystemAdministrator-740202120544"
    region_name = "us-east-1"
    
    session = boto3.Session(profile_name=profile_name)
    bedrock_client = session.client('bedrock', region_name=region_name)
    
    try:
        # List available foundation models
        logger.info("Checking available foundation models...")
        
        response = bedrock_client.list_foundation_models()
        
        claude_models = [model for model in response['modelSummaries'] 
                        if 'claude' in model['modelId'].lower()]
        
        logger.info(f"Found {len(claude_models)} Claude models:")
        for model in claude_models:
            logger.info(f"  - {model['modelId']}")
        
        # Check if Claude 3.7 is available
        claude_3_7_model = "anthropic.claude-3-7-sonnet-20250219-v1:0"
        is_available = any(model['modelId'] == claude_3_7_model for model in claude_models)
        
        if is_available:
            logger.info(f"✅ Claude 3.7 model is available: {claude_3_7_model}")
        else:
            logger.warning(f"⚠️  Claude 3.7 model not found: {claude_3_7_model}")
            logger.info("Available Claude models:")
            for model in claude_models:
                logger.info(f"  - {model['modelId']}")
        
        return is_available
        
    except Exception as e:
        logger.error(f"❌ Error checking model availability: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing Claude 3.7 and Inference Profile Setup")
    logger.info("=" * 60)
    
    # Test 1: Check model availability
    model_available = test_model_availability()
    
    # Test 2: Check inference profile
    profile_exists = test_inference_profile_creation()
    
    logger.info("=" * 60)
    if model_available and profile_exists:
        logger.info("✅ All tests passed! Claude 3.7 and inference profile are ready.")
    elif model_available:
        logger.info("⚠️  Claude 3.7 model is available but inference profile needs to be created.")
    else:
        logger.error("❌ Issues detected with Claude 3.7 setup.")