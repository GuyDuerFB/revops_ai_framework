# Agent Management Guide

This guide provides methods to update and manage agents in the RevOps AI Framework.

## Prerequisites

1. **AWS CLI configured** with profile `FireboltSystemAdministrator-740202120544`
2. **AWS permissions** for Bedrock Agent operations
3. **Python 3.9+** for deployment scripts

## Quick Start

### Update All Agents (Recommended)

Use the unified deployment script:

```bash
cd deployment/
python3 deploy.py
```

### Update Specific Agent

Update only a specific agent:

```bash
cd deployment/
python3 deploy.py --agent manager
python3 deploy.py --agent data
python3 deploy.py --agent deal_analysis
```

## Validate Deployment

Check system health after updates:

```bash
cd deployment/
python3 validate_deployment.py
```

## Manual Agent Management

For direct agent management, you can use AWS CLI commands. All agent IDs and configuration are available in `config.json`.

## V4 Architecture Overview

The V4 architecture includes:

### Manager Agent (PVWGKOWSOT)
- **Role**: Supervisor and intelligent router
- **Foundation Model**: Claude 3.7 Sonnet
- **Collaborators**: DataAgent, DealAnalysisAgent, LeadAnalysisAgent, WebSearchAgent, ExecutionAgent

### Specialized Agents:
- **DataAgent** (NOJMSQ8JPT): Data fetching and analysis
- **DealAnalysisAgent** (DBHYUWC6U6): MEDDPICC deal assessment
- **LeadAnalysisAgent** (IP9HPDIEPL): ICP analysis and engagement strategy
- **WebSearchAgent** (QKRQXXPJOJ): External intelligence gathering
- **ExecutionAgent** (AINAPUEIZU): Action execution and integration

## Agent Instructions

Agent instructions are stored in the `agents/` directory:

- **Manager Agent**: `agents/manager_agent/instructions.md`
- **Data Agent**: `agents/data_agent/instructions.md`
- **Deal Analysis Agent**: `agents/deal_analysis_agent/instructions.md`
- **Lead Analysis Agent**: `agents/lead_analysis_agent/instructions.md`
- **Web Search Agent**: `agents/web_search_agent/instructions.md`
- **Execution Agent**: `agents/execution_agent/instructions.md`

## Configuration

All agent settings and AWS resource configuration are centralized in `deployment/config.json`.

---

**Last Updated**: August 2025  
**Version**: V5.1  
**For detailed system documentation, see the main README.md**