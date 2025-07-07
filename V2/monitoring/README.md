# Enhanced Monitoring and Logging

Comprehensive monitoring solution for the RevOps AI Framework, providing real-time visibility into system performance, error tracking, and operational insights.

## Components

### 1. CloudFormation Template
- **File**: `enhanced-logging-solution.yaml`
- **Purpose**: Deploys monitoring infrastructure including CloudWatch dashboard, alarms, SNS alerts, and log analysis functions

### 2. Deployment Script
- **File**: `deploy-monitoring.py`
- **Purpose**: Automated deployment of monitoring stack with CloudWatch Insights queries and troubleshooting runbook

### 3. Troubleshooting Runbook
- **File**: `troubleshooting-runbook.md` (auto-generated)
- **Purpose**: Operational guide with common failure scenarios and diagnostic commands

## Features

### Real-time Monitoring
- **CloudWatch Dashboard**: Lambda performance, SQS metrics, error visualization
- **Automated Alarms**: Error detection, timeout warnings, dead letter queue alerts
- **SNS Notifications**: Critical issue alerting

### Log Analysis
- **Scheduled Lambda**: Automated pattern detection every 15 minutes
- **CloudWatch Insights Queries**: Pre-configured queries for common troubleshooting scenarios
- **Error Correlation**: Cross-reference errors across all system components

### Operational Tools
- **Diagnostic Commands**: Ready-to-use AWS CLI commands for health checks
- **Troubleshooting Runbook**: Step-by-step resolution guides
- **Performance Baselines**: Historical metrics for comparison

## Deployment

```bash
cd monitoring
python3 deploy-monitoring.py
```

## Accessing Monitoring

### CloudWatch Dashboard
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-slack-bedrock-monitoring

### CloudWatch Insights Queries
- `revops-bedrock-timeout-analysis`: Analyze timeout patterns and user queries
- `revops-user-request-complexity`: Track query complexity trends
- `revops-collaboration-patterns`: Monitor agent collaboration efficiency
- `revops-error-correlation`: Correlate errors across system components

### SNS Alerts
Subscribe to the `revops-slack-bedrock-alerts` topic for automated notifications.

## Troubleshooting Commands

### Quick Health Check
```bash
# Check processing queue
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-processing-queue \
  --attribute-names ApproximateNumberOfMessages

# Check for recent errors
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'ERROR' \
  --start-time $(date -u -d '1 hour ago' +%s)000

# Check dead letter queue
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-dlq \
  --attribute-names ApproximateNumberOfMessages
```

### Performance Monitoring
```bash
# Lambda duration metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=revops-slack-bedrock-processor \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Maximum,Average

# Error rate monitoring
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=revops-slack-bedrock-processor \
  --start-time $(date -u -d '1 hour ago' --iso-8601) \
  --end-time $(date -u --iso-8601) \
  --period 300 \
  --statistics Sum
```

## Key Metrics to Monitor

### Performance Indicators
- **Lambda Duration**: Should be under 280 seconds (5-minute timeout)
- **SQS Message Age**: Messages should process within minutes
- **Error Rate**: Should be less than 1% of total invocations
- **Dead Letter Queue**: Should remain at 0 under normal operation

### Alert Thresholds
- **Processor Errors**: ≥1 error in 5 minutes
- **Processor Timeouts**: Duration >290 seconds
- **Dead Letter Queue**: >0 messages

## Integration with Existing System

The monitoring solution integrates seamlessly with:
- **Slack Integration**: Tracks request processing from Slack events
- **Bedrock Agents**: Monitors agent collaboration and timeouts
- **Lambda Functions**: Performance and error tracking for all functions
- **SQS Queues**: Message processing and dead letter queue monitoring

## Maintenance

### Log Retention
- Handler logs: 30 days
- Processor logs: 30 days
- Detailed monitoring logs: 90 days

### Cost Optimization
- CloudWatch Insights queries run on-demand
- Log analysis Lambda executes every 15 minutes
- SNS notifications only for critical events
- Dashboard refreshes every 5 minutes

## Security

- IAM roles follow least privilege principle
- No sensitive data logged or exposed
- Secrets remain in AWS Secrets Manager
- Monitoring data encrypted at rest and in transit

This monitoring solution provides enterprise-grade observability for the RevOps AI Framework, ensuring reliable operation and rapid issue resolution.