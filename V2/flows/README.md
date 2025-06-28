# RevOps AI Framework V2 - Flows

This directory contains the workflow orchestration logic for the RevOps AI Framework.

## Overview

The flows directory is currently in early development phase. It will eventually define how to coordinate the actions of the framework's agents (Data Agent, Decision Agent, and Execution Agent) to solve specific business problems in revenue operations.

## Directory Structure

```
flows/
├── README.md              # This file
└── flow_orchestrator.py    # Flow orchestration engine (initial implementation)
```

## Current Implementation

The current implementation includes an initial version of the `flow_orchestrator.py` module, which provides basic functionality for coordinating interactions between the three core agents:

- Data Analysis Agent
- Decision Agent
- Execution Agent

The FlowOrchestrator class implements methods for executing specific business flows:

- Deal quality assessment flow
- Consumption pattern analysis flow
- Generic multi-agent flow execution

Full flow definition and execution capabilities are still under development. See ROADMAP.md for planned features.

## Deployment

The flow orchestrator is deployed as part of the RevOps AI Framework infrastructure. See the `/deployment` directory for deployment scripts and infrastructure definitions.
