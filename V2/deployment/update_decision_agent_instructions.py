#!/usr/bin/env python3
"""
Update Decision Agent Instructions Script
========================================

Updates the Decision Agent (TCX9CGOKBR) with new instructions from the instructions.md file.

Author: Claude (Anthropic)
Version: 1.0
"""

import boto3
import json
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    """Update Decision Agent with new instructions"""
    
    # Configuration from your requirements
    profile_name = "FireboltSystemAdministrator-740202120544"
    aws_region = "us-east-1"
    account_id = "740202120544"
    decision_agent_id = "TCX9CGOKBR"
    
    # Initialize AWS session and client
    logger.info(f"🔧 Initializing AWS session with profile: {profile_name}")
    session = boto3.Session(profile_name=profile_name, region_name=aws_region)
    bedrock_agent_client = session.client('bedrock-agent')
    
    # Load instructions file (using concise version to stay within 20k character limit)
    instructions_path = "/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V2/agents/decision_agent/instructions_concise.md"
    logger.info(f"📖 Reading instructions from: {instructions_path}")
    
    if not os.path.exists(instructions_path):
        logger.error(f"❌ Instructions file not found: {instructions_path}")
        return False
    
    with open(instructions_path, 'r', encoding='utf-8') as f:
        new_instructions = f.read()
    
    logger.info(f"📝 Instructions loaded ({len(new_instructions)} characters)")
    
    # Load current agent configuration for reference
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    decision_config = config.get('decision_agent', {})
    
    try:
        # Update the Decision Agent
        logger.info(f"🔄 Updating Decision Agent: {decision_agent_id}")
        
        update_response = bedrock_agent_client.update_agent(
            agentId=decision_agent_id,
            agentName="revops-decision-agent-v2",
            description=decision_config.get('description', 'Decision Agent for RevOps AI Framework with temporal analysis and business logic awareness'),
            instruction=new_instructions,
            foundationModel=decision_config.get('foundation_model', 'anthropic.claude-3-5-sonnet-20240620-v1:0'),
            agentResourceRoleArn=config.get('execution_role_arn', f"arn:aws:iam::{account_id}:role/AmazonBedrockExecutionRoleForAgents_revops"),
            agentCollaboration=decision_config.get('agent_collaboration', 'SUPERVISOR')
        )
        
        logger.info("✅ Decision Agent updated successfully")
        logger.info(f"📋 Agent Version: {update_response.get('agent', {}).get('agentVersion', 'Unknown')}")
        
        # Prepare the agent (this creates a new version)
        logger.info("🔄 Preparing agent (creating new version)...")
        prepare_response = bedrock_agent_client.prepare_agent(agentId=decision_agent_id)
        
        logger.info("✅ Agent prepared successfully")
        logger.info(f"📋 Prepared Version: {prepare_response.get('agentVersion', 'Unknown')}")
        logger.info(f"📋 Preparation Status: {prepare_response.get('agentStatus', 'Unknown')}")
        
        # Get agent details for confirmation
        agent_details = bedrock_agent_client.get_agent(agentId=decision_agent_id)
        logger.info(f"📋 Current Agent Status: {agent_details.get('agent', {}).get('agentStatus', 'Unknown')}")
        
        logger.info("🎉 Decision Agent instruction update completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating Decision Agent: {e}")
        logger.error(f"Error details: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)