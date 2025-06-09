#!/usr/bin/env python3
"""
Script to upload multiple files to S3.

Example:
    python bulk_upload.py --dir /path/to/folder --bucket my-bucket --prefix my-prefix/
"""
import os
import sys
import argparse
import glob
from pathlib import Path

# Add parent directory to path to allow importing from common
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.aws_utils import setup_logger, get_aws_client
from s3.upload_to_s3 import upload_file_to_s3

# Set up logger
logger = setup_logger(__name__)


def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Upload multiple files to S3')
    parser.add_argument('--dir', '-d', required=True, help='Local directory path with files to upload')
    parser.add_argument('--pattern', '-p', default='*', help='File pattern to match (e.g., *.md, *.txt)')
    parser.add_argument('--bucket', '-b', required=True, help='S3 bucket name')
    parser.add_argument('--prefix', '-x', default='', help='S3 prefix (folder path)')
    parser.add_argument('--recursive', '-r', action='store_true', help='Search for files recursively')
    return parser.parse_args()


def main():
    """
    Main entry point for the script.
    """
    args = parse_args()
    source_dir = Path(args.dir)
    
    # Validate source directory
    if not source_dir.exists() or not source_dir.is_dir():
        logger.error(f"Source directory not found or is not a directory: {source_dir}")
        return 1
    
    # Find files matching pattern
    if args.recursive:
        search_pattern = f"**/{args.pattern}"
    else:
        search_pattern = args.pattern
        
    files = list(source_dir.glob(search_pattern))
    
    if not files:
        logger.warning(f"No files found matching pattern '{args.pattern}' in {source_dir}")
        return 0
    
    logger.info(f"Found {len(files)} files to upload")
    
    # Upload each file
    success_count = 0
    for file_path in files:
        # Calculate relative path from source_dir
        rel_path = file_path.relative_to(source_dir)
        
        # Create S3 key with prefix
        s3_key = f"{args.prefix}{str(rel_path)}" if args.prefix else str(rel_path)
        
        # Upload file
        if upload_file_to_s3(str(file_path), args.bucket, s3_key):
            success_count += 1
    
    # Report results
    logger.info(f"Successfully uploaded {success_count} of {len(files)} files")
    if success_count == len(files):
        print(f"✅ All {success_count} files uploaded successfully to s3://{args.bucket}/{args.prefix}")
        return 0
    else:
        print(f"⚠️ {success_count} of {len(files)} files uploaded to s3://{args.bucket}/{args.prefix}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
