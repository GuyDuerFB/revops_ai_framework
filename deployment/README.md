# RevOps AI Framework - Deployment Management

## Overview

This directory contains deployment scripts and configuration for the RevOps AI Framework. All deployment operations are centralized here for consistency and maintainability.

## Files and Purpose

### Core Configuration
- **`config.json`** - Master configuration for all agents, Lambda functions, and AWS resources
- **`secrets.template.json`** - Template for AWS Secrets Manager configuration

### Active Scripts
- **`deploy.py`** - Unified deployment script for agents and Lambda functions  
- **`sync_knowledge_base.py`** - Knowledge base synchronization to S3 and Bedrock
- **`validate_deployment.py`** - System validation and health checks

### Supporting Files
- **`kb_sync_state.json`** - Knowledge base synchronization state (auto-generated)
- **`firebolt_api_schema.json`** - API schema for Firebolt integrations
- **`web_search_api_schema.json`** - API schema for web search functions

### Documentation
- **`DEPLOYMENT_GUIDE.md`** - Step-by-step deployment procedures
- **`TROUBLESHOOTING.md`** - Common issues and solutions

## Quick Start

### Prerequisites
```bash
# Ensure AWS CLI is configured
aws configure sso --profile FireboltSystemAdministrator-740202120544

# Verify Python environment
python3 --version  # Requires 3.9+
```

### Deploy All Components
```bash
cd deployment/
python3 deploy.py
```

### Deploy Specific Agent
```bash
# Deploy manager agent only
python3 deploy.py --agent manager

# Deploy with validation
python3 deploy.py --validate-only
```

### Sync Knowledge Base
```bash
python3 sync_knowledge_base.py
```

### Validate Deployment
```bash
python3 validate_deployment.py
```

## Configuration Management

### Agent Configuration
All agent settings are centralized in `config.json`:

```json
{
  "manager_agent": {
    "agent_id": "PVWGKOWSOT",
    "foundation_model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "instructions_file": "agents/manager_agent/instructions.md"
  }
}
```

### Environment Variables
Required environment variables are documented in each deployment script.

### AWS Permissions
All scripts use the profile: `FireboltSystemAdministrator-740202120544`

Required permissions are documented in the main README.md.

## Deployment Workflow

1. **Validation**: Scripts validate prerequisites and configuration
2. **Incremental Updates**: Only changed components are redeployed
3. **Health Checks**: Automatic validation after deployment
4. **Rollback**: Failed deployments can be rolled back

## Agent Management

### Update Agent Instructions
```bash
# Edit the instructions file
vim ../agents/manager_agent/instructions.md

# Deploy the update
python3 deploy.py --agent manager
```

### Add New Agent
1. Create agent directory in `../agents/new_agent/`
2. Add configuration to `config.json`
3. Run deployment: `python3 deploy.py --agent new_agent`

## Knowledge Base Management

### Automatic Sync
Knowledge base files are automatically synced when:
- Changes are committed to main branch
- GitHub Action runs the sync workflow

### Manual Sync
```bash
python3 sync_knowledge_base.py
```

### Monitor Sync Status
```bash
# Check sync state
cat kb_sync_state.json

# View S3 bucket contents
aws s3 ls s3://revops-ai-framework-kb-740202120544/knowledge-base/ --recursive
```

## Troubleshooting

### Common Issues

**Agent Update Fails**
1. Check agent status: `aws bedrock-agent get-agent --agent-id AGENT_ID`
2. Verify IAM permissions
3. Check CloudWatch logs for detailed errors

**Knowledge Base Sync Fails**
1. Verify S3 bucket permissions
2. Check AWS credentials
3. Review sync state file for errors

**Lambda Function Deployment Fails**
1. Check function size limits
2. Verify IAM role permissions
3. Review deployment logs

### Getting Help
- Check main README.md for system-wide documentation
- Review CloudWatch logs for runtime errors
- Use `validate_deployment.py` for comprehensive health checks

## Security

- All credentials managed through AWS Secrets Manager
- IAM roles follow least privilege principle
- API endpoints secured with certificate authentication
- Detailed security configuration in main README.md

---

**Last Updated**: August 2025  
**Version**: V5.1  
**Architecture**: Production-ready with Bedrock Agent collaboration