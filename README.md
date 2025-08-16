# RevOps AI Framework V5

AI-powered revenue operations platform with Slack and API integrations.

## Overview

Production-ready system that analyzes deals, qualifies leads, and provides revenue insights through two input channels:
- **Slack Integration**: Natural language conversations via @RevBot
- **API Integration**: HTTP webhooks for programmatic access

Built on Amazon Bedrock with 6 specialized AI agents handling different revenue operations tasks.

## Architecture

### Input Channels
- **Slack**: `https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events`
- **API**: `https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook`

### AI Agents
- **Manager Agent** (`PVWGKOWSOT`): Routes requests and coordinates other agents
- **Deal Analysis Agent** (`DBHYUWC6U6`): MEDDPICC analysis and deal assessment
- **Lead Analysis Agent** (`IP9HPDIEPL`): ICP scoring and engagement strategies
- **Data Agent** (`NOJMSQ8JPT`): SQL queries against Firebolt and Salesforce data
- **Web Search Agent** (`QKRQXXPJOJ`): External company research
- **Execution Agent** (`AINAPUEIZU`): Webhooks and system actions

### Data Sources
- **Firebolt Data Warehouse**: Revenue and customer analytics
- **Salesforce CRM**: Opportunities, contacts, leads
- **Gong**: Sales call transcripts
- **External Web**: Company intelligence

## Quick Start

### Prerequisites
- AWS CLI configured with profile: `FireboltSystemAdministrator-740202120544`
- Python 3.9+

### Current Status
Both integrations are deployed and operational:
- Slack Integration: ✅ `revops-slack-bedrock-stack`
- API Integration: ✅ `revops-webhook-gateway-stack`

### Test the System

**Slack**:
```
@RevBot what is the status of the IXIS deal?
@RevBot assess John Smith from DataCorp as a lead
@RevBot analyze Q4 revenue performance
```

**API**:
```bash
curl -X POST https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What deals are closing this quarter?",
    "source_system": "test",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

## Usage Examples

### Deal Analysis
```
@RevBot what is the status of the Microsoft Enterprise deal?
@RevBot assess risks for deals closing this quarter
```

**Response Example**:
```
**Deal Status: IXIS-Snowflake**
- Stage: Negotiate (75% probability)
- Size: $2.1M ARR
- Close Quarter: Q4 2025
- Owner: Sarah Johnson

**Risks**: Budget approval delays
**Next Steps**: Champion meeting scheduled
```

### Lead Assessment
```
@RevBot assess Sarah Johnson at TechCorp
@RevBot score our MQL leads from this week
```

**Response Example**:
```
**Lead: John Smith, VP Data Engineering at DataCorp**
- ICP Fit: HIGH (85/100)
- Company: Series B, 200-500 employees
- Tech Stack: Snowflake, modern data tools

**Engagement Strategy**: Focus on performance improvements
**Context Question**: "How are you handling real-time analytics?"
```

### Revenue Analysis
```
@RevBot analyze Q4 pipeline by segment
@RevBot identify expansion opportunities
@RevBot which customers show churn risk?
```

## Integration Endpoints

### Slack Integration
- **Endpoint**: `https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events`
- **Handler**: `revops-slack-bedrock-handler`
- **Processor**: `revops-slack-bedrock-processor`
- **Queue**: `revops-slack-bedrock-processing-queue`

### API Integration
- **Endpoint**: `https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook`
- **Gateway**: `prod-revops-webhook-gateway`
- **Processor**: `revops-webhook`
- **Queue**: `prod-revops-webhook-outbound-queue`

### API Response Format
```json
{
  "success": true,
  "message": "Request queued for processing",
  "tracking_id": "abc-123-def",
  "queued_at": "2025-08-16T10:00:01Z",
  "status": "queued"
}
```

## Monitoring & Troubleshooting

### Check System Health
```bash
# Slack integration logs
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow

# API integration logs  
aws logs tail /aws/lambda/revops-webhook --follow

# Queue status
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-processing-queue \
  --attribute-names ApproximateNumberOfMessages
```

### Common Issues
- **Slow responses**: Check agent timeouts and queue processing
- **Agent not responding**: Verify agent status in AWS Bedrock console
- **Authentication errors**: Confirm AWS profile and permissions

### Conversation Tracking
All conversations are exported to S3: `s3://revops-ai-framework-kb-740202120544/conversation-history/`

## Project Structure

```
revops_ai_framework/
├── agents/                     # AI agent definitions
│   ├── manager_agent/          # Main router
│   ├── deal_analysis_agent/    # Deal assessment
│   ├── lead_analysis_agent/    # Lead qualification
│   ├── data_agent/             # Data queries
│   ├── web_search_agent/       # External research
│   └── execution_agent/        # Actions
├── integrations/               # Input channels
│   ├── slack-bedrock-gateway/  # Slack integration
│   └── webhook-gateway/        # API integration
├── tools/                      # Supporting functions
│   ├── firebolt/               # Data warehouse
│   ├── gong/                   # Call transcripts
│   └── web_search/             # External intel
├── knowledge_base/             # AI knowledge
├── deployment/                 # Infrastructure scripts
└── monitoring/                 # Conversation tracking
```

## Deployment

### Update Slack Integration
```bash
cd integrations/slack-bedrock-gateway
python3 deploy.py
```

### Update API Integration
```bash
cd integrations/webhook-gateway
python3 deploy.py
```

### Update Agents
```bash
cd deployment/scripts
python3 deploy.py --agent manager
python3 deploy.py --agent deal_analysis
```

### Key Resources
- **AWS Profile**: `FireboltSystemAdministrator-740202120544`
- **Region**: `us-east-1`
- **Knowledge Base**: `F61WLOYZSW`
- **S3 Bucket**: `revops-ai-framework-kb-740202120544`