#!/usr/bin/env python
"""
Deploy the RevOps Data Agent to Amazon Bedrock.

This script can either:
1. Create a new agent from scratch (default behavior)
2. Update an existing agent with new configuration (use --agent-id)
3. Create knowledge base source files and upload them to S3

Prerequisite: Configure AWS SSO with the appropriate profile (default: revops-dev-profile)
"""

import os
import argparse
import json
import time
from pathlib import Path
from agent_definition import DataAgent, prepare_action_groups, get_bedrock_agent_client, get_lambda_client

def get_agent_lambda_arns(region=None, profile=None):
    """
    Get the ARNs of the Lambda functions used by the agent.
    
    Args:
        region (str, optional): AWS region
        profile (str, optional): AWS profile name
    
    Returns:
        dict: Dictionary mapping action group names to Lambda ARNs
    """
    # Get Lambda ARNs from environment variables if available
    lambda_arns = {}
    
    # For the firebolt_function action group
    firebolt_lambda_arn = os.environ.get('FIREBOLT_LAMBDA_ARN')
    if firebolt_lambda_arn:
        lambda_arns["firebolt_function"] = firebolt_lambda_arn
    
    # If not found in environment variables, try to get from AWS
    if not lambda_arns and (region or profile):
        try:
            import boto3
            session = boto3.Session(region_name=region, profile_name=profile)
            lambda_client = session.client('lambda')
            
            # Try to find Lambda functions by name pattern
            response = lambda_client.list_functions()
            for func in response.get('Functions', []):
                if 'firebolt' in func['FunctionName'].lower() or 'queryfirebolt' in func['FunctionName'].lower():
                    lambda_arns["firebolt_function"] = func['FunctionArn']
                    break
        except Exception as e:
            print(f"Warning: Could not retrieve Lambda ARNs from AWS: {e}")
            
    # Fall back to the known Lambda ARN if none found
    if not lambda_arns:
        lambda_arns["firebolt_function"] = "arn:aws:lambda:us-east-1:740202120544:function:QueryFirebolt"
        print(f"Using default Lambda ARN: {lambda_arns['firebolt_function']}")
    
    return lambda_arns

def deploy_agent(agent_name, alias_name, region=None, profile=None, agent_id=None):
    """
    Deploy the RevOps Data Agent to Amazon Bedrock, or update an existing agent.
    
    Args:
        agent_name (str): Name of the agent
        alias_name (str): Name of the agent alias
        region (str, optional): AWS region to deploy to
        profile (str, optional): AWS profile name to use
        agent_id (str, optional): Existing agent ID to update (if None, creates new agent)
    
    Returns:
        dict: Deployment details
    """
    # Configure AWS region if specified
    if region:
        os.environ['AWS_DEFAULT_REGION'] = region
    
    # Working mode: create new agent or use existing agent
    if agent_id:
        print(f"Working with existing Bedrock Agent: {agent_id}")
        # Get information about the agent
        try:
            agent_info = DataAgent.get_agent_info(agent_id, region, profile)
            print(f"Found existing agent: {agent_info.get('agentName', 'Unknown')}")
        except Exception as e:
            print(f"Error getting agent info: {e}")
            return {"error": f"Could not retrieve agent with ID {agent_id}"}
    else:
        # Create a new agent from scratch
        # Prepare action groups
        action_groups = prepare_action_groups()
        
        # Serialize and deserialize the action groups to ensure proper JSON formatting
        serialized_action_groups = json.dumps(action_groups)
        action_groups = json.loads(serialized_action_groups)
        
        # Create the agent
        print(f"Creating new Bedrock Agent: {agent_name}")
        agent_response = DataAgent.create_agent(
            agent_name=agent_name,
            description="RevOps Data Agent for retrieving and preprocessing data from multiple sources",
            instruction_source_file="instructions.md",
            foundation_model="anthropic.claude-3-sonnet-20240229-v1:0",
            action_group_definitions=action_groups,
            region_name=region,
            profile_name=profile
        )
        
        agent_id = agent_response['agentId']
        print(f"Agent created with ID: {agent_id}")
        
        # Wait for agent creation to complete
        print("Waiting for agent creation to complete...")
        time.sleep(10)
        
        # Get Lambda ARNs
        lambda_arns = get_agent_lambda_arns(region, profile)
        
        # Create the function schema for firebolt_function action group
        firebolt_function_schema = {
            "functions": [
                {
                    "name": "query_fire",
                    "description": "Execute SQL queries against Firebolt data warehouse and return structured results. Can handle both simple SQL queries and SQL queries wrapped in markdown code blocks. Useful for retrieving business data, consumption metrics, account information, and other analytics data from Firebolt.",
                    "parameters": {
                        "query": {
                            "description": "The SQL query to execute against Firebolt. Can be provided as plain SQL or wrapped in markdown code blocks (```sql ... ```). Examples: 'SELECT * FROM accounts LIMIT 10' or 'SELECT account_name, total_consumption FROM usage_summary WHERE date >= CURRENT_DATE - 7'",
                            "required": False,
                            "type": "string"
                        }
                    },
                    "requireConfirmation": "DISABLED"
                }
            ]
        }
        
        # Create or update action groups
        if lambda_arns:
            for action_group_name, lambda_arn in lambda_arns.items():
                print(f"Creating action group: {action_group_name}, Lambda: {lambda_arn}")
                try:
                    # If agent_id is provided, we're updating an existing agent
                    client = get_bedrock_agent_client(region_name=region, profile_name=profile)
                    client.create_agent_action_group(
                        agentId=agent_id,
                        agentVersion='DRAFT',
                        actionGroupExecutor={
                            "lambda": lambda_arn
                        },
                        actionGroupName=action_group_name,
                        description="Firebolt functions for the ai agent to use",
                        functionSchema=firebolt_function_schema
                    )
                except Exception as e:
                    print(f"Warning: Could not create/update action group: {e}")
                    
        # Create agent alias
        print(f"Creating agent alias: {alias_name}")
        alias_response = DataAgent.create_agent_alias(
            agent_id=agent_id,
            alias_name=alias_name,
            region_name=region,
            profile_name=profile
        )
        
        alias_id = alias_response.get('agentAliasId')
        print(f"Agent alias created with ID: {alias_id}")
    
    # Set up a default alias_id if we're working with an existing agent
    if agent_id and 'alias_id' not in locals():
        # Attempt to get the alias from the agent
        try:
            bedrock_agent = get_bedrock_agent_client(region_name=region, profile_name=profile)
            aliases_response = bedrock_agent.list_agent_aliases(
                agentId=agent_id
            )
            if aliases_response.get('agentAliasSummaries'):
                alias_id = aliases_response['agentAliasSummaries'][0]['agentAliasId']
                print(f"Using existing agent alias: {alias_id}")
            else:
                alias_id = "TSTALIASID"  # Default if no aliases found
                print(f"No aliases found, using default: {alias_id}")
        except Exception as e:
            print(f"Error getting agent aliases: {e}")
            alias_id = "TSTALIASID"  # Default if error occurs
            print(f"Using default alias ID: {alias_id}")
    
    # Prepare for agent invocation
    print("\nAgent Deployment Complete!")
    print(f"Agent ID: {agent_id}")
    print(f"Agent Alias ID: {alias_id}")
    
    # Create account_id - needed for ARN construction
    # Default value, will be overridden if running with the right permissions
    account_id = "740202120544"
    
    # Try to get account ID from STS if we have permission
    try:
        import boto3
        sts_client = boto3.client('sts', region_name=region if region else 'us-east-1')
        account_id = sts_client.get_caller_identity().get('Account')
    except Exception:
        # Use default account ID if STS call fails
        pass
    
    # Construct action_groups list and Lambda ARNs
    action_groups = ["firebolt_function"]
    if 'lambda_arns' in locals() and lambda_arns:
        action_groups = list(lambda_arns.keys())
        
    # Include Lambda ARNs in deployment details
    lambda_arns_for_json = {}
    if 'lambda_arns' in locals() and lambda_arns:
        lambda_arns_for_json = lambda_arns
    
    # Save deployment details to a JSON file
    deployment_details = {
        "agent_id": agent_id,
        "agent_alias_id": alias_id,
        "agent_name": agent_name,
        "agent_arn": f"arn:aws:bedrock:us-east-1:{account_id}:agent/{agent_id}",
        "action_groups": action_groups,
        "lambda_arns": lambda_arns_for_json,
        "foundation_model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "deployment_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "description": "RevOps Data Agent for retrieving and preprocessing data from multiple sources"
    }
    
    # Save deployment details to JSON file
    output_file = "agent_deployment.json"
    with open(output_file, "w") as f:
        json.dump(deployment_details, f, indent=2)
    
    print(f"Deployment details saved to {output_file}")
    print(f"Agent Name: {agent_name}")
    print(f"Agent ID: {agent_id}")
    print(f"Agent Alias ID: {alias_id}")
    print(f"Action Groups: {', '.join(action_groups)}")
    
    return deployment_details

def upload_knowledge_base(bucket_name, prefix, file_path, region=None, profile=None):
    """
    Upload a knowledge base file to S3.
    
    Args:
        bucket_name (str): S3 bucket name
        prefix (str): S3 key prefix (folder path)
        file_path (str): Local file path to upload
        region (str, optional): AWS region
        profile (str, optional): AWS profile name
    """
    try:
        import boto3
        session = boto3.Session(region_name=region, profile_name=profile)
        s3_client = session.client('s3')
        
        # Get just the filename
        filename = Path(file_path).name
        s3_key = f"{prefix}/{filename}"
        
        print(f"Uploading {file_path} to s3://{bucket_name}/{s3_key}")
        s3_client.upload_file(file_path, bucket_name, s3_key)
        print(f"Upload successful!")
        return True
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy RevOps Data Agent to Amazon Bedrock")
    parser.add_argument("--agent-name", default="RevOpsDataAgent", help="Name of the agent")
    parser.add_argument("--alias-name", default="Production", help="Name of the agent alias")
    parser.add_argument("--region", default="us-east-1", help="AWS region to deploy to")
    parser.add_argument("--profile", default="revops-dev-profile", help="AWS profile name")
    parser.add_argument("--agent-id", help="Existing agent ID to update (if not provided, creates new agent)")
    parser.add_argument("--upload-knowledge", action="store_true", help="Upload schema_knowledge.md to S3")
    parser.add_argument("--s3-bucket", default="revops-s3-bucket", help="S3 bucket for knowledge base")
    parser.add_argument("--s3-prefix", default="revops-ai-framework/schema-information", help="S3 prefix for knowledge base")
    
    args = parser.parse_args()
    
    # Upload knowledge base if requested
    if args.upload_knowledge:
        print("Uploading knowledge base file to S3...")
        # Ensure the schema_knowledge.md file exists
        knowledge_file = Path("schema_knowledge.md")
        if not knowledge_file.exists():
            print(f"Error: {knowledge_file} not found")
            exit(1)
            
        success = upload_knowledge_base(
            bucket_name=args.s3_bucket,
            prefix=args.s3_prefix,
            file_path=str(knowledge_file),
            region=args.region,
            profile=args.profile
        )
        
        if not success:
            print("Knowledge base upload failed. Exiting.")
            exit(1)
            
        print(f"Knowledge base uploaded to s3://{args.s3_bucket}/{args.s3_prefix}/{knowledge_file.name}")
    
    # Deploy or update the agent
    if args.agent_id:
        print(f"Updating existing agent: {args.agent_id}")
    else:
        print(f"Creating new agent: {args.agent_name}")
        
    deploy_agent(
        agent_name=args.agent_name,
        alias_name=args.alias_name,
        region=args.region,
        profile=args.profile,
        agent_id=args.agent_id
    )
