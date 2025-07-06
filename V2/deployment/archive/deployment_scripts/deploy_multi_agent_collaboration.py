#!/usr/bin/env python3
"""
Deploy Multi-Agent Collaboration for RevOps AI Framework V2

This script configures multi-agent collaboration by setting up the Decision Agent
as a SUPERVISOR and adding DataAgent and ExecutionAgent as collaborators.

Prerequisites:
- All agents must be deployed and prepared
- Agent aliases must exist
- Proper IAM permissions for cross-agent collaboration

Configuration:
- Decision Agent: SUPERVISOR role
- DataAgent: Collaborator for data fetching
- ExecutionAgent: Collaborator for action execution
"""

import boto3
import json
import sys
import os
import time
from typing import Dict, Any, List, Optional

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def setup_multi_agent_collaboration(
    bedrock_agent_client: Any,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Set up multi-agent collaboration for the Decision Agent
    
    Args:
        bedrock_agent_client: Boto3 Bedrock Agent client
        config: Configuration dictionary
        
    Returns:
        Dictionary with setup results
    """
    decision_agent = config['decision_agent']
    agent_id = decision_agent['agent_id']
    
    print(f"🔧 Setting up multi-agent collaboration for Decision Agent: {agent_id}")
    
    try:
        # 1. Update Decision Agent to enable collaboration
        print(f"   📋 Enabling collaboration mode for Decision Agent...")
        
        # Get current agent configuration
        current_agent = bedrock_agent_client.get_agent(agentId=agent_id)['agent']
        
        # Update agent with collaboration enabled
        update_response = bedrock_agent_client.update_agent(
            agentId=agent_id,
            agentName=current_agent['agentName'],
            instruction=current_agent['instruction'],
            foundationModel=current_agent['foundationModel'],
            agentResourceRoleArn=current_agent['agentResourceRoleArn'],
            agentCollaboration='SUPERVISOR',  # Enable as supervisor
            idleSessionTTLInSeconds=current_agent.get('idleSessionTTLInSeconds', 600),
            description=current_agent.get('description', '')
        )
        
        print(f"   ✅ Decision Agent updated with SUPERVISOR collaboration mode")
        
        # 2. Add collaborators
        results = []
        
        for collaborator in decision_agent.get('collaborators', []):
            print(f"   🤝 Adding collaborator: {collaborator['collaborator_name']}")
            
            try:
                # Associate agent collaborator
                collab_response = bedrock_agent_client.associate_agent_collaborator(
                    agentId=agent_id,
                    agentVersion='DRAFT',
                    agentDescriptor={
                        'aliasArn': collaborator['agent_alias_arn']
                    },
                    collaboratorName=collaborator['collaborator_name'],
                    collaborationInstruction=collaborator['collaboration_instruction'],
                    relayConversationHistory=collaborator.get('relay_conversation_history', 'TO_COLLABORATOR')
                )
                
                results.append({
                    'collaborator': collaborator['collaborator_name'],
                    'collaborator_id': collab_response['agentCollaborator']['collaboratorId'],
                    'status': 'success'
                })
                
                print(f"     ✅ {collaborator['collaborator_name']} added successfully")
                print(f"     📝 Collaborator ID: {collab_response['agentCollaborator']['collaboratorId']}")
                
            except Exception as e:
                error_msg = str(e)
                if 'already exists' in error_msg.lower():
                    print(f"     ⚠️  {collaborator['collaborator_name']} already exists as collaborator")
                    results.append({
                        'collaborator': collaborator['collaborator_name'],
                        'status': 'already_exists'
                    })
                else:
                    print(f"     ❌ Error adding {collaborator['collaborator_name']}: {error_msg}")
                    results.append({
                        'collaborator': collaborator['collaborator_name'],
                        'status': 'error',
                        'error': error_msg
                    })
        
        # 3. Prepare the agent
        print(f"   🔄 Preparing Decision Agent...")
        prepare_response = bedrock_agent_client.prepare_agent(agentId=agent_id)
        
        # Wait for preparation to complete
        max_wait = 300  # 5 minutes
        wait_time = 0
        
        while wait_time < max_wait:
            agent_status = bedrock_agent_client.get_agent(agentId=agent_id)['agent']['agentStatus']
            
            if agent_status == 'PREPARED':
                print(f"   ✅ Decision Agent prepared successfully")
                break
            elif agent_status == 'FAILED':
                print(f"   ❌ Decision Agent preparation failed")
                break
            else:
                print(f"   ⏳ Agent status: {agent_status}, waiting...")
                time.sleep(10)
                wait_time += 10
        
        return {
            'success': True,
            'agent_id': agent_id,
            'collaboration_mode': 'SUPERVISOR',
            'collaborators': results,
            'preparation_status': agent_status,
            'message': 'Multi-agent collaboration configured successfully'
        }
        
    except Exception as e:
        print(f"   ❌ Error setting up multi-agent collaboration: {str(e)}")
        return {
            'success': False,
            'agent_id': agent_id,
            'error': str(e),
            'message': 'Failed to configure multi-agent collaboration'
        }

def verify_collaboration_setup(
    bedrock_agent_client: Any,
    agent_id: str
) -> Dict[str, Any]:
    """
    Verify that multi-agent collaboration is properly set up
    
    Args:
        bedrock_agent_client: Boto3 Bedrock Agent client
        agent_id: Decision Agent ID
        
    Returns:
        Dictionary with verification results
    """
    print(f"🔍 Verifying multi-agent collaboration setup...")
    
    try:
        # Check agent collaboration status
        agent = bedrock_agent_client.get_agent(agentId=agent_id)['agent']
        collaboration_mode = agent.get('agentCollaboration', 'DISABLED')
        
        print(f"   📋 Agent collaboration mode: {collaboration_mode}")
        
        if collaboration_mode != 'SUPERVISOR':
            return {
                'success': False,
                'message': f'Expected SUPERVISOR mode, got {collaboration_mode}'
            }
        
        # List collaborators
        collaborators = bedrock_agent_client.list_agent_collaborators(
            agentId=agent_id,
            agentVersion='DRAFT'
        )
        
        collab_count = len(collaborators['agentCollaboratorSummaries'])
        print(f"   🤝 Found {collab_count} collaborators:")
        
        for collab in collaborators['agentCollaboratorSummaries']:
            print(f"     - {collab['collaboratorName']} (ID: {collab['collaboratorId']})")
        
        return {
            'success': True,
            'collaboration_mode': collaboration_mode,
            'collaborator_count': collab_count,
            'collaborators': [
                {
                    'name': c['collaboratorName'],
                    'id': c['collaboratorId'],
                    'agent_descriptor': c['agentDescriptor']
                }
                for c in collaborators['agentCollaboratorSummaries']
            ],
            'message': 'Multi-agent collaboration verified successfully'
        }
        
    except Exception as e:
        print(f"   ❌ Error verifying collaboration setup: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to verify multi-agent collaboration'
        }

def main():
    """Main deployment function"""
    print("🚀 RevOps AI Framework V2 - Multi-Agent Collaboration Deployment")
    print("=" * 80)
    
    try:
        # Load configuration
        config = load_config()
        
        # Initialize AWS clients
        session = boto3.Session(
            profile_name=config['profile_name'],
            region_name=config['region_name']
        )
        
        bedrock_agent = session.client('bedrock-agent')
        
        # Deploy multi-agent collaboration
        setup_result = setup_multi_agent_collaboration(bedrock_agent, config)
        
        if setup_result['success']:
            print(f"\n✅ Multi-agent collaboration setup completed successfully!")
            
            # Verify the setup
            verification = verify_collaboration_setup(
                bedrock_agent, 
                config['decision_agent']['agent_id']
            )
            
            if verification['success']:
                print(f"\n🎯 Verification Results:")
                print(f"   Collaboration Mode: {verification['collaboration_mode']}")
                print(f"   Collaborators: {verification['collaborator_count']}")
                
                print(f"\n📋 Summary:")
                print(f"   Decision Agent: {config['decision_agent']['agent_id']} (SUPERVISOR)")
                for collab in verification['collaborators']:
                    print(f"   Collaborator: {collab['name']} (ID: {collab['id']})")
                
                print(f"\n🎉 Multi-agent collaboration is ready for testing!")
                
            else:
                print(f"\n⚠️  Setup completed but verification failed:")
                print(f"   {verification['message']}")
                
        else:
            print(f"\n❌ Multi-agent collaboration setup failed:")
            print(f"   {setup_result['message']}")
            if 'error' in setup_result:
                print(f"   Error: {setup_result['error']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Deployment failed with error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()