#!/usr/bin/env python3
"""
Knowledge Base Sync Script for RevOps AI Framework
Automatically syncs local knowledge base files to S3 and triggers knowledge base ingestion
"""

import os
import sys
import json
import boto3
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from botocore.exceptions import ClientError, BotoCoreError

# Configuration
AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"
KNOWLEDGE_BASE_ID = "F61WLOYZSW"  # RevOps Knowledge Base ID
S3_BUCKET = "revops-ai-framework-kb-740202120544"
S3_PREFIX = "knowledge-base/"

# Local knowledge base directory
SCRIPT_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = SCRIPT_DIR.parent.parent / "knowledge_base"
SYNC_STATE_FILE = SCRIPT_DIR.parent / "config" / "kb_sync_state.json"

class KnowledgeBaseSync:
    """Main class for knowledge base synchronization"""
    
    def __init__(self):
        """Initialize the sync client"""
        self.session = boto3.Session(profile_name=AWS_PROFILE)
        self.s3_client = self.session.client('s3', region_name=AWS_REGION)
        self.bedrock_client = self.session.client('bedrock-agent', region_name=AWS_REGION)
        
        self.changed_files = []
        self.uploaded_files = []
        self.errors = []
        self.sync_state = self.load_sync_state()
        
        # Initialize colors for output
        self.colors = {
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'blue': '\033[94m',
            'bold': '\033[1m',
            'end': '\033[0m'
        }
    
    def log(self, message: str, color: str = None):
        """Log message with optional color"""
        if color and color in self.colors:
            print(f"{self.colors[color]}{message}{self.colors['end']}")
        else:
            print(message)
    
    def load_sync_state(self) -> Dict:
        """Load the last sync state from file"""
        if SYNC_STATE_FILE.exists():
            try:
                with open(SYNC_STATE_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.log(f"Warning: Could not read sync state file: {e}", 'yellow')
        
        return {
            'last_sync': None,
            'file_hashes': {},
            'last_successful_sync': None
        }
    
    def save_sync_state(self):
        """Save the current sync state to file"""
        try:
            with open(SYNC_STATE_FILE, 'w') as f:
                json.dump(self.sync_state, f, indent=2)
        except IOError as e:
            self.log(f"Warning: Could not save sync state: {e}", 'yellow')
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except IOError as e:
            self.log(f"Error reading file {file_path}: {e}", 'red')
            return ""
    
    def find_knowledge_base_files(self) -> List[Path]:
        """Find all knowledge base files in the directory"""
        if not KNOWLEDGE_BASE_DIR.exists():
            self.log(f"Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}", 'red')
            return []
        
        # Supported file types for knowledge base
        supported_extensions = {'.txt', '.md', '.pdf', '.doc', '.docx', '.html', '.csv', '.json'}
        files = []
        
        for file_path in KNOWLEDGE_BASE_DIR.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                # Skip hidden files and system files
                if not file_path.name.startswith('.') and not file_path.name.startswith('~'):
                    files.append(file_path)
        
        return files
    
    def detect_changed_files(self) -> List[Path]:
        """Detect files that have changed since last sync"""
        all_files = self.find_knowledge_base_files()
        changed_files = []
        
        self.log(f"📁 Scanning {len(all_files)} files in knowledge base directory...", 'blue')
        
        for file_path in all_files:
            try:
                current_hash = self.get_file_hash(file_path)
                relative_path = str(file_path.relative_to(KNOWLEDGE_BASE_DIR))
                
                # Check if file is new or changed
                if (relative_path not in self.sync_state['file_hashes'] or 
                    self.sync_state['file_hashes'][relative_path] != current_hash):
                    
                    changed_files.append(file_path)
                    self.sync_state['file_hashes'][relative_path] = current_hash
                    
                    # Log the change
                    status = "NEW" if relative_path not in self.sync_state['file_hashes'] else "CHANGED"
                    self.log(f"  📄 {status}: {relative_path}", 'yellow')
                
            except Exception as e:
                self.log(f"Error processing file {file_path}: {e}", 'red')
                self.errors.append(f"File processing error: {file_path} - {e}")
        
        return changed_files
    
    def upload_file_to_s3(self, file_path: Path) -> bool:
        """Upload a single file to S3"""
        try:
            relative_path = file_path.relative_to(KNOWLEDGE_BASE_DIR)
            s3_key = f"{S3_PREFIX}{relative_path}"
            
            # Determine content type
            content_type = self.get_content_type(file_path.suffix)
            
            # Upload file
            self.s3_client.upload_file(
                str(file_path),
                S3_BUCKET,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'source': 'knowledge-base-sync',
                        'upload-time': datetime.now().isoformat(),
                        'file-name': file_path.name
                    }
                }
            )
            
            self.log(f"  ✅ Uploaded: {relative_path}", 'green')
            return True
            
        except ClientError as e:
            error_msg = f"S3 upload failed for {file_path}: {e}"
            self.log(f"  ❌ {error_msg}", 'red')
            self.errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error uploading {file_path}: {e}"
            self.log(f"  ❌ {error_msg}", 'red')
            self.errors.append(error_msg)
            return False
    
    def get_content_type(self, file_extension: str) -> str:
        """Get content type based on file extension"""
        content_types = {
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.html': 'text/html',
            '.csv': 'text/csv',
            '.json': 'application/json'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')
    
    def verify_s3_bucket(self) -> bool:
        """Verify S3 bucket exists and is accessible"""
        try:
            self.s3_client.head_bucket(Bucket=S3_BUCKET)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                self.log(f"❌ S3 bucket '{S3_BUCKET}' not found", 'red')
            elif error_code == '403':
                self.log(f"❌ Access denied to S3 bucket '{S3_BUCKET}'", 'red')
            else:
                self.log(f"❌ S3 bucket error: {e}", 'red')
            
            self.errors.append(f"S3 bucket verification failed: {e}")
            return False
    
    def upload_changed_files(self) -> List[Path]:
        """Upload all changed files to S3"""
        if not self.changed_files:
            self.log("📤 No files to upload", 'blue')
            return []
        
        self.log(f"📤 Uploading {len(self.changed_files)} changed files to S3...", 'blue')
        
        successfully_uploaded = []
        for file_path in self.changed_files:
            if self.upload_file_to_s3(file_path):
                successfully_uploaded.append(file_path)
        
        self.uploaded_files = successfully_uploaded
        return successfully_uploaded
    
    def trigger_knowledge_base_sync(self) -> bool:
        """Trigger knowledge base ingestion job"""
        if not self.uploaded_files:
            self.log("🔄 No files uploaded, skipping knowledge base sync", 'blue')
            return True
        
        self.log("🔄 Triggering knowledge base ingestion...", 'blue')
        
        try:
            # Start ingestion job
            response = self.bedrock_client.start_ingestion_job(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                dataSourceId="0HMI5RHYUS",  # Default data source ID for S3
                description=f"Automatic sync - {len(self.uploaded_files)} files updated at {datetime.now().isoformat()}"
            )
            
            ingestion_job_id = response['ingestionJob']['ingestionJobId']
            self.log(f"  📋 Ingestion job started: {ingestion_job_id}", 'green')
            
            # Wait for completion (with timeout)
            self.log("  ⏳ Waiting for ingestion to complete...", 'blue')
            
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                job_response = self.bedrock_client.get_ingestion_job(
                    knowledgeBaseId=KNOWLEDGE_BASE_ID,
                    dataSourceId="0HMI5RHYUS",
                    ingestionJobId=ingestion_job_id
                )
                
                status = job_response['ingestionJob']['status']
                
                if status == 'COMPLETE':
                    self.log("  ✅ Knowledge base ingestion completed successfully!", 'green')
                    return True
                elif status == 'FAILED':
                    failure_reasons = job_response['ingestionJob'].get('failureReasons', ['Unknown error'])
                    error_msg = f"Knowledge base ingestion failed: {', '.join(failure_reasons)}"
                    self.log(f"  ❌ {error_msg}", 'red')
                    self.errors.append(error_msg)
                    return False
                elif status in ['STOPPING', 'STOPPED']:
                    error_msg = f"Knowledge base ingestion was stopped: {status}"
                    self.log(f"  ⚠️  {error_msg}", 'yellow')
                    self.errors.append(error_msg)
                    return False
                
                # Job is still running
                time.sleep(10)
                self.log(f"  ⏳ Ingestion status: {status}", 'blue')
            
            # Timeout reached
            error_msg = f"Knowledge base ingestion timed out after {max_wait_time} seconds"
            self.log(f"  ⏰ {error_msg}", 'yellow')
            self.errors.append(error_msg)
            return False
            
        except ClientError as e:
            error_msg = f"Failed to trigger knowledge base ingestion: {e}"
            self.log(f"  ❌ {error_msg}", 'red')
            self.errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error during knowledge base sync: {e}"
            self.log(f"  ❌ {error_msg}", 'red')
            self.errors.append(error_msg)
            return False
    
    def generate_summary(self, sync_successful: bool) -> str:
        """Generate a summary of the sync operation"""
        summary = []
        summary.append("=" * 60)
        summary.append("📋 KNOWLEDGE BASE SYNC SUMMARY")
        summary.append("=" * 60)
        summary.append(f"🕐 Sync Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append(f"📁 Knowledge Base Directory: {KNOWLEDGE_BASE_DIR}")
        summary.append(f"🪣 S3 Bucket: {S3_BUCKET}")
        summary.append(f"🧠 Knowledge Base ID: {KNOWLEDGE_BASE_ID}")
        summary.append("")
        
        # Files summary
        total_files = len(self.find_knowledge_base_files())
        summary.append(f"📊 FILES ANALYSIS:")
        summary.append(f"  • Total files scanned: {total_files}")
        summary.append(f"  • Files changed: {len(self.changed_files)}")
        summary.append(f"  • Files uploaded: {len(self.uploaded_files)}")
        summary.append("")
        
        # Changed files details
        if self.changed_files:
            summary.append(f"📄 CHANGED FILES:")
            for file_path in self.changed_files:
                relative_path = file_path.relative_to(KNOWLEDGE_BASE_DIR)
                uploaded = "✅" if file_path in self.uploaded_files else "❌"
                summary.append(f"  {uploaded} {relative_path}")
            summary.append("")
        
        # Operation status
        if sync_successful:
            summary.append("✅ OPERATION STATUS: SUCCESS")
            summary.append("  • All changed files uploaded successfully")
            summary.append("  • Knowledge base ingestion completed")
            summary.append("  • Knowledge base is ready for use")
        else:
            summary.append("❌ OPERATION STATUS: FAILED")
            if self.errors:
                summary.append("  • Errors encountered:")
                for error in self.errors:
                    summary.append(f"    - {error}")
        
        summary.append("")
        summary.append("=" * 60)
        
        return "\n".join(summary)
    
    def run_sync(self) -> bool:
        """Run the complete sync process"""
        self.log("🚀 Starting Knowledge Base Sync Process", 'bold')
        self.log("=" * 60, 'blue')
        
        # Step 1: Verify S3 bucket
        self.log("🔍 Step 1: Verifying S3 bucket access...", 'blue')
        if not self.verify_s3_bucket():
            return False
        self.log("  ✅ S3 bucket verified", 'green')
        
        # Step 2: Detect changed files
        self.log("🔍 Step 2: Detecting changed files...", 'blue')
        self.changed_files = self.detect_changed_files()
        
        if not self.changed_files:
            self.log("  ℹ️  No files have changed since last sync", 'blue')
            self.log("  ✅ Knowledge base is already up to date", 'green')
            return True
        
        # Step 3: Upload changed files
        self.log("🔍 Step 3: Uploading changed files...", 'blue')
        uploaded_files = self.upload_changed_files()
        
        if not uploaded_files:
            self.log("  ❌ No files were uploaded successfully", 'red')
            return False
        
        # Step 4: Trigger knowledge base sync
        self.log("🔍 Step 4: Syncing knowledge base...", 'blue')
        sync_successful = self.trigger_knowledge_base_sync()
        
        # Step 5: Update sync state
        if sync_successful:
            self.sync_state['last_sync'] = datetime.now().isoformat()
            self.sync_state['last_successful_sync'] = datetime.now().isoformat()
        else:
            self.sync_state['last_sync'] = datetime.now().isoformat()
        
        self.save_sync_state()
        
        return sync_successful

def main():
    """Main function"""
    try:
        # Initialize sync client
        sync_client = KnowledgeBaseSync()
        
        # Run the sync process
        success = sync_client.run_sync()
        
        # Generate and display summary
        summary = sync_client.generate_summary(success)
        print("\n" + summary)
        
        # Save summary to file
        summary_file = SCRIPT_DIR / f"kb_sync_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        sync_client.log(f"📄 Summary saved to: {summary_file}", 'blue')
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Sync process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()