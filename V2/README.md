# RevOps AI Framework V2

An agentic system for Firebolt RevOps built with AWS Bedrock, designed to provide insights and automate actions related to deal quality and consumption patterns.

## Architecture Overview

The framework uses AWS Bedrock Agents and Flows to create a multi-agent system that can:
1. Analyze data from multiple sources
2. Make intelligent decisions based on business rules
3. Execute actions through integrations

### Core Components

```
┌─────────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│                     │    │                   │    │                   │
│  Data Analysis      │    │  Decision         │    │  Execution        │
│  Agent              ├───►│  Agent            ├───►│  Agent            │
│                     │    │                   │    │                   │
└─────────────────────┘    └───────────────────┘    └───────────────────┘
         ▲                          ▲                        │
         │                          │                        │
         │                          │                        ▼
┌─────────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│                     │    │                   │    │                   │
│  Knowledge Base     │    │  Action           │    │  Integration      │
│  (Schema/Queries)   │    │  Repository       │    │  Hub (Webhooks)   │
│                     │    │                   │    │                   │
└─────────────────────┘    └───────────────────┘    └───────────────────┘
```

## Supported Scenarios

1. **Deal Quality Assessment**
   - Analyze pipeline against Ideal Customer Profile (ICP)
   - Identify data quality issues
   - Flag major use cases and potential blockers

2. **Consumption Pattern Analysis**
   - Monitor changes in consumption patterns
   - Identify potential churn risks
   - Suggest proactive next steps

## Setup and Configuration

### Prerequisites
- AWS CLI installed and configured
- AWS IAM permissions for Bedrock, Lambda, Secrets Manager, and S3
- Firebolt account with API access

### Deployment
```bash
# Navigate to the deployment directory
cd deployment

# Install dependencies
pip install -r requirements.txt

# Deploy the framework
python deploy_framework.py
```

## Usage

Once deployed, the framework can be triggered by:
1. **Scheduled runs**: Configured to run at specific times via EventBridge
2. **On-demand invocation**: Triggered through the provided CLI tools

## Development and Extension

To extend the framework with new capabilities:
1. Add new action groups to the appropriate agent
2. Create Lambda functions for custom tools
3. Update the knowledge base with new schema information
4. Modify flow definitions to incorporate new agents or steps
