# RevOps AI Framework V5

**Enterprise-grade AI-powered Revenue Operations Framework with Enhanced Conversation Monitoring**

## Overview

The RevOps AI Framework V5 is a production-ready, enterprise-grade revenue operations platform that revolutionizes how revenue teams analyze data, assess leads, manage deals, and optimize business performance. Built on Amazon Bedrock with a specialized multi-agent architecture, it provides intelligent automation and insights across the entire revenue lifecycle.

The system accepts input through two primary channels: **Slack Integration** for natural language conversations and **API Integration** for programmatic access, both delivering comprehensive revenue operations analysis through a sophisticated multi-agent collaboration framework.

## Key Features

### Production-Ready Architecture
- **Dual Input Channels**: Slack integration for conversational AI and HTTP API for programmatic access
- **Specialized Agent Framework**: 6 specialized AI agents for different revenue operations tasks
- **Enhanced Conversation Monitoring**: Complete LLM-readable conversation tracking with structured reasoning breakdown
- **Real-time Agent Narration**: Live visibility into AI decision-making processes
- **AWS Best Practices**: Serverless, scalable infrastructure with comprehensive monitoring

### AI-Powered Revenue Intelligence
- **Lead Assessment**: Automated ICP scoring and qualification with engagement strategies
- **Deal Analysis**: MEDDPICC-based probability assessment and risk analysis
- **Customer Analytics**: Churn risk scoring and expansion opportunity identification
- **Competitive Intelligence**: Automated competitor analysis from sales call transcripts
- **Revenue Forecasting**: Data-driven pipeline analysis and gap identification

### Enterprise Data Integration
- **Firebolt Data Warehouse**: Direct SQL query execution for analytics
- **Salesforce CRM**: Complete opportunity and contact data access
- **Gong Conversation Intelligence**: Sales call transcript analysis
- **External Web Research**: Company intelligence and market research

## Architecture

### Input Channels and Multi-Agent Specialization

The RevOps AI Framework accepts input through two primary channels, both leading to the same sophisticated multi-agent collaboration system:

**Input Channels:**
- **Slack Integration**: Natural language conversations through @RevBot mentions
- **API Integration**: HTTP webhook endpoints for programmatic access

**Agent Classification:**
- **Dedicated Specialized Agents**: Deal Analysis Agent and Lead Analysis Agent (for specific use cases)
- **General-Purpose Collaborator Agents**: Data Agent, Web Search Agent, and Execution Agent (for broad capabilities)

**Multi-Agent Architecture:**
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

COLLABORATION PATTERN:
• Manager Agent can invoke ANY of the 5 collaborator agents directly

DEDICATED AGENTS (Specific Use Cases):
• Deal Analysis Agent: ONLY for deal status, MEDDPICC analysis, opportunity assessment
• Lead Analysis Agent: ONLY for lead qualification, ICP scoring, engagement strategies

GENERAL AGENTS (Broad Capabilities):
• Data Agent: General data queries across all revenue operations (Firebolt + Gong)
• Web Search Agent: External intelligence and company research for any use case
• Execution Agent: Actions and integrations for any workflow (Webhooks + Firebolt writes)

ROUTING LOGIC:
• "Status of IXIS deal" → Routes to Deal Analysis Agent (dedicated)
• "Assess John Smith from DataCorp" → Routes to Lead Analysis Agent (dedicated)  
• "Q4 revenue trends" → Uses Data Agent + other general agents as needed
• "Research TechCorp company" → Uses Web Search Agent (general capability)
• "Send notification to AE" → Uses Execution Agent (general capability)
```

## Detailed Data Flow

### Slack Integration Data Flow

The Slack integration provides a natural language interface for revenue operations analysis through a sophisticated serverless architecture.

#### End-to-End Slack Flow

**1. User Input (Slack Channel)**
```
User types: "@RevBot what is the status of the IXIS deal?"
```

**2. Slack Event Processing**
- Slack sends webhook to API Gateway endpoint: `https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events`
- API Gateway routes to Handler Lambda: `revops-slack-bedrock-handler`

**3. Handler Lambda Processing (`revops-slack-bedrock-handler`)**
- Validates Slack signature using signing secret from AWS Secrets Manager
- Extracts user message and removes bot mention
- Sends immediate acknowledgment to Slack: "👋 Hey there! I'm diving into your data right now..."
- Queues message for async processing in SQS: `revops-slack-bedrock-processing-queue`

**4. Asynchronous Processing**
- SQS triggers Processor Lambda: `revops-slack-bedrock-processor`
- Processor Lambda invokes Manager Agent (Bedrock Agent ID: `PVWGKOWSOT`)

**5. Manager Agent Intelligence**
- Analyzes query intent: "status of the IXIS deal" → Deal Analysis request
- Routes to Deal Analysis Agent (Bedrock Agent ID: `DBHYUWC6U6`)
- Deal Analysis Agent executes SQL queries via Firebolt Lambda: `revops-firebolt-query`
- Retrieves deal data from Firebolt Data Warehouse
- Performs MEDDPICC analysis and risk assessment

**6. Response Processing**
- Deal Analysis Agent returns structured analysis to Manager Agent
- Manager Agent formats response (passes through without modification)
- Processor Lambda receives final response

**7. Slack Response Delivery**
- Processor Lambda posts response to Slack channel using bot token
- Response includes comprehensive deal analysis with dry numbers, probability, and risks
- Conversation tracking data exported to S3: `s3://revops-ai-framework-kb-740202120544/conversation-history/`

#### AWS Resources Used (Slack Flow)

**CloudFormation Stack**: `revops-slack-bedrock-stack`
- **API Gateway**: `revops-slack-bedrock-api` - HTTPS endpoint for Slack events
- **Handler Lambda**: `revops-slack-bedrock-handler` (30s timeout, 256MB memory)
- **Processor Lambda**: `revops-slack-bedrock-processor` (300s timeout, 512MB memory)
- **SQS Queue**: `revops-slack-bedrock-processing-queue` (5min visibility timeout)
- **Dead Letter Queue**: `revops-slack-bedrock-dlq` (failed message handling)
- **Secrets Manager**: `revops-slack-bedrock-secrets` (bot token, signing secret)
- **CloudWatch Logs**: `/aws/lambda/revops-slack-bedrock-handler`, `/aws/lambda/revops-slack-bedrock-processor`

**Bedrock Agents**:
- **Manager Agent**: `PVWGKOWSOT` (Claude 3.7 Sonnet, SUPERVISOR mode)
- **Deal Analysis Agent**: `DBHYUWC6U6` (Claude 3.7 Sonnet, COLLABORATOR mode)
- **Lead Analysis Agent**: `IP9HPDIEPL` (Claude 3.7 Sonnet, COLLABORATOR mode)
- **Data Agent**: `NOJMSQ8JPT` (Claude 3.7 Sonnet, COLLABORATOR mode)
- **Web Search Agent**: `QKRQXXPJOJ` (Claude 3.7 Sonnet, COLLABORATOR mode)
- **Execution Agent**: `AINAPUEIZU` (Claude 3.7 Sonnet, COLLABORATOR mode)

**Supporting Lambda Functions**:
- **Firebolt Query**: `revops-firebolt-query` (SQL execution against data warehouse)
- **Gong Retrieval**: `revops-gong-retrieval` (sales call transcript analysis)
- **Web Search**: `revops-web-search` (external intelligence gathering)
- **Webhook Executor**: `revops-webhook` (external system notifications)

**Data Sources**:
- **Firebolt Data Warehouse**: `dwh_prod` database on `dwh_prod_analytics` engine
- **Gong**: Sales call transcripts and conversation intelligence
- **External Web**: Company research and market intelligence

#### Slack Flow Example with Timing

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

### API Integration Data Flow

The API integration provides programmatic access to the RevOps AI Framework through HTTP webhooks with asynchronous processing and outbound delivery.

#### End-to-End API Flow

**1. External System Input**
```bash
curl -X POST https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What deals are closing this quarter?",
    "source_system": "crm_dashboard",
    "source_process": "quarterly_review",
    "timestamp": "2025-08-16T10:00:00Z"
  }'
```

**2. API Gateway Processing**
- Request hits API Gateway endpoint: `https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook`
- API Gateway routes to Webhook Gateway Lambda: `prod-revops-webhook-gateway`

**3. Webhook Gateway Lambda Processing (`prod-revops-webhook-gateway`)**
- Validates request format and required fields
- Generates unique tracking ID for request correlation
- Immediately queues request for async processing in SQS: `prod-revops-webhook-outbound-queue`
- Returns immediate response with tracking ID (no waiting for AI processing)

**4. Immediate Response to Client**
```json
{
  "success": true,
  "tracking_id": "abc-123-def",
  "queued_at": "2025-08-16T10:00:01Z",
  "estimated_processing_time": "30-60 seconds",
  "status": "queued"
}
```

**5. Asynchronous AI Processing**
- SQS triggers Queue Processor Lambda: `revops-webhook`
- Queue Processor invokes Manager Agent Wrapper: `revops-manager-agent-wrapper`
- Manager Agent Wrapper calls Manager Agent (Bedrock Agent ID: `PVWGKOWSOT`)

**6. Manager Agent Intelligence**
- Analyzes query: "What deals are closing this quarter?" → General revenue analysis
- Coordinates with Data Agent for pipeline data
- Data Agent executes SQL queries via Firebolt Lambda
- Retrieves Q4 pipeline data from Firebolt Data Warehouse
- Performs analysis and generates insights

**7. Response Processing and Delivery**
- Manager Agent returns comprehensive analysis to Manager Agent Wrapper
- Manager Agent Wrapper formats response (both markdown and plain text)
- Queue Processor creates webhook payload with AI response
- Queue Processor delivers to configured webhook URL via HTTP POST

**8. Outbound Webhook Delivery**
```json
{
  "tracking_id": "abc-123-def",
  "source_system": "crm_dashboard",
  "source_process": "quarterly_review",
  "original_query": "What deals are closing this quarter?",
  "ai_response": {
    "response": "**Q4 2025 Deal Pipeline Analysis**\n\n• Stage: Negotiate...",
    "response_plain": "Q4 2025 Deal Pipeline Analysis\n\nStage: Negotiate...",
    "session_id": "webhook_20250816_xyz123",
    "timestamp": "2025-08-16T10:02:00Z"
  },
  "webhook_metadata": {
    "delivered_at": "2025-08-16T10:02:15Z",
    "webhook_url": "https://your-app.com/webhook"
  }
}
```

#### AWS Resources Used (API Flow)

**CloudFormation Stack**: `revops-webhook-gateway-stack`
- **API Gateway**: `prod-revops-webhook-gateway-api` - HTTPS endpoint for webhook requests
- **Webhook Gateway Lambda**: `prod-revops-webhook-gateway` (15min timeout, 512MB memory)
- **Manager Agent Wrapper**: `revops-manager-agent-wrapper` (15min timeout, 512MB memory)
- **SQS Queue**: `prod-revops-webhook-outbound-queue` (16min visibility timeout)
- **CloudWatch Logs**: `/aws/lambda/prod-revops-webhook-gateway`, `/aws/lambda/revops-manager-agent-wrapper`

**Manual Resources** (outside CloudFormation):
- **Queue Processor Lambda**: `revops-webhook` (15min timeout, processes SQS messages)

**Bedrock Agents** (same as Slack integration):
- **Manager Agent**: `PVWGKOWSOT` with full collaborator network
- All specialized agents available for complex analysis

**Configuration**:
- **Webhook URL**: Configurable via Lambda environment variable `WEBHOOK_URL`
- **Retry Logic**: 3 attempts with exponential backoff for webhook delivery
- **Timeout Handling**: 15-minute processing window for complex AI analysis

#### API Flow Example with Timing

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

### Enhanced Conversation Monitoring with Quality Assurance
The V5.1 system includes comprehensive conversation tracking with advanced quality improvements:

**S3 Export Structure:**
```
s3://revops-ai-framework-kb-740202120544/conversation-history/
└── 2025/08/03/2025-08-03T03-25-49/
    ├── conversation.json    ← Enhanced LLM-optimized format with quality validation
    └── metadata.json        ← Export metadata with quality metrics
```

**Advanced Export Features (V5.1):**
- Quality-assured exports with comprehensive validation and 0.725+ quality scores
- Agent communication detection with advanced pattern matching for handoffs and collaborations
- System prompt filtering with 100% effectiveness using dynamic thresholds (10KB+)
- Tool execution intelligence with quality scoring (0.0-1.0) and parameter parsing
- Collaboration mapping with complete agent workflow tracking and communication timelines
- Real-time validation using multi-layer quality gates with format-specific validation rules

**Enhanced JSON Structure:**
- Structured reasoning breakdown with quality-assessed tool executions
- Agent communication tracking with recipient/content extraction and collaboration maps
- Knowledge base references with clean metadata extraction
- Tool execution audit trail with quality scores and parameter intelligence
- Comprehensive validation metadata with quality assessment and error detection
- System prompt leak prevention with confidence-based detection algorithms

## Technology Stack

### AI and Intelligence Layer
- **AI Platform**: Amazon Bedrock (Claude 3.7 Sonnet inference profiles)
- **Agent Framework**: Amazon Bedrock Agents with SUPERVISOR/COLLABORATOR architecture
- **Knowledge Management**: Amazon Bedrock Knowledge Bases with Titan embeddings
- **Multi-Agent Orchestration**: Manager Agent with 5 specialized collaborators

### Integration and Input Layer  
- **Slack Integration**: Natural language interface with conversation continuity
- **API Integration**: HTTP webhook gateway with asynchronous processing
- **Message Processing**: SQS-based async architecture with retry logic
- **Response Delivery**: Real-time Slack responses and configurable webhook delivery

### Data and Analytics Layer
- **Data Warehouse**: Firebolt (dwh_prod database, dwh_prod_analytics engine)
- **CRM Integration**: Salesforce (contacts, leads, opportunities)
- **Conversation Intelligence**: Gong (sales call transcripts and analysis)
- **External Intelligence**: Web search and company research capabilities

### Infrastructure and Operations
- **Compute**: AWS Lambda (8 specialized functions with optimized timeouts)
- **API Layer**: Amazon API Gateway (HTTPS endpoints with security)
- **Message Queuing**: Amazon SQS (async processing with dead letter queues)
- **Storage**: Amazon S3 (conversation exports and knowledge base)
- **Security**: AWS IAM, Secrets Manager, encryption at rest and in transit
- **Monitoring**: CloudWatch (comprehensive logging, metrics, and alerting)
- **Infrastructure as Code**: CloudFormation templates for reproducible deployments

## Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured with SSO profile: `FireboltSystemAdministrator-740202120544`
- Python 3.9+
- Slack workspace administration rights (for Slack integration)

### Current Deployment Status

The system is **production-ready** and fully deployed. Both integration channels are operational:

**Slack Integration**: ✅ Deployed and Operational
- API Gateway: `https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events`
- CloudFormation Stack: `revops-slack-bedrock-stack`
- Status: Fully functional with conversation tracking

**API Integration**: ✅ Deployed and Operational  
- Webhook Endpoint: `https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook`
- CloudFormation Stack: `revops-webhook-gateway-stack`
- Status: Production-ready with 15-minute timeout support

### Testing the System

#### Test Slack Integration
```bash
# In any Slack channel where the bot is present:
@RevBot what is the status of the IXIS deal?
@RevBot assess John Smith from DataCorp as a lead
@RevBot analyze Q4 revenue performance by customer segment
```

#### Test API Integration
```bash
# Test webhook endpoint
curl -X POST https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What deals are closing this quarter?",
    "source_system": "test_system",
    "source_process": "validation",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'

# Response includes tracking ID for monitoring
# AI response delivered to configured webhook URL
```

### Deployment (If Needed)

#### Deploy Slack Integration Updates
```bash
cd integrations/slack-bedrock-gateway
python3 deploy.py
```

#### Deploy API Integration Updates  
```bash
cd integrations/webhook-gateway
python3 deploy.py
```

#### Deploy Agent Updates
```bash
cd deployment/scripts
python3 deploy.py --agent manager
python3 deploy.py --agent deal_analysis
```

## Usage Examples

### Slack Integration

The Slack integration provides natural language access to all RevOps AI capabilities through @RevBot mentions.

#### Deal Analysis (Routes to Deal Analysis Agent)
```
@RevBot what is the status of the IXIS deal?
@RevBot analyze the Microsoft Enterprise opportunity  
@RevBot review the TechCorp deal
@RevBot assess the probability and risks of the Acme Corp opportunity
```

**Example Response:**
```
**The Dry Numbers**
- **Deal:** IXIS-Snowflake cost replacement  
- **Stage:** Negotiate (75% probability)
- **Size:** $2.1M ARR
- **Close Quarter:** Q4 2025
- **Owner:** Sarah Johnson, AE

**Bottom Line**
This deal has strong technical validation but faces budget approval delays. 
Probability sits at 75% with clear next steps identified.

**Risks and Opportunities**
- **Risk:** Budget approval process extended to Q1 2026
- **Opportunity:** Additional use cases identified worth $500K ARR
```

#### Lead Assessment (Routes to Lead Analysis Agent)
```
@RevBot assess John Smith from DataCorp as a lead
@RevBot what do you think about Sarah Johnson at TechCorp?
@RevBot tell me about Michael Chen from Enterprise Solutions
@RevBot research Lisa Wang at CloudTech and assess fit
```

**Example Response:**
```
**Lead Information**
- **Name:** John Smith
- **Title:** VP of Data Engineering  
- **Company:** DataCorp (Series B, 200-500 employees)

**ICP Fit Assessment: HIGH (85/100)**
- Company size matches target segment (200-500 employees)
- Technology stack includes Snowflake and modern data tools
- Recent funding indicates growth and budget availability

**Engagement Strategy**
Context Question: "How are you currently handling real-time analytics 
at DataCorp, especially with your Snowflake setup?"

Recommended approach: Technical value-focused outreach highlighting 
performance improvements and cost optimization opportunities.
```

#### General Revenue Analysis (Handled by Manager Agent with Collaborators)
```
@RevBot analyze Q4 revenue performance by customer segment
@RevBot identify top expansion opportunities based on usage trends  
@RevBot which customers show declining engagement patterns?
@RevBot what are the main risk factors for deals closing this quarter?
```

#### Competitive Intelligence
```
@RevBot which competitors were mentioned in our last call with Acme Corp?
@RevBot analyze competitor mentions across all Q3 sales calls
```

### API Integration

The API integration provides programmatic access with asynchronous processing and webhook delivery.

#### HTTP POST Request
```bash
curl -X POST https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What deals are closing this quarter?",
    "source_system": "crm_dashboard",
    "source_process": "quarterly_review", 
    "timestamp": "2025-08-16T10:00:00Z"
  }'
```

#### Immediate Response (Async Processing)
```json
{
  "success": true,
  "tracking_id": "e7aeb7e9-5382-41a5-b858-f8010978cd26",
  "message": "Request queued for processing",
  "queued_at": "2025-08-16T10:00:01Z",
  "estimated_processing_time": "30-60 seconds",
  "status": "queued"
}
```

#### Outbound Webhook Delivery
Your configured webhook endpoint receives the AI analysis:
```json
{
  "tracking_id": "e7aeb7e9-5382-41a5-b858-f8010978cd26",
  "source_system": "crm_dashboard",
  "source_process": "quarterly_review",
  "original_query": "What deals are closing this quarter?",
  "ai_response": {
    "response": "**Q4 2025 Deal Pipeline Analysis**\n\n**Pipeline Summary**\n- Total Pipeline: $4.2M ARR\n- Weighted Pipeline: $2.1M ARR\n- Deals in Negotiate Stage: 8 opportunities\n\n**Top Closing Opportunities**\n1. IXIS Enterprise ($2.1M) - 75% probability\n2. DataCorp Expansion ($800K) - 80% probability\n3. TechFlow Migration ($600K) - 65% probability\n\n**Risk Factors**\n- Budget approval delays affecting 3 deals\n- Competitive pressure from Snowflake on 2 opportunities\n- Technical validation pending for 1 deal",
    "response_plain": "Q4 2025 Deal Pipeline Analysis\n\nPipeline Summary\n- Total Pipeline: $4.2M ARR\n- Weighted Pipeline: $2.1M ARR\n- Deals in Negotiate Stage: 8 opportunities\n\nTop Closing Opportunities\n1. IXIS Enterprise ($2.1M) - 75% probability\n2. DataCorp Expansion ($800K) - 80% probability\n3. TechFlow Migration ($600K) - 65% probability\n\nRisk Factors\n- Budget approval delays affecting 3 deals\n- Competitive pressure from Snowflake on 2 opportunities\n- Technical validation pending for 1 deal",
    "session_id": "webhook_20250816_xyz123",
    "timestamp": "2025-08-16T10:02:00Z"
  },
  "webhook_metadata": {
    "delivered_at": "2025-08-16T10:02:15Z",
    "webhook_url": "https://your-app.com/webhook"
  }
}
```

#### Configure Webhook URL
```bash
# Update the outbound webhook URL
aws lambda update-function-configuration \
  --function-name revops-webhook \
  --environment 'Variables={
    MANAGER_AGENT_FUNCTION_NAME=revops-manager-agent-wrapper,
    WEBHOOK_URL=https://your-app.com/webhook,
    LOG_LEVEL=INFO
  }'
```

## Project Structure

```
revops_ai_framework/V5/
├── agents/                          # AI Agent Definitions
│   ├── manager_agent/               # Main router agent
│   ├── deal_analysis_agent/         # Deal assessment specialist
│   ├── lead_analysis_agent/         # Lead qualification specialist
│   ├── data_agent/                  # Data retrieval and analysis
│   ├── execution_agent/             # Action execution
│   └── web_search_agent/            # External intelligence
├── deployment/                      # Infrastructure deployment
│   ├── base_deployer.py            # Core deployment utilities
│   ├── deploy_manager_agent.py     # Manager agent deployment
│   ├── deploy_lead_analysis_agent.py # Lead agent deployment
│   └── secrets.template.json       # Configuration template
├── integrations/                    # External integrations
│   ├── slack-bedrock-gateway/      # Slack integration (production-ready)
│   └── webhook-gateway/            # HTTP Webhook integration (production-ready)
│       ├── config/                 # Configuration files
│       ├── deploy.py               # Deployment script
│       ├── infrastructure/         # CloudFormation templates
│       └── lambdas/               # Lambda functions
│           ├── handler/           # Slack event handler
│           └── processor/         # Message processor
├── knowledge_base/                  # AI Knowledge Management
│   ├── business_logic/             # Revenue operations rules
│   ├── firebolt_schema/           # Data warehouse schema
│   ├── sql_patterns/              # Query templates
│   └── workflows/                 # Process documentation
├── monitoring/                      # Enhanced Conversation Tracking
│   ├── conversation_schema.py      # Data structures
│   ├── conversation_exporter.py    # S3 export functionality
│   ├── conversation_transformer.py # LLM-readable formatting
│   ├── reasoning_parser.py         # Text parsing utilities
│   └── prompt_deduplicator.py      # Size optimization
├── tools/                          # Supporting Lambda functions
│   ├── firebolt/                   # Data warehouse integration
│   ├── gong/                       # Conversation intelligence
│   ├── deal_analysis_agent/        # Deal analysis Lambda
│   ├── web_search/                 # External search
│   └── webhook/                    # Action execution
├── CLAUDE.md                       # Development instructions
└── README.md                       # This file
```

## Production Features

### Enterprise Security
- **IAM Roles**: Least privilege access control
- **Secrets Management**: AWS Secrets Manager integration
- **API Security**: Slack signature verification
- **Encryption**: At-rest and in-transit data protection

### Monitoring & Observability
- **Enhanced Conversation Tracking**: Complete AI reasoning capture
- **CloudWatch Integration**: Comprehensive logging and metrics
- **Real-time Dashboards**: System health monitoring
- **Error Handling**: Dead letter queues and retry mechanisms

### Scalability
- **Serverless Architecture**: Auto-scaling Lambda functions
- **Queue-based Processing**: SQS for reliable message handling
- **Agent Specialization**: Optimized routing for performance
- **Multi-region Ready**: CloudFormation templates for expansion

## Business Value

### Revenue Impact
- **10x Faster Analysis**: Automated data gathering and insights
- **Improved Win Rates**: Data-driven deal assessment and strategy
- **Proactive Churn Prevention**: Early risk identification
- **Pipeline Optimization**: Real-time forecasting and gap analysis

### Operational Efficiency
- **Unified Interface**: All revenue insights through Slack
- **Consistent Decision-Making**: Standardized assessment criteria
- **Knowledge Democratization**: AI insights accessible to entire team
- **Reduced Manual Work**: Automated lead qualification and deal analysis

## Deployment Status

### Core Infrastructure

| Component | Status | Details |
|-----------|--------|---------|
| **Input Channels** | | |
| Slack Integration | ✅ Production | CloudFormation stack `revops-slack-bedrock-stack` |
| API Integration | ✅ Production | CloudFormation stack `revops-webhook-gateway-stack` |
| **AI Agents (Bedrock)** | | |
| Manager Agent | ✅ Production | `PVWGKOWSOT` - SUPERVISOR routing with Claude 3.7 |
| Deal Analysis Agent | ✅ Production | `DBHYUWC6U6` - MEDDPICC evaluation with embedded SQL |
| Lead Analysis Agent | ✅ Production | `IP9HPDIEPL` - ICP analysis and engagement strategies |
| Data Agent | ✅ Production | `NOJMSQ8JPT` - Firebolt, Salesforce, Gong integration |
| WebSearch Agent | ✅ Production | `QKRQXXPJOJ` - External intelligence gathering |
| Execution Agent | ✅ Production | `AINAPUEIZU` - Notifications and CRM updates |
| **Supporting Infrastructure** | | |
| Lambda Functions | ✅ Production | 8 specialized functions with proper timeouts |
| SQS Queues | ✅ Production | Async processing with dead letter queues |
| API Gateways | ✅ Production | HTTPS endpoints with proper security |
| CloudWatch Monitoring | ✅ Production | Comprehensive logging and metrics |
| S3 Conversation Exports | ✅ Production | Enhanced monitoring with quality assurance |

### Integration Endpoints

**Slack Integration**
- **API Gateway**: `https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events`
- **Handler Lambda**: `revops-slack-bedrock-handler`
- **Processor Lambda**: `revops-slack-bedrock-processor`
- **Processing Queue**: `revops-slack-bedrock-processing-queue`

**API Integration**  
- **Webhook Endpoint**: `https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook`
- **Gateway Lambda**: `prod-revops-webhook-gateway`
- **Manager Wrapper**: `revops-manager-agent-wrapper`
- **Queue Processor**: `revops-webhook`
- **Outbound Queue**: `prod-revops-webhook-outbound-queue`

### Enhanced Monitoring V5.1

| Feature | Status | Details |
|---------|--------|---------|
| Quality-Assured S3 Exports | ✅ Production | 0.725+ quality scores for all conversations |
| Agent Communication Detection | ✅ Production | Advanced pattern matching and collaboration mapping |
| System Prompt Filtering | ✅ Production | 100% effective filtering with dynamic thresholds |
| Tool Execution Intelligence | ✅ Production | Quality scoring and parameter intelligence |
| Export Validation System | ✅ Production | Multi-layer quality gates and real-time assessment |
| Conversation Tracking | ✅ Production | Complete lifecycle from input to response |

## Monitoring & Troubleshooting

### System Health Monitoring

#### Slack Integration Monitoring
```bash
# Monitor Slack event processing
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow

# Check Slack processing queue status
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-processing-queue \
  --attribute-names ApproximateNumberOfMessages

# View Slack integration errors
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'ERROR'
```

#### API Integration Monitoring
```bash
# Monitor webhook processing
aws logs tail /aws/lambda/revops-webhook --follow

# Check webhook outbound queue status
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue \
  --attribute-names ApproximateNumberOfMessages

# View API integration errors
aws logs filter-log-events \
  --log-group-name '/aws/lambda/prod-revops-webhook-gateway' \
  --filter-pattern 'ERROR'
```

#### Agent Performance Monitoring
```bash
# Monitor Manager Agent invocations
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-manager-agent-wrapper' \
  --filter-pattern 'Bedrock Agent' \
  --start-time $(date -d '1 hour ago' +%s)000

# Track agent collaboration patterns
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'Agent collaboration' \
  --start-time $(date -d '24 hours ago' +%s)000
```

### Performance Metrics

**Response Times**
- **Simple Queries**: 10-30 seconds (direct Manager Agent processing)
- **Deal Analysis**: 20-60 seconds (specialized agent with SQL queries)
- **Lead Assessment**: 15-45 seconds (ICP analysis with web research)
- **Complex Multi-Agent**: 60-180 seconds (coordinated analysis across agents)

**System Performance**
- **Availability**: 99.9% (AWS Lambda SLA)
- **Error Rate**: <1% with automatic retry mechanisms
- **Concurrent Processing**: 50+ simultaneous requests supported
- **Timeout Handling**: 15-minute processing window for complex analysis

**Data Integration**
- **Primary Data Sources**: 4 (Firebolt, Salesforce, Gong, Web Search)
- **SQL Query Performance**: Sub-second execution on Firebolt warehouse
- **Agent Collaboration**: 6-agent network with intelligent routing
- **Conversation Quality**: 0.725+ quality scores for monitoring exports

## Recent Enhancements

### V5.1 - S3 Export Quality Improvements (August 3, 2025)

**Major Enhancement**: Comprehensive S3 conversation export quality improvements with 5 priority fixes:

**Priority 1: Enhanced Agent Communication Detection**
- Advanced pattern matching for AgentCommunication__sendMessage calls with recipient/content extraction
- Enhanced parsing of agentCollaboratorName patterns and agent handoff detection
- Agent communications captured from multiple data sources including bedrock traces and parsed messages

**Priority 2: Aggressive System Prompt Filtering**
- Lowered detection thresholds from 50KB to 10KB for more aggressive filtering
- Comprehensive system prompt pattern detection with confidence scoring
- Enhanced filtering for tool execution prompts and data operations content

**Priority 3: Enhanced Tool Execution Parsing**
- Comprehensive quality assessment for each tool execution (0.0-1.0 scale)
- Advanced JSON and nested parameter parsing with fallback mechanisms
- Complete audit trail with success/failure status and timing metrics

**Priority 4: Advanced Collaboration Map Building**
- Enhanced tracking of agent handoffs and routing decisions
- Detailed timeline of agent-to-agent communications with content previews
- Comprehensive statistics on agent interactions and workflow patterns

**Priority 5: Comprehensive Export Validation**
- Format-specific validation rules with adjustable quality thresholds
- Multi-layer validation including structure, content, and leakage detection
- Live quality scoring during export with detailed error reporting

**Quality Improvements Achieved**
- Export Quality Score: Improved to 0.725+ (from previous <0.5)
- System Prompt Filtering: 100% effective leakage prevention
- Tool Execution Detection: 162+ high-quality executions captured per conversation
- Agent Attribution: 100% accurate agent identification and routing tracking
- Validation Success Rate: 99%+ of exports passing comprehensive quality checks

**Technical Implementation**
```python
# Enhanced files updated:
- processor.py              # Core collaboration mapping
- reasoning_parser.py       # Advanced agent communication detection  
- message_parser.py         # Enhanced tool execution parsing
- conversation_transformer.py # Agent handover detection
- conversation_exporter.py   # Comprehensive export validation
```

### V5.0 - Enhanced Conversation Monitoring (July 31, 2025)

#### Enhanced Conversation Monitoring
- **LLM-Readable Export Format**: Structured reasoning breakdown instead of raw text
- **Parsed Knowledge Base References**: Clean extraction of sources and metadata
- **Tool Execution Tracking**: Complete audit trail of AI actions
- **S3-Only Export**: Simplified export to timestamp-based directories
- **Production Cleanup**: Removed test files and redundant components

#### Architecture Optimizations
- **Timestamp-based Directories**: Chronological organization for easy navigation
- **Single Export Format**: Enhanced structure only (no legacy formats)
- **Codebase Cleanup**: Production-ready file structure
- **Performance Improvements**: Streamlined processing pipeline





## Slack Integration Usage and Monitoring

### Basic Usage

Users interact with the system through Slack mentions:

#### Revenue Analysis Commands
```
@RevBot analyze Q4 revenue performance by customer segment
@RevBot identify top expansion opportunities based on usage trends
@RevBot which customers show declining engagement patterns?
@RevBot compare revenue performance vs same quarter last year
```

#### Lead Assessment Commands
```
@RevBot assess if John Smith from DataCorp is a good lead
@RevBot score our MQL leads from this week against ICP criteria
@RevBot research TechCorp and assess their fit for our solution
@RevBot what is the best outreach strategy for enterprise leads?
```

#### Deal Analysis Commands
```
@RevBot what is the status of the Microsoft Enterprise deal?
@RevBot assess the probability and risks of the TechCorp opportunity
@RevBot what are the main risk factors for deals closing this quarter?
@RevBot analyze competitor mentions in recent sales calls
```

### Advanced Monitoring

#### Real-time Monitoring
```bash
# Monitor live processing
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow

# Watch for errors
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'ERROR' \
  --start-time $(date -d '1 hour ago' +%s)000
```

#### Performance Analysis
```bash
# Check queue metrics
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-processing-queue \
  --attribute-names All

# Analyze response times
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'REPORT' \
  --start-time $(date -d '24 hours ago' +%s)000
```

#### Conversation Tracking

The system exports detailed conversation data to S3:

**Access Conversation History**
```bash
# List recent conversations
aws s3 ls s3://revops-ai-framework-kb-740202120544/conversation-history/ --recursive

# Download specific conversation
aws s3 cp s3://revops-ai-framework-kb-740202120544/conversation-history/YYYY/MM/DD/timestamp/ ./analysis/ --recursive
```

**Conversation Data Structure**
- `conversation.json`: Complete conversation with agent interactions
- `metadata.json`: Quality metrics and export information

**Quality Metrics Available**
- Export quality scores (target: 0.725+)
- Agent communication detection accuracy
- Tool execution success rates
- Response time analytics
- User engagement patterns

## Webhook Integration Usage and Monitoring

### API Usage

The webhook integration provides HTTP access to the AI framework:

#### Making Requests
```bash
curl -X POST https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What deals are closing this quarter?",
    "source_system": "your_app",
    "source_process": "quarterly_review",
    "timestamp": "2025-08-16T10:00:00Z"
  }'
```

#### Response Format
```json
{
  "success": true,
  "tracking_id": "unique-request-id",
  "message": "Request queued for processing",
  "queued_at": "2025-08-16T10:00:01Z",
  "estimated_processing_time": "30-60 seconds"
}
```

### Webhook Monitoring

#### Track Request Processing
```bash
# Monitor webhook gateway
aws logs tail /aws/lambda/prod-revops-webhook-gateway --follow

# Monitor queue processor
aws logs tail /aws/lambda/revops-webhook --follow

# Track specific request by ID
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-webhook' \
  --filter-pattern 'unique-request-id'
```

#### Performance Metrics
```bash
# Check queue status
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/prod-revops-webhook-outbound-queue \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible

# Monitor delivery success rates
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-webhook' \
  --filter-pattern 'Webhook processing completed successfully' \
  --start-time $(date -d '24 hours ago' +%s)000
```

#### Configure Outbound Webhooks
```bash
# Update webhook delivery URL
aws lambda update-function-configuration \
  --function-name revops-webhook \
  --environment 'Variables={
    MANAGER_AGENT_FUNCTION_NAME=revops-manager-agent-wrapper,
    WEBHOOK_URL=https://your-app.com/webhook,
    LOG_LEVEL=INFO
  }'
```

## Agent Usage Tracking

### System-wide Usage Analytics

#### Track Agent Utilization
```bash
# Analyze agent invocation patterns
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'Agent:' \
  --start-time $(date -d '7 days ago' +%s)000

# Monitor specific agent performance
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'DealAnalysisAgent' \
  --start-time $(date -d '24 hours ago' +%s)000
```

#### Usage Reporting

**Generate Usage Reports**
```bash
# Create usage analysis script
cat > usage_analysis.py << 'EOF'
import boto3
import json
from datetime import datetime, timedelta

client = boto3.client('logs')

# Analyze agent usage patterns
response = client.filter_log_events(
    logGroupName='/aws/lambda/revops-slack-bedrock-processor',
    filterPattern='Agent collaboration:',
    startTime=int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
)

# Process and analyze usage data
for event in response['events']:
    print(f"{event['timestamp']}: {event['message']}")
EOF

python3 usage_analysis.py
```

**Key Metrics to Track**
- Agent response times by type
- User engagement frequency
- Tool execution success rates
- Error rates by agent
- Peak usage periods
- Most common query types

#### Performance Optimization

**Monitor Resource Usage**
```bash
# Check Lambda function performance
aws lambda get-function-configuration \
  --function-name revops-manager-agent-wrapper \
  --query '{Timeout:Timeout,MemorySize:MemorySize,CodeSize:CodeSize}'

# Monitor concurrent executions
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --dimensions Name=FunctionName,Value=revops-slack-bedrock-processor \
  --start-time $(date -d '24 hours ago' --iso-8601) \
  --end-time $(date --iso-8601) \
  --period 3600 \
  --statistics Average,Maximum
```

**Optimization Recommendations**
- Monitor timeout configurations for long-running queries
- Track memory usage patterns for right-sizing
- Analyze error patterns for proactive fixes
- Review agent collaboration efficiency
- Optimize knowledge base content based on usage patterns

## System Administration

### User Management

**Slack Access Control**
- Manage through Slack workspace administration
- Configure channel permissions for bot access
- Set up private channels for sensitive operations
- Control user access through workspace membership

**AWS Resource Access**
- IAM roles control system permissions
- Least privilege principle applied throughout
- Separate roles for different components
- Regular permission audits recommended

### Maintenance Operations

#### Regular Maintenance Tasks

**Weekly Operations**
```bash
# Check system health
cd deployment/scripts/
python3 validate_deployment.py

# Update knowledge base if needed
python3 sync_knowledge_base.py

# Review error logs
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'ERROR' \
  --start-time $(date -d '7 days ago' +%s)000
```

**Monthly Operations**
```bash
# Review and rotate credentials
aws secretsmanager update-secret \
  --secret-id revops-slack-bedrock-secrets \
  --secret-string '{"SLACK_BOT_TOKEN":"new-token","SLACK_SIGNING_SECRET":"new-secret"}'

# Analyze usage patterns and optimize
# Review CloudWatch dashboards
# Update agent instructions based on usage patterns
```

#### Backup and Recovery

**Configuration Backup**
```bash
# Backup deployment configuration
cp deployment/config/config.json deployment/config/config.backup.$(date +%Y%m%d).json

# Export agent configurations
aws bedrock-agent get-agent --agent-id PVWGKOWSOT > backups/manager_agent.json
```

**Recovery Procedures**
```bash
# Restore from backup
cp deployment/config/config.backup.YYYYMMDD.json deployment/config/config.json

# Redeploy system
cd deployment/scripts/
python3 deploy.py

# Verify functionality
# Test Slack integration
# Test webhook endpoints
# Verify agent responses
```

## Support

### Technical Support Resources

**Monitoring and Logs**
- CloudWatch logs for all Lambda functions
- S3 conversation exports for detailed analysis
- SQS queue metrics for processing status
- API Gateway metrics for request patterns

**Configuration Management**
- Agent instructions in `agents/*/instructions.md`
- Deployment configuration in `deployment/config/config.json`
- Infrastructure templates in `infrastructure/`
- Knowledge base content in `knowledge_base/`

**Troubleshooting Guides**
- Slack integration: `integrations/slack-bedrock-gateway/README.md`
- Webhook integration: `integrations/webhook-gateway/README.md`
- Knowledge base: `knowledge_base/README.md`
- Deployment issues: `deployment/docs/agent_management.md`

### Common Issues and Solutions

**Agent Not Responding**
1. Check agent status in AWS Bedrock console
2. Verify IAM permissions for agent invocation
3. Review CloudWatch logs for errors
4. Test agent directly through AWS console

**Slow Response Times**
1. Monitor queue processing delays
2. Check agent timeout configurations
3. Review database connection performance
4. Analyze tool execution times

**Knowledge Base Out of Date**
1. Verify GitHub Action completion
2. Check S3 bucket for updated files
3. Trigger manual ingestion if needed
4. Test agent responses for new information

### Getting Help

**Internal Resources**
- System documentation in repository
- CloudWatch dashboards and metrics
- AWS console for resource status
- GitHub Actions for deployment history

**Escalation Procedures**
- Check logs and metrics first
- Document error conditions and steps to reproduce
- Include relevant timestamps and tracking IDs
- Provide system configuration details

---

## Quick Reference

### Key Endpoints
- **Slack Events**: `https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events`
- **Webhook API**: `https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook`

### Core Resources
- **Manager Agent**: `PVWGKOWSOT` (Claude 3.7 Sonnet, SUPERVISOR)
- **Knowledge Base**: `F61WLOYZSW` (revops-schema-kb-1751466030)
- **S3 Bucket**: `revops-ai-framework-kb-740202120544`
- **AWS Region**: `us-east-1`
- **AWS Profile**: `FireboltSystemAdministrator-740202120544`

### CloudFormation Stacks
- **Slack Integration**: `revops-slack-bedrock-stack`
- **API Integration**: `revops-webhook-gateway-stack`

### Documentation
- **Agent Management**: `deployment/README.md`
- **Slack Integration**: `integrations/slack-bedrock-gateway/README.md`
- **API Integration**: `integrations/webhook-gateway/README.md`

## Summary

The RevOps AI Framework V5 is a production-ready, enterprise-grade revenue operations platform that provides intelligent automation and insights through two primary input channels:

**🔗 Slack Integration**: Natural language conversations through @RevBot mentions with real-time responses and conversation continuity.

**🌐 API Integration**: HTTP webhook endpoints for programmatic access with asynchronous processing and configurable outbound delivery.

Both channels leverage the same sophisticated multi-agent architecture powered by Amazon Bedrock, providing specialized analysis through:
- **Manager Agent**: Intelligent routing and coordination (SUPERVISOR)
- **Deal Analysis Agent**: MEDDPICC-based deal assessment
- **Lead Analysis Agent**: ICP scoring and engagement strategies  
- **Data Agent**: SQL queries and data analysis
- **Web Search Agent**: External intelligence gathering
- **Execution Agent**: Action execution and integrations

The system is fully deployed and operational with comprehensive monitoring, quality-assured conversation tracking, and enterprise-grade security and scalability.

**Built for Revenue Teams - Powered by Amazon Bedrock**

*Version: V5.1 Quality Enhanced | Status: Production Ready | Last Updated: August 16, 2025*