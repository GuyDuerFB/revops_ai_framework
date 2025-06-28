# RevOps AI Framework V2 - Tools

This directory contains utility tools and integrations that support the RevOps AI Framework's operations.

## Overview

The tools directory provides specialized components that perform specific functions required by the framework's agents. These include data connectors, API integrations, and webhook handlers that enhance the capabilities of the framework.

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
│   └── retrieval_lambda/     # Gong data retrieval Lambda
└── webhook/                  # Webhook integration
    ├── lambda_function.py     # Webhook Lambda handler
    ├── modules/              # Modular webhook components
    ├── tests/                # Webhook unit tests
    └── utils/                # Webhook utilities
```

## Available Tools

### Firebolt Tools

The Firebolt tools provide integration with the Firebolt data warehouse:

- **Metadata Lambda**: Retrieves schema metadata about tables and columns
- **Query Lambda**: Executes SQL queries against Firebolt
- **Writer Lambda**: Writes data to Firebolt tables

For detailed documentation, see the [Firebolt Tools README](/tools/firebolt/README.md).

### Gong Tools

The Gong tools provide integration with Gong's conversation intelligence platform:

- **Retrieval Lambda**: Module for retrieving data from Gong API

### Webhook Tools

The webhook tools enable integration with external systems via webhooks:

- **Lambda Function**: A consolidated webhook handler with support for:
  - Direct webhook invocation
  - Queue-based asynchronous processing
  - AWS Bedrock Agent compatibility

## Integration

These tools are integrated with the agents in the framework to provide data retrieval, messaging capabilities, and webhook handling functionality. Each tool is designed to be modular and reusable across different parts of the system.

For more details on future planned enhancements to these tools, see the ROADMAP.md file in the project root.
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
