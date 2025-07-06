#!/usr/bin/env python3
"""
Test Agent with Traces Enabled
==============================

Test the WebSearch Agent with explicit trace enabling.
"""

import boto3
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_agent_with_traces():
    """Test agent with traces explicitly enabled"""
    
    logger.info("🔍 Testing Agent with Traces Enabled")
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
    
    logger.info(f"🤖 Agent ID: {agent_id}")
    logger.info(f"🏷️ Alias ID: {agent_alias_id}")
    
    try:
        session_id = f"trace-test-{int(time.time())}"
        
        # Test with traces explicitly enabled
        logger.info("📞 Invoking agent with traces enabled...")
        
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText="You have access to search functions. Use search_web function to search for 'WINN.AI company' with 3 results.",
            enableTrace=True  # Explicitly enable traces
        )
        
        logger.info("📡 Processing response stream...")
        
        full_response = ""
        function_calls = []
        all_events = []
        trace_count = 0
        
        for event in response['completion']:
            all_events.append(list(event.keys()))
            
            logger.info(f"📦 Event: {list(event.keys())}")
            
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    text = chunk['bytes'].decode('utf-8')
                    full_response += text
                    logger.info(f"📝 Text chunk: {text[:100]}...")
            
            if 'trace' in event:
                trace_count += 1
                trace = event['trace']
                logger.info(f"🔍 Trace {trace_count}: {list(trace.keys())}")
                
                if 'orchestrationTrace' in trace:
                    orch_trace = trace['orchestrationTrace']
                    logger.info(f"🎭 Orchestration keys: {list(orch_trace.keys())}")
                    
                    # Check for rationale
                    if 'rationale' in orch_trace:
                        rationale = orch_trace['rationale']
                        logger.info(f"🤔 Rationale: {rationale.get('text', '')[:150]}...")
                    
                    # Check for invocation input
                    if 'invocationInput' in orch_trace:
                        inv_input = orch_trace['invocationInput']
                        logger.info(f"📞 Invocation input: {list(inv_input.keys())}")
                        
                        if 'actionGroupInvocationInput' in inv_input:
                            ag_input = inv_input['actionGroupInvocationInput']
                            function_calls.append(ag_input)
                            logger.info(f"🎯 FUNCTION CALL FOUND!")
                            logger.info(f"   Action Group: {ag_input.get('actionGroupName')}")
                            logger.info(f"   Function: {ag_input.get('function')}")
                            logger.info(f"   Parameters: {ag_input.get('parameters')}")
                        
                        if 'knowledgeBaseLookupInput' in inv_input:
                            kb_input = inv_input['knowledgeBaseLookupInput']
                            logger.info(f"📚 Knowledge base lookup: {kb_input}")
                    
                    # Check for observation
                    if 'observation' in orch_trace:
                        observation = orch_trace['observation']
                        logger.info(f"👁️ Observation: {observation.get('text', '')[:150]}...")
                
                # Check for other trace types
                if 'preProcessingTrace' in trace:
                    logger.info("🔄 Pre-processing trace found")
                
                if 'postProcessingTrace' in trace:
                    logger.info("🔄 Post-processing trace found")
            
            # Check for errors
            if 'internalServerException' in event:
                logger.error(f"❌ Internal Server Exception: {event['internalServerException']}")
            
            if 'dependencyFailedException' in event:
                logger.error(f"❌ Dependency Failed Exception: {event['dependencyFailedException']}")
        
        logger.info(f"\n📊 Final Results:")
        logger.info(f"   Total events: {len(all_events)}")
        logger.info(f"   Trace events: {trace_count}")
        logger.info(f"   Function calls: {len(function_calls)}")
        logger.info(f"   Response length: {len(full_response)}")
        logger.info(f"   Event types seen: {set([item for sublist in all_events for item in sublist])}")
        
        logger.info(f"\n📝 Full Response:")
        logger.info(f"{full_response}")
        
        if function_calls:
            logger.info("\n🎉 SUCCESS: Function calls detected!")
            for i, fc in enumerate(function_calls):
                logger.info(f"   Call {i+1}: {fc}")
            return True
        else:
            logger.warning("\n⚠️ No function calls detected")
            if trace_count == 0:
                logger.error("❌ CRITICAL: No traces at all - this suggests a fundamental issue")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing agent: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    success = test_agent_with_traces()
    
    if success:
        logger.info("\n🎉 Agent is working correctly!")
    else:
        logger.error("\n❌ Agent has fundamental issues")
        logger.info("\nThis suggests the problem may be:")
        logger.info("  1. Agent not configured for function calling")
        logger.info("  2. Foundation model not supporting tool use")
        logger.info("  3. AWS Bedrock service issue")
        logger.info("  4. Incorrect agent alias or preparation")
    
    return success

if __name__ == "__main__":
    main()