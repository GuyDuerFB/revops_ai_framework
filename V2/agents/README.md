# RevOps AI Framework V2 - Agents

This directory contains implementations of the various AI agents that form the core of the RevOps AI Framework.

## Overview

The agents in this directory are responsible for different aspects of the framework's functionality:

1. **Data Agent**: Retrieves and processes data from various sources
2. **Decision Agent**: Makes decisions based on data and business rules
3. **Execution Agent**: Executes actions based on decisions

Together, these agents form a pipeline that enables automated revenue operations workflows.

## Directory Structure

```
agents/
├── README.md                  # This file
├── __init__.py                # Package initialization
├── data_agent/                # Data retrieval and processing agent
├── decision_agent/            # Decision-making agent
└── execution_agent/           # Action execution agent
```

## Agent Architecture

Each agent follows a similar architecture:

1. **Input Handler**: Processes incoming requests and normalizes inputs
2. **Core Logic**: Implements the agent's main functionality
3. **Output Handler**: Formats and validates outputs
4. **State Management**: Tracks agent state across invocations
5. **Logging & Metrics**: Monitors agent performance and activity

## Usage

Agents are typically invoked as part of a flow, but can also be invoked directly via their Lambda entry points.

### Direct Invocation

```python
import boto3

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='revops-ai-v2-data-agent',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "data_source": "firebolt",
        "query": "get_customer_data",
        "parameters": {
            "customer_id": "cust-12345"
        }
    })
)
```

### Integration with Flows

See the `/flows` directory for examples of how agents are integrated into complete workflows.

## Development

### Adding a New Agent

1. Create a new subdirectory for your agent
2. Implement the standard agent interface:
   - `handler.py`: Lambda entry point
   - `agent.py`: Core agent logic
   - `config.py`: Agent configuration
3. Update the agent registry in the parent package
4. Add tests in the `/tests/unit/agents/` directory

### Configuration

Agent configuration is loaded from environment variables and/or configuration files. See each agent's documentation for specific configuration options.

## Deployment

Agents are deployed as AWS Lambda functions with the necessary IAM permissions to interact with other AWS services and external APIs. See the `/deployment` directory for deployment scripts and infrastructure definitions.
