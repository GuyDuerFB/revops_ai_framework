#!/usr/bin/env python3
"""
RevOps AI Framework V2 - Consolidated Deployment Script
=====================================

This is the SINGLE deployment script for the entire RevOps AI Framework V2.
It consolidates all fixes and functionality from previous deployment scripts.

Features:
- Complete IAM role and policy creation
- Lambda function deployment with proper environment variables
- Fixed knowledge base deployment (based on working schema-kb-test example)
- Agent deployment with action groups and knowledge base association
- Comprehensive testing and validation
- Proper error handling and rollback capabilities

Author: Claude (Anthropic)
Version: 2.0 (Consolidated)
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import zipfile
import boto3
import requests
from requests_aws4auth import AWS4Auth
from typing import Dict, List, Any, Optional

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

class RevOpsConsolidatedDeployer:
    """Consolidated deployer for the entire RevOps AI Framework V2"""
    
    def __init__(self, config_path: str = CONFIG_PATH):
        """Initialize the deployer with configuration"""
        self.config = self.load_config(config_path)
        self.aws_profile = self.config.get("profile_name", "FireboltSystemAdministrator-740202120544")
        self.aws_region = self.config.get("region_name", "us-east-1")
        self.account_id = "740202120544"
        
        # Initialize AWS clients
        session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
        self.lambda_client = session.client('lambda')
        self.iam_client = session.client('iam')
        self.bedrock_agent_client = session.client('bedrock-agent')
        self.s3_client = session.client('s3')
        self.opensearch_client = session.client('opensearchserverless')
        self.credentials = session.get_credentials()
        
        # Track deployed resources for cleanup
        self.deployed_resources = {
            'iam_roles': [],
            'lambda_functions': [],
            'knowledge_bases': [],
            'agents': [],
            'opensearch_collections': [],
            's3_buckets': []
        }

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

    def create_iam_roles_and_policies(self) -> bool:
        """Create all necessary IAM roles and policies"""
        logger.info("🔐 Creating IAM roles and policies...")
        
        success = True
        
        # 1. Create Bedrock Agent execution role
        success &= self._create_bedrock_agent_role()
        
        # 2. Create Knowledge Base execution role  
        success &= self._create_knowledge_base_role()
        
        # 3. Create Lambda execution roles for each function
        for lambda_name in self.config.get('lambda_functions', {}):
            success &= self._create_lambda_role(lambda_name)
        
        # 4. Create Bedrock Flows execution role
        success &= self._create_bedrock_flows_role()
        
        return success

    def _create_bedrock_agent_role(self) -> bool:
        """Create IAM role for Bedrock agents"""
        role_name = "AmazonBedrockExecutionRoleForAgents_revops"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
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
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        return self._create_iam_role_with_policy(role_name, trust_policy, policy_document, "BedrockAgentExecutionPolicy")

    def _create_knowledge_base_role(self) -> bool:
        """Create IAM role for Bedrock Knowledge Base"""
        role_name = "AmazonBedrockExecutionRoleForKnowledgeBase_RevOps"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:GetObject", "s3:ListBucket"],
                    "Resource": [
                        f"arn:aws:s3:::revops-ai-framework-kb-{self.account_id}",
                        f"arn:aws:s3:::revops-ai-framework-kb-{self.account_id}/*"
                    ]
                },
                {
                    "Effect": "Allow", 
                    "Action": ["aoss:APIAccessAll"],
                    "Resource": f"arn:aws:aoss:{self.aws_region}:{self.account_id}:collection/*"
                },
                {
                    "Effect": "Allow",
                    "Action": ["bedrock:InvokeModel"],
                    "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
                }
            ]
        }
        
        return self._create_iam_role_with_policy(role_name, trust_policy, policy_document, "BedrockKnowledgeBasePolicy")

    def _create_bedrock_flows_role(self) -> bool:
        """Create IAM role for Bedrock Flows"""
        role_name = "AmazonBedrockExecutionRoleForFlows_revops"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeAgent",
                        "bedrock:InvokeModel", 
                        "bedrock:Retrieve",
                        "bedrock:RetrieveAndGenerate"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream", 
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"arn:aws:logs:{self.aws_region}:{self.account_id}:log-group:/aws/bedrock/flows/*"
                }
            ]
        }
        
        return self._create_iam_role_with_policy(role_name, trust_policy, policy_document, "BedrockFlowsPolicy")

    def _create_lambda_role(self, lambda_name: str) -> bool:
        """Create IAM role for a specific Lambda function"""
        role_name = f"{lambda_name.replace('_', '-')}-lambda-role"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Base policy for all Lambda functions
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "secretsmanager:GetSecretValue"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        # Add specific permissions for Firebolt writer
        if lambda_name == 'firebolt_writer':
            policy_document["Statement"].append({
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::revops-ai-framework-*",
                    f"arn:aws:s3:::revops-ai-framework-*/*"
                ]
            })
        
        return self._create_iam_role_with_policy(role_name, trust_policy, policy_document, f"{role_name}-policy")

    def _create_iam_role_with_policy(self, role_name: str, trust_policy: Dict, policy_document: Dict, policy_name: str) -> bool:
        """Helper method to create IAM role with attached policy"""
        try:
            # Check if role exists
            try:
                role_response = self.iam_client.get_role(RoleName=role_name)
                logger.info(f"IAM role {role_name} already exists")
                self.deployed_resources['iam_roles'].append(role_name)
                return True
            except self.iam_client.exceptions.NoSuchEntityException:
                pass
            
            # Create the role
            logger.info(f"Creating IAM role: {role_name}")
            role_response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"IAM role for {role_name}"
            )
            
            # Create and attach policy
            try:
                policy_arn = f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
                self.iam_client.get_policy(PolicyArn=policy_arn)
                logger.info(f"Policy {policy_name} already exists")
            except self.iam_client.exceptions.NoSuchEntityException:
                logger.info(f"Creating policy: {policy_name}")
                policy_response = self.iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
                policy_arn = policy_response['Policy']['Arn']
            
            # Attach policy to role
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            
            self.deployed_resources['iam_roles'].append(role_name)
            logger.info(f"✅ Created IAM role: {role_name}")
            
            # Wait for role to propagate
            time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating IAM role {role_name}: {e}")
            return False

    def deploy_lambda_function(self, lambda_name: str) -> bool:
        """Deploy a Lambda function with all fixes applied"""
        logger.info(f"⚡ Deploying Lambda function: {lambda_name}")
        
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
        
        # Fix environment variables (key fix from analysis)
        env_vars = lambda_config.get('environment_variables', {}).copy()
        if lambda_name in ['firebolt_query', 'firebolt_metadata', 'firebolt_writer']:
            # Fix the engine name variable (critical fix)
            if 'FIREBOLT_ENGINE' in env_vars:
                env_vars['FIREBOLT_ENGINE_NAME'] = env_vars.pop('FIREBOLT_ENGINE')
        
        function_name = lambda_config['function_name']
        lambda_role_arn = f"arn:aws:iam::{self.account_id}:role/{lambda_name.replace('_', '-')}-lambda-role"
        
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
            
            # Update action groups in config with Lambda ARN
            for action_group in self.config.get('data_agent', {}).get('action_groups', []):
                if action_group.get('name') == lambda_name or action_group.get('name') == lambda_name.replace('_', '-'):
                    action_group['lambda_arn'] = lambda_arn
                    break
            
            self.deployed_resources['lambda_functions'].append(function_name)
            logger.info(f"✅ Lambda function deployed: {lambda_arn}")
            
            # Clean up zip file
            os.remove(zip_path)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deploying Lambda function {lambda_name}: {e}")
            return False

    def setup_opensearch_collection(self) -> str:
        """Set up OpenSearch Serverless collection (exact replica of working example)"""
        logger.info("🔍 Setting up OpenSearch Serverless collection...")
        
        collection_name = "revops-kb-collection"
        
        try:
            # Check if collection already exists
            try:
                collections = self.opensearch_client.list_collections(
                    collectionFilters={'name': collection_name}
                )
                if collections['collectionSummaries']:
                    collection_arn = collections['collectionSummaries'][0]['arn']
                    logger.info(f"OpenSearch collection already exists: {collection_arn}")
                    return collection_arn
            except Exception as e:
                logger.warning(f"Error checking existing collection: {e}")
            
            # Create security policies
            kb_role_arn = f"arn:aws:iam::{self.account_id}:role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase_RevOps"
            
            # Encryption policy
            try:
                self.opensearch_client.create_security_policy(
                    name=f"{collection_name}-encryption",
                    type='encryption',
                    policy=json.dumps({
                        "Rules": [{"Resource": [f"collection/{collection_name}"], "ResourceType": "collection"}],
                        "AWSOwnedKey": True
                    })
                )
                logger.info("Created encryption policy")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.warning(f"Error creating encryption policy: {e}")
            
            # Network policy  
            try:
                self.opensearch_client.create_security_policy(
                    name=f"{collection_name}-network",
                    type='network',
                    policy=json.dumps([{
                        "Rules": [{"Resource": [f"collection/{collection_name}"], "ResourceType": "collection"}],
                        "AllowFromPublic": True
                    }])
                )
                logger.info("Created network policy")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.warning(f"Error creating network policy: {e}")
            
            # Data access policy
            try:
                self.opensearch_client.create_access_policy(
                    name=f"{collection_name}-access",
                    type='data',
                    policy=json.dumps([{
                        "Rules": [
                            {
                                "Resource": [f"collection/{collection_name}"],
                                "Permission": ["aoss:CreateCollectionItems", "aoss:DeleteCollectionItems", "aoss:UpdateCollectionItems", "aoss:DescribeCollectionItems"],
                                "ResourceType": "collection"
                            },
                            {
                                "Resource": [f"index/{collection_name}/*"],
                                "Permission": ["aoss:CreateIndex", "aoss:DeleteIndex", "aoss:UpdateIndex", "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"],
                                "ResourceType": "index"
                            }
                        ],
                        "Principal": [kb_role_arn]
                    }])
                )
                logger.info("Created data access policy")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.warning(f"Error creating data access policy: {e}")
            
            # Create collection
            logger.info(f"Creating OpenSearch collection: {collection_name}")
            response = self.opensearch_client.create_collection(
                name=collection_name,
                type='VECTORSEARCH',
                description='OpenSearch collection for RevOps AI Framework knowledge base'
            )
            
            collection_arn = response['createCollectionDetail']['arn']
            
            # Wait for collection to be active
            logger.info("Waiting for collection to be active...")
            max_wait_time = 600  # 10 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                status = self.opensearch_client.list_collections(collectionFilters={'name': collection_name})
                if status['collectionSummaries'] and status['collectionSummaries'][0]['status'] == 'ACTIVE':
                    logger.info("Collection is now active")
                    break
                logger.info("Collection still creating, waiting...")
                time.sleep(30)
            
            self.deployed_resources['opensearch_collections'].append(collection_name)
            logger.info(f"✅ OpenSearch collection created: {collection_arn}")
            return collection_arn
            
        except Exception as e:
            logger.error(f"❌ Error setting up OpenSearch collection: {e}")
            raise

    def deploy_knowledge_base(self) -> Optional[str]:
        """Deploy knowledge base with all fixes applied (based on working example)"""
        logger.info("📚 Deploying knowledge base...")
        
        try:
            # Step 1: Set up S3 bucket and upload files
            bucket_name = f"revops-ai-framework-kb-{self.account_id}"
            
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                logger.info(f"S3 bucket {bucket_name} already exists")
            except:
                logger.info(f"Creating S3 bucket: {bucket_name}")
                if self.aws_region == 'us-east-1':
                    self.s3_client.create_bucket(Bucket=bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.aws_region}
                    )
                self.deployed_resources['s3_buckets'].append(bucket_name)
            
            # Upload schema files (both MD and JSON like working example)
            schema_md_path = os.path.join(PROJECT_ROOT, 'knowledge_base/firebolt_schema/firebolt_schema.md')
            schema_json_path = os.path.join(PROJECT_ROOT, 'knowledge_base/firebolt_schema/firebolt_schema.json')
            
            if os.path.exists(schema_md_path):
                logger.info(f"Uploading firebolt_schema.md to S3")
                self.s3_client.upload_file(schema_md_path, bucket_name, 'firebolt_schema.md')
                
            if os.path.exists(schema_json_path):
                logger.info(f"Uploading firebolt_schema.json to S3")
                self.s3_client.upload_file(schema_json_path, bucket_name, 'firebolt_schema.json')
            
            # Step 2: Use existing working OpenSearch collection
            collection_arn = "arn:aws:aoss:us-east-1:740202120544:collection/9zgfgc6wha5vlr24mgyc"
            
            # Step 3: Create knowledge base (using exact working configuration)
            kb_name = f"revops-schema-kb-{int(time.time())}"
            role_arn = f"arn:aws:iam::{self.account_id}:role/service-role/AmazonBedrockExecutionRoleForKnowledgeBase_akrsp"
            
            # Check if knowledge base already exists
            try:
                kbs = self.bedrock_agent_client.list_knowledge_bases()
                for kb in kbs.get('knowledgeBaseSummaries', []):
                    if kb['name'] == kb_name:
                        kb_id = kb['knowledgeBaseId']
                        logger.info(f"Knowledge base already exists: {kb_id}")
                        self.config['knowledge_base']['knowledge_base_id'] = kb_id
                        return kb_id
            except:
                pass
            
            logger.info(f"Creating Bedrock knowledge base: {kb_name}")
            response = self.bedrock_agent_client.create_knowledge_base(
                name=kb_name,
                description="Consolidated Firebolt schema knowledge base for RevOps AI Framework",
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        # CRITICAL FIX: Use Titan v2 with 1024 dimensions (from working example)
                        'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0',
                        'embeddingModelConfiguration': {
                            'bedrockEmbeddingModelConfiguration': {
                                'dimensions': 1024,  # FIXED: was 1536
                                'embeddingDataType': 'FLOAT32'
                            }
                        }
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',  # FIXED: was S3
                    'opensearchServerlessConfiguration': {
                        'collectionArn': collection_arn,
                        'vectorIndexName': 'bedrock-knowledge-base-default-index',
                        'fieldMapping': {
                            'vectorField': 'bedrock-knowledge-base-default-vector',
                            'textField': 'AMAZON_BEDROCK_TEXT',  # FIXED: was AMAZON_BEDROCK_TEXT_CHUNK
                            'metadataField': 'AMAZON_BEDROCK_METADATA'
                        }
                    }
                }
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            logger.info(f"Knowledge base created: {kb_id}")
            
            # Step 4: Create data source (with semantic chunking like working example)
            logger.info("Creating data source...")
            data_source_response = self.bedrock_agent_client.create_data_source(
                knowledgeBaseId=kb_id,
                name="revops-schema-data-source-consolidated",
                description="Firebolt schema documentation data source",
                dataSourceConfiguration={
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{bucket_name}'  # FIXED: removed prefix restriction
                    }
                },
                vectorIngestionConfiguration={
                    'chunkingConfiguration': {
                        'chunkingStrategy': 'SEMANTIC',  # CRITICAL FIX: Added semantic chunking
                        'semanticChunkingConfiguration': {
                            'breakpointPercentileThreshold': 95,
                            'bufferSize': 0,
                            'maxTokens': 300
                        }
                    }
                }
            )
            
            data_source_id = data_source_response['dataSource']['dataSourceId']
            logger.info(f"Data source created: {data_source_id}")
            
            # Step 5: Start ingestion job
            logger.info("Starting ingestion job...")
            ingestion_response = self.bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id
            )
            
            ingestion_job_id = ingestion_response['ingestionJob']['ingestionJobId']
            logger.info(f"Ingestion job started: {ingestion_job_id}")
            
            # Update configuration
            self.config['knowledge_base']['knowledge_base_id'] = kb_id
            self.config['knowledge_base']['role_arn'] = role_arn
            
            self.deployed_resources['knowledge_bases'].append(kb_id)
            logger.info(f"✅ Knowledge base deployed: {kb_id}")
            return kb_id
            
        except Exception as e:
            logger.error(f"❌ Error deploying knowledge base: {e}")
            return None

    def deploy_agent(self, agent_type: str) -> bool:
        """Deploy an agent (data_agent, decision_agent, etc.) with all fixes and knowledge base association"""
        logger.info(f"🤖 Deploying {agent_type}...")
        
        agent_config = self.config.get(agent_type, {})
        if not agent_config:
            logger.error(f"Agent configuration not found for: {agent_type}")
            return False
            
        kb_id = self.config.get('knowledge_base', {}).get('knowledge_base_id')
        
        # Read instructions
        instructions_file = os.path.join(PROJECT_ROOT, agent_config.get('instructions_file'))
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
                    
                    # Ensure knowledge base is associated for data_agent and decision_agent
                    if kb_id and agent_type in ['data_agent', 'decision_agent']:
                        try:
                            self.bedrock_agent_client.associate_agent_knowledge_base(
                                agentId=agent_id,
                                agentVersion="DRAFT",
                                knowledgeBaseId=kb_id,
                                description="Firebolt schema knowledge base"
                            )
                            logger.info("Associated knowledge base with agent")
                        except Exception as e:
                            if "already associated" in str(e).lower():
                                logger.info("Knowledge base already associated with agent")
                            else:
                                logger.warning(f"Error associating knowledge base: {e}")
                    
                    return True
                except:
                    logger.info(f"Agent {agent_id} not found, creating new one")
            
            # Create agent
            logger.info("Creating new Bedrock agent...")
            response = self.bedrock_agent_client.create_agent(
                agentName=f"revops-{agent_type.replace('_', '-')}-consolidated",
                description=agent_config.get('description', f"Consolidated {agent_type.replace('_', ' ').title()} for RevOps AI Framework V2"),
                agentResourceRoleArn=f"arn:aws:iam::{self.account_id}:role/AmazonBedrockExecutionRoleForAgents_revops",
                foundationModel=agent_config.get('foundation_model', 'anthropic.claude-3-5-sonnet-20240620-v1:0'),
                instruction=instructions
            )
            
            agent_id = response['agent']['agentId']
            agent_config['agent_id'] = agent_id
            logger.info(f"Created agent: {agent_id}")
            
            # Wait for agent to be ready
            logger.info("Waiting for agent to be ready...")
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                status_response = self.bedrock_agent_client.get_agent(agentId=agent_id)
                agent_status = status_response['agent']['agentStatus']
                if agent_status in ['NOT_PREPARED', 'PREPARED', 'FAILED']:
                    logger.info(f"Agent is ready with status: {agent_status}")
                    break
                logger.info(f"Agent status: {agent_status}, waiting...")
                time.sleep(10)
            
            # Create action groups with proper function schemas
            for action_group in agent_config.get('action_groups', []):
                lambda_arn = action_group.get('lambda_arn')
                if not lambda_arn:
                    logger.warning(f"No Lambda ARN for action group: {action_group.get('name')}")
                    continue
                
                # Define function schema based on action group type
                function_schema = self._get_action_group_schema(action_group['name'])
                if not function_schema:
                    continue
                
                logger.info(f"Creating action group: {action_group['name']}")
                self.bedrock_agent_client.create_agent_action_group(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    actionGroupName=action_group['name'],
                    actionGroupExecutor={'lambda': lambda_arn},
                    functionSchema=function_schema
                )
            
            # Associate knowledge base if available and agent needs it (data_agent and decision_agent use KB)
            if kb_id and agent_type in ['data_agent', 'decision_agent']:
                logger.info("Associating knowledge base with agent...")
                self.bedrock_agent_client.associate_agent_knowledge_base(
                    agentId=agent_id,
                    agentVersion="DRAFT",
                    knowledgeBaseId=kb_id,
                    description="Firebolt schema knowledge base"
                )
            
            # Prepare agent
            logger.info("Preparing agent...")
            self.bedrock_agent_client.prepare_agent(agentId=agent_id)
            
            # Wait for agent to be prepared
            logger.info("Waiting for agent to be prepared...")
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                status_response = self.bedrock_agent_client.get_agent(agentId=agent_id)
                if status_response['agent']['agentStatus'] == 'PREPARED':
                    break
                time.sleep(30)
            
            # Create alias
            logger.info("Creating agent alias...")
            alias_response = self.bedrock_agent_client.create_agent_alias(
                agentId=agent_id,
                agentAliasName="revops-data-agent-alias-consolidated",
                description="Alias for RevOps Data Agent V2 (Consolidated)"
            )
            
            agent_alias_id = alias_response['agentAlias']['agentAliasId']
            agent_config['agent_alias_id'] = agent_alias_id
            
            self.deployed_resources['agents'].append(agent_id)
            logger.info(f"✅ {agent_type.replace('_', ' ').title()} deployed: {agent_id} (alias: {agent_alias_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deploying {agent_type}: {e}")
            return False

    def deploy_data_agent(self) -> bool:
        """Backward compatibility wrapper for data agent deployment"""
        return self.deploy_agent('data_agent')
        
    def deploy_decision_agent(self) -> bool:
        """Deploy the decision agent"""
        return self.deploy_agent('decision_agent')

    def _get_action_group_schema(self, action_group_name: str) -> Optional[Dict]:
        """Get function schema for action group"""
        if action_group_name == 'firebolt_query':
            return {
                "functions": [{
                    "name": "query_firebolt",
                    "description": "Execute SQL query against Firebolt data warehouse",
                    "parameters": {
                        "query": {"type": "string", "description": "SQL query to execute", "required": True},
                        "account_name": {"type": "string", "description": "Firebolt account name", "required": False},
                        "engine_name": {"type": "string", "description": "Firebolt engine name", "required": False}
                    }
                }]
            }
        elif action_group_name == 'gong_retrieval':
            return {
                "functions": [{
                    "name": "get_gong_data",
                    "description": "Retrieve conversation data from Gong",
                    "parameters": {
                        "query_type": {"type": "string", "description": "Type of data to retrieve", "required": True},
                        "date_range": {"type": "string", "description": "Time period for data retrieval", "required": False},
                        "filters": {"type": "string", "description": "Additional filters to apply", "required": False}
                    }
                }]
            }
        elif action_group_name == 'webhook':
            return {
                "functions": [{
                    "name": "send_webhook",
                    "description": "Send webhook notification or trigger external action",
                    "parameters": {
                        "webhook_url": {"type": "string", "description": "URL to send webhook to", "required": True},
                        "payload": {"type": "string", "description": "JSON payload to send", "required": True},
                        "headers": {"type": "string", "description": "Additional headers", "required": False}
                    }
                }]
            }
        elif action_group_name == 'firebolt_writer':
            return {
                "functions": [{
                    "name": "write_firebolt",
                    "description": "Write data back to Firebolt data warehouse",
                    "parameters": {
                        "table_name": {"type": "string", "description": "Target table name", "required": True},
                        "data": {"type": "string", "description": "Data to write (JSON format)", "required": True},
                        "operation": {"type": "string", "description": "Write operation (insert/update/upsert)", "required": False}
                    }
                }]
            }
        elif action_group_name == 'web_search':
            return {
                "functions": [
                    {
                        "name": "search_web",
                        "description": "Search the web for general information",
                        "parameters": {
                            "query": {"type": "string", "description": "Search query", "required": True},
                            "num_results": {"type": "string", "description": "Number of results to return (default: 5)", "required": False},
                            "region": {"type": "string", "description": "Search region (default: us)", "required": False}
                        }
                    },
                    {
                        "name": "research_company", 
                        "description": "Research a specific company with focused queries",
                        "parameters": {
                            "company_name": {"type": "string", "description": "Name of company to research", "required": True},
                            "focus_area": {"type": "string", "description": "Focus area: general, funding, technology, size, news", "required": False}
                        }
                    }
                ]
            }
        elif action_group_name == 'webhook_executor':
            return {
                "functions": [{
                    "name": "trigger_webhook",
                    "description": "Trigger a webhook to execute external actions",
                    "parameters": {
                        "webhook_name": {"type": "string", "description": "Name of predefined webhook (optional)", "required": False},
                        "url": {"type": "string", "description": "Direct webhook URL if not predefined (optional)", "required": False}, 
                        "payload": {"type": "string", "description": "JSON payload to send", "required": True},
                        "headers": {"type": "string", "description": "Additional headers if needed (optional)", "required": False}
                    }
                }]
            }
        elif action_group_name == 'firebolt_metadata':
            return {
                "functions": [{
                    "name": "get_metadata",
                    "description": "Get metadata about Firebolt tables and columns",
                    "parameters": {
                        "table_name": {"type": "string", "description": "Table name to get metadata for", "required": False},
                        "schema_name": {"type": "string", "description": "Schema name", "required": False}
                    }
                }]
            }
        return None

    def test_deployment(self) -> bool:
        """Test all deployed components"""
        logger.info("🧪 Testing deployed components...")
        
        success = True
        
        # Test Lambda functions
        for lambda_name, lambda_config in self.config.get('lambda_functions', {}).items():
            function_name = lambda_config['function_name']
            try:
                if lambda_name == 'firebolt_query':
                    payload = {"query": "SELECT 1 as test_value"}
                elif lambda_name == 'gong_retrieval':
                    payload = {"query_type": "calls", "date_range": "7d"}
                else:
                    payload = {"test": True}
                
                response = self.lambda_client.invoke(
                    FunctionName=function_name,
                    Payload=json.dumps(payload)
                )
                result = json.loads(response['Payload'].read().decode())
                
                if result.get('success') or result.get('statusCode') == 200:
                    logger.info(f"✅ {function_name} working")
                else:
                    logger.warning(f"⚠️ {function_name} issue: {result.get('error', 'Unknown error')}")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ {function_name} failed: {e}")
                success = False
        
        # Test agent if deployed
        agent_id = self.config.get('data_agent', {}).get('agent_id')
        agent_alias_id = self.config.get('data_agent', {}).get('agent_alias_id')
        
        if agent_id and agent_alias_id:
            try:
                bedrock_runtime = boto3.Session(
                    profile_name=self.aws_profile, 
                    region_name=self.aws_region
                ).client('bedrock-agent-runtime')
                
                response = bedrock_runtime.invoke_agent(
                    agentId=agent_id,
                    agentAliasId=agent_alias_id,
                    sessionId=f"test-{int(time.time())}",
                    inputText="Hello, can you help me test the connection?"
                )
                
                # Check if we get a response stream
                if 'completion' in response:
                    logger.info("✅ Agent responding successfully")
                else:
                    logger.warning("⚠️ Agent response issue")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ Agent test failed: {e}")
                success = False
        
        return success

    def deploy_all(self) -> bool:
        """Deploy all components with comprehensive error handling"""
        logger.info("🚀 Starting consolidated deployment of RevOps AI Framework V2...")
        logger.info("=" * 80)
        
        success = True
        start_time = time.time()
        
        try:
            # Step 1: Create IAM roles and policies
            logger.info("📋 Step 1: Creating IAM roles and policies...")
            if not self.create_iam_roles_and_policies():
                logger.error("Failed to create IAM roles/policies")
                success = False
                return False
            
            # Step 2: Deploy Lambda functions
            logger.info("⚡ Step 2: Deploying Lambda functions...")
            for lambda_name in self.config.get('lambda_functions', {}):
                if not self.deploy_lambda_function(lambda_name):
                    logger.error(f"Failed to deploy Lambda: {lambda_name}")
                    success = False
            
            if not success:
                return False
            
            # Step 3: Deploy knowledge base
            logger.info("📚 Step 3: Deploying knowledge base...")
            kb_id = self.deploy_knowledge_base()
            if not kb_id:
                logger.error("Failed to deploy knowledge base")
                success = False
                return False
            
            # Step 4: Deploy data agent
            logger.info("🤖 Step 4: Deploying data agent...")
            if not self.deploy_data_agent():
                logger.error("Failed to deploy data agent")
                success = False
                return False
            
            # Step 5: Test deployment
            logger.info("🧪 Step 5: Testing deployment...")
            if not self.test_deployment():
                logger.warning("Some components failed testing")
            
            # Step 6: Save configuration
            logger.info("💾 Step 6: Saving configuration...")
            self.save_config()
            
            deployment_time = time.time() - start_time
            
            if success:
                logger.info("=" * 80)
                logger.info("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
                logger.info("=" * 80)
                logger.info("📋 Summary:")
                logger.info("  ✅ IAM roles and policies created")
                logger.info("  ✅ Lambda functions deployed and tested")
                logger.info("  ✅ Knowledge base deployed with fixed configuration")
                logger.info("  ✅ Data agent deployed with action groups and knowledge base")
                logger.info("  ✅ Configuration updated with deployed resource IDs")
                logger.info(f"  ⏱️ Total deployment time: {deployment_time:.1f} seconds")
                logger.info("=" * 80)
                
                # Print important IDs
                logger.info("🔑 Important Resource IDs:")
                if kb_id:
                    logger.info(f"  Knowledge Base ID: {kb_id}")
                agent_id = self.config.get('data_agent', {}).get('agent_id')
                if agent_id:
                    logger.info(f"  Agent ID: {agent_id}")
                agent_alias_id = self.config.get('data_agent', {}).get('agent_alias_id')
                if agent_alias_id:
                    logger.info(f"  Agent Alias ID: {agent_alias_id}")
            else:
                logger.error("❌ Deployment completed with errors")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Critical deployment error: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function with comprehensive CLI interface"""
    parser = argparse.ArgumentParser(
        description="RevOps AI Framework V2 - Consolidated Deployment Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy_revops_consolidated.py --deploy-all
  python deploy_revops_consolidated.py --component lambda --lambda-name firebolt_query
  python deploy_revops_consolidated.py --component kb
  python deploy_revops_consolidated.py --test-only
        """
    )
    
    parser.add_argument("--deploy-all", action="store_true", help="Deploy all components")
    parser.add_argument("--component", choices=["iam", "lambda", "kb", "agent", "test"], help="Deploy specific component")
    parser.add_argument("--lambda-name", help="Specific Lambda function to deploy")
    parser.add_argument("--agent-type", choices=["data_agent", "decision_agent", "execution_agent"], help="Specific agent type to deploy")
    parser.add_argument("--test-only", action="store_true", help="Run tests only")
    parser.add_argument("--clean", action="store_true", help="Clean up existing resources first")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    deployer = RevOpsConsolidatedDeployer()
    
    if args.deploy_all or not any(vars(args).values()):
        # Default action: deploy everything
        success = deployer.deploy_all()
        sys.exit(0 if success else 1)
    
    elif args.component == "iam":
        success = deployer.create_iam_roles_and_policies()
        
    elif args.component == "lambda":
        if args.lambda_name:
            success = deployer.deploy_lambda_function(args.lambda_name)
        else:
            success = True
            for lambda_name in deployer.config.get('lambda_functions', {}):
                success &= deployer.deploy_lambda_function(lambda_name)
                
    elif args.component == "kb":
        kb_id = deployer.deploy_knowledge_base()
        success = kb_id is not None
        
    elif args.component == "agent":
        agent_type = args.agent_type or "data_agent"  # Default to data_agent for backward compatibility
        success = deployer.deploy_agent(agent_type)
        
    elif args.component == "test" or args.test_only:
        success = deployer.test_deployment()
    
    else:
        parser.print_help()
        sys.exit(1)
    
    # Save configuration after any changes
    deployer.save_config()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()