# RevOps AI Framework - Monitoring

Comprehensive monitoring and observability solution for the RevOps AI Framework V4.

## Overview

This directory contains monitoring infrastructure for tracking agent performance, debugging conversations, and analyzing system health.

## Components

### Core Scripts
- **`deploy-agent-tracing.py`** - Deploy CloudWatch infrastructure and dashboards
- **`deploy_enhanced_monitoring.py`** - Deploy enhanced deal assessment monitoring
- **`enhanced_deal_monitoring.py`** - Deal assessment analysis and metrics
- **`agent_tracer.py`** - Agent tracing library for Lambda functions

### Infrastructure
- **`agent-tracing-infrastructure.yaml`** - CloudWatch log groups and dashboard configuration

## Quick Start

### 1. Deploy Basic Monitoring
```bash
# Deploy agent tracing infrastructure
python3 deploy-agent-tracing.py

# Deploy enhanced deal monitoring
python3 deploy_enhanced_monitoring.py
```

### 2. Access Dashboards
- **Agent Tracing**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-ai-agent-tracing
- **Deal Assessment**: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-ai-enhanced-deal-assessment

### 3. Monitor Deal Assessments
```bash
# Generate assessment report
python3 enhanced_deal_monitoring.py --report

# Analyze specific conversation
python3 enhanced_deal_monitoring.py --correlation-id <correlation_id>
```

## Log Groups

The monitoring system uses structured CloudWatch log groups:

- `/aws/revops-ai/conversation-trace` - End-to-end conversation tracking
- `/aws/revops-ai/agent-collaboration` - Agent-to-agent interactions
- `/aws/revops-ai/data-operations` - SQL queries and data retrieval
- `/aws/revops-ai/decision-logic` - Decision agent reasoning
- `/aws/revops-ai/error-analysis` - Errors and failure patterns

## Debugging Workflow

### 1. Find Conversation
```bash
# Search conversation logs
SOURCE /aws/revops-ai/conversation-trace
| filter user_query like /IXIS/
| sort @timestamp desc
```

### 2. Trace Complete Flow
```bash
# Multi-source query with correlation ID
SOURCE /aws/revops-ai/conversation-trace, /aws/revops-ai/agent-collaboration, /aws/revops-ai/data-operations
| filter correlation_id = "YOUR_CORRELATION_ID"
| sort @timestamp asc
```

### 3. Analyze Agent Decisions
```bash
# Check decision logic
SOURCE /aws/revops-ai/decision-logic
| filter correlation_id = "YOUR_CORRELATION_ID"
| fields @timestamp, decision_point, workflow_selected, reasoning
```

## Deal Assessment Monitoring

The enhanced monitoring system tracks:

- **Assessment Status**: Complete, partial, or failed
- **Data Sources**: SFDC opportunity data and call data retrieval
- **Processing Time**: End-to-end assessment duration
- **Agent Collaboration**: Multi-agent workflow execution

### Key Metrics
- **Completion Rate**: Percentage of assessments with both data sources
- **Processing Time**: Average time for deal assessments
- **Error Rate**: Failed assessments requiring intervention

## Common Debug Patterns

### Missing Call Data
```bash
# Check data operations for call retrieval
SOURCE /aws/revops-ai/data-operations
| filter correlation_id = "CORRELATION_ID" and data_source like /gong/
```

### SQL Errors
```bash
# Check for query errors
SOURCE /aws/revops-ai/data-operations
| filter correlation_id = "CORRELATION_ID" and error_message != ""
```

### Agent Collaboration Issues
```bash
# Analyze agent interactions
SOURCE /aws/revops-ai/agent-collaboration
| filter correlation_id = "CORRELATION_ID"
| stats count() by source_agent, target_agent
```

## Performance Monitoring

### CloudWatch Metrics
- **RevOpsAI/DealAssessment/AssessmentStatus** - Deal assessment outcomes
- **RevOpsAI/DealAssessment/ProcessingTimeMs** - Assessment duration
- **RevOpsAI/DealAssessment/AgentsInvoked** - Multi-agent coordination

### Alarms
- **RevOpsAI-DealAssessment-HighFailureRate** - Too many failed assessments
- **RevOpsAI-DealAssessment-SlowProcessing** - Processing time > 30 seconds
- **RevOpsAI-DealAssessment-DataRetrievalIssues** - Data source failures

## Maintenance

### Log Retention
- All log groups: 7-day retention
- Export critical sessions before purge if needed
- Monitor log group sizes for cost optimization

### Query Performance
- Use correlation IDs for efficient filtering
- Apply time ranges to limit scope
- Use specific log groups when possible

### Dashboard Updates
- Add widgets for new debug patterns
- Update queries based on common issues
- Share dashboard access with debugging team

## Security

- IAM roles follow least privilege principle
- No sensitive data logged in structured events
- Correlation IDs are UUID-based for security
- All logging data encrypted at rest and in transit

## Support

For monitoring issues:
1. Check CloudWatch dashboard for system health
2. Review agent tracing logs for conversation flow
3. Use enhanced monitoring for deal assessment analysis
4. Consult correlation IDs for systematic debugging

---

**Framework Version**: V3  
**Last Updated**: July 2025  
**Monitoring Region**: us-east-1