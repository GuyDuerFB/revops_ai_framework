#!/usr/bin/env python3
"""
Lead Analysis Agent V4 - Comprehensive Deployment Script
========================================================

This script properly configures the Lead Analysis Agent with all required components:
- Instructions from instructions.md
- Claude 3.7 inference profile configuration
- Knowledge base integration
- Proper preparation and alias creation
- Manager Agent collaboration setup

Usage:
    python3 deploy_lead_analysis_agent.py [options]
    
Options:
    --update-only      Only update existing agent (don't create new)
    --skip-alias       Skip creating agent aliases
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

class LeadAnalysisAgentDeployer:
    """Comprehensive Lead Analysis Agent deployment and configuration"""
    
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
        
        logger.info(f"Lead Analysis Agent Deployer initialized - Profile: {profile_name}, Region: {region_name}")
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
        """Load Lead Analysis Agent instructions from instructions.md"""
        lead_analysis_config = self.config['lead_analysis_agent']
        instructions_file = Path(lead_analysis_config['instructions_file'])
        
        if not instructions_file.exists():
            # Try relative to V4 root directory
            instructions_file = Path(__file__).parent.parent / lead_analysis_config['instructions_file']
        
        if not instructions_file.exists():
            logger.error(f"Instructions file not found: {lead_analysis_config['instructions_file']}")
            raise FileNotFoundError(f"Instructions file not found: {lead_analysis_config['instructions_file']}")
        
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
                    logger.error(f"❌ Agent failed to create/update")
                    return False
                else:
                    logger.info(f"⏳ Agent status: {status}, waiting...")
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"Error checking agent status: {e}")
                time.sleep(10)
        
        logger.error(f"⏰ Timeout waiting for agent to be ready")
        return False
    
    def wait_for_agent_prepared(self, agent_id, timeout=300):
        """Wait for agent to be PREPARED"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.bedrock_client.get_agent(agentId=agent_id)
                status = response['agent']['agentStatus']
                
                if status == 'PREPARED':
                    logger.info(f"✅ Agent prepared successfully")
                    return True
                elif status == 'FAILED':
                    logger.error(f"❌ Agent preparation failed")
                    return False
                else:
                    logger.info(f"⏳ Agent status: {status}, waiting for preparation...")
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"Error checking agent preparation: {e}")
                time.sleep(10)
        
        logger.error(f"⏰ Timeout waiting for agent preparation")
        return False
    
    def create_action_groups(self, agent_id):
        """Create action groups for the Lead Analysis Agent"""
        lead_analysis_config = self.config['lead_analysis_agent']
        action_groups = lead_analysis_config.get('action_groups', [])
        
        if not action_groups:
            logger.info("📝 No action groups configured, skipping...")
            return True
        
        for action_group_config in action_groups:
            action_group_name = action_group_config['name']
            description = action_group_config['description']
            lambda_arn = action_group_config['lambda_arn']
            
            logger.info(f"🔧 Creating action group: {action_group_name}")
            
            if self.dry_run:
                logger.info(f"🔍 DRY RUN: Would create action group {action_group_name}")
                continue
            
            try:
                # Use function schema instead of OpenAPI schema like Deal Analysis Agent
                if action_group_name == "firebolt_query":
                    function_schema = {
                        "functions": [
                            {
                                "name": "query_firebolt",
                                "description": "Execute SQL query against Firebolt for lead analysis",
                                "parameters": {
                                    "query": {
                                        "type": "string",
                                        "description": "SQL query to execute",
                                        "required": True
                                    }
                                },
                                "requireConfirmation": "DISABLED"
                            }
                        ]
                    }
                elif action_group_name == "web_search":
                    function_schema = {
                        "functions": [
                            {
                                "name": "search_web",
                                "description": "Search web for company and person information",
                                "parameters": {
                                    "query": {
                                        "type": "string",
                                        "description": "Search query for web research",
                                        "required": True
                                    },
                                    "search_type": {
                                        "type": "string",
                                        "description": "Type of search: company, person, or general",
                                        "required": False
                                    }
                                },
                                "requireConfirmation": "DISABLED"
                            },
                            {
                                "name": "research_company",
                                "description": "Research specific company information",
                                "parameters": {
                                    "company_name": {
                                        "type": "string",
                                        "description": "Company name to research",
                                        "required": True
                                    },
                                    "research_focus": {
                                        "type": "string",
                                        "description": "Specific research focus area",
                                        "required": False
                                    }
                                },
                                "requireConfirmation": "DISABLED"
                            }
                        ]
                    }
                else:
                    logger.error(f"Unknown action group: {action_group_name}")
                    return False
                
                response = self.bedrock_client.create_agent_action_group(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    actionGroupName=action_group_name,
                    description=description,
                    actionGroupExecutor={
                        'lambda': lambda_arn
                    },
                    functionSchema=function_schema,
                    actionGroupState="ENABLED"
                )
                
                action_group_id = response['agentActionGroup']['actionGroupId']
                logger.info(f"✅ Action group created: {action_group_name} ({action_group_id})")
                
                # Update config with action group ID
                action_group_config['action_group_id'] = action_group_id
                
            except Exception as e:
                if "ConflictException" in str(e):
                    logger.info(f"🔧 Action group {action_group_name} already exists")
                else:
                    logger.error(f"❌ Error creating action group {action_group_name}: {e}")
                    return False
        
        return True
    
    def create_agent(self, update_only=False):
        """Create or update the Lead Analysis Agent"""
        lead_analysis_config = self.config['lead_analysis_agent']
        instructions = self.load_instructions()
        
        agent_name = "LeadAnalysisAgent-V4"
        description = lead_analysis_config['description']
        foundation_model = lead_analysis_config['foundation_model']
        
        # Get execution role ARN from config
        execution_role_arn = self.config.get('execution_role_arn')
        if not execution_role_arn:
            logger.error("❌ Execution role ARN not found in config")
            return False
        
        # Get knowledge base ID from config
        knowledge_base_id = self.config['knowledge_base']['knowledge_base_id']
        
        logger.info("🔄 Creating/Updating Lead Analysis Agent...")
        logger.info(f"   Agent Name: {agent_name}")
        logger.info(f"   Foundation Model: {foundation_model}")
        logger.info(f"   Knowledge Base: {knowledge_base_id}")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would create/update agent with above configuration")
            return True
        
        try:
            # Check if agent exists
            existing_agent_id = lead_analysis_config.get('agent_id')
            if existing_agent_id and existing_agent_id != "TBD":
                # Update existing agent
                logger.info(f"🔄 Updating existing agent: {existing_agent_id}")
                response = self.bedrock_client.update_agent(
                    agentId=existing_agent_id,
                    agentName=agent_name,
                    description=description,
                    instruction=instructions,
                    foundationModel=foundation_model,
                    agentResourceRoleArn=execution_role_arn,
                    idleSessionTTLInSeconds=1800
                )
                agent_id = existing_agent_id
            else:
                # Create new agent
                logger.info("🆕 Creating new agent...")
                response = self.bedrock_client.create_agent(
                    agentName=agent_name,
                    description=description,
                    instruction=instructions,
                    foundationModel=foundation_model,
                    agentResourceRoleArn=execution_role_arn,
                    idleSessionTTLInSeconds=1800
                )
                agent_id = response['agent']['agentId']
                logger.info(f"✅ Agent created with ID: {agent_id}")
                
                # Update config with new agent ID
                self.update_config_agent_id(agent_id)
            
            # Wait for agent to be ready
            if not self.wait_for_agent_ready(agent_id):
                return False
            
            # Associate knowledge base
            logger.info("📚 Associating knowledge base...")
            try:
                self.bedrock_client.associate_agent_knowledge_base(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    knowledgeBaseId=knowledge_base_id,
                    description="RevOps Schema and Business Logic Knowledge Base",
                    knowledgeBaseState="ENABLED"
                )
                logger.info("✅ Knowledge base associated successfully")
            except Exception as e:
                if "ConflictException" in str(e):
                    logger.info("📚 Knowledge base already associated")
                else:
                    logger.error(f"❌ Error associating knowledge base: {e}")
                    return False
            
            # Create action groups
            logger.info("🔧 Creating action groups...")
            if not self.create_action_groups(agent_id):
                logger.warning("⚠️ Action group creation failed, but continuing deployment")
                # Don't fail deployment for action group issues
            
            # Prepare agent
            logger.info("⚙️ Preparing agent...")
            prepare_response = self.bedrock_client.prepare_agent(agentId=agent_id)
            logger.info(f"✅ Agent preparation initiated")
            
            # Wait for preparation to complete
            if not self.wait_for_agent_prepared(agent_id):
                return False
            
            return agent_id
            
        except Exception as e:
            logger.error(f"❌ Error creating/updating agent: {e}")
            return False
    
    def create_aliases(self, agent_id):
        """Create production and development aliases for the agent"""
        lead_analysis_config = self.config['lead_analysis_agent']
        
        logger.info("🏷️ Creating agent aliases...")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would create prod and dev aliases")
            return True
        
        try:
            # Get the latest prepared version - retry logic for timing issues
            prepared_versions = []
            max_retries = 3
            for attempt in range(max_retries):
                logger.info(f"🔍 Checking for prepared versions (attempt {attempt + 1}/{max_retries})...")
                versions_response = self.bedrock_client.list_agent_versions(agentId=agent_id)
                prepared_versions = [
                    v for v in versions_response['agentVersionSummaries'] 
                    if v['agentStatus'] == 'PREPARED' and v['agentVersion'] != 'DRAFT'
                ]
                
                if prepared_versions:
                    break
                elif attempt < max_retries - 1:
                    logger.info("⏳ No prepared versions found yet, waiting 10 seconds...")
                    time.sleep(10)
            
            if not prepared_versions:
                # Check if we can use DRAFT version as fallback
                logger.warning("⚠️ No numbered prepared versions found, checking for DRAFT version...")
                draft_versions = [
                    v for v in versions_response['agentVersionSummaries'] 
                    if v['agentStatus'] == 'PREPARED' and v['agentVersion'] == 'DRAFT'
                ]
                
                if draft_versions:
                    logger.info("✅ Using DRAFT version for alias creation")
                    latest_version = 'DRAFT'
                else:
                    logger.error("❌ No prepared versions (numbered or DRAFT) found for alias creation")
                    return False
            else:
                # Sort by version number and get the latest
                prepared_versions.sort(key=lambda x: int(x['agentVersion']), reverse=True)
                latest_version = prepared_versions[0]['agentVersion']
            
            logger.info(f"📌 Using version {latest_version} for aliases")
            
            # Create production alias
            prod_alias_name = lead_analysis_config['agent_alias_name']
            logger.info(f"🏷️ Creating production alias: {prod_alias_name}")
            
            prod_alias_response = self.bedrock_client.create_agent_alias(
                agentId=agent_id,
                agentAliasName=prod_alias_name,
                description="Lead Analysis Agent Production Alias",
                routingConfiguration=[
                    {
                        'agentVersion': latest_version
                    }
                ]
            )
            prod_alias_id = prod_alias_response['agentAlias']['agentAliasId']
            logger.info(f"✅ Production alias created: {prod_alias_id}")
            
            # Create development alias
            dev_alias_name = lead_analysis_config['dev_agent_alias_name']
            logger.info(f"🏷️ Creating development alias: {dev_alias_name}")
            
            dev_alias_response = self.bedrock_client.create_agent_alias(
                agentId=agent_id,
                agentAliasName=dev_alias_name,
                description="Lead Analysis Agent Development Alias",
                routingConfiguration=[
                    {
                        'agentVersion': latest_version
                    }
                ]
            )
            dev_alias_id = dev_alias_response['agentAlias']['agentAliasId']
            logger.info(f"✅ Development alias created: {dev_alias_id}")
            
            # Update config with alias IDs
            self.update_config_aliases(prod_alias_id, dev_alias_id, latest_version)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating aliases: {e}")
            return False
    
    def update_config_agent_id(self, agent_id):
        """Update config.json with new agent ID"""
        try:
            self.config['lead_analysis_agent']['agent_id'] = agent_id
            self.config['lead_analysis_agent']['agent_status'] = 'CREATED'
            
            config_path = Path(__file__).parent / self.config_file
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"✅ Config updated with agent ID: {agent_id}")
            
        except Exception as e:
            logger.error(f"❌ Error updating config with agent ID: {e}")
    
    def update_config_aliases(self, prod_alias_id, dev_alias_id, version):
        """Update config.json with alias IDs and version"""
        try:
            self.config['lead_analysis_agent']['agent_alias_id'] = prod_alias_id
            self.config['lead_analysis_agent']['dev_agent_alias_id'] = dev_alias_id
            self.config['lead_analysis_agent']['latest_version'] = version
            self.config['lead_analysis_agent']['agent_status'] = 'PREPARED'
            
            # Update Manager Agent collaborator configuration
            for collaborator in self.config['manager_agent']['collaborators']:
                if collaborator['collaborator_name'] == 'LeadAnalysisAgent':
                    collaborator['agent_id'] = self.config['lead_analysis_agent']['agent_id']
                    collaborator['agent_alias_arn'] = f"arn:aws:bedrock:{self.region_name}:740202120544:agent-alias/{self.config['lead_analysis_agent']['agent_id']}/{prod_alias_id}"
                    collaborator['collaborator_id'] = f"LA_{int(time.time())}"  # Generate unique ID
                    break
            
            config_path = Path(__file__).parent / self.config_file
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"✅ Config updated with aliases - Prod: {prod_alias_id}, Dev: {dev_alias_id}")
            
        except Exception as e:
            logger.error(f"❌ Error updating config with aliases: {e}")
    
    def deploy(self, update_only=False, skip_alias=False):
        """Deploy the complete Lead Analysis Agent"""
        logger.info("🚀 Starting Lead Analysis Agent V4 Deployment")
        logger.info("=" * 60)
        
        # Step 1: Create/Update Agent
        agent_id = self.create_agent(update_only)
        if not agent_id:
            logger.error("❌ Agent creation/update failed")
            return False
        
        # Step 2: Create Aliases
        if not skip_alias:
            if not self.create_aliases(agent_id):
                logger.error("❌ Alias creation failed")
                return False
        
        logger.info("🎉 Lead Analysis Agent deployment completed successfully!")
        logger.info("=" * 60)
        logger.info("✅ Next steps:")
        logger.info("1. Test the agent with a sample lead analysis query")
        logger.info("2. Update Manager Agent to include Lead Analysis Agent collaboration")
        logger.info("3. Monitor agent performance and responses")
        
        return True

def main():
    """Main deployment function"""
    
    # Parse command line arguments
    update_only = False
    skip_alias = False
    dry_run = False
    
    for arg in sys.argv[1:]:
        if arg == "--update-only":
            update_only = True
        elif arg == "--skip-alias":
            skip_alias = True
        elif arg == "--dry-run":
            dry_run = True
        elif arg == "--help":
            print(__doc__)
            return
    
    try:
        deployer = LeadAnalysisAgentDeployer(dry_run=dry_run)
        success = deployer.deploy(update_only=update_only, skip_alias=skip_alias)
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()