#!/usr/bin/env python3
"""
Complete WebSearch Agent Deployment

Full deployment script for WebSearch Agent including creation, action groups, 
alias, permissions, and testing.
"""

import boto3
import json
import sys
import os
import time
from typing import Dict, Any, Tuple

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def load_agent_instructions() -> str:
    """Load WebSearch Agent instructions from file"""
    instructions_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'agents', 
        'web_search_agent', 
        'instructions.md'
    )
    with open(instructions_path, 'r') as f:
        return f.read()

def create_websearch_agent(
    bedrock_agent_client: Any, 
    config: Dict[str, Any]
) -> Tuple[bool, str]:
    """Create the WebSearch Agent"""
    
    print("🔧 Creating WebSearch Agent...")
    
    try:
        instructions = load_agent_instructions()
        
        # Create agent
        response = bedrock_agent_client.create_agent(
            agentName='revops-websearch-agent',
            description='WebSearch Agent for RevOps AI Framework - External intelligence and company research',
            foundationModel='anthropic.claude-3-5-sonnet-20240620-v1:0',
            instruction=instructions,
            agentResourceRoleArn=config['execution_role_arn'],
            idleSessionTTLInSeconds=600,
            agentCollaboration='DISABLED'
        )
        
        agent_id = response['agent']['agentId']
        print(f"✅ WebSearch Agent created successfully!")
        print(f"   Agent ID: {agent_id}")
        
        return True, agent_id
        
    except Exception as e:
        print(f"❌ Error creating WebSearch Agent: {str(e)}")
        return False, ""

def create_web_search_action_group(
    bedrock_agent_client: Any,
    agent_id: str,
    web_search_lambda_arn: str
) -> Tuple[bool, str]:
    """Create web search action group for WebSearch Agent"""
    
    print("🔧 Creating web search action group...")
    
    # Action group schema
    function_schema = {
        "functions": [
            {
                "name": "search_web",
                "description": "Search the web using DuckDuckGo API to find information about companies, markets, or general topics",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "Search query - what to search for",
                        "required": True
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of search results to return (default: 5, max: 10)",
                        "required": False
                    },
                    "region": {
                        "type": "string",
                        "description": "Search region preference (default: us)",
                        "required": False
                    }
                },
                "requireConfirmation": "DISABLED"
            },
            {
                "name": "research_company",
                "description": "Research a specific company with focused queries about business, funding, technology, or recent news",
                "parameters": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to research",
                        "required": True
                    },
                    "focus_area": {
                        "type": "string",
                        "description": "Research focus area: general, funding, technology, size, or news (default: general)",
                        "required": False
                    }
                },
                "requireConfirmation": "DISABLED"
            }
        ]
    }
    
    try:
        response = bedrock_agent_client.create_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupName='web_search',
            description='Search the web for company research and lead intelligence',
            actionGroupExecutor={
                'lambda': web_search_lambda_arn
            },
            functionSchema=function_schema,
            actionGroupState='ENABLED'
        )
        
        action_group_id = response['agentActionGroup']['actionGroupId']
        print(f"✅ Web search action group created!")
        print(f"   Action Group ID: {action_group_id}")
        
        return True, action_group_id
        
    except Exception as e:
        print(f"❌ Error creating web search action group: {str(e)}")
        return False, ""

def prepare_agent(bedrock_agent_client: Any, agent_id: str) -> bool:
    """Prepare the WebSearch Agent"""
    
    print("🔄 Preparing WebSearch Agent...")
    
    try:
        bedrock_agent_client.prepare_agent(agentId=agent_id)
        
        # Wait for preparation to complete
        max_wait = 300  # 5 minutes
        wait_time = 0
        
        while wait_time < max_wait:
            agent_response = bedrock_agent_client.get_agent(agentId=agent_id)
            status = agent_response['agent']['agentStatus']
            
            if status == 'PREPARED':
                print(f"✅ WebSearch Agent prepared successfully!")
                return True
            elif status == 'FAILED':
                print(f"❌ WebSearch Agent preparation failed!")
                reasons = agent_response['agent'].get('failureReasons', [])
                for reason in reasons:
                    print(f"   Failure reason: {reason}")
                return False
            else:
                print(f"   Status: {status}, waiting...")
                time.sleep(10)
                wait_time += 10
        
        print(f"❌ WebSearch Agent preparation timed out!")
        return False
        
    except Exception as e:
        print(f"❌ Error preparing agent: {str(e)}")
        return False

def create_agent_alias(
    bedrock_agent_client: Any,
    agent_id: str
) -> Tuple[bool, str, str]:
    """Create alias for WebSearch Agent"""
    
    print("🔧 Creating WebSearch Agent alias...")
    
    try:
        response = bedrock_agent_client.create_agent_alias(
            agentId=agent_id,
            agentAliasName='revops-websearch-agent-alias',
            description='Alias for RevOps WebSearch Agent'
            # Default to DRAFT version
        )
        
        alias_id = response['agentAlias']['agentAliasId']
        alias_arn = response['agentAlias']['agentAliasArn']
        
        print(f"✅ WebSearch Agent alias created!")
        print(f"   Alias ID: {alias_id}")
        print(f"   Alias ARN: {alias_arn}")
        
        return True, alias_id, alias_arn
        
    except Exception as e:
        print(f"❌ Error creating agent alias: {str(e)}")
        return False, "", ""

def add_lambda_permissions(lambda_client: Any, agent_id: str) -> bool:
    """Add Lambda permissions for WebSearch Agent"""
    
    print("🔧 Adding Lambda permissions...")
    
    try:
        lambda_client.add_permission(
            FunctionName='revops-web-search',
            StatementId=f'WebSearchAgent-{agent_id}',
            Action='lambda:InvokeFunction',
            Principal='bedrock.amazonaws.com',
            SourceArn=f'arn:aws:bedrock:us-east-1:740202120544:agent/{agent_id}'
        )
        
        print(f"✅ Lambda permissions added!")
        return True
        
    except Exception as e:
        if 'ResourceConflictException' in str(e):
            print(f"✅ Lambda permissions already exist!")
            return True
        print(f"❌ Error adding Lambda permissions: {str(e)}")
        return False

def test_websearch_agent(
    bedrock_runtime_client: Any, 
    agent_id: str, 
    alias_id: str
) -> bool:
    """Test the WebSearch Agent"""
    
    print("🔧 Testing WebSearch Agent...")
    
    try:
        response = bedrock_runtime_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=alias_id,
            sessionId=f"deployment-test-{int(time.time())}",
            inputText="Hello, can you help me search for information?"
        )
        
        # Get first response chunk
        for event in response['completion']:
            if 'chunk' in event and 'bytes' in event['chunk']:
                chunk_text = event['chunk']['bytes'].decode('utf-8')
                print(f"✅ Agent responds: {chunk_text[:100]}...")
                return True
                
        return False
        
    except Exception as e:
        print(f"❌ Error testing WebSearch Agent: {str(e)}")
        return False

def update_config_file(
    agent_id: str, 
    alias_id: str, 
    action_group_id: str, 
    alias_arn: str
) -> bool:
    """Update config.json with WebSearch Agent details"""
    
    print("📋 Updating config.json...")
    
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Add WebSearch Agent to config
        config['web_search_agent'] = {
            "agent_id": agent_id,
            "agent_alias_id": alias_id,
            "foundation_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "description": "WebSearch Agent for RevOps AI Framework - External intelligence and company research",
            "instructions_file": "agents/web_search_agent/instructions.md",
            "action_groups": [
                {
                    "name": "web_search",
                    "description": "Search the web for company research and lead intelligence",
                    "lambda_arn": "arn:aws:lambda:us-east-1:740202120544:function:revops-web-search"
                }
            ]
        }
        
        # Update multi-agent setup
        if 'deployment_status' in config and 'multi_agent_setup' in config['deployment_status']:
            collaborators = config['deployment_status']['multi_agent_setup']['collaborator_agents']
            websearch_entry = f"{agent_id} (WebSearchAgent) - External intelligence and company research"
            if websearch_entry not in collaborators:
                collaborators.append(websearch_entry)
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Config updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {str(e)}")
        return False

def main():
    """Main deployment function"""
    print("🚀 RevOps AI Framework V2 - Complete WebSearch Agent Deployment")
    print("=" * 80)
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize AWS clients
        session = boto3.Session(
            profile_name=config['profile_name'],
            region_name=config['region_name']
        )
        
        bedrock_agent = session.client('bedrock-agent')
        bedrock_runtime = session.client('bedrock-agent-runtime')
        lambda_client = session.client('lambda')
        
        # Step 1: Create WebSearch Agent
        success, agent_id = create_websearch_agent(bedrock_agent, config)
        if not success:
            sys.exit(1)
        
        # Step 2: Create web search action group
        web_search_lambda_arn = config['lambda_functions']['web_search']['function_arn']
        success, action_group_id = create_web_search_action_group(
            bedrock_agent, 
            agent_id, 
            web_search_lambda_arn
        )
        if not success:
            sys.exit(1)
        
        # Step 3: Prepare agent
        if not prepare_agent(bedrock_agent, agent_id):
            sys.exit(1)
        
        # Step 4: Create agent alias
        success, alias_id, alias_arn = create_agent_alias(bedrock_agent, agent_id)
        if not success:
            sys.exit(1)
        
        # Step 5: Add Lambda permissions
        if not add_lambda_permissions(lambda_client, agent_id):
            print("⚠️ Lambda permissions failed but continuing...")
        
        # Step 6: Test agent
        if not test_websearch_agent(bedrock_runtime, agent_id, alias_id):
            print("⚠️ Agent test failed but deployment is complete")
        
        # Step 7: Update config file
        if not update_config_file(agent_id, alias_id, action_group_id, alias_arn):
            print("⚠️ Config update failed but deployment is complete")
        
        # Success summary
        print(f"\n🎉 WebSearch Agent Deployment Complete!")
        print("=" * 80)
        print(f"Agent ID: {agent_id}")
        print(f"Alias ID: {alias_id}")
        print(f"Action Group ID: {action_group_id}")
        print(f"Alias ARN: {alias_arn}")
        
        print(f"\n📋 Next Steps:")
        print(f"1. Verify agent functionality with test scripts")
        print(f"2. Add WebSearch Agent as collaborator to Decision Agent (manual)")
        print(f"3. Test multi-agent workflow")
        print(f"4. Update documentation")
        
    except Exception as e:
        print(f"\n💥 Deployment failed with error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()