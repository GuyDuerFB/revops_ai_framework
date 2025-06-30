#!/usr/bin/env python3
"""
RevOps AI Framework V2 - Knowledge Base Deployer

This script deploys a Bedrock knowledge base for the schema information
used by the data agent for schema-aware querying.
"""

import os
import json
import boto3
import time
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_s3_bucket(bucket_name: str, region: str) -> None:
    """
    Create an S3 bucket for knowledge base storage if it doesn't exist
    
    Args:
        bucket_name: Name of the S3 bucket
        region: AWS region
    """
    s3_client = boto3.client('s3')
    
    try:
        # Check if bucket already exists
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"S3 bucket {bucket_name} already exists")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == '404':
            # Bucket doesn't exist, create it
            if region == 'us-east-1':
                # Special case for us-east-1
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            print(f"Created S3 bucket: {bucket_name} in {region}")
        else:
            print(f"Error checking S3 bucket: {e}")
            raise


def upload_schema_to_s3(schema_file_path: str, bucket_name: str, s3_key: str) -> str:
    """
    Upload schema file to S3
    
    Args:
        schema_file_path: Path to schema file
        bucket_name: S3 bucket name
        s3_key: S3 object key
    
    Returns:
        S3 URI
    """
    # Resolve schema file path
    if not os.path.isabs(schema_file_path):
        schema_file_path = os.path.join(PROJECT_ROOT, schema_file_path)
    
    # Upload file to S3
    s3_client = boto3.client('s3')
    s3_client.upload_file(schema_file_path, bucket_name, s3_key)
    
    s3_uri = f"s3://{bucket_name}/{s3_key}"
    print(f"Uploaded schema file to {s3_uri}")
    return s3_uri


def create_knowledge_base_role(role_name: str, bucket_name: str) -> str:
    """
    Create an IAM role for the knowledge base with S3 access
    
    Args:
        role_name: Name of the IAM role
        bucket_name: S3 bucket name for permissions
    
    Returns:
        Role ARN
    """
    iam = boto3.client('iam')
    
    # Trust policy
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
    
    # S3 access policy
    s3_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ]
            }
        ]
    }
    
    try:
        # Check if role already exists
        try:
            response = iam.get_role(RoleName=role_name)
            print(f"IAM role {role_name} already exists")
            return response['Role']['Arn']
        except iam.exceptions.NoSuchEntityException:
            # Create the role
            response = iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Role for RevOps AI Framework Knowledge Base"
            )
            print(f"Created IAM role {role_name}")
            
            # Create inline policy for S3 access
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=f"{role_name}-s3-access",
                PolicyDocument=json.dumps(s3_policy_document)
            )
            print(f"Attached S3 access policy to {role_name}")
            
            # Wait for role to be available
            print("Waiting for IAM role to be available...")
            time.sleep(10)
            
            return response['Role']['Arn']
            
    except ClientError as e:
        print(f"Error creating IAM role: {e}")
        raise


def create_knowledge_base(
    kb_name: str,
    role_arn: str,
    data_source_bucket: str,
    data_source_prefix: str,
    embedding_model: str,
    region: str
) -> Dict[str, str]:
    """
    Create a Bedrock knowledge base
    
    Args:
        kb_name: Name of the knowledge base
        role_arn: IAM role ARN for the knowledge base
        data_source_bucket: S3 bucket for data source
        data_source_prefix: S3 prefix for data source
        embedding_model: Embedding model ARN
        region: AWS region
    
    Returns:
        Dictionary with knowledge base ID and ARN
    """
    bedrock = boto3.client('bedrock-agent', region_name=region)
    
    # Check if knowledge base already exists
    kb_id = None
    try:
        # List knowledge bases to find if one with the same name exists
        paginator = bedrock.get_paginator('list_knowledge_bases')
        for page in paginator.paginate():
            for kb in page['knowledgeBases']:
                if kb['name'] == kb_name:
                    kb_id = kb['knowledgeBaseId']
                    print(f"Knowledge base {kb_name} already exists with ID: {kb_id}")
                    return {
                        "knowledge_base_id": kb_id,
                        "knowledge_base_arn": kb['knowledgeBaseArn']
                    }
    except ClientError as e:
        print(f"Error checking existing knowledge bases: {e}")
    
    # Create new knowledge base
    try:
        s3_data_source = {
            "type": "S3",
            "s3Configuration": {
                "bucketArn": f"arn:aws:s3:::{data_source_bucket}",
                "inclusionPrefixes": [data_source_prefix]
            }
        }
        
        storage_configuration = {
            "type": "BEDROCK_VECTOR_STORE",
            "bedrockVectorStoreConfiguration": {
                "embeddingModelArn": embedding_model
            }
        }
        
        response = bedrock.create_knowledge_base(
            name=kb_name,
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": embedding_model
                }
            },
            storageConfiguration=storage_configuration,
            dataSource=s3_data_source,
            description=f"Schema knowledge base for RevOps AI Framework"
        )
        
        kb_id = response['knowledgeBase']['knowledgeBaseId']
        kb_arn = response['knowledgeBase']['knowledgeBaseArn']
        print(f"Created knowledge base {kb_name} with ID: {kb_id}")
        
        # Wait for knowledge base to be available
        print("Waiting for knowledge base to be available...")
        waiter = bedrock.get_waiter('knowledge_base_available')
        waiter.wait(knowledgeBaseId=kb_id)
        print(f"Knowledge base {kb_name} is available")
        
        return {
            "knowledge_base_id": kb_id,
            "knowledge_base_arn": kb_arn
        }
        
    except ClientError as e:
        print(f"Error creating knowledge base: {e}")
        raise


def deploy_knowledge_base(config: Dict[str, Any], secrets: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deploy knowledge base for schema information
    
    Args:
        config: Configuration dictionary
        secrets: Secrets dictionary
    
    Returns:
        Updated configuration with knowledge base ID
    """
    # Create a copy of the config to update
    updated_config = config.copy()
    
    # Get knowledge base config
    kb_config = updated_config.get("knowledge_base", {})
    if not kb_config:
        print("No knowledge base configuration found")
        return {"config": updated_config}
    
    # Get AWS region
    region = updated_config.get("region_name", "us-east-1")
    
    # Create S3 bucket for knowledge base
    bucket_name = kb_config.get("storage_bucket")
    if not bucket_name:
        print("No storage bucket specified in knowledge base configuration")
        return {"config": updated_config}
    
    create_s3_bucket(bucket_name, region)
    
    # Upload schema file to S3
    schema_file_path = kb_config.get("schema_file_path")
    storage_prefix = kb_config.get("storage_prefix", "revops-ai-framework/knowledge/")
    schema_key = os.path.join(storage_prefix, "firebolt_schema.json")
    
    if schema_file_path:
        s3_uri = upload_schema_to_s3(schema_file_path, bucket_name, schema_key)
        print(f"Schema file uploaded to {s3_uri}")
    
    # Create IAM role for knowledge base
    role_name = "revops-kb-role"
    role_arn = kb_config.get("role_arn")
    if not role_arn:
        role_arn = create_knowledge_base_role(role_name, bucket_name)
        updated_config["knowledge_base"]["role_arn"] = role_arn
    
    # Create knowledge base
    kb_name = f"{updated_config.get('project_name', 'revops-ai-framework')}-kb"
    embedding_model = kb_config.get("storage_configuration", {}).get(
        "embeddingModelArn", 
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
    )
    
    if not kb_config.get("knowledge_base_id"):
        kb_result = create_knowledge_base(
            kb_name,
            role_arn,
            bucket_name,
            storage_prefix,
            embedding_model,
            region
        )
        
        updated_config["knowledge_base"]["knowledge_base_id"] = kb_result["knowledge_base_id"]
        
        # Update data_agent action group if it exists
        for i, action_group in enumerate(updated_config.get("data_agent", {}).get("action_groups", [])):
            if action_group.get("name") == "schema_lookup":
                updated_config["data_agent"]["action_groups"][i]["knowledge_base_id"] = kb_result["knowledge_base_id"]
                print(f"Updated data_agent action_group with knowledge base ID: {kb_result['knowledge_base_id']}")
    
    return {"config": updated_config}


def test_knowledge_base(config: Dict[str, Any]) -> None:
    """
    Test the knowledge base by retrieving information
    
    Args:
        config: Configuration dictionary
    """
    # Get knowledge base ID
    kb_id = config.get("knowledge_base", {}).get("knowledge_base_id")
    if not kb_id:
        print("No knowledge base ID found in configuration")
        return
    
    # Get AWS region
    region = config.get("region_name", "us-east-1")
    
    # Create Bedrock client
    bedrock = boto3.client('bedrock-agent-runtime', region_name=region)
    
    try:
        # Test query to the knowledge base
        response = bedrock.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                "text": "What tables are available in the Firebolt schema?"
            },
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 5
                }
            }
        )
        
        # Process response
        if response['retrievalResults']:
            print("Knowledge base test successful!")
            print(f"Found {len(response['retrievalResults'])} results")
            for i, result in enumerate(response['retrievalResults']):
                print(f"Result {i+1}:")
                print(f"  Content: {result['content']['text'][:100]}...")
                print(f"  Score: {result['score']}")
        else:
            print("Knowledge base test returned no results")
            
    except ClientError as e:
        print(f"Error testing knowledge base: {e}")


if __name__ == "__main__":
    # This script is not meant to be run directly
    print("This script is meant to be imported by deploy.py")
