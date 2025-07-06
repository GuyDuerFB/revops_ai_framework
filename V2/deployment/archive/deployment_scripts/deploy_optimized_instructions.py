#!/usr/bin/env python3
"""
Deploy Optimized Data Agent Instructions
========================================

Deploys enhanced instructions and tests business logic integration.
"""

import boto3
import json
import logging
import os
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def deploy_optimized_instructions():
    """Deploy optimized Data Agent instructions"""
    
    logger.info("🚀 Deploying optimized Data Agent instructions...")
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_agent = session.client('bedrock-agent')
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('data_agent', {}).get('agent_id')
    if not agent_id:
        logger.error("❌ Data Agent ID not found in config")
        return False
    
    # Read optimized instructions
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    instructions_path = os.path.join(project_root, "agents/data_agent/instructions_v3_optimized.md")
    
    if not os.path.exists(instructions_path):
        logger.error(f"❌ Optimized instructions not found: {instructions_path}")
        return False
    
    with open(instructions_path, 'r') as f:
        optimized_instructions = f.read()
    
    logger.info(f"📄 Loaded optimized instructions ({len(optimized_instructions)} characters)")
    
    try:
        # Update agent with optimized instructions
        logger.info(f"🔄 Updating Data Agent: {agent_id}")
        
        bedrock_agent.update_agent(
            agentId=agent_id,
            agentName="revops-data-agent-optimized",
            description="Data Agent with enhanced business logic integration and optimization",
            instruction=optimized_instructions,
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
        
        logger.info("✅ Data Agent successfully updated with optimized instructions")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating Data Agent: {e}")
        return False

def run_optimization_validation():
    """Run quick validation test after deployment"""
    
    logger.info("🧪 Running optimization validation test...")
    
    try:
        # Import and run the business logic tester
        import subprocess
        result = subprocess.run(['python3', 'test_business_logic_integration.py'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("✅ Optimization validation completed successfully")
            return True
        else:
            logger.warning(f"⚠️ Validation completed with issues: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Validation test failed: {e}")
        return False

def main():
    """Main deployment and validation workflow"""
    
    logger.info("🚀 Starting Data Agent Optimization Deployment")
    logger.info("=" * 60)
    
    # Step 1: Deploy optimized instructions
    logger.info("📤 Step 1: Deploying optimized instructions...")
    if not deploy_optimized_instructions():
        logger.error("❌ Deployment failed")
        return False
    
    # Step 2: Wait for agent to be ready
    logger.info("⏳ Step 2: Waiting for agent stabilization...")
    time.sleep(30)  # Give agent time to fully process new instructions
    
    # Step 3: Run validation tests
    logger.info("🧪 Step 3: Running optimization validation...")
    validation_success = run_optimization_validation()
    
    # Summary
    logger.info("=" * 60)
    if validation_success:
        logger.info("🎉 OPTIMIZATION DEPLOYMENT SUCCESSFUL!")
        logger.info("✅ Data Agent updated with enhanced business logic integration")
        logger.info("✅ Validation tests passed")
        logger.info("📊 Check business_logic_optimization_report.md for detailed results")
    else:
        logger.warning("⚠️ Deployment completed but validation had issues")
        logger.info("📋 Manual testing recommended")
    
    logger.info("=" * 60)
    return validation_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)