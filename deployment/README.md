# RevOps AI Framework - Deployment Management

## Overview

This directory contains all deployment scripts, configuration, and documentation for the RevOps AI Framework. The structure is organized into logical subdirectories for maintainability and clarity.

## Directory Structure

```
deployment/
├── README.md                    # This overview document
├── scripts/                     # Deployment and maintenance scripts
│   ├── deploy.py               # Unified deployment script
│   ├── validate_deployment.py  # System health validation
│   └── sync_knowledge_base.py  # Knowledge base synchronization
├── config/                      # Configuration files
│   ├── config.json             # Master configuration
│   ├── secrets.template.json   # AWS Secrets template
│   ├── firebolt_api_schema.json # Firebolt API schema
│   ├── web_search_api_schema.json # Web search API schema
│   └── kb_sync_state.json      # Knowledge base sync state (auto-generated)
└── docs/                        # Documentation
    ├── README.md               # Complete deployment guide (this file)
    ├── agent_management.md     # Agent update procedures
    └── security_config.md      # Security configuration details
```

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
cd deployment/scripts/
python3 deploy.py
```

### Deploy Specific Agent
```bash
cd deployment/scripts/
python3 deploy.py --agent manager
python3 deploy.py --agent data
```

### Validate System Health
```bash
cd deployment/scripts/
python3 validate_deployment.py
```

### Sync Knowledge Base
```bash
cd deployment/scripts/
python3 sync_knowledge_base.py
```

## Configuration Management

### Master Configuration
All system configuration is centralized in `config/config.json`:
- Agent IDs and settings
- Lambda function configurations  
- AWS resource ARNs
- Foundation model specifications

### Environment Variables
Required AWS profile: `FireboltSystemAdministrator-740202120544`
Required region: `us-east-1`

### Secrets Management
Template for AWS Secrets Manager configuration is in `config/secrets.template.json`

## Scripts Overview

### `scripts/deploy.py`
**Unified deployment script** for all agents and components.

```bash
# Deploy all agents
python3 deploy.py

# Deploy specific agent
python3 deploy.py --agent manager

# Validation only (no changes)
python3 deploy.py --validate-only

# List current agents
python3 deploy.py --list-agents
```

### `scripts/validate_deployment.py`
**Comprehensive system health validation** with detailed diagnostics.

```bash
# Full system validation
python3 validate_deployment.py

# Component-specific validation
python3 validate_deployment.py --agents
python3 validate_deployment.py --lambdas
python3 validate_deployment.py --integrations
python3 validate_deployment.py --knowledge-base
```

### `scripts/sync_knowledge_base.py`
**Knowledge base synchronization** to S3 and Bedrock ingestion.

```bash
# Manual sync with detailed output
python3 sync_knowledge_base.py
```

## Agent Management

### Update Agent Instructions
1. Edit the agent instructions file: `../agents/{agent_name}/instructions.md`
2. Deploy the update: `python3 scripts/deploy.py --agent {agent_name}`
3. Validate: `python3 scripts/validate_deployment.py --agents`

### Add New Agent
1. Create agent directory: `../agents/new_agent/`
2. Add configuration to `config/config.json`
3. Deploy: `python3 scripts/deploy.py --agent new_agent`

See `docs/agent_management.md` for detailed procedures.

## Knowledge Base Management

### Automatic Sync
Changes to `../knowledge_base/*.md` files are automatically synced via GitHub Actions when committed to main branch.

### Manual Sync
Use `scripts/sync_knowledge_base.py` for immediate synchronization.

### Monitor Status
Check `config/kb_sync_state.json` for last sync status and timestamps.

## Security Configuration

All security settings and configurations are documented in `docs/security_config.md`:
- API Gateway client certificates
- IAM roles and permissions
- Encryption settings
- Access control policies

## Troubleshooting

### Common Issues

**Agent Deployment Fails**
1. Run validation: `python3 scripts/validate_deployment.py --agents`
2. Check AWS credentials: `aws sts get-caller-identity`
3. Verify agent status in AWS Bedrock console

**Knowledge Base Sync Issues**
1. Check S3 permissions and bucket access
2. Review sync state: `cat config/kb_sync_state.json`
3. Verify Bedrock knowledge base status

**Lambda Function Problems**
1. Run validation: `python3 scripts/validate_deployment.py --lambdas`
2. Check CloudWatch logs for errors
3. Verify IAM role permissions

### Getting Help
- Review main system README: `../README.md`
- Check CloudWatch logs for runtime errors
- Use validation scripts for comprehensive diagnostics

## Deployment Workflow

1. **Prerequisites Check**: Scripts validate AWS credentials and permissions
2. **Configuration Validation**: Verify all required settings are present
3. **Incremental Updates**: Only changed components are redeployed
4. **Health Validation**: Automatic system health checks after deployment
5. **Status Reporting**: Clear success/failure reporting with actionable errors

## File Naming Conventions

- **Scripts**: `snake_case.py` (executable Python scripts)
- **Config**: `snake_case.json` (configuration and data files)  
- **Docs**: `snake_case.md` (documentation files)
- **Consistency**: All files use lowercase with underscores

---

**Last Updated**: August 2025  
**Version**: V5.1  
**Architecture**: Production-ready Bedrock Agent collaboration with organized deployment structure