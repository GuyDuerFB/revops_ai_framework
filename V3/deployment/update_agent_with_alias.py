#!/usr/bin/env python3
"""
Update Decision Agent Instructions with Alias Update

This is a production script for updating the Decision Agent (ID: TCX9CGOKBR) with new instructions
and updating the agent alias to point to the new version.

Usage:
    python3 update_agent_with_alias.py [--no-alias]
    
Arguments:
    --no-alias    Skip updating the agent alias (only update instructions)
"""

import boto3
import json
import logging
from pathlib import Path
import sys
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        return None
    
    with open(config_path, 'r') as f:
        return json.load(f)

def load_instructions():
    """Load instructions from the instructions.md file"""
    instructions_path = Path(__file__).parent.parent / "agents" / "decision_agent" / "instructions.md"
    if not instructions_path.exists():
        logger.error(f"Instructions file not found: {instructions_path}")
        return None
    
    with open(instructions_path, 'r') as f:
        return f.read()

def wait_for_agent_ready(bedrock_agent, agent_id, timeout=300):
    """Wait for agent to be in NOT_PREPARED or PREPARED state"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = bedrock_agent.get_agent(agentId=agent_id)
            status = response['agent']['agentStatus']
            
            if status in ['NOT_PREPARED', 'PREPARED']:
                logger.info(f"Agent status: {status}")
                return True
            elif status == 'FAILED':
                logger.error(f"Agent preparation failed")
                return False
            else:
                logger.info(f"Agent status: {status}, waiting...")
                time.sleep(10)
        except Exception as e:
            logger.error(f"Error checking agent status: {e}")
            time.sleep(10)
    
    logger.error(f"Timeout waiting for agent to be ready")
    return False

def wait_for_agent_prepared(bedrock_agent, agent_id, timeout=300):
    """Wait for agent to be in PREPARED state with a proper version"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = bedrock_agent.get_agent(agentId=agent_id)
            agent_info = response['agent']
            status = agent_info['agentStatus']
            
            if status == 'PREPARED':
                # Check if we have a proper version (not DRAFT)
                prepared_at = agent_info.get('preparedAt')
                if prepared_at:
                    logger.info(f"Agent prepared at: {prepared_at}")
                    return True
                else:
                    logger.info("Agent prepared but no version info yet, waiting...")
                    time.sleep(5)
            elif status == 'FAILED':
                logger.error(f"Agent preparation failed")
                return False
            else:
                logger.info(f"Agent status: {status}, waiting...")
                time.sleep(10)
        except Exception as e:
            logger.error(f"Error checking agent status: {e}")
            time.sleep(10)
    
    logger.error(f"Timeout waiting for agent to be prepared")
    return False

def update_agent_instructions(config, instructions, update_alias=True):
    """Update the Decision Agent instructions using AWS Bedrock"""
    
    # Get agent configuration
    decision_agent_config = config.get('decision_agent', {})
    agent_id = decision_agent_config.get('agent_id')
    agent_alias_id = decision_agent_config.get('agent_alias_id')
    
    if not agent_id:
        logger.error("Decision Agent ID not found in configuration")
        return False
    
    # Initialize AWS clients
    profile_name = config.get('profile_name')
    region_name = config.get('region_name', 'us-east-1')
    
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    bedrock_agent = session.client('bedrock-agent')
    
    try:
        # Get current agent details
        logger.info(f"Retrieving current agent details for ID: {agent_id}")
        get_response = bedrock_agent.get_agent(agentId=agent_id)
        agent_info = get_response['agent']
        
        logger.info(f"Current agent status: {agent_info['agentStatus']}")
        
        # Update agent with new instructions
        logger.info("Updating agent instructions...")
        description = agent_info.get('description', '')
        if not description:
            description = "RevOps Decision Agent - Updated with enhanced deal review flow"
        
        update_response = bedrock_agent.update_agent(
            agentId=agent_id,
            agentName=agent_info['agentName'],
            description=description,
            instruction=instructions,
            foundationModel=agent_info.get('foundationModel'),
            agentResourceRoleArn=agent_info.get('agentResourceRoleArn'),
            agentCollaboration=agent_info.get('agentCollaboration', 'SUPERVISOR'),
            idleSessionTTLInSeconds=agent_info.get('idleSessionTTLInSeconds', 1800)
        )
        
        logger.info(f"✅ Agent instructions updated successfully!")
        logger.info(f"Agent Status: {update_response['agent']['agentStatus']}")
        
        # Wait for agent to be ready for preparation
        if not wait_for_agent_ready(bedrock_agent, agent_id):
            logger.error("Agent not ready for preparation")
            return False
        
        # Prepare agent (creates a new version)
        logger.info("Preparing agent (creating new version)...")
        prepare_response = bedrock_agent.prepare_agent(agentId=agent_id)
        
        logger.info(f"✅ Agent prepared successfully!")
        logger.info(f"Agent Version: {prepare_response['agentVersion']}")
        logger.info(f"Preparation Status: {prepare_response['preparedAt']}")
        
        # Wait for agent to be fully prepared
        if not wait_for_agent_prepared(bedrock_agent, agent_id):
            logger.error("Agent preparation did not complete properly")
            return False
        
        # Get the actual version number from the prepared agent
        agent_versions = bedrock_agent.list_agent_versions(agentId=agent_id)
        latest_version = None
        for version in agent_versions['agentVersionSummaries']:
            if version['agentStatus'] == 'PREPARED':
                latest_version = version['agentVersion']
                break
        
        if not latest_version:
            logger.error("Could not find a prepared version")
            return False
        
        new_version = latest_version
        logger.info(f"Using prepared version: {new_version}")
        
        # Update agent alias if requested
        if update_alias and agent_alias_id:
            logger.info(f"Updating agent alias {agent_alias_id} to point to version {new_version}...")
            
            # Get current alias details
            alias_response = bedrock_agent.get_agent_alias(
                agentId=agent_id,
                agentAliasId=agent_alias_id
            )
            alias_info = alias_response['agentAlias']
            
            # Update alias to point to new version
            alias_description = alias_info.get('description', '')
            if not alias_description:
                alias_description = "RevOps Decision Agent - Enhanced deal review flow"
            
            update_alias_response = bedrock_agent.update_agent_alias(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                agentAliasName=alias_info['agentAliasName'],
                description=alias_description,
                routingConfiguration=[
                    {
                        'agentVersion': new_version
                    }
                ]
            )
            
            logger.info(f"✅ Agent alias updated successfully!")
            logger.info(f"Alias Status: {update_alias_response['agentAlias']['agentAliasStatus']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating agent instructions: {str(e)}")
        return False

def main():
    """Main function to update Decision Agent instructions"""
    
    logger.info("🔄 Decision Agent Instructions Update with Alias")
    logger.info("=" * 60)
    
    # Parse command line arguments
    update_alias = True
    if len(sys.argv) > 1 and sys.argv[1] == "--no-alias":
        update_alias = False
        logger.info("🔹 Alias update disabled")
    
    # Load configuration
    config = load_config()
    if not config:
        sys.exit(1)
    
    # Load instructions
    instructions = load_instructions()
    if not instructions:
        sys.exit(1)
    
    logger.info(f"📋 Instructions loaded: {len(instructions)} characters")
    
    # Update agent
    success = update_agent_instructions(config, instructions, update_alias)
    
    if success:
        logger.info("\n🎉 UPDATE SUCCESSFUL!")
        logger.info("✅ Decision Agent instructions updated")
        logger.info("✅ New agent version prepared")
        if update_alias:
            logger.info("✅ Agent alias updated to new version")
        logger.info("\n📋 Next Steps:")
        logger.info("1. Test the updated agent with a sample query")
        logger.info("2. Monitor agent performance and responses")
        logger.info("3. Verify the new instructions are working correctly")
    else:
        logger.error("\n❌ UPDATE FAILED!")
        logger.error("Please check the logs above for error details")
        sys.exit(1)

if __name__ == "__main__":
    main()