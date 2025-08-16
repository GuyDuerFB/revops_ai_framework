# RevOps AI Framework Knowledge Base

## Overview

This knowledge base contains structured information that powers the RevOps AI Framework's intelligent agents. All `.md` files in this directory and its subdirectories are automatically synchronized to AWS Bedrock to provide up-to-date context for AI-driven revenue operations analysis.

## Directory Structure

```
knowledge_base/
├── README.md                          # This file - usage guidelines
├── business_logic/                    # Business rules and logic
│   ├── churn_risk_logic.md           # Customer churn risk assessment
│   ├── consumption_logic.md          # Usage consumption patterns
│   ├── conversion_funnels.md         # Sales conversion analysis
│   ├── customer_classification.md    # Customer segmentation rules
│   ├── firebolt_business_logic.md    # Core business logic
│   ├── revenue_logic.md              # Revenue calculation methods
│   └── sales_process_logic.md        # Sales process workflows
├── firebolt_schema/                   # Database schema documentation (EXCLUDED from auto-sync)
│   ├── firebolt_schema.json          # Schema definition (JSON)
│   └── firebolt_schema.md            # Schema documentation (Markdown)
├── icp_and_reachout/                 # Ideal Customer Profile and messaging
│   ├── firebolt_icp.md               # Ideal Customer Profile definition
│   └── firebolt_messeging.md         # Messaging and communication templates
├── sql_patterns/                     # Common SQL query patterns
│   ├── customer_segmentation.md     # Customer analysis queries
│   ├── gong_call_analysis.md        # Call analysis patterns
│   ├── lead_analysis.md             # Lead scoring and analysis
│   ├── regional_analysis.md         # Geographic analysis queries
│   └── temporal_analysis.md         # Time-based analysis patterns
└── workflows/                        # Process workflows and procedures
    ├── closed_lost_re_engagement.md # Lost deal re-engagement process
    ├── comprehensive_customer_risk_assessment_workflow.md
    ├── comprehensive_deal_assessment_workflow.md
    ├── lead_assessment_workflow.md  # Lead qualification process
    └── poc_execution_workflow.md    # Proof of concept execution
```

## Automatic Synchronization

### How It Works

When you merge changes to the `main` branch that affect `.md` files in the `knowledge_base/` directory:

1. **GitHub Action Trigger**: The `knowledge-base-sync` workflow automatically runs
2. **Change Detection**: Identifies added, modified, or deleted `.md` files
3. **S3 Upload**: Syncs changes to `s3://revops-ai-framework-kb-740202120544/knowledge-base/`
4. **Bedrock Ingestion**: Triggers AWS Bedrock knowledge base refresh
5. **Agent Updates**: AI agents receive updated context within minutes

### Supported Operations

- ✅ **Add new files**: Upload new `.md` files to any subdirectory
- ✅ **Modify existing files**: Update content in existing `.md` files
- ✅ **Delete files**: Remove files from repository (also removes from S3)
- ✅ **Create directories**: Add new subdirectories with `.md` files
- ✅ **Delete directories**: Remove entire subdirectories and contents

### File Requirements

- **Format**: Only `.md` (Markdown) files are synchronized
- **Location**: Must be within the `knowledge_base/` directory or subdirectories
- **Trigger**: Changes must be merged to the `main` branch
- **Exclusions**: The `firebolt_schema/` directory is excluded from auto-sync (managed separately)
- **Ignored files**: Temporary files, hidden files, and non-`.md` files are ignored

### Excluded Directories

**`firebolt_schema/`**: This directory contains database schema documentation that is managed through a separate process and should not be automatically synchronized through GitHub Actions. Changes to schema files require manual review and controlled deployment.

## Content Guidelines

### Writing Best Practices

1. **Clear Headings**: Use descriptive headers with proper Markdown hierarchy
2. **Structured Content**: Organize information logically with consistent formatting
3. **Business Context**: Include relevant business context and reasoning
4. **Examples**: Provide concrete examples where applicable
5. **Updates**: Keep content current and remove outdated information

### Markdown Formatting

```markdown
# Main Title
## Section Header
### Subsection

- Use bullet points for lists
- **Bold** for emphasis
- `code` for technical terms
- [Links](https://example.com) for references

```sql
-- SQL code blocks for queries
SELECT customer_id, revenue
FROM customers
WHERE status = 'active';
```
```

### Content Types

- **Business Logic**: Rules, calculations, and decision criteria
- **Schema Documentation**: Database structure and relationships
- **SQL Patterns**: Reusable query templates and examples
- **Workflows**: Step-by-step processes and procedures
- **ICP & Messaging**: Customer profiles and communication templates

## Monitoring and Troubleshooting

### GitHub Actions

- **Location**: `.github/workflows/knowledge-base-sync.yml`
- **Logs**: View sync results in GitHub Actions tab
- **Status**: Check workflow status for sync success/failure

### Common Issues

1. **No Sync Triggered**: Ensure changes are in `.md` files within `knowledge_base/`
2. **S3 Upload Failed**: Check AWS credentials and permissions (ensure AWS_SESSION_TOKEN is set for temporary credentials)
3. **Bedrock Sync Failed**: Verify knowledge base ID and data source configuration
4. **Large Files**: Files over AWS limits will be logged as warnings

### Verification

After making changes:

1. Check GitHub Actions for successful workflow completion
2. Verify files appear in S3 bucket: `s3://revops-ai-framework-kb-740202120544/knowledge-base/`
3. Test AI agents to confirm they're using updated information

## Security & Authentication

### OIDC-Based Authentication (Current Implementation)

The knowledge base sync uses **OpenID Connect (OIDC)** for secure, token-less authentication with AWS. This approach follows security best practices and eliminates the need for long-term credentials.

#### Security Benefits
- **No Long-term Secrets**: No AWS access keys stored in GitHub secrets
- **Temporary Tokens**: AWS generates temporary credentials for each workflow run
- **Scoped Access**: Role-based permissions limit access to specific resources
- **Audit Trail**: All actions are logged and traceable
- **Automatic Rotation**: Tokens expire automatically, reducing exposure risk

#### AWS Infrastructure

**OIDC Provider**: `arn:aws:iam::740202120544:oidc-provider/token.actions.githubusercontent.com`
- Configured to trust GitHub Actions from this repository
- Uses standard GitHub OIDC thumbprint for verification

**IAM Role**: `GitHubActionsRevOpsKBSyncRole`
- **ARN**: `arn:aws:iam::740202120544:role/GitHubActionsRevOpsKBSyncRole`
- **Trust Policy**: Restricts access to `firebolt-analytics/revops_agent_framework` repository
- **Session Name**: `GitHubActionsKBSync` for audit logging

#### IAM Policy: GitHubActionsRevOpsKBSyncPolicy

**Principle of Least Privilege**: The role has minimal permissions required for the sync operation:

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
        "bedrock:StartIngestionJob",
        "bedrock:GetIngestionJob",
        "bedrock:ListIngestionJobs"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1:740202120544:knowledge-base/F61WLOYZSW",
        "arn:aws:bedrock:us-east-1:740202120544:knowledge-base/F61WLOYZSW/data-source/0HMI5RHYUS"
      ]
    }
  ]
}
```

#### Trust Policy Configuration

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::740202120544:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:firebolt-analytics/revops_agent_framework:*"
        }
      }
    }
  ]
}
```

### Configuration Requirements

**GitHub Workflow Permissions** (`.github/workflows/knowledge-base-sync.yml`):
```yaml
permissions:
  id-token: write   # Required for OIDC token generation
  contents: read    # Required to checkout repository
```

**AWS Configuration** (in workflow):
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::740202120544:role/GitHubActionsRevOpsKBSyncRole
    role-session-name: GitHubActionsKBSync
    aws-region: us-east-1
```

### Security Compliance

#### Access Control
- **Repository Scope**: Limited to `firebolt-analytics/revops_agent_framework` repository
- **Branch Protection**: Only `main` branch changes trigger sync
- **File Filtering**: Only `.md` files in `knowledge_base/` directory (excluding `firebolt_schema/`)
- **Resource Boundaries**: Scoped to specific S3 bucket and Bedrock knowledge base

#### Monitoring & Auditing
- **CloudTrail Logging**: All AWS API calls are logged
- **GitHub Actions Logs**: Complete workflow execution logs
- **IAM Session Names**: Identifiable session names for audit trails
- **S3 Object Versioning**: Track all file changes in S3

#### Data Protection
- **In-Transit Encryption**: All data transfers use HTTPS/TLS
- **At-Rest Encryption**: S3 bucket and Bedrock use AWS encryption
- **Access Logging**: S3 access logs capture all operations
- **Content Filtering**: Only approved file types and locations

## Technical Maintenance

### For Developers & DevOps

#### Workflow Architecture
- **File**: `.github/workflows/knowledge-base-sync.yml`
- **Trigger**: Push to `main` branch affecting `knowledge_base/**/*.md` files
- **Runtime**: Ubuntu latest with AWS CLI pre-installed
- **Duration**: Typically 1-3 minutes per run

#### Key Components
1. **Change Detection**: Uses `git diff` to identify modified/deleted files
2. **S3 Sync**: Uploads only changed files (not full sync)
3. **Bedrock Ingestion**: Triggers knowledge base refresh
4. **Error Handling**: Graceful degradation with detailed logging

#### Maintenance Tasks

**Regular**:
- Monitor GitHub Actions success rate
- Check Bedrock ingestion job status in AWS console
- Review S3 bucket storage usage and costs

**Periodic**:
- Validate IAM role permissions remain minimal
- Update workflow action versions (quarterly)
- Review and rotate OIDC provider thumbprints if needed

**Emergency**:
- Disable workflow by renaming `.yml` file if needed
- Check CloudTrail logs for security incidents
- Review S3 access logs for anomalous activity

#### Troubleshooting Guide

**Common Issues**:

1. **OIDC Authentication Failed**
   - Verify repository name matches trust policy
   - Check OIDC provider exists and thumbprint is current
   - Ensure workflow has `id-token: write` permission

2. **S3 Access Denied**
   - Verify IAM role has S3 permissions
   - Check bucket name and region configuration
   - Ensure S3 bucket policy allows role access

3. **Bedrock Ingestion Failed**
   - Confirm knowledge base ID and data source ID
   - Verify Bedrock permissions in IAM policy
   - Check if knowledge base is in correct region

4. **No Files Detected**
   - Ensure changes are in `.md` files within `knowledge_base/`
   - Verify files are not in excluded `firebolt_schema/` directory
   - Check git diff command output in workflow logs

#### AWS Resource Dependencies

**S3 Bucket**: `revops-ai-framework-kb-740202120544`
- **Region**: us-east-1
- **Purpose**: Knowledge base file storage
- **Encryption**: AWS managed (SSE-S3)

**Bedrock Knowledge Base**: `F61WLOYZSW`
- **Data Source**: `0HMI5RHYUS`
- **Vector Store**: Amazon OpenSearch Serverless
- **Embedding Model**: Amazon Titan Text Embeddings

**IAM Resources**:
- **Role**: `GitHubActionsRevOpsKBSyncRole`
- **Policy**: `GitHubActionsRevOpsKBSyncPolicy`
- **OIDC Provider**: `token.actions.githubusercontent.com`

#### Performance Optimization

**Current Optimizations**:
- Only changed files are uploaded (not full directory sync)
- Parallel operations where possible
- Efficient git diff for change detection

**Monitoring Metrics**:
- Workflow execution time
- S3 data transfer costs
- Bedrock ingestion job duration
- GitHub Actions minutes usage

#### Security Considerations for Maintainers

**Access Review**:
- IAM role permissions should be reviewed quarterly
- Trust policy should restrict to specific repository
- No long-term credentials should be stored

**Incident Response**:
- Disable workflow immediately if security concern identified
- Review CloudTrail logs for unauthorized access
- Rotate OIDC provider configuration if compromised

### Documentation Exclusions

This README.md file is **automatically excluded** from S3 sync to prevent documentation about the sync process from being included in the knowledge base content itself. The exclusion is handled by the workflow's file filtering logic.

## Support

For questions or issues:

- **GitHub Issues**: Report problems via repository issues
- **Documentation**: Check workflow logs for detailed error messages
- **AWS Console**: Monitor S3 bucket and Bedrock ingestion jobs directly
- **Security Issues**: Contact security team immediately for access-related concerns

---

**Last Updated**: August 2025  
**Version**: 2.0  
**Maintained by**: RevOps AI Framework Team