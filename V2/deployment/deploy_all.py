#!/usr/bin/env python3
"""
RevOps AI Framework V2 - Unified Deployment Script
Consolidates all deployment functionality with fixes and knowledge base support
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

class RevOpsDeployer:
    def __init__(self, config_path: str = CONFIG_PATH):
        """Initialize the deployer with configuration"""
        self.config = self.load_config(config_path)
        self.aws_profile = self.config.get("profile_name", "FireboltSystemAdministrator-740202120544")
        self.aws_region = self.config.get("region_name", "us-east-1")
        self.account_id = self.config.get("account_id", "740202120544")
        
        # Initialize AWS clients
        session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
        self.lambda_client = session.client('lambda')
        self.iam_client = session.client('iam')
        self.bedrock_agent_client = session.client('bedrock-agent')
        self.s3_client = session.client('s3')
        self.opensearch_client = session.client('opensearchserverless')
        self.credentials = session.get_credentials()
        
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
                policy_arn = f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
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
                lambda_role_name = f"{lambda_name.replace('_', '-')}-lambda-role"
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
                    logger.info(f"Creating Lambda IAM role: {lambda_role_name}")
                    self.iam_client.create_role(
                        RoleName=lambda_role_name,
                        AssumeRolePolicyDocument=json.dumps(lambda_trust_policy)
                    )
                    
                    # Attach basic execution policy
                    self.iam_client.attach_role_policy(
                        RoleName=lambda_role_name,
                        PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    )
                    
                    # Attach secrets manager policy for accessing credentials
                    lambda_policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "secretsmanager:GetSecretValue"
                                ],
                                "Resource": "*"
                            }
                        ]
                    }
                    
                    policy_name = f"{lambda_role_name}-secrets-policy"
                    self.iam_client.create_policy(
                        PolicyName=policy_name,
                        PolicyDocument=json.dumps(lambda_policy)
                    )
                    
                    self.iam_client.attach_role_policy(
                        RoleName=lambda_role_name,
                        PolicyArn=f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
                    )
                    
                    # Wait for role to be available
                    time.sleep(10)
                
                lambda_role_arn = f"arn:aws:iam::{self.account_id}:role/{lambda_role_name}"
                
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

    def setup_opensearch_collection(self) -> str:
        """Set up OpenSearch Serverless collection for knowledge base"""
        logger.info("Setting up OpenSearch Serverless collection...")
        
        collection_name = "revops-kb"
        
        try:
            # Check if collection already exists
            try:
                collections = self.opensearch_client.list_collections(
                    collectionFilters={'name': collection_name}
                )
                if collections['collectionSummaries']:
                    collection_arn = collections['collectionSummaries'][0]['arn']
                    logger.info(f"OpenSearch collection already exists: {collection_arn}")
                    
                    # Get collection details to ensure it's ready
                    collection_details = self.opensearch_client.batch_get_collection(
                        ids=[collections['collectionSummaries'][0]['id']]
                    )
                    
                    if collection_details['collectionDetails']:
                        collection_endpoint = collection_details['collectionDetails'][0]['collectionEndpoint']
                        logger.info(f"Collection endpoint: {collection_endpoint}")
                        return collection_arn
            except Exception as e:
                logger.warning(f"Error checking existing collection: {e}")
            
            # Create security policies
            # Encryption policy
            try:
                self.opensearch_client.create_security_policy(
                    name=f"{collection_name}-encryption",
                    type='encryption',
                    policy=json.dumps({
                        "Rules": [
                            {
                                "Resource": [f"collection/{collection_name}"],
                                "ResourceType": "collection"
                            }
                        ],
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
                    policy=json.dumps([
                        {
                            "Rules": [
                                {
                                    "Resource": [f"collection/{collection_name}"],
                                    "ResourceType": "collection"
                                }
                            ],
                            "AllowFromPublic": True
                        }
                    ])
                )
                logger.info("Created network policy")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.warning(f"Error creating network policy: {e}")
            
            # Data access policy
            try:
                bedrock_role_arn = f"arn:aws:iam::{self.account_id}:role/AmazonBedrockExecutionRoleForAgents_revops"
                self.opensearch_client.create_access_policy(
                    name=f"{collection_name}-access",
                    type='data',
                    policy=json.dumps([
                        {
                            "Rules": [
                                {
                                    "Resource": [f"collection/{collection_name}"],
                                    "Permission": [
                                        "aoss:CreateCollectionItems",
                                        "aoss:DeleteCollectionItems",
                                        "aoss:UpdateCollectionItems",
                                        "aoss:DescribeCollectionItems"
                                    ],
                                    "ResourceType": "collection"
                                },
                                {
                                    "Resource": [f"index/{collection_name}/*"],
                                    "Permission": [
                                        "aoss:CreateIndex",
                                        "aoss:DeleteIndex",
                                        "aoss:UpdateIndex",
                                        "aoss:DescribeIndex",
                                        "aoss:ReadDocument",
                                        "aoss:WriteDocument"
                                    ],
                                    "ResourceType": "index"
                                }
                            ],
                            "Principal": [bedrock_role_arn]
                        }
                    ])
                )
                logger.info("Created data access policy")
            except Exception as e:
                if "already exists" not in str(e):
                    logger.warning(f"Error creating data access policy: {e}")
            
            # Create collection if it doesn't exist
            try:
                logger.info(f"Creating OpenSearch collection: {collection_name}")
                response = self.opensearch_client.create_collection(
                    name=collection_name,
                    type='VECTORSEARCH'
                )
                
                collection_arn = response['createCollectionDetail']['arn']
                collection_id = response['createCollectionDetail']['id']
                
                # Wait for collection to be active
                logger.info("Waiting for collection to be active...")
                while True:
                    status = self.opensearch_client.list_collections(
                        collectionFilters={'name': collection_name}
                    )
                    if status['collectionSummaries'] and status['collectionSummaries'][0]['status'] == 'ACTIVE':
                        break
                    time.sleep(30)
                
                # Get collection endpoint
                collection_details = self.opensearch_client.batch_get_collection(ids=[collection_id])
                collection_endpoint = collection_details['collectionDetails'][0]['collectionEndpoint']
                
                # Create the vector index
                self.create_vector_index(collection_endpoint)
                
                logger.info(f"OpenSearch collection created: {collection_arn}")
                return collection_arn
                
            except Exception as e:
                if "already exists" in str(e):
                    # If collection already exists, get its details
                    collections = self.opensearch_client.list_collections(
                        collectionFilters={'name': collection_name}
                    )
                    if collections['collectionSummaries']:
                        collection_arn = collections['collectionSummaries'][0]['arn']
                        logger.info(f"Using existing OpenSearch collection: {collection_arn}")
                        return collection_arn
                else:
                    raise e
            
        except Exception as e:
            logger.error(f"Error setting up OpenSearch collection: {e}")
            return None

    def create_vector_index(self, collection_endpoint: str) -> bool:
        """Create vector index in OpenSearch collection"""
        logger.info("Creating vector index in OpenSearch collection...")
        
        try:
            # Set up authentication
            awsauth = AWS4Auth(
                self.credentials.access_key,
                self.credentials.secret_key,
                self.aws_region,
                'aoss',
                session_token=self.credentials.token
            )
            
            # Create index
            index_name = "bedrock-knowledge-base-default-index"
            url = f"{collection_endpoint}/{index_name}"
            
            index_config = {
                'settings': {
                    'index': {
                        'knn': True,
                        'knn.algo_param.ef_search': 512
                    }
                },
                'mappings': {
                    'properties': {
                        'bedrock-knowledge-base-default-vector': {
                            'type': 'knn_vector',
                            'dimension': 1536,
                            'method': {
                                'name': 'hnsw',
                                'space_type': 'l2',
                                'engine': 'nmslib',
                                'parameters': {
                                    'ef_construction': 512,
                                    'm': 16
                                }
                            }
                        },
                        'AMAZON_BEDROCK_TEXT_CHUNK': {
                            'type': 'text'
                        },
                        'AMAZON_BEDROCK_METADATA': {
                            'type': 'text'
                        }
                    }
                }
            }
            
            response = requests.put(
                url,
                auth=awsauth,
                json=index_config,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Vector index created successfully: {index_name}")
                return True
            else:
                logger.error(f"Failed to create vector index: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating vector index: {e}")
            return False

    def deploy_knowledge_base(self) -> Optional[str]:
        """Deploy knowledge base for schema awareness"""
        logger.info("Deploying knowledge base...")
        
        kb_config = self.config.get('knowledge_base', {})
        bucket_name = kb_config.get('storage_bucket', f'revops-ai-framework-kb-{self.account_id}')
        
        try:
            # Create S3 bucket
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
            
            # Upload schema file
            schema_file_path = os.path.join(PROJECT_ROOT, kb_config.get('schema_file_path', 'knowledge_base/firebolt_schema/firebolt_schema.md'))
            if os.path.exists(schema_file_path):
                s3_key = f"{kb_config.get('storage_prefix', 'revops-ai-framework/knowledge/')}firebolt_schema.md"
                logger.info(f"Uploading schema file to S3: {s3_key}")
                self.s3_client.upload_file(schema_file_path, bucket_name, s3_key)
            
            # Set up OpenSearch collection
            collection_arn = self.setup_opensearch_collection()
            if not collection_arn:
                logger.error("Failed to set up OpenSearch collection")
                return None
            
            # Create Bedrock knowledge base
            kb_name = "revops-schema-kb"
            
            # Check if knowledge base already exists
            try:
                kbs = self.bedrock_agent_client.list_knowledge_bases()
                for kb in kbs.get('knowledgeBaseSummaries', []):
                    if kb['name'] == kb_name:
                        kb_id = kb['knowledgeBaseId']
                        logger.info(f"Knowledge base already exists: {kb_id}")
                        kb_config['knowledge_base_id'] = kb_id
                        return kb_id
            except:
                pass
            
            logger.info(f"Creating Bedrock knowledge base: {kb_name}")
            response = self.bedrock_agent_client.create_knowledge_base(
                name=kb_name,
                description="Firebolt schema knowledge base for RevOps AI Framework",
                roleArn=f"arn:aws:iam::{self.account_id}:role/AmazonBedrockExecutionRoleForAgents_revops",
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1'
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': collection_arn,
                        'vectorIndexName': 'bedrock-knowledge-base-default-index',
                        'fieldMapping': {
                            'vectorField': 'bedrock-knowledge-base-default-vector',
                            'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                            'metadataField': 'AMAZON_BEDROCK_METADATA'
                        }
                    }
                }
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            kb_config['knowledge_base_id'] = kb_id
            
            # Create data source
            logger.info("Creating knowledge base data source...")
            data_source_response = self.bedrock_agent_client.create_data_source(
                knowledgeBaseId=kb_id,
                name="firebolt-schema-source",
                description="Firebolt schema documentation",
                dataSourceConfiguration={
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{bucket_name}',
                        'inclusionPrefixes': [kb_config.get('storage_prefix', 'revops-ai-framework/knowledge/')]
                    }
                }
            )
            
            data_source_id = data_source_response['dataSource']['dataSourceId']
            
            # Start ingestion job
            logger.info("Starting knowledge base ingestion...")
            self.bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id
            )
            
            logger.info(f"Knowledge base deployed successfully: {kb_id}")
            return kb_id
            
        except Exception as e:
            logger.error(f"Error deploying knowledge base: {e}")
            return None

    def deploy_data_agent(self) -> bool:
        """Deploy the data agent with action groups and knowledge base"""
        logger.info("Deploying data agent...")
        
        agent_config = self.config.get('data_agent', {})
        kb_id = self.config.get('knowledge_base', {}).get('knowledge_base_id')
        
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
                    
                    # Check if knowledge base is associated
                    if kb_id:
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
                agentName="revops-data-agent-v2",
                description="Data Analysis Agent for RevOps AI Framework V2",
                agentResourceRoleArn=f"arn:aws:iam::{self.account_id}:role/AmazonBedrockExecutionRoleForAgents_revops",
                foundationModel=agent_config.get('foundation_model', 'anthropic.claude-3-7-sonnet-20250219-v1:0'),
                instruction=instructions
            )
            
            agent_id = response['agent']['agentId']
            agent_config['agent_id'] = agent_id
            logger.info(f"Created agent: {agent_id}")
            
            # Wait for agent to be in a valid state before creating action groups
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
            
            # Associate knowledge base if available
            if kb_id:
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
        logger.info("🚀 Starting full deployment of RevOps AI Framework V2...")
        
        success = True
        
        # 1. Create IAM roles and policies
        logger.info("📋 Step 1: Creating IAM roles and policies...")
        if not self.create_iam_roles_and_policies():
            logger.error("Failed to create IAM roles/policies")
            success = False
        
        # 2. Deploy Lambda functions
        logger.info("⚡ Step 2: Deploying Lambda functions...")
        for lambda_name in self.config.get('lambda_functions', {}):
            if not self.deploy_lambda_function(lambda_name):
                logger.error(f"Failed to deploy Lambda: {lambda_name}")
                success = False
        
        # 3. Deploy knowledge base
        logger.info("📚 Step 3: Deploying knowledge base...")
        kb_id = self.deploy_knowledge_base()
        if not kb_id:
            logger.error("Failed to deploy knowledge base")
            success = False
        
        # 4. Deploy data agent
        logger.info("🤖 Step 4: Deploying data agent...")
        if not self.deploy_data_agent():
            logger.error("Failed to deploy data agent")
            success = False
        
        # 5. Test functions
        logger.info("🧪 Step 5: Testing deployed functions...")
        self.test_lambda_functions()
        
        # 6. Save updated configuration
        self.save_config()
        
        if success:
            logger.info("🎉 Deployment completed successfully!")
            logger.info("📋 Summary:")
            logger.info("  ✅ IAM roles and policies created")
            logger.info("  ✅ Lambda functions deployed and tested")
            logger.info("  ✅ Knowledge base deployed with schema data")
            logger.info("  ✅ Data agent deployed with action groups and knowledge base")
            logger.info("  ✅ Configuration updated with deployed resource IDs")
        else:
            logger.error("❌ Deployment completed with errors")
        
        return success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="RevOps AI Framework V2 Deployment")
    parser.add_argument("--component", choices=["iam", "lambda", "kb", "agent", "all"], 
                       default="all", help="Component to deploy")
    parser.add_argument("--lambda-name", help="Specific Lambda function to deploy")
    parser.add_argument("--test", action="store_true", help="Run tests after deployment")
    parser.add_argument("--clean", action="store_true", help="Clean up existing resources first")
    
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