# RevOps AI Framework V2 - Webhook Lambda

This directory contains a consolidated webhook Lambda implementation that supports multiple modes of operation for integrating with external systems.

## Overview

The webhook Lambda is designed to trigger external webhooks with configurable payloads. It can be used to integrate the RevOps AI Framework with services like Zapier, Slack, or any custom HTTP endpoint.

### Key Features

- **Multiple Operational Modes**:
  - Direct webhook invocation
  - Asynchronous processing via SQS queue with retry logic
  - AWS Bedrock Agent compatibility
  
- **Configuration-Driven Behavior**:
  - Feature flags for enabling/disabling functionality
  - Environment variable configuration
  - Support for configuration files
  
- **Security**:
  - AWS Secrets Manager integration for secure webhook URL storage
  - HTTPS enforcement for all webhook calls
  - JWT and request signing support (if configured)

- **Observability**:
  - Comprehensive logging
  - Optional metrics tracking

## Directory Structure

```
webhook/
├── README.md                       # This file
├── lambda_function.py              # Main webhook lambda handler
├── modules/                        # Modular components for the consolidated lambda
│   ├── __init__.py
│   ├── core.py                     # Core webhook handling logic
│   ├── queue_processor.py          # SQS queue processing logic
│   └── bedrock_adapter.py          # AWS Bedrock Agent adapter
├── utils/                          # Utility functions
│   ├── __init__.py
│   ├── config_loader.py            # Configuration loading
│   └── secret_manager.py           # Secret management utilities
└── webhook_config_template.json    # Template for webhook configuration
```

## Usage

### Lambda Event Format

The consolidated webhook Lambda accepts events in three formats:

#### 1. Direct Webhook Invocation

```json
{
  "webhook_name": "notification",    // Named webhook from configuration
  "webhook_url": "https://...",      // Or direct webhook URL
  "payload": {                       // Payload to send to webhook
    "message": "Hello, world!",
    "data": {
      "key": "value"
    }
  },
  "queue": false                     // Optional, set to true to queue the request
}
```

#### 2. Queue Processing (SQS Message)

SQS message body should contain the same format as Direct Webhook Invocation.

#### 3. Bedrock Agent Format

```json
{
  "messageVersion": "1.0",
  "action": "trigger_webhook",
  "actionGroup": "webhooks",
  "parameters": {
    "webhook_name": "notification",
    "payload": {
      "message": "Hello from Bedrock Agent!",
      "data": {
        "key": "value"
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBHOOK_CONFIG_PATH` | Path to webhook configuration file | None |
| `WEBHOOK_URL_SECRET` | AWS Secrets Manager secret name for webhook URLs | `webhook-urls` |
| `WEBHOOK_QUEUE_URL` | SQS queue URL for asynchronous processing | None |
| `LOG_LEVEL` | Logging level | `INFO` |
| `WEBHOOK_RETRIES_ENABLED` | Enable/disable retry logic | `false` |
| `WEBHOOK_MAX_RETRIES` | Maximum retry attempts | `3` |
| `WEBHOOK_ENABLE_BEDROCK` | Enable Bedrock Agent compatibility | `false` |
| `WEBHOOK_ENABLE_ENRICHMENT` | Enable payload enrichment | `true` |
| `WEBHOOK_ENABLE_METRICS` | Enable CloudWatch metrics | `false` |

### Configuration File Format

```json
{
  "features": {
    "queue_processing": {
      "enabled": false,
      "queue_url": "${env:WEBHOOK_QUEUE_URL}",
      "retries": {
        "max_attempts": 3,
        "backoff_base": 2
      }
    },
    "bedrock_agent_compatibility": {
      "enabled": false,
      "response_format": "agent_function"
    },
    "payload_enrichment": {
      "enabled": true,
      "add_timestamp": true,
      "add_request_id": true,
      "add_context": true
    },
    "metrics": {
      "enabled": false,
      "namespace": "WebhookLambda"
    }
  },
  "webhooks": {
    "path": "${env:WEBHOOK_CONFIG_PATH}",
    "allow_direct_url": true,
    "url_secret_name": "${env:WEBHOOK_URL_SECRET:webhook-urls}"
  },
  "logging": {
    "level": "${env:LOG_LEVEL:INFO}"
  }
}
```

## Migration Guide

### Migrating from Legacy Webhook Lambda

1. Update references in your code to use the new consolidated Lambda function
2. Ensure your event format matches the expected format shown above
3. No changes to environment variables are needed; the consolidated Lambda supports all existing variables

### Migrating from Dispatcher Lambda

1. Update references to use the consolidated Lambda function
2. Ensure the `queue_processing` feature is enabled:
   ```
   WEBHOOK_QUEUE_URL=<your-queue-url>
   ```
3. Set the queue flag in your webhook request:
   ```json
   {
     "webhook_name": "your-webhook",
     "payload": { "your": "payload" },
     "queue": true
   }
   ```

### Migrating from Executor Lambda

1. Update references to use the consolidated Lambda function
2. Enable Bedrock Agent compatibility:
   ```
   WEBHOOK_ENABLE_BEDROCK=true
   ```
3. Event format remains compatible with Bedrock Agent function calling

## Development

### Adding a New Webhook

1. Add the webhook URL to the AWS Secrets Manager secret specified by `WEBHOOK_URL_SECRET`
2. Use the webhook by name in your Lambda invocation

### Adding New Features

The modular architecture makes it easy to extend the Lambda with new features:

1. Create a new module in the `modules/` directory
2. Update the configuration template in `utils/config_loader.py`
3. Integrate your module in `lambda_function.py`

## Testing

Unit tests for the webhook Lambda are available in the `/tests/unit/tools/webhook` directory.

## Deployment

The webhook Lambda is deployed as part of the RevOps AI Framework V2 infrastructure. See the deployment documentation for details.

## Legacy Implementations (Deprecated)

The following implementations are deprecated and will be removed in future releases:

- `lambda_function.py`: Basic webhook handler
- `dispatcher_lambda/lambda_function.py`: SQS queue dispatcher with retry logic
- `executor_lambda/lambda_function.py`: Bedrock Agent compatible webhook handler

All functionality from these implementations has been consolidated into the new modular Lambda function.
