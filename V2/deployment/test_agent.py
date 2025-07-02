#!/usr/bin/env python3
"""
Test script for the deployed RevOps data agent
"""

import boto3
import json
import time

def test_agent():
    # Initialize Bedrock agent runtime client
    session = boto3.Session(profile_name="FireboltSystemAdministrator-740202120544", region_name="us-east-1")
    client = session.client('bedrock-agent-runtime')
    
    agent_id = "P84K34SLQX"
    agent_alias_id = "YSI0ZRMAH6"
    session_id = f"test-{int(time.time())}"
    
    try:
        print(f"Testing agent {agent_id} with alias {agent_alias_id}")
        print("=" * 60)
        
        # Test 1: Simple Firebolt query
        print("\n🧪 Test 1: Simple Firebolt query")
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText="Can you run a simple Firebolt query to test the connection? Please use the query 'SELECT 1 as test_value'"
        )
        
        # Process streaming response
        print("Response:")
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    print(text, end='')
            elif 'trace' in event:
                print(f"\n[TRACE] {event['trace']}")
        
        print("\n" + "=" * 60)
        
        # Test 2: Gong data retrieval
        print("\n🧪 Test 2: Gong data retrieval")
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id + "-gong",
            inputText="Can you retrieve some call data from Gong for the last 7 days?"
        )
        
        # Process streaming response
        print("Response:")
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    print(text, end='')
            elif 'trace' in event:
                print(f"\n[TRACE] {event['trace']}")
        
        print("\n" + "=" * 60)
        print("✅ Agent testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agent()