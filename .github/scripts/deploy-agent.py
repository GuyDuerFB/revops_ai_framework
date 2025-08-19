#!/usr/bin/env python3
"""
Agent Deployment Script for RevOps AI Framework
Deploys agent to AWS with consistent configuration matching existing agents
"""

import os
import sys
import json
import boto3
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from botocore.exceptions import ClientError


class AgentDeployer:
    """Deploys agent to AWS with consistent configuration"""
    
    def __init__(self, agent_name: str, environment: str = "dev", dry_run: bool = False):
        self.agent_name = agent_name.strip()
        self.environment = environment.lower().strip()
        self.dry_run = dry_run
        
        # Get repository root (assuming script is in .github/scripts/)
        self.repo_root = Path(__file__).parent.parent.parent
        self.config_file = Path(__file__).parent / "agent-config-template.json"
        
        # Load configuration
        self.config = self._load_config_template()
        
        # Initialize AWS session
        self.aws_session = None
        self.bedrock_client = None
        self.iam_client = None
        self._init_aws_clients()
        
        self.deployment_output = {}
        
    def _load_config_template(self) -> Dict[str, Any]:
        """Load agent configuration template"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading configuration template: {e}")
            sys.exit(1)
    
    def _init_aws_clients(self) -> None:
        """Initialize AWS clients with proper profile and region"""
        try:
            # Use OIDC credentials if available (GitHub Actions), otherwise use profile
            if os.getenv('AWS_ROLE_ARN'):
                self.aws_session = boto3.Session()
            else:
                profile_name = self.config['aws_settings']['profile_name']
                self.aws_session = boto3.Session(profile_name=profile_name)
            
            region = self.config['region']
            self.bedrock_client = self.aws_session.client('bedrock-agent', region_name=region)
            self.iam_client = self.aws_session.client('iam', region_name=region)
            
            # Test AWS connectivity
            sts_client = self.aws_session.client('sts')
            identity = sts_client.get_caller_identity()
            print(f"✅ AWS credentials valid - Account: {identity['Account']}, User: {identity.get('UserId', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error initializing AWS clients: {e}")
            sys.exit(1)
    
    def _validate_prerequisites(self, agent_dir: str, instructions_file: str) -> bool:
        """Validate that prerequisites are met"""
        print("🔍 Validating deployment prerequisites...")
        
        try:
            # Check agent directory and instructions file
            if not Path(agent_dir).exists():
                print(f"❌ Agent directory does not exist: {agent_dir}")
                return False
            
            if not Path(instructions_file).exists():
                print(f"❌ Instructions file does not exist: {instructions_file}")
                return False
            
            # Read and validate instructions content
            with open(instructions_file, 'r') as f:
                instructions_content = f.read()
            
            if not instructions_content.strip():
                print(f"❌ Instructions file is empty: {instructions_file}")
                return False
            
            # Check for required sections
            required_sections = self.config['validation']['required_sections']
            missing_sections = []
            for section in required_sections:
                if section not in instructions_content:
                    missing_sections.append(section)
            
            if missing_sections:
                print(f"❌ Instructions file missing required sections: {missing_sections}")
                return False
            
            # Check if template placeholders are still present
            remaining_placeholders = []
            for placeholder in self.config['validation']['required_placeholders_removed']:
                if placeholder in instructions_content:
                    remaining_placeholders.append(placeholder)
            
            if remaining_placeholders and not self.dry_run:
                print(f"❌ Instructions file contains template placeholders: {remaining_placeholders}")
                print("   Please customize the instructions before deployment")
                return False
            elif remaining_placeholders and self.dry_run:
                print(f"⚠️  Instructions file contains template placeholders: {remaining_placeholders}")
                print("   (Proceeding with dry run)")
            
            # Check Bedrock Agent service access
            try:
                self.bedrock_client.list_agents(maxResults=1)
                print("✅ Bedrock Agent service accessible")
            except Exception as e:
                print(f"❌ Cannot access Bedrock Agent service: {e}")
                return False
            
            # Check knowledge base exists
            kb_id = self.config['knowledge_base_id']
            try:
                self.bedrock_client.get_knowledge_base(knowledgeBaseId=kb_id)
                print(f"✅ Knowledge base accessible: {kb_id}")
            except Exception as e:
                print(f"❌ Cannot access knowledge base {kb_id}: {e}")
                return False
            
            # Check IAM execution role exists
            role_arn = self.config['execution_role_arn']
            role_name = role_arn.split('/')[-1]
            try:
                self.iam_client.get_role(RoleName=role_name)
                print(f"✅ IAM execution role accessible: {role_name}")
            except Exception as e:
                print(f"❌ Cannot access IAM role {role_name}: {e}")
                return False
            
            print("✅ Prerequisites validation passed")
            return True
            
        except Exception as e:
            print(f"❌ Error during prerequisites validation: {e}")
            return False
    
    def _generate_agent_config(self, instructions_content: str) -> Dict[str, Any]:
        """Generate agent configuration based on template and agent-specific values"""
        # Use exact directory name as agent name
        agent_name_formatted = self.agent_name
        display_name = self.agent_name.replace('-', ' ').replace('_', ' ').title()
        
        return {
            'agentName': agent_name_formatted,
            'description': f"{display_name} agent for the RevOps AI Framework",
            'instruction': instructions_content,
            'foundationModel': self.config['foundation_model'],
            'agentResourceRoleArn': self.config['execution_role_arn'],
            'idleSessionTTLInSeconds': self.config['idle_session_ttl'],
            'agentCollaboration': self.config['collaboration_type']
        }
    
    def _create_agent(self, agent_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Create the Bedrock Agent"""
        if self.dry_run:
            print("🔍 [DRY RUN] Would create Bedrock Agent with config:")
            print(f"   Name: {agent_config['agentName']}")
            print(f"   Model: {agent_config['foundationModel']}")
            print(f"   Role: {agent_config['agentResourceRoleArn']}")
            print(f"   Collaboration: {agent_config['agentCollaboration']}")
            return True, {
                'agent_id': 'DRY_RUN_AGENT_ID',
                'agent_arn': 'arn:aws:bedrock:us-east-1:740202120544:agent/DRY_RUN_AGENT_ID'
            }
        
        try:
            print("🤖 Creating Bedrock Agent...")
            response = self.bedrock_client.create_agent(**agent_config)
            
            agent_info = response['agent']
            agent_id = agent_info['agentId']
            agent_arn = agent_info['agentArn']
            
            print(f"✅ Agent created successfully")
            print(f"   Agent ID: {agent_id}")
            print(f"   Agent ARN: {agent_arn}")
            
            return True, {
                'agent_id': agent_id,
                'agent_arn': agent_arn,
                'agent_name': agent_info['agentName']
            }
            
        except ClientError as e:
            print(f"❌ Error creating agent: {e}")
            return False, {}
    
    def _associate_knowledge_base(self, agent_id: str) -> bool:
        """Associate the knowledge base with the agent"""
        if self.dry_run:
            print(f"🔍 [DRY RUN] Would associate knowledge base {self.config['knowledge_base_id']} with agent {agent_id}")
            return True
        
        try:
            print("📚 Associating knowledge base...")
            kb_config = self.config['knowledge_base_config']
            
            self.bedrock_client.associate_agent_knowledge_base(
                agentId=agent_id,
                agentVersion='DRAFT',
                knowledgeBaseId=self.config['knowledge_base_id'],
                description=kb_config['description'],
                knowledgeBaseState='ENABLED'
            )
            
            print(f"✅ Knowledge base associated: {self.config['knowledge_base_id']}")
            return True
            
        except ClientError as e:
            print(f"❌ Error associating knowledge base: {e}")
            return False
    
    def _prepare_agent(self, agent_id: str) -> bool:
        """Prepare the agent (create version)"""
        if self.dry_run:
            print(f"🔍 [DRY RUN] Would prepare agent {agent_id}")
            return True
        
        try:
            print("🔧 Preparing agent...")
            self.bedrock_client.prepare_agent(agentId=agent_id)
            
            # Wait for preparation to complete
            max_wait = 120  # 2 minutes
            wait_interval = 5
            waited = 0
            
            while waited < max_wait:
                try:
                    response = self.bedrock_client.get_agent(agentId=agent_id)
                    status = response['agent']['agentStatus']
                    
                    if status == 'PREPARED':
                        print(f"✅ Agent prepared successfully")
                        return True
                    elif status == 'FAILED':
                        print(f"❌ Agent preparation failed")
                        return False
                    else:
                        print(f"⏳ Agent preparation in progress... ({status})")
                        time.sleep(wait_interval)
                        waited += wait_interval
                        
                except Exception as e:
                    print(f"⚠️  Error checking agent status: {e}")
                    time.sleep(wait_interval)
                    waited += wait_interval
            
            print(f"⚠️  Agent preparation timeout after {max_wait} seconds")
            return False
            
        except ClientError as e:
            print(f"❌ Error preparing agent: {e}")
            return False
    
    def _create_aliases(self, agent_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Create dev and prod aliases for the agent"""
        aliases_info = {
            'dev_alias': {},
            'prod_alias': {}
        }
        
        # Create both dev and prod aliases
        for env_type in ['dev', 'prod']:
            alias_name = f"{self.agent_name}_{env_type}"
            
            if self.dry_run:
                print(f"🔍 [DRY RUN] Would create alias:")
                print(f"   Name: {alias_name}")
                print(f"   Environment: {env_type}")
                print(f"   Agent Version: 1")
                aliases_info[f'{env_type}_alias'] = {
                    'alias_id': f'DRY_RUN_ALIAS_ID_{env_type.upper()}',
                    'alias_name': alias_name
                }
                continue
            
            try:
                print(f"🏷️  Creating {env_type} alias: {alias_name}...")
                
                response = self.bedrock_client.create_agent_alias(
                    agentId=agent_id,
                    agentAliasName=alias_name,
                    description=f"{env_type.title()} environment alias for {self.agent_name}",
                    routingConfiguration=[{
                        'agentVersion': '1'  # Use version 1 for both aliases
                    }]
                )
                
                alias_info = response['agentAlias']
                alias_id = alias_info['agentAliasId']
                
                print(f"✅ Created {env_type} alias successfully")
                print(f"   Alias ID: {alias_id}")
                print(f"   Alias Name: {alias_name}")
                
                aliases_info[f'{env_type}_alias'] = {
                    'alias_id': alias_id,
                    'alias_name': alias_name
                }
                
            except ClientError as e:
                print(f"❌ Error creating {env_type} alias: {e}")
                return False, {}
        
        return True, aliases_info
    
    def _update_multi_agent_policies(self, agent_id: str) -> bool:
        """Update multi-agent collaboration policies to include the new agent"""
        if self.dry_run:
            print(f"🔍 [DRY RUN] Would update multi-agent policies to include agent {agent_id}")
            return True
        
        try:
            print("🔗 Updating multi-agent collaboration policies...")
            
            # This is a complex operation that would require:
            # 1. Getting the current multi-agent policy
            # 2. Adding the new agent's ARN to the allowed resources
            # 3. Updating the policy
            # For now, we'll log that this needs to be done manually
            
            print("⚠️  Multi-agent policy update requires manual intervention")
            print("   Please update the AmazonBedrockAgentsMultiAgentsPolicies to include:")
            print(f"   arn:aws:bedrock:us-east-1:{self.config['account_id']}:agent-alias/{agent_id}/*")
            
            return True
            
        except Exception as e:
            print(f"⚠️  Note: Multi-agent policy update needs manual configuration: {e}")
            return True  # Don't fail deployment for this
    
    def _validate_deployment(self, agent_id: str) -> bool:
        """Validate the deployment was successful"""
        if self.dry_run:
            print(f"🔍 [DRY RUN] Would validate deployment of agent {agent_id}")
            return True
        
        try:
            print("🧪 Validating deployment...")
            
            # Check agent status
            response = self.bedrock_client.get_agent(agentId=agent_id)
            agent_status = response['agent']['agentStatus']
            
            if agent_status not in ['PREPARED', 'NOT_PREPARED']:
                print(f"⚠️  Agent status is {agent_status}, may need more time")
                return True
            
            # Check knowledge base association
            try:
                kb_response = self.bedrock_client.list_agent_knowledge_bases(
                    agentId=agent_id,
                    agentVersion='DRAFT'
                )
                if kb_response['agentKnowledgeBaseSummaries']:
                    print("✅ Knowledge base association verified")
                else:
                    print("⚠️  No knowledge base associations found")
                    return False
            except Exception as e:
                print(f"⚠️  Could not verify knowledge base association: {e}")
            
            print("✅ Deployment validation completed")
            return True
            
        except Exception as e:
            print(f"❌ Error during deployment validation: {e}")
            return False
    
    def _save_deployment_output(self) -> None:
        """Save deployment output to file for GitHub Actions"""
        try:
            output_file = "/tmp/agent_deployment_output.json"
            with open(output_file, 'w') as f:
                json.dump(self.deployment_output, f, indent=2, default=str)
            print(f"📊 Deployment output saved to {output_file}")
        except Exception as e:
            print(f"⚠️  Could not save deployment output: {e}")
    
    def deploy_agent(self, agent_dir: str, instructions_file: str) -> bool:
        """Execute the complete agent deployment process"""
        print(f"🚀 Starting agent deployment")
        print(f"   Agent: {self.agent_name}")
        print(f"   Environment: {self.environment}")
        print(f"   Directory: {agent_dir}")
        print(f"   Instructions: {instructions_file}")
        print(f"   Dry Run: {self.dry_run}")
        print("=" * 60)
        
        try:
            # Step 1: Validate prerequisites
            if not self._validate_prerequisites(agent_dir, instructions_file):
                return False
            
            # Step 2: Read instructions file
            print("📖 Reading agent instructions...")
            with open(instructions_file, 'r') as f:
                instructions_content = f.read()
            
            # Step 3: Generate agent configuration
            print("⚙️  Generating agent configuration...")
            agent_config = self._generate_agent_config(instructions_content)
            
            # Step 4: Create Bedrock Agent
            success, agent_info = self._create_agent(agent_config)
            if not success:
                return False
            
            agent_id = agent_info['agent_id']
            self.deployment_output.update(agent_info)
            self.deployment_output['foundation_model'] = self.config['foundation_model']
            self.deployment_output['knowledge_base_id'] = self.config['knowledge_base_id']
            
            # Step 5: Associate knowledge base
            if not self._associate_knowledge_base(agent_id):
                return False
            
            # Step 6: Prepare agent
            if not self._prepare_agent(agent_id):
                return False
            
            # Step 7: Create aliases
            success, aliases_info = self._create_aliases(agent_id)
            if not success:
                return False
            
            self.deployment_output.update(aliases_info)
            
            # Step 8: Update multi-agent policies (manual step noted)
            self._update_multi_agent_policies(agent_id)
            
            # Step 9: Validate deployment
            if not self._validate_deployment(agent_id):
                print("⚠️  Deployment validation had issues, but deployment may still be successful")
            
            # Step 10: Save output
            self._save_deployment_output()
            
            print("\n🎉 Agent deployment completed successfully!")
            print(f"   Agent ID: {agent_id}")
            if not self.dry_run:
                print(f"   Test your agent through the RevOps AI Framework")
                print(f"   Monitor logs in CloudWatch: /aws/lambda/revops-*")
            
            return True
            
        except Exception as e:
            print(f"❌ Unexpected error during deployment: {e}")
            return False


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description='Deploy agent to AWS for RevOps AI Framework'
    )
    parser.add_argument(
        '--agent-name',
        required=True,
        help='Name of the agent directory to deploy'
    )
    parser.add_argument(
        '--environment',
        default='dev',
        choices=['dev', 'staging', 'prod', 'sandbox'],
        help='Deployment environment'
    )
    parser.add_argument(
        '--agent-dir',
        required=True,
        help='Path to agent directory'
    )
    parser.add_argument(
        '--instructions-file',
        required=True,
        help='Path to instructions.md file'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without deployment'
    )
    
    args = parser.parse_args()
    
    try:
        deployer = AgentDeployer(
            agent_name=args.agent_name,
            environment=args.environment,
            dry_run=args.dry_run
        )
        
        success = deployer.deploy_agent(args.agent_dir, args.instructions_file)
        
        if success:
            print(f"\n✅ Agent deployment {'simulation' if args.dry_run else 'process'} completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Agent deployment {'simulation' if args.dry_run else 'process'} failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Agent deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
