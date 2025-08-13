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

## System Flow
1. **Inbound Request** → API Gateway → Webhook Gateway Lambda
2. **AI Processing** → Manager Agent Wrapper → Bedrock Agent
3. **Response Classification** → Determines target webhook type (deal/data/lead/general)
4. **Outbound Queuing** → Message sent to SQS for async delivery
5. **Delivery Processing** → SQS triggers Lambda for webhook delivery with retries

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