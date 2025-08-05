# GitHub Action: Knowledge Base Sync

## Overview

This document describes the automated GitHub Action workflow that synchronizes knowledge base files from the repository to AWS S3 and triggers Bedrock knowledge base ingestion.

## Workflow File Location

`.github/workflows/knowledge-base-sync.yml`

## Trigger Conditions

- **Event**: Push to `main` branch
- **Path Filter**: Only triggers on changes to `knowledge_base/**/*.md` files
- **Exclusions**: Excludes `knowledge_base/firebolt_schema/**` directory

## Workflow Steps

### 1. Repository Checkout
- Uses `actions/checkout@v4`
- Fetches 2 commits deep to enable change detection
- Required for `git diff` operations

### 2. AWS Credentials Configuration
- Uses `aws-actions/configure-aws-credentials@v4`
- Supports both permanent (AKIA*) and temporary (ASIA*) credentials
- Requires repository secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
- Uses repository variable: `AWS_REGION`

### 3. Change Detection
- Detects modified and deleted `.md` files in `knowledge_base/` directory
- Excludes `firebolt_schema/` subdirectory from processing
- Sets output variables for subsequent steps

### 4. S3 Synchronization
**Conditions**: Only runs if changes are detected

**Actions**:
- Uploads all current `.md` files (excluding `firebolt_schema/`)
- Maintains directory structure in S3
- Sets proper content-type: `text/markdown`
- Removes deleted files from S3

**Target**: `s3://revops-ai-framework-kb-740202120544/knowledge-base/`

### 5. Bedrock Knowledge Base Ingestion
**Conditions**: Only runs if S3 sync succeeds

**Actions**:
- Triggers ingestion job on knowledge base `F61WLOYZSW`
- Uses data source `0HMI5RHYUS`
- Provides descriptive job description with timestamp
- Waits 5 seconds and reports initial status
- Continues on Bedrock failures (doesn't fail the entire workflow)

### 6. Summary Report
- Lists processed files (added, modified, deleted)
- Confirms S3 sync completion
- Confirms Bedrock ingestion trigger
- Provides user-friendly status update

## Example Workflow Run

### Successful Execution Log
```
Detecting changes in knowledge_base directory (excluding firebolt_schema/)...
Changed files:
knowledge_base/icp_and_reachout/firebolt_icp.md

Starting S3 sync...
Uploading current .md files to S3 (excluding firebolt_schema)...
[Multiple file uploads...]
S3 sync completed successfully!

Triggering Bedrock knowledge base ingestion...
✅ Bedrock ingestion job started successfully!
Job ID: KSCLHEAVWI
Initial ingestion job status: IN_PROGRESS

📋 Knowledge Base Sync Summary:
================================
📝 Updated/Added files:
  - knowledge_base/icp_and_reachout/firebolt_icp.md

✅ S3 sync completed
✅ Bedrock ingestion triggered
🎯 Knowledge base agents will use updated content within a few minutes
```

## Required AWS Permissions

The GitHub Action requires AWS credentials with the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject", 
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::revops-ai-framework-kb-740202120544",
        "arn:aws:s3:::revops-ai-framework-kb-740202120544/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agent:StartIngestionJob",
        "bedrock-agent:GetIngestionJob"
      ],
      "Resource": "*"
    }
  ]
}
```

## Repository Secrets Configuration

### For Temporary Credentials (ASIA* access keys)
- `AWS_ACCESS_KEY_ID`: Temporary access key ID
- `AWS_SECRET_ACCESS_KEY`: Secret access key
- `AWS_SESSION_TOKEN`: Required session token
- `AWS_REGION` (variable): Target AWS region

### For Permanent Credentials (AKIA* access keys)
- `AWS_ACCESS_KEY_ID`: IAM user access key ID
- `AWS_SECRET_ACCESS_KEY`: IAM user secret access key
- `AWS_REGION` (variable): Target AWS region

## Excluded Directories

- `knowledge_base/firebolt_schema/`: Excluded from automatic sync
  - Managed through separate controlled process
  - Requires manual review for schema changes

## Error Handling

### S3 Sync Failures
- Workflow fails if S3 operations encounter authentication or permission errors
- Individual file upload failures are logged but don't stop the process

### Bedrock Ingestion Failures
- Bedrock failures are logged as warnings
- Workflow continues and reports success if S3 sync succeeded
- Allows manual Bedrock ingestion if needed

### Common Issues
1. **Invalid security token**: Update AWS credentials in repository secrets
2. **Permission denied**: Verify IAM permissions match required policy
3. **No changes detected**: Ensure changes are in `.md` files within `knowledge_base/`

## Performance Metrics

### Typical Execution Time
- **Change Detection**: < 5 seconds
- **S3 Sync (20 files)**: ~15 seconds
- **Bedrock Ingestion**: 5-30 seconds (asynchronous)
- **Total Workflow**: ~25 seconds

### Resource Usage
- **Runner**: ubuntu-latest
- **Concurrent Executions**: Limited by GitHub Actions quotas
- **AWS API Calls**: Minimal (upload files + 1 ingestion trigger)

## Monitoring and Verification

### GitHub Actions
- View workflow runs in repository Actions tab
- Check logs for detailed execution information
- Monitor success/failure rates

### AWS Console
- S3 bucket: `revops-ai-framework-kb-740202120544/knowledge-base/`
- Bedrock knowledge base: `F61WLOYZSW` (revops-schema-kb-1751466030)
- CloudWatch logs for ingestion job details

### Verification Steps
1. Check workflow completion in GitHub Actions
2. Verify file timestamps in S3 bucket
3. Confirm ingestion job completion in Bedrock console
4. Test AI agents for updated content availability

## Maintenance

### Regular Tasks
- **Monitor credential expiration** (for temporary credentials)
- **Review workflow logs** for any recurring issues
- **Update AWS permissions** if new resources are added

### Updates Required When
- **New directories added** to knowledge_base/
- **AWS resources change** (bucket, knowledge base ID)
- **Permission requirements evolve**

## Implementation History

- **Initial Version**: August 2025
- **Session Token Support**: Added for temporary AWS credentials
- **Firebolt Schema Exclusion**: Implemented for controlled schema management
- **Error Handling Enhancement**: Improved Bedrock failure handling

---

**Last Updated**: August 2025  
**Workflow Version**: 1.0  
**Status**: Production Ready ✅