#!/usr/bin/env python3
"""
Script to upload files to S3.

- Can be used to upload any file to a specified S3 location
- Uses common AWS utilities for consistent credential and logging handling
"""
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to allow importing from common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.aws_utils import setup_logger, get_aws_client

# Set up logger
logger = setup_logger(__name__)

def upload_file_to_s3(file_path, bucket_name, object_key):
    """
    Upload a file to a specified S3 bucket.
    
    Args:
        file_path (str): Path to the local file
        bucket_name (str): S3 bucket name
        object_key (str): S3 object key (path in S3)
    
    Returns:
        bool: True if upload succeeds, False otherwise
    """
    try:
        logger.info(f"Uploading {file_path} to s3://{bucket_name}/{object_key}")
        s3_client = get_aws_client('s3')
        s3_client.upload_file(file_path, bucket_name, object_key)
        logger.info(f"Upload successful!")
        return True
    except Exception as e:
        logger.error(f"Error uploading file to S3: {e}")
        return False

def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Upload a file to S3')
    parser.add_argument('--file', '-f', required=True, help='Local file path to upload')
    parser.add_argument('--bucket', '-b', required=True, help='S3 bucket name')
    parser.add_argument('--key', '-k', required=True, help='S3 object key (path in S3)')
    return parser.parse_args()


def main():
    """
    Main entry point for the script.
    """
    # Parse command line arguments or use default values
    if len(sys.argv) > 1:
        args = parse_args()
        source_file = Path(args.file)
        bucket_name = args.bucket
        object_key = args.key
    else:
        # Default values for schema knowledge upload
        source_file = Path("/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/agents/data_agent/schema_knowledge.md")
        bucket_name = "revops-s3-bucket"
        object_key = "revops-ai-framework/schema-information/schema_knowledge.md"
        print(f"Using default values to upload schema_knowledge.md to S3")
    
    # Verify file exists
    if not source_file.exists():
        logger.error(f"Source file not found: {source_file}")
        return 1
    
    # Upload file
    success = upload_file_to_s3(str(source_file), bucket_name, object_key)
    
    if success:
        print(f"✅ Successfully uploaded {source_file.name} to s3://{bucket_name}/{object_key}")
        return 0
    else:
        print("❌ Upload failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
