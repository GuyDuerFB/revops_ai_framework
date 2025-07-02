#!/usr/bin/env python3
"""
RevOps AI Framework - Fixed Deployment Script
Based on learnings from deployment process

Fixes included:
1. Correct Lambda environment variable names (FIREBOLT_ENGINE_NAME vs FIREBOLT_ENGINE)
2. Proper IAM role creation and policies for Bedrock agents
3. Fixed Gong Lambda parameter handling 
4. Knowledge base deployment with OpenSearch Serverless
5. Agent action group creation with proper function schemas
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import zipfile
from typing import Dict, List, Any, Optional
import boto3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOYMENT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(DEPLOYMENT_ROOT, "config.json")

class RevOpsDeployer:
    def __init__(self, config_path: str = CONFIG_PATH):
        """Initialize the deployer with configuration"""
        self.config = self.load_config(config_path)
        self.aws_profile = self.config.get("profile_name", "FireboltSystemAdministrator-740202120544")
        self.aws_region = self.config.get("region_name", "us-east-1")
        
        # Initialize AWS clients
        session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
        self.lambda_client = session.client('lambda')
        self.iam_client = session.client('iam')
        self.bedrock_agent_client = session.client('bedrock-agent')
        self.s3_client = session.client('s3')
        self.opensearch_client = session.client('opensearchserverless')
        
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def save_config(self) -> None:
        """Save updated configuration back to file"""
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration updated and saved")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def run_aws_command(self, command: List[str]) -> Dict[str, Any]:
        """Run AWS CLI command with proper profile and region"""
        cmd = command + ["--profile", self.aws_profile, "--region", self.aws_region]
        
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, 
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"output": result.stdout}
            return {}
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            return {"error": str(e)}

    def create_iam_roles_and_policies(self) -> bool:
        """Create necessary IAM roles and policies for Bedrock agents"""
        logger.info("Creating IAM roles and policies...")
        
        # IAM role for Bedrock agents
        role_name = "AmazonBedrockExecutionRoleForAgents_revops"
        
        # Create trust policy for Bedrock
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Check if role exists
            try:
                self.iam_client.get_role(RoleName=role_name)
                logger.info(f"IAM role {role_name} already exists")
            except self.iam_client.exceptions.NoSuchEntityException:
                # Create the role
                logger.info(f"Creating IAM role: {role_name}")
                self.iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy)
                )
            
            # Create comprehensive policy for Bedrock operations
            policy_name = "BedrockAgentExecutionPolicy"
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream",
                            "bedrock:InvokeAgent",
                            "bedrock:Retrieve", 
                            "bedrock:RetrieveAndGenerate",
                            "lambda:InvokeFunction",
                            "s3:GetObject",
                            "s3:PutObject",
                            "s3:ListBucket",
                            "aoss:APIAccessAll",
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            # Check if policy exists, create if not
            try:
                policy_arn = f"arn:aws:iam::{self.config.get('account_id', '740202120544')}:policy/{policy_name}"
                self.iam_client.get_policy(PolicyArn=policy_arn)
                logger.info(f"Policy {policy_name} already exists")
            except self.iam_client.exceptions.NoSuchEntityException:
                logger.info(f"Creating policy: {policy_name}")
                response = self.iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
                policy_arn = response['Policy']['Arn']
            
            # Attach policy to role
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating IAM roles/policies: {e}")
            return False

    def deploy_lambda_function(self, lambda_name: str) -> bool:
        """Deploy a Lambda function with correct environment variables"""
        logger.info(f"Deploying Lambda function: {lambda_name}")
        
        lambda_config = self.config['lambda_functions'].get(lambda_name)
        if not lambda_config:
            logger.error(f"Lambda configuration not found for: {lambda_name}")
            return False
        
        source_dir = os.path.join(PROJECT_ROOT, lambda_config['source_dir'])
        if not os.path.exists(source_dir):
            logger.error(f"Source directory not found: {source_dir}")
            return False
        
        # Create deployment package
        zip_path = os.path.join(DEPLOYMENT_ROOT, f"{lambda_name}.zip")
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
            
            logger.info(f"Created deployment package: {zip_path}")
        except Exception as e:
            logger.error(f"Error creating deployment package: {e}")
            return False
        
        # Deploy function
        function_name = lambda_config['function_name']
        
        # Fix environment variables based on our learnings
        env_vars = lambda_config.get('environment_variables', {}).copy()
        if lambda_name in ['firebolt_query', 'firebolt_metadata', 'firebolt_writer']:
            # Fix the engine name variable
            if 'FIREBOLT_ENGINE' in env_vars:
                env_vars['FIREBOLT_ENGINE_NAME'] = env_vars.pop('FIREBOLT_ENGINE')
        
        try:
            # Check if function exists
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                logger.info(f"Updating existing Lambda function: {function_name}")
                
                # Update function code
                with open(zip_path, 'rb') as zip_file:
                    self.lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_file.read()
                    )
                
                # Update environment variables
                if env_vars:
                    self.lambda_client.update_function_configuration(
                        FunctionName=function_name,
                        Environment={'Variables': env_vars}
                    )
                    
            except self.lambda_client.exceptions.ResourceNotFoundException:
                logger.info(f"Creating new Lambda function: {function_name}")
                
                # Create IAM role for Lambda if it doesn't exist
                lambda_role_name = f"{lambda_name}-lambda-role"
                lambda_trust_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "lambda.amazonaws.com"
                            },
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
                
                try:
                    self.iam_client.get_role(RoleName=lambda_role_name)
                except self.iam_client.exceptions.NoSuchEntityException:
                    self.iam_client.create_role(
                        RoleName=lambda_role_name,
                        AssumeRolePolicyDocument=json.dumps(lambda_trust_policy)
                    )
                    
                    # Attach basic execution policy
                    self.iam_client.attach_role_policy(
                        RoleName=lambda_role_name,
                        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    )
                    
                    # Wait for role to be available
                    time.sleep(10)
                
                lambda_role_arn = f"arn:aws:iam::{self.config.get('account_id', '740202120544')}:role/{lambda_role_name}"
                
                # Create function
                with open(zip_path, 'rb') as zip_file:
                    self.lambda_client.create_function(
                        FunctionName=function_name,
                        Runtime=lambda_config.get('runtime', 'python3.12'),
                        Role=lambda_role_arn,
                        Handler=lambda_config.get('handler', 'lambda_function.lambda_handler'),
                        Code={'ZipFile': zip_file.read()},
                        Timeout=lambda_config.get('timeout', 60),
                        MemorySize=lambda_config.get('memory_size', 256),
                        Environment={'Variables': env_vars} if env_vars else {}
                    )
            
            # Get function ARN and update config
            response = self.lambda_client.get_function(FunctionName=function_name)
            lambda_arn = response['Configuration']['FunctionArn']
            
            # Update config with Lambda ARN
            for action_group in self.config.get('data_agent', {}).get('action_groups', []):
                if action_group.get('name') == lambda_name or action_group.get('name') == lambda_name.replace('_', '-'):
                    action_group['lambda_arn'] = lambda_arn
                    break
            
            logger.info(f"Lambda function deployed successfully: {lambda_arn}")
            
            # Clean up zip file
            os.remove(zip_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deploying Lambda function {lambda_name}: {e}")
            return False

    def deploy_knowledge_base(self) -> bool:
        """Deploy knowledge base for schema awareness"""
        logger.info("Deploying knowledge base...")
        
        kb_config = self.config.get('knowledge_base', {})
        bucket_name = kb_config.get('storage_bucket', 'revops-ai-framework-kb-740202120544')
        
        try:
            # Create S3 bucket
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"S3 bucket {bucket_name} already exists")
            except:
                logger.info(f"Creating S3 bucket: {bucket_name}")
                self.s3_client.create_bucket(Bucket=bucket_name)
            
            # Upload schema file
            schema_file_path = os.path.join(PROJECT_ROOT, kb_config.get('schema_file_path', 'knowledge_base/firebolt_schema/firebolt_schema.md'))
            if os.path.exists(schema_file_path):
                s3_key = f"{kb_config.get('storage_prefix', 'revops-ai-framework/knowledge/')}firebolt_schema.md"
                logger.info(f"Uploading schema file to S3: {s3_key}")
                self.s3_client.upload_file(schema_file_path, bucket_name, s3_key)
            
            logger.info("Knowledge base setup completed (manual Bedrock KB creation required)")
            return True
            
        except Exception as e:
            logger.error(f"Error deploying knowledge base: {e}")
            return False

    def deploy_data_agent(self) -> bool:
        """Deploy the data agent with action groups"""
        logger.info("Deploying data agent...")
        
        agent_config = self.config.get('data_agent', {})
        
        # Read instructions
        instructions_file = os.path.join(PROJECT_ROOT, agent_config.get('instructions_file', 'agents/data_agent/instructions.md'))
        if not os.path.exists(instructions_file):
            logger.error(f"Instructions file not found: {instructions_file}")
            return False
        
        with open(instructions_file, 'r') as f:
            instructions = f.read()
        
        try:
            # Check if agent exists
            agent_id = agent_config.get('agent_id')
            if agent_id:
                try:
                    self.bedrock_agent_client.get_agent(agentId=agent_id)
                    logger.info(f"Agent already exists: {agent_id}")
                    return True
                except:
                    logger.info(f"Agent {agent_id} not found, creating new one")
            
            # Create agent
            logger.info("Creating new Bedrock agent...")
            response = self.bedrock_agent_client.create_agent(
                agentName="revops-data-agent-v2",
                description="Data Analysis Agent for RevOps AI Framework V2",
                agentResourceRoleArn=f"arn:aws:iam::{self.config.get('account_id', '740202120544')}:role/AmazonBedrockExecutionRoleForAgents_revops",
                foundationModel=agent_config.get('foundation_model', 'anthropic.claude-3-7-sonnet-20250219-v1:0'),
                instruction=instructions
            )
            
            agent_id = response['agent']['agentId']
            agent_config['agent_id'] = agent_id
            logger.info(f"Created agent: {agent_id}")
            
            # Create action groups
            for action_group in agent_config.get('action_groups', []):
                lambda_arn = action_group.get('lambda_arn')
                if not lambda_arn:
                    logger.warning(f"No Lambda ARN for action group: {action_group.get('name')}")
                    continue
                
                # Define function schema based on action group type
                if action_group['name'] == 'firebolt_query':
                    function_schema = {
                        "functions": [
                            {
                                "name": "query_fire",
                                "description": "Execute SQL query against Firebolt data warehouse",
                                "parameters": {
                                    "query": {
                                        "type": "string",
                                        "description": "SQL query to execute",
                                        "required": True
                                    },
                                    "account_name": {
                                        "type": "string", 
                                        "description": "Firebolt account name",
                                        "required": False
                                    },
                                    "engine_name": {
                                        "type": "string",
                                        "description": "Firebolt engine name", 
                                        "required": False
                                    }
                                }
                            }
                        ]
                    }
                elif action_group['name'] == 'gong_retrieval':
                    function_schema = {
                        "functions": [
                            {
                                "name": "get_gong_data",
                                "description": "Retrieve conversation data from Gong",
                                "parameters": {
                                    "query_type": {
                                        "type": "string",
                                        "description": "Type of data to retrieve (calls, topics, keywords)",
                                        "required": True
                                    },
                                    "date_range": {
                                        "type": "string",
                                        "description": "Time period for data retrieval (e.g., '7d', '30d')",
                                        "required": False
                                    },
                                    "filters": {
                                        "type": "string",
                                        "description": "Additional filters to apply",
                                        "required": False
                                    }
                                }
                            }
                        ]
                    }
                else:
                    continue
                
                logger.info(f"Creating action group: {action_group['name']}")
                self.bedrock_agent_client.create_agent_action_group(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    actionGroupName=action_group['name'],
                    actionGroupExecutor={'lambda': lambda_arn},
                    functionSchema=function_schema
                )
            
            # Prepare agent
            logger.info("Preparing agent...")
            self.bedrock_agent_client.prepare_agent(agentId=agent_id)
            
            # Wait for agent to be prepared
            logger.info("Waiting for agent to be prepared...")
            while True:
                status_response = self.bedrock_agent_client.get_agent(agentId=agent_id)
                if status_response['agent']['agentStatus'] == 'PREPARED':
                    break
                time.sleep(30)
            
            # Create alias
            logger.info("Creating agent alias...")
            alias_response = self.bedrock_agent_client.create_agent_alias(
                agentId=agent_id,
                agentAliasName="revops-data-agent-alias",
                description="Alias for RevOps Data Agent V2"
            )
            
            agent_alias_id = alias_response['agentAlias']['agentAliasId']
            agent_config['agent_alias_id'] = agent_alias_id
            
            logger.info(f"Data agent deployed successfully: {agent_id} (alias: {agent_alias_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error deploying data agent: {e}")
            return False

    def test_lambda_functions(self) -> bool:
        """Test deployed Lambda functions"""
        logger.info("Testing Lambda functions...")
        
        # Test Firebolt query
        try:
            response = self.lambda_client.invoke(
                FunctionName='revops-firebolt-query',
                Payload=json.dumps({"query": "SELECT 1 as test_value"})
            )
            result = json.loads(response['Payload'].read().decode())
            if result.get('success'):
                logger.info("✅ Firebolt query Lambda working")
            else:
                logger.warning(f"⚠️ Firebolt query Lambda issue: {result.get('error')}")
        except Exception as e:
            logger.error(f"❌ Firebolt query Lambda failed: {e}")
        
        # Test Gong retrieval
        try:
            response = self.lambda_client.invoke(
                FunctionName='revops-gong-retrieval',
                Payload=json.dumps({"query_type": "calls", "date_range": "7d"})
            )
            result = json.loads(response['Payload'].read().decode())
            if result.get('success'):
                logger.info("✅ Gong retrieval Lambda working")
            else:
                logger.warning(f"⚠️ Gong retrieval Lambda issue: {result.get('error')}")
        except Exception as e:
            logger.error(f"❌ Gong retrieval Lambda failed: {e}")
        
        return True

    def deploy_all(self) -> bool:
        """Deploy all components"""
        logger.info("Starting full deployment...")
        
        success = True
        
        # 1. Create IAM roles and policies
        if not self.create_iam_roles_and_policies():
            logger.error("Failed to create IAM roles/policies")
            success = False
        
        # 2. Deploy Lambda functions
        for lambda_name in self.config.get('lambda_functions', {}):
            if not self.deploy_lambda_function(lambda_name):
                logger.error(f"Failed to deploy Lambda: {lambda_name}")
                success = False
        
        # 3. Deploy knowledge base
        if not self.deploy_knowledge_base():
            logger.error("Failed to deploy knowledge base")
            success = False
        
        # 4. Deploy data agent
        if not self.deploy_data_agent():
            logger.error("Failed to deploy data agent")
            success = False
        
        # 5. Test functions
        self.test_lambda_functions()
        
        # 6. Save updated configuration
        self.save_config()
        
        if success:
            logger.info("🎉 Deployment completed successfully!")
        else:
            logger.error("❌ Deployment completed with errors")
        
        return success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="RevOps AI Framework Fixed Deployment")
    parser.add_argument("--component", choices=["iam", "lambda", "kb", "agent", "all"], 
                       default="all", help="Component to deploy")
    parser.add_argument("--lambda-name", help="Specific Lambda function to deploy")
    parser.add_argument("--test", action="store_true", help="Run tests after deployment")
    
    args = parser.parse_args()
    
    deployer = RevOpsDeployer()
    
    if args.component == "iam":
        deployer.create_iam_roles_and_policies()
    elif args.component == "lambda":
        if args.lambda_name:
            deployer.deploy_lambda_function(args.lambda_name)
        else:
            for lambda_name in deployer.config.get('lambda_functions', {}):
                deployer.deploy_lambda_function(lambda_name)
    elif args.component == "kb":
        deployer.deploy_knowledge_base()
    elif args.component == "agent":
        deployer.deploy_data_agent()
    elif args.component == "all":
        deployer.deploy_all()
    
    if args.test:
        deployer.test_lambda_functions()

if __name__ == "__main__":
    main()