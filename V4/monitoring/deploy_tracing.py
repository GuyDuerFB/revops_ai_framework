#!/usr/bin/env python3
"""
Deploy Agent Tracing Integration
Updates all Lambda functions to include the agent_tracer.py library
"""

import os
import sys
import json
import boto3
import zipfile
import tempfile
import shutil
from pathlib import Path

# Configuration
AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"

# Lambda functions that need tracing
LAMBDA_FUNCTIONS = [
    "revops-manager-agent",
    "revops-deal-analysis-agent", 
    "revops-data-agent",
    "revops-web-search-agent",
    "revops-execution-agent",
    "revops-firebolt-query",
    "revops-gong-retrieval",
    "revops-slack-bedrock-processor"
]

def create_deployment_package_with_tracer(lambda_function_name: str) -> str:
    """Create deployment package including agent_tracer.py"""
    
    print(f"📦 Creating deployment package for {lambda_function_name}")
    
    # Create temporary directory
    temp_dir = Path(f"/tmp/{lambda_function_name}_tracing_deployment")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    try:
        # Get current function code
        session = boto3.Session(profile_name=AWS_PROFILE)
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        code_location = response['Code']['Location']
        
        # Download current code
        import urllib.request
        urllib.request.urlretrieve(code_location, str(temp_dir / "current_code.zip"))
        
        # Extract current code
        with zipfile.ZipFile(temp_dir / "current_code.zip", 'r') as zip_ref:
            zip_ref.extractall(temp_dir / "extracted")
        
        # Copy agent_tracer.py to monitoring directory within package
        monitoring_dir = temp_dir / "extracted" / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        tracer_source = Path(__file__).parent / "agent_tracer.py"
        tracer_dest = monitoring_dir / "agent_tracer.py"
        shutil.copy2(tracer_source, tracer_dest)
        
        # Create __init__.py for monitoring module
        (monitoring_dir / "__init__.py").write_text("")
        
        # Create new deployment package
        package_path = temp_dir / f"{lambda_function_name}_with_tracing.zip"
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            extracted_dir = temp_dir / "extracted"
            for file in extracted_dir.rglob("*"):
                if file.is_file():
                    zipf.write(file, file.relative_to(extracted_dir))
        
        print(f"✅ Package created: {package_path}")
        return str(package_path)
        
    except Exception as e:
        print(f"❌ Error creating package for {lambda_function_name}: {str(e)}")
        return None
    
def update_lambda_function(lambda_function_name: str, package_path: str):
    """Update Lambda function with new package including tracer"""
    
    print(f"🔄 Updating {lambda_function_name} with tracing integration...")
    
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        
        with open(package_path, 'rb') as f:
            lambda_client.update_function_code(
                FunctionName=lambda_function_name,
                ZipFile=f.read()
            )
        
        print(f"✅ {lambda_function_name} updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {lambda_function_name}: {str(e)}")
        return False

def verify_tracing_integration(lambda_function_name: str):
    """Verify tracing integration by invoking function with test event"""
    
    print(f"🧪 Verifying tracing integration for {lambda_function_name}...")
    
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        lambda_client = session.client('lambda', region_name=AWS_REGION)
        
        # Create test event with correlation_id
        test_event = {
            "correlation_id": f"test-tracing-{lambda_function_name}",
            "query": "Test tracing integration",
            "test": True
        }
        
        response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            Payload=json.dumps(test_event),
            InvocationType='RequestResponse'
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print(f"✅ {lambda_function_name} tracing verification successful")
            return True
        else:
            print(f"⚠️  {lambda_function_name} returned status {response['StatusCode']}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying {lambda_function_name}: {str(e)}")
        return False

def check_log_groups():
    """Check that required log groups exist"""
    
    print("📋 Checking CloudWatch log groups...")
    
    required_log_groups = [
        '/aws/revops-ai/conversation-trace',
        '/aws/revops-ai/agent-collaboration',
        '/aws/revops-ai/data-operations', 
        '/aws/revops-ai/decision-logic',
        '/aws/revops-ai/error-analysis'
    ]
    
    try:
        session = boto3.Session(profile_name=AWS_PROFILE)
        logs_client = session.client('logs', region_name=AWS_REGION)
        
        existing_groups = []
        paginator = logs_client.get_paginator('describe_log_groups')
        
        for page in paginator.paginate():
            for group in page['logGroups']:
                existing_groups.append(group['logGroupName'])
        
        missing_groups = []
        for group in required_log_groups:
            if group not in existing_groups:
                missing_groups.append(group)
            else:
                print(f"✅ Log group exists: {group}")
        
        if missing_groups:
            print(f"⚠️  Missing log groups: {missing_groups}")
            print("Run deploy-agent-tracing.py to create missing log groups")
            return False
        
        print("✅ All required log groups exist")
        return True
        
    except Exception as e:
        print(f"❌ Error checking log groups: {str(e)}")
        return False

def main():
    """Deploy tracing integration to all Lambda functions"""
    
    print("🚀 Deploying Agent Tracing Integration")
    print("=" * 60)
    
    # Check prerequisites
    if not check_log_groups():
        print("❌ Please ensure all log groups exist before deploying tracing")
        return False
    
    successful_deployments = []
    failed_deployments = []
    
    for function_name in LAMBDA_FUNCTIONS:
        print(f"\n🔧 Processing {function_name}...")
        
        try:
            # Create package with tracer
            package_path = create_deployment_package_with_tracer(function_name)
            if not package_path:
                failed_deployments.append(function_name)
                continue
            
            # Update function
            if update_lambda_function(function_name, package_path):
                # Verify integration
                if verify_tracing_integration(function_name):
                    successful_deployments.append(function_name)
                else:
                    failed_deployments.append(function_name)
            else:
                failed_deployments.append(function_name)
            
            # Clean up package
            if os.path.exists(package_path):
                os.remove(package_path)
                
        except Exception as e:
            print(f"❌ Error processing {function_name}: {str(e)}")
            failed_deployments.append(function_name)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 60)
    
    if successful_deployments:
        print(f"✅ Successfully deployed tracing to {len(successful_deployments)} functions:")
        for func in successful_deployments:
            print(f"   - {func}")
    
    if failed_deployments:
        print(f"\n❌ Failed to deploy tracing to {len(failed_deployments)} functions:")
        for func in failed_deployments:
            print(f"   - {func}")
    
    if successful_deployments and not failed_deployments:
        print(f"\n🎉 All {len(LAMBDA_FUNCTIONS)} functions updated successfully!")
        print("\n📋 Next steps:")
        print("1. Send a test message to RevBot via Slack")
        print("2. Check CloudWatch log groups for tracing data:")
        for group in ['/aws/revops-ai/conversation-trace', '/aws/revops-ai/agent-collaboration', 
                     '/aws/revops-ai/data-operations', '/aws/revops-ai/decision-logic', '/aws/revops-ai/error-analysis']:
            print(f"   - {group}")
        print("\n3. Use CloudWatch Logs Insights for analysis:")
        print("   - Filter by correlation_id to trace complete conversations")
        print("   - Analyze agent collaboration patterns")
        print("   - Monitor data operation performance")
        
        return True
    else:
        print(f"\n⚠️  Partial deployment: {len(successful_deployments)}/{len(LAMBDA_FUNCTIONS)} functions updated")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)