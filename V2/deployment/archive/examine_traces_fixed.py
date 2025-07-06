#!/usr/bin/env python3
"""
Examine Traces in Detail - Fixed
===============================

Examine the trace content in detail to understand why functions aren't being called.
"""

import boto3
import json
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def safe_json_serialize(obj):
    """Safely serialize objects to JSON, handling datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: safe_json_serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [safe_json_serialize(item) for item in obj]
    else:
        return obj

def examine_traces():
    """Examine trace content in detail"""
    
    logger.info("🔍 Examining Traces in Detail (Fixed)")
    logger.info("=" * 60)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load agent config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('web_search_agent', {}).get('agent_id')
    agent_alias_id = config.get('web_search_agent', {}).get('agent_alias_id')
    
    try:
        session_id = f"examine-traces-{int(time.time())}"
        
        logger.info("📞 Invoking agent with very explicit function request...")
        
        explicit_prompt = """You are a WebSearch Agent with access to these functions:
- search_web(query, num_results, region)
- research_company(company_name, focus_area)

CRITICAL: You MUST call the search_web function now.

Parameters to use:
- query: "WINN.AI company"  
- num_results: "3"

Call this function immediately. Do not respond with text until you call the function."""
        
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=explicit_prompt,
            enableTrace=True
        )
        
        trace_number = 0
        response_chunks = []
        
        for event in response['completion']:
            if 'trace' in event:
                trace_number += 1
                trace = event['trace']
                
                logger.info(f"\n🔍 TRACE {trace_number}:")
                
                # Get the trace content
                trace_content = trace.get('trace', {})
                
                if 'orchestrationTrace' in trace_content:
                    orch_trace = trace_content['orchestrationTrace']
                    logger.info(f"   🎭 Orchestration trace type: {orch_trace.get('type', 'unknown')}")
                    
                    # Check for model invocation input
                    if 'modelInvocationInput' in orch_trace:
                        model_input = orch_trace['modelInvocationInput']
                        logger.info(f"   📤 Model invocation input:")
                        logger.info(f"      Foundation Model: {model_input.get('foundationModel')}")
                        logger.info(f"      Text length: {len(model_input.get('text', ''))}")
                        logger.info(f"      Text preview: {model_input.get('text', '')[:300]}...")
                    
                    # Check for model invocation output
                    if 'modelInvocationOutput' in orch_trace:
                        model_output = orch_trace['modelInvocationOutput']
                        logger.info(f"   📥 Model invocation output:")
                        if 'rawResponse' in model_output:
                            raw_response = model_output['rawResponse']
                            logger.info(f"      Content: {raw_response.get('content', '')[:300]}...")
                    
                    # Check for rationale
                    if 'rationale' in orch_trace:
                        rationale = orch_trace['rationale']
                        logger.info(f"   🤔 Agent rationale: {rationale.get('text', '')[:300]}...")
                    
                    # Check for invocation input (this is where function calls would appear)
                    if 'invocationInput' in orch_trace:
                        inv_input = orch_trace['invocationInput']
                        logger.info(f"   📞 INVOCATION INPUT FOUND: {list(inv_input.keys())}")
                        
                        if 'actionGroupInvocationInput' in inv_input:
                            ag_input = inv_input['actionGroupInvocationInput']
                            logger.info(f"   🎯 FUNCTION CALL DETECTED!")
                            logger.info(f"      Action Group: {ag_input.get('actionGroupName')}")
                            logger.info(f"      Function: {ag_input.get('function')}")
                            logger.info(f"      Parameters: {ag_input.get('parameters')}")
                        
                        if 'knowledgeBaseLookupInput' in inv_input:
                            kb_input = inv_input['knowledgeBaseLookupInput']
                            logger.info(f"   📚 Knowledge base lookup: {kb_input.get('text')}")
                    
                    # Check for observation (function call results)
                    if 'observation' in orch_trace:
                        observation = orch_trace['observation']
                        logger.info(f"   👁️ Agent observation: {observation.get('text', '')[:300]}...")
            
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    response_chunks.append(text)
                    logger.info(f"📝 Response chunk: {text[:100]}...")
        
        full_response = ''.join(response_chunks)
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"   Total traces: {trace_number}")
        logger.info(f"   Response length: {len(full_response)}")
        logger.info(f"   Full response: {full_response}")
        
        # Check if the response indicates the agent is pretending vs actually calling functions
        if "based on the search results" in full_response.lower() or "search results for" in full_response.lower():
            logger.warning("⚠️ Agent appears to be PRETENDING it searched without actually calling functions!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error examining traces: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    examine_traces()

if __name__ == "__main__":
    main()