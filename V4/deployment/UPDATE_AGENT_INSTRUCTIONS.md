# Update Manager Agent Instructions

This guide provides methods to update the Manager Agent (ID: PVWGKOWSOT) with new instructions from `/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V4/agents/manager_agent/instructions.md`.

## Prerequisites

1. **AWS CLI configured** with profile `FireboltSystemAdministrator-740202120544`
2. **AWS permissions** for Bedrock Agent operations
3. **Python 3.9+** for deployment scripts

## Method 1: Complete V4 Deployment (Recommended)

Use the comprehensive V4 deployment script:

```bash
cd /Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V4/deployment
python3 deploy_v4.py
```

## Method 2: Manager Agent Only

Update only the Manager Agent:

```bash
cd /Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V4/deployment
python3 deploy_manager_agent.py
```

## Method 3: Manual AWS CLI Commands

If you prefer to run the AWS CLI commands manually:

### Step 1: Update Agent Instructions

```bash
# Set variables
AGENT_ID="PVWGKOWSOT"
AGENT_ALIAS_ID="LH87RBMCUQ"
PROFILE="FireboltSystemAdministrator-740202120544"
REGION="us-east-1"

# Get current agent details
aws bedrock-agent get-agent \
  --agent-id "$AGENT_ID" \
  --profile "$PROFILE" \
  --region "$REGION"

# Update agent with new instructions
aws bedrock-agent update-agent \
  --agent-id "$AGENT_ID" \
  --agent-name "Manager_Agent_V4" \
  --description "Manager Agent V4 - Claude 3.7 intelligent router and coordinator" \
  --instruction "$(cat ../agents/manager_agent/instructions.md)" \
  --foundation-model "us.anthropic.claude-3-7-sonnet-20250219-v1:0" \
  --agent-resource-role-arn "arn:aws:iam::740202120544:role/AmazonBedrockExecutionRoleForAgents_revops" \
  --idle-session-ttl-in-seconds 1800 \
  --profile "$PROFILE" \
  --region "$REGION"
```

### Step 2: Prepare Agent

```bash
# Prepare agent (creates new version)
aws bedrock-agent prepare-agent \
  --agent-id "$AGENT_ID" \
  --profile "$PROFILE" \
  --region "$REGION"
```

### Step 3: Update Agent Alias

```bash
# Update alias to point to new version (replace VERSION with actual version)
aws bedrock-agent update-agent-alias \
  --agent-id "$AGENT_ID" \
  --agent-alias-id "$AGENT_ALIAS_ID" \
  --agent-alias-name "Manager_Agent_Prod" \
  --routing-configuration agentVersion="VERSION" \
  --profile "$PROFILE" \
  --region "$REGION"
```

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

## Verification

After updating, test the agent with:

```bash
# Test the updated agent
aws bedrock-agent-runtime invoke-agent \
  --agent-id "PVWGKOWSOT" \
  --agent-alias-id "LH87RBMCUQ" \
  --session-id "test-session-$(date +%s)" \
  --input-text "What is the status of the ACME Corp deal?" \
  --profile "FireboltSystemAdministrator-740202120544" \
  --region "us-east-1"
```

## Troubleshooting

### Common Issues:

1. **Permission Denied**
   ```bash
   aws sts get-caller-identity --profile FireboltSystemAdministrator-740202120544
   ```

2. **Agent Not Ready**
   - Wait for agent status to be `NOT_PREPARED` or `PREPARED`
   - Check agent status with `get-agent` command

3. **Alias Update Fails**
   - Ensure agent preparation is complete
   - Verify agent version exists

### Monitoring:

```bash
# Check agent status
aws bedrock-agent get-agent \
  --agent-id "PVWGKOWSOT" \
  --profile "FireboltSystemAdministrator-740202120544" \
  --region "us-east-1"

# Check alias status
aws bedrock-agent get-agent-alias \
  --agent-id "PVWGKOWSOT" \
  --agent-alias-id "LH87RBMCUQ" \
  --profile "FireboltSystemAdministrator-740202120544" \
  --region "us-east-1"
```

## File Locations

- **Manager Agent Instructions**: `/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V4/agents/manager_agent/instructions.md`
- **Configuration**: `/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V4/deployment/config.json`
- **Deployment Scripts**: `/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V4/deployment/`

## Agent Configuration

- **Agent ID**: PVWGKOWSOT
- **Agent Alias ID**: LH87RBMCUQ
- **Foundation Model**: us.anthropic.claude-3-7-sonnet-20250219-v1:0
- **Profile**: FireboltSystemAdministrator-740202120544
- **Region**: us-east-1
- **Architecture**: V4 Multi-Agent Collaboration