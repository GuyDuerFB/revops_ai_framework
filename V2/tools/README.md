# RevOps AI Framework V2 - Tools

This directory contains utility tools and integrations that support the RevOps AI Framework's operations.

## Overview

The tools directory provides specialized components that perform specific functions required by the framework's agents. These include data connectors, API integrations, webhook handlers, and utility services that enhance the capabilities of the framework.

## Directory Structure

```
tools/
├── README.md                 # This file
├── firebolt/                 # Firebolt database integration tools
│   ├── README.md             # Firebolt tools documentation
│   ├── metadata_lambda/      # Metadata retrieval Lambda
│   ├── query_lambda/         # Query execution Lambda
│   └── writer_lambda/        # Data writing Lambda
├── gong/                     # Gong integration tools
│   ├── api_client.py         # Gong API client
│   └── processors/           # Gong data processors
├── webhook/                  # Webhook integration
│   ├── README.md             # Webhook documentation
│   ├── lambda_function.py              # Webhook handler
│   ├── modules/              # Modular webhook components
│   └── utils/                # Webhook utilities
└── common/                   # Shared utilities and helpers
    ├── auth/                 # Authentication utilities
    ├── logging/              # Logging configuration
    └── validation/           # Input validation utilities
```

## Available Tools

### Firebolt Tools

The Firebolt tools provide integration with the Firebolt data warehouse:

- **Metadata Lambda**: Retrieves metadata about tables and columns
- **Query Lambda**: Executes SQL queries against Firebolt
- **Writer Lambda**: Writes data to Firebolt tables

For detailed documentation, see the [Firebolt Tools README](/tools/firebolt/README.md).

### Gong Tools

The Gong tools provide integration with Gong's conversation intelligence platform:

- **API Client**: Client for interacting with the Gong API
- **Processors**: Components for processing Gong call data
- **Analyzers**: Tools for analyzing conversation content

### Webhook Tools

The webhook tools enable integration with external systems via webhooks:

- **Consolidated Lambda**: A unified webhook handler supporting multiple modes:
  - Direct webhook invocation
  - Queue-based asynchronous processing
  - AWS Bedrock Agent compatibility

For detailed documentation, see the [Webhook Tools README](/tools/webhook/README.md).

### Common Utilities

The common utilities provide shared functionality used across the framework:

- **Authentication**: Utilities for handling authentication
- **Logging**: Standardized logging configuration
- **Validation**: Input validation and sanitization

## Usage

### Using Tools in Agents

Tools are typically imported and used by the framework's agents:

```python
from tools.firebolt.client import FireboltClient
from tools.webhook.client import WebhookClient

# Using the Firebolt client
firebolt = FireboltClient()
results = firebolt.execute_query("SELECT * FROM customers LIMIT 10")

# Using the webhook client
webhook = WebhookClient()
response = webhook.trigger_webhook(
    webhook_name="slack_notification",
    payload={"message": "Hello from RevOps AI!"}
)
```

### Using Tools Directly

Tools can also be invoked directly via their Lambda functions:

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Invoke Firebolt query Lambda
response = lambda_client.invoke(
    FunctionName='revops-ai-v2-firebolt-query',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "query": "SELECT * FROM customers WHERE customer_id = ?",
        "parameters": ["cust-12345"]
    })
)

# Parse the result
result = json.loads(response['Payload'].read())
```

## Development

### Adding a New Tool

1. Create a new directory for your tool
2. Implement the core functionality
3. Create a Lambda handler if needed
4. Add configuration and documentation
5. Add tests in the `/tests/unit/tools/` directory

### Best Practices

- **Modularity**: Design tools to be modular and reusable
- **Configuration**: Use environment variables for configuration
- **Error Handling**: Implement comprehensive error handling
- **Logging**: Use the standard logging framework
- **Documentation**: Document the tool's functionality and usage
- **Testing**: Write unit and integration tests

## Deployment

Tools are deployed as AWS Lambda functions or library modules, depending on their nature. See the `/deployment` directory for deployment scripts and infrastructure definitions.
