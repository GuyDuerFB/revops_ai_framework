# RevOps AI Framework V2 - Decision Agent

The Decision Agent is responsible for analyzing data and making intelligent decisions to guide the RevOps AI workflow.

## Overview

The Decision Agent serves as the analytical brain of the RevOps AI Framework. It processes data provided by the Data Agent, applies business rules and AI models, and determines the optimal actions to take. Its primary responsibilities include:

1. **Data Analysis**: Analyzing structured and unstructured data
2. **Decision Making**: Applying business rules and ML models to make decisions
3. **Recommendation Generation**: Creating actionable recommendations
4. **Risk Assessment**: Evaluating potential outcomes and risks
5. **Prioritization**: Ranking actions based on business impact

## Architecture

```
decision_agent/
├── README.md            # This file
├── __init__.py          # Package initialization
├── agent.py             # Core agent implementation
├── handler.py           # AWS Lambda handler
├── config.py            # Agent configuration
├── models/              # Decision models
├── rules/               # Business rules engine
├── analyzers/           # Data analysis components
└── recommenders/        # Recommendation generators
```

## Decision Models

The Decision Agent employs several types of models:

- **Rule-based Models**: Explicit business rules defined by domain experts
- **Machine Learning Models**: Trained on historical data to predict outcomes
- **Heuristic Models**: Best-practice approaches for common scenarios
- **Hybrid Models**: Combinations of rules and ML for robust decision-making

## Usage

### Direct Invocation

```python
from agents.decision_agent.agent import DecisionAgent

# Initialize the agent
agent = DecisionAgent()

# Process data and make a decision
response = agent.process({
    "customer_data": {...},
    "interaction_history": [...],
    "business_context": {...},
    "decision_type": "renewal_strategy"
})

# Access the decision
decision = response["decision"]
recommendations = response["recommendations"]
```

### Lambda Invocation

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='revops-ai-v2-decision-agent',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "customer_data": {...},
        "interaction_history": [...],
        "business_context": {...},
        "decision_type": "renewal_strategy"
    })
)

# Parse response
result = json.loads(response['Payload'].read())
decision = result["decision"]
recommendations = result["recommendations"]
```

## Configuration

The Decision Agent can be configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DECISION_AGENT_LOG_LEVEL` | Logging level | `INFO` |
| `DECISION_MODEL_PATH` | Path to decision models | `/opt/models` |
| `RULES_CONFIG_PATH` | Path to business rules configuration | `/opt/config/rules.json` |
| `DECISION_AGENT_EXPLANATION_LEVEL` | Level of decision explanation | `STANDARD` |

## Development

### Adding a New Decision Model

1. Create a new model in the `models/` directory
2. Implement the `BaseModel` interface
3. Register the model in `config.py`
4. Add any necessary business rules in the `rules/` directory

### Business Rules Definition

Business rules are defined in JSON format:

```json
{
  "rule_id": "renewal_discount_rule",
  "conditions": [
    {
      "field": "customer.lifetime_value",
      "operator": "greater_than",
      "value": 10000
    },
    {
      "field": "customer.renewal_risk",
      "operator": "greater_than",
      "value": 0.7
    }
  ],
  "actions": [
    {
      "type": "offer_discount",
      "parameters": {
        "discount_percentage": 10,
        "reason": "high-value customer at risk"
      }
    }
  ]
}
```

### Testing

Unit tests for the Decision Agent are available in `/tests/unit/agents/decision_agent/`.

## Deployment

The Decision Agent is deployed as an AWS Lambda function with access to necessary model artifacts and configuration files. See the deployment directory for more details.
