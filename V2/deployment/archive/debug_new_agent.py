#!/usr/bin/env python3
"""
Debug New WebSearch Agent
========================

Deep debugging of the new WebSearch Agent to understand why it's not calling functions.
"""

import boto3
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def debug_new_agent():
    """Debug the new agent comprehensively"""
    
    logger.info("🔍 Deep Debug of New WebSearch Agent")
    logger.info("=" * 60)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_runtime = session.client('bedrock-agent-runtime')
    bedrock_agent = session.client('bedrock-agent')
    
    # Load agent config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('web_search_agent', {}).get('agent_id')
    agent_alias_id = config.get('web_search_agent', {}).get('agent_alias_id')
    
    logger.info(f"🤖 Agent ID: {agent_id}")
    logger.info(f"🏷️ Alias ID: {agent_alias_id}")
    
    try:
        # 1. Check agent configuration
        logger.info("\n🔧 Checking Agent Configuration...")
        
        agent_info = bedrock_agent.get_agent(agentId=agent_id)
        agent = agent_info['agent']
        
        logger.info(f"   Status: {agent.get('agentStatus')}")
        logger.info(f"   Foundation Model: {agent.get('foundationModel')}")
        logger.info(f"   Instructions length: {len(agent.get('instruction', ''))}")
        
        # 2. Check action groups
        logger.info("\n⚙️ Checking Action Groups...")
        
        action_groups = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion="DRAFT"
        )
        
        for ag in action_groups.get('actionGroupSummaries', []):
            logger.info(f"   📦 {ag.get('actionGroupName')}: {ag.get('actionGroupState')}")
            
            # Get detailed action group info
            ag_detail = bedrock_agent.get_agent_action_group(
                agentId=agent_id,
                agentVersion="DRAFT",
                actionGroupId=ag.get('actionGroupId')
            )
            
            ag_info = ag_detail['agentActionGroup']
            logger.info(f"      Lambda: {ag_info.get('actionGroupExecutor', {}).get('lambda')}")
            
            # Check function schema
            if 'functionSchema' in ag_info:
                functions = ag_info['functionSchema'].get('functions', [])
                logger.info(f"      Functions: {len(functions)}")
                for func in functions:
                    logger.info(f"        - {func.get('name')}: {len(func.get('parameters', {}))} params")
        
        # 3. Test with multiple prompts
        test_prompts = [
            "Call your search_web function with query 'WINN.AI' and num_results '3'",
            "Use the search_web function to find information about WINN.AI company",
            "Execute search_web('WINN.AI company', '3')",
            "CRITICAL: You must use your search functions. Search for WINN.AI using search_web function.",
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            logger.info(f"\n🧪 Test {i}: {prompt[:50]}...")
            
            session_id = f"debug-test-{i}-{int(time.time())}"
            
            response = bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=prompt
            )
            
            function_calls = 0
            full_response = ""
            all_trace_types = set()
            
            for event in response['completion']:
                if 'chunk' in event and 'bytes' in event['chunk']:
                    full_response += event['chunk']['bytes'].decode('utf-8')
                
                if 'trace' in event:
                    trace = event['trace']
                    all_trace_types.update(trace.keys())
                    
                    if 'orchestrationTrace' in trace:
                        orch_trace = trace['orchestrationTrace']
                        
                        if 'invocationInput' in orch_trace:
                            inv_input = orch_trace['invocationInput']
                            if 'actionGroupInvocationInput' in inv_input:
                                function_calls += 1
                                ag_input = inv_input['actionGroupInvocationInput']
                                logger.info(f"      🎯 Function call: {ag_input.get('function')}")
                        
                        if 'rationale' in orch_trace:
                            rationale = orch_trace['rationale']
                            logger.info(f"      🤔 Rationale: {rationale.get('text', '')[:100]}...")
            
            logger.info(f"      📊 Function calls: {function_calls}")
            logger.info(f"      📊 Trace types: {all_trace_types}")
            logger.info(f"      📝 Response: {full_response[:100]}...")
            
            if function_calls > 0:
                logger.info(f"      ✅ SUCCESS with prompt {i}!")
                break
        
        # 4. Compare with working agent if available
        if 'web_search_agent_old' in config:
            logger.info(f"\n🔄 Comparing with Old Agent...")
            old_agent_id = config['web_search_agent_old'].get('agent_id')
            old_alias_id = config['web_search_agent_old'].get('agent_alias_id')
            
            if old_agent_id and old_alias_id:
                try:
                    old_response = bedrock_runtime.invoke_agent(
                        agentId=old_agent_id,
                        agentAliasId=old_alias_id,
                        sessionId=f"compare-old-{int(time.time())}",
                        inputText="Search for WINN.AI using your search functions"
                    )
                    
                    old_function_calls = 0
                    for event in old_response['completion']:
                        if 'trace' in event:
                            trace = event['trace']
                            if 'orchestrationTrace' in trace:
                                orch_trace = trace['orchestrationTrace']
                                if 'invocationInput' in orch_trace:
                                    inv_input = orch_trace['invocationInput']
                                    if 'actionGroupInvocationInput' in inv_input:
                                        old_function_calls += 1
                    
                    logger.info(f"   📊 Old agent function calls: {old_function_calls}")
                    
                except Exception as e:
                    logger.info(f"   ❌ Old agent test failed: {e}")
        
        return function_calls > 0
        
    except Exception as e:
        logger.error(f"❌ Debug error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    success = debug_new_agent()
    
    if success:
        logger.info("\n🎉 New agent is working!")
    else:
        logger.error("\n❌ New agent still has issues")
        logger.info("\n💡 Next steps:")
        logger.info("   1. Check agent instructions format")
        logger.info("   2. Verify function schema compatibility")
        logger.info("   3. Test with different foundation models")
        logger.info("   4. Check for Bedrock service limitations")
    
    return success

if __name__ == "__main__":
    main()