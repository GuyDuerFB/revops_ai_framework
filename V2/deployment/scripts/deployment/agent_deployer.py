#!/usr/bin/env python3
"""
RevOps AI Framework V2 - Agent Deployer

This script deploys Bedrock agents including:
- Data Analysis Agent
- Decision Agent
- Execution Agent

Each agent is created with appropriate action groups and prompt configurations.
"""

import os
import json
import boto3
import time
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_agent_instructions(instructions_file: str) -> str:
    """
    Read agent instructions from file
    
    Args:
        instructions_file: Path to instructions file
        
    Returns:
        Instructions text
    """
    # Resolve file path
    if not os.path.isabs(instructions_file):
        instructions_file = os.path.join(PROJECT_ROOT, instructions_file)
    
    with open(instructions_file, 'r') as f:
        return f.read()


def create_bedrock_agent(
    agent_name: str,
    instructions: str,
    foundation_model: str,
    action_groups: List[Dict[str, Any]],
    region: str
) -> Dict[str, str]:
    """
    Create a Bedrock agent with the specified configuration
    
    Args:
        agent_name: Name of the agent
        instructions: Agent instructions
        foundation_model: Foundation model ARN
        action_groups: List of action group configurations
        region: AWS region
        
    Returns:
        Dictionary with agent ID and ARN
    """
    bedrock = boto3.client('bedrock-agent', region_name=region)
    
    # Check if agent already exists
    agent_id = None
    try:
        # List agents to find if one with the same name exists
        paginator = bedrock.get_paginator('list_agents')
        for page in paginator.paginate():
            for agent in page['agents']:
                if agent['displayName'] == agent_name:
                    agent_id = agent['agentId']
                    print(f"Agent {agent_name} already exists with ID: {agent_id}")
                    return {
                        "agent_id": agent_id,
                        "agent_arn": agent['agentArn']
                    }
    except ClientError as e:
        print(f"Error checking existing agents: {e}")
    
    # Create new agent
    try:
        response = bedrock.create_agent(
            agentName=agent_name,
            foundationModel=foundation_model,
            instruction=instructions,
            description=f"RevOps AI Framework {agent_name}",
            customerEncryptionKeyArn=None,
            idleSessionTTLInSeconds=1800  # 30 minutes
        )
        
        agent_id = response['agent']['agentId']
        agent_arn = response['agent']['agentArn']
        print(f"Created agent {agent_name} with ID: {agent_id}")
        
        # Wait for agent to be available
        print("Waiting for agent to be available...")
        waiter = bedrock.get_waiter('agent_available')
        waiter.wait(agentId=agent_id)
        print(f"Agent {agent_name} is available")
        
        return {
            "agent_id": agent_id,
            "agent_arn": agent_arn
        }
        
    except ClientError as e:
        print(f"Error creating agent: {e}")
        raise


def prepare_action_groups(agent_type: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare action groups for the agent based on configuration
    
    Args:
        agent_type: Type of agent (data_agent, decision_agent, execution_agent)
        config: Configuration dictionary
        
    Returns:
        List of action group configurations
    """
    agent_config = config.get(agent_type, {})
    action_groups_config = agent_config.get("action_groups", [])
    prepared_groups = []
    
    for action_group in action_groups_config:
        action_group_name = action_group.get("name")
        
        # Skip if no name
        if not action_group_name:
            continue
        
        # Prepare action group based on type
        if "lambda_arn" in action_group and action_group["lambda_arn"]:
            # This is a Lambda action group
            prepared_groups.append({
                "actionGroupName": action_group_name,
                "actionGroupExecutor": {
                    "lambda": action_group["lambda_arn"]
                },
                "description": action_group.get("description", "")
            })
        elif "knowledge_base_id" in action_group and action_group["knowledge_base_id"]:
            # This is a knowledge base action group
            prepared_groups.append({
                "actionGroupName": action_group_name,
                "actionGroupExecutor": {
                    "knowledgeBaseId": action_group["knowledge_base_id"]
                },
                "description": action_group.get("description", "")
            })
    
    return prepared_groups


def add_action_groups_to_agent(
    agent_id: str,
    action_groups: List[Dict[str, Any]],
    region: str
) -> None:
    """
    Add action groups to a Bedrock agent
    
    Args:
        agent_id: Agent ID
        action_groups: List of action group configurations
        region: AWS region
    """
    bedrock = boto3.client('bedrock-agent', region_name=region)
    
    for action_group in action_groups:
        try:
            print(f"Adding action group {action_group['actionGroupName']} to agent {agent_id}")
            
            # Determine the type of action group
            if "lambda" in action_group["actionGroupExecutor"]:
                # Lambda action group
                bedrock.create_agent_action_group(
                    agentId=agent_id,
                    actionGroupName=action_group["actionGroupName"],
                    actionGroupExecutor={
                        "lambda": action_group["actionGroupExecutor"]["lambda"]
                    },
                    description=action_group["description"]
                )
            elif "knowledgeBaseId" in action_group["actionGroupExecutor"]:
                # Knowledge base action group
                bedrock.create_agent_action_group(
                    agentId=agent_id,
                    actionGroupName=action_group["actionGroupName"],
                    actionGroupExecutor={
                        "knowledgeBase": {
                            "knowledgeBaseId": action_group["actionGroupExecutor"]["knowledgeBaseId"]
                        }
                    },
                    description=action_group["description"]
                )
            
            print(f"Action group {action_group['actionGroupName']} added successfully")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'ConflictException':
                print(f"Action group {action_group['actionGroupName']} already exists, updating...")
                # Delete existing action group
                bedrock.delete_agent_action_group(
                    agentId=agent_id,
                    actionGroupName=action_group["actionGroupName"]
                )
                
                # Retry adding the action group
                time.sleep(5)  # Wait for delete to complete
                add_action_groups_to_agent(agent_id, [action_group], region)
            else:
                print(f"Error adding action group: {e}")
                raise


def create_agent_alias(
    agent_id: str,
    alias_name: str,
    region: str
) -> str:
    """
    Create an agent alias for the Bedrock agent
    
    Args:
        agent_id: Agent ID
        alias_name: Alias name
        region: AWS region
        
    Returns:
        Alias ID
    """
    bedrock = boto3.client('bedrock-agent', region_name=region)
    
    # Check if alias already exists
    alias_id = None
    try:
        # List aliases to find if one with the same name exists
        paginator = bedrock.get_paginator('list_agent_aliases')
        for page in paginator.paginate(agentId=agent_id):
            for alias in page['agentAliases']:
                if alias['agentAliasName'] == alias_name:
                    alias_id = alias['agentAliasId']
                    print(f"Agent alias {alias_name} already exists with ID: {alias_id}")
                    return alias_id
    except ClientError as e:
        print(f"Error checking existing aliases: {e}")
    
    # Create new alias
    try:
        response = bedrock.create_agent_alias(
            agentId=agent_id,
            agentAliasName=alias_name,
            description=f"Alias for RevOps AI Framework agent"
        )
        
        alias_id = response['agentAlias']['agentAliasId']
        print(f"Created agent alias {alias_name} with ID: {alias_id}")
        
        return alias_id
        
    except ClientError as e:
        print(f"Error creating agent alias: {e}")
        raise


def deploy_agent(config: Dict[str, Any], secrets: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
    """
    Deploy a Bedrock agent
    
    Args:
        config: Configuration dictionary
        secrets: Secrets dictionary
        agent_type: Type of agent (data_agent, decision_agent, execution_agent)
        
    Returns:
        Updated configuration with agent ID and alias ID
    """
    # Create a copy of the config to update
    updated_config = config.copy()
    
    # Get AWS region
    region = updated_config.get("region_name", "us-east-1")
    
    # Get agent-specific config
    agent_config = updated_config.get(agent_type, {})
    if not agent_config:
        print(f"No configuration found for {agent_type}")
        return {"config": updated_config}
    
    # Read agent instructions
    instructions_file = agent_config.get("instructions_file")
    if not instructions_file:
        print(f"No instructions file specified for {agent_type}")
        return {"config": updated_config}
    
    instructions = read_agent_instructions(instructions_file)
    
    # Check if agent already exists
    agent_id = agent_config.get("agent_id")
    if not agent_id:
        # Create new agent
        agent_name = f"{updated_config.get('project_name', 'revops-ai-framework')}-{agent_type}"
        foundation_model = agent_config.get("foundation_model", "anthropic.claude-3-sonnet-20240229-v1:0")
        
        agent_result = create_bedrock_agent(
            agent_name,
            instructions,
            foundation_model,
            [],  # Empty action groups initially
            region
        )
        
        agent_id = agent_result["agent_id"]
        updated_config[agent_type]["agent_id"] = agent_id
    
    # Prepare and add action groups
    action_groups = prepare_action_groups(agent_type, updated_config)
    if action_groups:
        add_action_groups_to_agent(agent_id, action_groups, region)
    
    # Create agent alias
    alias_id = agent_config.get("agent_alias_id")
    if not alias_id:
        alias_name = f"{updated_config.get('project_name', 'revops-ai-framework')}-{agent_type}-alias"
        alias_id = create_agent_alias(agent_id, alias_name, region)
        updated_config[agent_type]["agent_alias_id"] = alias_id
    
    return {"config": updated_config}


def test_agent(config: Dict[str, Any], secrets: Dict[str, Any], agent_type: str) -> None:
    """
    Test a Bedrock agent with a simple query
    
    Args:
        config: Configuration dictionary
        secrets: Secrets dictionary
        agent_type: Type of agent (data_agent, decision_agent, execution_agent)
    """
    # Get agent-specific config
    agent_config = config.get(agent_type, {})
    if not agent_config:
        print(f"No configuration found for {agent_type}")
        return
    
    # Get agent ID and alias ID
    agent_id = agent_config.get("agent_id")
    agent_alias_id = agent_config.get("agent_alias_id")
    
    if not agent_id or not agent_alias_id:
        print(f"Agent ID or alias ID is missing for {agent_type}")
        return
    
    # Get AWS region
    region = config.get("region_name", "us-east-1")
    
    # Create Bedrock agent runtime client
    bedrock = boto3.client('bedrock-agent-runtime', region_name=region)
    
    # Test query based on agent type
    test_query = ""
    if agent_type == "data_agent":
        test_query = "What tables are available in the Firebolt schema?"
    elif agent_type == "decision_agent":
        test_query = "Should we take action on accounts with decreasing usage?"
    elif agent_type == "execution_agent":
        test_query = "Send a test notification to slack channel #test"
    
    try:
        # Invoke agent
        print(f"Testing {agent_type} with query: '{test_query}'")
        
        response = bedrock.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=f"test-{agent_type}-{int(time.time())}",
            inputText=test_query
        )
        
        # Process response
        completion = ""
        for chunk in response["completion"]:
            if "chunk" in chunk and "bytes" in chunk["chunk"]:
                completion += chunk["chunk"]["bytes"].decode("utf-8")
        
        print(f"{agent_type} response:")
        print("-" * 50)
        print(completion)
        print("-" * 50)
        print(f"{agent_type} test completed successfully!")
        
    except ClientError as e:
        print(f"Error testing {agent_type}: {e}")


if __name__ == "__main__":
    # This script is not meant to be run directly
    print("This script is meant to be imported by deploy.py")
