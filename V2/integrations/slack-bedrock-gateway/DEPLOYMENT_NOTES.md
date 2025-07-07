# Slack-Bedrock Gateway Deployment Notes

## Current Configuration (WORKING)

### Decision Agent Configuration
- **Agent ID**: `TCX9CGOKBR`
- **Alias ID**: `RSYE8T5V96` 
- **Current Version**: 1 (working)
- **Foundation Model**: `anthropic.claude-3-5-sonnet-20240620-v1:0`
- **Role**: `SUPERVISOR` with NO action groups
- **IAM Service Role**: `arn:aws:iam::740202120544:role/AmazonBedrockExecutionRoleForAgents_TCX9CGOKBR`

### Agent Collaborators
1. **DataAgent** (`NIQUKBY9MA`) - Firebolt DWH, Gong, Salesforce queries
2. **WebSearchAgent** (`ZA2EWWTRUO`) - External intelligence gathering  
3. **ExecutionAgent** (`7NXLCQHMPL`) - Webhooks, notifications, actions

### Lambda Configuration
- **Handler**: `revops-slack-bedrock-handler`
- **Processor**: `revops-slack-bedrock-processor`
- **SQS Queue**: `revops-slack-bedrock-processing-queue`

### Key Fixes Applied
1. **Created Missing IAM Role**: `AmazonBedrockExecutionRoleForAgents_TCX9CGOKBR` with proper Bedrock permissions
2. **Fixed Agent Version**: Updated alias to point to version 1 (compatible model)
3. **Removed Action Groups**: Decision Agent now works exclusively through collaborators
4. **Updated Instructions**: Latest supervisor-only configuration

### Model Compatibility
- ✅ **Version 1**: `anthropic.claude-3-5-sonnet-20240620-v1:0` (works with on-demand)
- ❌ **Version 2**: `anthropic.claude-3-5-sonnet-20241022-v2:0` (requires inference profile)

## Testing
- Integration test: `python3 test_integration.py`
- Direct agent test: `python3 test_bedrock_access.py`
- Both should return success status

## Architecture
```
Slack → API Gateway → Handler Lambda → SQS → Processor Lambda → Bedrock Agent → Collaborator Agents
```

All components verified working as of 2025-07-06.