#!/usr/bin/env python3
"""
Update Decision Agent Collaborators
==================================

Update the Decision Agent to use the new WebSearch Agent ID.
"""

import boto3
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def update_decision_agent_collaborators():
    """Update Decision Agent collaborators with new WebSearch Agent"""
    
    logger.info("🔧 Updating Decision Agent Collaborators")
    logger.info("=" * 60)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_agent = session.client('bedrock-agent')
    
    # Load current configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    decision_agent_id = config.get('decision_agent', {}).get('agent_id')
    new_websearch_agent_id = config.get('web_search_agent', {}).get('agent_id')
    new_websearch_alias_id = config.get('web_search_agent', {}).get('agent_alias_id')
    
    logger.info(f"🤖 Decision Agent ID: {decision_agent_id}")
    logger.info(f"🔍 New WebSearch Agent ID: {new_websearch_agent_id}")
    logger.info(f"🏷️ New WebSearch Alias ID: {new_websearch_alias_id}")
    
    if not all([decision_agent_id, new_websearch_agent_id, new_websearch_alias_id]):
        logger.error("❌ Missing required agent IDs")
        return False
    
    try:
        # Get current collaborators
        logger.info("📋 Getting current agent collaborators...")
        
        collaborators_response = bedrock_agent.list_agent_collaborators(
            agentId=decision_agent_id,
            agentVersion="DRAFT"
        )
        
        current_collaborators = collaborators_response.get('collaboratorSummaries', [])
        logger.info(f"📊 Found {len(current_collaborators)} current collaborators")
        
        # Find and update the WebSearch collaborator
        websearch_collaborator_id = None
        
        for collaborator in current_collaborators:
            if collaborator.get('collaboratorName') == 'WebSearchAgent':
                websearch_collaborator_id = collaborator.get('collaboratorId')
                logger.info(f"🔍 Found WebSearch collaborator: {websearch_collaborator_id}")
                break
        
        if not websearch_collaborator_id:
            logger.error("❌ WebSearch collaborator not found")
            return False
        
        # Update the WebSearch collaborator
        logger.info("🔄 Updating WebSearch collaborator...")
        
        new_alias_arn = f"arn:aws:bedrock:us-east-1:740202120544:agent-alias/{new_websearch_agent_id}/{new_websearch_alias_id}"
        
        update_response = bedrock_agent.update_agent_collaborator(
            agentId=decision_agent_id,
            agentVersion="DRAFT",
            collaboratorId=websearch_collaborator_id,
            agentDescriptor={
                'aliasArn': new_alias_arn
            }
        )
        
        logger.info("✅ WebSearch collaborator updated successfully")
        
        # Update configuration file
        logger.info("📝 Updating configuration file...")
        
        # Update the collaborator in config
        for collaborator in config['decision_agent']['collaborators']:
            if collaborator.get('collaborator_name') == 'WebSearchAgent':
                collaborator['agent_id'] = new_websearch_agent_id
                collaborator['agent_alias_arn'] = new_alias_arn
                logger.info(f"✅ Updated config for WebSearchAgent collaborator")
                break
        
        # Save updated configuration
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("✅ Configuration file updated")
        
        # Prepare the agent to activate changes
        logger.info("⚡ Preparing Decision Agent...")
        
        bedrock_agent.prepare_agent(agentId=decision_agent_id)
        
        logger.info("✅ Decision Agent prepared with new collaborator")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating collaborators: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_updated_decision_agent():
    """Test the Decision Agent with updated collaborators"""
    
    logger.info("\n🧪 Testing Updated Decision Agent")
    logger.info("=" * 50)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('decision_agent', {}).get('agent_id')
    agent_alias_id = config.get('decision_agent', {}).get('agent_alias_id')
    
    try:
        import time
        session_id = f"test-updated-decision-{int(time.time())}"
        
        # Simple test that should trigger WebSearch collaboration
        test_prompt = "Research WINN.AI company and provide a brief assessment."
        
        logger.info(f"📞 Testing with prompt: {test_prompt}")
        
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText=test_prompt,
            enableTrace=True
        )
        
        # Analyze response
        response_text = ""
        collaborations = []
        errors = []
        
        for event in response['completion']:
            if 'chunk' in event and 'bytes' in event['chunk']:
                response_text += event['chunk']['bytes'].decode('utf-8')
            
            if 'trace' in event:
                trace = event['trace']
                # Look for collaboration traces
                if 'trace' in trace:
                    trace_content = trace['trace']
                    if 'orchestrationTrace' in trace_content:
                        orch_trace = trace_content['orchestrationTrace']
                        if 'invocationInput' in orch_trace:
                            inv_input = orch_trace['invocationInput']
                            if 'collaboratorInvocationInput' in inv_input:
                                collaborations.append("Collaboration detected")
            
            # Check for errors
            if 'dependencyFailedException' in event:
                errors.append("Dependency Failed")
            if 'internalServerException' in event:
                errors.append("Internal Server Error")
        
        logger.info(f"📊 Test Results:")
        logger.info(f"   Response length: {len(response_text)}")
        logger.info(f"   Collaborations: {len(collaborations)}")
        logger.info(f"   Errors: {len(errors)}")
        
        if errors:
            logger.error(f"   ❌ Errors: {errors}")
            return False
        elif len(response_text) > 100:
            logger.info(f"   ✅ Good response received")
            logger.info(f"   📝 Preview: {response_text[:150]}...")
            return True
        else:
            logger.warning(f"   ⚠️ Short response: {response_text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return False

def main():
    """Update collaborators and test"""
    
    # Update collaborators
    update_success = update_decision_agent_collaborators()
    
    if not update_success:
        logger.error("❌ Failed to update Decision Agent collaborators")
        return False
    
    # Wait a moment for changes to propagate
    import time
    logger.info("⏳ Waiting for changes to propagate...")
    time.sleep(10)
    
    # Test the updated agent
    test_success = test_updated_decision_agent()
    
    if update_success and test_success:
        logger.info("\n🎉 Decision Agent Collaborator Update: SUCCESS!")
        logger.info("✅ WebSearch collaborator updated")
        logger.info("✅ Configuration file updated")
        logger.info("✅ Decision Agent test passed")
    else:
        logger.error("\n❌ Decision Agent Collaborator Update: ISSUES")
        if not update_success:
            logger.error("   - Collaborator update failed")
        if not test_success:
            logger.error("   - Agent test failed")
    
    return update_success and test_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)