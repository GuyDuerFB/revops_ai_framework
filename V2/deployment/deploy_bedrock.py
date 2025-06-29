#!/usr/bin/env python3
# RevOps AI Framework - Bedrock Deployment Script
# This script handles Amazon Bedrock operations for the deployment process
# It works with the main deploy_aws_cli.sh script and reads/updates the same state file

import argparse
import boto3
import botocore
import json
import os
import sys
import time
from typing import Dict, Any, Optional, List

# Configure logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default state file path
DEFAULT_STATE_FILE = "deploy_state.json"

def read_state(state_file: str = DEFAULT_STATE_FILE) -> Dict[str, Any]:
    """
    Read the deployment state from file
    
    Args:
        state_file: Path to the state file
        
    Returns:
        Dict containing the deployment state
    """
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"State file {state_file} not found, initializing empty state")
            return {}
    except Exception as e:
        logger.error(f"Failed to read state file: {e}")
        return {}

def write_state(state: Dict[str, Any], state_file: str = DEFAULT_STATE_FILE) -> None:
    """
    Write the deployment state to file
    
    Args:
        state: Dict containing the state to write
        state_file: Path to the state file
    """
    try:
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        logger.info(f"Updated state file {state_file}")
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")

def create_knowledge_base(profile_name: Optional[str] = None, state_file: str = DEFAULT_STATE_FILE) -> Dict[str, Any]:
    """
    Create an Amazon Bedrock knowledge base for the Firebolt schema
    
    Args:
        profile_name: AWS CLI profile name to use for credentials
        
    Returns:
        Dict with knowledge base information
    """
    # Create boto3 session and client with the specified profile
    session = boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
    bedrock_client = session.client('bedrock-agent')
    
    # Read the current state
    state = read_state()
    
    # Get required values from state file
    bucket_name = state.get('kb_bucket_name')
    role_name = state.get('lambda_role_name')
    
    if not bucket_name:
        logger.error("Knowledge base bucket not found in deployment state")
        sys.exit(1)
    
    if not role_name:
        logger.error("Lambda role not found in deployment state")
        sys.exit(1)
    
    # Get IAM role ARN 
    iam_client = session.client('iam')
    try:
        role_response = iam_client.get_role(RoleName=role_name)
        role_arn = role_response['Role']['Arn']
    except Exception as e:
        logger.error(f"Failed to retrieve IAM role ARN: {e}")
        sys.exit(1)
    
    bucket_arn = f"arn:aws:s3:::{bucket_name}"
    
    logger.info(f"Creating Bedrock knowledge base using S3 bucket: {bucket_name}")
    
    # Create data source
    try:
        # Check if the knowledge base already exists in the state
        if 'kb_id' in state:
            logger.info(f"Knowledge base already exists with ID: {state['kb_id']}")
            return {"kb_id": state['kb_id']}
            
        # Create data source
        ds_response = bedrock_client.create_data_source(
            name="firebolt-schema-datasource",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": bucket_arn,
                    "inclusionPrefixes": ["firebolt_schema/source/"]
                }
            }
        )
        
        # Extract data source ID
        data_source_id = ds_response['dataSource']['dataSourceId']
        logger.info(f"Created data source with ID: {data_source_id}")
        
        # Create knowledge base
        kb_response = bedrock_client.create_knowledge_base(
            name="firebolt-schema-kb",
            description="Firebolt schema knowledge base for data agent",
            roleArn=role_arn,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v1"
                }
            },
            storageConfiguration={
                "type": "BEDROCK_MANAGED"
            }
        )
        
        # Extract knowledge base ID
        kb_id = kb_response['knowledgeBase']['knowledgeBaseId']
        logger.info(f"Created knowledge base with ID: {kb_id}")
        
        # Associate data source with knowledge base
        bedrock_client.associate_knowledge_base_data_source(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id
        )
        
        # Update state file
        if 'kb_id' not in state:
            state['kb_id'] = kb_id
            write_state(state)
        
        return {"kb_id": kb_id}
        
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        
        # Handle idempotent creation (resource already exists)
        if error_code == 'ConflictException':
            logger.warning(f"Resource already exists: {e}")
            # Try to get existing KB ID
            existing_kbs = bedrock_client.list_knowledge_bases()
            for kb in existing_kbs.get('knowledgeBaseSummaries', []):
                if kb['name'] == "firebolt-schema-kb":
                    kb_id = kb['knowledgeBaseId']
                    logger.info(f"Found existing knowledge base with ID: {kb_id}")
                    state['kb_id'] = kb_id
                    write_state(state)
                    return {"kb_id": kb_id}
            logger.error("Failed to find existing knowledge base")
            sys.exit(1)
        else:
            logger.error(f"Failed to create knowledge base: {e}")
            sys.exit(1)

def create_agent(profile_name: Optional[str] = None, state_file: str = DEFAULT_STATE_FILE) -> Dict[str, Any]:
    """
    Create an Amazon Bedrock agent for the RevOps AI framework data agent
    
    Args:
        profile_name: AWS CLI profile name to use for credentials
        
    Returns:
        Dict with agent and alias information
    """
    # Create boto3 session and client with the specified profile
    session = boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
    bedrock_client = session.client('bedrock-agent')
    
    # Read the current state
    state = read_state()
    
    # Get required values from state file
    kb_id = state.get('kb_id')
    lambda_functions = state.get('lambda_functions', {})
    reader_lambda_arn = lambda_functions.get('firebolt_reader')
    
    if not kb_id:
        logger.error("Knowledge base ID not found in deployment state")
        sys.exit(1)
        
    if not reader_lambda_arn:
        logger.error("Firebolt reader Lambda ARN not found in deployment state")
        sys.exit(1)
    
    # Check if the agent already exists in the state
    if 'agents' in state and 'data_agent' in state['agents']:
        agent_id = state['agents']['data_agent'].get('id')
        alias_id = state['agents']['data_agent'].get('alias_id')
        logger.info(f"Agent already exists with ID: {agent_id}")
        return {"agent_id": agent_id, "alias_id": alias_id}
    
    logger.info("Creating Bedrock agent")
    
    try:
        # Create agent
        agent_response = bedrock_client.create_agent(
            agentName="revops-data-agent",
            description="RevOps AI Framework Data Agent",
            instructions="You are an AI assistant that helps with querying and analyzing data from Firebolt databases. You can help users explore schema information and execute SQL queries.",
            foundationModel="anthropic.claude-3-7-sonnet-20250219-v1:0",
        )
        
        # Extract agent ID
        agent_id = agent_response['agent']['agentId']
        logger.info(f"Created agent with ID: {agent_id}")
        
        # Associate knowledge base with agent
        bedrock_client.associate_agent_knowledge_base(
            agentId=agent_id,
            knowledgeBaseId=kb_id,
            description="Firebolt schema knowledge base"
        )
        
        # Find the schema file for action group
        api_schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                      "tools/firebolt/query_lambda/api_schema.json")
        
        # Read the API schema file
        with open(api_schema_path, 'r') as f:
            api_schema = json.load(f)
        
        # Create action group for firebolt reader
        bedrock_client.create_agent_action_group(
            agentId=agent_id,
            actionGroupName="firebolt-reader-action",
            actionGroupExecutor="firebolt_reader",
            description="Actions for querying Firebolt database",
            functionSchema=json.dumps(api_schema),
            lambdaFunction=reader_lambda_arn
        )
        
        # Create agent alias for deployment
        alias_response = bedrock_client.create_agent_alias(
            agentId=agent_id,
            agentAliasName="data-agent-prod",
            description="Production alias for data agent"
        )
        
        # Extract alias ID
        alias_id = alias_response['agentAlias']['agentAliasId']
        logger.info(f"Created agent alias: {alias_id}")
        
        # Update state file
        if 'agents' not in state:
            state['agents'] = {}
            
        state['agents']['data_agent'] = {
            'id': agent_id,
            'alias_id': alias_id
        }
        
        write_state(state)
        
        return {"agent_id": agent_id, "alias_id": alias_id}
        
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        
        # Handle idempotent creation (resource already exists)
        if error_code == 'ConflictException':
            logger.warning(f"Resource already exists: {e}")
            # Try to get existing agent
            existing_agents = bedrock_client.list_agents()
            for agent in existing_agents.get('agentSummaries', []):
                if agent['agentName'] == "revops-data-agent":
                    agent_id = agent['agentId']
                    logger.info(f"Found existing agent with ID: {agent_id}")
                    
                    # Get agent aliases
                    aliases = bedrock_client.list_agent_aliases(agentId=agent_id)
                    alias_id = None
                    for alias in aliases.get('agentAliasSummaries', []):
                        if alias['agentAliasName'] == "data-agent-prod":
                            alias_id = alias['agentAliasId']
                            logger.info(f"Found existing agent alias: {alias_id}")
                            break
                    
                    # Store in state
                    if 'agents' not in state:
                        state['agents'] = {}
                    
                    state['agents']['data_agent'] = {
                        'id': agent_id,
                        'alias_id': alias_id
                    }
                    write_state(state)
                    
                    return {"agent_id": agent_id, "alias_id": alias_id}
            
            logger.error("Failed to find existing agent")
            sys.exit(1)
        else:
            logger.error(f"Failed to create agent: {e}")
            sys.exit(1)

def parse_arguments():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(description="Deploy Bedrock knowledge base and agent")
    parser.add_argument('--create-kb', action='store_true', help='Create Bedrock knowledge base')
    parser.add_argument('--create-agent', action='store_true', help='Create Bedrock agent')
    parser.add_argument('--profile', type=str, help='AWS CLI profile to use')
    parser.add_argument('--state-file', type=str, default=DEFAULT_STATE_FILE, help='Path to the deployment state file')
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Set deployment state file path
    state_file = args.state_file
    
    # Print boto3 version information for debugging
    logger.debug(f"boto3 version: {boto3.__version__}")
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Using state file: {state_file}")
    
    if args.profile:
        logger.debug(f"Using AWS profile: {args.profile}")
    else:
        logger.debug("No AWS profile specified, using default credentials")
    
    try:
        if args.create_kb:
            create_knowledge_base(args.profile, state_file)
            
        if args.create_agent:
            create_agent(args.profile, state_file)
            
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
