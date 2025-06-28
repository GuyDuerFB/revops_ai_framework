# RevOps AI Framework V2 - Decision Agent

The Decision Agent is responsible for analyzing data and making intelligent decisions to guide the RevOps AI workflow.

## Overview

The Decision Agent serves as the analytical brain of the RevOps AI Framework. It processes data provided by the Data Agent and determines the optimal actions to take based on business rules and context.

## Current Implementation

```
decision_agent/
├── README.md            # This file
├── decision_agent.py     # Core agent implementation
└── instructions.md      # Agent instructions and capabilities
```

## Current Capabilities

The Decision Agent is in early development. Its current implementation focuses on:

- Receiving data and context from the Data Agent
- Processing information to make recommendations
- Using instructions to guide decision-making processes

## Integration

The Decision Agent is designed to work with AWS Bedrock and integrate with the other agents in the RevOps AI Framework.

## Deployment

The agent is deployed through Terraform configuration in the `deployment/terraform/modules/agent` directory, which sets up the AWS Bedrock agent with the appropriate resources and permissions.



Future enhancements to the Decision Agent capabilities are documented in the main ROADMAP.md file.
