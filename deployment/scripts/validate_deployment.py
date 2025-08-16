#!/usr/bin/env python3
"""
RevOps AI Framework - Deployment Validation
===========================================

Comprehensive validation script to verify system health and configuration.
Replaces multiple diagnostic scripts with a unified validation tool.

Usage:
    python3 validate_deployment.py              # Full validation
    python3 validate_deployment.py --agents     # Agents only
    python3 validate_deployment.py --lambdas    # Lambda functions only
    python3 validate_deployment.py --integrations # Integrations only
"""

import os
import sys
import json
import boto3
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError

class DeploymentValidator:
    """Comprehensive deployment validation for RevOps AI Framework"""
    
    def __init__(self):
        self.config = self._load_config()
        
        # Initialize AWS clients
        profile_name = self.config.get('profile_name', 'FireboltSystemAdministrator-740202120544')
        region_name = self.config.get('region_name', 'us-east-1')
        
        self.session = boto3.Session(profile_name=profile_name)
        self.bedrock_client = self.session.client('bedrock-agent', region_name=region_name)
        self.lambda_client = self.session.client('lambda', region_name=region_name)
        self.apigateway_client = self.session.client('apigateway', region_name=region_name)
        self.s3_client = self.session.client('s3', region_name=region_name)
        
        self.region_name = region_name
        self.profile_name = profile_name
        
        print(f"""
🔍 RevOps AI Framework - Deployment Validation
==============================================
Profile: {profile_name}
Region: {region_name}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        config_file = Path(__file__).parent.parent / "config" / "config.json"
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            sys.exit(1)
    
    def validate_agents(self) -> bool:
        """Validate all Bedrock agents"""
        print("\n🤖 Validating Bedrock Agents")
        print("=" * 40)
        
        agents_valid = True
        expected_agents = ['manager_agent', 'data_agent', 'deal_analysis_agent', 
                          'lead_analysis_agent', 'web_search_agent', 'execution_agent']
        
        for agent_name in expected_agents:
            agent_config = self.config.get(agent_name)
            if not agent_config:
                print(f"⚠️  {agent_name}: No configuration found")
                continue
            
            try:
                agent_id = agent_config['agent_id']
                response = self.bedrock_client.get_agent(agentId=agent_id)
                agent = response['agent']
                
                status = agent['agentStatus']
                if status == 'PREPARED':
                    print(f"✅ {agent_name}: {status} (ID: {agent_id})")
                else:
                    print(f"⚠️  {agent_name}: {status} (ID: {agent_id})")
                    agents_valid = False
                
                # Check agent alias
                if 'agent_alias_id' in agent_config:
                    try:
                        alias_response = self.bedrock_client.get_agent_alias(
                            agentId=agent_id,
                            agentAliasId=agent_config['agent_alias_id']
                        )
                        alias_status = alias_response['agentAlias']['agentAliasStatus']
                        print(f"   Alias: {alias_status}")
                    except Exception as e:
                        print(f"   Alias: ERROR - {e}")
                        agents_valid = False
                        
            except Exception as e:
                print(f"❌ {agent_name}: ERROR - {e}")
                agents_valid = False
        
        return agents_valid
    
    def validate_lambda_functions(self) -> bool:
        """Validate Lambda functions"""
        print("\n⚡ Validating Lambda Functions")
        print("=" * 40)
        
        lambdas_valid = True
        lambda_functions = self.config.get('lambda_functions', {})
        
        for func_name, func_config in lambda_functions.items():
            try:
                function_name = func_config['function_name']
                response = self.lambda_client.get_function(FunctionName=function_name)
                
                config = response['Configuration']
                state = config['State']
                
                if state == 'Active':
                    print(f"✅ {func_name}: {state}")
                    
                    # Check recent errors
                    try:
                        metrics = self.lambda_client.get_function_configuration(
                            FunctionName=function_name
                        )
                        print(f"   Runtime: {config['Runtime']}, Timeout: {config['Timeout']}s")
                    except Exception:
                        pass
                        
                else:
                    print(f"⚠️  {func_name}: {state}")
                    lambdas_valid = False
                    
            except Exception as e:
                print(f"❌ {func_name}: ERROR - {e}")
                lambdas_valid = False
        
        return lambdas_valid
    
    def validate_integrations(self) -> bool:
        """Validate integrations (Slack, Webhook Gateway)"""
        print("\n🔗 Validating Integrations")
        print("=" * 40)
        
        integrations_valid = True
        
        # Check Slack integration
        slack_config = self.config.get('integrations', {}).get('slack_bedrock_gateway', {})
        if slack_config:
            api_gateway_url = slack_config.get('api_gateway_url')
            if api_gateway_url:
                # Extract API ID from URL
                api_id = api_gateway_url.split('//')[1].split('.')[0] if '//' in api_gateway_url else None
                if api_id:
                    try:
                        response = self.apigateway_client.get_rest_api(restApiId=api_id)
                        print(f"✅ Slack Integration API: {response['name']}")
                    except Exception as e:
                        print(f"❌ Slack Integration API: ERROR - {e}")
                        integrations_valid = False
                else:
                    print("⚠️  Slack Integration: Invalid API Gateway URL")
        
        # Check webhook gateway
        webhook_functions = ['prod-revops-webhook-gateway', 'revops-webhook', 'revops-manager-agent-wrapper']
        for func_name in webhook_functions:
            try:
                self.lambda_client.get_function(FunctionName=func_name)
                print(f"✅ Webhook Gateway: {func_name}")
            except Exception as e:
                print(f"❌ Webhook Gateway {func_name}: ERROR - {e}")
                integrations_valid = False
        
        return integrations_valid
    
    def validate_knowledge_base(self) -> bool:
        """Validate knowledge base configuration"""
        print("\n📚 Validating Knowledge Base")
        print("=" * 40)
        
        kb_valid = True
        kb_config = self.config.get('knowledge_base', {})
        
        if not kb_config:
            print("⚠️  No knowledge base configuration found")
            return False
        
        try:
            # Check knowledge base
            kb_id = kb_config['knowledge_base_id']
            response = self.bedrock_client.get_knowledge_base(knowledgeBaseId=kb_id)
            kb = response['knowledgeBase']
            
            status = kb['status']
            if status == 'ACTIVE':
                print(f"✅ Knowledge Base: {status} (ID: {kb_id})")
            else:
                print(f"⚠️  Knowledge Base: {status} (ID: {kb_id})")
                kb_valid = False
            
            # Check S3 bucket
            bucket_name = kb_config.get('storage_bucket')
            if bucket_name:
                try:
                    self.s3_client.head_bucket(Bucket=bucket_name)
                    print(f"✅ S3 Bucket: {bucket_name}")
                except Exception as e:
                    print(f"❌ S3 Bucket: ERROR - {e}")
                    kb_valid = False
            
        except Exception as e:
            print(f"❌ Knowledge Base: ERROR - {e}")
            kb_valid = False
        
        return kb_valid
    
    def validate_system_health(self) -> bool:
        """Overall system health check"""
        print("\n💚 System Health Summary")
        print("=" * 40)
        
        all_validations = [
            ("Agents", self.validate_agents()),
            ("Lambda Functions", self.validate_lambda_functions()),
            ("Integrations", self.validate_integrations()),
            ("Knowledge Base", self.validate_knowledge_base())
        ]
        
        healthy_count = sum(1 for _, valid in all_validations if valid)
        total_count = len(all_validations)
        
        print(f"\nHealth Score: {healthy_count}/{total_count}")
        
        for component, valid in all_validations:
            status = "✅ HEALTHY" if valid else "❌ ISSUES"
            print(f"{component}: {status}")
        
        overall_health = healthy_count == total_count
        
        if overall_health:
            print("\n🎉 System is healthy and ready for production!")
        else:
            print("\n⚠️  System has issues that need attention")
        
        return overall_health
    
    def run(self, component: Optional[str] = None) -> bool:
        """Run validation for specified component or all components"""
        if component == "agents":
            return self.validate_agents()
        elif component == "lambdas":
            return self.validate_lambda_functions()
        elif component == "integrations":
            return self.validate_integrations()
        elif component == "knowledge-base":
            return self.validate_knowledge_base()
        else:
            return self.validate_system_health()

def main():
    parser = argparse.ArgumentParser(description='RevOps AI Framework Deployment Validation')
    parser.add_argument('--agents', action='store_true', help='Validate agents only')
    parser.add_argument('--lambdas', action='store_true', help='Validate Lambda functions only')
    parser.add_argument('--integrations', action='store_true', help='Validate integrations only')
    parser.add_argument('--knowledge-base', action='store_true', help='Validate knowledge base only')
    
    args = parser.parse_args()
    
    validator = DeploymentValidator()
    
    component = None
    if args.agents:
        component = "agents"
    elif args.lambdas:
        component = "lambdas"
    elif args.integrations:
        component = "integrations"
    elif args.knowledge_base:
        component = "knowledge-base"
    
    success = validator.run(component)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()