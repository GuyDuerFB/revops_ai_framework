#!/usr/bin/env python3
"""
S3 Export Bucket Setup
Creates and configures S3 bucket for conversation exports
"""

import boto3
import json
from datetime import datetime

def setup_s3_export_bucket(bucket_name: str, region: str = "us-east-1"):
    """Create and configure S3 bucket for conversation exports"""
    
    s3_client = boto3.client('s3', region_name=region)
    
    print(f"Setting up S3 export bucket: {bucket_name}")
    
    # Step 1: Create bucket
    try:
        if region == 'us-east-1':
            # us-east-1 doesn't need LocationConstraint
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        print(f"✓ Created bucket: {bucket_name}")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"✓ Bucket {bucket_name} already exists")
    except Exception as e:
        print(f"✗ Error creating bucket: {e}")
        return None
    
    # Step 2: Configure lifecycle policy
    lifecycle_config = {
        'Rules': [
            {
                'ID': 'ConversationArchiving',
                'Status': 'Enabled',
                'Filter': {'Prefix': 'conversations/'},
                'Transitions': [
                    {
                        'Days': 30,
                        'StorageClass': 'STANDARD_IA'
                    },
                    {
                        'Days': 90,
                        'StorageClass': 'GLACIER'
                    },
                    {
                        'Days': 365,
                        'StorageClass': 'DEEP_ARCHIVE'
                    }
                ]
            }
        ]
    }
    
    try:
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_config
        )
        print("✓ Configured lifecycle policy")
    except Exception as e:
        print(f"✗ Error configuring lifecycle: {e}")
    
    # Step 3: Configure bucket policy for Lambda access
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::740202120544:role/revops-slack-bedrock-processor-role"
                },
                "Action": [
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                    "s3:GetObject"
                ],
                "Resource": f"arn:aws:s3:::{bucket_name}/conversations/*"
            }
        ]
    }
    
    try:
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print("✓ Configured bucket policy for Lambda access")
    except Exception as e:
        print(f"✗ Error configuring bucket policy: {e}")
    
    # Step 4: Configure bucket versioning (optional)
    try:
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print("✓ Enabled bucket versioning")
    except Exception as e:
        print(f"⚠ Warning: Could not enable versioning: {e}")
    
    # Step 5: Configure server-side encryption
    try:
        s3_client.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256'
                        }
                    }
                ]
            }
        )
        print("✓ Enabled server-side encryption")
    except Exception as e:
        print(f"⚠ Warning: Could not enable encryption: {e}")
    
    print(f"✅ S3 export bucket {bucket_name} configured successfully")
    print(f"📊 Bucket URL: s3://{bucket_name}")
    print(f"🌐 Console URL: https://s3.console.aws.amazon.com/s3/buckets/{bucket_name}")
    
    return f"s3://{bucket_name}"

def test_bucket_access(bucket_name: str):
    """Test bucket access and permissions"""
    
    s3_client = boto3.client('s3')
    
    print(f"\nTesting bucket access: {bucket_name}")
    
    try:
        # Test write access
        test_key = f"test/{datetime.now().isoformat()}/test.txt"
        test_content = "Test conversation export content"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content.encode('utf-8'),
            ContentType='text/plain'
        )
        print(f"✓ Write access successful: {test_key}")
        
        # Test read access
        response = s3_client.get_object(Bucket=bucket_name, Key=test_key)
        content = response['Body'].read().decode('utf-8')
        assert content == test_content
        print("✓ Read access successful")
        
        # Clean up test object
        s3_client.delete_object(Bucket=bucket_name, Key=test_key)
        print("✓ Test cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Bucket access test failed: {e}")
        return False

if __name__ == "__main__":
    # Setup bucket for conversation exports
    bucket_name = "revops-ai-conversations-740202120544"
    bucket_url = setup_s3_export_bucket(bucket_name)
    
    if bucket_url:
        # Test access
        if test_bucket_access(bucket_name):
            print("\n🎉 S3 export setup completed successfully!")
        else:
            print("\n❌ S3 setup completed but access test failed")
    else:
        print("\n❌ S3 setup failed")