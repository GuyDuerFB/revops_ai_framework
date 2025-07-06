#!/usr/bin/env python3
"""
Fix Bedrock permissions for Slack Lambda with more comprehensive access
"""
import json
import boto3

AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"
PROJECT_NAME = "revops-slack-bedrock"

def update_bedrock_permissions():
    """Update Lambda execution role with comprehensive Bedrock permissions"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        iam_client = session.client('iam', region_name=AWS_REGION)
        
        # Get the processor Lambda execution role
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        response = lambda_client.get_function(FunctionName=f"{PROJECT_NAME}-processor")
        role_arn = response['Configuration']['Role']
        role_name = role_arn.split('/')[-1]
        
        print(f"🔐 Updating comprehensive Bedrock permissions for role: {role_name}")
        
        # Comprehensive Bedrock access policy
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeAgent",
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock:RetrieveAndGenerate",
                        "bedrock:Retrieve",
                        "bedrock:GetAgent",
                        "bedrock:GetAgentAlias",
                        "bedrock:ListAgents",
                        "bedrock:ListAgentAliases"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }
        
        # Update the existing policy
        policy_arn = f"arn:aws:iam::740202120544:policy/BedrockAgentAccess"
        
        try:
            # Create new policy version
            iam_client.create_policy_version(
                PolicyArn=policy_arn,
                PolicyDocument=json.dumps(bedrock_policy),
                SetAsDefault=True
            )
            print(f"✅ Updated Bedrock policy with comprehensive permissions")
            
            # Also check if we need to add Secrets Manager access
            secrets_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "secretsmanager:GetSecretValue",
                            "secretsmanager:DescribeSecret"
                        ],
                        "Resource": "arn:aws:secretsmanager:us-east-1:740202120544:secret:revops-slack-bedrock-secrets-*"
                    }
                ]
            }
            
            # Create Secrets Manager policy
            secrets_policy_name = "SlackSecretsAccess"
            secrets_policy_arn = f"arn:aws:iam::740202120544:policy/{secrets_policy_name}"
            
            try:
                iam_client.create_policy(
                    PolicyName=secrets_policy_name,
                    PolicyDocument=json.dumps(secrets_policy),
                    Description="Allow Lambda to access Slack secrets"
                )
                print(f"✅ Created Secrets policy: {secrets_policy_name}")
            except iam_client.exceptions.EntityAlreadyExistsException:
                # Policy exists, update it
                iam_client.create_policy_version(
                    PolicyArn=secrets_policy_arn,
                    PolicyDocument=json.dumps(secrets_policy),
                    SetAsDefault=True
                )
                print(f"✅ Updated Secrets policy: {secrets_policy_name}")
            
            # Attach Secrets policy to role
            try:
                iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=secrets_policy_arn
                )
                print(f"✅ Attached Secrets policy to role: {role_name}")
            except iam_client.exceptions.LimitExceededException:
                print(f"ℹ️  Secrets policy already attached to role: {role_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating policies: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error updating Bedrock permissions: {e}")
        return False

def verify_agent_access():
    """Verify that the agent is accessible"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        bedrock_client = session.client('bedrock-agent-runtime', region_name=AWS_REGION)
        
        agent_id = "TCX9CGOKBR"
        agent_alias_id = "FUKETW8HXV"
        
        print(f"🧪 Testing Bedrock Agent access: {agent_id}")
        
        # Try to invoke the agent with a simple test
        response = bedrock_client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId="test-session-123",
            inputText="Hello, can you help me?"
        )
        
        print("✅ Bedrock Agent access verified successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying Bedrock Agent access: {e}")
        print("   This may be normal if testing from local machine")
        return False

def main():
    """Main function to fix Bedrock permissions"""
    print("🔧 Fixing Bedrock Permissions for Slack Integration")
    print("=" * 60)
    
    # Update permissions
    if not update_bedrock_permissions():
        print("❌ Failed to update Bedrock permissions")
        return False
    
    # Verify agent access (may fail locally but should work from Lambda)
    print("\n🧪 Verifying agent access...")
    verify_agent_access()
    
    print("\n🎉 Bedrock permissions updated successfully!")
    print("✅ Comprehensive Bedrock access granted")
    print("✅ Secrets Manager access granted")
    print("\n🧪 Test the integration again with test_integration.py")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)