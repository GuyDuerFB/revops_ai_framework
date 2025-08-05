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

## AWS Credentials Setup

The GitHub Action requires AWS credentials configured as repository secrets:

### Required Secrets

For **temporary credentials** (Access Key starts with `ASIA`):
- `AWS_ACCESS_KEY_ID`: Your temporary access key ID
- `AWS_SECRET_ACCESS_KEY`: Your secret access key  
- `AWS_SESSION_TOKEN`: Required for temporary credentials
- `AWS_REGION`: Set as repository variable (e.g., `us-east-1`)

For **permanent credentials** (Access Key starts with `AKIA`):
- `AWS_ACCESS_KEY_ID`: Your IAM user access key ID
- `AWS_SECRET_ACCESS_KEY`: Your IAM user secret access key
- `AWS_REGION`: Set as repository variable (e.g., `us-east-1`)

### Required AWS Permissions

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

## Support

For questions or issues:

- **GitHub Issues**: Report problems via repository issues
- **Documentation**: Check workflow logs for detailed error messages
- **AWS Console**: Monitor S3 bucket and Bedrock ingestion jobs directly

---

**Last Updated**: August 2025  
**Version**: 1.0  
**Maintained by**: RevOps AI Framework Team