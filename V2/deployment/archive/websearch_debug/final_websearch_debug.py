#!/usr/bin/env python3
"""
Final WebSearch Debug
====================

Last attempt to debug why WebSearch Agent won't call functions.
"""

import boto3
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def final_websearch_debug():
    """Final debug attempt"""
    
    logger.info("🔍 Final WebSearch Debug - Function Calling Issue")
    logger.info("=" * 60)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_runtime = session.client('bedrock-agent-runtime')
    bedrock_agent = session.client('bedrock-agent')
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('web_search_agent', {}).get('agent_id')
    agent_alias_id = config.get('web_search_agent', {}).get('agent_alias_id')
    
    # Try extremely explicit function calling request
    explicit_request = """
You are a WebSearch Agent. You have access to two functions:
1. search_web(query, num_results, region)
2. research_company(company_name, focus_area)

I am now instructing you to call your search_web function with the following parameters:
- query: "WINN.AI company"
- num_results: "3"

Please call this function NOW. Do not respond with any text until you have called the function.
"""
    
    logger.info("🧪 Testing with EXTREMELY explicit function calling request...")
    logger.info(f"📝 Request: {explicit_request}")
    
    try:
        session_id = f"final-debug-{int(time.time())}"
        
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=explicit_request
        )
        
        # Collect ALL trace information
        full_response = ""
        all_traces = []
        function_calls = []
        errors = []
        
        for event in response['completion']:
            logger.info(f"📡 Event type: {list(event.keys())}")
            
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    full_response += text
                    logger.info(f"📝 Chunk text: {text[:100]}...")
            
            if 'trace' in event:
                trace = event['trace']
                all_traces.append(trace)
                logger.info(f"🔍 Trace keys: {list(trace.keys())}")
                
                # Check for orchestration traces
                if 'orchestrationTrace' in trace:
                    orch_trace = trace['orchestrationTrace']
                    logger.info(f"🎭 Orchestration trace keys: {list(orch_trace.keys())}")
                    
                    # Look for invocation input
                    if 'invocationInput' in orch_trace:
                        inv_input = orch_trace['invocationInput']
                        logger.info(f"📞 Invocation input keys: {list(inv_input.keys())}")
                        
                        if 'actionGroupInvocationInput' in inv_input:
                            ag_input = inv_input['actionGroupInvocationInput']
                            function_calls.append(ag_input)
                            logger.info(f"🎯 FUNCTION CALL DETECTED!")
                            logger.info(f"   Action Group: {ag_input.get('actionGroupName')}")
                            logger.info(f"   Function: {ag_input.get('function')}")
                            logger.info(f"   Parameters: {ag_input.get('parameters')}")
                        
                        # Check for knowledge base invocation
                        if 'knowledgeBaseLookupInput' in inv_input:
                            kb_input = inv_input['knowledgeBaseLookupInput']
                            logger.info(f"📚 Knowledge base lookup: {kb_input.get('text')}")
                    
                    # Look for rationale
                    if 'rationale' in orch_trace:
                        rationale = orch_trace['rationale']
                        logger.info(f"🤔 Agent rationale: {rationale.get('text', '')[:200]}...")
                    
                    # Look for observation
                    if 'observation' in orch_trace:
                        observation = orch_trace['observation']
                        logger.info(f"👁️ Agent observation: {observation.get('text', '')[:200]}...")
            
            if 'internalServerException' in event or 'badGatewayException' in event:
                errors.append(event)
                logger.error(f"❌ Error event: {event}")
        
        logger.info(f"\n📊 FINAL ANALYSIS:")
        logger.info(f"   Function calls detected: {len(function_calls)}")
        logger.info(f"   Total traces: {len(all_traces)}")
        logger.info(f"   Errors: {len(errors)}")
        logger.info(f"   Response length: {len(full_response)}")
        
        if function_calls:
            logger.info("🎉 SUCCESS: Agent IS calling functions!")
            for i, fc in enumerate(function_calls):
                logger.info(f"   Call {i+1}: {fc.get('function')} with {len(fc.get('parameters', []))} params")
        else:
            logger.error("❌ CRITICAL: Agent is NOT calling functions despite explicit request")
            logger.info("🔍 Possible causes:")
            logger.info("   1. Function schema format issue")
            logger.info("   2. Agent instructions preventing function calls")
            logger.info("   3. Action group not properly enabled")
            logger.info("   4. Permission issue with Lambda invocation")
            logger.info("   5. Bedrock Agent service issue")
        
        logger.info(f"\n📝 Final Response Preview:")
        logger.info(f"   {full_response[:300]}...")
        
        # Check agent status one more time
        logger.info(f"\n⚙️ Agent Status Check:")
        try:
            agent_info = bedrock_agent.get_agent(agentId=agent_id)
            agent = agent_info['agent']
            logger.info(f"   Status: {agent.get('agentStatus')}")
            logger.info(f"   Foundation Model: {agent.get('foundationModel')}")
            
            # Check action groups
            action_groups = bedrock_agent.list_agent_action_groups(
                agentId=agent_id,
                agentVersion="DRAFT"
            )
            
            logger.info(f"   Action Groups: {len(action_groups.get('actionGroupSummaries', []))}")
            for ag in action_groups.get('actionGroupSummaries', []):
                logger.info(f"     - {ag.get('actionGroupName')}: {ag.get('actionGroupState')}")
                
        except Exception as e:
            logger.error(f"❌ Error checking agent status: {e}")
        
        return len(function_calls) > 0
        
    except Exception as e:
        logger.error(f"❌ Critical error in final debug: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    success = final_websearch_debug()
    
    if success:
        logger.info("\n🎉 BREAKTHROUGH: Function calling is working!")
    else:
        logger.error("\n🚨 CRITICAL ISSUE: Function calling fundamentally broken")
        logger.info("\n💡 Recommended next steps:")
        logger.info("   1. Create entirely new WebSearch Agent from scratch")
        logger.info("   2. Check AWS Bedrock Agent service status")
        logger.info("   3. Contact AWS support for Bedrock Agent issues")
        logger.info("   4. Use alternative search implementation")
    
    return success

if __name__ == "__main__":
    main()