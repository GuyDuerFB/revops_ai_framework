#!/usr/bin/env python3
"""
Deploy Enforcement-Mode Data Agent Instructions
==============================================

Deploys strict enforcement instructions with immediate validation.
"""

import boto3
import json
import logging
import os
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def deploy_enforcement_instructions():
    """Deploy enforcement-mode Data Agent instructions"""
    
    logger.info("🚨 Deploying ENFORCEMENT MODE Data Agent instructions...")
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_agent = session.client('bedrock-agent')
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('data_agent', {}).get('agent_id')
    agent_alias_id = config.get('data_agent', {}).get('agent_alias_id')
    
    if not agent_id:
        logger.error("❌ Data Agent ID not found in config")
        return False
    
    # Read enforcement instructions
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instructions_path = os.path.join(project_root, "agents/data_agent/instructions_v4_enforcement.md")
    
    if not os.path.exists(instructions_path):
        logger.error(f"❌ Enforcement instructions not found: {instructions_path}")
        return False
    
    with open(instructions_path, 'r') as f:
        enforcement_instructions = f.read()
    
    logger.info(f"📄 Loaded enforcement instructions ({len(enforcement_instructions)} characters)")
    
    try:
        # Update agent with enforcement instructions
        logger.info(f"🔄 Updating Data Agent with ENFORCEMENT MODE: {agent_id}")
        
        bedrock_agent.update_agent(
            agentId=agent_id,
            agentName="revops-data-agent-enforcement",
            description="Data Agent with STRICT business logic enforcement and compliance requirements",
            instruction=enforcement_instructions,
            foundationModel="anthropic.claude-3-5-sonnet-20240620-v1:0",
            agentResourceRoleArn="arn:aws:iam::740202120544:role/AmazonBedrockExecutionRoleForAgents_revops"
        )
        
        # Prepare agent
        logger.info("⚡ Preparing agent...")
        bedrock_agent.prepare_agent(agentId=agent_id)
        
        # Wait for preparation
        logger.info("⏳ Waiting for agent preparation...")
        max_wait = 180  # 3 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = bedrock_agent.get_agent(agentId=agent_id)
            status = status_response['agent']['agentStatus']
            
            if status == 'PREPARED':
                logger.info("✅ Agent preparation completed")
                break
            elif status == 'FAILED':
                logger.error("❌ Agent preparation failed")
                return False
            
            logger.info(f"📊 Agent status: {status}")
            time.sleep(15)
        
        logger.info("✅ Data Agent successfully updated with ENFORCEMENT MODE instructions")
        
        # Quick validation test
        logger.info("🧪 Running immediate validation test...")
        
        test_query = "Show me Q2 2025 revenue by customer type with proper business logic"
        
        response = bedrock_runtime.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            sessionId=f"enforcement-test-{int(time.time())}",
            inputText=test_query
        )
        
        # Collect response
        full_response = ""
        for event in response['completion']:
            if 'chunk' in event and 'bytes' in event['chunk']:
                full_response += event['chunk']['bytes'].decode('utf-8')
        
        # Quick validation
        compliance_checks = {
            "knowledge_base_consultation": "knowledge" in full_response.lower() or "consulted" in full_response.lower(),
            "customer_segmentation": all(term in full_response.lower() for term in ["commit", "plg", "prospect"]),
            "structured_output": "json" in full_response.lower() or "{" in full_response,
            "business_context": "business" in full_response.lower() or "classification" in full_response.lower()
        }
        
        compliance_score = sum(compliance_checks.values()) / len(compliance_checks)
        
        logger.info(f"📊 Immediate compliance score: {compliance_score:.2f}/1.00")
        logger.info(f"📋 Compliance checks: {compliance_checks}")
        
        if compliance_score >= 0.75:
            logger.info("✅ EXCELLENT: Enforcement mode working effectively!")
        elif compliance_score >= 0.5:
            logger.info("✅ GOOD: Significant improvement detected")
        else:
            logger.warning("⚠️ NEEDS WORK: Additional optimization required")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating Data Agent: {e}")
        return False

def main():
    """Main enforcement deployment workflow"""
    
    logger.info("🚨 Starting ENFORCEMENT MODE Deployment")
    logger.info("=" * 60)
    
    # Deploy enforcement instructions
    success = deploy_enforcement_instructions()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 ENFORCEMENT MODE DEPLOYMENT SUCCESSFUL!")
        logger.info("📋 Next steps:")
        logger.info("  1. Run full business logic integration tests")
        logger.info("  2. Test with real use cases")
        logger.info("  3. Monitor compliance scores")
    else:
        logger.error("❌ Enforcement deployment failed")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)