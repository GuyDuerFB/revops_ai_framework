# RevOps AI Framework V4 - Deployment Guide

## Overview

This directory contains deployment scripts and configuration for the RevOps AI Framework V4. The framework provides comprehensive revenue operations analysis through specialized AI agents with Claude 3.7 inference profiles and dev/prod alias support.

## Core Components

### V4 Deployment Scripts

- **`deploy_v4.py`** - Complete V4 architecture deployment with Manager Agent and specialized collaborators
- **`deploy_manager_agent.py`** - Deploy/update Manager Agent with collaborator configuration
- **`deploy_lead_analysis_agent.py`** - Deploy/update Lead Analysis Agent with ICP capabilities
- **`sync_knowledge_base.py`** - Synchronize knowledge base content with AWS Bedrock
- **`list_agents.py`** - List and verify agent configurations

### Configuration Files

- **`config.json`** - Complete V4 configuration with all agent IDs, aliases, and collaborators
- **`secrets.template.json`** - Template for required secrets configuration  
- **`kb_sync_state.json`** - Knowledge base synchronization state tracking
- **`firebolt_api_schema.json`** - Firebolt Lambda function API schema
- **`web_search_api_schema.json`** - Web search Lambda function API schema

### Documentation

- **`UPDATE_AGENT_INSTRUCTIONS.md`** - Guide for updating Manager Agent instructions
- **`SECURITY_CONFIG.md`** - Security configuration and best practices
- **`CLEAN_DEPLOYMENT_GUIDE.md`** - Clean environment deployment guide

## Quick Start

### 1. Complete V4 Deployment

```bash
# Deploy complete V4 architecture
python3 deploy_v4.py

# Deploy Slack integration
cd ../integrations/slack-bedrock-gateway
python3 deploy.py

# Deploy monitoring infrastructure  
cd ../../monitoring
python3 deploy-agent-tracing.py
python3 deploy_enhanced_monitoring.py
```

### 2. Individual Agent Deployment

```bash
# Deploy Manager Agent only
python3 deploy_manager_agent.py

# Deploy Lead Analysis Agent
python3 deploy_lead_analysis_agent.py
```

### 3. Knowledge Base Management

```bash
# Synchronize knowledge base content
python3 sync_knowledge_base.py

# Check synchronization status
cat kb_sync_state.json
```

## V4 Architecture

### Specialized Agent System

The V4 framework uses a Manager Agent with specialized collaborators:

#### Manager Agent (PVWGKOWSOT)
- **Role**: SUPERVISOR - Intelligent router and coordinator
- **Foundation Model**: Claude 3.7 Sonnet
- **Alias**: Manager_Agent_Prod (LH87RBMCUQ)
- **Collaborators**: 5 specialized agents

#### Specialized Collaborators

1. **Data Agent** (NOJMSQ8JPT)
   - **Role**: Data retrieval from Firebolt, Salesforce, Gong
   - **Alias**: Data_Agent_Prod (BHFBAW3YMM)
   - **Foundation Model**: Claude 3.7 Sonnet

2. **Deal Analysis Agent** (DBHYUWC6U6)
   - **Role**: Specialized deal assessment with MEDDPICC
   - **Alias**: Deal_Analysis_Agent_Prod (SQQLCFQJUA)
   - **Foundation Model**: Claude 3.7 Sonnet
   - **Features**: Embedded SQL queries, MEDDPICC evaluation

3. **Lead Analysis Agent** (IP9HPDIEPL)
   - **Role**: ICP analysis and engagement strategy
   - **Alias**: Lead_Analysis_Agent_Prod (FO8UT25HFA)
   - **Foundation Model**: Claude 3.7 Sonnet
   - **Features**: ICP fit assessment, outreach strategy

4. **WebSearch Agent** (QKRQXXPJOJ)
   - **Role**: External intelligence and company research
   - **Alias**: Web_Search_Agent_Prod (P3UKIIHUPI)
   - **Foundation Model**: Claude 3.7 Sonnet

5. **Execution Agent** (AINAPUEIZU)
   - **Role**: Action execution and system integration
   - **Alias**: Execution_Agent_Prod (RD6YGAICP0)
   - **Foundation Model**: Claude 3.7 Sonnet

### Dev/Prod Alias Strategy

Each agent maintains separate development and production aliases:

| Agent | Production Alias | Development Alias | Current Version |
|-------|------------------|-------------------|-----------------|
| Manager Agent | Manager_Agent_Prod (LH87RBMCUQ) | Manager_Agent_Dev (9MVRKEHMHX) | v4 / v2 |
| Deal Analysis | Deal_Analysis_Agent_Prod (SQQLCFQJUA) | Deal_Analysis_Agent_Dev (OAQ3FEIF2X) | v5 / v3 |
| Lead Analysis | Lead_Analysis_Agent_Prod (FO8UT25HFA) | Lead_Analysis_Agent_Dev (TBD) | v1 / DRAFT |
| Data Agent | Data_Agent_Prod (BHFBAW3YMM) | Data_Agent_Dev (DQQHJQWXFH) | v2 / v2 |
| WebSearch | Web_Search_Agent_Prod (P3UKIIHUPI) | Web_Search_Agent_Dev (2VDZRA61PT) | v2 / v1 |
| Execution | Execution_Agent_Prod (RD6YGAICP0) | Execution_Agent_Dev (8UTY0IVI7I) | v2 / v1 |

## Core Workflows

### 1. Deal Assessment Workflow
- **Trigger**: Deal-related queries (status, probability, assessment)
- **Routing**: Manager Agent → Deal Analysis Agent
- **Process**: MEDDPICC evaluation with embedded SQL queries
- **Output**: Structured assessment with dry numbers, bottom line, risks/opportunities

### 2. Lead Assessment Workflow  
- **Trigger**: Lead qualification queries
- **Routing**: Manager Agent → Lead Analysis Agent
- **Process**: ICP fit analysis, Salesforce data retrieval, web research
- **Output**: ICP scoring, confidence levels, engagement strategy

### 3. Data Analysis Workflow
- **Trigger**: Complex data queries
- **Routing**: Manager Agent → Data Agent
- **Process**: Multi-source data retrieval (Firebolt, Salesforce, Gong)
- **Output**: Comprehensive data analysis with insights

### 4. Intelligence Workflow
- **Trigger**: External research requests
- **Routing**: Manager Agent → WebSearch Agent
- **Process**: Company research, market intelligence gathering
- **Output**: Structured intelligence reports

### 5. Execution Workflow
- **Trigger**: Action requests (notifications, updates)
- **Routing**: Manager Agent → Execution Agent  
- **Process**: Webhook execution, system integration
- **Output**: Action confirmation and status

## Deployment Configuration

### Prerequisites

1. **AWS Configuration**
   - AWS CLI configured with `FireboltSystemAdministrator-740202120544` profile
   - Appropriate IAM permissions for Bedrock Agents
   - Python 3.9+ with required dependencies

2. **Secrets Configuration**
   ```bash
   cp secrets.template.json secrets.json
   # Edit secrets.json with actual credentials
   ```

3. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

The deployment scripts use the following configuration:

- **AWS Profile**: `FireboltSystemAdministrator-740202120544`
- **AWS Region**: `us-east-1`
- **AWS Account**: `740202120544`
- **Foundation Model**: `us.anthropic.claude-3-7-sonnet-20250219-v1:0`

### Lambda Functions

The framework includes supporting Lambda functions:

- **revops-firebolt-query**: SQL query execution
- **revops-gong-retrieval**: Call data retrieval  
- **revops-webhook**: Action execution
- **revops-firebolt-metadata**: Schema metadata
- **revops-firebolt-writer**: Data writing
- **revops-web-search**: External search capabilities

## Monitoring and Observability

### CloudWatch Integration

- **Log Groups**: Separate log groups for each agent and component
- **Dashboards**: Real-time monitoring dashboard
- **Alerts**: Automated alerting for errors and performance issues

### Monitoring Commands

```bash
# Check agent status
aws bedrock-agent get-agent --agent-id PVWGKOWSOT --profile FireboltSystemAdministrator-740202120544

# View agent alias configuration
aws bedrock-agent get-agent-alias --agent-id PVWGKOWSOT --agent-alias-id LH87RBMCUQ --profile FireboltSystemAdministrator-740202120544

# Monitor Slack integration logs
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow --profile FireboltSystemAdministrator-740202120544
```

### Health Checks

```bash
# List all agents
python3 list_agents.py

# Test Slack integration
cd ../integrations/slack-bedrock-gateway
python3 tests/test_integration.py
```

## Troubleshooting

### Common Issues

1. **Agent Preparation Failures**
   - Check IAM permissions for Bedrock service role
   - Verify foundation model compatibility
   - Ensure knowledge base is synchronized

2. **Collaboration Issues**
   - Verify collaborator agent aliases are correct
   - Check agent collaboration configuration
   - Ensure all collaborator agents are PREPARED

3. **Lambda Function Errors**
   - Check Lambda function permissions
   - Verify environment variables
   - Review CloudWatch logs for specific errors

### Debugging Commands

```bash
# Check agent collaboration configuration
aws bedrock-agent get-agent --agent-id PVWGKOWSOT --query 'agent.agentCollaboration' --profile FireboltSystemAdministrator-740202120544

# Verify knowledge base status
aws bedrock-agent get-knowledge-base --knowledge-base-id F61WLOYZSW --profile FireboltSystemAdministrator-740202120544

# Test agent invocation
aws bedrock-agent-runtime invoke-agent \
  --agent-id PVWGKOWSOT \
  --agent-alias-id LH87RBMCUQ \
  --session-id test-$(date +%s) \
  --input-text "test connectivity" \
  --profile FireboltSystemAdministrator-740202120544
```

## Security Configuration

### IAM Roles

- **AmazonBedrockExecutionRoleForAgents_revops**: Main execution role for all agents
- **Individual Lambda Roles**: Specific roles for each Lambda function
- **Knowledge Base Role**: Role for knowledge base operations

### Secrets Management

- **revops-slack-bedrock-secrets**: Slack integration credentials
- **firebolt-credentials**: Firebolt database credentials
- **gong-credentials**: Gong API credentials

### Network Security

- All communications use HTTPS/TLS encryption
- AWS services communicate within VPC when possible
- API Gateway with proper authentication

## Best Practices

### Deployment Strategy

1. **Test in Development**: Always test agent changes with development aliases first
2. **Gradual Rollout**: Update production aliases only after development validation
3. **Version Control**: Maintain clear versioning for all agent updates
4. **Backup Configuration**: Keep backup copies of working configurations

### Monitoring Strategy

1. **Comprehensive Logging**: Enable detailed logging for all components
2. **Performance Metrics**: Monitor response times and success rates
3. **Error Tracking**: Set up alerts for critical errors
4. **Regular Health Checks**: Automated testing of key workflows

### Security Strategy

1. **Least Privilege**: Use minimal required permissions for all roles
2. **Secret Rotation**: Regular rotation of API keys and credentials
3. **Access Auditing**: Regular review of access patterns and permissions
4. **Encryption**: Encrypt all data at rest and in transit

## Support and Maintenance

### Regular Maintenance Tasks

- **Knowledge Base Sync**: Weekly sync of knowledge base content
- **Agent Version Updates**: Monthly review and updates of agent versions
- **Credential Rotation**: Quarterly rotation of API credentials
- **Performance Review**: Weekly review of system performance metrics

### Documentation Updates

- Update this README when deploying new features
- Maintain changelog for all configuration changes
- Document any custom configurations or workarounds
- Keep troubleshooting section current with latest solutions

---

*Last Updated: July 23, 2025 | Version: V4.2 | Architecture: Specialized Agent Collaboration with Claude 3.7*