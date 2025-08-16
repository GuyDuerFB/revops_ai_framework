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

### Slack Integration - Complete End-to-End Flow

**Example Query: "@RevBot what is the status of the IXIS deal?"**

#### Phase 1: Message Reception and Authentication (0-2 seconds)
```
00:00 - USER ACTION
├─ User types: "@RevBot what is the status of the IXIS deal?" in Slack channel
├─ Message contains: user_id, channel_id, timestamp, text, team_id
└─ Slack Platform sends webhook POST to AWS

00:01 - SLACK WEBHOOK → AWS API GATEWAY
├─ Component: API Gateway (revops-slack-bedrock-api)
├─ Endpoint: https://s4tdiv7qrf.execute-api.us-east-1.amazonaws.com/prod/slack-events
├─ Function: HTTP endpoint, SSL termination, request routing
├─ Input: Slack webhook payload (JSON)
├─ Processing: Route /slack-events POST to Handler Lambda
└─ Output: Invokes Handler Lambda with Slack event

00:01 - API GATEWAY → HANDLER LAMBDA
├─ Component: revops-slack-bedrock-handler
├─ Runtime: Python 3.11, 256MB memory, 30s timeout
├─ Function: Slack signature verification, immediate response, queue message
├─ Input: Slack event payload with headers
├─ Processing Steps:
│  ├─ 1. Verify Slack signature using signing secret from AWS Secrets Manager
│  ├─ 2. Extract user message and remove @RevBot mention
│  ├─ 3. Generate correlation ID for tracking
│  ├─ 4. Validate event type (app_mention)
│  └─ 5. Prepare message for async processing
└─ Output: Two parallel actions (response + queue)
```

#### Phase 2: Immediate Response and Async Queuing (2-3 seconds)
```
00:02 - HANDLER LAMBDA → SLACK RESPONSE
├─ Component: Slack Web API
├─ Function: Immediate acknowledgment to user
├─ Method: POST to https://slack.com/api/chat.postMessage
├─ Authentication: Bot token from AWS Secrets Manager
├─ Payload: {"channel": "C123", "text": "👋 Hey there! I'm diving..."}
└─ Result: User sees immediate response in Slack

00:02 - HANDLER LAMBDA → SQS QUEUE
├─ Component: revops-slack-bedrock-processing-queue
├─ Function: Async message processing queue
├─ Queue Settings:
│  ├─ Visibility timeout: 300 seconds (5 minutes)
│  ├─ Message retention: 14 days
│  ├─ Dead letter queue: revops-slack-bedrock-dlq
│  └─ Max receive count: 3
├─ Message Payload:
│  ├─ correlation_id: "550e8400-e29b-41d4-a716-446655440000"
│  ├─ user_message: "what is the status of the IXIS deal?"
│  ├─ slack_channel: "C1234567890"
│  ├─ slack_user: "U0987654321"
│  ├─ timestamp: "2025-08-16T16:30:00Z"
│  └─ team_id: "T1234567890"
└─ Trigger: SQS event source mapping invokes Processor Lambda
```

#### Phase 3: Async Processing and AI Analysis (3-25 seconds)
```
00:03 - SQS → PROCESSOR LAMBDA
├─ Component: revops-slack-bedrock-processor
├─ Runtime: Python 3.11, 512MB memory, 300s timeout
├─ Function: Main AI processing orchestration
├─ Event Source: SQS event source mapping (batch size: 1)
├─ Input: SQS message with user query
├─ Processing Steps:
│  ├─ 1. Parse SQS message and extract correlation_id
│  ├─ 2. Initialize conversation tracking
│  ├─ 3. Validate message format and user permissions
│  ├─ 4. Prepare payload for Manager Agent
│  └─ 5. Invoke Manager Agent via Bedrock Agent Runtime
└─ Output: Manager Agent invocation

00:05 - PROCESSOR LAMBDA → MANAGER AGENT (BEDROCK)
├─ Component: Amazon Bedrock Agent (PVWGKOWSOT)
├─ Model: Claude 3.7 Sonnet with inference profile
├─ Function: Intelligent routing and workflow coordination
├─ Agent Type: SUPERVISOR
├─ Knowledge Base: F61WLOYZSW (Firebolt schema, business logic)
├─ Input: {"user_message": "what is the status of the IXIS deal?"}
├─ Processing:
│  ├─ 1. Analyze query intent: "deal status" → Deal Analysis Agent needed
│  ├─ 2. Extract deal name: "IXIS"
│  ├─ 3. Determine required data: opportunity details, stage, probability
│  ├─ 4. Route to Deal Analysis Agent with context
│  └─ 5. Prepare agent collaboration instructions
└─ Output: Deal Analysis Agent invocation with routing context

00:07 - MANAGER AGENT → DEAL ANALYSIS AGENT (BEDROCK)
├─ Component: Amazon Bedrock Agent (DBHYUWC6U6)
├─ Model: Claude 3.7 Sonnet with inference profile
├─ Function: MEDDPICC analysis and deal assessment
├─ Agent Type: COLLABORATOR (dedicated specialist)
├─ Tools Available:
│  ├─ firebolt_sql_query: Direct SQL execution
│  ├─ knowledge_base_retrieval: Business logic and schema
│  └─ agent_collaboration: Communication with other agents
├─ Input: {"deal_name": "IXIS", "analysis_type": "status_assessment"}
├─ Processing:
│  ├─ 1. Query knowledge base for IXIS deal information
│  ├─ 2. Determine required SQL queries for comprehensive analysis
│  ├─ 3. Execute Firebolt queries via Lambda tool
│  └─ 4. Prepare MEDDPICC framework analysis
└─ Output: SQL query execution via Firebolt Lambda

00:10 - DEAL ANALYSIS AGENT → FIREBOLT LAMBDA
├─ Component: revops-firebolt-query
├─ Runtime: Python 3.11, 512MB memory, 300s timeout
├─ Function: SQL query execution against Firebolt data warehouse
├─ Database: dwh_prod.opportunities, dwh_prod.contacts, dwh_prod.activities
├─ Connection: Firebolt engine dwh_prod_analytics
├─ Input SQL Query:
│  ```sql
│  SELECT 
│    o.opportunity_name,
│    o.stage_name,
│    o.probability,
│    o.amount,
│    o.close_date,
│    o.owner_name,
│    o.created_date,
│    o.last_activity_date,
│    c.name as account_name,
│    c.industry,
│    c.employee_count
│  FROM opportunities o
│  LEFT JOIN accounts c ON o.account_id = c.id
│  WHERE o.opportunity_name ILIKE '%IXIS%'
│  ORDER BY o.last_modified_date DESC
│  ```
├─ Processing:
│  ├─ 1. Establish secure connection to Firebolt
│  ├─ 2. Execute SQL query with parameterization
│  ├─ 3. Process result set (rows, columns, data types)
│  ├─ 4. Format response for AI agent consumption
│  └─ 5. Log query execution time and row count
└─ Output: Structured deal data returned to Deal Analysis Agent
```

#### Phase 4: Data Analysis and Response Generation (15-25 seconds)
```
00:15 - FIREBOLT LAMBDA → DEAL ANALYSIS AGENT
├─ Data Returned:
│  ├─ opportunity_name: "IXIS-Snowflake Cost Replacement"
│  ├─ stage_name: "Negotiate"
│  ├─ probability: 75
│  ├─ amount: 2100000
│  ├─ close_date: "2025-12-31"
│  ├─ owner_name: "Sarah Johnson"
│  ├─ account_name: "IXIS Investment Management"
│  └─ last_activity_date: "2025-08-15"
├─ Processing: Deal Analysis Agent analyzes data
├─ MEDDPICC Analysis:
│  ├─ Metrics: Cost savings calculation
│  ├─ Economic Buyer: Budget approval status
│  ├─ Decision Criteria: Performance vs cost factors
│  ├─ Decision Process: Technical → Financial → Legal
│  ├─ Paper Process: Procurement requirements
│  ├─ Identify Pain: Current Snowflake cost issues
│  └─ Champion: Internal advocate strength
└─ Output: Comprehensive deal assessment

00:20 - DEAL ANALYSIS AGENT → GONG LAMBDA (if call data needed)
├─ Component: revops-gong-retrieval (conditional)
├─ Function: Retrieve sales call transcripts for deal context
├─ API: Gong REST API with OAuth authentication
├─ Query: Calls related to IXIS opportunity
├─ Processing:
│  ├─ 1. Search calls by opportunity ID or account name
│  ├─ 2. Extract recent call transcripts (last 30 days)
│  ├─ 3. Identify competitive mentions, objections, next steps
│  └─ 4. Return structured call intelligence
└─ Output: Call transcript analysis (if applicable)

00:22 - DEAL ANALYSIS AGENT → MANAGER AGENT
├─ Component: Agent collaboration via Bedrock
├─ Function: Return structured deal analysis
├─ Response Format:
│  ├─ deal_summary: Core deal metrics
│  ├─ meddpicc_analysis: Framework-based assessment
│  ├─ risk_factors: Identified challenges
│  ├─ next_steps: Recommended actions
│  ├─ confidence_score: Analysis reliability
│  └─ data_sources: Firebolt tables, Gong calls used
├─ Processing: Manager Agent receives and validates response
└─ Output: Final response preparation

00:24 - MANAGER AGENT → PROCESSOR LAMBDA
├─ Component: Bedrock Agent response handling
├─ Function: Format final response for Slack delivery
├─ Response Processing:
│  ├─ 1. Validate agent response completeness
│  ├─ 2. Format for Slack markdown rendering
│  ├─ 3. Add conversation tracking metadata
│  ├─ 4. Prepare S3 export data
│  └─ 5. Generate delivery payload
└─ Output: Formatted response ready for Slack
```

#### Phase 5: Response Delivery and Monitoring (25-28 seconds)
```
00:25 - PROCESSOR LAMBDA → SLACK API
├─ Component: Slack Web API
├─ Method: POST to https://slack.com/api/chat.postMessage
├─ Authentication: Bot token from AWS Secrets Manager
├─ Payload Structure:
│  ├─ channel: Original Slack channel ID
│  ├─ thread_ts: Reply in thread if applicable
│  ├─ text: Markdown-formatted deal analysis
│  ├─ blocks: Rich formatting for better UX
│  └─ unfurl_links: false
├─ Response Content:
│  ```
│  **Deal Status: IXIS-Snowflake Cost Replacement**
│  - Stage: Negotiate (75% probability)
│  - Size: $2.1M ARR
│  - Close Quarter: Q4 2025
│  - Owner: Sarah Johnson
│  
│  **MEDDPICC Analysis:**
│  - Metrics: Cost savings validated at $500K annually
│  - Economic Buyer: CFO engaged, budget approved
│  - Decision Criteria: Performance and cost reduction
│  - Decision Process: Technical validation → Budget → Legal
│  - Paper Process: Standard MSA, procurement team involved
│  - Identify Pain: Current Snowflake costs unsustainable
│  - Champion: Data Engineering Director advocating internally
│  
│  **Risks**: Budget approval delays, competing priorities
│  **Next Steps**: Champion meeting scheduled, technical validation pending
│  ```
└─ Result: User sees comprehensive deal analysis in Slack

00:26 - PROCESSOR LAMBDA → S3 CONVERSATION EXPORT
├─ Component: AWS S3 (revops-ai-framework-kb-740202120544)
├─ Function: Complete conversation tracking and monitoring
├─ Export Path: conversation-history/2025/08/16/2025-08-16T16-30-25/
├─ Files Created:
│  ├─ conversation.json: Complete conversation with agent traces
│  └─ metadata.json: Export metadata and quality metrics
├─ Conversation.json Contents:
│  ├─ user_input: Original Slack message
│  ├─ agent_invocations: Manager → Deal Analysis agent flow
│  ├─ tool_executions: Firebolt SQL queries, Gong API calls
│  ├─ collaboration_map: Agent handoffs and communications
│  ├─ response_content: Final formatted response
│  ├─ timing_data: Processing duration for each component
│  ├─ quality_scores: Response quality assessment
│  └─ error_handling: Any retries or fallbacks used
├─ Metadata.json Contents:
│  ├─ conversation_id: Unique tracking identifier
│  ├─ processing_time: Total duration (26 seconds)
│  ├─ agent_count: Number of agents involved (2)
│  ├─ tool_executions: Number of external calls (1 Firebolt)
│  ├─ data_sources: Systems accessed (Firebolt, Knowledge Base)
│  └─ export_quality: Quality validation score
└─ Result: Complete audit trail available for analysis

00:27 - PROCESSOR LAMBDA → CLOUDWATCH LOGS
├─ Component: AWS CloudWatch Logs
├─ Log Groups:
│  ├─ /aws/lambda/revops-slack-bedrock-processor
│  ├─ /aws/lambda/revops-firebolt-query
│  └─ /aws/lambda/revops-gong-retrieval
├─ Log Entries:
│  ├─ INFO: Request processing started (correlation_id)
│  ├─ INFO: Manager Agent invoked successfully
│  ├─ INFO: Deal Analysis Agent collaboration initiated
│  ├─ INFO: Firebolt query executed (1 row returned, 250ms)
│  ├─ INFO: MEDDPICC analysis completed
│  ├─ INFO: Response formatted and delivered to Slack
│  ├─ INFO: S3 conversation export completed
│  └─ INFO: Request processing completed (total: 26.5s)
└─ Result: Complete operational visibility for monitoring
```

### API Integration - Complete End-to-End Flow

**Example Query: "What deals are closing this quarter?" via HTTP POST**

#### Phase 1: External Request and Gateway Processing (0-2 seconds)
```
00:00 - EXTERNAL SYSTEM → API GATEWAY
├─ Component: API Gateway (prod-revops-webhook-gateway-api)
├─ Endpoint: https://w3ir4f0ba8.execute-api.us-east-1.amazonaws.com/prod/webhook
├─ Method: POST /webhook
├─ Function: HTTPS endpoint, request validation, Lambda proxy integration
├─ Input Payload:
│  ```json
│  {
│    "query": "What deals are closing this quarter?",
│    "source_system": "crm_dashboard",
│    "source_process": "quarterly_review",
│    "timestamp": "2025-08-16T16:30:00Z"
│  }
│  ```
├─ Processing:
│  ├─ 1. SSL termination and HTTPS enforcement
│  ├─ 2. Request size validation (max 6MB)
│  ├─ 3. Rate limiting and throttling controls
│  ├─ 4. CORS headers for cross-origin requests
│  └─ 5. Route to Webhook Gateway Lambda
└─ Output: Lambda proxy integration invocation

00:01 - API GATEWAY → WEBHOOK GATEWAY LAMBDA
├─ Component: prod-revops-webhook-gateway
├─ Runtime: Python 3.11, 512MB memory, 15min timeout
├─ Function: Request validation, tracking ID generation, async queuing
├─ Input: API Gateway event with request payload
├─ Processing Steps:
│  ├─ 1. Parse and validate JSON payload structure
│  ├─ 2. Validate required fields (query, source_system)
│  ├─ 3. Generate unique tracking ID (UUID4)
│  ├─ 4. Create correlation metadata
│  ├─ 5. Prepare SQS message for async processing
│  └─ 6. Format immediate response
├─ Validation Rules:
│  ├─ query: Required string, max 1000 characters
│  ├─ source_system: Required string, alphanumeric + underscore
│  ├─ source_process: Optional string
│  └─ timestamp: Optional ISO 8601 datetime
└─ Output: Immediate response + SQS message

00:02 - WEBHOOK GATEWAY LAMBDA → IMMEDIATE RESPONSE
├─ Component: API Gateway response
├─ Function: Immediate acknowledgment to external system
├─ HTTP Status: 200 OK
├─ Response Headers:
│  ├─ Content-Type: application/json
│  ├─ Access-Control-Allow-Origin: *
│  └─ X-Request-ID: tracking_id
├─ Response Body:
│  ```json
│  {
│    "success": true,
│    "message": "Request queued for processing",
│    "tracking_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
│    "queued_at": "2025-08-16T16:30:02.123Z",
│    "status": "queued"
│  }
│  ```
└─ Result: External system receives tracking ID immediately
```

#### Phase 2: Async Queuing and Processing Initiation (2-5 seconds)
```
00:02 - WEBHOOK GATEWAY LAMBDA → SQS OUTBOUND QUEUE
├─ Component: prod-revops-webhook-outbound-queue
├─ Function: Async processing queue for webhook requests
├─ Queue Configuration:
│  ├─ Visibility timeout: 960 seconds (16 minutes)
│  ├─ Message retention: 14 days
│  ├─ Dead letter queue: prod-revops-webhook-outbound-dlq
│  ├─ Max receive count: 3
│  └─ Batch size: 1 (for event source mapping)
├─ Message Payload:
│  ```json
│  {
│    "tracking_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
│    "user_message": "What deals are closing this quarter?",
│    "source_system": "crm_dashboard",
│    "source_process": "quarterly_review",
│    "queued_at": "2025-08-16T16:30:02.123Z",
│    "correlation_metadata": {
│      "request_ip": "203.0.113.45",
│      "user_agent": "CRM-Dashboard/1.2.3",
│      "api_version": "v1"
│    }
│  }
│  ```
├─ Processing: Message triggers event source mapping
└─ Output: Queue Processor Lambda invocation

00:03 - SQS → QUEUE PROCESSOR LAMBDA
├─ Component: revops-webhook
├─ Runtime: Python 3.11, 512MB memory, 15min timeout
├─ Function: SQS message processing and Manager Agent invocation
├─ Event Source: SQS event source mapping
├─ Input: SQS message with webhook request
├─ Processing Steps:
│  ├─ 1. Parse SQS message and extract tracking_id
│  ├─ 2. Initialize conversation tracking
│  ├─ 3. Validate message format and required fields
│  ├─ 4. Prepare Manager Agent Wrapper invocation
│  └─ 5. Handle any processing errors with retries
└─ Output: Manager Agent Wrapper invocation

00:04 - QUEUE PROCESSOR → MANAGER AGENT WRAPPER
├─ Component: revops-manager-agent-wrapper
├─ Runtime: Python 3.11, 512MB memory, 15min timeout
├─ Function: Bedrock Agent invocation wrapper with error handling
├─ Input: Webhook request with tracking metadata
├─ Processing Steps:
│  ├─ 1. Format payload for Bedrock Agent Runtime API
│  ├─ 2. Configure agent session with correlation ID
│  ├─ 3. Set up conversation tracking parameters
│  ├─ 4. Invoke Manager Agent via Bedrock Runtime
│  └─ 5. Handle Bedrock API responses and errors
├─ Bedrock Configuration:
│  ├─ Agent ID: PVWGKOWSOT
│  ├─ Agent Alias: TSTALIASID
│  ├─ Session timeout: 15 minutes
│  └─ Enable conversation tracing
└─ Output: Manager Agent processing via Bedrock
```

#### Phase 3: AI Processing and Data Retrieval (5-35 seconds)
```
00:05 - MANAGER AGENT WRAPPER → MANAGER AGENT (BEDROCK)
├─ Component: Amazon Bedrock Agent (PVWGKOWSOT)
├─ Model: Claude 3.7 Sonnet with inference profile
├─ Function: Query analysis and agent routing
├─ Agent Type: SUPERVISOR
├─ Knowledge Base: F61WLOYZSW (revenue operations knowledge)
├─ Input: {"user_message": "What deals are closing this quarter?"}
├─ Processing:
│  ├─ 1. Analyze query intent: "quarterly deal pipeline" → Data Agent needed
│  ├─ 2. Determine scope: Current quarter (Q4 2025)
│  ├─ 3. Identify required data: deals in closing stages
│  ├─ 4. Route to Data Agent with specific parameters
│  └─ 5. Prepare comprehensive analysis instructions
└─ Output: Data Agent invocation with pipeline analysis request

00:07 - MANAGER AGENT → DATA AGENT (BEDROCK)
├─ Component: Amazon Bedrock Agent (NOJMSQ8JPT)
├─ Model: Claude 3.7 Sonnet with inference profile
├─ Function: Data retrieval and analytics across revenue operations
├─ Agent Type: COLLABORATOR (general-purpose)
├─ Tools Available:
│  ├─ firebolt_sql_query: SQL execution against data warehouse
│  ├─ gong_retrieval: Sales call transcript analysis
│  ├─ knowledge_base_retrieval: Schema and business logic
│  └─ agent_collaboration: Communication with other agents
├─ Input: {"analysis_type": "quarterly_pipeline", "quarter": "Q4_2025"}
├─ Processing:
│  ├─ 1. Query knowledge base for Q4 date ranges and stage definitions
│  ├─ 2. Construct comprehensive SQL queries for pipeline analysis
│  ├─ 3. Execute multiple Firebolt queries for complete picture
│  └─ 4. Aggregate and analyze results
└─ Output: Multiple SQL query executions

00:10 - DATA AGENT → FIREBOLT LAMBDA (Query 1: Pipeline Overview)
├─ Component: revops-firebolt-query
├─ Function: Execute pipeline overview query
├─ SQL Query:
│  ```sql
│  SELECT 
│    stage_name,
│    COUNT(*) as deal_count,
│    SUM(amount) as total_value,
│    AVG(probability) as avg_probability,
│    SUM(amount * probability / 100) as weighted_value
│  FROM opportunities 
│  WHERE close_date BETWEEN '2025-10-01' AND '2025-12-31'
│    AND is_closed = false
│    AND stage_name IN ('Negotiate', 'Proposal', 'Verbal Commit')
│  GROUP BY stage_name
│  ORDER BY 
│    CASE stage_name 
│      WHEN 'Verbal Commit' THEN 1
│      WHEN 'Negotiate' THEN 2  
│      WHEN 'Proposal' THEN 3
│    END
│  ```
├─ Processing: Execute query and return aggregated pipeline data
└─ Output: Pipeline overview statistics

00:12 - DATA AGENT → FIREBOLT LAMBDA (Query 2: Top Opportunities)
├─ Component: revops-firebolt-query
├─ Function: Execute top deals query
├─ SQL Query:
│  ```sql
│  SELECT 
│    opportunity_name,
│    account_name,
│    amount,
│    probability,
│    stage_name,
│    close_date,
│    owner_name,
│    last_activity_date,
│    DATEDIFF('day', CURRENT_DATE, close_date) as days_to_close
│  FROM opportunities o
│  LEFT JOIN accounts a ON o.account_id = a.id
│  WHERE close_date BETWEEN '2025-10-01' AND '2025-12-31'
│    AND is_closed = false
│    AND amount >= 100000
│  ORDER BY (amount * probability / 100) DESC
│  LIMIT 10
│  ```
├─ Processing: Execute query and return top opportunities
└─ Output: Detailed top deals information

00:15 - DATA AGENT → FIREBOLT LAMBDA (Query 3: Risk Analysis)
├─ Component: revops-firebolt-query
├─ Function: Execute risk analysis query
├─ SQL Query:
│  ```sql
│  SELECT 
│    CASE 
│      WHEN last_activity_date < CURRENT_DATE - INTERVAL 14 DAY 
│        THEN 'Stale - No Recent Activity'
│      WHEN probability < 50 AND stage_name = 'Negotiate' 
│        THEN 'Low Probability in Late Stage'
│      WHEN close_date < CURRENT_DATE + INTERVAL 30 DAY 
│        AND stage_name NOT IN ('Verbal Commit', 'Closed Won')
│        THEN 'Closing Soon - Early Stage'
│      ELSE 'On Track'
│    END as risk_category,
│    COUNT(*) as deal_count,
│    SUM(amount) as total_value
│  FROM opportunities
│  WHERE close_date BETWEEN '2025-10-01' AND '2025-12-31'
│    AND is_closed = false
│  GROUP BY risk_category
│  ORDER BY total_value DESC
│  ```
├─ Processing: Execute query and analyze risk factors
└─ Output: Risk assessment data

00:20 - DATA AGENT → GONG LAMBDA (Competitive Intelligence)
├─ Component: revops-gong-retrieval
├─ Function: Analyze recent calls for competitive mentions
├─ API Query: Recent calls for Q4 closing opportunities
├─ Processing:
│  ├─ 1. Search calls by opportunity IDs from Firebolt results
│  ├─ 2. Extract competitive mentions and objections
│  ├─ 3. Identify common themes and concerns
│  └─ 4. Summarize competitive landscape
└─ Output: Competitive intelligence summary

00:25 - DATA AGENT → MANAGER AGENT
├─ Component: Agent collaboration via Bedrock
├─ Function: Return comprehensive Q4 pipeline analysis
├─ Response Structure:
│  ├─ pipeline_overview: Aggregated statistics by stage
│  ├─ top_opportunities: Detailed list of highest-value deals
│  ├─ risk_analysis: Risk categorization and mitigation needs
│  ├─ competitive_intelligence: Market dynamics and competitor activity
│  ├─ forecasting_data: Probability-weighted projections
│  └─ data_quality: Confidence scores and data completeness
├─ Processing: Manager Agent synthesizes comprehensive response
└─ Output: Final response preparation
```

#### Phase 4: Response Generation and Delivery (35-47 seconds)
```
00:35 - MANAGER AGENT → MANAGER AGENT WRAPPER
├─ Component: Agent response processing
├─ Function: Format response for external webhook delivery
├─ Response Processing:
│  ├─ 1. Validate completeness of agent response
│  ├─ 2. Format both markdown and plain text versions
│  ├─ 3. Add conversation tracking metadata
│  ├─ 4. Prepare webhook delivery payload
│  └─ 5. Generate session summary
├─ Formatted Response:
│  ```markdown
│  **Q4 2025 Deal Pipeline Analysis**
│  
│  **Pipeline Summary**
│  - Total Pipeline: $4.2M ARR across 23 opportunities
│  - Weighted Pipeline: $2.1M ARR (50% probability-adjusted)
│  - Deals in Negotiate Stage: 8 opportunities ($2.8M value)
│  
│  **Top Closing Opportunities**
│  1. IXIS Enterprise ($2.1M) - 75% probability - Negotiate
│  2. DataCorp Expansion ($800K) - 80% probability - Verbal Commit  
│  3. TechFlow Migration ($600K) - 65% probability - Negotiate
│  
│  **Risk Factors**
│  - 3 deals with stale activity (no updates in 14+ days)
│  - 2 deals facing competitive pressure from Snowflake
│  - 1 deal closing in <30 days still in early stage
│  
│  **Competitive Landscape**
│  - Snowflake mentioned in 40% of Q4 deal calls
│  - Primary objection: "Already invested in current solution"
│  - Opportunity: Cost optimization messaging resonating well
│  ```
└─ Output: Formatted response ready for webhook delivery

00:40 - MANAGER AGENT WRAPPER → QUEUE PROCESSOR
├─ Component: Response handling and webhook preparation
├─ Function: Prepare final webhook delivery
├─ Response Package:
│  ├─ tracking_id: Original request tracking ID
│  ├─ ai_response: Formatted AI analysis (markdown + plain text)
│  ├─ session_id: Bedrock session identifier
│  ├─ processing_metadata: Timing and agent information
│  ├─ data_sources: Systems accessed during analysis
│  └─ quality_metrics: Response completeness scores
├─ Processing: Queue Processor prepares webhook delivery
└─ Output: Webhook delivery execution

00:42 - QUEUE PROCESSOR → EXTERNAL WEBHOOK DELIVERY
├─ Component: HTTP client for webhook delivery
├─ Function: Deliver AI response to configured webhook URL
├─ Webhook Configuration: Environment variable WEBHOOK_URL
├─ HTTP Request:
│  ├─ Method: POST
│  ├─ Headers: Content-Type: application/json
│  ├─ Timeout: 30 seconds
│  ├─ Retry Policy: 3 attempts with exponential backoff
│  └─ SSL verification: Enabled
├─ Payload:
│  ```json
│  {
│    "tracking_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
│    "source_system": "crm_dashboard", 
│    "source_process": "quarterly_review",
│    "original_query": "What deals are closing this quarter?",
│    "ai_response": {
│      "response": "**Q4 2025 Deal Pipeline Analysis**\n\n...",
│      "response_plain": "Q4 2025 Deal Pipeline Analysis...",
│      "session_id": "session_20250816_abc123",
│      "timestamp": "2025-08-16T16:30:40Z"
│    },
│    "processing_metadata": {
│      "total_duration_seconds": 37,
│      "agents_invoked": ["Manager", "Data"],
│      "data_sources": ["Firebolt", "Gong"],
│      "queries_executed": 3
│    },
│    "webhook_metadata": {
│      "delivered_at": "2025-08-16T16:30:42Z",
│      "delivery_attempt": 1
│    }
│  }
│  ```
└─ Result: External system receives comprehensive AI analysis

00:43 - QUEUE PROCESSOR → S3 CONVERSATION EXPORT
├─ Component: Conversation tracking and audit trail
├─ Export Path: conversation-history/2025/08/16/2025-08-16T16-30-43/
├─ Conversation Export: Complete request/response cycle with timing
├─ Processing: Same detailed export as Slack integration
└─ Result: Complete audit trail for webhook processing

00:44 - QUEUE PROCESSOR → CLOUDWATCH METRICS
├─ Component: Custom CloudWatch metrics
├─ Metrics Published:
│  ├─ WebhookProcessingDuration: 37 seconds
│  ├─ AgentsInvoked: 2
│  ├─ SQLQueriesExecuted: 3
│  ├─ WebhookDeliverySuccess: 1
│  └─ ResponseQualityScore: 0.87
├─ Dimensions: source_system, request_type, agent_routing
└─ Result: Operational metrics for monitoring and alerting
```

### Component Function Reference

#### Input Layer Components
- **API Gateway**: SSL termination, request routing, rate limiting, CORS handling
- **Slack Webhook Verification**: Signature validation, event filtering, security enforcement  
- **Handler Lambda**: Immediate response, message validation, SQS queuing
- **Webhook Gateway Lambda**: Request validation, tracking ID generation, async queuing

#### Processing Layer Components  
- **SQS Queues**: Async processing, message durability, retry logic, dead letter handling
- **Processor Lambda**: Slack message processing, agent orchestration, response delivery
- **Queue Processor Lambda**: Webhook message processing, external delivery
- **Manager Agent Wrapper**: Bedrock API integration, error handling, session management

#### AI Layer Components
- **Manager Agent (PVWGKOWSOT)**: Query routing, workflow coordination, response synthesis
- **Deal Analysis Agent (DBHYUWC6U6)**: MEDDPICC analysis, deal assessment, risk evaluation
- **Lead Analysis Agent (IP9HPDIEPL)**: ICP scoring, qualification, engagement strategies  
- **Data Agent (NOJMSQ8JPT)**: SQL execution, data analysis, multi-source aggregation
- **Web Search Agent (QKRQXXPJOJ)**: External intelligence, company research
- **Execution Agent (AINAPUEIZU)**: Action execution, webhook delivery, integrations

#### Data Layer Components
- **Firebolt Lambda**: SQL query execution, connection management, result formatting
- **Gong Lambda**: API integration, call transcript retrieval, competitive intelligence
- **Knowledge Base**: Schema documentation, business logic, agent instructions
- **S3 Export**: Conversation tracking, audit trails, quality metrics

#### Monitoring Layer Components
- **CloudWatch Logs**: Detailed execution logging, error tracking, performance monitoring
- **CloudWatch Metrics**: Custom metrics, operational dashboards, alerting
- **S3 Conversation Export**: Complete conversation audit, quality assessment, compliance
- **Dead Letter Queues**: Failed message handling, error analysis, retry management

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