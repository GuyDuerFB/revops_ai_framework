# Agent Tracing Implementation Testing & Validation

## Implementation Status ✅ COMPLETED

### Components Integrated

✅ **CloudWatch Infrastructure**
- 5 log groups created with 7-day retention
- Dashboard deployed with monitoring widgets
- Saved queries created for common debug patterns

✅ **Agent Tracer Library** (`monitoring/agent_tracer.py`)
- Structured logging with correlation IDs
- Event types for conversation, collaboration, data operations, errors
- Fallback handlers for environments without CloudWatch access

✅ **Lambda Function Integration**
- **Firebolt Query Lambda**: Full tracing with SQL operation tracking
- **Gong Retrieval Lambda**: API call tracing with timing metrics
- **Web Search Lambda**: Search operation and company research tracing

✅ **Enhanced Slack Processor**
- Conversation start/end tracing
- Temporal context extraction and logging
- Agent collaboration chain tracking
- Error handling with structured logging

## Testing Guide

### 1. Test Query for IXIS Deal Analysis

**Query to test in Slack:**
```
@RevBot what is the status of IXIS deal?
```

**Expected Tracing Behavior:**
- Conversation start logged with correlation ID: `slack_{timestamp}_{user_id}`
- Temporal context extraction: current date = 2025-07-13
- Agent invocation: SlackProcessor → DecisionAgent
- Data operations logged for SQL queries to find IXIS opportunities
- Call data retrieval with proper owner name resolution
- Conversation end with processing time and agent count

### 2. Validation Steps

#### Step 1: Trigger Test Query
```bash
# In Slack workspace
@RevBot what is the status of IXIS deal?
```

#### Step 2: Find Correlation ID
```
SOURCE /aws/revops-ai/conversation-trace
| fields @timestamp, correlation_id, user_query
| filter user_query like /IXIS/
| sort @timestamp desc
| limit 5
```

#### Step 3: Trace Complete Flow
```
SOURCE /aws/revops-ai/conversation-trace, /aws/revops-ai/agent-collaboration, /aws/revops-ai/data-operations
| fields @timestamp, correlation_id, event_type, agent_name, message_summary
| filter correlation_id = "YOUR_CORRELATION_ID"
| sort @timestamp asc
```

#### Step 4: Verify Data Operations
```
SOURCE /aws/revops-ai/data-operations
| fields @timestamp, operation_type, data_source, query_summary, result_count
| filter correlation_id = "YOUR_CORRELATION_ID"
| sort @timestamp asc
```

#### Step 5: Check Agent Collaborations
```
SOURCE /aws/revops-ai/agent-collaboration
| fields @timestamp, source_agent, target_agent, collaboration_type, reasoning
| filter correlation_id = "YOUR_CORRELATION_ID"
| sort @timestamp asc
```

### 3. Expected Results Validation

#### ✅ Original Issues Should Be Fixed:

1. **Date Logic Error**
   - Should see temporal context: "Current date: 2025-07-13"
   - No more "May 2025 is in the future" errors
   - Proper date comparisons in SQL queries

2. **Call Data Retrieval**
   - Should see data operations for both opportunity and call queries
   - Decision logic should show dual-mode analysis triggered
   - Call data should be retrieved and included in response

3. **Owner Name Resolution**
   - SQL queries should include employee_d joins
   - Owner names should appear in response instead of IDs
   - Data operations should show successful joins

#### ✅ Tracing Coverage:

1. **Conversation Tracing**
   - Start event with user query and temporal context
   - End event with response summary and processing time
   - Correlation ID consistency across all events

2. **Agent Collaboration**
   - SlackProcessor → DecisionAgent invocation
   - DecisionAgent → DataAgent collaboration
   - Any additional agent invocations

3. **Data Operations**
   - SQL queries to Firebolt with execution times
   - Gong API calls for retrieving call information
   - Web search operations if company research is performed

4. **Error Handling**
   - Any errors logged with context and correlation ID
   - Recovery attempts tracked
   - Meaningful error messages to users

### 4. Performance Validation

#### Expected Processing Times:
- Simple queries: < 5 seconds
- Complex deal analysis: 15-30 seconds
- With call data retrieval: 30-60 seconds

#### Tracing Overhead:
- Minimal impact (< 100ms additional processing)
- Structured JSON logging for efficient parsing
- 7-day retention to balance debugging needs with costs

### 5. Dashboard Validation

**Access Dashboard:**
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-ai-agent-tracing

**Widgets to Verify:**
1. **Recent Conversations** - Shows latest user queries
2. **Agent Collaborations** - Shows agent interaction patterns
3. **Data Operations** - Shows SQL/API performance
4. **Error Analysis** - Shows error patterns and frequency

### 6. Debugging Workflow Test

**Scenario**: Reproduce original IXIS deal analysis issues

1. **Find the conversation**:
   ```
   SOURCE /aws/revops-ai/conversation-trace
   | filter user_query like /IXIS/
   | sort @timestamp desc
   | limit 1
   ```

2. **Extract correlation ID** from results

3. **Trace complete flow**:
   ```
   SOURCE /aws/revops-ai/conversation-trace, /aws/revops-ai/agent-collaboration, /aws/revops-ai/data-operations, /aws/revops-ai/decision-logic
   | filter correlation_id = "CORRELATION_ID"
   | sort @timestamp asc
   ```

4. **Analyze specific issues**:
   - **Date Logic**: Check temporal_context field in conversation-trace
   - **Call Data**: Look for GONG_API_CALL operations in data-operations
   - **Owner Names**: Check for employee_d joins in SQL query_summary fields

## Integration Verification Checklist

- [ ] **CloudWatch Log Groups**: All 5 groups exist with 7-day retention
- [ ] **Agent Tracer Library**: Successfully imported in all Lambda functions
- [ ] **Firebolt Query Lambda**: SQL operations traced with timing
- [ ] **Gong Retrieval Lambda**: API calls traced with result counts
- [ ] **Web Search Lambda**: Search operations traced
- [ ] **Enhanced Slack Processor**: Conversation flow traced end-to-end
- [ ] **Dashboard**: Accessible with relevant widgets displaying data
- [ ] **IXIS Test Query**: Successfully traced with correlation ID
- [ ] **Original Issues**: All three issues resolved and traceable
- [ ] **Performance**: Minimal overhead, acceptable processing times

## Rollback Plan

If issues are encountered:

1. **Lambda Functions**: Revert to previous versions without tracing
2. **Slack Processor**: Restore original processor.py from backup
3. **CloudWatch**: Log groups can remain (no impact on functionality)
4. **Agent Instructions**: Revert to previous versions if needed

## Support and Maintenance

### Log Retention
- Logs automatically purge after 7 days
- Export critical debugging sessions before purge if needed
- Monitor log group sizes and costs weekly

### Query Optimization
- Use time ranges to limit query scope
- Filter early in queries for performance
- Use specific correlation IDs when possible

### Troubleshooting
- Check agent_tracer import in Lambda function logs
- Verify CloudWatch permissions for log group access
- Ensure correlation IDs are properly propagated

This comprehensive testing validation ensures the agent tracing implementation successfully addresses the original debugging challenges while providing systematic observability for future issues.