#!/usr/bin/env python3
"""
RevOps AI Framework V2 - Agent Permissions Fix Script

This script fixes agent configurations and Lambda permissions to ensure
proper function calling from Bedrock Agents.
"""

import json
import boto3
import sys
import time
from typing import Dict, List, Any

CONFIG_PATH = "config.json"
AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"
ACCOUNT_ID = "740202120544"

def load_config():
    """Load configuration from JSON file"""
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def fix_lambda_permissions():
    """Fix Lambda permissions for Bedrock Agent access"""
    print("🔐 Fixing Lambda permissions for Bedrock Agent access...")
    
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    lambda_client = session.client('lambda')
    
    # Lambda permissions mapping: function_name -> (agent_id, statement_id)
    permissions = [
        ("revops-firebolt-writer", "TCX9CGOKBR", "bedrock-agent-decision-invoke"),
        ("revops-firebolt-writer", "UWMCP4AYZX", "bedrock-agent-exec-invoke"),
        ("revops-web-search", "TCX9CGOKBR", "bedrock-agent-decision-invoke"),
        ("revops-webhook", "TCX9CGOKBR", "bedrock-agent-decision-invoke"),
        ("revops-webhook", "UWMCP4AYZX", "bedrock-agent-exec-invoke"),
        ("revops-firebolt-query", "9B8EGU46UV", "bedrock-agent-data-invoke"),
        ("revops-gong-retrieval", "9B8EGU46UV", "bedrock-agent-data-invoke"),
    ]
    
    for function_name, agent_id, statement_id in permissions:
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='bedrock.amazonaws.com',
                SourceArn=f'arn:aws:bedrock:{AWS_REGION}:{ACCOUNT_ID}:agent/{agent_id}'
            )
            print(f"✅ Added permission for {function_name} (agent: {agent_id})")
        except lambda_client.exceptions.ResourceConflictException:
            print(f"ℹ️  Permission already exists for {function_name} (agent: {agent_id})")
        except Exception as e:
            print(f"❌ Error adding permission for {function_name}: {e}")

def create_action_group_schema():
    """Create action group schemas for agents"""
    schemas = {
        "web_search": {
            "type": "object",
            "properties": {
                "search_web": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "integer", "description": "Number of results (default: 5)"},
                        "region": {"type": "string", "description": "Search region (default: us)"}
                    },
                    "required": ["query"]
                },
                "research_company": {
                    "type": "object", 
                    "properties": {
                        "company_name": {"type": "string", "description": "Company name to research"},
                        "focus_area": {"type": "string", "description": "Research focus area"}
                    },
                    "required": ["company_name"]
                }
            }
        },
        "firebolt_writer": {
            "type": "object",
            "properties": {
                "write_insight": {
                    "type": "object",
                    "properties": {
                        "insight_data": {"type": "object", "description": "Insight data to write"},
                        "table_name": {"type": "string", "description": "Target table name"}
                    },
                    "required": ["insight_data"]
                }
            }
        },
        "webhook": {
            "type": "object",
            "properties": {
                "send_notification": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Notification message"},
                        "priority": {"type": "string", "description": "Priority level"},
                        "recipient": {"type": "string", "description": "Notification recipient"}
                    },
                    "required": ["message"]
                }
            }
        }
    }
    return schemas

def fix_decision_agent_action_groups():
    """Fix Decision Agent action groups configuration"""
    print("🔧 Fixing Decision Agent action groups...")
    
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    bedrock_client = session.client('bedrock-agent')
    
    agent_id = "TCX9CGOKBR"
    schemas = create_action_group_schema()
    
    # Action groups for Decision Agent
    action_groups = [
        {
            "actionGroupName": "web_search",
            "description": "Search the web for company research and lead intelligence",
            "actionGroupExecutor": {
                "lambda": f"arn:aws:lambda:{AWS_REGION}:{ACCOUNT_ID}:function:revops-web-search"
            },
            "functionSchema": {
                "functions": [
                    {
                        "name": "search_web",
                        "description": "Search the web using DuckDuckGo API",
                        "parameters": schemas["web_search"]["properties"]["search_web"]["properties"]
                    },
                    {
                        "name": "research_company", 
                        "description": "Research a specific company",
                        "parameters": schemas["web_search"]["properties"]["research_company"]["properties"]
                    }
                ]
            }
        },
        {
            "actionGroupName": "webhook",
            "description": "Send webhook notifications and trigger external actions",
            "actionGroupExecutor": {
                "lambda": f"arn:aws:lambda:{AWS_REGION}:{ACCOUNT_ID}:function:revops-webhook"
            },
            "functionSchema": {
                "functions": [
                    {
                        "name": "send_notification",
                        "description": "Send a webhook notification",
                        "parameters": schemas["webhook"]["properties"]["send_notification"]["properties"]
                    }
                ]
            }
        },
        {
            "actionGroupName": "firebolt_writer",
            "description": "Write data and insights back to Firebolt data warehouse",
            "actionGroupExecutor": {
                "lambda": f"arn:aws:lambda:{AWS_REGION}:{ACCOUNT_ID}:function:revops-firebolt-writer"
            },
            "functionSchema": {
                "functions": [
                    {
                        "name": "write_insight",
                        "description": "Write insight data to Firebolt",
                        "parameters": schemas["firebolt_writer"]["properties"]["write_insight"]["properties"]
                    }
                ]
            }
        }
    ]
    
    # Create each action group
    for action_group in action_groups:
        try:
            response = bedrock_client.create_agent_action_group(
                agentId=agent_id,
                agentVersion="DRAFT",
                **action_group
            )
            print(f"✅ Created action group: {action_group['actionGroupName']}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"ℹ️  Action group already exists: {action_group['actionGroupName']}")
            else:
                print(f"❌ Error creating action group {action_group['actionGroupName']}: {e}")

def prepare_agent():
    """Prepare the agent after updating action groups"""
    print("🔄 Preparing Decision Agent...")
    
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    bedrock_client = session.client('bedrock-agent')
    
    try:
        response = bedrock_client.prepare_agent(agentId="TCX9CGOKBR")
        print(f"✅ Agent preparation initiated: {response['agentStatus']}")
        
        # Wait for preparation to complete
        print("⏳ Waiting for agent preparation to complete...")
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(10)
            agent_response = bedrock_client.get_agent(agentId="TCX9CGOKBR")
            status = agent_response['agent']['agentStatus']
            print(f"   Status: {status}")
            
            if status == "PREPARED":
                print("✅ Agent preparation completed successfully!")
                return True
            elif status == "FAILED":
                print("❌ Agent preparation failed!")
                return False
                
        print("⚠️  Agent preparation timed out")
        return False
        
    except Exception as e:
        print(f"❌ Error preparing agent: {e}")
        return False

def main():
    """Main execution function"""
    print("🚀 RevOps AI Framework V2 - Agent Permissions Fix")
    print("=" * 60)
    
    try:
        # Step 1: Fix Lambda permissions
        fix_lambda_permissions()
        print()
        
        # Step 2: Fix Decision Agent action groups
        fix_decision_agent_action_groups()
        print()
        
        # Step 3: Prepare agent
        success = prepare_agent()
        print()
        
        if success:
            print("🎉 Agent permissions fix completed successfully!")
            print("🧪 You can now test the flow execution.")
        else:
            print("⚠️  Agent preparation had issues. Check AWS console.")
            
    except Exception as e:
        print(f"❌ Script execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()