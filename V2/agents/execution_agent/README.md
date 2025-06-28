# RevOps AI Framework V2 - Execution Agent

The Execution Agent is responsible for carrying out actions determined by the Decision Agent within the RevOps AI workflow.

## Overview

The Execution Agent serves as the action implementation component of the RevOps AI Framework. It takes decisions from the Decision Agent and converts them into concrete actions, ensuring they are executed properly. Its primary responsibilities include:

1. **Action Execution**: Implementing decisions through API calls, webhooks, etc.
2. **Workflow Orchestration**: Managing multi-step execution processes
3. **Error Handling**: Gracefully handling execution failures with retries and fallbacks
4. **Status Tracking**: Monitoring and reporting on action execution status
5. **Rollback Management**: Implementing compensating transactions when needed

## Architecture

```
execution_agent/
├── README.md            # This file
├── __init__.py          # Package initialization
├── agent.py             # Core agent implementation
├── handler.py           # AWS Lambda handler
├── config.py            # Agent configuration
├── actions/             # Action implementations
├── workflows/           # Workflow definitions
├── adapters/            # Integration adapters for external systems
└── validators/          # Action validation components
```

## Supported Actions

The Execution Agent can perform various types of actions:

- **Communication Actions**: Sending emails, Slack messages, etc.
- **CRM Actions**: Creating/updating records in CRM systems
- **Workflow Actions**: Starting/controlling business processes
- **Integration Actions**: Triggering external system processes
- **Custom Actions**: Implementing client-specific business logic

## Usage

### Direct Invocation

```python
from agents.execution_agent.agent import ExecutionAgent

# Initialize the agent
agent = ExecutionAgent()

# Execute an action
response = agent.process({
    "action_type": "send_email",
    "parameters": {
        "template": "renewal_reminder",
        "recipient": "customer@example.com",
        "variables": {
            "customer_name": "Acme Inc.",
            "renewal_date": "2023-12-31"
        }
    }
})

# Access the result
result = response["result"]
action_id = response["action_id"]
```

### Lambda Invocation

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='revops-ai-v2-execution-agent',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "action_type": "send_email",
        "parameters": {
            "template": "renewal_reminder",
            "recipient": "customer@example.com",
            "variables": {
                "customer_name": "Acme Inc.",
                "renewal_date": "2023-12-31"
            }
        }
    })
)

# Parse response
result = json.loads(response['Payload'].read())
action_status = result["status"]
```

## Configuration

The Execution Agent can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `EXECUTION_AGENT_LOG_LEVEL` | Logging level | `INFO` |
| `ACTION_TEMPLATES_PATH` | Path to action templates | `/opt/templates` |
| `MAX_RETRIES` | Maximum retry attempts | `3` |
| `RETRY_BACKOFF_MS` | Base retry backoff in milliseconds | `1000` |
| `WEBHOOK_CONFIG_PATH` | Path to webhook configuration | `/opt/config/webhooks.json` |

## Development

### Adding a New Action Type

1. Create a new action handler in the `actions/` directory
2. Implement the `BaseAction` interface
3. Register the action in `config.py`
4. Add any necessary templates or configurations
5. Implement validation logic in the `validators/` directory

### Action Definition Format

Actions are defined in a structured JSON format:

```json
{
  "action_type": "send_email",
  "parameters": {
    "template": "renewal_reminder",
    "recipient": "customer@example.com",
    "variables": {
      "customer_name": "Acme Inc.",
      "renewal_date": "2023-12-31"
    }
  },
  "options": {
    "priority": "high",
    "retry_policy": "exponential",
    "max_retries": 3
  }
}
```

### Testing

Unit tests for the Execution Agent are available in `/tests/unit/agents/execution_agent/`.

## Deployment

The Execution Agent is deployed as an AWS Lambda function with appropriate IAM permissions for executing actions and interacting with external systems. See the deployment directory for more details.
