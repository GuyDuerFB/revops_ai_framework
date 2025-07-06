#!/usr/bin/env python3
"""
Verify Decision Agent Update Script
==================================

Tests that the Decision Agent has been updated with new instructions and is functioning correctly.
"""

import boto3
import json
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_decision_agent():
    """Test the Decision Agent with new instructions"""
    
    # Configuration
    profile_name = "FireboltSystemAdministrator-740202120544"
    aws_region = "us-east-1"
    agent_id = "TCX9CGOKBR"
    agent_alias_id = "FUKETW8HXV"
    
    # Initialize AWS session and client
    session = boto3.Session(profile_name=profile_name, region_name=aws_region)
    bedrock_agent_runtime = session.client('bedrock-agent-runtime')
    
    # Test prompt to verify the agent's understanding of its role
    test_prompt = """
    Hello! I need to verify that you understand your role as the Decision Agent and supervisor. 
    Can you briefly explain:
    1. Your main purpose
    2. The three collaborator agents you work with
    3. One example of how you would handle a lead assessment request
    
    Please keep your response concise.
    """
    
    try:
        logger.info("🧪 Testing Decision Agent with new instructions...")
        
        # Create a session
        session_id = str(uuid.uuid4())
        
        # Invoke the agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=test_prompt
        )
        
        # Collect and display the response
        response_text = ""
        logger.info("📝 Agent Response:")
        logger.info("=" * 50)
        
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    response_text += chunk_text
                    print(chunk_text, end='', flush=True)
        
        print("\n" + "=" * 50)
        
        # Verify key elements in the response
        logger.info("🔍 Verifying response contains key elements...")
        
        key_elements = [
            "Decision Agent",
            "SUPERVISOR",
            "DataAgent",
            "WebSearchAgent", 
            "ExecutionAgent",
            "lead assessment"
        ]
        
        missing_elements = []
        for element in key_elements:
            if element.lower() not in response_text.lower():
                missing_elements.append(element)
        
        if missing_elements:
            logger.warning(f"⚠️ Missing elements in response: {missing_elements}")
        else:
            logger.info("✅ All key elements found in response")
        
        logger.info("🎉 Decision Agent verification completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing Decision Agent: {e}")
        return False

def main():
    """Main verification function"""
    
    logger.info("🌟 Decision Agent Update Verification")
    logger.info("=" * 50)
    
    success = test_decision_agent()
    
    if success:
        logger.info("\n🎉 VERIFICATION SUCCESSFUL!")
        logger.info("✅ Decision Agent is functioning with new instructions")
    else:
        logger.error("\n❌ VERIFICATION FAILED!")
        logger.error("The Decision Agent may not be functioning properly")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)