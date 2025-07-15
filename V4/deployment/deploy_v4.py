#!/usr/bin/env python3
"""
RevOps AI Framework V4 - Production Deployment
==============================================

Deployment script for the V4 architecture with Manager Agent and Deal Analysis Agent.
"""

import boto3
import json
import logging
import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class V4Deployer:
    """V4 Architecture Deployment Manager"""
    
    def __init__(self, config_file="config.json"):
        """Initialize the deployer"""
        self.config_file = config_file
        self.config = self.load_config()
        
        # Initialize AWS clients
        profile_name = self.config.get('profile_name', 'FireboltSystemAdministrator-740202120544')
        region_name = self.config.get('region_name', 'us-east-1')
        
        session = boto3.Session(profile_name=profile_name)
        self.bedrock_client = session.client('bedrock-agent', region_name=region_name)
        self.bedrock_runtime_client = session.client('bedrock', region_name=region_name)
        self.lambda_client = session.client('lambda', region_name=region_name)
        self.iam_client = session.client('iam', region_name=region_name)
        
        self.region_name = region_name
        self.profile_name = profile_name
        
        logger.info(f"V4 Deployer initialized - Profile: {profile_name}, Region: {region_name}")
    
    def load_config(self):
        """Load deployment configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_file} not found")
            raise
    
    def create_inference_profile(self):
        """Create Claude 3.7 inference profile for enhanced performance"""
        logger.info("🧠 Creating Claude 3.7 Inference Profile")
        
        inference_profile_name = "claude-3-7-revops-profile"
        model_id = "anthropic.claude-3-7-sonnet-20250219-v1:0"
        
        try:
            # Check if inference profile already exists
            try:
                response = self.bedrock_runtime_client.get_inference_profile(
                    inferenceProfileIdentifier=inference_profile_name
                )
                logger.info(f"✅ Inference profile already exists: {response['inferenceProfileId']}")
                return response['inferenceProfileId']
            except self.bedrock_runtime_client.exceptions.ResourceNotFoundException:
                # Profile doesn't exist, create it
                pass
            
            # Create inference profile
            response = self.bedrock_runtime_client.create_inference_profile(
                inferenceProfileName=inference_profile_name,
                description="Claude 3.7 inference profile for RevOps AI Framework V4 enhanced performance",
                modelSource={
                    'copyFrom': model_id
                },
                tags=[
                    {
                        'key': 'Project',
                        'value': 'RevOps-AI-Framework-V4'
                    },
                    {
                        'key': 'Purpose',
                        'value': 'Deal-Analysis-Enhanced-Performance'
                    }
                ]
            )
            
            inference_profile_id = response['inferenceProfileArn']
            logger.info(f"✅ Claude 3.7 Inference Profile created: {inference_profile_id}")
            
            # Update config with inference profile ID
            self.config['inference_profile'] = {
                'inference_profile_id': inference_profile_id,
                'inference_profile_name': inference_profile_name,
                'model_id': model_id
            }
            self.save_config()
            
            return inference_profile_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create inference profile: {str(e)}")
            # If inference profile creation fails, fall back to direct model usage
            logger.warning("⚠️ Falling back to direct model usage without inference profile")
            return model_id
    
    def create_lambda_deployment_package(self, source_dir, function_name):
        """Create deployment package for Lambda function"""
        logger.info(f"Creating deployment package for {function_name}")
        
        # Create temporary directory
        temp_dir = Path(f"/tmp/{function_name}_deployment")
        temp_dir.mkdir(exist_ok=True)
        
        # Copy source files
        source_path = Path(source_dir)
        for file in source_path.glob("*"):
            if file.is_file():
                shutil.copy2(file, temp_dir)
        
        # Install requirements if they exist
        requirements_file = temp_dir / "requirements.txt"
        if requirements_file.exists():
            logger.info(f"Installing requirements for {function_name}")
            os.system(f"pip install -r {requirements_file} -t {temp_dir}")
        
        # Create zip file
        zip_file = Path(f"/tmp/{function_name}.zip")
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in temp_dir.rglob("*"):
                if file.is_file():
                    zipf.write(file, file.relative_to(temp_dir))
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        logger.info(f"Deployment package created: {zip_file}")
        return zip_file
    
    def deploy_deal_analysis_agent_lambda(self):
        """Deploy Deal Analysis Agent Lambda function"""
        logger.info("🚀 Deploying Deal Analysis Agent Lambda Function")
        
        function_config = self.config['lambda_functions']['deal_analysis_agent']
        function_name = function_config['function_name']
        
        # Update environment variables with inference profile ID if available
        if 'inference_profile' in self.config:
            function_config['environment_variables']['INFERENCE_PROFILE_ID'] = self.config['inference_profile']['inference_profile_id']
            logger.info(f"Updated INFERENCE_PROFILE_ID: {self.config['inference_profile']['inference_profile_id']}")
        
        # Create deployment package
        deployment_package = self.create_lambda_deployment_package(
            function_config['source_dir'], 
            function_name
        )
        
        try:
            # Check if function exists
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                # Function exists, update it
                logger.info(f"Updating existing function: {function_name}")
                
                with open(deployment_package, 'rb') as f:
                    response = self.lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=f.read()
                    )
                
                # Update configuration
                self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Runtime=function_config['runtime'],
                    Handler=function_config['handler'],
                    Timeout=function_config['timeout'],
                    MemorySize=function_config['memory_size'],
                    Environment={
                        'Variables': function_config['environment_variables']
                    }
                )
                
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Function doesn't exist, create it
                logger.info(f"Creating new function: {function_name}")
                
                with open(deployment_package, 'rb') as f:
                    response = self.lambda_client.create_function(
                        FunctionName=function_name,
                        Runtime=function_config['runtime'],
                        Role=self.config['execution_role_arn'],
                        Handler=function_config['handler'],
                        Code={'ZipFile': f.read()},
                        Timeout=function_config['timeout'],
                        MemorySize=function_config['memory_size'],
                        Environment={
                            'Variables': function_config['environment_variables']
                        }
                    )
            
            logger.info(f"✅ Deal Analysis Agent Lambda deployed: {response['FunctionArn']}")
            return response['FunctionArn']
            
        except Exception as e:
            logger.error(f"❌ Failed to deploy Deal Analysis Agent Lambda: {str(e)}")
            raise
        
        finally:
            # Clean up deployment package
            if deployment_package.exists():
                deployment_package.unlink()
    
    def create_deal_analysis_agent(self):
        """Create Deal Analysis Agent in Bedrock"""
        logger.info("🤖 Creating Deal Analysis Agent V4")
        
        agent_config = self.config['deal_analysis_agent']
        
        # Read instructions
        instructions_file = Path(agent_config['instructions_file'])
        if not instructions_file.exists():
            logger.error(f"Instructions file not found: {instructions_file}")
            raise FileNotFoundError(f"Instructions file not found: {instructions_file}")
        
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
                    'Model': 'Claude-3.7',
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
            logger.error(f"Instructions file not found: {instructions_file}")
            raise FileNotFoundError(f"Instructions file not found: {instructions_file}")
        
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
                    'Model': 'Claude-3.7',
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
    
    def create_data_agent(self):
        """Create Data Agent V4"""
        logger.info("🤖 Creating Data Agent V4")
        
        agent_config = self.config['data_agent']
        
        # Read instructions
        instructions_file = Path(agent_config['instructions_file'])
        if not instructions_file.exists():
            logger.error(f"Instructions file not found: {instructions_file}")
            raise FileNotFoundError(f"Instructions file not found: {instructions_file}")
        
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
                    'Model': 'Claude-3.7',
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
            logger.error(f"Instructions file not found: {instructions_file}")
            raise FileNotFoundError(f"Instructions file not found: {instructions_file}")
        
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
                    'Model': 'Claude-3.7',
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
            logger.error(f"Instructions file not found: {instructions_file}")
            raise FileNotFoundError(f"Instructions file not found: {instructions_file}")
        
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
                    'Model': 'Claude-3.7',
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
    
    def prepare_agents(self):
        """Prepare all V4 agents"""
        logger.info("🔧 Preparing V4 Agents")
        
        agents_to_prepare = [
            ('data_agent', 'Data Agent V4'),
            ('web_search_agent', 'Web Search Agent V4'),
            ('execution_agent', 'Execution Agent V4'),
            ('deal_analysis_agent', 'Deal Analysis Agent V4'),
            ('manager_agent', 'Manager Agent V4')
        ]
        
        for agent_key, agent_name in agents_to_prepare:
            if agent_key in self.config and self.config[agent_key]['agent_id']:
                agent_id = self.config[agent_key]['agent_id']
                logger.info(f"Preparing {agent_name}: {agent_id}")
                
                try:
                    response = self.bedrock_client.prepare_agent(agentId=agent_id)
                    logger.info(f"✅ {agent_name} prepared successfully")
                except Exception as e:
                    logger.error(f"❌ Failed to prepare {agent_name}: {str(e)}")
    
    def create_agent_aliases(self):
        """Create aliases for all V4 agents"""
        logger.info("🏷️ Creating V4 Agent Aliases")
        
        agents_to_alias = [
            ('data_agent', 'Data Agent V4'),
            ('web_search_agent', 'Web Search Agent V4'),
            ('execution_agent', 'Execution Agent V4'),
            ('deal_analysis_agent', 'Deal Analysis Agent V4'),
            ('manager_agent', 'Manager Agent V4')
        ]
        
        for agent_key, agent_name in agents_to_alias:
            if agent_key in self.config and self.config[agent_key]['agent_id']:
                agent_config = self.config[agent_key]
                agent_id = agent_config['agent_id']
                
                try:
                    # Create alias with V4 naming
                    alias_name = f"{agent_name.replace(' ', '')}-Alias"
                    response = self.bedrock_client.create_agent_alias(
                        agentId=agent_id,
                        agentAliasName=alias_name,
                        description=f"Production alias for {agent_name}",
                        routingConfiguration=[
                            {
                                'agentVersion': 'DRAFT'
                            }
                        ],
                        tags={
                            'Project': 'RevOps-AI-Framework',
                            'Version': 'V4',
                            'AgentType': agent_key.split('_')[0].capitalize(),
                            'AliasType': 'Production'
                        }
                    )
                    
                    alias_id = response['agentAlias']['agentAliasId']
                    logger.info(f"✅ {agent_name} alias created: {alias_id}")
                    
                    # Update config
                    self.config[agent_key]['agent_alias_id'] = alias_id
                    self.save_config()
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create alias for {agent_name}: {str(e)}")
    
    def test_deal_analysis_agent(self):
        """Test Deal Analysis Agent"""
        logger.info("🧪 Testing Deal Analysis Agent")
        
        # Test with IXIS deal
        test_query = "What is the status of the IXIS deal?"
        
        try:
            function_name = self.config['lambda_functions']['deal_analysis_agent']['function_name']
            
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                Payload=json.dumps({"query": test_query})
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('success'):
                logger.info("✅ Deal Analysis Agent test passed")
                logger.info(f"Sample analysis: {result.get('analysis', '')[:200]}...")
            else:
                logger.error(f"❌ Deal Analysis Agent test failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Deal Analysis Agent test error: {str(e)}")
    
    def save_config(self):
        """Save updated configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        logger.info("📄 Configuration saved")
    
    def deploy_v4(self):
        """Deploy complete V4 architecture"""
        logger.info("🚀 Starting V4 Architecture Deployment")
        
        deployment_steps = [
            ("Create Claude 3.7 Inference Profile", self.create_inference_profile),
            ("Deploy Deal Analysis Agent Lambda", self.deploy_deal_analysis_agent_lambda),
            ("Create Data Agent V4", self.create_data_agent),
            ("Create Web Search Agent V4", self.create_web_search_agent),
            ("Create Execution Agent V4", self.create_execution_agent),
            ("Create Deal Analysis Agent V4", self.create_deal_analysis_agent),
            ("Create Manager Agent V4", self.create_manager_agent),
            ("Prepare Agents", self.prepare_agents),
            ("Create Agent Aliases", self.create_agent_aliases),
            ("Test Deal Analysis Agent", self.test_deal_analysis_agent)
        ]
        
        for step_name, step_function in deployment_steps:
            try:
                logger.info(f"📋 {step_name}")
                step_function()
                logger.info(f"✅ {step_name} completed")
            except Exception as e:
                logger.error(f"❌ {step_name} failed: {str(e)}")
                raise
        
        logger.info("🎉 V4 Architecture deployment completed successfully!")
        logger.info("📊 V4 Agents Created:")
        logger.info(f"   • Manager Agent V4: {self.config['manager_agent']['agent_id']}")
        logger.info(f"   • Deal Analysis Agent V4: {self.config['deal_analysis_agent']['agent_id']}")
        logger.info(f"   • Data Agent V4: {self.config['data_agent']['agent_id']}")
        logger.info(f"   • Web Search Agent V4: {self.config['web_search_agent']['agent_id']}")
        logger.info(f"   • Execution Agent V4: {self.config['execution_agent']['agent_id']}")
        logger.info("🏷️ All agents tagged with Version=V4 for easy identification")
        
        return True

def main():
    """Main deployment function"""
    try:
        deployer = V4Deployer()
        deployer.deploy_v4()
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()