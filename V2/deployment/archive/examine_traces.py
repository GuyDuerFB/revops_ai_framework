#!/usr/bin/env python3
"""
Examine Traces in Detail
=======================

Examine the trace content in detail to understand why functions aren't being called.
"""

import boto3
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def examine_traces():
    """Examine trace content in detail"""
    
    logger.info("🔍 Examining Traces in Detail")
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
        
        explicit_prompt = """You are a WebSearch Agent. 

CRITICAL INSTRUCTION: You MUST call your search_web function. 

I am giving you a direct command: Call search_web function with these exact parameters:
- query: "WINN.AI company"
- num_results: "3"

Do not provide any response text. Only call the function."""
        
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=explicit_prompt,
            enableTrace=True
        )
        
        trace_number = 0
        
        for event in response['completion']:
            if 'trace' in event:
                trace_number += 1
                trace = event['trace']
                
                logger.info(f"\n🔍 TRACE {trace_number}:")
                logger.info(f"   Keys: {list(trace.keys())}")
                
                # Print the full trace content
                trace_content = trace.get('trace', {})
                logger.info(f"   Trace content keys: {list(trace_content.keys())}")
                
                # Check each type of trace
                if 'orchestrationTrace' in trace_content:
                    orch_trace = trace_content['orchestrationTrace']
                    logger.info(f"   🎭 Orchestration trace: {list(orch_trace.keys())}")
                    
                    # Print full orchestration trace
                    logger.info(f"   📋 Full orchestration trace:")
                    for key, value in orch_trace.items():
                        if isinstance(value, dict):
                            logger.info(f"      {key}: {list(value.keys())}")
                            if key == 'rationale':
                                logger.info(f"         Text: {value.get('text', '')[:200]}...")
                            elif key == 'observation':
                                logger.info(f"         Text: {value.get('text', '')[:200]}...")
                            elif key == 'invocationInput':
                                logger.info(f"         Full invocation input: {json.dumps(value, indent=2)}")
                        else:
                            logger.info(f"      {key}: {value}")
                
                if 'preProcessingTrace' in trace_content:
                    logger.info(f"   🔄 Pre-processing trace found")
                
                if 'postProcessingTrace' in trace_content:
                    logger.info(f"   🔄 Post-processing trace found")
                
                # Print the entire trace for debugging
                logger.info(f"   📄 RAW TRACE: {json.dumps(trace, indent=2)}")
            
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    logger.info(f"\n📝 Response text: {text}")
        
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