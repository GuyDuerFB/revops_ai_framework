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

def invoke_agent(prompt, session_id=None, deployment_file="agent_deployment.json", region="us-east-1", profile="revops-dev-profile"):
    """
    Invoke the RevOps Data Agent with a prompt.
    
    Args:
        prompt (str): The prompt to send to the agent
        session_id (str, optional): Session ID for conversation context
        deployment_file (str): Path to the deployment details file
        region (str): AWS region name
        profile (str): AWS profile name
        
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
    print(f"Using AWS profile: {profile}")
    response = agent.invoke(prompt, session_id, region_name=region, profile_name=profile)
    
    # Print the important response metadata
    if 'agent_response' in response:
        print("\nAgent Response Metadata:")
        if 'sessionId' in response['agent_response']:
            print(f"Session ID: {response['agent_response']['sessionId']}")
        if 'contentType' in response['agent_response']:
            print(f"Content Type: {response['agent_response']['contentType']}")
            
        # Create a standardized response object
        processed_response = {
            'session_id': response.get('session_id', ''),
            'metadata': {
                'session_id': response['agent_response'].get('sessionId', ''),
                'content_type': response['agent_response'].get('contentType', '')
            }
        }
        
        # Check if this is a streaming response
        if 'completion' in response['agent_response']:
            print("\nResponse content:")
            print("---------------------")
            print("The agent provided a streaming response. Due to the limitations")
            print("of the AWS SDK, we can only indicate that a response was received.")
            print("\nTo view the full conversation and responses, please use the")
            print("AWS Console to check the Bedrock Agent conversation history.")
            print("---------------------")
            processed_response['response_type'] = 'stream'
            processed_response['has_content'] = True
            
        return processed_response
    else:
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
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--profile", default="revops-dev-profile", help="AWS profile name")
    
    args = parser.parse_args()
    
    if args.examples:
        sample_query_examples()
    elif args.prompt:
        response = invoke_agent(args.prompt, args.session_id, args.deployment_file, args.region, args.profile)
        print("\nAgent Response:")
        
        # Handle different response types
        if 'error' in response:
            print(f"Error: {response['error']}")
        elif 'response_text' in response:
            print("\n" + response['response_text'])
        else:
            # Try to print as JSON, but if it fails, print as string
            try:
                print(json.dumps(response, indent=2))
            except TypeError:
                print(str(response))
    else:
        parser.print_help()
