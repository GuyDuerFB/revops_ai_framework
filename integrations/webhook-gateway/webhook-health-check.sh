#!/bin/bash
# RevOps Webhook Gateway Health Check Script
# Usage: ./webhook-health-check.sh
# Requires: AWS CLI configured with FireboltSystemAdministrator-740202120544 profile

set -e

echo "🏥 RevOps Webhook Gateway Health Check"
echo "======================================"

# Set AWS profile
export AWS_PROFILE=FireboltSystemAdministrator-740202120544

# 1. Check Lambda function status
echo "📋 Checking Lambda function configurations..."
MANAGER_TIMEOUT=$(aws lambda get-function-configuration --function-name revops-manager-agent-wrapper --query 'Timeout' --output text)
QUEUE_TIMEOUT=$(aws lambda get-function-configuration --function-name revops-webhook --query 'Timeout' --output text)

echo "   Manager Agent Timeout: ${MANAGER_TIMEOUT}s (should be 900)"
echo "   Queue Processor Timeout: ${QUEUE_TIMEOUT}s (should be 900)"

if [ "$MANAGER_TIMEOUT" -eq 900 ] && [ "$QUEUE_TIMEOUT" -eq 900 ]; then
    echo "   ✅ Lambda timeouts configured correctly"
else
    echo "   ❌ Lambda timeouts not configured correctly"
fi

# 2. Check SQS configuration
echo "📤 Checking SQS queue configuration..."
SQS_VISIBILITY=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue \
  --attribute-names VisibilityTimeout \
  --query 'Attributes.VisibilityTimeout' --output text)

echo "   SQS Visibility Timeout: ${SQS_VISIBILITY}s (should be 960)"

if [ "$SQS_VISIBILITY" -eq 960 ]; then
    echo "   ✅ SQS visibility timeout configured correctly"
else
    echo "   ❌ SQS visibility timeout not configured correctly"
fi

# 3. Check queue backlog
QUEUE_MESSAGES=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' --output text)

echo "   Messages in Queue: ${QUEUE_MESSAGES}"

# 4. Test webhook endpoint
echo "🚀 Testing webhook endpoint..."
RESPONSE=$(curl -s -X POST https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "query": "System health check test",
    "source_system": "health_check",
    "source_process": "validation",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }')

# Parse response
if echo "$RESPONSE" | grep -q '"success":true'; then
    TRACKING_ID=$(echo $RESPONSE | grep -o '"tracking_id":"[^"]*"' | cut -d'"' -f4)
    echo "   ✅ Webhook endpoint responding correctly"
    echo "   📋 Tracking ID: ${TRACKING_ID}"
else
    echo "   ❌ Webhook endpoint error"
    echo "   Response: $RESPONSE"
fi

echo ""
echo "✅ Health check completed."
echo ""
echo "📊 Monitoring Commands:"
echo "   Queue Logs: aws logs tail /aws/lambda/revops-webhook --follow"
echo "   Manager Logs: aws logs tail /aws/lambda/revops-manager-agent-wrapper --follow"
echo "   Gateway Logs: aws logs tail /aws/lambda/prod-revops-webhook-gateway --follow"

# 5. Check recent errors
echo ""
echo "🔍 Checking for recent errors (last 30 minutes)..."
ERROR_COUNT=$(aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-webhook' \
  --filter-pattern 'ERROR' \
  --start-time $(date -d '30 minutes ago' +%s)000 \
  --query 'length(events)' --output text 2>/dev/null || echo "0")

MANAGER_ERROR_COUNT=$(aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-manager-agent-wrapper' \
  --filter-pattern 'ERROR' \
  --start-time $(date -d '30 minutes ago' +%s)000 \
  --query 'length(events)' --output text 2>/dev/null || echo "0")

echo "   Queue Processor Errors (30min): ${ERROR_COUNT}"
echo "   Manager Agent Errors (30min): ${MANAGER_ERROR_COUNT}"

if [ "$ERROR_COUNT" -eq 0 ] && [ "$MANAGER_ERROR_COUNT" -eq 0 ]; then
    echo "   ✅ No recent errors detected"
else
    echo "   ⚠️  Recent errors detected - check CloudWatch logs"
fi

echo ""
echo "🎯 System Status: 🟢 HEALTHY"