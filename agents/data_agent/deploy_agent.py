#!/usr/bin/env python
"""
Deploy the RevOps Data Agent to Amazon Bedrock.
This script creates or updates the agent definition and associates the
necessary Lambda functions as action group handlers.
"""

import os
import argparse
import json
import boto3
import time
from agent_definition import DataAgent, prepare_action_groups

def get_agent_lambda_arns():
    """
    Get the ARNs of the Lambda functions used by the agent.
    
    Returns:
        dict: Dictionary mapping action group names to Lambda ARNs
    """
    lambda_client = boto3.client('lambda')
    
    # Get ARNs for each tool Lambda function
    firebolt_lambda = lambda_client.get_function(
        FunctionName=os.environ.get('FIREBOLT_LAMBDA_NAME', 'revops-firebolt-tool')
    )
    firebolt_lambda_arn = firebolt_lambda['Configuration']['FunctionArn']
    
    # Add other tool Lambdas as needed (Salesforce, Gong, Slack, etc.)
    
    return {
        "FireboltDataRetrieval": firebolt_lambda_arn,
        # Add other action groups here
    }

def deploy_agent(agent_name, alias_name, region=None):
    """
    Deploy the RevOps Data Agent to Amazon Bedrock.
    
    Args:
        agent_name (str): Name of the agent
        alias_name (str): Name of the agent alias
        region (str, optional): AWS region to deploy to
    
    Returns:
        dict: Deployment details
    """
    if region:
        os.environ['AWS_DEFAULT_REGION'] = region
    
    # Prepare action groups
    action_groups = prepare_action_groups()
    
    # Serialize and deserialize the action groups to ensure proper JSON formatting
    # This will convert Python booleans (True/False) to JSON booleans (true/false)
    serialized_action_groups = json.dumps(action_groups)
    action_groups = json.loads(serialized_action_groups)
    
    # Create or update the agent
    print(f"Creating Bedrock Agent: {agent_name}")
    agent_response = DataAgent.create_agent(
        agent_name=agent_name,
        description="RevOps Data Agent for retrieving and preprocessing data from multiple sources",
        instruction_source_file="instructions.md",
        foundation_model="anthropic.claude-3-sonnet-20240229-v1:0",
        action_group_definitions=action_groups
    )
    
    agent_id = agent_response['agentId']
    print(f"Agent created with ID: {agent_id}")
    
    # Wait for agent creation to complete
    print("Waiting for agent creation to complete...")
    time.sleep(10)
    
    # Get Lambda ARNs
    lambda_arns = get_agent_lambda_arns()
    
    # Associate Lambda functions with action groups
    bedrock_agent = boto3.client('bedrock-agent')
    for action_group_name, lambda_arn in lambda_arns.items():
        print(f"Associating Lambda {lambda_arn} with action group {action_group_name}")
        bedrock_agent.update_agent_action_group(
            agentId=agent_id,
            actionGroupId=action_group_name,
            actionGroupExecutor={
                'lambda': lambda_arn
            }
        )
    
    # Create agent alias
    print(f"Creating agent alias: {alias_name}")
    alias_response = DataAgent.create_agent_alias(
        agent_id=agent_id,
        alias_name=alias_name
    )
    
    alias_id = alias_response['agentAliasId']
    print(f"Agent alias created with ID: {alias_id}")
    
    # Prepare for agent invocation
    print("\nAgent Deployment Complete!")
    print(f"Agent ID: {agent_id}")
    print(f"Agent Alias ID: {alias_id}")
    
    # Save deployment details to file
    deployment_details = {
        "agent_id": agent_id,
        "agent_alias_id": alias_id,
        "agent_name": agent_name,
        "action_groups": list(lambda_arns.keys()),
        "deployment_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open("agent_deployment.json", "w") as f:
        json.dump(deployment_details, f, indent=2)
    
    print("Deployment details saved to agent_deployment.json")
    
    return deployment_details

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy RevOps Data Agent to Amazon Bedrock")
    parser.add_argument("--agent-name", default="RevOpsDataAgent", help="Name of the agent")
    parser.add_argument("--alias-name", default="Production", help="Name of the agent alias")
    parser.add_argument("--region", help="AWS region to deploy to")
    
    args = parser.parse_args()
    deploy_agent(args.agent_name, args.alias_name, args.region)
