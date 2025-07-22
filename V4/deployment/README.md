# RevOps AI Framework - Deployment Guide

## Overview

This directory contains deployment scripts and configuration for the RevOps AI Framework V4. The framework provides comprehensive revenue operations analysis through specialized AI agents with dev/prod alias support.

## Core Components

### Production Deployment Scripts

- **`deploy_production.py`** - Main deployment script for core framework components
- **`update_agent_with_alias.py`** - Update Manager Agent instructions and alias routing
- **`sync_knowledge_base.py`** - Synchronize knowledge base content with AWS Bedrock

### Configuration Files

- **`config.json`** - Core AWS configuration (agent IDs, regions, profiles)
- **`secrets.template.json`** - Template for required secrets configuration
- **`kb_sync_state.json`** - Knowledge base synchronization state tracking

### Documentation

- **`UPDATE_AGENT_INSTRUCTIONS.md`** - Comprehensive guide for updating agent instructions
- **`SECURITY_CONFIG.md`** - Security configuration and best practices

## Quick Start

### 1. Initial Deployment

```bash
# Deploy core framework
python3 deploy_production.py

# Deploy Slack integration
cd ../integrations/slack-bedrock-gateway
python3 deploy.py

# Deploy monitoring infrastructure  
cd ../../monitoring
python3 deploy-agent-tracing.py
python3 deploy_enhanced_monitoring.py
```

### 2. Update Agent Instructions

```bash
# Update Decision Agent with new instructions
python3 update_agent_with_alias.py

# Or update without alias changes
python3 update_agent_with_alias.py --no-alias
```

### 3. Sync Knowledge Base

```bash
# Synchronize knowledge base content
python3 sync_knowledge_base.py
```

## Architecture

### Multi-Agent System

The framework uses a supervisor pattern with these agents:

- **Decision Agent** (`TCX9CGOKBR`) - Orchestrates workflows and makes strategic decisions
- **Data Agent** (`9B8EGU46UV`) - Queries Firebolt DWH, Gong calls, and Salesforce
- **WebSearch Agent** (`83AGBVJLEB`) - Gathers external intelligence and research
- **Execution Agent** (`UWMCP4AYZX`) - Performs operational actions and notifications

### Core Workflows

1. **Deal Assessment** - Comprehensive deal status analysis with dual data collection
2. **Lead Assessment** - ICP alignment scoring and qualification
3. **Customer Risk Assessment** - Churn risk and usage pattern analysis
4. **Pipeline Reviews** - Forecasting and opportunity analysis
5. **Consumption Analysis** - FBU utilization and optimization

## Enhanced Deal Review Flow

The framework implements a robust deal review process:

### Step 1A: Opportunity Data Collection
- SFDC opportunity details, MEDDPICC fields, account information
- Sales activity tracking and owner resolution

### Step 1B: Call Data Collection  
- Gong call summaries via `gong_call_f` table
- Stakeholder engagement patterns and conversation insights

### Step 2: Market Context (Optional)
- External company research and competitive intelligence

### Step 3: Deal Assessment Analysis
- Risk analysis across technical, engagement, and competitive dimensions
- Data conflict resolution and comprehensive recommendations

## Monitoring and Observability

### CloudWatch Integration

- **Log Groups**: Structured logging across conversation, collaboration, data operations
- **Dashboards**: Real-time monitoring of agent performance and deal assessments
- **Alarms**: Automated alerts for failure rates and performance issues

### Enhanced Monitoring

```bash
# Generate deal assessment report
cd ../monitoring
python3 enhanced_deal_monitoring.py --report

# Analyze specific conversation
python3 enhanced_deal_monitoring.py --correlation-id <correlation_id>
```

## Configuration Management

### AWS Profile Setup

The framework uses the `FireboltSystemAdministrator-740202120544` profile:

```bash
# Configure AWS SSO
aws configure sso --profile FireboltSystemAdministrator-740202120544

# Login when needed
aws sso login --profile FireboltSystemAdministrator-740202120544
```

### Environment Variables

Key configuration parameters are stored in `config.json`:

```json
{
  "profile_name": "FireboltSystemAdministrator-740202120544",
  "region_name": "us-east-1",
  "decision_agent": {
    "agent_id": "TCX9CGOKBR",
    "agent_alias_id": "BKLREFH3L0"
  }
}
```

## Troubleshooting

### Common Issues

1. **Agent Version Conflicts**
   - Ensure alias points to correct agent version
   - Use `update_agent_with_alias.py` to sync versions

2. **Data Retrieval Failures**
   - Check Firebolt and Gong Lambda permissions
   - Verify collaborator agent configurations

3. **Monitoring Gaps**
   - Ensure agent tracing is properly configured
   - Check CloudWatch log group permissions

### Debug Commands

```bash
# Check agent status
aws bedrock-agent get-agent --agent-id TCX9CGOKBR --profile FireboltSystemAdministrator-740202120544

# View recent logs
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow --profile FireboltSystemAdministrator-740202120544

# Test integration
@RevBot could you tell me about the status of the IXIS deal?
```

## Security

- All secrets managed through AWS Secrets Manager
- IAM roles follow principle of least privilege
- Agent collaboration restricted to authorized aliases
- Comprehensive audit logging enabled

For detailed security configuration, see `SECURITY_CONFIG.md`.

## Support

For deployment issues or questions:

1. Check CloudWatch logs for error details
2. Review agent tracing dashboards
3. Use enhanced monitoring tools for deal assessment analysis
4. Consult knowledge base workflows for process guidance

---

**Framework Version**: V3  
**Last Updated**: July 2025  
**Deployment Region**: us-east-1