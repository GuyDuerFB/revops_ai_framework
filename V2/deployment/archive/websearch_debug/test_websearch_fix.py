#!/usr/bin/env python3
"""
Test WebSearch Agent Fix
========================

Validates that the WebSearch Agent fix is working by testing function calling.
"""

import boto3
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_websearch_agent_fix():
    """Test WebSearch Agent function calling after fix"""
    
    logger.info("🧪 Testing WebSearch Agent Fix")
    logger.info("=" * 50)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    websearch_config = config.get('web_search_agent', {})
    agent_id = websearch_config.get('agent_id')
    agent_alias_id = websearch_config.get('agent_alias_id')
    
    if not agent_id or not agent_alias_id:
        logger.error("❌ Agent configuration not found")
        return False
    
    # Test cases designed to force function calling
    test_cases = [
        {
            "name": "Direct Function Call Test",
            "query": "Call your search_web function right now to search for 'WINN.AI company'",
            "expected_function": "search_web"
        },
        {
            "name": "Company Research Test",
            "query": "Use research_company function to research WINN.AI with general focus",
            "expected_function": "research_company"
        },
        {
            "name": "Lead Assessment Test",
            "query": "Research Eldad Postan-Koren from WINN.AI. You must use your search functions to find real information.",
            "expected_function": "search_web"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        logger.info(f"🧪 Test {i}/3: {test['name']}")
        logger.info(f"📝 Query: {test['query']}")
        
        try:
            session_id = f"fix-test-{int(time.time())}-{i}"
            
            response = bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=test['query']
            )
            
            # Collect response and trace information
            full_response = ""
            function_calls = []
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        full_response += chunk['bytes'].decode('utf-8')
                
                # Check for function call traces
                if 'trace' in event:
                    trace = event['trace']
                    if 'orchestrationTrace' in trace:
                        orch_trace = trace['orchestrationTrace']
                        if 'invocationInput' in orch_trace:
                            inv_input = orch_trace['invocationInput']
                            if 'actionGroupInvocationInput' in inv_input:
                                ag_input = inv_input['actionGroupInvocationInput']
                                function_calls.append({
                                    "action_group": ag_input.get('actionGroupName'),
                                    "function": ag_input.get('function'),
                                    "parameters": ag_input.get('parameters', [])
                                })
            
            # Analyze results
            function_called = len(function_calls) > 0
            expected_function_called = any(
                fc.get('function') == test['expected_function'] 
                for fc in function_calls
            )
            
            # Check if response mentions actual search results vs hallucination
            authentic_results = any(term in full_response.lower() for term in [
                'search performed', 'search results', 'found information', 'based on search'
            ]) and not any(term in full_response.lower() for term in [
                'i searched for', 'search would find', 'search could reveal'
            ])
            
            result = {
                "test_name": test['name'],
                "function_called": function_called,
                "expected_function_called": expected_function_called,
                "function_calls_count": len(function_calls),
                "function_calls": function_calls,
                "authentic_results": authentic_results,
                "response_length": len(full_response),
                "response_preview": full_response[:400] + "..." if len(full_response) > 400 else full_response
            }
            
            results.append(result)
            
            # Status reporting
            if function_called and expected_function_called:
                status = "✅ SUCCESS"
            elif function_called:
                status = "⚠️ PARTIAL"
            else:
                status = "❌ FAILED"
            
            logger.info(f"  {status} - Functions called: {len(function_calls)}")
            if function_calls:
                for fc in function_calls:
                    logger.info(f"    📞 Called: {fc.get('function')} with {len(fc.get('parameters', []))} params")
            
            logger.info("-" * 30)
            
        except Exception as e:
            logger.error(f"  ❌ ERROR: {e}")
            results.append({
                "test_name": test['name'],
                "error": str(e),
                "function_called": False
            })
    
    # Overall assessment
    successful_tests = sum(1 for r in results if r.get('function_called', False))
    total_tests = len(results)
    success_rate = successful_tests / total_tests
    
    logger.info("=" * 50)
    logger.info(f"🎯 FUNCTION CALLING SUCCESS RATE: {successful_tests}/{total_tests} ({success_rate:.0%})")
    
    if success_rate >= 0.8:
        logger.info("🎉 EXCELLENT: WebSearch Agent is now calling functions correctly!")
        overall_status = "EXCELLENT"
    elif success_rate >= 0.5:
        logger.info("✅ GOOD: WebSearch Agent is calling functions (needs minor tuning)")
        overall_status = "GOOD"
    else:
        logger.error("❌ POOR: WebSearch Agent still not calling functions properly")
        overall_status = "POOR"
    
    # Save test report
    report = f"""# WebSearch Agent Fix Test Report

## 🎯 Overall Result: {overall_status}
**Function Calling Success Rate**: {successful_tests}/{total_tests} ({success_rate:.0%})

## Test Results:

"""
    
    for result in results:
        status = "✅ PASS" if result.get('function_called', False) else "❌ FAIL"
        report += f"""
### {result.get('test_name')} - {status}
- **Function Called**: {result.get('function_called', False)}
- **Expected Function Called**: {result.get('expected_function_called', False)}
- **Function Calls Count**: {result.get('function_calls_count', 0)}
- **Function Calls**: {result.get('function_calls', [])}
- **Response Preview**: {result.get('response_preview', result.get('error', 'No response'))[:300]}

"""
    
    if success_rate >= 0.8:
        report += "\n## 🎉 Conclusion: WebSearch Agent is working correctly!\n"
        report += "The function calling issue has been resolved. The agent now properly calls search functions instead of hallucinating results.\n"
    elif success_rate >= 0.5:
        report += "\n## ✅ Conclusion: Significant improvement achieved\n"
        report += "The agent is now calling functions, but may need minor instruction refinements.\n"
    else:
        report += "\n## ❌ Conclusion: Additional fixes needed\n"
        report += "The agent is still not calling functions consistently. Consider additional troubleshooting.\n"
    
    with open('websearch_fix_test_report.md', 'w') as f:
        f.write(report)
    
    logger.info("📄 Test report saved: websearch_fix_test_report.md")
    
    return success_rate >= 0.5

def main():
    success = test_websearch_agent_fix()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)