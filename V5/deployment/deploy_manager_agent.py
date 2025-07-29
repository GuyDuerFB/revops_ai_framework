#!/usr/bin/env python3
"""
Manager Agent V4 - Comprehensive Deployment Script
=================================================

This script properly configures the Manager Agent with all required components:
- Instructions from instructions.md
- Collaborator configuration
- Knowledge base integration
- Action groups (if needed)
- Proper preparation and alias updates

Usage:
    python3 deploy_manager_agent.py [options]
    
Options:
    --update-only      Only update existing agent (don't create new)
    --skip-alias       Skip updating the agent alias
    --dry-run         Show what would be done without making changes
    --help            Show help message
"""

import boto3
import json
import logging
import time
from pathlib import Path
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ManagerAgentDeployer:
    """Comprehensive Manager Agent deployment and configuration"""
    
    def __init__(self, config_file="config.json", dry_run=False):
        self.config_file = config_file
        self.dry_run = dry_run
        self.config = self.load_config()
        
        # Initialize AWS clients
        profile_name = self.config.get('profile_name', 'FireboltSystemAdministrator-740202120544')
        region_name = self.config.get('region_name', 'us-east-1')
        
        session = boto3.Session(profile_name=profile_name)
        self.bedrock_client = session.client('bedrock-agent', region_name=region_name)
        
        self.region_name = region_name
        self.profile_name = profile_name
        
        logger.info(f"Manager Agent Deployer initialized - Profile: {profile_name}, Region: {region_name}")
        if dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
    
    def load_config(self):
        """Load deployment configuration"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                config_path = Path(__file__).parent / self.config_file
            
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found")
            raise
    
    def load_instructions(self):
        """Load Manager Agent instructions from instructions.md"""
        manager_config = self.config['manager_agent']
        instructions_file = Path(manager_config['instructions_file'])
        
        if not instructions_file.exists():
            # Try relative to V4 root directory
            instructions_file = Path(__file__).parent.parent / manager_config['instructions_file']
        
        if not instructions_file.exists():
            logger.error(f"Instructions file not found: {manager_config['instructions_file']}")
            raise FileNotFoundError(f"Instructions file not found: {manager_config['instructions_file']}")
        
        with open(instructions_file, 'r') as f:
            instructions = f.read()
        
        logger.info(f"✅ Loaded instructions: {len(instructions)} characters")
        return instructions
    
    def wait_for_agent_ready(self, agent_id, timeout=300):
        """Wait for agent to be ready for operations"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.bedrock_client.get_agent(agentId=agent_id)
                status = response['agent']['agentStatus']
                
                if status in ['NOT_PREPARED', 'PREPARED']:
                    logger.info(f"✅ Agent status: {status}")
                    return True
                elif status == 'FAILED':
                    logger.error(f"❌ Agent in FAILED state")
                    return False
                else:
                    logger.info(f"⏳ Agent status: {status}, waiting...")
                    time.sleep(10)
            except Exception as e:
                logger.error(f"Error checking agent status: {e}")
                time.sleep(10)
        
        logger.error(f"❌ Timeout waiting for agent to be ready")
        return False
    
    def update_agent_instructions(self, agent_id):
        """Update Manager Agent with full instructions"""
        logger.info("📝 Updating Manager Agent instructions...")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would update agent instructions")
            return True
        
        try:
            # Load instructions
            instructions = self.load_instructions()
            
            # Get current agent details
            get_response = self.bedrock_client.get_agent(agentId=agent_id)
            agent_info = get_response['agent']
            
            # Update agent with instructions
            update_response = self.bedrock_client.update_agent(
                agentId=agent_id,
                agentName=agent_info['agentName'],
                description=agent_info.get('description', 'Manager Agent V4 - Intelligent router and coordinator'),
                instruction=instructions,
                foundationModel=agent_info.get('foundationModel'),
                agentResourceRoleArn=agent_info.get('agentResourceRoleArn'),
                agentCollaboration=agent_info.get('agentCollaboration', 'SUPERVISOR'),
                idleSessionTTLInSeconds=agent_info.get('idleSessionTTLInSeconds', 1800)
            )
            
            logger.info(f"✅ Agent instructions updated successfully!")
            logger.info(f"   Status: {update_response['agent']['agentStatus']}")
            
            # Wait for agent to be ready
            if not self.wait_for_agent_ready(agent_id):
                logger.error("❌ Agent not ready after instruction update")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating agent instructions: {str(e)}")
            return False
    
    def configure_collaborators(self, agent_id):
        """Configure all collaborators for the Manager Agent"""
        logger.info("🤝 Configuring Manager Agent collaborators...")
        
        manager_config = self.config['manager_agent']
        collaborators = manager_config.get('collaborators', [])
        
        if not collaborators:
            logger.warning("⚠️  No collaborators defined in config")
            return True
        
        success_count = 0
        
        for collaborator in collaborators:
            collaborator_name = collaborator['collaborator_name']
            agent_alias_arn = collaborator['agent_alias_arn']
            collaboration_instruction = collaborator['collaboration_instruction']
            relay_conversation_history = collaborator.get('relay_conversation_history', 'TO_COLLABORATOR')
            
            logger.info(f"   Adding collaborator: {collaborator_name}")
            
            if self.dry_run:
                logger.info(f"🔍 DRY RUN: Would add collaborator {collaborator_name}")
                success_count += 1
                continue
            
            try:
                # Check if collaborator already exists
                existing_collaborators = self.bedrock_client.list_agent_collaborators(
                    agentId=agent_id,
                    agentVersion="DRAFT"
                )
                
                # Check if this collaborator already exists
                collaborator_exists = any(
                    existing['collaboratorName'] == collaborator_name 
                    for existing in existing_collaborators['agentCollaboratorSummaries']
                )
                
                if collaborator_exists:
                    logger.info(f"   ✅ Collaborator {collaborator_name} already exists")
                    success_count += 1
                    continue
                
                # Add the collaborator
                response = self.bedrock_client.associate_agent_collaborator(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    agentDescriptor={
                        'aliasArn': agent_alias_arn
                    },
                    collaboratorName=collaborator_name,
                    collaborationInstruction=collaboration_instruction,
                    relayConversationHistory=relay_conversation_history
                )
                
                logger.info(f"   ✅ Added collaborator: {collaborator_name}")
                logger.info(f"      Collaborator ID: {response['agentCollaborator']['collaboratorId']}")
                success_count += 1
                
                # Small delay between collaborator additions
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"   ❌ Failed to add collaborator {collaborator_name}: {str(e)}")
                # Continue with other collaborators
                continue
        
        logger.info(f"✅ Configured {success_count}/{len(collaborators)} collaborators")
        return success_count > 0
    
    def configure_knowledge_base(self, agent_id):
        """Configure knowledge base for the Manager Agent"""
        logger.info("📚 Configuring knowledge base integration...")
        
        knowledge_base_config = self.config.get('knowledge_base', {})
        knowledge_base_id = knowledge_base_config.get('knowledge_base_id')
        
        if not knowledge_base_id:
            logger.warning("⚠️  No knowledge base ID configured")
            return True
        
        if self.dry_run:
            logger.info(f"🔍 DRY RUN: Would configure knowledge base {knowledge_base_id}")
            return True
        
        try:
            # Check if knowledge base is already associated
            existing_kbs = self.bedrock_client.list_agent_knowledge_bases(
                agentId=agent_id,
                agentVersion="DRAFT"
            )
            
            # Check if this knowledge base already exists
            kb_exists = any(
                kb['knowledgeBaseId'] == knowledge_base_id 
                for kb in existing_kbs['agentKnowledgeBaseSummaries']
            )
            
            if kb_exists:
                logger.info(f"   ✅ Knowledge base {knowledge_base_id} already configured")
                return True
            
            # Associate knowledge base
            response = self.bedrock_client.associate_agent_knowledge_base(
                agentId=agent_id,
                agentVersion="DRAFT",
                description="Firebolt schema and RevOps knowledge base",
                knowledgeBaseId=knowledge_base_id,
                knowledgeBaseState="ENABLED"
            )
            
            logger.info(f"✅ Knowledge base configured successfully")
            logger.info(f"   Knowledge Base ID: {knowledge_base_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configuring knowledge base: {str(e)}")
            return False
    
    def prepare_agent(self, agent_id):
        """Prepare the Manager Agent after configuration"""
        logger.info("🔧 Preparing Manager Agent...")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would prepare agent")
            return True
        
        try:
            # Prepare agent
            response = self.bedrock_client.prepare_agent(agentId=agent_id)
            
            logger.info(f"✅ Agent preparation initiated")
            logger.info(f"   Agent Status: {response['agentStatus']}")
            
            # Wait for preparation to complete
            logger.info("⏳ Waiting for agent preparation to complete...")
            max_wait = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait:
                agent_response = self.bedrock_client.get_agent(agentId=agent_id)
                status = agent_response['agent']['agentStatus']
                
                if status == 'PREPARED':
                    logger.info(f"✅ Manager Agent prepared successfully")
                    return True
                elif status == 'FAILED':
                    logger.error(f"❌ Manager Agent preparation failed")
                    return False
                
                logger.info(f"   Status: {status}, waiting...")
                time.sleep(10)
                wait_time += 10
            
            logger.error(f"❌ Manager Agent preparation timed out")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error preparing agent: {str(e)}")
            return False
    
    def update_agent_alias(self, agent_id):
        """Update agent alias to point to the latest version"""
        logger.info("🏷️  Updating agent alias...")
        
        manager_config = self.config['manager_agent']
        agent_alias_id = manager_config.get('agent_alias_id')
        
        if not agent_alias_id:
            logger.warning("⚠️  No agent alias ID configured")
            return True
        
        if self.dry_run:
            logger.info(f"🔍 DRY RUN: Would update alias {agent_alias_id}")
            return True
        
        try:
            # Get available versions
            versions_response = self.bedrock_client.list_agent_versions(agentId=agent_id)
            
            # Find the latest prepared version
            prepared_versions = [
                v for v in versions_response['agentVersionSummaries']
                if v['agentStatus'] == 'PREPARED' and v['agentVersion'] != 'DRAFT'
            ]
            
            if not prepared_versions:
                logger.error("❌ No prepared versions found")
                return False
            
            # Sort by version number to get the latest
            prepared_versions.sort(key=lambda x: int(x['agentVersion']), reverse=True)
            latest_version = prepared_versions[0]['agentVersion']
            
            logger.info(f"   Using version: {latest_version}")
            
            # Get current alias info
            alias_response = self.bedrock_client.get_agent_alias(
                agentId=agent_id,
                agentAliasId=agent_alias_id
            )
            alias_info = alias_response['agentAlias']
            
            # Update alias
            update_response = self.bedrock_client.update_agent_alias(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                agentAliasName=alias_info['agentAliasName'],
                description=alias_info.get('description', 'Manager Agent V4 - Production alias'),
                routingConfiguration=[
                    {
                        'agentVersion': latest_version
                    }
                ]
            )
            
            logger.info(f"✅ Agent alias updated successfully")
            logger.info(f"   Alias points to version: {latest_version}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating agent alias: {str(e)}")
            return False
    
    def validate_configuration(self, agent_id):
        """Validate that all configurations are properly applied"""
        logger.info("🔍 Validating Manager Agent configuration...")
        
        validation_results = {
            'instructions': False,
            'collaborators': False,
            'knowledge_base': False,
            'agent_status': False
        }
        
        try:
            # Check agent status and instructions
            agent_response = self.bedrock_client.get_agent(agentId=agent_id)
            agent_info = agent_response['agent']
            
            validation_results['agent_status'] = agent_info['agentStatus'] == 'PREPARED'
            validation_results['instructions'] = 'instruction' in agent_info
            
            # Check collaborators
            collaborators_response = self.bedrock_client.list_agent_collaborators(
                agentId=agent_id,
                agentVersion="DRAFT"
            )
            collaborator_count = len(collaborators_response['agentCollaboratorSummaries'])
            validation_results['collaborators'] = collaborator_count > 0
            
            # Check knowledge base
            kb_response = self.bedrock_client.list_agent_knowledge_bases(
                agentId=agent_id,
                agentVersion="DRAFT"
            )
            kb_count = len(kb_response['agentKnowledgeBaseSummaries'])
            validation_results['knowledge_base'] = kb_count > 0
            
            # Print validation results
            logger.info("📊 Validation Results:")
            logger.info(f"   ✅ Agent Status: {'PREPARED' if validation_results['agent_status'] else 'NOT PREPARED'}")
            logger.info(f"   ✅ Instructions: {'Loaded' if validation_results['instructions'] else 'Missing'}")
            logger.info(f"   ✅ Collaborators: {collaborator_count} configured")
            logger.info(f"   ✅ Knowledge Base: {kb_count} configured")
            
            return all(validation_results.values())
            
        except Exception as e:
            logger.error(f"❌ Error validating configuration: {str(e)}")
            return False
    
    def deploy_manager_agent(self, update_only=False, skip_alias=False):
        """Deploy and configure the Manager Agent comprehensively"""
        logger.info("🚀 Starting Manager Agent comprehensive deployment")
        
        manager_config = self.config['manager_agent']
        agent_id = manager_config.get('agent_id')
        
        if not agent_id:
            logger.error("❌ Manager Agent ID not found in configuration")
            return False
        
        logger.info(f"🎯 Target Agent ID: {agent_id}")
        
        # Check if agent exists
        try:
            agent_response = self.bedrock_client.get_agent(agentId=agent_id)
            logger.info(f"✅ Manager Agent found: {agent_response['agent']['agentName']}")
        except Exception as e:
            logger.error(f"❌ Manager Agent not found: {str(e)}")
            return False
        
        # Deployment steps
        steps = [
            ("Update Agent Instructions", lambda: self.update_agent_instructions(agent_id)),
            ("Configure Collaborators", lambda: self.configure_collaborators(agent_id)),
            ("Configure Knowledge Base", lambda: self.configure_knowledge_base(agent_id)),
            ("Prepare Agent", lambda: self.prepare_agent(agent_id)),
        ]
        
        if not skip_alias:
            steps.append(("Update Agent Alias", lambda: self.update_agent_alias(agent_id)))
        
        steps.append(("Validate Configuration", lambda: self.validate_configuration(agent_id)))
        
        # Execute deployment steps
        for step_name, step_function in steps:
            logger.info(f"📋 {step_name}...")
            
            try:
                success = step_function()
                if success:
                    logger.info(f"✅ {step_name} completed successfully")
                else:
                    logger.error(f"❌ {step_name} failed")
                    return False
            except Exception as e:
                logger.error(f"❌ {step_name} failed with error: {str(e)}")
                return False
        
        logger.info("🎉 Manager Agent deployment completed successfully!")
        return True


def main():
    """Main deployment function"""
    logger.info("Manager Agent V4 - Comprehensive Deployment")
    logger.info("=" * 60)
    
    # Parse command line arguments
    update_only = False
    skip_alias = False
    dry_run = False
    
    for arg in sys.argv[1:]:
        if arg == "--update-only":
            update_only = True
            logger.info("🔹 Update only mode enabled")
        elif arg == "--skip-alias":
            skip_alias = True
            logger.info("🔹 Alias update disabled")
        elif arg == "--dry-run":
            dry_run = True
            logger.info("🔹 Dry run mode enabled")
        elif arg == "--help":
            print("Usage: python3 deploy_manager_agent.py [options]")
            print("Options:")
            print("  --update-only    Only update existing agent")
            print("  --skip-alias     Skip updating the agent alias")
            print("  --dry-run        Show what would be done without making changes")
            print("  --help           Show this help message")
            return
    
    try:
        deployer = ManagerAgentDeployer(dry_run=dry_run)
        success = deployer.deploy_manager_agent(update_only=update_only, skip_alias=skip_alias)
        
        if success:
            logger.info("\n🎉 DEPLOYMENT SUCCESSFUL!")
            logger.info("✅ Manager Agent fully configured")
            logger.info("✅ Instructions loaded")
            logger.info("✅ Collaborators configured")
            logger.info("✅ Knowledge base integrated")
            logger.info("✅ Agent prepared and ready")
            logger.info("\n📋 Next Steps:")
            logger.info("1. Test Manager Agent through Slack integration")
            logger.info("2. Verify deal analysis routing is working")
            logger.info("3. Monitor agent performance and collaboration")
        else:
            logger.error("\n❌ DEPLOYMENT FAILED!")
            logger.error("Please check the logs above for error details")
            return False
            
    except Exception as e:
        logger.error(f"❌ Deployment failed with error: {str(e)}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)