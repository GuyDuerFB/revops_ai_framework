#!/usr/bin/env python3
"""
Enhanced Knowledge Base Upload Script
====================================

Uploads the enhanced knowledge base structure (business logic, workflows, etc.)
to AWS S3 and triggers knowledge base ingestion job.

Author: Claude (Anthropic)
Version: 1.0
"""

import argparse
import boto3
import json
import logging
import os
import time
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class EnhancedKnowledgeBaseUploader:
    """Upload enhanced knowledge base structure to AWS S3"""
    
    def __init__(self, profile_name: str = "revops-dev-profile"):
        """Initialize the uploader with AWS profile"""
        self.aws_profile = profile_name
        self.aws_region = "us-east-1"
        self.account_id = "740202120544"
        self.bucket_name = f"revops-ai-framework-kb-{self.account_id}"
        
        # Initialize AWS clients
        session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
        self.s3_client = session.client('s3')
        self.bedrock_agent_client = session.client('bedrock-agent')
        
        # Project paths
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.kb_root = os.path.join(self.project_root, "knowledge_base")
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def upload_knowledge_base_files(self) -> bool:
        """Upload all knowledge base files to S3"""
        logger.info(f"🚀 Uploading enhanced knowledge base to S3 bucket: {self.bucket_name}")
        
        try:
            # Check if bucket exists
            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info(f"✅ S3 bucket {self.bucket_name} exists")
            except Exception as e:
                logger.error(f"❌ S3 bucket {self.bucket_name} not found: {e}")
                return False
            
            # Upload files recursively
            uploaded_count = 0
            
            for root, dirs, files in os.walk(self.kb_root):
                for file in files:
                    if file.endswith(('.md', '.json', '.txt', '.yaml', '.yml')):
                        local_path = os.path.join(root, file)
                        
                        # Create S3 key (relative path from kb_root)
                        relative_path = os.path.relpath(local_path, self.kb_root)
                        s3_key = relative_path.replace(os.sep, '/')
                        
                        logger.info(f"📄 Uploading: {relative_path}")
                        
                        try:
                            self.s3_client.upload_file(
                                local_path,
                                self.bucket_name,
                                s3_key,
                                ExtraArgs={'ContentType': 'text/plain'}
                            )
                            uploaded_count += 1
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to upload {relative_path}: {e}")
                            return False
            
            logger.info(f"✅ Successfully uploaded {uploaded_count} files")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error uploading knowledge base: {e}")
            return False
    
    def trigger_ingestion_job(self) -> bool:
        """Trigger knowledge base ingestion job"""
        logger.info("🔄 Triggering knowledge base ingestion job...")
        
        try:
            # Get knowledge base ID from config
            kb_id = self.config.get('knowledge_base', {}).get('knowledge_base_id')
            if not kb_id:
                logger.error("❌ Knowledge base ID not found in configuration")
                return False
            
            # Find the data source
            data_sources = self.bedrock_agent_client.list_data_sources(knowledgeBaseId=kb_id)
            
            if not data_sources.get('dataSourceSummaries'):
                logger.error("❌ No data sources found for knowledge base")
                return False
            
            data_source_id = data_sources['dataSourceSummaries'][0]['dataSourceId']
            
            # Start ingestion job
            logger.info(f"🔄 Starting ingestion job for KB: {kb_id}, Data Source: {data_source_id}")
            
            response = self.bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                description="Enhanced knowledge base ingestion with business logic and workflows"
            )
            
            ingestion_job_id = response['ingestionJob']['ingestionJobId']
            logger.info(f"✅ Ingestion job started: {ingestion_job_id}")
            
            # Wait for ingestion to complete
            logger.info("⏳ Waiting for ingestion to complete...")
            max_wait_time = 1800  # 30 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    job_response = self.bedrock_agent_client.get_ingestion_job(
                        knowledgeBaseId=kb_id,
                        dataSourceId=data_source_id,
                        ingestionJobId=ingestion_job_id
                    )
                    
                    status = job_response['ingestionJob']['status']
                    logger.info(f"📊 Ingestion status: {status}")
                    
                    if status == 'COMPLETE':
                        logger.info("✅ Ingestion completed successfully!")
                        return True
                    elif status == 'FAILED':
                        logger.error(f"❌ Ingestion failed: {job_response['ingestionJob'].get('failureReasons', [])}")
                        return False
                    elif status in ['STARTING', 'IN_PROGRESS']:
                        logger.info("⏳ Ingestion in progress...")
                        time.sleep(30)
                    else:
                        logger.warning(f"⚠️ Unknown status: {status}")
                        time.sleep(30)
                        
                except Exception as e:
                    logger.error(f"❌ Error checking ingestion status: {e}")
                    time.sleep(30)
            
            logger.warning("⚠️ Ingestion job timeout - check AWS console for final status")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error triggering ingestion job: {e}")
            return False
    
    def list_s3_contents(self) -> bool:
        """List contents of S3 bucket for verification"""
        logger.info(f"📋 Listing S3 bucket contents: {self.bucket_name}")
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                logger.info("📁 S3 bucket is empty")
                return True
            
            logger.info(f"📁 Found {len(response['Contents'])} objects in S3:")
            for obj in response['Contents']:
                size_kb = obj['Size'] / 1024
                logger.info(f"  📄 {obj['Key']} ({size_kb:.1f} KB)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error listing S3 contents: {e}")
            return False
    
    def update_agents_with_kb(self) -> bool:
        """Update agent instructions to reference the enhanced knowledge base"""
        logger.info("🤖 Updating agent instructions to reference enhanced knowledge base...")
        
        try:
            # Update Decision Agent to use instructions_v2.md (streamlined version)
            decision_agent_id = self.config.get('decision_agent', {}).get('agent_id')
            if decision_agent_id:
                logger.info(f"🔄 Updating Decision Agent: {decision_agent_id}")
                
                # Read streamlined instructions
                instructions_path = os.path.join(self.project_root, "agents/decision_agent/instructions_v2.md")
                if os.path.exists(instructions_path):
                    with open(instructions_path, 'r') as f:
                        new_instructions = f.read()
                    
                    # Update agent instructions
                    self.bedrock_agent_client.update_agent(
                        agentId=decision_agent_id,
                        agentName="revops-decision-agent-enhanced",
                        description="Enhanced Decision Agent with knowledge base integration",
                        instruction=new_instructions,
                        foundationModel="anthropic.claude-3-5-sonnet-20240620-v1:0",
                        agentResourceRoleArn=f"arn:aws:iam::{self.account_id}:role/AmazonBedrockExecutionRoleForAgents_revops"
                    )
                    
                    # Prepare agent
                    self.bedrock_agent_client.prepare_agent(agentId=decision_agent_id)
                    logger.info("✅ Decision Agent updated with enhanced instructions")
                else:
                    logger.warning("⚠️ Decision Agent instructions_v2.md not found")
            
            # Update Data Agent to use instructions_v2.md (enhanced version)
            data_agent_id = self.config.get('data_agent', {}).get('agent_id')
            if data_agent_id:
                logger.info(f"🔄 Updating Data Agent: {data_agent_id}")
                
                # Read enhanced instructions
                instructions_path = os.path.join(self.project_root, "agents/data_agent/instructions_v2.md")
                if os.path.exists(instructions_path):
                    with open(instructions_path, 'r') as f:
                        new_instructions = f.read()
                    
                    # Update agent instructions
                    self.bedrock_agent_client.update_agent(
                        agentId=data_agent_id,
                        agentName="revops-data-agent-enhanced",
                        description="Enhanced Data Agent with business logic integration",
                        instruction=new_instructions,
                        foundationModel="anthropic.claude-3-5-sonnet-20240620-v1:0",
                        agentResourceRoleArn=f"arn:aws:iam::{self.account_id}:role/AmazonBedrockExecutionRoleForAgents_revops"
                    )
                    
                    # Prepare agent
                    self.bedrock_agent_client.prepare_agent(agentId=data_agent_id)
                    logger.info("✅ Data Agent updated with enhanced instructions")
                else:
                    logger.warning("⚠️ Data Agent instructions_v2.md not found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating agent instructions: {e}")
            return False
    
    def deploy_enhanced_kb(self) -> bool:
        """Complete deployment of enhanced knowledge base"""
        logger.info("🚀 Starting enhanced knowledge base deployment...")
        logger.info("=" * 70)
        
        success = True
        
        # Step 1: Upload files to S3
        logger.info("📤 Step 1: Uploading knowledge base files to S3...")
        if not self.upload_knowledge_base_files():
            logger.error("❌ Failed to upload knowledge base files")
            success = False
            return False
        
        # Step 2: List S3 contents for verification
        logger.info("📋 Step 2: Verifying S3 upload...")
        if not self.list_s3_contents():
            logger.error("❌ Failed to verify S3 contents")
            success = False
        
        # Step 3: Trigger ingestion job
        logger.info("🔄 Step 3: Triggering knowledge base ingestion...")
        if not self.trigger_ingestion_job():
            logger.error("❌ Failed to complete ingestion job")
            success = False
        
        # Step 4: Update agent instructions
        logger.info("🤖 Step 4: Updating agent instructions...")
        if not self.update_agents_with_kb():
            logger.error("❌ Failed to update agent instructions")
            success = False
        
        if success:
            logger.info("=" * 70)
            logger.info("🎉 ENHANCED KNOWLEDGE BASE DEPLOYMENT COMPLETED!")
            logger.info("=" * 70)
            logger.info("📋 Summary:")
            logger.info("  ✅ Knowledge base files uploaded to S3")
            logger.info("  ✅ Knowledge base ingestion completed")
            logger.info("  ✅ Agent instructions updated")
            logger.info("  ✅ System ready with enhanced business logic")
            logger.info("=" * 70)
        else:
            logger.error("❌ Enhanced knowledge base deployment completed with errors")
        
        return success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Enhanced Knowledge Base Upload Script",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--profile", default="revops-dev-profile", help="AWS profile name")
    parser.add_argument("--upload-only", action="store_true", help="Only upload files, don't trigger ingestion")
    parser.add_argument("--ingestion-only", action="store_true", help="Only trigger ingestion job")
    parser.add_argument("--list-only", action="store_true", help="Only list S3 contents")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    uploader = EnhancedKnowledgeBaseUploader(profile_name=args.profile)
    
    if args.upload_only:
        success = uploader.upload_knowledge_base_files()
    elif args.ingestion_only:
        success = uploader.trigger_ingestion_job()
    elif args.list_only:
        success = uploader.list_s3_contents()
    else:
        # Default: full deployment
        success = uploader.deploy_enhanced_kb()
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()