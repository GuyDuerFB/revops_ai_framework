# RevOps Claude Code Slash Commands

Custom slash commands for debugging and managing the RevOps AI Framework within Claude Code.

## Installation

1. **Run the setup script:**
   ```bash
   cd tools/claude_code_commands
   ./setup.sh
   ```

2. **Ensure AWS SSO is configured:**
   ```bash
   aws sso login --profile FireboltSystemAdministrator-740202120544
   ```

## Available Commands

### `/revops debug_agent`

Systematically debug and fix unexpected agent behavior in the RevOps AI Framework by analyzing conversation logs, AWS traces, and agent configurations.

#### Usage Examples

```bash
# Interactive debugging session
/revops debug_agent

# Debug with conversation file
/revops debug_agent --conversation conversation.txt --timestamp "2025-07-07 15:24"

# Focus on specific agent
/revops debug_agent --agent data
```

#### What It Does

1. **Conversation Analysis**: Extracts user query, agent response, and timestamps
2. **Context Gathering**: Collects expected behavior and data sources
3. **AWS Log Analysis**: Searches CloudWatch logs across all agents with precise time windows
4. **Root Cause Analysis**: Systematic framework to identify collaboration, data retrieval, and execution issues
5. **Knowledge Base Review**: Identifies relevant documentation files to check
6. **Fix Suggestions**: Provides specific actions and file locations
7. **Agent Status Check**: Verifies current deployment status
8. **Deployment Commands**: Generates exact AWS CLI commands for fixes

#### Agent Coverage

- **Decision Agent** (TCX9CGOKBR): Supervisor managing agent collaboration
- **Data Agent** (9B8EGU46UV): Firebolt/Salesforce/Gong data retrieval
- **WebSearch Agent** (83AGBVJLEB): Web search and company research
- **Execution Agent** (UWMCP4AYZX): Webhook execution and actions

#### Parameters

| Parameter | Description | Required | Example |
|-----------|-------------|----------|---------|
| `--conversation` | Path to conversation file or paste text | No | `conversation.txt` |
| `--timestamp` | Israel time of the issue | No | `"2025-07-07 15:24"` |
| `--agent` | Focus on specific agent | No | `data` |

## Debug Workflow

The command follows a systematic 8-step process:

### Step 1: Conversation Analysis
- Extracts user query and agent response
- Converts Israel time to UTC for AWS log analysis
- Identifies the core issue and expected behavior

### Step 2: Additional Context Gathering
- Determines expected data sources
- Collects similar working queries for comparison
- Identifies which agents should be involved

### Step 3: AWS CloudWatch Log Analysis
- Searches precise time windows (±5 minutes from incident)
- Analyzes Slack processor logs for function calls
- Reviews each involved agent's logs for errors/patterns

### Step 4: Root Cause Analysis Framework
- **Collaboration Issues**: Decision agent not invoking collaborators
- **Data Retrieval Issues**: Missing SQL queries or execution errors
- **General Errors**: Permission issues or configuration problems

### Step 5: Knowledge Base Review
- Lists relevant documentation files to check
- Agent-specific instructions and patterns
- Schema documentation and SQL patterns

### Step 6: Fix Suggestions
- Specific file paths and actions to take
- Instruction updates vs knowledge base updates
- Testing recommendations

### Step 7: Agent Status Check
- Current deployment status of all agents
- Last update timestamps
- Preparation status

### Step 8: Deployment Commands
- Knowledge base sync commands
- Agent update commands with exact IDs
- Testing recommendations

## Example Output

```
🔧======================================================================
🚀 RevOps Agent Debug Tool - Enhanced Analysis
========================================================================

📋 STEP 1: Conversation Analysis
--------------------------------------------------
📝 Paste the Slack conversation (or path to file): 
⏰ Timestamp (Israel time, e.g., '2025-07-07 15:24'): 2025-07-07 15:24
🎯 Expected behavior: Show count of new leads from last week
✅ User Query: how many new leads did we get last week?
✅ UTC Time Window: 2025-07-07 13:24:00 ± 5 minutes

🔍 STEP 2: Additional Context Gathering
--------------------------------------------------
📊 Expected data sources (Firebolt/Salesforce/Gong/Web): Firebolt
✅ Similar working queries (examples): revenue analysis queries work fine
🐛 Specific issue observed: Agent claimed schema limitations
🤖 Identified involved agents: decision_agent, data_agent

📊 STEP 3: AWS CloudWatch Log Analysis
--------------------------------------------------
🔍 Analyzing Slack processor logs...
🔍 Analyzing decision_agent logs...
🔍 Analyzing data_agent logs...

🔍 STEP 4: Root Cause Analysis
--------------------------------------------------
🚨 Root Causes Identified:
  • Data agent not executing SQL queries
    Evidence: No SQL queries found in data agent logs
    Fix: Check schema documentation and SQL patterns

📚 STEP 5: Knowledge Base Review
--------------------------------------------------
📋 Knowledge base files to review:
  ✅ agents/decision_agent/instructions.md
  ✅ agents/data_agent/instructions.md
  ✅ knowledge_base/firebolt_schema/firebolt_schema.md
  ✅ knowledge_base/sql_patterns/lead_analysis.md

🔧 STEP 6: Suggested Fixes
--------------------------------------------------
🎯 Recommended fixes:
  1. Add or update SQL patterns for the specific query type
     File: knowledge_base/sql_patterns/
     Type: knowledge_base
  2. Ensure proper reference to knowledge base files
     File: agents/data_agent/instructions.md
     Type: instructions

🤖 STEP 7: Agent Status Check
--------------------------------------------------
✅ decision_agent: PREPARED (Updated: 2025-07-10T07:36:01.595719+00:00)
✅ data_agent: PREPARED (Updated: 2025-07-10T07:36:01.595719+00:00)
✅ websearch_agent: PREPARED (Updated: 2025-07-09T14:15:48.527791+00:00)
✅ execution_agent: PREPARED (Updated: 2025-07-09T14:15:48.527791+00:00)

🚀 STEP 8: Deployment Commands
--------------------------------------------------
Run these commands to deploy fixes:

# 1. Sync knowledge base (if KB files were updated)
cd V3/deployment
python3 sync_knowledge_base.py

# 2. Update agent instructions
aws bedrock-agent update-agent --agent-id TCX9CGOKBR \
  --instruction "$(cat agents/decision_agent/instructions.md)" \
  --profile FireboltSystemAdministrator-740202120544

# 3. Test the fix
# Create a test with the original failing query and verify the response

========================================================================
🎉 Debug analysis complete!
📝 Review the suggested fixes and run the deployment commands.
🧪 Don't forget to test the original failing scenario after deployment.
========================================================================
```

## Troubleshooting

### Command Not Found
If `/revops debug_agent` is not recognized:
1. Verify Claude Code is installed and up to date
2. Run `./setup.sh` again
3. Restart Claude Code

### AWS Access Issues
```bash
# Check AWS configuration
aws sts get-caller-identity --profile FireboltSystemAdministrator-740202120544

# Re-login if needed
aws sso login --profile FireboltSystemAdministrator-740202120544
```

### Python Dependencies
```bash
# Install required packages
pip3 install boto3 botocore
```

## Contributing

To add new slash commands:

1. Create a new Python script in this directory
2. Update `claude_code_commands.json` with the new command
3. Update `setup.sh` to include the new files
4. Test the command and update this README

## Related Documentation

- [Claude Code Slash Commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands)
- [RevOps AI Framework Documentation](../../README.md)
- [Agent Deployment Guide](../../V3/CLEAN_DEPLOYMENT_GUIDE.md)