#!/usr/bin/env python3
"""
RevOps AI Framework - Unified Deployment Script
===============================================

Consolidated deployment script for all agents and components.
Replaces multiple individual deployment scripts with a single, comprehensive tool.

Usage:
    python3 deploy.py                    # Deploy all components
    python3 deploy.py --agent manager    # Deploy specific agent
    python3 deploy.py --validate-only    # Validation only
    python3 deploy.py --list-agents      # List current agents

Requirements:
    - AWS CLI configured with SSO profile
    - Python 3.9+
    - Proper IAM permissions for Bedrock and Lambda
"""

import os
import sys
import json
import boto3
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError

class RevOpsDeployer:
    """Unified deployment manager for RevOps AI Framework"""
    
    def __init__(self, validate_only: bool = False):
        self.validate_only = validate_only
        self.config = self._load_config()
        
        # Initialize AWS clients
        profile_name = self.config.get('profile_name', 'FireboltSystemAdministrator-740202120544')
        region_name = self.config.get('region_name', 'us-east-1')
        
        self.session = boto3.Session(profile_name=profile_name)
        self.bedrock_client = self.session.client('bedrock-agent', region_name=region_name)
        self.lambda_client = self.session.client('lambda', region_name=region_name)
        
        self.region_name = region_name
        self.profile_name = profile_name
        
        print(f"""
🚀 RevOps AI Framework - Unified Deployment
============================================
Mode: {'Validation Only' if validate_only else 'Full Deployment'}
Profile: {profile_name}
Region: {region_name}
""")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration"""
        config_file = Path(__file__).parent.parent / "config" / "config.json"
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    def validate_prerequisites(self) -> bool:
        """Validate deployment prerequisites"""
        print("🔍 Validating prerequisites...")
        
        # Check AWS credentials
        try:
            sts_client = self.session.client('sts')
            identity = sts_client.get_caller_identity()
            print(f"✅ AWS credentials valid - Account: {identity['Account']}")
        except Exception as e:
            print(f"❌ AWS credentials invalid: {e}")
            return False
        
        # Check Bedrock permissions
        try:
            self.bedrock_client.list_agents(maxResults=1)
            print("✅ Bedrock permissions valid")
        except Exception as e:
            print(f"❌ Bedrock permissions invalid: {e}")
            return False
        
        # Check Lambda permissions
        try:
            self.lambda_client.list_functions(MaxItems=1)
            print("✅ Lambda permissions valid")
        except Exception as e:
            print(f"❌ Lambda permissions invalid: {e}")
            return False
        
        return True
    
    def list_agents(self) -> None:
        """List all current agents"""
        print("📋 Current Bedrock Agents:")
        print("=" * 50)
        
        try:
            response = self.bedrock_client.list_agents()
            agents = response['agentSummaries']
            
            for agent in agents:
                print(f"• {agent['agentName']} ({agent['agentId']})")
                print(f"  Status: {agent['agentStatus']}")
                print(f"  Updated: {agent['updatedAt'].strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
        except Exception as e:
            print(f"❌ Error listing agents: {e}")
    
    def deploy_agent(self, agent_name: str) -> bool:
        """Deploy a specific agent"""
        print(f"🤖 Deploying {agent_name} agent...")
        
        agent_config = self.config.get(agent_name)
        if not agent_config:
            print(f"❌ No configuration found for agent: {agent_name}")
            return False
        
        if self.validate_only:
            print(f"✅ Configuration valid for {agent_name}")
            return True
        
        try:
            # Read instructions file
            instructions_file = Path(__file__).parent.parent.parent / agent_config['instructions_file']
            if not instructions_file.exists():
                print(f"❌ Instructions file not found: {instructions_file}")
                return False
            
            with open(instructions_file, 'r') as f:
                instructions = f.read()
            
            # Update agent
            agent_id = agent_config['agent_id']
            self.bedrock_client.update_agent(
                agentId=agent_id,
                agentName=agent_config.get('description', f"{agent_name}_V4"),
                description=agent_config.get('description', f"{agent_name} V4 Agent"),
                instruction=instructions,
                foundationModel=agent_config.get('foundation_model'),
                agentResourceRoleArn=self.config.get('execution_role_arn'),
                idleSessionTTLInSeconds=1800
            )
            
            # Prepare agent (create new version)
            self.bedrock_client.prepare_agent(agentId=agent_id)
            
            print(f"✅ {agent_name} agent updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error deploying {agent_name} agent: {e}")
            return False
    
    def deploy_all_agents(self) -> bool:
        """Deploy all configured agents"""
        print("🚀 Deploying all agents...")
        
        agents = ['manager_agent', 'data_agent', 'deal_analysis_agent', 
                 'lead_analysis_agent', 'web_search_agent', 'execution_agent']
        
        success_count = 0
        for agent in agents:
            if agent in self.config:
                if self.deploy_agent(agent):
                    success_count += 1
                    time.sleep(2)  # Brief pause between deployments
        
        print(f"\n📊 Deployment Summary: {success_count}/{len(agents)} agents deployed successfully")
        return success_count == len(agents)
    
    def sync_knowledge_base(self) -> bool:
        """Trigger knowledge base sync"""
        print("📚 Syncing knowledge base...")
        
        if self.validate_only:
            print("✅ Knowledge base sync would be triggered")
            return True
        
        try:
            # Import and run knowledge base sync
            sync_script = Path(__file__).parent / "sync_knowledge_base.py"
            if sync_script.exists():
                import subprocess
                result = subprocess.run([sys.executable, str(sync_script)], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Knowledge base sync completed")
                    return True
                else:
                    print(f"❌ Knowledge base sync failed: {result.stderr}")
                    return False
            else:
                print("⚠️  Knowledge base sync script not found")
                return True
                
        except Exception as e:
            print(f"❌ Error syncing knowledge base: {e}")
            return False
    
    def run(self, agent_name: Optional[str] = None) -> bool:
        """Run the deployment process"""
        if not self.validate_prerequisites():
            return False
        
        if agent_name:
            return self.deploy_agent(agent_name)
        else:
            success = True
            success &= self.deploy_all_agents()
            success &= self.sync_knowledge_base()
            
            if success:
                print("\n🎉 Deployment completed successfully!")
            else:
                print("\n❌ Deployment completed with errors")
            
            return success

def main():
    parser = argparse.ArgumentParser(description='RevOps AI Framework Deployment')
    parser.add_argument('--agent', help='Deploy specific agent (manager, data, deal_analysis, etc.)')
    parser.add_argument('--validate-only', action='store_true', help='Validate configuration only')
    parser.add_argument('--list-agents', action='store_true', help='List current agents')
    
    args = parser.parse_args()
    
    deployer = RevOpsDeployer(validate_only=args.validate_only)
    
    if args.list_agents:
        deployer.list_agents()
        return
    
    success = deployer.run(agent_name=args.agent)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()