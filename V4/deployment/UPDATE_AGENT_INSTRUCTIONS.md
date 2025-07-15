# Update Decision Agent Instructions

This guide provides three methods to update the Decision Agent (ID: TCX9CGOKBR) with new instructions from `/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V3/agents/decision_agent/instructions.md`.

## Prerequisites

1. **AWS CLI configured** with profile `FireboltSystemAdministrator-740202120544`
2. **AWS permissions** for Bedrock Agent operations
3. **jq installed** (for shell script method)
4. **Python 3.9+** (for Python script methods)

## Method 1: Shell Script (Recommended)

The shell script provides the most direct AWS CLI approach with detailed logging.

```bash
cd /Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V3/deployment
./update_decision_agent.sh
```

**Features:**
- ✅ Direct AWS CLI commands
- ✅ Comprehensive error handling
- ✅ Automatic agent preparation
- ✅ Agent alias update to new version
- ✅ Detailed progress logging
- ✅ Test command generation

## Method 2: Python Script with Alias Update

This Python script provides the most comprehensive update with alias management.

```bash
cd /Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V3/deployment
python3 update_agent_with_alias.py
```

**Options:**
- Default: Updates agent and alias
- `--no-alias`: Updates only agent instructions (not alias)

**Features:**
- ✅ Automatic configuration loading from config.json
- ✅ Agent status monitoring
- ✅ Optional alias update
- ✅ Comprehensive error handling
- ✅ Timeout protection

## Method 3: Basic Python Script

Simple script for updating just the agent instructions.

```bash
cd /Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V3/deployment
python3 update_decision_agent_instructions.py
```

**Features:**
- ✅ Basic agent update
- ✅ Agent preparation
- ✅ Configuration loading
- ✅ Simple error handling

## Manual AWS CLI Commands

If you prefer to run the AWS CLI commands manually:

### Step 1: Update Agent Instructions

```bash
# Set variables
AGENT_ID="TCX9CGOKBR"
AGENT_ALIAS_ID="BKLREFH3L0"
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
  --agent-name "DecisionAgent" \
  --description "Decision Agent for RevOps AI Framework with temporal analysis and business logic awareness" \
  --instruction "$(cat ../agents/decision_agent/instructions.md)" \
  --foundation-model "anthropic.claude-sonnet-4-20250514-v1:0" \
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
  --agent-alias-name "decision-agent-alias" \
  --routing-configuration agentVersion="VERSION" \
  --profile "$PROFILE" \
  --region "$REGION"
```

## Current Instructions Summary

The updated instructions include:

### Key Changes:
1. **Split Step 1** into Step 1A (Opportunity Data) and Step 1B (Call Data)
2. **Explicit validation requirements** for data collection
3. **Enhanced error handling** with fallback strategies
4. **Clear guidance** on using `query_firebolt` vs `get_gong_data`

### New Features:
- **Dual data collection** for deal reviews
- **Data validation checks** before proceeding
- **Comprehensive error handling** for missing data
- **Structured deal assessment** framework
- **Data conflict resolution** guidelines

## Verification

After updating, test the agent with:

```bash
# Test the updated agent
aws bedrock-agent-runtime invoke-agent \
  --agent-id "TCX9CGOKBR" \
  --agent-alias-id "BKLREFH3L0" \
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
  --agent-id "TCX9CGOKBR" \
  --profile "FireboltSystemAdministrator-740202120544" \
  --region "us-east-1"

# Check alias status
aws bedrock-agent get-agent-alias \
  --agent-id "TCX9CGOKBR" \
  --agent-alias-id "BKLREFH3L0" \
  --profile "FireboltSystemAdministrator-740202120544" \
  --region "us-east-1"
```

## File Locations

- **Decision Agent Instructions**: `/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V3/agents/decision_agent/instructions.md`
- **Configuration**: `/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V3/deployment/config.json`
- **Update Scripts**: `/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V3/deployment/`

## Agent Configuration

- **Agent ID**: TCX9CGOKBR
- **Agent Alias ID**: BKLREFH3L0
- **Foundation Model**: anthropic.claude-sonnet-4-20250514-v1:0
- **Profile**: FireboltSystemAdministrator-740202120544
- **Region**: us-east-1