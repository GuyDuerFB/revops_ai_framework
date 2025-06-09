#!/usr/bin/env python
"""
List Bedrock agent details
"""
import boto3
import json

# Initialize client
bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')

def get_agent_details(agent_id):
    """Get details for a specific agent"""
    try:
        # Describe the agent
        response = bedrock_agent.get_agent(
            agentId=agent_id
        )
        print("Agent Details:")
        print(json.dumps(response, indent=2, default=str))
        
        # List aliases
        aliases = bedrock_agent.list_agent_aliases(
            agentId=agent_id
        )
        print("\nAgent Aliases:")
        print(json.dumps(aliases, indent=2, default=str))
        
        return response
    except Exception as e:
        print(f"Error accessing agent: {e}")
        return None

if __name__ == "__main__":
    # Your agent ID
    agent_id = "JDIOCIZ7XU"
    get_agent_details(agent_id)
