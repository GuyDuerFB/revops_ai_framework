#!/usr/bin/env python3
"""
RevOps AI Framework V4 - Agents Only Deployment
===============================================

Deploy only the Bedrock Agents (skip Lambda deployment)
"""

import boto3
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class V4AgentsDeployer:
    """V4 Agents Only Deployment Manager"""
    
    def __init__(self, config_file="config.json"):
        """Initialize the deployer"""
        self.config_file = config_file
        self.config = self.load_config()
        
        # Initialize AWS clients
        profile_name = self.config.get('profile_name', 'FireboltSystemAdministrator-740202120544')
        region_name = self.config.get('region_name', 'us-east-1')
        
        session = boto3.Session(profile_name=profile_name)
        self.bedrock_client = session.client('bedrock-agent', region_name=region_name)
        
        self.region_name = region_name
        self.profile_name = profile_name
        
        logger.info(f"V4 Agents Deployer initialized - Profile: {profile_name}, Region: {region_name}")
    
    def load_config(self):
        """Load deployment configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found")
            raise
    
    def save_config(self):
        """Save updated configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        logger.info("📄 Configuration saved")
    
    def create_data_agent(self):
        """Create Data Agent V4"""
        logger.info("🤖 Creating Data Agent V4")
        
        agent_config = self.config['data_agent']
        
        # Read instructions
        instructions_file = Path(agent_config['instructions_file'])
        if not instructions_file.exists():
            # Try relative to V4 root directory (one level up from deployment)
            instructions_file = Path(__file__).parent.parent / agent_config['instructions_file']
        
        if not instructions_file.exists():
            logger.error(f"Instructions file not found: {agent_config['instructions_file']}")
            raise FileNotFoundError(f"Instructions file not found: {agent_config['instructions_file']}")
        
        with open(instructions_file, 'r') as f:
            instructions = f.read()
        
        try:
            # Create the agent with V4 naming and comprehensive tagging
            response = self.bedrock_client.create_agent(
                agentName="DataAgent-V4",
                description=agent_config['description'],
                foundationModel=agent_config['foundation_model'],
                instruction=instructions,
                agentResourceRoleArn=self.config['execution_role_arn'],
                idleSessionTTLInSeconds=1800,
                tags={
                    'Project': 'RevOps-AI-Framework',
                    'Version': 'V4',
                    'AgentType': 'Data',
                    'Model': 'Claude-3.5-Sonnet',
                    'Environment': 'Production',
                    'CreatedBy': 'V4-Deployment-Script',
                    'Purpose': 'Data-Retrieval-Analysis'
                }
            )
            
            agent_id = response['agent']['agentId']
            logger.info(f"✅ Data Agent V4 created: {agent_id}")
            
            # Update config with agent ID
            self.config['data_agent']['agent_id'] = agent_id
            self.save_config()
            
            return agent_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create Data Agent V4: {str(e)}")
            raise
    
    def create_web_search_agent(self):
        """Create Web Search Agent V4"""
        logger.info("🤖 Creating Web Search Agent V4")
        
        agent_config = self.config['web_search_agent']
        
        # Read instructions
        instructions_file = Path(agent_config['instructions_file'])
        if not instructions_file.exists():
            # Try relative to V4 root directory (one level up from deployment)
            instructions_file = Path(__file__).parent.parent / agent_config['instructions_file']
        
        if not instructions_file.exists():
            logger.error(f"Instructions file not found: {agent_config['instructions_file']}")
            raise FileNotFoundError(f"Instructions file not found: {agent_config['instructions_file']}")
        
        with open(instructions_file, 'r') as f:
            instructions = f.read()
        
        try:
            # Create the agent with V4 naming and comprehensive tagging
            response = self.bedrock_client.create_agent(
                agentName="WebSearchAgent-V4",
                description=agent_config['description'],
                foundationModel=agent_config['foundation_model'],
                instruction=instructions,
                agentResourceRoleArn=self.config['execution_role_arn'],
                idleSessionTTLInSeconds=1800,
                tags={
                    'Project': 'RevOps-AI-Framework',
                    'Version': 'V4',
                    'AgentType': 'WebSearch',
                    'Model': 'Claude-3.5-Sonnet',
                    'Environment': 'Production',
                    'CreatedBy': 'V4-Deployment-Script',
                    'Purpose': 'External-Intelligence-Research'
                }
            )
            
            agent_id = response['agent']['agentId']
            logger.info(f"✅ Web Search Agent V4 created: {agent_id}")
            
            # Update config with agent ID
            self.config['web_search_agent']['agent_id'] = agent_id
            self.save_config()
            
            return agent_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create Web Search Agent V4: {str(e)}")
            raise
    
    def create_execution_agent(self):
        """Create Execution Agent V4"""
        logger.info("🤖 Creating Execution Agent V4")
        
        agent_config = self.config['execution_agent']
        
        # Read instructions
        instructions_file = Path(agent_config['instructions_file'])
        if not instructions_file.exists():
            # Try relative to V4 root directory (one level up from deployment)
            instructions_file = Path(__file__).parent.parent / agent_config['instructions_file']
        
        if not instructions_file.exists():
            logger.error(f"Instructions file not found: {agent_config['instructions_file']}")
            raise FileNotFoundError(f"Instructions file not found: {agent_config['instructions_file']}")
        
        with open(instructions_file, 'r') as f:
            instructions = f.read()
        
        try:
            # Create the agent with V4 naming and comprehensive tagging
            response = self.bedrock_client.create_agent(
                agentName="ExecutionAgent-V4",
                description=agent_config['description'],
                foundationModel=agent_config['foundation_model'],
                instruction=instructions,
                agentResourceRoleArn=self.config['execution_role_arn'],
                idleSessionTTLInSeconds=1800,
                tags={
                    'Project': 'RevOps-AI-Framework',
                    'Version': 'V4',
                    'AgentType': 'Execution',
                    'Model': 'Claude-3.5-Sonnet',
                    'Environment': 'Production',
                    'CreatedBy': 'V4-Deployment-Script',
                    'Purpose': 'Action-Execution-Integration'
                }
            )
            
            agent_id = response['agent']['agentId']
            logger.info(f"✅ Execution Agent V4 created: {agent_id}")
            
            # Update config with agent ID
            self.config['execution_agent']['agent_id'] = agent_id
            self.save_config()
            
            return agent_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create Execution Agent V4: {str(e)}")
            raise
    
    def create_deal_analysis_agent(self):
        """Create Deal Analysis Agent V4"""
        logger.info("🤖 Creating Deal Analysis Agent V4")
        
        agent_config = self.config['deal_analysis_agent']
        
        # Read instructions
        instructions_file = Path(agent_config['instructions_file'])
        if not instructions_file.exists():
            # Try relative to V4 root directory (one level up from deployment)
            instructions_file = Path(__file__).parent.parent / agent_config['instructions_file']
        
        if not instructions_file.exists():
            logger.error(f"Instructions file not found: {agent_config['instructions_file']}")
            raise FileNotFoundError(f"Instructions file not found: {agent_config['instructions_file']}")
        
        with open(instructions_file, 'r') as f:
            instructions = f.read()
        
        try:
            # Create the agent with V4 naming and comprehensive tagging
            response = self.bedrock_client.create_agent(
                agentName="DealAnalysisAgent-V4",
                description=agent_config['description'],
                foundationModel=agent_config['foundation_model'],
                instruction=instructions,
                agentResourceRoleArn=self.config['execution_role_arn'],
                idleSessionTTLInSeconds=1800,
                tags={
                    'Project': 'RevOps-AI-Framework',
                    'Version': 'V4',
                    'AgentType': 'DealAnalysis',
                    'Model': 'Claude-3.5-Sonnet',
                    'Environment': 'Production',
                    'CreatedBy': 'V4-Deployment-Script',
                    'Purpose': 'MEDDPICC-Deal-Assessment'
                }
            )
            
            agent_id = response['agent']['agentId']
            logger.info(f"✅ Deal Analysis Agent V4 created: {agent_id}")
            
            # Update config with agent ID
            self.config['deal_analysis_agent']['agent_id'] = agent_id
            self.save_config()
            
            return agent_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create Deal Analysis Agent V4: {str(e)}")
            raise
    
    def create_manager_agent(self):
        """Create Manager Agent V4"""
        logger.info("🤖 Creating Manager Agent V4")
        
        agent_config = self.config['manager_agent']
        
        # Read instructions
        instructions_file = Path(agent_config['instructions_file'])
        if not instructions_file.exists():
            # Try relative to V4 root directory (one level up from deployment)
            instructions_file = Path(__file__).parent.parent / agent_config['instructions_file']
        
        if not instructions_file.exists():
            logger.error(f"Instructions file not found: {agent_config['instructions_file']}")
            raise FileNotFoundError(f"Instructions file not found: {agent_config['instructions_file']}")
        
        with open(instructions_file, 'r') as f:
            instructions = f.read()
        
        try:
            # Create the agent with V4 naming and comprehensive tagging
            response = self.bedrock_client.create_agent(
                agentName="ManagerAgent-V4",
                description=agent_config['description'],
                foundationModel=agent_config['foundation_model'],
                instruction=instructions,
                agentResourceRoleArn=self.config['execution_role_arn'],
                idleSessionTTLInSeconds=1800,
                tags={
                    'Project': 'RevOps-AI-Framework',
                    'Version': 'V4',
                    'AgentType': 'Manager',
                    'Model': 'Claude-3.5-Sonnet',
                    'Environment': 'Production',
                    'CreatedBy': 'V4-Deployment-Script',
                    'Purpose': 'Intelligent-Routing-Supervisor'
                }
            )
            
            agent_id = response['agent']['agentId']
            logger.info(f"✅ Manager Agent V4 created: {agent_id}")
            
            # Update config with agent ID
            self.config['manager_agent']['agent_id'] = agent_id
            self.save_config()
            
            return agent_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create Manager Agent V4: {str(e)}")
            raise
    
    def deploy_v4_agents(self):
        """Deploy all V4 agents"""
        logger.info("🚀 Starting V4 Agents Deployment")
        
        deployment_steps = [
            ("Create Data Agent V4", self.create_data_agent),
            ("Create Web Search Agent V4", self.create_web_search_agent),
            ("Create Execution Agent V4", self.create_execution_agent),
            ("Create Deal Analysis Agent V4", self.create_deal_analysis_agent),
            ("Create Manager Agent V4", self.create_manager_agent)
        ]
        
        for step_name, step_function in deployment_steps:
            try:
                logger.info(f"📋 {step_name}")
                step_function()
                logger.info(f"✅ {step_name} completed")
            except Exception as e:
                logger.error(f"❌ {step_name} failed: {str(e)}")
                # Continue with other agents instead of failing completely
                continue
        
        logger.info("🎉 V4 Agents deployment completed!")
        
        return True

def main():
    """Main deployment function"""
    try:
        deployer = V4AgentsDeployer()
        deployer.deploy_v4_agents()
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()