# RevOps AI Framework V5

Enterprise-grade AI-powered Revenue Operations Framework with Enhanced Conversation Monitoring

## Overview

### What It Does
The RevOps AI Framework is a production-ready platform that transforms how revenue teams work by providing instant, intelligent analysis of deals, leads, and revenue data. Instead of manually digging through CRM data and spreadsheets, teams can ask natural questions and get comprehensive insights in seconds.

### Business Value
- **10x Faster Analysis**: Get deal assessments and lead scoring in seconds, not hours
- **Consistent Decision-Making**: Standardized MEDDPICC and ICP evaluation across all deals and leads
- **Proactive Risk Management**: Early identification of at-risk deals and churning customers
- **Data-Driven Insights**: Comprehensive analysis combining CRM, call transcripts, and external intelligence
- **Team Productivity**: Revenue teams focus on selling, not data gathering

### How It Works
The system accepts input through two channels:
- **Slack Integration**: Natural language conversations via @RevBot mentions
- **API Integration**: HTTP webhooks for programmatic access from other systems

Both channels leverage 6 specialized AI agents built on Amazon Bedrock that analyze data from Firebolt, Salesforce, Gong, and external sources to provide comprehensive revenue operations insights.

## Architecture

### Multi-Agent System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    INPUT CHANNELS                                   │
│  ┌─────────────────────┐    ┌─────────────────────────────────────┐ │
│  │   SLACK INTEGRATION │    │        API INTEGRATION              │ │
│  │   @RevBot mentions  │    │   HTTP Webhook Gateway              │ │
│  └─────────────────────┘    └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MANAGER AGENT (SUPERVISOR)                      │
│  • Intelligent routing to dedicated specialized agents             │
│  • Handles general queries with general-purpose collaborators      │
│  • Coordinates multi-agent workflows                               │
│  • Maintains conversation context and continuity                   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
    ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
    │  DEDICATED AGENTS   │ │  GENERAL AGENTS     │ │  GENERAL AGENTS     │
    │  (Specific Cases)   │ │  (Broad Capability) │ │  (Broad Capability) │
    └─────────────────────┘ └─────────────────────┘ └─────────────────────┘
                │                       │                       │
        ┌───────┴───────┐       ┌───────┴───────┐       ┌───────┴───────┐
        ▼               ▼       ▼               ▼       ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│DEAL ANALYSIS│ │LEAD ANALYSIS│ │ DATA AGENT  │ │ WEBSEARCH   │ │ EXECUTION   │
│   AGENT     │ │   AGENT     │ │             │ │   AGENT     │ │   AGENT     │
│ (DEDICATED) │ │ (DEDICATED) │ │ (GENERAL)   │ │ (GENERAL)   │ │ (GENERAL)   │
│             │ │             │ │             │ │             │ │             │
│• MEDDPICC   │ │• ICP Scoring│ │• SQL Queries│ │• Market     │ │• Webhooks   │
│• Risk Anal. │ │• Qualificat.│ │• Salesforce │ │  Intel      │ │• CRM Updates│
│• Probability│ │• Outreach   │ │• Gong Calls │ │• Company    │ │• Notificat. │
│• Deal Focus │ │  Strategy   │ │• Analytics  │ │  Research   │ │• Actions    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
       │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   TOOLS:    │ │   TOOLS:    │ │   TOOLS:    │ │   TOOLS:    │ │   TOOLS:    │
│• Firebolt   │ │• Firebolt   │ │• Firebolt   │ │• Web Search │ │• Webhook    │
│  SQL Query  │ │  SQL Query  │ │  SQL Query  │ │• Company    │ │  Executor   │
│             │ │• Web Search │ │• Gong API   │ │  Research   │ │• Firebolt   │
│             │ │             │ │             │ │             │ │  Writer     │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │    DATA SOURCES     │
                            │                     │
                            │• Firebolt DWH       │
                            │• Salesforce CRM     │
                            │• Gong Conversations │
                            │• External Web APIs  │
                            └─────────────────────┘
```

### Agent Specialization

**DEDICATED AGENTS (Specific Use Cases):**
- **Deal Analysis Agent** (`DBHYUWC6U6`): ONLY for deal status, MEDDPICC analysis, opportunity assessment
- **Lead Analysis Agent** (`IP9HPDIEPL`): ONLY for lead qualification, ICP scoring, engagement strategies

**GENERAL AGENTS (Broad Capabilities):**
- **Manager Agent** (`PVWGKOWSOT`): Routes requests and coordinates all other agents (SUPERVISOR)
- **Data Agent** (`NOJMSQ8JPT`): General data queries across all revenue operations (Firebolt + Gong)
- **Web Search Agent** (`QKRQXXPJOJ`): External intelligence and company research for any use case
- **Execution Agent** (`AINAPUEIZU`): Actions and integrations for any workflow (Webhooks + Firebolt writes)

### Routing Logic Examples
- "Status of IXIS deal" → Routes to Deal Analysis Agent (dedicated)
- "Assess John Smith from DataCorp" → Routes to Lead Analysis Agent (dedicated)
- "Q4 revenue trends" → Uses Data Agent + other general agents as needed
- "Research TechCorp company" → Uses Web Search Agent (general capability)
- "Send notification to AE" → Uses Execution Agent (general capability)

## Data Flow

### Slack Integration Flow

**End-to-End Process:**
```
00:00 - User: "@RevBot what is the status of the IXIS deal?"
00:01 - Slack → API Gateway → Handler Lambda (signature validation)
00:02 - Handler Lambda → Slack: "👋 Hey there! I'm diving into your data right now..."
00:02 - Handler Lambda → SQS Queue (async processing)
00:03 - SQS → Processor Lambda → Manager Agent
00:05 - Manager Agent → Deal Analysis Agent (intent: deal analysis)
00:10 - Deal Analysis Agent → Firebolt Lambda (SQL queries)
00:15 - Firebolt returns deal data (stage, probability, risks)
00:20 - Deal Analysis Agent → MEDDPICC analysis
00:25 - Deal Analysis Agent → Manager Agent (structured response)
00:26 - Manager Agent → Processor Lambda (final response)
00:27 - Processor Lambda → Slack (comprehensive deal analysis)
00:28 - Conversation exported to S3 for monitoring
```

**AWS Resources:**
- **API Gateway**: `https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events`
- **Handler Lambda**: `revops-slack-bedrock-handler` (30s timeout, 256MB memory)
- **Processor Lambda**: `revops-slack-bedrock-processor` (300s timeout, 512MB memory)
- **SQS Queue**: `revops-slack-bedrock-processing-queue` (5min visibility timeout)
- **CloudWatch Logs**: `/aws/lambda/revops-slack-bedrock-handler`, `/aws/lambda/revops-slack-bedrock-processor`

### API Integration Flow

**End-to-End Process:**
```
00:00 - External System → HTTP POST to API Gateway
00:01 - API Gateway → Webhook Gateway Lambda (request validation)
00:02 - Webhook Gateway Lambda → SQS Queue + Immediate Response
00:02 - Client receives tracking ID and continues processing
00:03 - SQS → Queue Processor Lambda → Manager Agent Wrapper
00:05 - Manager Agent Wrapper → Manager Agent (Bedrock)
00:10 - Manager Agent → Data Agent (pipeline analysis)
00:15 - Data Agent → Firebolt Lambda (Q4 deals query)
00:25 - Firebolt returns pipeline data (deals, stages, probabilities)
00:35 - Data Agent → Manager Agent (structured data)
00:40 - Manager Agent → comprehensive analysis and insights
00:45 - Manager Agent Wrapper → Queue Processor (formatted response)
00:46 - Queue Processor → External webhook delivery
00:47 - External system receives AI analysis via webhook
```

**AWS Resources:**
- **API Gateway**: `https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook`
- **Webhook Gateway Lambda**: `prod-revops-webhook-gateway` (15min timeout, 512MB memory)
- **Manager Agent Wrapper**: `revops-manager-agent-wrapper` (15min timeout, 512MB memory)
- **Queue Processor Lambda**: `revops-webhook` (15min timeout, processes SQS messages)
- **SQS Queue**: `prod-revops-webhook-outbound-queue` (16min visibility timeout)

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

**API Response Format:**
```json
{
  "success": true,
  "message": "Request queued for processing",
  "tracking_id": "abc-123-def",
  "queued_at": "2025-08-16T10:00:01Z",
  "status": "queued"
}
```

## Usage Examples

### Deal Analysis
```
@RevBot what is the status of the Microsoft Enterprise deal?
@RevBot assess risks for deals closing this quarter
@RevBot analyze the TechCorp opportunity probability
```

**Response Example**:
```
**Deal Status: IXIS-Snowflake**
- Stage: Negotiate (75% probability)
- Size: $2.1M ARR
- Close Quarter: Q4 2025
- Owner: Sarah Johnson

**MEDDPICC Analysis:**
- Metrics: Cost savings validated at $500K annually
- Economic Buyer: CFO engaged, budget approved
- Decision Criteria: Performance and cost reduction
- Decision Process: Technical validation → Budget → Legal
- Paper Process: Standard MSA, procurement team involved
- Identify Pain: Current Snowflake costs unsustainable
- Champion: Data Engineering Director advocating internally

**Risks**: Budget approval delays, competing priorities
**Next Steps**: Champion meeting scheduled, technical validation pending
```

### Lead Assessment
```
@RevBot assess Sarah Johnson at TechCorp
@RevBot score our MQL leads from this week
@RevBot research DataCorp and assess their fit
```

**Response Example**:
```
**Lead: John Smith, VP Data Engineering at DataCorp**
- ICP Fit: HIGH (85/100)
- Company: Series B, 200-500 employees, $50M revenue
- Tech Stack: Snowflake, dbt, Looker, AWS infrastructure
- Recent Activity: Expanding analytics team, raised $25M Series B

**ICP Analysis:**
✅ Company size matches target (200-500 employees)
✅ Technology stack includes target tools (Snowflake)
✅ Growth stage indicates budget availability
✅ Data maturity suggests performance needs

**Engagement Strategy:**
- Context Question: "How are you handling real-time analytics at scale with your current Snowflake setup?"
- Value Prop Focus: Performance improvements and cost optimization
- Recommended Channel: LinkedIn technical discussion
- Follow-up: Share cost optimization case study
```

### Revenue Analysis
```
@RevBot analyze Q4 pipeline by segment
@RevBot identify expansion opportunities based on usage trends
@RevBot which customers show churn risk signals?
```

## End-to-End Monitoring & Observability

### Conversation Tracking
All conversations are automatically exported to S3 with complete tracing:
- **Location**: `s3://revops-ai-framework-kb-740202120544/conversation-history/`
- **Format**: Enhanced LLM-readable JSON with agent collaboration mapping
- **Contents**: Complete conversation flow, agent handoffs, tool executions, timing

**S3 Export Structure:**
```
s3://revops-ai-framework-kb-740202120544/conversation-history/
└── 2025/08/16/2025-08-16T14-30-15/
    ├── conversation.json    ← Complete conversation with agent traces
    └── metadata.json        ← Export metadata and quality metrics
```

### Slack Integration Monitoring

**Real-time Monitoring:**
```bash
# Monitor live processing
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow

# Track specific conversation by user
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'user_id:U123456'

# Check processing queue status
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-processing-queue \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible
```

**Agent Invocation Tracking:**
```bash
# Monitor Manager Agent invocations
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'Invoking Manager Agent' \
  --start-time $(date -d '1 hour ago' +%s)000

# Track agent collaboration patterns
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'Agent collaboration:' \
  --start-time $(date -d '24 hours ago' +%s)000
```

### API Integration Monitoring

**Request Tracking:**
```bash
# Monitor webhook gateway
aws logs tail /aws/lambda/prod-revops-webhook-gateway --follow

# Monitor queue processor
aws logs tail /aws/lambda/revops-webhook --follow

# Track specific request by tracking ID
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-webhook' \
  --filter-pattern 'abc-123-def'
```

**Performance Monitoring:**
```bash
# Check outbound queue status
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible

# Monitor delivery success rates
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-webhook' \
  --filter-pattern 'Webhook processing completed successfully' \
  --start-time $(date -d '24 hours ago' +%s)000
```

### Agent Performance Tracking

**Individual Agent Monitoring:**
```bash
# Deal Analysis Agent performance
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'DealAnalysisAgent' \
  --start-time $(date -d '24 hours ago' +%s)000

# Lead Analysis Agent usage
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'LeadAnalysisAgent' \
  --start-time $(date -d '24 hours ago' +%s)000

# Data Agent SQL query tracking
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-firebolt-query' \
  --filter-pattern 'SQL execution' \
  --start-time $(date -d '1 hour ago' +%s)000
```

## Troubleshooting

### Common Issues and Solutions

**1. Agent Not Responding**
```bash
# Check agent status
aws bedrock-agent get-agent --agent-id PVWGKOWSOT --region us-east-1

# Verify IAM permissions
aws iam get-role --role-name prod-revops-manager-agent-wrapper-role

# Test agent directly
aws lambda invoke --function-name revops-manager-agent-wrapper \
  --payload '{"user_message":"test","correlation_id":"test-123"}' \
  /tmp/test_response.json
```

**2. Slow Response Times**
```bash
# Check queue processing delays
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-processing-queue \
  --attribute-names All

# Monitor agent timeout configurations
aws lambda get-function-configuration \
  --function-name revops-manager-agent-wrapper \
  --query '{Timeout:Timeout,MemorySize:MemorySize}'

# Check database connection performance
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-firebolt-query' \
  --filter-pattern 'Query execution time'
```

**3. Authentication Errors**
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check Slack token validity
aws secretsmanager get-secret-value \
  --secret-id revops-slack-bedrock-secrets \
  --query 'SecretString' --output text

# Test Bedrock agent access
aws bedrock-agent list-agents --region us-east-1
```

**4. Data Integration Issues**
```bash
# Test Firebolt connection
aws lambda invoke --function-name revops-firebolt-query \
  --payload '{"query":"SELECT 1 as test"}' \
  /tmp/firebolt_test.json

# Check Gong API status
aws lambda invoke --function-name revops-gong-retrieval \
  --payload '{"action":"test_connection"}' \
  /tmp/gong_test.json

# Verify knowledge base ingestion
aws bedrock-agent get-knowledge-base --knowledge-base-id F61WLOYZSW --region us-east-1
```

**5. Webhook Delivery Failures**
```bash
# Check webhook configuration
aws lambda get-function-configuration \
  --function-name revops-webhook \
  --query 'Environment.Variables'

# Monitor delivery attempts
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-webhook' \
  --filter-pattern 'Webhook delivery failed'

# Test webhook endpoint
curl -X POST [YOUR_WEBHOOK_URL] \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}'
```

### Error Patterns and Diagnostics

**Timeout Errors:**
- Check Lambda timeout configurations (15min max for complex analysis)
- Monitor SQS visibility timeouts
- Review agent processing times in CloudWatch

**Memory Issues:**
- Monitor Lambda memory usage in CloudWatch
- Check for large SQL result sets
- Review conversation export sizes

**Rate Limiting:**
- Monitor Bedrock API throttling
- Check concurrent Lambda executions
- Review SQS message processing rates

## Integration Endpoints

### Slack Integration
- **Endpoint**: `https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events`
- **Handler**: `revops-slack-bedrock-handler`
- **Processor**: `revops-slack-bedrock-processor`
- **Queue**: `revops-slack-bedrock-processing-queue`
- **CloudFormation Stack**: `revops-slack-bedrock-stack`

### API Integration
- **Endpoint**: `https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook`
- **Gateway**: `prod-revops-webhook-gateway`
- **Processor**: `revops-webhook`
- **Queue**: `prod-revops-webhook-outbound-queue`
- **CloudFormation Stack**: `revops-webhook-gateway-stack`

## Project Structure

```
revops_ai_framework/
├── agents/                     # AI agent definitions
│   ├── manager_agent/          # Main router and coordinator
│   ├── deal_analysis_agent/    # MEDDPICC deal assessment
│   ├── lead_analysis_agent/    # ICP scoring and qualification
│   ├── data_agent/             # SQL queries and analytics
│   ├── web_search_agent/       # External research
│   └── execution_agent/        # Actions and integrations
├── integrations/               # Input channels
│   ├── slack-bedrock-gateway/  # Slack integration
│   └── webhook-gateway/        # API integration
├── tools/                      # Supporting Lambda functions
│   ├── firebolt/               # Data warehouse integration
│   ├── gong/                   # Conversation intelligence
│   ├── web_search/             # External intelligence
│   └── webhook/                # Action execution
├── knowledge_base/             # AI knowledge management
├── deployment/                 # Infrastructure and deployment
└── monitoring/                 # Conversation tracking and exports
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
python3 deploy.py --agent lead_analysis
```

### Key Resources
- **AWS Profile**: `FireboltSystemAdministrator-740202120544`
- **Region**: `us-east-1`
- **Knowledge Base**: `F61WLOYZSW`
- **S3 Bucket**: `revops-ai-framework-kb-740202120544`
- **Manager Agent**: `PVWGKOWSOT`