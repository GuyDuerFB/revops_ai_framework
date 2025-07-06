#!/usr/bin/env python3
"""
Fix Lambda Permissions for New WebSearch Agent
==============================================

Adds the necessary permissions for the new WebSearch Agent to invoke Lambda.
"""

import boto3
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fix_lambda_permissions():
    """Add permission for new agent to invoke Lambda"""
    
    logger.info("🔧 Fixing Lambda Permissions for New WebSearch Agent")
    logger.info("=" * 60)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    lambda_client = session.client('lambda')
    
    # Load new agent config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    new_agent_id = config.get('web_search_agent', {}).get('agent_id')
    lambda_function_name = "revops-web-search"
    account_id = "740202120544"
    
    logger.info(f"📋 Agent ID: {new_agent_id}")
    logger.info(f"🔗 Lambda Function: {lambda_function_name}")
    
    try:
        # Add permission for new agent to invoke Lambda
        statement_id = f"allow-bedrock-agent-{new_agent_id}"
        
        logger.info("🔒 Adding Lambda permission for new agent...")
        
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=statement_id,
            Action='lambda:InvokeFunction',
            Principal='bedrock.amazonaws.com',
            SourceArn=f"arn:aws:bedrock:us-east-1:{account_id}:agent/{new_agent_id}",
            SourceAccount=account_id
        )
        
        logger.info("✅ Lambda permission added successfully")
        
        # Verify the permission was added
        logger.info("🔍 Verifying Lambda permissions...")
        
        policy_response = lambda_client.get_policy(FunctionName=lambda_function_name)
        policy = json.loads(policy_response['Policy'])
        
        # Check if our permission exists
        permission_found = False
        for statement in policy.get('Statement', []):
            if statement.get('Sid') == statement_id:
                permission_found = True
                logger.info(f"✅ Permission verified: {statement_id}")
                break
        
        if not permission_found:
            logger.warning("⚠️ Permission may not have been added correctly")
        
        return True
        
    except lambda_client.exceptions.ResourceConflictException:
        logger.info("✅ Permission already exists, continuing...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error adding Lambda permission: {e}")
        return False

def test_new_agent():
    """Test the new agent with proper permissions"""
    
    logger.info("🧪 Testing New WebSearch Agent")
    logger.info("=" * 40)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load agent config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('web_search_agent', {}).get('agent_id')
    agent_alias_id = config.get('web_search_agent', {}).get('agent_alias_id')
    
    try:
        import time
        session_id = f"test-fixed-agent-{int(time.time())}"
        
        logger.info("📞 Invoking new agent...")
        
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=session_id,
            inputText="Use your search_web function to search for 'WINN.AI company information'"
        )
        
        # Check for function calls and errors
        function_calls_detected = 0
        response_text = ""
        errors = []
        
        for event in response['completion']:
            if 'chunk' in event and 'bytes' in event['chunk']:
                response_text += event['chunk']['bytes'].decode('utf-8')
            
            if 'trace' in event:
                trace = event['trace']
                if 'orchestrationTrace' in trace:
                    orch_trace = trace['orchestrationTrace']
                    if 'invocationInput' in orch_trace:
                        inv_input = orch_trace['invocationInput']
                        if 'actionGroupInvocationInput' in inv_input:
                            function_calls_detected += 1
                            ag_input = inv_input['actionGroupInvocationInput']
                            logger.info(f"🎯 Function call detected: {ag_input.get('function')}")
            
            # Check for errors
            if 'dependencyFailedException' in event:
                errors.append("Dependency Failed Exception")
            if 'internalServerException' in event:
                errors.append("Internal Server Exception")
        
        logger.info(f"\n📊 Test Results:")
        logger.info(f"   Function calls: {function_calls_detected}")
        logger.info(f"   Errors: {len(errors)}")
        logger.info(f"   Response length: {len(response_text)}")
        
        if errors:
            logger.error(f"❌ Test failed with errors: {errors}")
            return False
        elif function_calls_detected > 0:
            logger.info("🎉 SUCCESS: New agent is calling functions!")
            logger.info(f"📝 Response preview: {response_text[:200]}...")
            return True
        else:
            logger.warning("⚠️ No function calls detected, but no errors either")
            logger.info(f"📝 Response preview: {response_text[:200]}...")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing new agent: {e}")
        return False

def main():
    # Fix permissions
    permissions_fixed = fix_lambda_permissions()
    
    if not permissions_fixed:
        logger.error("❌ Failed to fix Lambda permissions")
        return False
    
    # Test the agent
    test_success = test_new_agent()
    
    if test_success:
        logger.info("\n🎉 NEW WEBSEARCH AGENT IS WORKING!")
        logger.info("=" * 50)
        logger.info("✅ Agent created and tested successfully")
        logger.info("✅ Function calling is working")
        logger.info("✅ Lambda permissions are correct")
        logger.info("\n📋 Ready for lead assessment testing!")
    else:
        logger.error("\n❌ New agent needs additional debugging")
    
    return test_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)