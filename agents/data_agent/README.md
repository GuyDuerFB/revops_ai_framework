# RevOps AI Framework - Schema-Aware Data Agent

## Overview

The Schema-Aware Data Agent is a core component of the RevOps AI Framework, responsible for retrieving, preprocessing, and contextualizing data from multiple sources. It is implemented as an Amazon Bedrock Agent with schema-aware API definitions, AWS knowledge base integration, and specialized tool integrations.

## Key Features

- **Multi-Source Data Retrieval**: Fetches data from Firebolt DWH, Salesforce, Gong, and Slack
- **Schema-Aware Design**: Uses AWS knowledge base integration (`revops-firebolt-schema`) for comprehensive schema understanding
- **Intelligent Query Building**: Builds optimized SQL queries based on business requirements
- **Large Result Set Management**: Implements chunking strategy for handling large datasets without intermediate storage
- **Contextual Enrichment**: Adds business context, data quality information, and insights
- **Secure Credential Management**: Uses AWS Secrets Manager for secure API authentication

## Directory Structure

```
data_agent/
├── agent_definition.py              # Core agent implementation and schema definitions
├── deploy_agent.py                  # Script for deploying the agent to Amazon Bedrock
├── instructions.md                  # Agent instructions for foundation model guidance
├── schema_knowledge.md              # Comprehensive schema documentation for knowledge base
├── invoke_agent.py                  # Sample script for invoking the agent
├── aws_console_deployment_guide.md  # Step-by-step guide for AWS Console deployment
├── README.md                        # This documentation file
└── tools/                           # Lambda function tools for different data sources
    ├── firebolt/                    # Firebolt data warehouse integration
    ├── salesforce/                  # Salesforce CRM integration (future)
    ├── gong/                        # Gong conversation analytics integration (future)
    └── slack/                       # Slack communication integration (future)
```

## Schema-Aware Knowledge Base Integration

The Data Agent integrates with AWS knowledge base (`revops-firebolt-schema`) to provide comprehensive schema awareness. This enables the agent to:

1. Understand database tables, columns, and their relationships
2. Build optimized SQL queries with proper joins and filters
3. Apply business logic and metrics calculations correctly
4. Generate insights based on domain-specific knowledge
5. Handle complex analysis patterns (A1-A6) efficiently

The knowledge base contains detailed information about:
- Table definitions and column descriptions
- Primary and foreign key relationships
- Common join patterns and query templates
- Business metrics definitions and calculation methods
- Analysis types and their implementation patterns

## Data Chunking Mechanism

For large query results, the Data Agent implements a sophisticated chunking strategy that eliminates the need for intermediate storage:

1. Initial query returns metadata and first chunk of data
2. Analysis Agent can request additional chunks as needed
3. Each chunk maintains context about its position in the sequence
4. Progress tracking for multi-chunk operations
5. Optimized API endpoint structure for reliable data retrieval
6. Configurable chunk size based on query complexity

Benefits of this approach:
- Eliminates Lambda payload size limitations
- Improves performance by avoiding S3 storage requirements
- Enables progressive analysis without waiting for complete datasets
- Enhances fault tolerance through partial result processing

## AWS Knowledge Base Setup

The schema_knowledge.md file contains all the information needed for the AWS knowledge base:

1. Create a new knowledge base in AWS Bedrock
2. Name it `revops-firebolt-schema`
3. Upload the schema_knowledge.md file
4. Associate the knowledge base with your Bedrock agent

## Deployment Instructions

### Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.9+ with boto3 installed
- Lambda functions deployed for each data source tool

### Deploy the Agent

```bash
# Set environment variables for Lambda function names
export FIREBOLT_LAMBDA_NAME=revops-firebolt-tool
export SALESFORCE_LAMBDA_NAME=revops-salesforce-tool
export GONG_LAMBDA_NAME=revops-gong-tool
export SLACK_LAMBDA_NAME=revops-slack-tool

# Deploy the agent
python deploy_agent.py --agent-name RevOpsDataAgent --alias-name Production
```

### Invoke the Agent

```bash
# View sample query examples
python invoke_agent.py --examples

# Invoke with a specific prompt
python invoke_agent.py --prompt "Gather all data required for A1 analysis. Target: enterprise accounts."
```

## Adding New Data Sources

To add a new data source:

1. Create a new Lambda function tool in the `tools/` directory
2. Add a new action group definition in `agent_definition.py`
3. Update the `get_agent_lambda_arns()` function in `deploy_agent.py`
4. Deploy the updated agent

## Security Considerations

- All credentials are stored in AWS Secrets Manager
- Lambda functions use IAM roles with least privilege
- Data classification is applied to all retrieved information
- PII handling follows GDPR and CCPA guidelines
