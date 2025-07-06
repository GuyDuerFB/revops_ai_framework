#!/usr/bin/env python3
"""
WebSearch Agent Comprehensive Diagnostic
=======================================

Diagnoses WebSearch Agent functionality at multiple levels:
1. Lambda function direct testing
2. Agent action group configuration
3. Agent instruction following
4. End-to-end function calling
"""

import boto3
import json
import logging
import time
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class WebSearchDiagnostic:
    """Comprehensive WebSearch Agent diagnostic tool"""
    
    def __init__(self, profile_name: str = "revops-dev-profile"):
        session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
        self.lambda_client = session.client('lambda')
        self.bedrock_agent = session.client('bedrock-agent')
        self.bedrock_runtime = session.client('bedrock-agent-runtime')
        
        # Load configuration
        with open('config.json', 'r') as f:
            self.config = json.load(f)
        
        self.websearch_config = self.config.get('web_search_agent', {})
        self.agent_id = self.websearch_config.get('agent_id')
        self.agent_alias_id = self.websearch_config.get('agent_alias_id')
        self.lambda_arn = None
        
        # Get Lambda ARN from action groups
        for action_group in self.websearch_config.get('action_groups', []):
            if action_group.get('name') == 'web_search':
                self.lambda_arn = action_group.get('lambda_arn')
                break
    
    def test_lambda_function_direct(self) -> Dict[str, Any]:
        """Test Lambda function directly with different payload formats"""
        
        logger.info("🧪 Testing Lambda function directly...")
        
        if not self.lambda_arn:
            return {"error": "Lambda ARN not found in configuration"}
        
        # Extract function name from ARN
        function_name = self.lambda_arn.split(':')[-1]
        
        test_payloads = [
            {
                "name": "Direct Query Test",
                "payload": {
                    "query": "WINN.AI company information",
                    "num_results": 3
                }
            },
            {
                "name": "Direct Company Research Test", 
                "payload": {
                    "company_name": "WINN.AI",
                    "focus_area": "general"
                }
            },
            {
                "name": "Bedrock Agent Format Test (New)",
                "payload": {
                    "function": "search_web",
                    "actionGroup": "web_search",
                    "parameters": [
                        {"name": "query", "value": "WINN.AI company"},
                        {"name": "num_results", "value": "3"}
                    ]
                }
            },
            {
                "name": "Bedrock Agent Format Test (Old)",
                "payload": {
                    "actionGroup": "web_search",
                    "action": "search_web",
                    "body": {
                        "parameters": {
                            "query": "WINN.AI company",
                            "num_results": 3
                        }
                    }
                }
            }
        ]
        
        results = []
        
        for test in test_payloads:
            logger.info(f"  🔍 Testing: {test['name']}")
            
            try:
                response = self.lambda_client.invoke(
                    FunctionName=function_name,
                    Payload=json.dumps(test['payload'])
                )
                
                result_payload = json.loads(response['Payload'].read().decode())
                
                success = (
                    response['StatusCode'] == 200 and
                    (result_payload.get('success', False) or 'results' in result_payload)
                )
                
                results.append({
                    "test_name": test['name'],
                    "success": success,
                    "status_code": response['StatusCode'],
                    "payload_preview": str(result_payload)[:200] + "..." if len(str(result_payload)) > 200 else str(result_payload)
                })
                
                status = "✅ SUCCESS" if success else "❌ FAILED"
                logger.info(f"    {status} - Status: {response['StatusCode']}")
                
            except Exception as e:
                logger.error(f"    ❌ ERROR: {e}")
                results.append({
                    "test_name": test['name'],
                    "success": False,
                    "error": str(e)
                })
        
        return {"lambda_tests": results}
    
    def test_agent_configuration(self) -> Dict[str, Any]:
        """Test agent configuration and action group setup"""
        
        logger.info("🧪 Testing Agent configuration...")
        
        if not self.agent_id:
            return {"error": "Agent ID not found in configuration"}
        
        try:
            # Get agent details
            agent_response = self.bedrock_agent.get_agent(agentId=self.agent_id)
            agent = agent_response['agent']
            
            # Get action groups
            action_groups = self.bedrock_agent.list_agent_action_groups(
                agentId=self.agent_id,
                agentVersion="DRAFT"
            )
            
            # Get agent alias details
            agent_alias = None
            if self.agent_alias_id:
                try:
                    alias_response = self.bedrock_agent.get_agent_alias(
                        agentId=self.agent_id,
                        agentAliasId=self.agent_alias_id
                    )
                    agent_alias = alias_response['agentAlias']
                except Exception as e:
                    logger.warning(f"Could not get agent alias: {e}")
            
            config_analysis = {
                "agent_status": agent.get('agentStatus'),
                "foundation_model": agent.get('foundationModel'),
                "agent_name": agent.get('agentName'),
                "action_groups_count": len(action_groups.get('actionGroupSummaries', [])),
                "action_groups": [],
                "agent_alias_status": agent_alias.get('agentAliasStatus') if agent_alias else "Not found"
            }
            
            # Analyze action groups
            for ag in action_groups.get('actionGroupSummaries', []):
                ag_detail = self.bedrock_agent.get_agent_action_group(
                    agentId=self.agent_id,
                    agentVersion="DRAFT",
                    actionGroupId=ag['actionGroupId']
                )
                
                ag_info = ag_detail['agentActionGroup']
                config_analysis["action_groups"].append({
                    "name": ag_info.get('actionGroupName'),
                    "state": ag_info.get('actionGroupState'),
                    "lambda_arn": ag_info.get('actionGroupExecutor', {}).get('lambda'),
                    "function_schema": bool(ag_info.get('functionSchema'))
                })
            
            return {"agent_config": config_analysis}
            
        except Exception as e:
            logger.error(f"Error checking agent configuration: {e}")
            return {"error": str(e)}
    
    def test_agent_function_calling(self) -> Dict[str, Any]:
        """Test agent's ability to call functions"""
        
        logger.info("🧪 Testing Agent function calling...")
        
        if not self.agent_id or not self.agent_alias_id:
            return {"error": "Agent ID or Alias ID not found"}
        
        test_queries = [
            {
                "name": "Simple Search Request",
                "query": "Search for information about WINN.AI company",
                "expected_function": "search_web"
            },
            {
                "name": "Explicit Function Request",
                "query": "Use your search_web function to find information about WINN.AI",
                "expected_function": "search_web"
            },
            {
                "name": "Company Research Request",
                "query": "Use research_company function to research WINN.AI",
                "expected_function": "research_company"
            },
            {
                "name": "Direct Instruction",
                "query": "Call search_web('WINN.AI company', 3) now",
                "expected_function": "search_web"
            }
        ]
        
        results = []
        
        for test in test_queries:
            logger.info(f"  🔍 Testing: {test['name']}")
            
            try:
                session_id = f"websearch-test-{int(time.time())}"
                
                response = self.bedrock_runtime.invoke_agent(
                    agentId=self.agent_id,
                    agentAliasId=self.agent_alias_id,
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
                
                has_search_results = any(term in full_response.lower() for term in [
                    'search results', 'found', 'company', 'website', 'information'
                ])
                
                result = {
                    "test_name": test['name'],
                    "function_called": function_called,
                    "expected_function_called": expected_function_called,
                    "function_calls": function_calls,
                    "has_search_results": has_search_results,
                    "response_length": len(full_response),
                    "response_preview": full_response[:300] + "..." if len(full_response) > 300 else full_response
                }
                
                results.append(result)
                
                status = "✅ SUCCESS" if function_called and expected_function_called else "❌ FAILED"
                logger.info(f"    {status} - Functions called: {len(function_calls)}")
                
            except Exception as e:
                logger.error(f"    ❌ ERROR: {e}")
                results.append({
                    "test_name": test['name'],
                    "error": str(e),
                    "function_called": False
                })
        
        return {"function_calling_tests": results}
    
    def generate_diagnostic_report(self) -> None:
        """Generate comprehensive diagnostic report"""
        
        logger.info("📋 Generating WebSearch Agent Diagnostic Report...")
        
        # Run all tests
        lambda_results = self.test_lambda_function_direct()
        agent_config = self.test_agent_configuration()
        function_calling = self.test_agent_function_calling()
        
        # Analyze overall health
        lambda_working = any(t.get('success', False) for t in lambda_results.get('lambda_tests', []))
        agent_configured = agent_config.get('agent_config', {}).get('agent_status') == 'PREPARED'
        functions_working = any(t.get('function_called', False) for t in function_calling.get('function_calling_tests', []))
        
        overall_score = sum([lambda_working, agent_configured, functions_working]) / 3
        
        # Generate report
        report = f"""# WebSearch Agent Diagnostic Report

## 🎯 Overall Health Score: {overall_score:.2f}/1.00

### Health Summary:
- **Lambda Function**: {'✅ Working' if lambda_working else '❌ Issues'}
- **Agent Configuration**: {'✅ Configured' if agent_configured else '❌ Issues'}
- **Function Calling**: {'✅ Working' if functions_working else '❌ Issues'}

## 🔧 Lambda Function Tests

"""
        
        for test in lambda_results.get('lambda_tests', []):
            status = "✅ PASS" if test.get('success', False) else "❌ FAIL"
            report += f"""
### {test.get('test_name')} - {status}
- **Success**: {test.get('success', False)}
- **Status Code**: {test.get('status_code', 'N/A')}
- **Result Preview**: {test.get('payload_preview', test.get('error', 'N/A'))}
"""
        
        report += f"""
## ⚙️ Agent Configuration Analysis

"""
        
        config = agent_config.get('agent_config', {})
        report += f"""
- **Agent Status**: {config.get('agent_status', 'Unknown')}
- **Foundation Model**: {config.get('foundation_model', 'Unknown')}
- **Agent Name**: {config.get('agent_name', 'Unknown')}
- **Action Groups Count**: {config.get('action_groups_count', 0)}
- **Agent Alias Status**: {config.get('agent_alias_status', 'Unknown')}

### Action Groups:
"""
        
        for ag in config.get('action_groups', []):
            report += f"""
- **{ag.get('name')}**: State={ag.get('state')}, Lambda={'✅' if ag.get('lambda_arn') else '❌'}, Schema={'✅' if ag.get('function_schema') else '❌'}
"""
        
        report += f"""
## 🔄 Function Calling Tests

"""
        
        for test in function_calling.get('function_calling_tests', []):
            status = "✅ PASS" if test.get('function_called', False) else "❌ FAIL"
            report += f"""
### {test.get('test_name')} - {status}
- **Function Called**: {test.get('function_called', False)}
- **Expected Function Called**: {test.get('expected_function_called', False)}
- **Function Calls**: {len(test.get('function_calls', []))}
- **Has Search Results**: {test.get('has_search_results', False)}
- **Response Preview**: {test.get('response_preview', test.get('error', 'No response'))[:200]}
"""
        
        report += f"""
## 🎯 Diagnostic Conclusions

"""
        
        if overall_score >= 0.8:
            report += "✅ **EXCELLENT**: WebSearch Agent is working properly\n"
        elif overall_score >= 0.5:
            report += "⚠️ **PARTIAL**: WebSearch Agent has some issues\n"
        else:
            report += "❌ **CRITICAL**: WebSearch Agent has major issues\n"
        
        # Add specific recommendations
        recommendations = []
        
        if not lambda_working:
            recommendations.append("🔧 **Fix Lambda Function**: Lambda function is not responding correctly")
        
        if not agent_configured:
            recommendations.append("⚙️ **Fix Agent Configuration**: Agent is not properly configured or prepared")
        
        if not functions_working:
            recommendations.append("🔄 **Fix Function Calling**: Agent is not calling functions properly")
        
        if lambda_working and agent_configured and not functions_working:
            recommendations.append("📝 **Fix Agent Instructions**: Agent may not understand when to call functions")
        
        report += "\n### Recommendations:\n"
        for rec in recommendations:
            report += f"- {rec}\n"
        
        # Save report
        with open('websearch_diagnostic_report.md', 'w') as f:
            f.write(report)
        
        logger.info("📄 Diagnostic report saved: websearch_diagnostic_report.md")
        logger.info(f"🎯 Overall Health Score: {overall_score:.2f}/1.00")
        
        return overall_score

def main():
    diagnostic = WebSearchDiagnostic()
    score = diagnostic.generate_diagnostic_report()
    
    if score >= 0.8:
        logger.info("🎉 WebSearch Agent is working well!")
    elif score >= 0.5:
        logger.warning("⚠️ WebSearch Agent has some issues that need attention")
    else:
        logger.error("🚨 WebSearch Agent has critical issues requiring immediate fix")
    
    return score

if __name__ == "__main__":
    main()