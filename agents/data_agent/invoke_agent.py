#!/usr/bin/env python
"""
Sample script to invoke the RevOps Data Agent.
This script demonstrates how to interact with the Bedrock agent
once it has been deployed.
"""

import os
import json
import argparse
from agent_definition import DataAgent

def load_deployment_details(deployment_file="agent_deployment.json"):
    """
    Load agent deployment details from file.
    
    Args:
        deployment_file (str): Path to the deployment details file
        
    Returns:
        dict: Deployment details
    """
    try:
        with open(deployment_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception(f"Deployment file {deployment_file} not found. Please deploy the agent first.")

def invoke_agent(prompt, session_id=None, deployment_file="agent_deployment.json"):
    """
    Invoke the RevOps Data Agent with a prompt.
    
    Args:
        prompt (str): The prompt to send to the agent
        session_id (str, optional): Session ID for conversation context
        deployment_file (str): Path to the deployment details file
        
    Returns:
        dict: Agent response
    """
    # Load deployment details
    details = load_deployment_details(deployment_file)
    
    # Initialize the agent
    agent = DataAgent(
        agent_id=details["agent_id"],
        agent_alias_id=details["agent_alias_id"]
    )
    
    # Invoke the agent
    print(f"Invoking agent {details['agent_name']} with prompt: {prompt[:100]}...")
    response = agent.invoke(prompt, session_id)
    
    return response

def sample_query_examples():
    """
    Print sample query examples for the Data Agent.
    """
    examples = [
        "Gather all data required for A1 analysis (at-risk account identification). Target: enterprise accounts. Additional context: focus on accounts with declining usage trends in the last 90 days.",
        
        "Gather all data required for A3 analysis (upsell opportunity detection). Target: account_id='ACME-123'. Additional context: look for features with high adoption among similar customers that this account isn't using.",
        
        "What are the most common reasons for closed-lost opportunities in the healthcare sector during Q1 2025? Use data from both Salesforce and Gong calls.",
        
        "Identify customers with unusually high data scan volume compared to their query count over the past 30 days."
    ]
    
    print("\nSample query examples for the RevOps Data Agent:")
    for i, example in enumerate(examples, 1):
        print(f"\nExample {i}:")
        print(f"  {example}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Invoke the RevOps Data Agent")
    parser.add_argument("--prompt", help="Prompt to send to the agent")
    parser.add_argument("--session-id", help="Session ID for conversation context")
    parser.add_argument("--deployment-file", default="agent_deployment.json", help="Path to the deployment details file")
    parser.add_argument("--examples", action="store_true", help="Show sample query examples")
    
    args = parser.parse_args()
    
    if args.examples:
        sample_query_examples()
    elif args.prompt:
        response = invoke_agent(args.prompt, args.session_id, args.deployment_file)
        print("\nAgent Response:")
        print(json.dumps(response, indent=2))
    else:
        parser.print_help()
