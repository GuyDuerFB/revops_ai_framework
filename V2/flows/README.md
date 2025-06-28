# RevOps AI Framework V2 - Flows

This directory contains the workflow definitions and orchestration logic for the RevOps AI Framework.

## Overview

The flows directory defines the end-to-end workflows that coordinate the actions of the framework's agents (Data Agent, Decision Agent, and Execution Agent) to solve specific business problems in revenue operations.

A flow represents a complete business process, such as customer onboarding, renewal management, or churn prediction and intervention. Each flow orchestrates the interactions between agents, manages state transitions, and ensures successful execution of the overall process.

## Directory Structure

```
flows/
├── README.md                   # This file
├── __init__.py                 # Package initialization
├── flow_engine.py              # Flow orchestration engine
├── flow_registry.py            # Flow registration and discovery
├── flow_state.py               # Flow state management
├── standard_flows/             # Pre-defined standard flows
│   ├── onboarding_flow.py      # Customer onboarding workflow
│   ├── renewal_flow.py         # Renewal management workflow
│   └── churn_prevention_flow.py # Churn prediction and prevention
└── custom_flows/               # Customer-specific flow implementations
```

## Flow Definition

A flow is defined as a directed graph of steps, with each step corresponding to an agent action or control flow operation. Flows are defined using a declarative YAML syntax or programmatically using the Flow API.

### Example Flow Definition (YAML)

```yaml
flow_id: renewal_management
description: "Manage customer renewals with automated analysis and recommendations"
version: "1.0"
trigger:
  type: schedule
  schedule: "cron(0 9 * * ? *)"  # Daily at 9 AM
  filter:
    - "customer.renewal_date <= now() + interval '30 days'"

steps:
  - id: retrieve_customer_data
    agent: data_agent
    action: retrieve_customer_data
    parameters:
      include_fields:
        - contract_details
        - usage_metrics
        - support_history

  - id: assess_renewal_risk
    agent: decision_agent
    action: assess_renewal_risk
    depends_on:
      - retrieve_customer_data
    parameters:
      model: renewal_risk_v2
      threshold: 0.7

  - id: generate_recommendations
    agent: decision_agent
    action: generate_renewal_recommendations
    depends_on:
      - assess_renewal_risk
    parameters:
      strategy: "value_based"

  - id: send_notifications
    agent: execution_agent
    action: send_notifications
    depends_on:
      - generate_recommendations
    parameters:
      template: "renewal_recommendations"
      recipients:
        - "${customer.account_manager_email}"

  - id: schedule_followup
    agent: execution_agent
    action: create_calendar_event
    depends_on:
      - send_notifications
    parameters:
      title: "Renewal Discussion - ${customer.name}"
      attendees:
        - "${customer.account_manager_email}"
      duration_minutes: 30
      description: "Discuss renewal recommendations for ${customer.name}"

error_handling:
  default_strategy: retry
  retry_count: 3
  failure_notification: "${admin_email}"
```

### Programmatic Flow Definition

```python
from flows.flow_engine import Flow, Step, Trigger

# Define a flow
flow = Flow(
    flow_id="renewal_management",
    description="Manage customer renewals with automated analysis and recommendations",
    version="1.0"
)

# Define the trigger
flow.set_trigger(
    Trigger.schedule(
        cron="0 9 * * ? *",
        filter="customer.renewal_date <= now() + interval '30 days'"
    )
)

# Add steps
flow.add_step(
    Step(
        id="retrieve_customer_data",
        agent="data_agent",
        action="retrieve_customer_data",
        parameters={
            "include_fields": [
                "contract_details",
                "usage_metrics",
                "support_history"
            ]
        }
    )
)

flow.add_step(
    Step(
        id="assess_renewal_risk",
        agent="decision_agent",
        action="assess_renewal_risk",
        depends_on=["retrieve_customer_data"],
        parameters={
            "model": "renewal_risk_v2",
            "threshold": 0.7
        }
    )
)

# Add error handling
flow.set_error_handling(
    default_strategy="retry",
    retry_count=3,
    failure_notification="${admin_email}"
)

# Register the flow
flow.register()
```

## Flow Execution

Flows can be executed via the Flow Engine API or through AWS Step Functions.

### Direct Execution

```python
from flows.flow_engine import FlowEngine

# Initialize the flow engine
engine = FlowEngine()

# Execute a flow
execution = engine.execute_flow(
    flow_id="renewal_management",
    input_parameters={
        "customer_id": "cust-12345"
    }
)

# Check execution status
status = engine.get_execution_status(execution.id)
```

### AWS Step Functions Execution

```python
import boto3

step_functions = boto3.client('stepfunctions')

# Start execution
response = step_functions.start_execution(
    stateMachineArn='arn:aws:states:us-west-2:123456789012:stateMachine:RenewalManagement',
    input=json.dumps({
        "customer_id": "cust-12345"
    })
)

# Get execution status
execution_arn = response['executionArn']
execution = step_functions.describe_execution(
    executionArn=execution_arn
)
status = execution['status']
```

## Flow State Management

Flow state is managed by the Flow State Manager, which persists execution state in DynamoDB or another state store. This enables:

- Resuming flows after interruptions
- Tracking flow execution history
- Analyzing flow performance metrics
- Debugging flow execution issues

## Development

### Creating a New Flow

1. Define the flow using YAML or the Flow API
2. Register the flow in the Flow Registry
3. Implement any custom steps needed for the flow
4. Test the flow with sample inputs
5. Deploy the flow to the target environment

### Testing Flows

Unit tests for flows can be written using the Flow Testing Framework:

```python
from flows.testing import FlowTestCase

class RenewalFlowTest(FlowTestCase):
    def test_high_risk_customer(self):
        # Mock agent responses
        self.mock_agent_response(
            agent="data_agent",
            action="retrieve_customer_data",
            response={
                "usage_metrics": {"utilization": 0.2}
            }
        )
        
        # Execute the flow
        result = self.execute_flow(
            flow_id="renewal_management",
            input_parameters={
                "customer_id": "cust-low-usage"
            }
        )
        
        # Assert on the outcome
        self.assertIn("send_notifications", result.completed_steps)
        self.assertEqual(
            "high",
            result.step_outputs["assess_renewal_risk"]["risk_level"]
        )
```

## Deployment

Flows are deployed as part of the RevOps AI Framework infrastructure. See the `/deployment` directory for deployment scripts and infrastructure definitions.

For AWS Step Functions deployments, the flow definitions are automatically converted to Amazon States Language (ASL) during the deployment process.
