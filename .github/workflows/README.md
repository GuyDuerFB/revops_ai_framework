# GitHub Actions Workflows

This directory contains automated workflows for the RevOps AI Framework.

## Available Workflows

### 1. Knowledge Base Sync (`knowledge-base-sync.yml`)
**Trigger**: Push to main branch with changes to `knowledge_base/**/*.md` files  
**Purpose**: Automatically synchronizes knowledge base files to S3 and triggers Bedrock ingestion

**Features**:
- Detects changes in knowledge base markdown files
- Syncs only changed/added files to S3
- Removes deleted files from S3
- Triggers Bedrock knowledge base ingestion
- Excludes `firebolt_schema/` for controlled schema management

### 2. Agent Creation (`create-agent.yml`)
**Trigger**: Manual (`workflow_dispatch`)  
**Purpose**: Creates new agent directory structure with templated instructions

**Inputs**:
- `agent_name` (required): Name of the new agent
- `agent_description` (optional): Brief description of the agent purpose

**Features**:
- Creates sanitized directory name under `agents/`
- Copies and processes agent template with placeholders
- Commits changes to repository with descriptive commit message
- Provides guidance on next steps for customization

**Usage**:
1. Go to Actions tab in GitHub
2. Select "Agent Creation" workflow
3. Click "Run workflow"
4. Enter agent name and optional description
5. Review created directory and customize `instructions.md`

### 3. Agent Deployment (`deploy-agent.yml`)
**Trigger**: Manual (`workflow_dispatch`)  
**Purpose**: Deploys agent to AWS Bedrock with consistent configuration

**Inputs**:
- `agent_name` (required): Name of agent directory to deploy
- `environment` (optional): Deployment environment (dev/staging/prod, default: dev)
- `dry_run` (optional): Preview changes without actual deployment

**Features**:
- Validates agent directory structure and instructions
- Creates Bedrock Agent with same configuration as existing agents
- Associates knowledge base and configures permissions
- Creates environment-specific alias
- Provides deployment summary and next steps

**Usage**:
1. Ensure agent instructions are customized (no template placeholders)
2. Go to Actions tab in GitHub
3. Select "Agent Deployment" workflow
4. Click "Run workflow"
5. Enter agent name and select environment
6. Optionally enable dry-run for preview

## Authentication

All workflows use the same OIDC authentication as the Knowledge Base Sync:
- **Role**: `arn:aws:iam::740202120544:role/GitHubActionsRevOpsKBSyncRole`
- **Region**: `us-east-1`
- **Permissions**: Read/write to S3, Bedrock agent management

## Supporting Scripts

### `.github/scripts/create-agent.py`
Python script that handles agent creation:
- Name sanitization and validation
- Template processing with placeholder replacement
- Directory structure creation
- Error handling and cleanup

### `.github/scripts/deploy-agent.py`
Python script that handles AWS deployment:
- Prerequisites validation
- Bedrock Agent creation with consistent configuration
- Knowledge base association
- Alias creation and management
- Post-deployment validation

### `.github/scripts/agent-config-template.json`
Configuration template with:
- Foundation model settings matching existing agents
- IAM role and permission configurations
- Knowledge base association settings
- Environment-specific alias configurations

## Agent Development Workflow

1. **Create Agent Structure**:
   ```
   Actions → Create New Agent → Enter name/description
   ```

2. **Customize Instructions**:
   ```
   Edit agents/[agent-name]/instructions.md
   Replace [CUSTOMIZE: ...] placeholders
   Define output format
   Test instructions locally
   ```

3. **Deploy to Development**:
   ```
   Actions → Deploy Agent to AWS → Select dev environment
   Test through RevOps AI Framework
   Monitor CloudWatch logs
   ```

4. **Deploy to Production**:
   ```
   Actions → Deploy Agent to AWS → Select prod environment
   Update multi-agent policies if needed
   Validate production deployment
   ```

## Troubleshooting

### Common Issues

**Agent Creation**:
- Directory already exists → Choose different name or remove existing directory
- Invalid characters in name → Script will sanitize automatically
- Template not found → Verify `generic_agent_instructions_template_bedrock_ai_framework.md` exists

**Agent Deployment**:
- Template placeholders remain → Customize instructions.md before deployment
- AWS permission denied → Verify GitHub Actions IAM role permissions
- Agent creation timeout → Check Bedrock service status in AWS Console
- Knowledge base association fails → Verify knowledge base is active

### Debugging

1. **Check Workflow Logs**: Actions tab → Select workflow run → View detailed logs
2. **Validate AWS Resources**: Use AWS Console to verify agent creation
3. **Test Agent Locally**: Use deployment script with `--dry-run` flag
4. **Monitor CloudWatch**: Check `/aws/lambda/revops-*` log groups

## Security

- All workflows use OIDC for secure AWS authentication
- No long-term AWS credentials stored in repository
- Least privilege access with specific IAM roles
- Git operations use GitHub Action bot token

## Maintenance

- **Template Updates**: Modify `generic_agent_instructions_template_bedrock_ai_framework.md`
- **Configuration Changes**: Update `agent-config-template.json`
- **Script Updates**: Modify Python scripts in `.github/scripts/`
- **Workflow Updates**: Edit YAML files and test with dry-run