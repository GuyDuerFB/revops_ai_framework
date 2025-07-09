# RevOps AI Framework - Deployment

Clean deployment directory for the RevOps AI Framework V2.

## Recent Updates (July 9, 2025)
- ✅ Enhanced date context awareness for temporal analysis
- ✅ Improved Gong API integration with priority-based data access
- ✅ Competitive intelligence analysis from sales call transcripts
- ✅ Expanded knowledge base with comprehensive schema documentation

## Files

### Core Deployment
- **`deploy_production.py`** - Main production deployment script
- **`config.json`** - Agent and infrastructure configuration
- **`requirements.txt`** - Python dependencies for deployment

### Configuration
- **`secrets.json`** - Contains actual secrets for deployment (git-ignored for security)
- **`secrets.template.json`** - Template for new environments

## Usage

### Prerequisites
1. AWS CLI configured with `FireboltSystemAdministrator-740202120544` profile
2. Python 3.9+ with dependencies installed
3. Secrets file configured

### Quick Deployment
```bash
cd deployment

# Install dependencies
pip install -r requirements.txt

# Secrets are already configured in secrets.json (git-ignored)
# For new environments, copy from template:
# cp secrets.template.json secrets.json

# Run deployment
python3 deploy_production.py
```

### Configuration
- All agent IDs, Lambda ARNs, and infrastructure details are in `config.json`
- Deployment status is tracked within the configuration file
- Secrets should be stored in AWS Secrets Manager for production use

## Security Notes
- **`secrets.json` is git-ignored** - contains actual secrets for deployment
- **`secrets.template.json`** - safe template for new environments  
- Use AWS Secrets Manager for production credentials
- Rotate credentials regularly
- Follow principle of least privilege for IAM roles

## Knowledge Base Sync Script

### Overview
The `sync_knowledge_base.py` script automatically synchronizes local knowledge base files with AWS S3 and triggers Amazon Bedrock knowledge base ingestion.

### Features
- **File Change Detection**: Uses MD5 hashing to detect only changed files
- **S3 Upload**: Uploads changed files to the configured S3 bucket
- **Knowledge Base Sync**: Triggers Amazon Bedrock ingestion job
- **Progress Tracking**: Maintains sync state between runs
- **Comprehensive Reporting**: Generates detailed operation summaries

### Usage
```bash
cd deployment
python3 sync_knowledge_base.py
```

### Configuration
The script is configured for the RevOps AI Framework with the following settings:
- **Knowledge Base ID**: `F61WLOYZSW`
- **S3 Bucket**: `revops-ai-framework-kb-740202120544`
- **Data Source ID**: `0HMI5RHYUS`
- **AWS Profile**: `FireboltSystemAdministrator-740202120544`
- **Region**: `us-east-1`

### Supported File Types
- `.txt` - Plain text files
- `.md` - Markdown files
- `.pdf` - PDF documents
- `.doc/.docx` - Microsoft Word documents
- `.html` - HTML files
- `.csv` - CSV files
- `.json` - JSON files

### Operation Flow
1. **Verify S3 Access**: Checks that the S3 bucket exists and is accessible
2. **Detect Changes**: Scans knowledge base directory for changed files
3. **Upload Files**: Uploads only changed files to S3
4. **Sync Knowledge Base**: Triggers Bedrock ingestion job
5. **Generate Summary**: Creates detailed operation report

### Output Files
- `kb_sync_state.json` - Maintains sync state between runs
- `kb_sync_summary_YYYYMMDD_HHMMSS.txt` - Operation summary

## Clean Architecture
This directory contains only essential deployment files. All debugging, testing, and archived scripts have been removed to maintain clarity and security.