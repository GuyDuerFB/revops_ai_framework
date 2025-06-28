# RevOps AI Framework V2 - Data Agent

The Data Agent is responsible for retrieving and processing data from various sources to support the RevOps AI workflow.

## Overview

The Data Agent serves as the data retrieval and processing component of the RevOps AI Framework. Its current implementation focuses on connecting to Firebolt data warehouse and providing query capabilities based on schema knowledge.

## Current Implementation

```
data_agent/
├── README.md            # This file
├── data_agent.py         # Core agent implementation
└── instructions.md      # Agent instructions and capabilities
```

## Current Capabilities

The Data Agent currently focuses primarily on Firebolt database integration:

- Access to Firebolt schema information via the knowledge base
- Natural language query interpretation for data retrieval

## Integration

The Data Agent is designed to work with AWS Bedrock and leverage the Firebolt schema knowledge base to understand database structure and generate appropriate queries.

## Deployment

The agent is deployed through Terraform configuration in the `deployment/terraform/modules/agent` directory, which sets up the AWS Bedrock agent with the appropriate resources and permissions.

Future enhancements to the Data Agent capabilities are documented in the main ROADMAP.md file.


