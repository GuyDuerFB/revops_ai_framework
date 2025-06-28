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
├── data_agent/                # Data retrieval and processing agent
│   ├── data_agent.py          # Data agent implementation
│   ├── instructions.md        # Instructions for the data agent
│   └── README.md              # Data agent documentation
├── decision_agent/            # Decision-making agent
│   ├── decision_agent.py      # Decision agent implementation
│   ├── instructions.md        # Instructions for the decision agent
│   └── README.md              # Decision agent documentation
└── execution_agent/           # Action execution agent
    ├── execution_agent.py     # Execution agent implementation
    ├── instructions.md        # Instructions for the execution agent
    └── README.md              # Execution agent documentation
```

## Current Implementation

Each agent directory currently contains:

- A core agent implementation file (e.g., `data_agent.py`)
- An instructions markdown file defining the agent's capabilities and usage
- A README with agent-specific documentation

The implementation of the three agent types is actively in development. Each agent has the following responsibilities:

1. **Data Agent**: Interfaces with the Firebolt database to retrieve and process data needed for analysis and decision-making. Uses the tools in the `tools/firebolt` directory.

2. **Decision Agent**: Analyzes data and makes recommendations based on business rules and patterns.

3. **Execution Agent**: Takes action based on decisions, such as updating systems or sending notifications.

## Deployment

The deployment configuration for these agents is defined in the `deployment/terraform` directory. The current implementation includes configuration for AWS Bedrock-powered agent deployments.
