# RevOps AI Agent Tracing Debug Guide

## Quick Start

### 1. Find Conversation by Query
```
SOURCE /aws/revops-ai/conversation-trace
| fields @timestamp, correlation_id, user_query, query_type
| filter user_query like /IXIS/
| sort @timestamp desc
| limit 10
```

### 2. Trace Complete Conversation Flow
```
SOURCE /aws/revops-ai/conversation-trace, /aws/revops-ai/agent-collaboration, /aws/revops-ai/data-operations
| fields @timestamp, correlation_id, event_type, agent_name, message_summary
| filter correlation_id = "YOUR_CORRELATION_ID_HERE"
| sort @timestamp asc
```

### 3. Analyze Agent Collaboration Chain
```
SOURCE /aws/revops-ai/agent-collaboration  
| fields @timestamp, source_agent, target_agent, collaboration_type, reasoning
| filter correlation_id = "YOUR_CORRELATION_ID_HERE"
| sort @timestamp asc
```

### 4. Review Data Operations
```
SOURCE /aws/revops-ai/data-operations
| fields @timestamp, operation_type, data_source, query_summary, result_count, execution_time_ms
| filter correlation_id = "YOUR_CORRELATION_ID_HERE"
| sort @timestamp asc
```

### 5. Error Analysis
```
SOURCE /aws/revops-ai/error-analysis
| fields @timestamp, error_type, error_message, agent_context
| filter @timestamp >= "2025-07-13T10:00:00.000Z" and @timestamp <= "2025-07-13T12:00:00.000Z"
| stats count() by error_type, agent_context
```

## Common Debug Scenarios

### Issue: Agent not retrieving call data
Query to check:
```
SOURCE /aws/revops-ai/decision-logic
| fields @timestamp, decision_point, workflow_selected, reasoning
| filter correlation_id = "CORRELATION_ID" and decision_point like /deal/
```

### Issue: Date logic errors
Query to check:
```
SOURCE /aws/revops-ai/data-operations
| fields @timestamp, query_summary, temporal_context
| filter correlation_id = "CORRELATION_ID" and operation_type = "SQL_QUERY"
```

### Issue: Owner ID not resolved to names
Query to check:
```
SOURCE /aws/revops-ai/data-operations
| fields @timestamp, query_summary, result_count
| filter correlation_id = "CORRELATION_ID" and query_summary like /employee_d/
```

## Dashboard Access
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-ai-agent-tracing