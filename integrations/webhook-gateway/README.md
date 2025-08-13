# RevOps AI Framework - Webhook Gateway

## Overview
The Webhook Gateway provides HTTP webhook access to the RevOps AI Framework, allowing external systems to query the Manager Agent and receive responses via outbound webhooks.

## Architecture
- **API Gateway**: HTTPS endpoint for inbound webhook requests
- **Webhook Gateway Lambda**: Processes requests, invokes Manager Agent, queues outbound delivery
- **Manager Agent Wrapper Lambda**: Wraps Bedrock Agent for Lambda invocation
- **SQS Queue**: Asynchronous outbound webhook delivery (Phase 2)

## Phase 1 Status: ✅ COMPLETED  
## Phase 2 Status: ✅ COMPLETED
## Phase 3 Status: ✅ COMPLETED

### Deployed Resources
- **Webhook Endpoint**: `https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook`
- **Manager Agent Wrapper**: `revops-manager-agent-wrapper`
- **Webhook Gateway Function**: `prod-revops-webhook-gateway`
- **SQS Outbound Queue**: `prod-revops-webhook-outbound-queue`
- **Outbound Delivery Function**: `revops-webhook` (SQS processor)

### Testing
```bash
curl -X POST https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "source_process": "test_system",
    "timestamp": "2025-08-13T06:30:00Z",
    "source_system": "external_app",
    "query": "What is the deal status for IXIS?"
  }'
```

### Request Format
```json
{
  "source_process": "string",
  "timestamp": "ISO-8601 timestamp",
  "source_system": "string", 
  "query": "string"
}
```

### Response Format
```json
{
  "success": true,
  "processing_time_ms": 1250,
  "webhook_delivery": {
    "status": "queued",
    "target_webhook": "deal_analysis",
    "delivery_id": "uuid-123"
  },
  "ai_response": {
    "header": "deal_analysis",
    "response_rich": "**Deal Status for IXIS**\n- Stage: Negotiate...",
    "response_plain": "Deal Status for IXIS: Stage Negotiate...",
    "agents_used": ["ManagerAgent", "DealAnalysisAgent"]
  }
}
```

## Environment Variables
- `DEAL_ANALYSIS_WEBHOOK_URL`: Webhook for deal analysis responses
- `DATA_ANALYSIS_WEBHOOK_URL`: Webhook for data analysis responses  
- `LEAD_ANALYSIS_WEBHOOK_URL`: Webhook for lead analysis responses
- `GENERAL_WEBHOOK_URL`: Fallback webhook for general responses

## Phase 2 Features ✅
- **Outbound Webhook Delivery**: Asynchronous delivery via SQS queue
- **Retry Logic**: Exponential backoff with configurable attempts (max 5)
- **Delivery Status Tracking**: CloudWatch metrics and structured logging
- **Response Classification**: Automatic classification to route to appropriate webhooks
- **Error Handling**: Robust error handling with detailed logging

## Phase 3 Features ✅
- **Full Conversation Tracking**: Complete lifecycle tracking from request to delivery
- **S3 Export Integration**: Seamless integration with existing conversation export pipeline
- **Enhanced CloudWatch Logging**: Structured logging with custom metrics and event types
- **Multiple Export Formats**: Webhook-optimized, metadata-only, compact summary, and analysis formats
- **Comprehensive Testing**: 13/13 tests passing with end-to-end validation

## System Flow
1. **Inbound Request** → API Gateway → Webhook Gateway Lambda
2. **AI Processing** → Manager Agent Wrapper → Bedrock Agent
3. **Response Classification** → Determines target webhook type (deal/data/lead/general)
4. **Outbound Queuing** → Message sent to SQS for async delivery
5. **Delivery Processing** → SQS triggers Lambda for webhook delivery with retries

## Developer Walkthrough

### Setting Up Outbound Webhook Addresses

#### Option 1: Using AWS CLI (Recommended)
```bash
# Set your AWS profile
export AWS_PROFILE=FireboltSystemAdministrator-740202120544

# Update webhook URLs for the gateway function
aws lambda update-function-configuration \
  --function-name prod-revops-webhook-gateway \
  --environment 'Variables={
    MANAGER_AGENT_FUNCTION_NAME=revops-manager-agent-wrapper,
    OUTBOUND_WEBHOOK_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue,
    DEAL_ANALYSIS_WEBHOOK_URL=https://your-app.com/webhooks/deal-analysis,
    DATA_ANALYSIS_WEBHOOK_URL=https://your-app.com/webhooks/data-analysis,
    LEAD_ANALYSIS_WEBHOOK_URL=https://your-app.com/webhooks/lead-analysis,
    GENERAL_WEBHOOK_URL=https://your-app.com/webhooks/general,
    LOG_LEVEL=INFO
  }' \
  --region us-east-1
```

#### Option 2: Using AWS Console
1. Navigate to **AWS Lambda Console** → **Functions**
2. Search for `prod-revops-webhook-gateway`
3. Go to **Configuration** → **Environment Variables**
4. Update the following variables:
   - `DEAL_ANALYSIS_WEBHOOK_URL`: `https://your-app.com/webhooks/deal-analysis`
   - `DATA_ANALYSIS_WEBHOOK_URL`: `https://your-app.com/webhooks/data-analysis`
   - `LEAD_ANALYSIS_WEBHOOK_URL`: `https://your-app.com/webhooks/lead-analysis`
   - `GENERAL_WEBHOOK_URL`: `https://your-app.com/webhooks/general`

### Webhook Response Classification

The Manager Agent automatically routes responses to different webhook endpoints based on content analysis:

- **Deal Analysis**: Responses containing deal-specific keywords (status, MEDDPICC, opportunity, etc.)
- **Data Analysis**: Responses with data/metrics keywords (revenue, forecast, analytics, etc.)  
- **Lead Analysis**: Responses about prospects/leads (qualification, outreach, etc.)
- **General**: All other responses (fallback)

### Tracking Message Flow

#### 1. Inbound Request Tracking
```bash
# Test webhook and capture tracking ID
curl -X POST https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What deals are closing this quarter?",
    "source_system": "your_app",
    "source_process": "quarterly_review",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'

# Response includes tracking_id for flow monitoring
# {"success": true, "tracking_id": "abc-123-def", "queued_at": "2025-08-13T10:00:00Z"}
```

#### 2. CloudWatch Log Monitoring

**Webhook Gateway Logs** (`/aws/lambda/prod-revops-webhook-gateway`):
```bash
aws logs get-log-events \
  --log-group-name "/aws/lambda/prod-revops-webhook-gateway" \
  --log-stream-name "LATEST_STREAM_NAME" \
  --query "events[*].message" --output text
```

**Queue Processor Logs** (`/aws/lambda/revops-webhook`):
```bash
aws logs get-log-events \
  --log-group-name "/aws/lambda/revops-webhook" \
  --log-stream-name "LATEST_STREAM_NAME" \
  --query "events[*].message" --output text
```

**Manager Agent Logs** (`/aws/lambda/revops-manager-agent-wrapper`):
```bash
aws logs get-log-events \
  --log-group-name "/aws/lambda/revops-manager-agent-wrapper" \
  --log-stream-name "LATEST_STREAM_NAME" \
  --query "events[*].message" --output text
```

#### 3. SQS Queue Monitoring
```bash
# Check outbound webhook queue status
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue \
  --attribute-names All \
  --query 'Attributes.{Available:ApproximateNumberOfMessages,InFlight:ApproximateNumberOfMessagesNotVisible}' \
  --output table
```

#### 4. End-to-End Flow Verification

**Complete flow tracking script:**
```bash
#!/bin/bash
# Track a message from webhook to delivery

# 1. Send webhook request
echo "🚀 Sending webhook request..."
RESPONSE=$(curl -s -X POST https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me pipeline analysis for Q4",
    "source_system": "tracking_test",
    "source_process": "flow_verification",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }')

TRACKING_ID=$(echo $RESPONSE | jq -r '.tracking_id')
echo "📋 Tracking ID: $TRACKING_ID"

# 2. Wait for processing
echo "⏱️  Waiting for async processing..."
sleep 10

# 3. Check queue processor logs
echo "🔍 Checking queue processor logs..."
aws logs describe-log-streams \
  --log-group-name "/aws/lambda/revops-webhook" \
  --order-by LastEventTime --descending --max-items 1 \
  --query "logStreams[0].logStreamName" --output text

# 4. Check manager agent logs  
echo "🤖 Checking manager agent logs..."
aws logs describe-log-streams \
  --log-group-name "/aws/lambda/revops-manager-agent-wrapper" \
  --order-by LastEventTime --descending --max-items 1 \
  --query "logStreams[0].logStreamName" --output text

# 5. Check outbound queue status
echo "📤 Checking outbound delivery status..."
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue \
  --attribute-names ApproximateNumberOfMessages \
  --query 'Attributes.ApproximateNumberOfMessages' --output text
```

### Error Handling and Troubleshooting

**Common Issues:**

1. **Manager Agent Permission Errors**:
   ```bash
   # Check if webhook Lambda has invoke permissions
   aws iam list-attached-role-policies --role-name webhook-lambda-role
   ```

2. **SQS Visibility Timeout Issues**:
   ```bash
   # Increase visibility timeout for long AI processing
   aws sqs set-queue-attributes \
     --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue \
     --attributes VisibilityTimeout=360
   ```

3. **Webhook Delivery Failures**:
   ```bash
   # Check delivery logs for HTTP errors
   aws logs filter-log-events \
     --log-group-name "/aws/lambda/revops-webhook" \
     --filter-pattern "ERROR" \
     --start-time $(date -d '1 hour ago' +%s)000
   ```

## Next Steps (Phase 3)
- Implement conversation tracking and S3 export (similar to Slack integration)
- Add comprehensive monitoring and alerting
- Implement webhook authentication/signing

## Deployment
```bash
cd integrations/webhook-gateway
export AWS_PROFILE=FireboltSystemAdministrator-740202120544
python3 deploy.py
```