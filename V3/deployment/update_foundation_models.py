#!/usr/bin/env python3
"""
Update Foundation Models for RevOps AI Framework Agents
======================================================

Script to update the foundation models for decision and data agents to Claude 3.7 Sonnet.
"""

import boto3
import json
import logging
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AgentModelUpdater:
    """Updates foundation models for Bedrock agents"""
    
    def __init__(self, config_file='config.json'):
        """Initialize with configuration"""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.session = boto3.Session(profile_name=self.config['profile_name'])
        self.bedrock_client = self.session.client('bedrock-agent', region_name=self.config['region_name'])
        
        self.new_model = "anthropic.claude-3-7-sonnet-20250219-v1:0"
        
    def update_agent_model(self, agent_name, agent_config):
        """Update a single agent's foundation model"""
        agent_id = agent_config['agent_id']
        current_model = agent_config.get('foundation_model', 'unknown')
        
        logger.info(f"🔄 Updating {agent_name} (ID: {agent_id})")
        logger.info(f"   Current model: {current_model}")
        logger.info(f"   New model: {self.new_model}")
        
        # Check if model is already updated
        if current_model == self.new_model:
            logger.info(f"   ✅ Agent already using target model")
            return True
        
        try:
            # Get current agent configuration
            response = self.bedrock_client.get_agent(agentId=agent_id)
            agent_details = response['agent']
            
            # Build update parameters - start with required fields
            update_params = {
                'agentId': agent_id,
                'agentName': agent_details['agentName'],
                'foundationModel': self.new_model,
                'instruction': agent_details['instruction'],
                'description': agent_details.get('description', ''),
                'idleSessionTTLInSeconds': agent_details.get('idleSessionTTLInSeconds', 1800),
                'agentResourceRoleArn': agent_details['agentResourceRoleArn']
            }
            
            # Handle customer encryption key if present
            if 'customerEncryptionKeyArn' in agent_details:
                update_params['customerEncryptionKeyArn'] = agent_details['customerEncryptionKeyArn']
            
            # For decision agent, preserve collaboration settings
            if agent_name == 'Decision Agent':
                if 'agentCollaboration' in agent_details:
                    update_params['agentCollaboration'] = agent_details['agentCollaboration']
            
            # Skip prompt override configuration to avoid conflicts
            logger.info(f"   📝 Updating agent without prompt override configuration")
            
            # Update the agent
            update_response = self.bedrock_client.update_agent(**update_params)
            
            logger.info(f"   ✅ Agent updated successfully")
            logger.info(f"   Status: {update_response['agent']['agentStatus']}")
            
            # Wait for the update to complete
            self.wait_for_agent_status(agent_id, 'NOT_PREPARED')
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to update {agent_name}: {str(e)}")
            return False
    
    def prepare_agent(self, agent_name, agent_id):
        """Prepare the agent after model update"""
        logger.info(f"🔧 Preparing {agent_name} (ID: {agent_id})")
        
        try:
            # Prepare the agent
            response = self.bedrock_client.prepare_agent(agentId=agent_id)
            
            logger.info(f"   ✅ Agent preparation started")
            logger.info(f"   Status: {response['agentStatus']}")
            
            # Wait for preparation to complete
            self.wait_for_agent_status(agent_id, 'PREPARED')
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Failed to prepare {agent_name}: {str(e)}")
            return False
    
    def wait_for_agent_status(self, agent_id, target_status):
        """Wait for agent to reach target status"""
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.bedrock_client.get_agent(agentId=agent_id)
                current_status = response['agent']['agentStatus']
                
                if current_status == target_status:
                    logger.info(f"   ✅ Agent reached status: {target_status}")
                    return True
                elif current_status == 'FAILED':
                    logger.error(f"   ❌ Agent failed to reach target status")
                    return False
                
                logger.info(f"   ⏳ Current status: {current_status}, waiting for: {target_status}")
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"   ❌ Error checking agent status: {str(e)}")
                return False
        
        logger.error(f"   ⏰ Timeout waiting for agent to reach status: {target_status}")
        return False
    
    def update_config_file(self):
        """Update the config file with new model information"""
        logger.info("📝 Updating configuration file")
        
        # Update the config
        self.config['data_agent']['foundation_model'] = self.new_model
        self.config['decision_agent']['foundation_model'] = self.new_model
        
        # Save the updated config
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
        
        logger.info("   ✅ Configuration file updated")
    
    def run_update(self):
        """Run the complete model update process"""
        logger.info("🚀 Starting Foundation Model Update Process")
        logger.info("=" * 70)
        logger.info(f"New model: {self.new_model}")
        logger.info("=" * 70)
        
        success_count = 0
        total_agents = 0
        
        # Update Data Agent
        if 'data_agent' in self.config:
            total_agents += 1
            if self.update_agent_model('Data Agent', self.config['data_agent']):
                if self.prepare_agent('Data Agent', self.config['data_agent']['agent_id']):
                    success_count += 1
        
        # Update Decision Agent
        if 'decision_agent' in self.config:
            total_agents += 1
            if self.update_agent_model('Decision Agent', self.config['decision_agent']):
                if self.prepare_agent('Decision Agent', self.config['decision_agent']['agent_id']):
                    success_count += 1
        
        # Update configuration file if all updates succeeded
        if success_count == total_agents:
            self.update_config_file()
            
            logger.info("\n🎉 MODEL UPDATE SUCCESSFUL!")
            logger.info(f"✅ Updated {success_count}/{total_agents} agents")
            logger.info(f"✅ All agents now using: {self.new_model}")
            logger.info("\n📋 Next Steps:")
            logger.info("1. Test agent functionality with new model")
            logger.info("2. Monitor performance and response quality")
            logger.info("3. Update agent aliases if needed")
            return True
        else:
            logger.error(f"\n❌ MODEL UPDATE FAILED!")
            logger.error(f"Only {success_count}/{total_agents} agents updated successfully")
            return False

def main():
    """Main function"""
    try:
        updater = AgentModelUpdater()
        success = updater.run_update()
        return success
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)