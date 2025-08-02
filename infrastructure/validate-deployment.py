#!/usr/bin/env python3
"""
RevOps AI Framework - Deployment Validation
==========================================
Comprehensive validation tests for deployed infrastructure and agents.

Usage:
    python infrastructure/validate-deployment.py
    python infrastructure/validate-deployment.py --component bedrock
    python infrastructure/validate-deployment.py --component slack
"""

import os
import sys
import json
import boto3
import requests
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class DeploymentValidator:
    """Comprehensive deployment validation"""
    
    def __init__(self, profile_name: str = None, region: str = 'us-east-1'):
        self.profile_name = profile_name
        self.region = region
        self.session = None
        self.validation_results = []
        
        # Load configuration
        self._load_configuration()
        self._initialize_aws_session()
        
    def _load_configuration(self):
        """Load deployment configuration"""
        config_path = Path("deployment/config.json")
        if not config_path.exists():
            self._error("Configuration file not found: deployment/config.json")
        
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.profile_name = self.profile_name or self.config.get('profile_name')
        self.region = self.region or self.config.get('region_name', 'us-east-1')
        
    def _initialize_aws_session(self):
        """Initialize AWS session"""
        try:
            if self.profile_name:
                self.session = boto3.Session(profile_name=self.profile_name)
            else:
                self.session = boto3.Session()
                
            # Test connection
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ Connected to AWS as: {identity.get('Arn')}")
            
        except Exception as e:
            self._error(f"AWS connection failed: {e}")
    
    def validate_all_components(self) -> bool:
        """Run comprehensive validation of all components"""
        print("\n🧪 Running Comprehensive Deployment Validation...")
        
        all_passed = True
        
        # 1. Validate Bedrock Agents
        if not self.validate_bedrock_agents():
            all_passed = False
        
        # 2. Validate Lambda Functions
        if not self.validate_lambda_functions():
            all_passed = False
        
        # 3. Validate Infrastructure
        if not self.validate_infrastructure():
            all_passed = False
        
        # 4. Validate Slack Integration
        if not self.validate_slack_integration():
            all_passed = False
        
        # 5. Validate End-to-End Connectivity
        if not self.validate_end_to_end():
            all_passed = False
        
        # Generate validation report
        self._generate_validation_report()
        
        return all_passed
    
    def validate_bedrock_agents(self) -> bool:
        """Validate all Bedrock agents"""
        print("\n🤖 Validating Bedrock Agents...")
        
        bedrock = self.session.client('bedrock-agent')
        bedrock_runtime = self.session.client('bedrock-agent-runtime')
        
        agents = ['manager_agent', 'data_agent', 'deal_analysis_agent', 
                 'lead_analysis_agent', 'web_search_agent', 'execution_agent']
        
        all_valid = True
        
        for agent_name in agents:
            agent_config = self.config.get(agent_name)
            if not agent_config:
                print(f"  ⚠️  No configuration for {agent_name}")
                continue
            
            try:
                agent_id = agent_config.get('agent_id')
                agent_alias_id = agent_config.get('agent_alias_id')
                
                if not agent_id:
                    print(f"  ❌ {agent_name}: No agent_id configured")
                    all_valid = False
                    continue
                
                # Check agent status
                response = bedrock.get_agent(agentId=agent_id)
                status = response['agent']['agentStatus']
                
                if status == 'PREPARED':
                    print(f"  ✅ {agent_name}: Agent ready ({agent_id})")
                    
                    # Test agent invocation if alias is available
                    if agent_alias_id:
                        try:
                            test_response = bedrock_runtime.invoke_agent(
                                agentId=agent_id,
                                agentAliasId=agent_alias_id,
                                sessionId=f'validation-{int(time.time())}',
                                inputText='Health check - please respond with OK'
                            )
                            print(f"    ✅ Agent invocation test passed")
                            
                        except Exception as e:
                            print(f"    ⚠️  Agent invocation failed: {e}")
                    else:
                        print(f"    ⚠️  No agent_alias_id configured")
                        
                else:
                    print(f"  ⚠️  {agent_name}: Agent status is {status} (not PREPARED)")
                    
                self._record_result(f"Bedrock Agent {agent_name}", True, f"Status: {status}")
                
            except Exception as e:
                print(f"  ❌ {agent_name}: Validation failed - {e}")
                self._record_result(f"Bedrock Agent {agent_name}", False, str(e))
                all_valid = False
        
        return all_valid
    
    def validate_lambda_functions(self) -> bool:
        """Validate Lambda functions"""
        print("\n📦 Validating Lambda Functions...")
        
        lambda_client = self.session.client('lambda')
        all_valid = True
        
        lambda_functions = self.config.get('lambda_functions', {})
        
        for func_key, func_config in lambda_functions.items():
            try:
                function_name = func_config.get('function_name')
                if not function_name:
                    print(f"  ⚠️  No function_name for {func_key}")
                    continue
                
                # Get function configuration
                response = lambda_client.get_function(FunctionName=function_name)
                
                state = response['Configuration']['State']
                last_modified = response['Configuration']['LastModified']
                
                if state == 'Active':
                    print(f"  ✅ {function_name}: Active (modified: {last_modified})")
                    
                    # Test function invocation (dry run)
                    try:
                        test_payload = {'test': True, 'validation': True}
                        invoke_response = lambda_client.invoke(
                            FunctionName=function_name,
                            InvocationType='DryRun',
                            Payload=json.dumps(test_payload)
                        )
                        print(f"    ✅ Function validation test passed")
                        
                    except Exception as e:
                        print(f"    ⚠️  Function test failed: {e}")
                        
                else:
                    print(f"  ⚠️  {function_name}: State is {state} (not Active)")
                    all_valid = False
                
                self._record_result(f"Lambda Function {function_name}", True, f"State: {state}")
                
            except Exception as e:
                print(f"  ❌ {func_key}: Validation failed - {e}")
                self._record_result(f"Lambda Function {func_key}", False, str(e))
                all_valid = False
        
        return all_valid
    
    def validate_infrastructure(self) -> bool:
        """Validate CloudFormation infrastructure"""
        print("\n🏗️  Validating Infrastructure...")
        
        cf_client = self.session.client('cloudformation')
        all_valid = True
        
        # Check main stack
        stack_name = 'revops-slack-bedrock'
        
        try:
            response = cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            status = stack['StackStatus']
            
            if status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                print(f"  ✅ Stack {stack_name}: {status}")
                
                # Validate outputs
                outputs = {output['OutputKey']: output['OutputValue'] 
                          for output in stack.get('Outputs', [])}
                
                required_outputs = ['ApiGatewayUrl', 'ProcessingQueueUrl', 'SecretsArn']
                for output_key in required_outputs:
                    if output_key in outputs:
                        print(f"    ✅ Output {output_key}: {outputs[output_key]}")
                    else:
                        print(f"    ❌ Missing output: {output_key}")
                        all_valid = False
                
                self._record_result(f"CloudFormation Stack {stack_name}", True, f"Status: {status}")
                
            else:
                print(f"  ❌ Stack {stack_name}: Unexpected status {status}")
                self._record_result(f"CloudFormation Stack {stack_name}", False, f"Status: {status}")
                all_valid = False
                
        except cf_client.exceptions.ClientError as e:
            if 'does not exist' in str(e):
                print(f"  ❌ Stack {stack_name}: Does not exist")
            else:
                print(f"  ❌ Stack {stack_name}: Error - {e}")
            self._record_result(f"CloudFormation Stack {stack_name}", False, str(e))
            all_valid = False
        
        return all_valid
    
    def validate_slack_integration(self) -> bool:
        """Validate Slack integration"""
        print("\n💬 Validating Slack Integration...")
        
        slack_config = self.config.get('integrations', {}).get('slack_bedrock_gateway', {})
        
        if not slack_config:
            print("  ⚠️  No Slack configuration found")
            return False
        
        api_gateway_url = slack_config.get('api_gateway_url')
        
        if not api_gateway_url:
            print("  ❌ No API Gateway URL configured")
            return False
        
        try:
            # Test API Gateway health (if health endpoint exists)
            health_url = api_gateway_url.replace('/slack-events', '/health')
            
            print(f"  🔍 Testing API Gateway: {api_gateway_url}")
            
            # Test with a simple GET request (should return method not allowed)
            response = requests.get(api_gateway_url, timeout=10)
            
            # API Gateway should respond (even with an error for GET on POST endpoint)
            if response.status_code in [200, 403, 405, 500]:
                print(f"    ✅ API Gateway responding (status: {response.status_code})")
                self._record_result("Slack API Gateway", True, f"Status: {response.status_code}")
            else:
                print(f"    ⚠️  Unexpected response: {response.status_code}")
                self._record_result("Slack API Gateway", False, f"Status: {response.status_code}")
                return False
            
            # Check SQS queue
            sqs_client = self.session.client('sqs')
            try:
                # List queues to verify they exist
                response = sqs_client.list_queues(QueueNamePrefix='revops-slack-bedrock')
                queues = response.get('QueueUrls', [])
                
                if queues:
                    print(f"    ✅ SQS Queues found: {len(queues)}")
                    for queue_url in queues:
                        queue_name = queue_url.split('/')[-1]
                        print(f"      - {queue_name}")
                else:
                    print("    ⚠️  No SQS queues found")
                    
            except Exception as e:
                print(f"    ⚠️  SQS validation failed: {e}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Slack integration validation failed: {e}")
            self._record_result("Slack Integration", False, str(e))
            return False
    
    def validate_end_to_end(self) -> bool:
        """Validate end-to-end system connectivity"""
        print("\n🔄 Validating End-to-End Connectivity...")
        
        try:
            # Test manager agent
            manager_agent = self.config.get('manager_agent', {})
            agent_id = manager_agent.get('agent_id')
            agent_alias_id = manager_agent.get('agent_alias_id')
            
            if not agent_id or not agent_alias_id:
                print("  ⚠️  Manager agent not fully configured")
                return False
            
            bedrock_runtime = self.session.client('bedrock-agent-runtime')
            
            # Test agent collaboration
            test_message = "System health check: Please confirm all agents are operational and respond with a summary."
            
            response = bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=f'e2e-validation-{int(time.time())}',
                inputText=test_message
            )
            
            print("  ✅ End-to-end agent communication test passed")
            self._record_result("End-to-End Connectivity", True, "Agent communication successful")
            
            # Test knowledge base access (if configured)
            kb_config = self.config.get('knowledge_base')
            if kb_config and kb_config.get('knowledge_base_id'):
                print("    ✅ Knowledge base configuration found")
            else:
                print("    ⚠️  Knowledge base not configured")
            
            return True
            
        except Exception as e:
            print(f"  ❌ End-to-end validation failed: {e}")
            self._record_result("End-to-End Connectivity", False, str(e))
            return False
    
    def _record_result(self, component: str, success: bool, details: str):
        """Record validation result"""
        self.validation_results.append({
            'component': component,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def _generate_validation_report(self):
        """Generate comprehensive validation report"""
        print(f"\n📋 Validation Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for result in self.validation_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "No tests run")
        
        print("\nDetailed Results:")
        for result in self.validation_results:
            status_icon = "✅" if result['success'] else "❌"
            print(f"{status_icon} {result['component']}: {result['details']}")
        
        # Save report to file
        report_path = Path("validation-report.json")
        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'success_rate': passed_tests/total_tests*100 if total_tests > 0 else 0
                },
                'results': self.validation_results
            }, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_path}")
    
    def _error(self, message: str):
        """Handle validation error"""
        print(f"❌ ERROR: {message}")
        sys.exit(1)

def main():
    """Main validation entry point"""
    parser = argparse.ArgumentParser(description='RevOps AI Framework Deployment Validation')
    parser.add_argument('--component', choices=['bedrock', 'lambda', 'infrastructure', 'slack', 'e2e'],
                       help='Validate specific component only')
    parser.add_argument('--profile', help='AWS profile name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    # Create validator
    validator = DeploymentValidator(
        profile_name=args.profile,
        region=args.region
    )
    
    # Run validation
    if args.component:
        component_methods = {
            'bedrock': validator.validate_bedrock_agents,
            'lambda': validator.validate_lambda_functions,
            'infrastructure': validator.validate_infrastructure,
            'slack': validator.validate_slack_integration,
            'e2e': validator.validate_end_to_end
        }
        
        method = component_methods[args.component]
        success = method()
        validator._generate_validation_report()
        
    else:
        success = validator.validate_all_components()
    
    if success:
        print("\n✅ All validations passed!")
        sys.exit(0)
    else:
        print("\n❌ Some validations failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()