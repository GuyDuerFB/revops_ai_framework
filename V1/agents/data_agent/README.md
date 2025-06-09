# RevOps AI Framework - Schema-Aware Data Agent

## Overview

The Schema-Aware Data Agent is a core component of the RevOps AI Framework, responsible for retrieving, preprocessing, and contextualizing data from multiple sources. It is implemented as an Amazon Bedrock Agent (current agent ID: `THA3J7B4NP`) with schema-aware API definitions, AWS knowledge base integration, and specialized tool integrations.

## Key Features

- **Multi-Source Data Retrieval**: Fetches data from Firebolt DWH, Salesforce, Gong, and Slack
- **Schema-Aware Design**: Uses AWS knowledge base integration (`revops-firebolt-schema`) for comprehensive schema understanding
- **Intelligent Query Building**: Builds optimized SQL queries based on business requirements
- **Large Result Set Management**: Implements chunking strategy for handling large datasets without intermediate storage
- **Contextual Enrichment**: Adds business context, data quality information, and insights
- **Secure Credential Management**: Uses AWS Secrets Manager for secure API authentication
- **Standardized Parameter Handling**: Implements consistent default values for simplified user interaction
- **Optimized API Endpoints**: Uses validated API URL structure for reliable Firebolt connectivity

## Directory Structure

```
data_agent/
├── agent_definition.py              # Core agent implementation and schema definitions
├── deploy_agent.py                  # Script for deploying or updating agents in Amazon Bedrock
├── update_agent_info.py             # Script to retrieve info from existing Bedrock agent
├── instructions.md                  # Agent instructions for foundation model guidance
├── schema_knowledge.md              # Comprehensive schema documentation for knowledge base
├── invoke_agent.py                  # Script for invoking the agent with AWS SSO credentials
├── agent_deployment.json            # Current agent deployment details (ID, alias, action groups, etc.)
├── aws_console_deployment_guide.md  # Step-by-step guide for AWS Console deployment
├── README.md                        # This documentation file
└── tools/                           # Lambda function tools for different data sources
    └── firebolt/                    # Firebolt data warehouse integration
        └── consolidated_lambda_function.py  # Lambda implementation of query_fire function
```

## Implementation Notes

### Current Bedrock Agent Configuration

The deployed Bedrock agent has the following configuration:

- **Agent ID**: `THA3J7B4NP`
- **Primary Alias**: `DataAgent` (ID: `BMPQHI8K0O`)
- **Published Version**: 1
- **Foundation Model**: `anthropic.claude-3-sonnet-20240229-v1:0`
- **Action Group**: `firebolt_function` (ID: `IREBEG6U7I`)
- **Lambda Function**: `QueryFirebolt` (ARN: `arn:aws:lambda:us-east-1:740202120544:function:QueryFirebolt`)

### Function Schema

The agent exposes a single function:

```json
{
  "name": "query_fire",
  "description": "Execute SQL queries against Firebolt data warehouse and return structured results.",
  "parameters": {
    "query": {
      "description": "The SQL query to execute against Firebolt. Can be provided as plain SQL or wrapped in markdown code blocks",
      "type": "string",
      "required": false
    }
  }
}
```

### Knowledge Base Integration

The Data Agent uses an AWS knowledge base named `revops-firebolt-schema` that contains:

- Table definitions and relationships
- Column descriptions and data types
- Common query patterns and join strategies
- Business metrics definitions

- **Simplified User Interface**: Users only need to provide the SQL query, with all other parameters using sensible defaults
- **Default Parameters**: Standardized defaults for `secret_name` ("firebolt-api-credentials") and `region_name` ("eu-north-1")
- **Environment Configuration**: Lambda environment variables handle Firebolt-specific configuration

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

- **Agent ID**: THA3J7B4NP
- **Agent ARN**: arn:aws:bedrock:us-east-1:740202120544:agent/THA3J7B4NP
- **Foundation Model**: Claude 3 Sonnet
- **Knowledge Base**: Schema knowledge file uploaded to S3

### AWS Authentication

- **Authentication Method**: AWS SSO
- **Profile Name**: revops-dev-profile
- **Region**: us-east-1

## Working with the Agent

### Updating Schema Knowledge

1. Update schema_knowledge.md with latest schema information
2. Upload to S3 with the deploy script:
   ```
   python deploy_agent.py --upload-knowledge --profile revops-dev-profile
   ```

### Retrieving Existing Agent Info

1. Get details of the existing Bedrock agent:
   ```
   python update_agent_info.py --agent-id THA3J7B4NP --profile revops-dev-profile
   ```

### Testing the Agent

### Prerequisites

1. Configure AWS SSO with appropriate credentials:
   ```bash
   aws configure sso --profile revops-dev-profile
   aws sso login --profile revops-dev-profile
   ```

2. Ensure your AWS SSO profile has permissions for:
   - Amazon Bedrock agent access and invocation
   - S3 knowledge base access and modification
   - Lambda function access (if modifying tools)

### Working with Existing Agent

1. Retrieve information about the existing Bedrock agent:
   ```bash
   python agents/data_agent/update_agent_info.py --agent-id THA3J7B4NP --profile revops-dev-profile
   ```

2. Update schema knowledge in S3:
   ```bash
   python agents/data_agent/deploy_agent.py --upload-knowledge --profile revops-dev-profile
   ```

3. Invoke the agent with a query:
   ```bash
   python agents/data_agent/invoke_agent.py --prompt "Show me tables related to revenue" --profile revops-dev-profile
   ```

### Usage Examples

```bash
# View sample queries
python agents/data_agent/invoke_agent.py --examples

# Invoke with a specific prompt
python agents/data_agent/invoke_agent.py --prompt "Gather all data required for A1 analysis. Target: enterprise accounts." --profile revops-dev-profile

# Maintain conversation context with session ID
python agents/data_agent/invoke_agent.py --prompt "Show more details about the last query" --session-id "your_previous_session_id" --profile revops-dev-profile
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
