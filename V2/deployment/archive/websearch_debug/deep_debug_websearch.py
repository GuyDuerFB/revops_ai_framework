#!/usr/bin/env python3
"""
Deep Debug WebSearch Agent
=========================

Deep debugging to identify the exact issue preventing function calling.
"""

import boto3
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def deep_debug_websearch():
    """Perform deep debugging of WebSearch Agent"""
    
    logger.info("🔍 Deep Debugging WebSearch Agent")
    logger.info("=" * 60)
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_agent = session.client('bedrock-agent')
    lambda_client = session.client('lambda')
    iam_client = session.client('iam')
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('web_search_agent', {}).get('agent_id')
    lambda_arn = None
    
    for action_group in config.get('web_search_agent', {}).get('action_groups', []):
        if action_group.get('name') == 'web_search':
            lambda_arn = action_group.get('lambda_arn')
            break
    
    logger.info(f"🤖 Agent ID: {agent_id}")
    logger.info(f"⚡ Lambda ARN: {lambda_arn}")
    
    # 1. Check Lambda function exists and permissions
    logger.info("\n🔧 1. Checking Lambda Function...")
    
    function_name = lambda_arn.split(':')[-1] if lambda_arn else None
    
    try:
        lambda_info = lambda_client.get_function(FunctionName=function_name)
        logger.info(f"  ✅ Lambda function exists: {function_name}")
        logger.info(f"  📊 Runtime: {lambda_info['Configuration']['Runtime']}")
        logger.info(f"  📊 Status: {lambda_info['Configuration']['State']}")
        
        # Check if Bedrock can invoke this Lambda
        try:
            policy = lambda_client.get_policy(FunctionName=function_name)
            policy_doc = json.loads(policy['Policy'])
            
            bedrock_permissions = []
            for statement in policy_doc.get('Statement', []):
                if 'bedrock' in statement.get('Principal', {}).get('Service', '').lower():
                    bedrock_permissions.append(statement)
            
            if bedrock_permissions:
                logger.info(f"  ✅ Bedrock permissions found: {len(bedrock_permissions)}")
            else:
                logger.warning("  ⚠️ No Bedrock permissions found for Lambda")
                
        except Exception as e:
            logger.warning(f"  ⚠️ Could not check Lambda permissions: {e}")
            
    except Exception as e:
        logger.error(f"  ❌ Lambda function issue: {e}")
    
    # 2. Check Action Group Details
    logger.info("\n⚙️ 2. Checking Action Group Configuration...")
    
    try:
        action_groups = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion="DRAFT"
        )
        
        for ag_summary in action_groups.get('actionGroupSummaries', []):
            ag_id = ag_summary['actionGroupId']
            
            ag_detail = bedrock_agent.get_agent_action_group(
                agentId=agent_id,
                agentVersion="DRAFT",
                actionGroupId=ag_id
            )
            
            ag = ag_detail['agentActionGroup']
            
            logger.info(f"  📋 Action Group: {ag.get('actionGroupName')}")
            logger.info(f"  📊 State: {ag.get('actionGroupState')}")
            logger.info(f"  ⚡ Lambda ARN: {ag.get('actionGroupExecutor', {}).get('lambda')}")
            
            # Check function schema
            schema = ag.get('functionSchema', {})
            functions = schema.get('functions', [])
            
            logger.info(f"  🔍 Functions defined: {len(functions)}")
            for func in functions:
                logger.info(f"    📞 {func.get('name')}: {func.get('description')[:50]}...")
                params = func.get('parameters', {})
                required_params = [k for k, v in params.items() if v.get('required')]
                logger.info(f"      📝 Required params: {required_params}")
    
    except Exception as e:
        logger.error(f"  ❌ Action group check failed: {e}")
    
    # 3. Check Agent Status and Permissions
    logger.info("\n🤖 3. Checking Agent Configuration...")
    
    try:
        agent_info = bedrock_agent.get_agent(agentId=agent_id)
        agent = agent_info['agent']
        
        logger.info(f"  📋 Agent Name: {agent.get('agentName')}")
        logger.info(f"  📊 Status: {agent.get('agentStatus')}")
        logger.info(f"  🧠 Foundation Model: {agent.get('foundationModel')}")
        logger.info(f"  🔑 Role ARN: {agent.get('agentResourceRoleArn')}")
        
        # Check if agent role can invoke Lambda
        role_arn = agent.get('agentResourceRoleArn')
        if role_arn:
            role_name = role_arn.split('/')[-1]
            try:
                role_policies = iam_client.list_attached_role_policies(RoleName=role_name)
                logger.info(f"  📋 Attached policies: {len(role_policies.get('AttachedPolicies', []))}")
                
                for policy in role_policies.get('AttachedPolicies', []):
                    logger.info(f"    📄 {policy.get('PolicyName')}")
                    
            except Exception as e:
                logger.warning(f"  ⚠️ Could not check role policies: {e}")
    
    except Exception as e:
        logger.error(f"  ❌ Agent check failed: {e}")
    
    # 4. Test Lambda Direct Invocation
    logger.info("\n⚡ 4. Testing Lambda Direct Invocation...")
    
    test_payload = {
        "function": "search_web",
        "actionGroup": "web_search", 
        "parameters": [
            {"name": "query", "value": "test search"},
            {"name": "num_results", "value": "3"}
        ]
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read().decode())
        
        logger.info(f"  📊 Status Code: {response['StatusCode']}")
        logger.info(f"  ✅ Lambda Response: {str(result)[:200]}...")
        
        if response['StatusCode'] == 200 and 'success' in result:
            logger.info("  ✅ Lambda function is working correctly")
        else:
            logger.warning("  ⚠️ Lambda function response unexpected")
            
    except Exception as e:
        logger.error(f"  ❌ Lambda invocation failed: {e}")
    
    # 5. Check for Common Issues
    logger.info("\n🔍 5. Checking for Common Issues...")
    
    # Issue 1: Function schema parameter types
    logger.info("  🔍 Checking parameter types in schema...")
    try:
        action_groups = bedrock_agent.list_agent_action_groups(
            agentId=agent_id,
            agentVersion="DRAFT"
        )
        
        ag_id = action_groups['actionGroupSummaries'][0]['actionGroupId']
        ag_detail = bedrock_agent.get_agent_action_group(
            agentId=agent_id,
            agentVersion="DRAFT", 
            actionGroupId=ag_id
        )
        
        schema = ag_detail['agentActionGroup'].get('functionSchema', {})
        
        for func in schema.get('functions', []):
            for param_name, param_def in func.get('parameters', {}).items():
                param_type = param_def.get('type')
                if param_type == 'integer':
                    logger.warning(f"    ⚠️ Found integer parameter: {param_name} (should be string)")
                elif param_type == 'string':
                    logger.info(f"    ✅ String parameter: {param_name}")
                    
    except Exception as e:
        logger.error(f"  ❌ Schema check failed: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 Deep Debug Complete")

def main():
    deep_debug_websearch()

if __name__ == "__main__":
    main()