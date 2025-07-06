#!/usr/bin/env python3
"""
Comprehensive diagnostic for Bedrock access issues
"""
import json
import boto3

AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"
PROJECT_NAME = "revops-slack-bedrock"
BEDROCK_AGENT_ID = "TCX9CGOKBR"
BEDROCK_AGENT_ALIAS_ID = "FUKETW8HXV"

def diagnose_lambda_role():
    """Diagnose Lambda role permissions"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        iam_client = session.client('iam', region_name=AWS_REGION)
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        
        # Get Lambda role
        response = lambda_client.get_function(FunctionName=f"{PROJECT_NAME}-processor")
        role_arn = response['Configuration']['Role']
        role_name = role_arn.split('/')[-1]
        
        print(f"🔍 Lambda Role: {role_name}")
        print(f"   ARN: {role_arn}")
        
        # List attached policies
        policies = iam_client.list_attached_role_policies(RoleName=role_name)
        print("📋 Attached Policies:")
        for policy in policies['AttachedPolicies']:
            print(f"   - {policy['PolicyName']}: {policy['PolicyArn']}")
            
            # Get policy details if it's our custom policy
            if 'BedrockAgentAccess' in policy['PolicyName']:
                policy_response = iam_client.get_policy_version(
                    PolicyArn=policy['PolicyArn'],
                    VersionId='$Default'
                )
                print(f"     Policy Document:")
                print(f"     {json.dumps(policy_response['PolicyVersion']['Document'], indent=6)}")
        
        # Check trust relationship
        role_response = iam_client.get_role(RoleName=role_name)
        trust_policy = role_response['Role']['AssumeRolePolicyDocument']
        print("🤝 Trust Policy:")
        print(f"   {json.dumps(trust_policy, indent=3)}")
        
        return role_arn
        
    except Exception as e:
        print(f"❌ Error diagnosing Lambda role: {e}")
        return None

def diagnose_bedrock_agent():
    """Diagnose Bedrock agent configuration"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        bedrock_client = session.client('bedrock-agent', region_name=AWS_REGION)
        
        # Get agent details
        agent_response = bedrock_client.get_agent(agentId=BEDROCK_AGENT_ID)
        agent = agent_response['agent']
        
        print(f"🤖 Bedrock Agent: {agent['agentName']}")
        print(f"   ID: {agent['agentId']}")
        print(f"   Status: {agent['agentStatus']}")
        print(f"   Foundation Model: {agent['foundationModel']}")
        print(f"   Agent Role ARN: {agent['agentResourceRoleArn']}")
        
        # Get agent alias
        alias_response = bedrock_client.get_agent_alias(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID
        )
        alias = alias_response['agentAlias']
        
        print(f"🏷️  Agent Alias: {alias['agentAliasName']}")
        print(f"   Alias ID: {alias['agentAliasId']}")
        print(f"   Status: {alias['agentAliasStatus']}")
        
        return agent['agentResourceRoleArn']
        
    except Exception as e:
        print(f"❌ Error diagnosing Bedrock agent: {e}")
        return None

def diagnose_bedrock_permissions():
    """Check if current credentials can access Bedrock"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        
        # Test basic Bedrock access
        bedrock_client = session.client('bedrock', region_name=AWS_REGION)
        foundation_models = bedrock_client.list_foundation_models()
        print(f"✅ Bedrock basic access: Found {len(foundation_models['modelSummaries'])} foundation models")
        
        # Test agent runtime access
        bedrock_runtime = session.client('bedrock-agent-runtime', region_name=AWS_REGION)
        print("✅ Bedrock Agent Runtime client created successfully")
        
        # Try to invoke the agent
        try:
            response = bedrock_runtime.invoke_agent(
                agentId=BEDROCK_AGENT_ID,
                agentAliasId=BEDROCK_AGENT_ALIAS_ID,
                sessionId="diagnostic-test-session",
                inputText="Hello, this is a diagnostic test"
            )
            
            # Try to read one event from the stream
            for event in response['completion']:
                print("✅ Bedrock agent invocation successful!")
                break
                
        except Exception as e:
            print(f"❌ Bedrock agent invocation failed: {e}")
            
            # Check if it's a specific permission issue
            if "accessDeniedException" in str(e):
                print("🔍 This appears to be a permissions issue")
                return False
            elif "ValidationException" in str(e):
                print("🔍 This appears to be a validation issue (agent/alias not found)")
                return False
            else:
                print(f"🔍 Unknown error type: {type(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Bedrock permissions: {e}")
        return False

def suggest_fixes(lambda_role_arn, agent_role_arn):
    """Suggest potential fixes based on diagnosis"""
    print("\n🔧 SUGGESTED FIXES:")
    print("=" * 50)
    
    if lambda_role_arn and agent_role_arn:
        print("1. Ensure Lambda role can invoke Bedrock agents:")
        print(f"   aws iam attach-role-policy --role-name {lambda_role_arn.split('/')[-1]} \\")
        print(f"     --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess")
        
        print("\n2. Verify Bedrock service is enabled in this region:")
        print(f"   Check AWS Console > Bedrock > Model access in {AWS_REGION}")
        
        print("\n3. Test direct agent invocation:")
        print(f"   aws bedrock-agent-runtime invoke-agent \\")
        print(f"     --agent-id {BEDROCK_AGENT_ID} \\")
        print(f"     --agent-alias-id {BEDROCK_AGENT_ALIAS_ID} \\")
        print(f"     --session-id test-session \\")
        print(f"     --input-text 'Hello' \\")
        print(f"     --region {AWS_REGION}")
        
        print("\n4. Alternative: Use managed policy for comprehensive access:")
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "bedrock:*",
                    "Resource": "*"
                }
            ]
        }
        print(f"   Policy document: {json.dumps(bedrock_policy, indent=3)}")

def main():
    """Main diagnostic function"""
    print("🔍 Bedrock Access Diagnostic")
    print("=" * 50)
    
    # Diagnose Lambda role
    print("\n1. LAMBDA ROLE ANALYSIS:")
    lambda_role_arn = diagnose_lambda_role()
    
    print("\n2. BEDROCK AGENT ANALYSIS:")
    agent_role_arn = diagnose_bedrock_agent()
    
    print("\n3. BEDROCK PERMISSIONS TEST:")
    bedrock_works = diagnose_bedrock_permissions()
    
    # Suggest fixes
    suggest_fixes(lambda_role_arn, agent_role_arn)
    
    if bedrock_works:
        print("\n✅ DIAGNOSIS: Bedrock works with current credentials")
        print("   The issue may be with Lambda environment or role assumptions")
    else:
        print("\n❌ DIAGNOSIS: Bedrock access issue detected")
        print("   This explains why Lambda is failing")

if __name__ == "__main__":
    main()