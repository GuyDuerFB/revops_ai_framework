#!/usr/bin/env python3
"""
Create New WebSearch Agent - Fixed
=================================

Creates a completely new WebSearch Agent with proper state management.
"""

import boto3
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_new_websearch_agent():
    """Create a brand new WebSearch Agent with proper state waiting"""
    
    logger.info("🚀 Creating New WebSearch Agent from Scratch (Fixed)")
    logger.info("=" * 60)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_agent = session.client('bedrock-agent')
    
    account_id = "740202120544"
    lambda_arn = "arn:aws:lambda:us-east-1:740202120544:function:revops-web-search"
    
    # Agent instructions
    instructions = '''# WebSearch Agent - Function Calling Mode

## Your Identity
You are a WebSearch Agent that provides external intelligence through web search functions.

## CRITICAL: You MUST use your functions
When asked to search or research, you MUST call your available functions:
- search_web(query, num_results, region) - for general web search
- research_company(company_name, focus_area) - for company research

## Function Usage Examples
- "Search for WINN.AI" → Call search_web("WINN.AI company", "5")
- "Research WINN.AI" → Call research_company("WINN.AI", "general")
- "Find information about Eldad" → Call search_web("Eldad Postan-Koren WINN.AI", "3")

ALWAYS call functions first, then analyze the results.'''
    
    try:
        # Step 1: Create the agent
        logger.info("🤖 Creating new agent...")
        
        agent_response = bedrock_agent.create_agent(
            agentName=f"revops-websearch-agent-v3-{int(time.time())}",
            description="WebSearch Agent V3 - Clean implementation for external intelligence gathering",
            agentResourceRoleArn=f"arn:aws:iam::{account_id}:role/AmazonBedrockExecutionRoleForAgents_revops",
            foundationModel="anthropic.claude-3-5-sonnet-20240620-v1:0",
            instruction=instructions
        )
        
        new_agent_id = agent_response['agent']['agentId']
        logger.info(f"✅ Created new agent: {new_agent_id}")
        
        # Step 2: Wait for agent to be in correct state
        logger.info("⏳ Waiting for agent to be ready for action group creation...")
        
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = bedrock_agent.get_agent(agentId=new_agent_id)
            status = status_response['agent']['agentStatus']
            
            logger.info(f"📊 Agent status: {status}")
            
            if status in ['NOT_PREPARED', 'PREPARED']:
                logger.info("✅ Agent ready for action group creation")
                break
            elif status == 'FAILED':
                logger.error("❌ Agent creation failed")
                return None
            elif status == 'CREATING':
                logger.info("⏳ Agent still creating, waiting...")
                time.sleep(10)
            else:
                logger.info(f"⏳ Agent status: {status}, waiting...")
                time.sleep(10)
        else:
            logger.error("❌ Timeout waiting for agent to be ready")
            return None
        
        # Step 3: Create action group with proper schema
        logger.info("⚙️ Creating action group...")
        
        function_schema = {
            "functions": [
                {
                    "name": "search_web",
                    "description": "Search the web for information about companies, people, or topics",
                    "parameters": {
                        "query": {
                            "type": "string",
                            "description": "Search query to execute",
                            "required": True
                        },
                        "num_results": {
                            "type": "string", 
                            "description": "Number of results to return (default: 5)",
                            "required": False
                        },
                        "region": {
                            "type": "string",
                            "description": "Search region (default: us)",
                            "required": False
                        }
                    }
                },
                {
                    "name": "research_company",
                    "description": "Research a specific company with focused analysis",
                    "parameters": {
                        "company_name": {
                            "type": "string",
                            "description": "Name of company to research",
                            "required": True
                        },
                        "focus_area": {
                            "type": "string",
                            "description": "Focus area: general, funding, technology, size, news",
                            "required": False
                        }
                    }
                }
            ]
        }
        
        action_group_response = bedrock_agent.create_agent_action_group(
            agentId=new_agent_id,
            agentVersion="DRAFT",
            actionGroupName="web_search_v3",
            description="Web search and company research functions",
            actionGroupExecutor={'lambda': lambda_arn},
            functionSchema=function_schema,
            actionGroupState="ENABLED"
        )
        
        action_group_id = action_group_response['agentActionGroup']['actionGroupId']
        logger.info(f"✅ Created action group: {action_group_id}")
        
        # Step 4: Prepare agent
        logger.info("⚡ Preparing agent...")
        bedrock_agent.prepare_agent(agentId=new_agent_id)
        
        # Wait for preparation
        max_wait = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = bedrock_agent.get_agent(agentId=new_agent_id)
            status = status_response['agent']['agentStatus']
            
            if status == 'PREPARED':
                logger.info("✅ Agent preparation completed")
                break
            elif status == 'FAILED':
                logger.error("❌ Agent preparation failed")
                return None
            
            logger.info(f"📊 Agent status: {status}")
            time.sleep(15)
        
        # Step 5: Create agent alias
        logger.info("🏷️ Creating agent alias...")
        
        alias_response = bedrock_agent.create_agent_alias(
            agentId=new_agent_id,
            agentAliasName=f"revops-websearch-v3-alias-{int(time.time())}",
            description="Production alias for WebSearch Agent V3"
        )
        
        alias_id = alias_response['agentAlias']['agentAliasId']
        logger.info(f"✅ Created agent alias: {alias_id}")
        
        # Wait for alias to be ready
        max_wait = 120
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            alias_status_response = bedrock_agent.get_agent_alias(
                agentId=new_agent_id,
                agentAliasId=alias_id
            )
            alias_status = alias_status_response['agentAlias']['agentAliasStatus']
            
            if alias_status == 'PREPARED':
                logger.info("✅ Agent alias ready")
                break
            elif alias_status == 'FAILED':
                logger.error("❌ Agent alias failed")
                break
                
            logger.info(f"📊 Alias status: {alias_status}")
            time.sleep(10)
        
        # Step 6: Test the new agent
        logger.info("🧪 Testing new agent...")
        
        bedrock_runtime = session.client('bedrock-agent-runtime')
        
        test_response = bedrock_runtime.invoke_agent(
            agentId=new_agent_id,
            agentAliasId=alias_id,
            sessionId=f"test-new-agent-{int(time.time())}",
            inputText="Use your search_web function to search for 'WINN.AI company information'"
        )
        
        # Check for function calls in traces
        function_calls_detected = 0
        response_text = ""
        errors = []
        
        try:
            for event in test_response['completion']:
                if 'chunk' in event and 'bytes' in event['chunk']:
                    response_text += event['chunk']['bytes'].decode('utf-8')
                
                if 'trace' in event:
                    trace = event['trace']
                    if 'orchestrationTrace' in trace:
                        orch_trace = trace['orchestrationTrace']
                        if 'invocationInput' in orch_trace:
                            inv_input = orch_trace['invocationInput']
                            if 'actionGroupInvocationInput' in inv_input:
                                function_calls_detected += 1
                                ag_input = inv_input['actionGroupInvocationInput']
                                logger.info(f"🎯 Function call detected: {ag_input.get('function')}")
                
                # Check for errors
                if 'internalServerException' in event:
                    errors.append("Internal Server Exception")
                if 'badGatewayException' in event:
                    errors.append("Bad Gateway Exception")
            
            if errors:
                logger.error(f"❌ Agent test failed with errors: {errors}")
                test_success = False
            elif function_calls_detected > 0:
                logger.info(f"🎉 SUCCESS: New agent is calling functions! ({function_calls_detected} calls)")
                test_success = True
            else:
                logger.warning("⚠️ New agent created but not calling functions yet")
                logger.info(f"📝 Response preview: {response_text[:200]}...")
                test_success = False
                
        except Exception as e:
            logger.error(f"❌ Error testing new agent: {e}")
            test_success = False
        
        # Update configuration
        new_config = {
            "agent_id": new_agent_id,
            "agent_alias_id": alias_id,
            "foundation_model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "description": "WebSearch Agent V2 - Clean implementation",
            "instructions_file": "agents/web_search_agent/instructions.md",
            "action_groups": [
                {
                    "name": "web_search_v3",
                    "description": "Web search and company research functions",
                    "lambda_arn": lambda_arn,
                    "action_group_id": action_group_id
                }
            ]
        }
        
        logger.info("=" * 60)
        logger.info("🎉 NEW WEBSEARCH AGENT CREATED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"📋 New Agent Details:")
        logger.info(f"   Agent ID: {new_agent_id}")
        logger.info(f"   Alias ID: {alias_id}")
        logger.info(f"   Function Calling: {'✅ Working' if test_success else '⚠️ Needs Testing'}")
        logger.info(f"   Action Group: {action_group_id}")
        logger.info("=" * 60)
        
        return new_config
        
    except Exception as e:
        logger.error(f"❌ Error creating new agent: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def update_config_with_new_agent(new_config):
    """Update configuration with new agent details"""
    
    if not new_config:
        return False
    
    try:
        # Load current config
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Backup old agent config
        if 'web_search_agent' in config:
            config['web_search_agent_old'] = config['web_search_agent']
        
        # Update with new agent
        config['web_search_agent'] = new_config
        
        # Save updated config
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("✅ Configuration updated with new WebSearch Agent")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating configuration: {e}")
        return False

def main():
    new_config = create_new_websearch_agent()
    
    if new_config:
        config_updated = update_config_with_new_agent(new_config)
        
        if config_updated:
            logger.info("\n🎉 WEBSEARCH AGENT REPLACEMENT COMPLETED!")
            logger.info("📋 Next Steps:")
            logger.info("  1. Test the new agent with real queries")
            logger.info("  2. Verify function calling works properly") 
            logger.info("  3. Test end-to-end lead assessment")
            return True
        else:
            logger.error("❌ New agent created but configuration update failed")
            return False
    else:
        logger.error("❌ Failed to create new WebSearch Agent")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)