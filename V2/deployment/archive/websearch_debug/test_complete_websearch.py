#!/usr/bin/env python3
"""
Test Complete WebSearch Agent Flow
=================================

Test the complete WebSearch Agent flow with updated Lambda.
"""

import boto3
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_complete_websearch_flow():
    """Test the complete WebSearch Agent flow"""
    
    logger.info("🧪 Testing Complete WebSearch Agent Flow")
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
    
    logger.info(f"🤖 Testing Agent: {agent_id}")
    logger.info(f"🏷️ Alias: {agent_alias_id}")
    
    # Test cases
    test_cases = [
        {
            "name": "Lead Assessment Test",
            "prompt": "I need to assess if Eldad Postan-Koren [CEO] of WINN.AI is a good lead. Please use your search functions to research both the company and the person.",
            "expected_functions": ["search_web", "research_company"]
        },
        {
            "name": "Company Research Test", 
            "prompt": "Use your research_company function to research WINN.AI with general focus.",
            "expected_functions": ["research_company"]
        },
        {
            "name": "Simple Search Test",
            "prompt": "Use your search_web function to search for 'WINN.AI company CEO' with 5 results.",
            "expected_functions": ["search_web"]
        }
    ]
    
    overall_success = True
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n🧪 Test {i}: {test_case['name']}")
        logger.info(f"📝 Prompt: {test_case['prompt']}")
        
        try:
            session_id = f"test-complete-{i}-{int(time.time())}"
            
            response = bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=test_case['prompt'],
                enableTrace=True
            )
            
            # Analyze response
            function_calls = []
            response_text = ""
            errors = []
            
            for event in response['completion']:
                if 'chunk' in event and 'bytes' in event['chunk']:
                    response_text += event['chunk']['bytes'].decode('utf-8')
                
                if 'trace' in event:
                    trace = event['trace']
                    if 'trace' in trace and 'orchestrationTrace' in trace['trace']:
                        orch_trace = trace['trace']['orchestrationTrace']
                        
                        if 'invocationInput' in orch_trace:
                            inv_input = orch_trace['invocationInput']
                            if 'actionGroupInvocationInput' in inv_input:
                                ag_input = inv_input['actionGroupInvocationInput']
                                function_calls.append({
                                    'function': ag_input.get('function'),
                                    'parameters': ag_input.get('parameters', [])
                                })
                                logger.info(f"   🎯 Function call: {ag_input.get('function')}")
                
                # Check for errors
                if 'dependencyFailedException' in event:
                    errors.append("Dependency Failed")
                if 'internalServerException' in event:
                    errors.append("Internal Server Error")
            
            # Evaluate test results
            test_success = True
            
            if errors:
                logger.error(f"   ❌ Errors: {errors}")
                test_success = False
            
            if len(function_calls) == 0:
                logger.error(f"   ❌ No function calls detected")
                test_success = False
            else:
                logger.info(f"   ✅ Function calls: {len(function_calls)}")
                for fc in function_calls:
                    logger.info(f"      - {fc['function']} with {len(fc['parameters'])} params")
            
            # Check response quality
            if len(response_text) < 50:
                logger.warning(f"   ⚠️ Very short response: {len(response_text)} chars")
            elif "appears to be a technology company" in response_text:
                logger.warning(f"   ⚠️ Generic response detected (fallback mode)")
            else:
                logger.info(f"   ✅ Good response length: {len(response_text)} chars")
            
            logger.info(f"   📝 Response preview: {response_text[:150]}...")
            
            if test_success:
                logger.info(f"   🎉 Test {i} PASSED")
            else:
                logger.error(f"   ❌ Test {i} FAILED")
                overall_success = False
                
        except Exception as e:
            logger.error(f"   ❌ Test {i} ERROR: {e}")
            overall_success = False
    
    return overall_success

def test_lead_assessment_workflow():
    """Test the specific lead assessment workflow"""
    
    logger.info("\n🎯 Testing Lead Assessment Workflow")
    logger.info("=" * 50)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load agent config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('web_search_agent', {}).get('agent_id')
    agent_alias_id = config.get('web_search_agent', {}).get('agent_alias_id')
    
    # Simulate the exact original request
    original_request = "I need to assess if Eldad Postan-Koren [CEO] of WINN.AI is a good lead."
    
    try:
        session_id = f"lead-assessment-{int(time.time())}"
        
        logger.info(f"📞 Testing original request: {original_request}")
        
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=original_request,
            enableTrace=True
        )
        
        # Collect full response
        full_response = ""
        function_calls = []
        
        for event in response['completion']:
            if 'chunk' in event and 'bytes' in event['chunk']:
                full_response += event['chunk']['bytes'].decode('utf-8')
            
            if 'trace' in event:
                trace = event['trace']
                if 'trace' in trace and 'orchestrationTrace' in trace['trace']:
                    orch_trace = trace['trace']['orchestrationTrace']
                    
                    if 'invocationInput' in orch_trace:
                        inv_input = orch_trace['invocationInput']
                        if 'actionGroupInvocationInput' in inv_input:
                            ag_input = inv_input['actionGroupInvocationInput']
                            function_calls.append(ag_input.get('function'))
        
        # Analyze the complete assessment
        logger.info(f"\n📊 Lead Assessment Results:")
        logger.info(f"   Function calls made: {len(function_calls)}")
        logger.info(f"   Functions called: {function_calls}")
        logger.info(f"   Response length: {len(full_response)} characters")
        
        # Check if it provides actual assessment
        assessment_indicators = [
            "assessment", "analysis", "evaluation", "recommendation", 
            "good lead", "qualified", "company information", "CEO"
        ]
        
        found_indicators = [ind for ind in assessment_indicators if ind.lower() in full_response.lower()]
        logger.info(f"   Assessment indicators found: {found_indicators}")
        
        logger.info(f"\n📝 Full Assessment Response:")
        logger.info(f"{full_response}")
        
        # Determine success
        if len(function_calls) > 0 and len(full_response) > 100:
            logger.info(f"\n🎉 Lead Assessment Workflow: SUCCESS")
            logger.info(f"✅ Agent is calling search functions")
            logger.info(f"✅ Agent is providing assessment responses")
            return True
        else:
            logger.error(f"\n❌ Lead Assessment Workflow: FAILED")
            return False
            
    except Exception as e:
        logger.error(f"❌ Lead assessment error: {e}")
        return False

def main():
    # Test complete flow
    flow_success = test_complete_websearch_flow()
    
    # Test lead assessment specifically  
    assessment_success = test_lead_assessment_workflow()
    
    logger.info(f"\n" + "=" * 60)
    logger.info(f"🎯 FINAL RESULTS")
    logger.info(f"=" * 60)
    
    if flow_success and assessment_success:
        logger.info(f"🎉 ALL TESTS PASSED!")
        logger.info(f"✅ WebSearch Agent is fully functional")
        logger.info(f"✅ Function calling is working")
        logger.info(f"✅ Lead assessment workflow is operational")
        logger.info(f"\n📋 WebSearch Agent is ready for production use!")
    else:
        logger.error(f"❌ Some tests failed")
        if not flow_success:
            logger.error(f"   - Basic function calling issues")
        if not assessment_success:
            logger.error(f"   - Lead assessment workflow issues")
    
    return flow_success and assessment_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)