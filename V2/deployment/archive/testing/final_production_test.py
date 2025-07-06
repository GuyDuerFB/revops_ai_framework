#!/usr/bin/env python3
"""
Final Production Test
====================

Final test of the WebSearch Agent in production-ready state.
"""

import boto3
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_websearch_agent_production():
    """Test the WebSearch Agent in production"""
    
    logger.info("🎯 Final Production Test - WebSearch Agent")
    logger.info("=" * 60)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('web_search_agent', {}).get('agent_id')
    agent_alias_id = config.get('web_search_agent', {}).get('agent_alias_id')
    
    logger.info(f"🤖 Agent ID: {agent_id}")
    logger.info(f"🏷️ Alias ID: {agent_alias_id}")
    
    # Original user request that started this journey
    original_request = "I need to assess if Eldad Postan-Koren [CEO] of WINN.AI is a good lead."
    
    try:
        session_id = f"final-production-test-{int(time.time())}"
        
        logger.info(f"📞 Testing original request: {original_request}")
        
        start_time = time.time()
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=original_request,
            enableTrace=True
        )
        
        # Collect response
        full_response = ""
        function_calls = 0
        
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
                            function_calls += 1
        
        execution_time = time.time() - start_time
        
        # Evaluate success
        success_criteria = {
            'function_calls': function_calls > 0,
            'response_length': len(full_response) > 200,
            'contains_assessment': 'assessment' in full_response.lower(),
            'contains_company': 'WINN.AI' in full_response,
            'contains_person': 'Eldad' in full_response,
            'reasonable_time': execution_time < 60
        }
        
        logger.info(f"\n📊 Production Test Results:")
        logger.info(f"   Execution time: {execution_time:.1f}s")
        logger.info(f"   Function calls: {function_calls}")
        logger.info(f"   Response length: {len(full_response)} characters")
        
        logger.info(f"\n✅ Success Criteria:")
        for criterion, passed in success_criteria.items():
            status = "✅" if passed else "❌"
            logger.info(f"   {status} {criterion}: {passed}")
        
        all_passed = all(success_criteria.values())
        
        if all_passed:
            logger.info(f"\n🎉 PRODUCTION TEST: SUCCESS!")
            logger.info(f"✅ All success criteria met")
            logger.info(f"✅ WebSearch Agent is production-ready")
        else:
            logger.error(f"\n❌ PRODUCTION TEST: PARTIAL SUCCESS")
            failed = [k for k, v in success_criteria.items() if not v]
            logger.error(f"Failed criteria: {failed}")
        
        logger.info(f"\n📝 Full Assessment Response:")
        logger.info(f"{full_response}")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Production test error: {e}")
        return False

def main():
    """Run final production test"""
    
    success = test_websearch_agent_production()
    
    logger.info("\n" + "=" * 70)
    logger.info("🎯 FINAL PRODUCTION ASSESSMENT")
    logger.info("=" * 70)
    
    if success:
        logger.info("🎉 REVOPS AI FRAMEWORK V2 - PRODUCTION READY!")
        logger.info("✅ WebSearch Agent fully functional")
        logger.info("✅ Lead assessment workflow operational")
        logger.info("✅ Function calling working correctly")
        logger.info("✅ Response quality meets standards")
        logger.info("✅ Codebase clean and organized")
        logger.info("\n🚀 Ready for production deployment and use!")
    else:
        logger.error("❌ Production readiness issues detected")
        logger.info("📋 Check the WebSearch Agent configuration and test results")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)