#!/usr/bin/env python3
"""
Firebolt RevOps AI Framework V2 - Deployment Automation

This script automates the deployment of Firebolt RevOps AI Framework V2, including:
- AWS Bedrock agents (Data, Decision, Execution)
- Knowledge bases for schema and business logic
- Lambda functions for data operations and integrations
- Bedrock flows for orchestration
- AWS Secrets management

Usage:
    python deploy.py --config config.json --secrets secrets.json [--deploy-all]
    python deploy.py --deploy-agents --config config.json
"""

import os
import sys
import json
import time
import argparse
import boto3
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("deployment/deployment.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("revops-deployment")

# Constants
DEFAULT_CONFIG_PATH = "deployment/config_template.json"
DEFAULT_SECRETS_PATH = "deployment/secrets.json"
DEFAULT_REGION = "us-east-1"

class RevOpsDeployer:
    """Main class for deploying the RevOps AI Framework V2"""
    
    def __init__(self, config_path: str, secrets_path: str, region: str = DEFAULT_REGION):
        """Initialize the deployer with configuration"""
        self.config_path = config_path
        self.secrets_path = secrets_path
        self.region = region
        self.base_path = Path(__file__).parent.parent.absolute()
        
        # Load configs
        self.config = self._load_json(config_path)
        self.secrets = self._load_json(secrets_path) if Path(secrets_path).exists() else {}
        
        # Initialize AWS clients
        self.bedrock = boto3.client('bedrock', region_name=region)
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.secrets_manager = boto3.client('secretsmanager', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        
        # Track deployed resources
        self.deployed_resources = {
            "agents": {},
            "knowledge_bases": {},
            "lambda_functions": {},
            "secrets": {},
            "flows": {}
        }
    
    def _load_json(self, path: str) -> Dict[str, Any]:
        """Load JSON configuration from file"""
        try:
            with open(path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning(f"File not found: {path}")
            if "template" in path:
                # If it's a template, return empty dict
                return {}
            else:
                raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {path}")
            raise
    
    def _save_deployment_state(self):
        """Save current deployment state to file"""
        state_file = Path(self.base_path) / "deployment" / "deployment_state.json"
        state = {
            "timestamp": datetime.now().isoformat(),
            "region": self.region,
            "resources": self.deployed_resources
        }
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Deployment state saved to {state_file}")
    
    def deploy_secrets(self):
        """Deploy secrets to AWS Secrets Manager"""
        logger.info("Deploying secrets to AWS Secrets Manager...")
        
        secrets_config = self.config.get("secrets", {})
        deployed_secrets = {}
        
        for secret_name, secret_config in secrets_config.items():
            full_secret_name = f"revops-ai-framework/{secret_name}"
            
            # Get secret value from secrets file
            secret_type = secret_config.get("type")
            if not secret_type or secret_type not in self.secrets:
                logger.warning(f"Secret type '{secret_type}' not found in secrets file")
                continue
            
            secret_value = self.secrets.get(secret_type, {})
            if not secret_value:
                logger.warning(f"Empty secret for '{secret_type}'")
                continue
            
            try:
                # Check if secret already exists
                try:
                    self.secrets_manager.describe_secret(SecretId=full_secret_name)
                    # Secret exists, update it
                    response = self.secrets_manager.update_secret(
                        SecretId=full_secret_name,
                        SecretString=json.dumps(secret_value)
                    )
                    logger.info(f"Updated existing secret: {full_secret_name}")
                except self.secrets_manager.exceptions.ResourceNotFoundException:
                    # Secret doesn't exist, create it
                    response = self.secrets_manager.create_secret(
                        Name=full_secret_name,
                        Description=f"RevOps AI Framework - {secret_name}",
                        SecretString=json.dumps(secret_value),
                        Tags=[
                            {"Key": "Project", "Value": "RevOps-AI-Framework"},
                            {"Key": "Environment", "Value": "Production"}
                        ]
                    )
                    logger.info(f"Created new secret: {full_secret_name}")
                
                # Record the deployed secret
                deployed_secrets[secret_name] = {
                    "name": full_secret_name,
                    "arn": response.get("ARN")
                }
                
            except Exception as e:
                logger.error(f"Failed to deploy secret {secret_name}: {str(e)}")
        
        self.deployed_resources["secrets"] = deployed_secrets
        logger.info(f"Deployed {len(deployed_secrets)} secrets")
        
        return deployed_secrets
    
    def deploy_lambda_functions(self):
        """Deploy Lambda functions for RevOps AI Framework"""
        logger.info("Deploying Lambda functions...")
        
        lambda_configs = self.config.get("lambda_functions", {})
        deployed_functions = {}
        
        for func_name, func_config in lambda_configs.items():
            logger.info(f"Processing Lambda function: {func_name}")
            
            # Prepare Lambda function code
            source_path = Path(self.base_path) / func_config.get("source_path")
            if not source_path.exists():
                logger.error(f"Lambda source path does not exist: {source_path}")
                continue
            
            # Create a deployment package (zip file)
            package_path = self._create_lambda_package(source_path, func_name)
            if not package_path:
                logger.error(f"Failed to create Lambda package for {func_name}")
                continue
            
            # Read the zip file
            with open(package_path, 'rb') as file:
                code_binary = file.read()
            
            # Prepare environment variables
            environment = {
                "Variables": {
                    "AWS_REGION": self.region
                }
            }
            
            # Add any custom environment variables
            if "environment" in func_config:
                for key, value in func_config["environment"].items():
                    # If the value references a secret, get the ARN
                    if key.endswith("_SECRET") and value in self.deployed_resources["secrets"]:
                        environment["Variables"][key] = self.deployed_resources["secrets"][value]["name"]
                    else:
                        environment["Variables"][key] = value
            
            # Get or create IAM role for the Lambda
            role_arn = self._get_or_create_lambda_role(func_name, func_config.get("permissions", []))
            if not role_arn:
                logger.error(f"Failed to get or create IAM role for {func_name}")
                continue
            
            try:
                # Check if Lambda function already exists
                try:
                    function_info = self.lambda_client.get_function(FunctionName=func_name)
                    # Update existing function
                    response = self.lambda_client.update_function_code(
                        FunctionName=func_name,
                        ZipFile=code_binary
                    )
                    
                    # Update configuration if needed
                    self.lambda_client.update_function_configuration(
                        FunctionName=func_name,
                        Runtime=func_config.get("runtime", "python3.11"),
                        Handler=func_config.get("handler", "lambda_function.lambda_handler"),
                        Environment=environment,
                        Timeout=func_config.get("timeout", 30),
                        MemorySize=func_config.get("memory", 256)
                    )
                    
                    logger.info(f"Updated existing Lambda function: {func_name}")
                    
                except self.lambda_client.exceptions.ResourceNotFoundException:
                    # Create new function
                    response = self.lambda_client.create_function(
                        FunctionName=func_name,
                        Runtime=func_config.get("runtime", "python3.11"),
                        Role=role_arn,
                        Handler=func_config.get("handler", "lambda_function.lambda_handler"),
                        Code={
                            'ZipFile': code_binary
                        },
                        Environment=environment,
                        Timeout=func_config.get("timeout", 30),
                        MemorySize=func_config.get("memory", 256),
                        Tags={
                            "Project": "RevOps-AI-Framework",
                            "Component": func_config.get("type", "tool")
                        }
                    )
                    
                    logger.info(f"Created new Lambda function: {func_name}")
                
                # Wait for function to be ready (active)
                wait_count = 0
                while wait_count < 10:  # Wait for up to 10 checks
                    function_info = self.lambda_client.get_function(FunctionName=func_name)
                    if function_info["Configuration"]["State"] == "Active":
                        break
                    logger.info(f"Waiting for Lambda function to become active: {func_name}")
                    time.sleep(3)
                    wait_count += 1
                
                # Record the deployed function
                function_arn = function_info["Configuration"]["FunctionArn"]
                deployed_functions[func_name] = {
                    "name": func_name,
                    "arn": function_arn,
                    "type": func_config.get("type", "tool"),
                }
                
                # Add Lambda permission for Bedrock Agent to invoke (if needed)
                if func_config.get("type") == "agent_action":
                    try:
                        self.lambda_client.add_permission(
                            FunctionName=func_name,
                            StatementId=f"bedrock-agent-invoke-{int(time.time())}",
                            Action="lambda:InvokeFunction",
                            Principal="bedrock.amazonaws.com",
                        )
                        logger.info(f"Added Bedrock invoke permission for {func_name}")
                    except self.lambda_client.exceptions.ResourceConflictException:
                        # Permission already exists
                        logger.info(f"Bedrock invoke permission already exists for {func_name}")
                
            except Exception as e:
                logger.error(f"Failed to deploy Lambda function {func_name}: {str(e)}")
        
        self.deployed_resources["lambda_functions"] = deployed_functions
        logger.info(f"Deployed {len(deployed_functions)} Lambda functions")
        
        return deployed_functions
    
    def _create_lambda_package(self, source_path: Path, func_name: str) -> Optional[str]:
        """Create a deployment package (zip file) for a Lambda function"""
        import shutil
        import zipfile
        import subprocess
        import tempfile
        
        try:
            # Create a temporary directory to prepare the package
            with tempfile.TemporaryDirectory() as temp_dir:
                package_dir = Path(temp_dir)
                
                # Check if source is a file or directory
                if source_path.is_file():
                    # Single file Lambda
                    target_file = package_dir / source_path.name
                    shutil.copy(source_path, target_file)
                else:
                    # Directory with multiple files
                    for item in source_path.glob('**/*'):
                        if item.is_file():
                            # Create relative path structure
                            rel_path = item.relative_to(source_path)
                            target_file = package_dir / rel_path
                            target_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy(item, target_file)
                
                # Check for requirements.txt and install dependencies
                req_file = source_path / "requirements.txt" if source_path.is_dir() else source_path.parent / "requirements.txt"
                if req_file.exists():
                    logger.info(f"Installing dependencies for {func_name} from {req_file}")
                    try:
                        subprocess.run(
                            [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-t", str(package_dir)],
                            check=True, capture_output=True
                        )
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to install dependencies: {e.stderr.decode()}")
                
                # Create zip file
                zip_path = Path(self.base_path) / "deployment" / "lambda_packages" / f"{func_name}.zip"
                zip_path.parent.mkdir(parents=True, exist_ok=True)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for item in package_dir.glob('**/*'):
                        if item.is_file():
                            zipf.write(item, item.relative_to(package_dir))
                
                logger.info(f"Created Lambda package: {zip_path}")
                return str(zip_path)
        
        except Exception as e:
            logger.error(f"Failed to create Lambda package: {str(e)}")
            return None
    
    def _get_or_create_lambda_role(self, func_name: str, permissions: List[str]) -> Optional[str]:
        """Get or create IAM role for Lambda function"""
        role_name = f"RevOpsAIFramework-{func_name}-Role"
        
        try:
            # Check if role already exists
            try:
                response = self.iam.get_role(RoleName=role_name)
                logger.info(f"Using existing IAM role: {role_name}")
                return response["Role"]["Arn"]
            except self.iam.exceptions.NoSuchEntityException:
                # Create new role
                assume_role_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole"
                        }
                    ]
                }
                
                response = self.iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                    Description=f"Role for RevOps AI Framework Lambda function: {func_name}"
                )
                
                # Attach basic Lambda execution policy
                self.iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                )
                
                # Attach additional policies based on permissions needed
                policy_arns = []
                if "secretsmanager" in permissions:
                    policy_arns.append("arn:aws:iam::aws:policy/SecretsManagerReadWrite")
                if "s3" in permissions:
                    policy_arns.append("arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess")
                if "bedrock" in permissions:
                    policy_arns.append("arn:aws:iam::aws:policy/AmazonBedrockFullAccess")
                
                for policy_arn in policy_arns:
                    self.iam.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy_arn
                    )
                
                # Wait for role to be available
                time.sleep(10)
                
                logger.info(f"Created new IAM role: {role_name}")
                return response["Role"]["Arn"]
        
        except Exception as e:
            logger.error(f"Failed to get or create IAM role: {str(e)}")
            return None
    
    def deploy_knowledge_bases(self):
        """Deploy knowledge bases for RevOps AI Framework"""
        logger.info("Deploying knowledge bases...")
        
        kb_configs = self.config.get("knowledge_bases", {})
        deployed_kbs = {}
        
        # Create S3 bucket for knowledge base files if it doesn't exist
        kb_bucket = f"revops-ai-framework-kb-{int(time.time())}-{self.region}"
        try:
            self.s3.create_bucket(
                Bucket=kb_bucket,
                CreateBucketConfiguration={
                    'LocationConstraint': self.region if self.region != 'us-east-1' else ''
                }
            )
            logger.info(f"Created S3 bucket for knowledge bases: {kb_bucket}")
        except Exception as e:
            logger.error(f"Failed to create S3 bucket: {str(e)}")
            # Try to use an existing bucket with a more generic name
            kb_bucket = f"revops-ai-framework-kb"
        
        for kb_name, kb_config in kb_configs.items():
            logger.info(f"Processing knowledge base: {kb_name}")
            
            # Prepare knowledge base files
            content_path = Path(self.base_path) / kb_config.get("content_path")
            if not content_path.exists():
                logger.error(f"Knowledge base content path does not exist: {content_path}")
                continue
            
            # Upload knowledge base files to S3
            s3_prefix = f"knowledge-bases/{kb_name}/"
            kb_files = []
            
            if content_path.is_file():
                # Upload single file
                file_key = f"{s3_prefix}{content_path.name}"
                try:
                    self.s3.upload_file(str(content_path), kb_bucket, file_key)
                    kb_files.append({
                        "name": content_path.name,
                        "s3_key": file_key
                    })
                    logger.info(f"Uploaded knowledge base file: {file_key}")
                except Exception as e:
                    logger.error(f"Failed to upload file {content_path.name}: {str(e)}")
            else:
                # Upload directory of files
                for item in content_path.glob('**/*'):
                    if item.is_file():
                        rel_path = item.relative_to(content_path)
                        file_key = f"{s3_prefix}{rel_path}"
                        try:
                            self.s3.upload_file(str(item), kb_bucket, file_key)
                            kb_files.append({
                                "name": str(rel_path),
                                "s3_key": file_key
                            })
                            logger.info(f"Uploaded knowledge base file: {file_key}")
                        except Exception as e:
                            logger.error(f"Failed to upload file {rel_path}: {str(e)}")
            
            if not kb_files:
                logger.error(f"No files uploaded for knowledge base: {kb_name}")
                continue
            
            # Create Bedrock knowledge base
            try:
                # Check if knowledge base already exists
                existing_kb_id = None
                try:
                    # List knowledge bases to find if this one exists
                    paginator = self.bedrock_agent.get_paginator('list_knowledge_bases')
                    page_iterator = paginator.paginate()
                    
                    for page in page_iterator:
                        for kb in page.get("knowledgeBases", []):
                            if kb["name"] == f"RevOpsAIFramework-{kb_name}":
                                existing_kb_id = kb["knowledgeBaseId"]
                                break
                        if existing_kb_id:
                            break
                except Exception as e:
                    logger.warning(f"Error listing knowledge bases: {str(e)}")
                
                if existing_kb_id:
                    # Update existing knowledge base
                    response = self.bedrock_agent.update_knowledge_base(
                        knowledgeBaseId=existing_kb_id,
                        description=kb_config.get("description", f"RevOps AI Framework - {kb_name} Knowledge Base"),
                        roleArn=kb_config.get("role_arn")  # Assuming role ARN is provided
                    )
                    kb_id = existing_kb_id
                    logger.info(f"Updated existing knowledge base: {kb_name} ({kb_id})")
                else:
                    # Create new knowledge base
                    response = self.bedrock_agent.create_knowledge_base(
                        name=f"RevOpsAIFramework-{kb_name}",
                        description=kb_config.get("description", f"RevOps AI Framework - {kb_name} Knowledge Base"),
                        roleArn=kb_config.get("role_arn"),  # Assuming role ARN is provided
                        knowledgeBaseConfiguration={
                            "type": kb_config.get("type", "VECTOR"),
                            "vectorKnowledgeBaseConfiguration": {
                                "embeddingModelArn": kb_config.get("embedding_model", "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1")
                            }
                        },
                        storageConfiguration={
                            "type": "S3",
                            "s3Configuration": {
                                "bucketName": kb_bucket,
                                "bucketOwner": "" # Leave empty to use the caller's account
                            }
                        },
                        tags={
                            "Project": "RevOps-AI-Framework",
                            "Component": kb_name
                        }
                    )
                    
                    kb_id = response["knowledgeBase"]["knowledgeBaseId"]
                    logger.info(f"Created new knowledge base: {kb_name} ({kb_id})")
                
                # Upload data sources to knowledge base
                for file_info in kb_files:
                    try:
                        source_response = self.bedrock_agent.create_data_source(
                            knowledgeBaseId=kb_id,
                            name=file_info["name"],
                            dataSourceConfiguration={
                                "type": "S3",
                                "s3Configuration": {
                                    "bucketName": kb_bucket,
                                    "inclusionPrefixes": [file_info["s3_key"]]
                                }
                            },
                            vectorIngestionConfiguration={
                                "chunkingConfiguration": kb_config.get("chunking_config", {
                                    "chunkingStrategy": "FIXED_SIZE",
                                    "fixedSizeChunkingConfiguration": {
                                        "maxTokens": 300,
                                        "overlapPercentage": 10
                                    }
                                })
                            }
                        )
                        
                        # Start ingestion
                        self.bedrock_agent.start_ingestion_job(
                            knowledgeBaseId=kb_id,
                            dataSourceId=source_response["dataSource"]["dataSourceId"]
                        )
                        
                        logger.info(f"Added data source {file_info['name']} to knowledge base {kb_name}")
                    except Exception as e:
                        logger.error(f"Failed to add data source {file_info['name']}: {str(e)}")
                
                # Record the deployed knowledge base
                deployed_kbs[kb_name] = {
                    "id": kb_id,
                    "name": f"RevOpsAIFramework-{kb_name}",
                    "s3_bucket": kb_bucket,
                    "s3_prefix": s3_prefix
                }
                
            except Exception as e:
                logger.error(f"Failed to deploy knowledge base {kb_name}: {str(e)}")
        
        self.deployed_resources["knowledge_bases"] = deployed_kbs
        logger.info(f"Deployed {len(deployed_kbs)} knowledge bases")
        
        return deployed_kbs
    
    def deploy_agents(self):
        """Deploy Bedrock agents for RevOps AI Framework"""
        logger.info("Deploying Bedrock agents...")
        
        agent_configs = self.config.get("agents", {})
        deployed_agents = {}
        
        for agent_name, agent_config in agent_configs.items():
            logger.info(f"Processing agent: {agent_name}")
            
            # Prepare agent instructions from file
            instructions_path = Path(self.base_path) / agent_config.get("instructions_path")
            if not instructions_path.exists():
                logger.error(f"Agent instructions file does not exist: {instructions_path}")
                continue
            
            # Read instructions
            try:
                with open(instructions_path, 'r') as file:
                    instructions = file.read()
            except Exception as e:
                logger.error(f"Failed to read instructions for agent {agent_name}: {str(e)}")
                continue
            
            # Prepare agent action groups
            action_groups = []
            for action_group_name, action_group_config in agent_config.get("action_groups", {}).items():
                # Get function ARNs from deployed Lambda functions
                functions = []
                for func_name in action_group_config.get("functions", []):
                    if func_name in self.deployed_resources["lambda_functions"]:
                        functions.append({
                            "name": func_name,
                            "description": action_group_config.get("function_descriptions", {}).get(func_name, ""),
                            "functionArn": self.deployed_resources["lambda_functions"][func_name]["arn"]
                        })
                    else:
                        logger.warning(f"Function {func_name} not found in deployed functions")
                
                # Create action group
                action_group = {
                    "actionGroupName": action_group_name,
                    "actionGroupExecutor": {
                        "lambda": {
                            "functions": functions
                        }
                    },
                    "description": action_group_config.get("description", f"Action group for {agent_name}")
                }
                
                action_groups.append(action_group)
            
            # Prepare knowledge base associations
            kb_associations = []
            for kb_name in agent_config.get("knowledge_bases", []):
                if kb_name in self.deployed_resources["knowledge_bases"]:
                    kb_info = self.deployed_resources["knowledge_bases"][kb_name]
                    kb_associations.append({
                        "knowledgeBaseId": kb_info["id"],
                        "description": f"Knowledge base {kb_name} for {agent_name}"
                    })
                else:
                    logger.warning(f"Knowledge base {kb_name} not found in deployed KBs")
            
            # Create or update the agent
            try:
                # Check if agent already exists
                existing_agent_id = None
                try:
                    # List agents to find if this one exists
                    paginator = self.bedrock_agent.get_paginator('list_agents')
                    page_iterator = paginator.paginate()
                    
                    for page in page_iterator:
                        for agent in page.get("agents", []):
                            if agent["agentName"] == f"RevOpsAIFramework-{agent_name}":
                                existing_agent_id = agent["agentId"]
                                break
                        if existing_agent_id:
                            break
                except Exception as e:
                    logger.warning(f"Error listing agents: {str(e)}")
                
                # Set foundation model
                foundation_model = agent_config.get("foundation_model", "anthropic.claude-3-7-sonnet-20250219-v1:0")
                
                if existing_agent_id:
                    # Update existing agent
                    response = self.bedrock_agent.update_agent(
                        agentId=existing_agent_id,
                        agentName=f"RevOpsAIFramework-{agent_name}",
                        description=agent_config.get("description", f"RevOps AI Framework - {agent_name} Agent"),
                        instructions=instructions,
                        foundationModel=foundation_model
                    )
                    agent_id = existing_agent_id
                    logger.info(f"Updated existing agent: {agent_name} ({agent_id})")
                    
                    # Update action groups - we need to handle them separately
                    for action_group in action_groups:
                        # Check if action group exists
                        try:
                            existing_groups = self.bedrock_agent.list_agent_action_groups(agentId=agent_id)
                            action_group_exists = False
                            
                            for group in existing_groups.get("agentActionGroups", []):
                                if group["actionGroupName"] == action_group["actionGroupName"]:
                                    action_group_exists = True
                                    # Update action group
                                    self.bedrock_agent.update_agent_action_group(
                                        agentId=agent_id,
                                        actionGroupId=group["actionGroupId"],
                                        actionGroupName=action_group["actionGroupName"],
                                        actionGroupExecutor=action_group["actionGroupExecutor"],
                                        description=action_group["description"]
                                    )
                                    logger.info(f"Updated action group {action_group['actionGroupName']} for agent {agent_name}")
                                    break
                            
                            if not action_group_exists:
                                # Create new action group
                                self.bedrock_agent.create_agent_action_group(
                                    agentId=agent_id,
                                    actionGroupName=action_group["actionGroupName"],
                                    actionGroupExecutor=action_group["actionGroupExecutor"],
                                    description=action_group["description"]
                                )
                                logger.info(f"Created new action group {action_group['actionGroupName']} for agent {agent_name}")
                                
                        except Exception as e:
                            logger.error(f"Failed to update action group {action_group['actionGroupName']}: {str(e)}")
                    
                    # Update knowledge base associations
                    # First disassociate any existing KBs
                    try:
                        existing_kbs = self.bedrock_agent.list_agent_knowledge_bases(agentId=agent_id)
                        for kb in existing_kbs.get("agentKnowledgeBases", []):
                            self.bedrock_agent.disassociate_agent_knowledge_base(
                                agentId=agent_id,
                                knowledgeBaseId=kb["knowledgeBaseId"]
                            )
                            logger.info(f"Disassociated KB {kb['knowledgeBaseId']} from agent {agent_name}")
                    except Exception as e:
                        logger.warning(f"Error managing KB associations: {str(e)}")
                    
                    # Associate new KBs
                    for kb_assoc in kb_associations:
                        try:
                            self.bedrock_agent.associate_agent_knowledge_base(
                                agentId=agent_id,
                                knowledgeBaseId=kb_assoc["knowledgeBaseId"],
                                description=kb_assoc["description"]
                            )
                            logger.info(f"Associated KB {kb_assoc['knowledgeBaseId']} with agent {agent_name}")
                        except Exception as e:
                            logger.error(f"Failed to associate KB: {str(e)}")
                    
                else:
                    # Create new agent
                    response = self.bedrock_agent.create_agent(
                        agentName=f"RevOpsAIFramework-{agent_name}",
                        description=agent_config.get("description", f"RevOps AI Framework - {agent_name} Agent"),
                        instructions=instructions,
                        foundationModel=foundation_model,
                        idleSessionTTLInSeconds=agent_config.get("idle_session_ttl", 1800),  # Default 30 minutes
                        tags={
                            "Project": "RevOps-AI-Framework",
                            "Component": agent_name
                        }
                    )
                    
                    agent_id = response["agent"]["agentId"]
                    logger.info(f"Created new agent: {agent_name} ({agent_id})")
                    
                    # Add action groups
                    for action_group in action_groups:
                        try:
                            self.bedrock_agent.create_agent_action_group(
                                agentId=agent_id,
                                actionGroupName=action_group["actionGroupName"],
                                actionGroupExecutor=action_group["actionGroupExecutor"],
                                description=action_group["description"]
                            )
                            logger.info(f"Added action group {action_group['actionGroupName']} to agent {agent_name}")
                        except Exception as e:
                            logger.error(f"Failed to add action group {action_group['actionGroupName']}: {str(e)}")
                    
                    # Associate knowledge bases
                    for kb_assoc in kb_associations:
                        try:
                            self.bedrock_agent.associate_agent_knowledge_base(
                                agentId=agent_id,
                                knowledgeBaseId=kb_assoc["knowledgeBaseId"],
                                description=kb_assoc["description"]
                            )
                            logger.info(f"Associated KB {kb_assoc['knowledgeBaseId']} with agent {agent_name}")
                        except Exception as e:
                            logger.error(f"Failed to associate KB: {str(e)}")
                
                # Prepare and start the agent alias
                try:
                    # Check if alias exists
                    alias_id = None
                    try:
                        aliases = self.bedrock_agent.list_agent_aliases(agentId=agent_id)
                        for alias in aliases.get("agentAliases", []):
                            if alias["agentAliasName"] == "TSTALIASID":
                                alias_id = alias["agentAliasId"]
                                break
                    except Exception as e:
                        logger.warning(f"Error checking agent aliases: {str(e)}")
                    
                    if alias_id:
                        # Update alias
                        self.bedrock_agent.update_agent_alias(
                            agentId=agent_id,
                            agentAliasId=alias_id,
                            agentAliasName="TSTALIASID",
                            description=f"RevOps AI Framework - {agent_name} Latest Version",
                            routingConfiguration={
                                "agentVersion": "DRAFT"
                            }
                        )
                        logger.info(f"Updated alias for agent {agent_name}")
                    else:
                        # Create alias
                        alias_resp = self.bedrock_agent.create_agent_alias(
                            agentId=agent_id,
                            agentAliasName="TSTALIASID",
                            description=f"RevOps AI Framework - {agent_name} Latest Version",
                            routingConfiguration={
                                "agentVersion": "DRAFT"
                            }
                        )
                        alias_id = alias_resp["agentAlias"]["agentAliasId"]
                        logger.info(f"Created alias for agent {agent_name}: {alias_id}")
                    
                    # Prepare agent for aliasing by creating a version
                    try:
                        # Check if there are any existing prepared versions
                        versions = self.bedrock_agent.list_agent_versions(agentId=agent_id)
                        has_prepared_version = any(v["status"] == "PREPARED" for v in versions.get("agentVersions", []))
                        
                        if not has_prepared_version:
                            # Prepare a new version
                            self.bedrock_agent.prepare_agent(
                                agentId=agent_id
                            )
                            logger.info(f"Prepared agent for deployment: {agent_name}")
                    except Exception as e:
                        logger.warning(f"Error preparing agent version: {str(e)}")
                        
                except Exception as e:
                    logger.error(f"Failed to create/update agent alias: {str(e)}")
                
                # Record the deployed agent
                deployed_agents[agent_name] = {
                    "id": agent_id,
                    "name": f"RevOpsAIFramework-{agent_name}",
                    "alias_id": alias_id
                }
                
            except Exception as e:
                logger.error(f"Failed to deploy agent {agent_name}: {str(e)}")
        
        self.deployed_resources["agents"] = deployed_agents
        logger.info(f"Deployed {len(deployed_agents)} agents")
        
        return deployed_agents
    
    def deploy_flows(self):
        """Deploy Bedrock flows for RevOps AI Framework"""
        logger.info("Deploying Bedrock flows...")
        
        flow_configs = self.config.get("flows", {})
        deployed_flows = {}
        
        for flow_name, flow_config in flow_configs.items():
            logger.info(f"Processing flow: {flow_name}")
            
            # Get agent references
            agent_nodes = {}
            for node_name, node_config in flow_config.get("nodes", {}).items():
                agent_name = node_config.get("agent")
                if agent_name in self.deployed_resources["agents"]:
                    agent_info = self.deployed_resources["agents"][agent_name]
                    agent_nodes[node_name] = {
                        "node_name": node_name,
                        "agent_id": agent_info["id"],
                        "alias_id": agent_info.get("alias_id"),
                        "prompt_template": node_config.get("prompt_template", "")
                    }
                else:
                    logger.warning(f"Agent {agent_name} not found for flow node {node_name}")
            
            if len(agent_nodes) < len(flow_config.get("nodes", {})):
                logger.error(f"Not all agents found for flow {flow_name}, skipping deployment")
                continue
            
            # Prepare flow definition
            flow_def = {
                "name": f"RevOpsAIFramework-{flow_name}",
                "description": flow_config.get("description", f"RevOps AI Framework - {flow_name} Flow"),
                "definition": {
                    "nodes": [],
                    "edges": []
                }
            }
            
            # Add nodes
            for node_name, node_info in agent_nodes.items():
                node = {
                    "name": node_name,
                    "type": "BedrockAgent",
                    "configuration": {
                        "agentAliasId": node_info["alias_id"],
                        "agentId": node_info["agent_id"]
                    }
                }
                
                # Add prompt template if provided
                if node_info["prompt_template"]:
                    node["configuration"]["promptOverrideTemplate"] = node_info["prompt_template"]
                
                flow_def["definition"]["nodes"].append(node)
            
            # Add input/output nodes
            flow_def["definition"]["nodes"].append({
                "name": "FlowInput",
                "type": "Input"
            })
            
            flow_def["definition"]["nodes"].append({
                "name": "FlowOutput",
                "type": "Output"
            })
            
            # Add edges between nodes
            for edge in flow_config.get("edges", []):
                flow_def["definition"]["edges"].append({
                    "name": f"{edge.get('source')}-{edge.get('target')}",
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "outputPath": edge.get("output_path", "output")
                })
            
            # Create or update the flow
            try:
                # Check if flow already exists
                existing_flow_id = None
                try:
                    # List flows to find if this one exists
                    paginator = self.bedrock_agent.get_paginator('list_flows')
                    page_iterator = paginator.paginate()
                    
                    for page in page_iterator:
                        for flow in page.get("flows", []):
                            if flow["name"] == f"RevOpsAIFramework-{flow_name}":
                                existing_flow_id = flow["flowId"]
                                break
                        if existing_flow_id:
                            break
                except Exception as e:
                    logger.warning(f"Error listing flows: {str(e)}")
                
                if existing_flow_id:
                    # Update existing flow
                    response = self.bedrock_agent.update_flow(
                        flowId=existing_flow_id,
                        name=f"RevOpsAIFramework-{flow_name}",
                        description=flow_config.get("description", f"RevOps AI Framework - {flow_name} Flow"),
                        definition=flow_def["definition"]
                    )
                    flow_id = existing_flow_id
                    logger.info(f"Updated existing flow: {flow_name} ({flow_id})")
                else:
                    # Create new flow
                    response = self.bedrock_agent.create_flow(
                        name=f"RevOpsAIFramework-{flow_name}",
                        description=flow_config.get("description", f"RevOps AI Framework - {flow_name} Flow"),
                        definition=flow_def["definition"],
                        tags={
                            "Project": "RevOps-AI-Framework",
                            "Component": flow_name
                        }
                    )
                    
                    flow_id = response["flow"]["flowId"]
                    logger.info(f"Created new flow: {flow_name} ({flow_id})")
                
                # Prepare and create an alias for the flow
                try:
                    # Create a new version of the flow
                    version_response = self.bedrock_agent.create_flow_version(
                        flowId=flow_id
                    )
                    flow_version = version_response["flowVersion"]["version"]
                    logger.info(f"Created flow version {flow_version} for flow {flow_name}")
                    
                    # Check if alias exists
                    alias_id = None
                    try:
                        aliases = self.bedrock_agent.list_flow_aliases(flowId=flow_id)
                        for alias in aliases.get("flowAliases", []):
                            if alias["flowAliasName"] == "TSTALIASID":
                                alias_id = alias["flowAliasId"]
                                break
                    except Exception as e:
                        logger.warning(f"Error checking flow aliases: {str(e)}")
                    
                    if alias_id:
                        # Update alias
                        self.bedrock_agent.update_flow_alias(
                            flowId=flow_id,
                            flowAliasId=alias_id,
                            flowAliasName="TSTALIASID",
                            description=f"RevOps AI Framework - {flow_name} Latest Version",
                            routingConfiguration={
                                "flowVersion": flow_version
                            }
                        )
                        logger.info(f"Updated alias for flow {flow_name}")
                    else:
                        # Create alias
                        alias_resp = self.bedrock_agent.create_flow_alias(
                            flowId=flow_id,
                            flowAliasName="TSTALIASID",
                            description=f"RevOps AI Framework - {flow_name} Latest Version",
                            routingConfiguration={
                                "flowVersion": flow_version
                            }
                        )
                        alias_id = alias_resp["flowAlias"]["flowAliasId"]
                        logger.info(f"Created alias for flow {flow_name}: {alias_id}")
                        
                except Exception as e:
                    logger.error(f"Failed to create/update flow alias: {str(e)}")
                
                # Record the deployed flow
                deployed_flows[flow_name] = {
                    "id": flow_id,
                    "name": f"RevOpsAIFramework-{flow_name}",
                    "alias_id": alias_id
                }
                
            except Exception as e:
                logger.error(f"Failed to deploy flow {flow_name}: {str(e)}")
        
        self.deployed_resources["flows"] = deployed_flows
        logger.info(f"Deployed {len(deployed_flows)} flows")
        
        return deployed_flows
    
    def deploy_all(self):
        """Deploy all components of the RevOps AI Framework"""
        logger.info("Deploying all RevOps AI Framework components...")
        
        # Deploy in order of dependencies
        self.deploy_secrets()
        self.deploy_lambda_functions()
        self.deploy_knowledge_bases()
        self.deploy_agents()
        self.deploy_flows()
        
        # Save final deployment state
        self._save_deployment_state()
        
        logger.info("Deployment completed successfully")
        return self.deployed_resources


def main():
    """Main entry point for the deployment script"""
    parser = argparse.ArgumentParser(description="Deploy RevOps AI Framework V2 components to AWS")
    
    parser.add_argument("--config", type=str, default=DEFAULT_CONFIG_PATH,
                        help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})")
    parser.add_argument("--secrets", type=str, default=DEFAULT_SECRETS_PATH,
                        help=f"Path to secrets file (default: {DEFAULT_SECRETS_PATH})")
    parser.add_argument("--region", type=str, default=DEFAULT_REGION,
                        help=f"AWS region (default: {DEFAULT_REGION})")
    
    # Component-specific deployment options
    parser.add_argument("--deploy-all", action="store_true",
                        help="Deploy all components")
    parser.add_argument("--deploy-secrets", action="store_true",
                        help="Deploy only secrets")
    parser.add_argument("--deploy-lambdas", action="store_true",
                        help="Deploy only Lambda functions")
    parser.add_argument("--deploy-knowledge-bases", action="store_true",
                        help="Deploy only knowledge bases")
    parser.add_argument("--deploy-agents", action="store_true",
                        help="Deploy only Bedrock agents")
    parser.add_argument("--deploy-flows", action="store_true",
                        help="Deploy only Bedrock flows")
    
    args = parser.parse_args()
    
    # Initialize the deployer
    deployer = RevOpsDeployer(args.config, args.secrets, args.region)
    
    # Determine what to deploy
    if args.deploy_all:
        deployer.deploy_all()
    else:
        if args.deploy_secrets:
            deployer.deploy_secrets()
        
        if args.deploy_lambdas:
            deployer.deploy_lambda_functions()
        
        if args.deploy_knowledge_bases:
            deployer.deploy_knowledge_bases()
        
        if args.deploy_agents:
            deployer.deploy_agents()
        
        if args.deploy_flows:
            deployer.deploy_flows()
        
        # If no specific component was selected, deploy everything
        if not any([args.deploy_secrets, args.deploy_lambdas, args.deploy_knowledge_bases, 
                    args.deploy_agents, args.deploy_flows]):
            deployer.deploy_all()
    
    logger.info("Deployment script completed")


if __name__ == "__main__":
    main()
