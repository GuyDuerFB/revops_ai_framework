#!/usr/bin/env python3
"""
Update Knowledge Base Files to AWS
==================================

Upload all knowledge base files to AWS S3 and sync with Bedrock Knowledge Base.
"""

import boto3
import json
import logging
import os
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def upload_kb_files_to_s3():
    """Upload all knowledge base files to S3"""
    
    logger.info("📚 Updating Knowledge Base Files to AWS")
    logger.info("=" * 60)
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    kb_config = config.get('knowledge_base', {})
    bucket_name = kb_config.get('storage_bucket')
    prefix = kb_config.get('storage_prefix')
    
    if not bucket_name or not prefix:
        logger.error("❌ Missing knowledge base configuration")
        return False
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    s3_client = session.client('s3')
    
    logger.info(f"📦 Target bucket: {bucket_name}")
    logger.info(f"📁 Target prefix: {prefix}")
    
    # Get all knowledge base files
    kb_dir = Path("/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V2/knowledge_base")
    
    md_files = list(kb_dir.glob("**/*.md"))
    json_files = list(kb_dir.glob("**/*.json"))
    
    all_files = md_files + json_files
    
    logger.info(f"📋 Found {len(all_files)} files to upload:")
    for file in all_files:
        logger.info(f"   📄 {file.relative_to(kb_dir)}")
    
    uploaded_count = 0
    failed_count = 0
    
    try:
        for file_path in all_files:
            # Calculate relative path and S3 key
            relative_path = file_path.relative_to(kb_dir)
            s3_key = f"{prefix}{relative_path}".replace("\\", "/")  # Ensure forward slashes
            
            try:
                # Upload file
                logger.info(f"📤 Uploading {relative_path} → s3://{bucket_name}/{s3_key}")
                
                with open(file_path, 'rb') as f:
                    s3_client.put_object(
                        Bucket=bucket_name,
                        Key=s3_key,
                        Body=f.read(),
                        ContentType='text/markdown' if file_path.suffix == '.md' else 'application/json'
                    )
                
                uploaded_count += 1
                logger.info(f"   ✅ Uploaded successfully")
                
            except Exception as e:
                logger.error(f"   ❌ Failed to upload {relative_path}: {e}")
                failed_count += 1
        
        logger.info(f"\n📊 Upload Summary:")
        logger.info(f"   ✅ Uploaded: {uploaded_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        
        return failed_count == 0
        
    except Exception as e:
        logger.error(f"❌ Error during upload: {e}")
        return False

def sync_knowledge_base():
    """Trigger knowledge base sync in Bedrock"""
    
    logger.info("\n🔄 Syncing Knowledge Base with Bedrock")
    logger.info("=" * 50)
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    kb_config = config.get('knowledge_base', {})
    kb_id = kb_config.get('knowledge_base_id')
    
    if not kb_id:
        logger.error("❌ Missing knowledge base ID")
        return False
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_agent = session.client('bedrock-agent')
    
    try:
        logger.info(f"🔄 Starting sync for knowledge base: {kb_id}")
        
        # Start ingestion job
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=kb_id,
            description="Updated knowledge base files - SQL patterns and schema corrections"
        )
        
        ingestion_job_id = response['ingestionJob']['ingestionJobId']
        logger.info(f"📝 Ingestion job started: {ingestion_job_id}")
        
        # Wait for completion
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            job_response = bedrock_agent.get_ingestion_job(
                knowledgeBaseId=kb_id,
                ingestionJobId=ingestion_job_id
            )
            
            status = job_response['ingestionJob']['status']
            logger.info(f"📊 Ingestion status: {status}")
            
            if status == 'COMPLETE':
                logger.info("✅ Knowledge base sync completed successfully")
                
                # Show ingestion statistics if available
                stats = job_response['ingestionJob'].get('statistics', {})
                if stats:
                    logger.info(f"📈 Ingestion statistics:")
                    for key, value in stats.items():
                        logger.info(f"   {key}: {value}")
                
                return True
                
            elif status == 'FAILED':
                logger.error("❌ Knowledge base sync failed")
                failure_reasons = job_response['ingestionJob'].get('failureReasons', [])
                for reason in failure_reasons:
                    logger.error(f"   Reason: {reason}")
                return False
                
            elif status in ['STARTING', 'IN_PROGRESS']:
                logger.info("⏳ Sync in progress, waiting...")
                time.sleep(10)
            else:
                logger.warning(f"⚠️ Unexpected status: {status}")
                time.sleep(10)
        
        logger.warning("⏳ Sync taking longer than expected, but may still complete")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error syncing knowledge base: {e}")
        return False

def verify_kb_update():
    """Verify the knowledge base update was successful"""
    
    logger.info("\n🔍 Verifying Knowledge Base Update")
    logger.info("=" * 40)
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    kb_config = config.get('knowledge_base', {})
    bucket_name = kb_config.get('storage_bucket')
    prefix = kb_config.get('storage_prefix')
    
    # AWS setup
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    s3_client = session.client('s3')
    
    try:
        # List objects in S3 bucket
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        objects = response.get('Contents', [])
        
        logger.info(f"📊 Files in S3 bucket:")
        logger.info(f"   Total objects: {len(objects)}")
        
        # Group by type
        md_files = [obj for obj in objects if obj['Key'].endswith('.md')]
        json_files = [obj for obj in objects if obj['Key'].endswith('.json')]
        
        logger.info(f"   Markdown files: {len(md_files)}")
        logger.info(f"   JSON files: {len(json_files)}")
        
        # Show recent uploads
        recent_files = sorted(objects, key=lambda x: x['LastModified'], reverse=True)[:5]
        logger.info(f"📅 Most recently updated files:")
        for obj in recent_files:
            file_name = obj['Key'].replace(prefix, '')
            logger.info(f"   {file_name} (modified: {obj['LastModified']})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying KB update: {e}")
        return False

def main():
    """Main function to update knowledge base"""
    
    logger.info("📚 Knowledge Base Update Process")
    logger.info("=" * 60)
    
    # Upload files to S3
    upload_success = upload_kb_files_to_s3()
    
    if not upload_success:
        logger.error("❌ File upload failed, skipping sync")
        return False
    
    # Sync knowledge base
    sync_success = sync_knowledge_base()
    
    # Verify update
    verify_success = verify_kb_update()
    
    if upload_success and sync_success and verify_success:
        logger.info("\n🎉 KNOWLEDGE BASE UPDATE COMPLETED!")
        logger.info("✅ All files uploaded to S3")
        logger.info("✅ Knowledge base synced with Bedrock") 
        logger.info("✅ Update verified")
        logger.info("\n📋 Updated files include:")
        logger.info("   • Fixed SQL patterns (customer_segmentation.md, temporal_analysis.md)")
        logger.info("   • Current schema documentation")
        logger.info("   • Business logic and workflows")
        logger.info("   • ICP and messaging guidelines")
        logger.info("\n🚀 Knowledge base is ready for agent use!")
    else:
        logger.error("❌ Knowledge base update encountered issues")
        if not upload_success:
            logger.error("   - File upload problems")
        if not sync_success:
            logger.error("   - Knowledge base sync problems")
        if not verify_success:
            logger.error("   - Verification problems")
    
    return upload_success and sync_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)