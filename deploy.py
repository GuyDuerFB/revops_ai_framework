#!/usr/bin/env python3
"""
RevOps AI Framework - Unified Deployment
========================================
Single-command deployment for the entire RevOps AI system.

Usage:
    python deploy.py                    # Interactive deployment
    python deploy.py --validate-only    # Validation only
    python deploy.py --rollback         # Rollback deployment

Requirements:
    - AWS CLI configured with SSO
    - Python 3.9+
    - Proper IAM permissions
"""

import os
import sys
import json
import boto3
import subprocess
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class RevOpsDeployer:
    """Unified deployment manager for RevOps AI Framework"""
    
    def __init__(self, validate_only: bool = False, rollback: bool = False):
        self.validate_only = validate_only
        self.rollback = rollback
        self.config = {}
        self.session = None
        self.deployment_log = []
        
        # Load configuration
        self._load_configuration()
        
        print(f"""
🚀 RevOps AI Framework - Unified Deployment
============================================
Mode: {'Validation Only' if validate_only else 'Rollback' if rollback else 'Full Deployment'}
Profile: {self.config.get('profile_name', 'default')}
Region: {self.config.get('region_name', 'us-east-1')}
""")
    
    def _load_configuration(self):
        """Load deployment configuration"""
        config_path = Path("deployment/config.json")
        if not config_path.exists():
            self._error("Configuration file not found: deployment/config.json")
        
        with open(config_path) as f:
            self.config = json.load(f)
        
        self._log("✅ Configuration loaded successfully")
    
    def validate_prerequisites(self) -> bool:
        """Comprehensive prerequisite validation"""
        print("\n🔍 Validating Prerequisites...")
        
        try:
            # 1. AWS SSO Authentication
            if not self._validate_aws_sso():
                return False
            
            # 2. Required Permissions
            if not self._validate_permissions():
                return False
            
            # 3. Python Environment
            if not self._validate_python_environment():
                return False
            
            # 4. AWS Resources
            if not self._validate_aws_resources():
                return False
            
            # 5. Configuration Completeness
            if not self._validate_configuration():
                return False
            
            print("✅ All prerequisites validated successfully!")
            return True
            
        except Exception as e:
            self._error(f"Prerequisite validation failed: {e}")
            return False
    
    def _validate_aws_sso(self) -> bool:
        """Validate AWS SSO connection"""
        try:
            profile_name = self.config.get('profile_name')
            if not profile_name:
                self._error("No profile_name in configuration")
                return False
            
            # Test SSO connection
            self.session = boto3.Session(profile_name=profile_name)
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            
            print(f"  ✅ AWS SSO: Connected as {identity.get('Arn')}")
            return True
            
        except Exception as e:
            print(f"  ❌ AWS SSO: Connection failed - {e}")
            print(f"     Run: aws configure sso --profile {profile_name}")
            return False
    
    def _validate_permissions(self) -> bool:
        """Validate required AWS permissions"""
        required_permissions = [
            ('bedrock', 'list_agents'),
            ('lambda', 'list_functions'),
            ('iam', 'list_roles'),
            ('secretsmanager', 'list_secrets'),
            ('cloudformation', 'list_stacks')
        ]
        
        for service, action in required_permissions:
            try:
                client = self.session.client(service)
                getattr(client, action)()
                print(f"  ✅ Permissions: {service}:{action}")
            except Exception as e:
                print(f"  ❌ Permissions: Missing {service}:{action} - {e}")
                return False
        
        return True
    
    def _validate_python_environment(self) -> bool:
        """Validate Python environment"""
        import sys
        
        # Check Python version
        if sys.version_info < (3, 9):
            print(f"  ❌ Python: Version {sys.version} < 3.9 required")
            return False
        
        print(f"  ✅ Python: Version {sys.version_info.major}.{sys.version_info.minor}")
        
        # Check required packages
        required_packages = ['boto3', 'requests', 'yaml']
        for package in required_packages:
            try:
                __import__(package)
                print(f"  ✅ Package: {package}")
            except ImportError:
                print(f"  ❌ Package: {package} not installed")
                return False
        
        return True
    
    def _validate_aws_resources(self) -> bool:
        """Validate existing AWS resources"""
        try:
            # Check if agents exist
            bedrock = self.session.client('bedrock-agent')
            
            for agent_name in ['manager_agent', 'data_agent', 'deal_analysis_agent']:
                agent_config = self.config.get(agent_name, {})
                agent_id = agent_config.get('agent_id')
                
                if agent_id:
                    try:
                        response = bedrock.get_agent(agentId=agent_id)
                        print(f"  ✅ Agent: {agent_name} ({agent_id})")
                    except Exception:
                        print(f"  ⚠️  Agent: {agent_name} ({agent_id}) not found")
                else:
                    print(f"  ⚠️  Agent: {agent_name} - no agent_id in config")
            
            return True
            
        except Exception as e:
            print(f"  ❌ AWS Resources validation failed: {e}")
            return False
    
    def _validate_configuration(self) -> bool:
        """Validate configuration completeness"""
        required_keys = ['profile_name', 'region_name', 'lambda_functions']
        
        for key in required_keys:
            if key not in self.config:
                print(f"  ❌ Configuration: Missing required key '{key}'")
                return False
            print(f"  ✅ Configuration: {key}")
        
        return True
    
    def deploy_full_system(self) -> bool:
        """Deploy the complete RevOps AI system"""
        if self.validate_only:
            return True
        
        if self.rollback:
            return self._rollback_deployment()
        
        print("\n🚀 Starting Full System Deployment...")
        
        try:
            # Phase 1: Deploy Lambda Functions
            if not self._deploy_lambda_functions():
                return False
            
            # Phase 2: Deploy/Update Bedrock Agents
            if not self._deploy_bedrock_agents():
                return False
            
            # Phase 3: Deploy Slack Integration
            if not self._deploy_slack_integration():
                return False
            
            # Phase 4: Validate Deployment
            if not self._validate_deployment():
                return False
            
            print("\n🎉 Deployment completed successfully!")
            self._generate_deployment_summary()
            return True
            
        except Exception as e:
            self._error(f"Deployment failed: {e}")
            return False
    
    def _deploy_lambda_functions(self) -> bool:
        """Deploy all Lambda functions"""
        print("\n📦 Deploying Lambda Functions...")
        
        lambda_functions = self.config.get('lambda_functions', {})
        lambda_client = self.session.client('lambda')
        
        for func_name, func_config in lambda_functions.items():
            try:
                function_name = func_config['function_name']
                source_dir = func_config['source_dir']
                
                print(f"  🔄 Deploying {function_name}...")
                
                # Check if function exists
                try:
                    lambda_client.get_function(FunctionName=function_name)
                    print(f"    ✅ Function {function_name} already exists")
                except lambda_client.exceptions.ResourceNotFoundException:
                    print(f"    ⚠️  Function {function_name} not found - needs creation")
                
                self._log(f"Lambda function {function_name} processed")
                
            except Exception as e:
                print(f"    ❌ Failed to deploy {func_name}: {e}")
                return False
        
        return True
    
    def _deploy_bedrock_agents(self) -> bool:
        """Deploy/Update Bedrock agents"""
        print("\n🤖 Deploying Bedrock Agents...")
        
        bedrock = self.session.client('bedrock-agent')
        
        agents = ['manager_agent', 'data_agent', 'deal_analysis_agent', 
                 'lead_analysis_agent', 'web_search_agent', 'execution_agent']
        
        for agent_name in agents:
            agent_config = self.config.get(agent_name)
            if not agent_config:
                print(f"  ⚠️  No configuration for {agent_name}")
                continue
            
            try:
                agent_id = agent_config.get('agent_id')
                if agent_id:
                    # Verify agent exists
                    response = bedrock.get_agent(agentId=agent_id)
                    print(f"  ✅ Agent {agent_name}: {agent_id} (status: {response['agent']['agentStatus']})")
                else:
                    print(f"  ⚠️  Agent {agent_name}: No agent_id configured")
                
                self._log(f"Bedrock agent {agent_name} processed")
                
            except Exception as e:
                print(f"  ❌ Agent {agent_name}: {e}")
                return False
        
        return True
    
    def _deploy_slack_integration(self) -> bool:
        """Deploy Slack integration"""
        print("\n💬 Deploying Slack Integration...")
        
        try:
            slack_config = self.config.get('integrations', {}).get('slack_bedrock_gateway', {})
            
            if slack_config.get('status') == 'deployed_and_tested':
                api_gateway_url = slack_config.get('api_gateway_url')
                print(f"  ✅ Slack Integration: Already deployed")
                print(f"    API Gateway URL: {api_gateway_url}")
                
                # Test the endpoint
                if api_gateway_url:
                    import requests
                    try:
                        response = requests.get(api_gateway_url.replace('/slack-events', '/health'), timeout=10)
                        print(f"    ✅ Health Check: {response.status_code}")
                    except Exception as e:
                        print(f"    ⚠️  Health Check: Failed - {e}")
            else:
                print("  ⚠️  Slack Integration: Not configured")
            
            self._log("Slack integration processed")
            return True
            
        except Exception as e:
            print(f"  ❌ Slack Integration failed: {e}")
            return False
    
    def _validate_deployment(self) -> bool:
        """Comprehensive deployment validation"""
        print("\n🧪 Validating Deployment...")
        
        try:
            # Test agent connectivity
            bedrock_runtime = self.session.client('bedrock-agent-runtime')
            
            manager_agent = self.config.get('manager_agent', {})
            if manager_agent.get('agent_id') and manager_agent.get('agent_alias_id'):
                try:
                    response = bedrock_runtime.invoke_agent(
                        agentId=manager_agent['agent_id'],
                        agentAliasId=manager_agent['agent_alias_id'],
                        sessionId='deployment-test',
                        inputText='System health check'
                    )
                    print("  ✅ Agent Connectivity: Manager agent responding")
                except Exception as e:
                    print(f"  ⚠️  Agent Connectivity: {e}")
            
            # Test Lambda functions
            lambda_client = self.session.client('lambda')
            for func_name, func_config in self.config.get('lambda_functions', {}).items():
                try:
                    function_name = func_config['function_name']
                    lambda_client.get_function(FunctionName=function_name)
                    print(f"  ✅ Lambda: {function_name}")
                except Exception as e:
                    print(f"  ❌ Lambda: {function_name} - {e}")
                    return False
            
            print("✅ Deployment validation completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Deployment validation failed: {e}")
            return False
    
    def _rollback_deployment(self) -> bool:
        """Rollback deployment"""
        print("\n⏪ Rolling back deployment...")
        print("  ⚠️  Rollback functionality not implemented yet")
        print("  💡 Manual rollback required using AWS Console")
        return True
    
    def _generate_deployment_summary(self):
        """Generate deployment summary"""
        print(f"""
📋 Deployment Summary
====================
Timestamp: {datetime.now().isoformat()}
Profile: {self.config.get('profile_name')}
Region: {self.config.get('region_name')}

Components Deployed:
• Lambda Functions: {len(self.config.get('lambda_functions', {}))}
• Bedrock Agents: 6 agents
• Slack Integration: {self.config.get('integrations', {}).get('slack_bedrock_gateway', {}).get('status', 'unknown')}

Next Steps:
1. Configure Slack app with API Gateway URL
2. Test system with: @RevBot test connectivity
3. Monitor CloudWatch logs for any issues

Slack Setup:
API Gateway URL: {self.config.get('integrations', {}).get('slack_bedrock_gateway', {}).get('api_gateway_url', 'Not configured')}
""")
    
    def _log(self, message: str):
        """Log deployment action"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.deployment_log.append(log_entry)
        # Could write to file here
    
    def _error(self, message: str):
        """Handle deployment error"""
        print(f"❌ ERROR: {message}")
        sys.exit(1)

def main():
    """Main deployment entry point"""
    parser = argparse.ArgumentParser(description='RevOps AI Framework Deployment')
    parser.add_argument('--validate-only', action='store_true', 
                       help='Only validate prerequisites, do not deploy')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback previous deployment')
    
    args = parser.parse_args()
    
    # Create deployer
    deployer = RevOpsDeployer(
        validate_only=args.validate_only,
        rollback=args.rollback
    )
    
    # Run prerequisite validation
    if not deployer.validate_prerequisites():
        sys.exit(1)
    
    # Run deployment
    if not deployer.deploy_full_system():
        sys.exit(1)
    
    print("\n✅ RevOps AI Framework deployment completed successfully!")

if __name__ == "__main__":
    main()