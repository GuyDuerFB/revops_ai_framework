#!/usr/bin/env python3
"""
Update Agent Instructions Script
==============================

Updates agent instructions to use the enhanced knowledge base.

Author: Claude (Anthropic)
Version: 1.0
"""

import boto3
import json
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    # Initialize AWS clients
    profile_name = "revops-dev-profile"
    aws_region = "us-east-1"
    account_id = "740202120544"
    
    session = boto3.Session(profile_name=profile_name, region_name=aws_region)
    bedrock_agent_client = session.client('bedrock-agent')
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Update Decision Agent
    decision_agent_id = config.get('decision_agent', {}).get('agent_id')
    if decision_agent_id:
        logger.info(f"🔄 Updating Decision Agent: {decision_agent_id}")
        
        instructions_path = os.path.join(project_root, "agents/decision_agent/instructions_v2.md")
        if os.path.exists(instructions_path):
            with open(instructions_path, 'r') as f:
                new_instructions = f.read()
            
            try:
                bedrock_agent_client.update_agent(
                    agentId=decision_agent_id,
                    agentName="revops-decision-agent-enhanced",
                    description="Enhanced Decision Agent with knowledge base integration",
                    instruction=new_instructions,
                    foundationModel="anthropic.claude-3-5-sonnet-20240620-v1:0",
                    agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/AmazonBedrockExecutionRoleForAgents_revops"
                )
                
                bedrock_agent_client.prepare_agent(agentId=decision_agent_id)
                logger.info("✅ Decision Agent updated with enhanced instructions")
            except Exception as e:
                logger.error(f"❌ Error updating Decision Agent: {e}")
        else:
            logger.warning("⚠️ Decision Agent instructions_v2.md not found")
    
    # Update Data Agent
    data_agent_id = config.get('data_agent', {}).get('agent_id')
    if data_agent_id:
        logger.info(f"🔄 Updating Data Agent: {data_agent_id}")
        
        instructions_path = os.path.join(project_root, "agents/data_agent/instructions_v2.md")
        if os.path.exists(instructions_path):
            with open(instructions_path, 'r') as f:
                new_instructions = f.read()
            
            try:
                bedrock_agent_client.update_agent(
                    agentId=data_agent_id,
                    agentName="revops-data-agent-enhanced",
                    description="Enhanced Data Agent with business logic integration",
                    instruction=new_instructions,
                    foundationModel="anthropic.claude-3-5-sonnet-20240620-v1:0",
                    agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/AmazonBedrockExecutionRoleForAgents_revops"
                )
                
                bedrock_agent_client.prepare_agent(agentId=data_agent_id)
                logger.info("✅ Data Agent updated with enhanced instructions")
            except Exception as e:
                logger.error(f"❌ Error updating Data Agent: {e}")
        else:
            logger.warning("⚠️ Data Agent instructions_v2.md not found")
    
    logger.info("🎉 Agent instruction updates completed!")

if __name__ == "__main__":
    main()