#!/usr/bin/env python3
"""
List and compare V3 vs V4 agents in AWS Bedrock
"""

import boto3
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_agents_by_version():
    """List all agents grouped by version"""
    
    profile_name = "FireboltSystemAdministrator-740202120544"
    region_name = "us-east-1"
    
    session = boto3.Session(profile_name=profile_name)
    bedrock_client = session.client('bedrock-agent', region_name=region_name)
    
    try:
        # Get all agents
        response = bedrock_client.list_agents()
        agents = response['agentSummaries']
        
        # Group by version
        v3_agents = []
        v4_agents = []
        other_agents = []
        
        for agent in agents:
            agent_name = agent['agentName']
            agent_id = agent['agentId']
            
            if '-V4' in agent_name:
                v4_agents.append(agent)
            elif any(name in agent_name for name in ['DataAgent', 'ManagerAgent', 'DecisionAgent', 'WebSearchAgent', 'ExecutionAgent']):
                # These are likely V3 agents
                v3_agents.append(agent)
            else:
                other_agents.append(agent)
        
        # Print results
        print("🔍 RevOps AI Framework Agents by Version")
        print("=" * 60)
        
        print(f"\n📊 V4 Agents ({len(v4_agents)}):")
        for agent in v4_agents:
            print(f"   • {agent['agentName']} ({agent['agentId']})")
            print(f"     Created: {agent['createdAt'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     Status: {agent['agentStatus']}")
        
        print(f"\n📊 V3 Agents ({len(v3_agents)}):")
        for agent in v3_agents:
            print(f"   • {agent['agentName']} ({agent['agentId']})")
            print(f"     Created: {agent['createdAt'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     Status: {agent['agentStatus']}")
        
        if other_agents:
            print(f"\n📊 Other Agents ({len(other_agents)}):")
            for agent in other_agents:
                print(f"   • {agent['agentName']} ({agent['agentId']})")
                print(f"     Created: {agent['createdAt'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"     Status: {agent['agentStatus']}")
        
        print(f"\n📈 Summary:")
        print(f"   V4 Agents: {len(v4_agents)}")
        print(f"   V3 Agents: {len(v3_agents)}")
        print(f"   Other Agents: {len(other_agents)}")
        print(f"   Total: {len(agents)}")
        
    except Exception as e:
        logger.error(f"❌ Error listing agents: {str(e)}")

def get_agent_tags(agent_id):
    """Get tags for a specific agent"""
    
    profile_name = "FireboltSystemAdministrator-740202120544"
    region_name = "us-east-1"
    
    session = boto3.Session(profile_name=profile_name)
    bedrock_client = session.client('bedrock-agent', region_name=region_name)
    
    try:
        response = bedrock_client.list_tags_for_resource(
            resourceArn=f"arn:aws:bedrock:{region_name}:740202120544:agent/{agent_id}"
        )
        return response.get('tags', {})
    except Exception as e:
        logger.error(f"❌ Error getting tags for agent {agent_id}: {str(e)}")
        return {}

if __name__ == "__main__":
    list_agents_by_version()