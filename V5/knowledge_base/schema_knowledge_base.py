"""
RevOps AI Framework V2 - Schema Knowledge Base

This module defines the Schema Knowledge Base for the Data Analysis Agent,
providing schema-aware query capabilities.
"""

import json
import os
import boto3
import logging
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchemaKnowledgeBase:
    """
    Schema Knowledge Base for the RevOps AI Framework V2.
    Provides schema-aware querying capabilities to agents.
    """
    
    def __init__(
        self,
        knowledge_base_id: str = None,
        region_name: str = 'us-east-1',
        profile_name: Optional[str] = None,
        schema_file_path: Optional[str] = None
    ):
        """
        Initialize the Schema Knowledge Base.
        
        Args:
            knowledge_base_id (str): Bedrock Knowledge Base ID
            region_name (str): AWS region name
            profile_name (Optional[str]): AWS profile name
            schema_file_path (Optional[str]): Path to schema file
        """
        self.knowledge_base_id = knowledge_base_id
        self.region_name = region_name
        self.profile_name = profile_name
        self.schema_file_path = schema_file_path
        
        # Initialize AWS clients
        self.bedrock_agent = self._get_bedrock_agent_client()
        self.s3_client = self._get_s3_client()
        
        # Load schema if provided
        self.schema = None
        if schema_file_path and os.path.exists(schema_file_path):
            with open(schema_file_path, 'r') as f:
                self.schema = f.read()
    
    def _get_bedrock_agent_client(self):
        """Get Bedrock Agent client with the specified region and profile."""
        session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
        return session.client('bedrock-agent')
    
    def _get_s3_client(self):
        """Get S3 client with the specified region and profile."""
        session = boto3.Session(region_name=self.region_name, profile_name=self.profile_name)
        return session.client('s3')
    
    def create_knowledge_base(self, 
                             name: str, 
                             description: str,
                             data_source_bucket: str,
                             storage_configuration: Dict[str, Any],
                             role_arn: str) -> Dict[str, Any]:
        """
        Create a knowledge base in Amazon Bedrock.
        
        Args:
            name (str): Knowledge base name
            description (str): Knowledge base description
            data_source_bucket (str): S3 bucket for data source
            storage_configuration (Dict[str, Any]): Storage configuration
            role_arn (str): IAM role ARN for Bedrock to access S3
            
        Returns:
            Dict[str, Any]: Created knowledge base details
        """
        try:
            response = self.bedrock_agent.create_knowledge_base(
                name=name,
                description=description,
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': storage_configuration
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': storage_configuration.get('collectionArn'),
                        'vectorIndexName': 'bedrock-knowledge-base-default-index',
                        'fieldMapping': {
                            'vectorField': 'bedrock-knowledge-base-default-vector',
                            'textField': 'AMAZON_BEDROCK_TEXT',
                            'metadataField': 'AMAZON_BEDROCK_METADATA'
                        }
                    }
                }
            )
            
            self.knowledge_base_id = response['knowledgeBase']['knowledgeBaseId']
            
            logger.info(f"Created knowledge base with ID: {self.knowledge_base_id}")
            
            return response
        except Exception as e:
            logger.error(f"Error creating knowledge base: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def add_data_source(self, 
                       name: str,
                       description: str, 
                       data_source_bucket: str,
                       data_source_prefix: str) -> Dict[str, Any]:
        """
        Add a data source to the knowledge base.
        
        Args:
            name (str): Data source name
            description (str): Data source description
            data_source_bucket (str): S3 bucket containing the data
            data_source_prefix (str): S3 prefix for the data
            
        Returns:
            Dict[str, Any]: Added data source details
        """
        try:
            if not self.knowledge_base_id:
                return {
                    "status": "error",
                    "error": "No knowledge base ID provided"
                }
            
            response = self.bedrock_agent.create_data_source(
                knowledgeBaseId=self.knowledge_base_id,
                name=name,
                description=description,
                dataSourceConfiguration={
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{data_source_bucket}'
                    }
                },
                vectorIngestionConfiguration={
                    'chunkingConfiguration': {
                        'chunkingStrategy': 'SEMANTIC',
                        'semanticChunkingConfiguration': {
                            'breakpointPercentileThreshold': 95,
                            'bufferSize': 0,
                            'maxTokens': 300
                        }
                    }
                }
            )
            
            logger.info(f"Added data source with ID: {response['dataSource']['dataSourceId']}")
            
            return response
        except Exception as e:
            logger.error(f"Error adding data source: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def upload_schema_file(self, bucket_name: str, prefix: str = 'schema/') -> Dict[str, Any]:
        """
        Upload schema file to S3 for use in the knowledge base.
        
        Args:
            bucket_name (str): S3 bucket name
            prefix (str): S3 prefix
            
        Returns:
            Dict[str, Any]: Upload result
        """
        try:
            if not self.schema_file_path or not os.path.exists(self.schema_file_path):
                return {
                    "status": "error",
                    "error": "Schema file not found"
                }
            
            key = f"{prefix}{os.path.basename(self.schema_file_path)}"
            
            # Upload schema file to S3
            with open(self.schema_file_path, 'rb') as f:
                self.s3_client.upload_fileobj(f, bucket_name, key)
            
            logger.info(f"Uploaded schema file to s3://{bucket_name}/{key}")
            
            return {
                "status": "success",
                "bucket": bucket_name,
                "key": key
            }
        except Exception as e:
            logger.error(f"Error uploading schema file: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def sync_data_source(self, data_source_id: str) -> Dict[str, Any]:
        """
        Sync a data source in the knowledge base.
        
        Args:
            data_source_id (str): Data source ID
            
        Returns:
            Dict[str, Any]: Sync result
        """
        try:
            if not self.knowledge_base_id:
                return {
                    "status": "error",
                    "error": "No knowledge base ID provided"
                }
            
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=self.knowledge_base_id,
                dataSourceId=data_source_id
            )
            
            logger.info(f"Started ingestion job with ID: {response['ingestionJob']['ingestionJobId']}")
            
            return response
        except Exception as e:
            logger.error(f"Error syncing data source: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def associate_with_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Associate the knowledge base with a Bedrock agent.
        
        Args:
            agent_id (str): Bedrock Agent ID
            
        Returns:
            Dict[str, Any]: Association result
        """
        try:
            if not self.knowledge_base_id:
                return {
                    "status": "error",
                    "error": "No knowledge base ID provided"
                }
            
            response = self.bedrock_agent.associate_agent_knowledge_base(
                agentId=agent_id,
                knowledgeBaseId=self.knowledge_base_id,
                description="Schema knowledge base for RevOps AI Framework"
            )
            
            logger.info(f"Associated knowledge base with agent ID: {agent_id}")
            
            return response
        except Exception as e:
            logger.error(f"Error associating knowledge base with agent: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @classmethod
    def from_deployment_config(cls, config_path: str) -> 'SchemaKnowledgeBase':
        """
        Create a SchemaKnowledgeBase instance from a deployment configuration file.
        
        Args:
            config_path (str): Path to the deployment configuration file
            
        Returns:
            SchemaKnowledgeBase: Initialized knowledge base instance
        """
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        schema_file_path = config.get('knowledge_base', {}).get('schema_file_path')
        
        return cls(
            knowledge_base_id=config.get('knowledge_base', {}).get('knowledge_base_id'),
            region_name=config.get('region_name', 'us-east-1'),
            profile_name=config.get('profile_name'),
            schema_file_path=schema_file_path
        )
