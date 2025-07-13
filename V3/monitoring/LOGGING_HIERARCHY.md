# RevOps AI Framework - Coherent Logging Hierarchy

## Overview

This document provides a comprehensive view of the logging architecture for the RevOps AI Framework, designed to enable systematic debugging and root cause analysis of multi-agent interactions.

## CloudWatch Log Groups Architecture

### Primary Log Groups (7-day retention)

#### 1. `/aws/revops-ai/conversation-trace`
**Purpose**: End-to-end conversation tracking and temporal context
**Events**: 
- `CONVERSATION_START`: User query initiation with temporal context
- `CONVERSATION_END`: Final response with processing metrics
- `TEMPORAL_CONTEXT`: Date/time reference extraction and injection

**Key Fields**:
- `correlation_id`: Unique identifier for conversation thread
- `user_query`: Original user input
- `temporal_context`: Current date and time references
- `processing_time_ms`: Total conversation processing time
- `success`: Boolean indicating conversation completion status

#### 2. `/aws/revops-ai/agent-collaboration`
**Purpose**: Agent-to-agent interactions and collaboration patterns
**Events**:
- `AGENT_INVOCATION`: One agent calling another
- `COLLABORATION_START`: Multi-agent workflow initiation
- `COLLABORATION_END`: Workflow completion with results

**Key Fields**:
- `source_agent`: Agent initiating the collaboration
- `target_agent`: Agent being invoked
- `collaboration_type`: Type of interaction (SUPERVISOR, DATA_ANALYSIS, etc.)
- `reasoning`: Why this collaboration was initiated
- `workflow_selected`: Specific workflow or strategy chosen

#### 3. `/aws/revops-ai/data-operations`
**Purpose**: SQL queries, API calls, and data retrieval operations
**Events**:
- `SQL_QUERY`: Firebolt database queries
- `GONG_API_CALL`: Gong API interactions
- `WEB_SEARCH`: DuckDuckGo search operations
- `COMPANY_RESEARCH`: Targeted company information gathering

**Key Fields**:
- `operation_type`: Type of data operation
- `data_source`: Source system (FIREBOLT, GONG, DUCKDUCKGO)
- `query_summary`: Abbreviated query or operation description
- `result_count`: Number of results returned
- `execution_time_ms`: Operation execution time

#### 4. `/aws/revops-ai/decision-logic`
**Purpose**: Decision agent reasoning and workflow selection
**Events**:
- `WORKFLOW_SELECTION`: Which analysis workflow was chosen
- `DECISION_POINT`: Key decision moments in analysis
- `CONFIDENCE_ASSESSMENT`: Confidence levels for recommendations

**Key Fields**:
- `decision_point`: Stage of analysis (initial_assessment, data_collection, etc.)
- `workflow_selected`: Chosen workflow (deal_analysis, lead_research, etc.)
- `reasoning`: Explanation of decision logic
- `confidence_score`: Numerical confidence level (0-100)
- `context_factors`: Factors influencing the decision

#### 5. `/aws/revops-ai/error-analysis`
**Purpose**: Errors, failures, and recovery attempts
**Events**:
- `ERROR_OCCURRED`: Any system error or exception
- `RECOVERY_ATTEMPTED`: Retry or fallback operations
- `DEGRADED_SERVICE`: Partial service availability

**Key Fields**:
- `error_type`: Exception class name
- `error_message`: Error description
- `agent_context`: Which agent/component experienced the error
- `recovery_attempted`: Whether recovery was tried
- `impact_level`: Severity of the error (LOW, MEDIUM, HIGH, CRITICAL)

## Correlation ID Strategy

### Format: `{source}_{timestamp}_{identifier}`

**Examples**:
- Slack: `slack_1720872000_U01234567`
- Direct API: `api_1720872000_req123`
- Scheduled Task: `sched_1720872000_daily`

### Propagation Path:
1. **Slack Processor** → Creates correlation ID
2. **Decision Agent** → Receives via sessionId
3. **Data Agent** → Inherits from Decision Agent context
4. **Lambda Functions** → Extract from event parameters
5. **CloudWatch Logs** → Include in all log entries

## Integration Points

### Lambda Functions with Tracing

#### Enhanced Functions:
- **Firebolt Query Lambda**: SQL operation tracing
- **Gong Retrieval Lambda**: API call tracing
- **Web Search Lambda**: Search operation tracing
- **Slack-Bedrock Processor**: Conversation flow tracing

#### Tracing Pattern:
```python
# Import agent tracer
from agent_tracer import trace_data_operation, trace_error

# Trace operations
trace_data_operation(
    operation_type="SQL_QUERY",
    data_source="FIREBOLT",
    query_summary="SELECT opportunities...",
    result_count=5,
    execution_time_ms=150
)
```

### Agent Instruction Integration

#### Bedrock Agents with Tracing Context:
- **Decision Agent**: Workflow selection logging
- **Data Agent**: Query execution logging
- **WebSearch Agent**: Research operation logging
- **Execution Agent**: Action execution logging

#### Instruction Pattern:
```markdown
## Tracing and Debugging

**CRITICAL**: Log all major decisions and data operations:
1. **Agent Invocations**: Log reasoning for collaborator calls
2. **Data Operations**: Log SQL queries, API calls, results
3. **Decision Points**: Log workflow selections and confidence
4. **Errors**: Log all errors with context

Use correlation ID from session for consistent tracing.
```

## Dashboard and Monitoring

### CloudWatch Dashboard
**URL**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-ai-agent-tracing

**Widgets**:
1. **Recent Conversations**: Latest user queries and processing times
2. **Agent Collaborations**: Interaction patterns and frequencies
3. **Data Operation Performance**: Query times and success rates
4. **Error Trends**: Error patterns and recovery success

### Saved Queries for Common Patterns

#### Find Conversation by Query:
```
SOURCE /aws/revops-ai/conversation-trace
| filter user_query like /SEARCH_TERM/
| sort @timestamp desc
```

#### Trace Complete Flow:
```
SOURCE /aws/revops-ai/conversation-trace, /aws/revops-ai/agent-collaboration, /aws/revops-ai/data-operations
| filter correlation_id = "CORRELATION_ID"
| sort @timestamp asc
```

#### Performance Analysis:
```
SOURCE /aws/revops-ai/data-operations
| filter execution_time_ms > 5000
| stats count() by data_source, operation_type
```

## Debugging Workflow

### Standard Debugging Process:

1. **Identify Issue**: Get user query and timestamp
2. **Find Correlation ID**: Search conversation-trace log group
3. **Trace Complete Flow**: Multi-source query across all log groups
4. **Analyze Components**:
   - **Temporal Context**: Check date/time handling
   - **Agent Decisions**: Review decision-logic entries
   - **Data Operations**: Examine query performance and results
   - **Collaborations**: Verify agent interaction patterns
5. **Identify Root Cause**: Look for errors, missing steps, logic issues
6. **Implement Fix**: Update instructions, fix code, adjust configuration
7. **Validate**: Re-run query and verify in logs

### Issue-Specific Queries:

#### Date Logic Errors:
```
SOURCE /aws/revops-ai/conversation-trace
| filter correlation_id = "ID" and temporal_context != ""
```

#### Missing Call Data:
```
SOURCE /aws/revops-ai/data-operations
| filter correlation_id = "ID" and operation_type = "GONG_API_CALL"
```

#### Owner Name Resolution:
```
SOURCE /aws/revops-ai/data-operations
| filter correlation_id = "ID" and query_summary like /employee_d/
```

## Maintenance and Operations

### Log Retention Policy
- **Duration**: 7 days automatic retention
- **Rationale**: Balance between debugging needs and cost optimization
- **Export**: Critical debugging sessions can be exported before purge

### Performance Considerations
- **Tracing Overhead**: < 100ms per operation
- **Log Volume**: Estimated 10-50 MB per day
- **Query Performance**: Use time ranges and correlation IDs for efficiency

### Cost Optimization
- **Log Groups**: Standard CloudWatch pricing
- **Retention**: 7-day auto-purge reduces storage costs
- **Queries**: Use saved queries to avoid repeated complex operations

### Monitoring Health
- **Dashboard**: Monitor error rates and performance trends
- **Alerts**: Can be configured for high error rates or performance degradation
- **Metrics**: Track conversation success rates and processing times

## Security and Compliance

### Data Handling
- **PII**: User IDs are hashed or anonymized in logs
- **Queries**: SQL queries logged with sensitive data redacted
- **Retention**: 7-day retention limits exposure window

### Access Control
- **CloudWatch**: IAM-based access to log groups
- **Dashboard**: Team-specific access permissions
- **Queries**: Logged access for audit trail

This coherent logging hierarchy provides comprehensive observability for the RevOps AI Framework while maintaining performance, cost efficiency, and security best practices.