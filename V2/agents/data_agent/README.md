# RevOps AI Framework V2 - Data Agent

The Data Agent is responsible for retrieving and processing data from various sources to support the RevOps AI workflow.

## Overview

The Data Agent serves as the data retrieval and processing component of the RevOps AI Framework. Its primary responsibilities include:

1. **Data Retrieval**: Connecting to various data sources (Firebolt, Gong, CRMs, etc.)
2. **Data Processing**: Cleaning, transforming, and enriching raw data
3. **Data Integration**: Combining data from multiple sources into a unified format
4. **Query Translation**: Converting natural language queries into structured data requests
5. **Caching**: Managing data caching for performance optimization

## Architecture

```
data_agent/
├── README.md            # This file
├── __init__.py          # Package initialization
├── agent.py             # Core agent implementation
├── handler.py           # AWS Lambda handler
├── config.py            # Agent configuration
├── processors/          # Data processors for different sources
├── connectors/          # Data source connectors
└── models/              # Data models and schemas
```

## Data Sources

The Data Agent supports the following data sources:

- **Firebolt**: Data warehouse queries
- **Gong**: Call recordings and analytics
- **CRM Systems**: Customer relationship management data
- **Custom APIs**: Integration with custom data sources
- **File Systems**: CSV, JSON, and other file formats

## Usage

### Direct Invocation

```python
from agents.data_agent.agent import DataAgent

# Initialize the agent
agent = DataAgent()

# Request data
response = agent.process({
    "data_source": "firebolt",
    "query": "get_customer_revenue",
    "parameters": {
        "customer_id": "cust-12345",
        "time_period": "last_6_months"
    }
})

# Access the data
data = response["data"]
```

### Lambda Invocation

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='revops-ai-v2-data-agent',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "data_source": "firebolt",
        "query": "get_customer_revenue",
        "parameters": {
            "customer_id": "cust-12345",
            "time_period": "last_6_months"
        }
    })
)

# Parse response
result = json.loads(response['Payload'].read())
data = result["data"]
```

## Configuration

The Data Agent can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATA_AGENT_LOG_LEVEL` | Logging level | `INFO` |
| `DATA_AGENT_CACHE_TTL` | Cache time-to-live (seconds) | `3600` |
| `FIREBOLT_CONNECTION_STRING` | Firebolt connection string | None |
| `GONG_API_KEY` | Gong API key | None |
| `DATA_AGENT_MAX_RETRIES` | Maximum retry attempts | `3` |

## Development

### Adding a New Data Source

1. Create a new connector in the `connectors/` directory
2. Implement the `BaseConnector` interface
3. Register the connector in `config.py`
4. Add any necessary data processors in the `processors/` directory

### Testing

Unit tests for the Data Agent are available in `/tests/unit/agents/data_agent/`.

## Deployment

The Data Agent is deployed as an AWS Lambda function with appropriate IAM permissions for accessing data sources and AWS services. See the deployment directory for more details.
