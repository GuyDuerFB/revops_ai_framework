# Enhanced Agent Tracing Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing robust agent tracing across the RevOps AI Framework to enable systematic debugging and root cause analysis.

## Architecture Deployed

### CloudWatch Log Groups (7-day retention)
- `/aws/revops-ai/conversation-trace` - End-to-end conversation tracking
- `/aws/revops-ai/agent-collaboration` - Agent-to-agent interactions
- `/aws/revops-ai/data-operations` - SQL queries and data retrieval
- `/aws/revops-ai/decision-logic` - Decision agent reasoning
- `/aws/revops-ai/error-analysis` - Errors and failure patterns

### Dashboard
- **URL**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-ai-agent-tracing
- **Widgets**: Recent conversations, agent collaborations, errors, data operations

## Implementation Steps

### 1. Update Slack-Bedrock Processor

```bash
# Replace current processor with enhanced version
cd integrations/slack-bedrock-gateway/lambdas/processor
cp ../../enhanced_processor.py processor.py

# Add agent_tracer dependency
echo "agent_tracer>=1.0.0" >> requirements.txt

# Redeploy
cd ../../../
python3 deploy.py
```

### 2. Integrate Tracing into Agent Instructions

Add to each agent's Lambda function:

```python
import sys
import os
sys.path.append('/opt/python/lib/python3.12/site-packages')

from agent_tracer import create_tracer, trace_data_operation, trace_error

def lambda_handler(event, context):
    # Extract correlation ID from event
    correlation_id = event.get('correlation_id') or event.get('sessionId')
    tracer = create_tracer(correlation_id)
    
    try:
        # Your existing agent logic here
        
        # Trace data operations
        trace_data_operation(
            operation_type="SQL_QUERY",
            data_source="FIREBOLT", 
            query_summary="SELECT opportunities FROM...",
            result_count=5,
            execution_time_ms=150
        )
        
        return result
        
    except Exception as e:
        trace_error(
            error_type=type(e).__name__,
            error_message=str(e),
            agent_context="DataAgent.opportunity_analysis"
        )
        raise
```

### 3. Update Agent Lambda Functions

For each agent Lambda:

```bash
# Add tracing layer
cd tools/[agent_type]/[lambda_dir]

# Copy agent_tracer
cp ../../../monitoring/agent_tracer.py .

# Update requirements.txt
echo "boto3>=1.26.0" >> requirements.txt

# Redeploy
cd ../../../deployment
python3 deploy_production.py --agent [agent_name]
```

### 4. Update Bedrock Agent Instructions

Add to each agent's instructions.md:

```markdown
## Tracing and Debugging

**CRITICAL**: Log all major decisions and data operations for debugging:

1. **Agent Invocations**: When calling collaborators, log the reasoning
2. **Data Operations**: Log SQL queries, API calls, and results
3. **Decision Points**: Log workflow selections and confidence scores
4. **Errors**: Log all errors with context for root cause analysis

Use correlation ID from session for consistent tracing across agents.
```

## Usage Guide

### Debug a Specific Conversation

1. **Find Conversation**:
```
SOURCE /aws/revops-ai/conversation-trace
| fields @timestamp, correlation_id, user_query, query_type
| filter user_query like /YOUR_SEARCH_TERM/
| sort @timestamp desc
| limit 10
```

2. **Trace Complete Flow**:
```
SOURCE /aws/revops-ai/conversation-trace, /aws/revops-ai/agent-collaboration, /aws/revops-ai/data-operations
| fields @timestamp, correlation_id, event_type, agent_name, message_summary
| filter correlation_id = "YOUR_CORRELATION_ID"
| sort @timestamp asc
```

3. **Analyze Agent Chain**:
```
SOURCE /aws/revops-ai/agent-collaboration
| fields @timestamp, source_agent, target_agent, collaboration_type, reasoning
| filter correlation_id = "YOUR_CORRELATION_ID"
| sort @timestamp asc
```

### Common Debug Patterns

#### Issue: Missing Call Data
```
SOURCE /aws/revops-ai/decision-logic
| fields @timestamp, decision_point, workflow_selected, reasoning
| filter correlation_id = "CORRELATION_ID" and decision_point like /deal/
```

#### Issue: SQL/Data Errors
```
SOURCE /aws/revops-ai/data-operations
| fields @timestamp, operation_type, query_summary, error_message
| filter correlation_id = "CORRELATION_ID" and error_message != ""
```

#### Issue: Agent Not Collaborating
```
SOURCE /aws/revops-ai/agent-collaboration
| fields @timestamp, source_agent, target_agent, collaboration_type
| filter correlation_id = "CORRELATION_ID"
| stats count() by source_agent, target_agent
```

## Testing the Implementation

### 1. Basic Test
```bash
# Test query in Slack
@RevBot what is the status of IXIS deal?

# Find correlation ID in dashboard
# Use correlation ID in CloudWatch Insights to trace flow
```

### 2. Validate Tracing
```
# Check all log groups have recent entries
SOURCE /aws/revops-ai/conversation-trace | head 5
SOURCE /aws/revops-ai/agent-collaboration | head 5  
SOURCE /aws/revops-ai/data-operations | head 5
```

### 3. Error Testing
```bash
# Intentionally trigger error
@RevBot analyze deal for NONEXISTENT_COMPANY

# Check error analysis logs
SOURCE /aws/revops-ai/error-analysis | head 10
```

## Integration Checklist

- [ ] CloudWatch log groups created (✅ Done)
- [ ] Dashboard deployed (✅ Done)
- [ ] agent_tracer.py library created (✅ Done)
- [ ] Enhanced Slack processor created (✅ Done)
- [ ] Update Slack-Bedrock processor Lambda
- [ ] Add tracing to Data Agent Lambda
- [ ] Add tracing to WebSearch Agent Lambda  
- [ ] Add tracing to Execution Agent Lambda
- [ ] Update Bedrock agent instructions
- [ ] Test with IXIS deal query
- [ ] Validate 7-day log retention
- [ ] Train team on debugging procedures

## Debugging Workflow for RevOps Debug

1. **Identify Issue**: Get user query and timestamp
2. **Find Correlation ID**: Search conversation-trace log group
3. **Trace Complete Flow**: Use multi-source query to see full chain
4. **Analyze Agent Decisions**: Check decision-logic for reasoning
5. **Review Data Operations**: Check data-operations for queries/results
6. **Identify Root Cause**: Look for errors, missing steps, or logic issues
7. **Implement Fix**: Update agent instructions or knowledge base
8. **Test and Validate**: Re-run same query and verify in logs

## Maintenance

### Log Retention
- Logs automatically purge after 7 days
- Export critical debugging sessions before purge if needed
- Monitor log group sizes and costs

### Query Optimization
- Use time ranges to limit query scope
- Filter early in queries for performance
- Use specific correlation IDs when possible

### Dashboard Updates
- Add new widgets for specific debug patterns
- Update queries based on common issues
- Share dashboard with debugging team

This implementation provides comprehensive visibility into agent chain-of-thought and enables systematic debugging of complex multi-agent interactions.