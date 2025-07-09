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

## Clean Architecture
This directory contains only essential deployment files. All debugging, testing, and archived scripts have been removed to maintain clarity and security.