# RevOps AI Framework V2

**Enterprise-grade AI-powered Revenue Operations Framework built on Amazon Bedrock**

## Project Goal

The RevOps AI Framework is a comprehensive, AI-powered revenue operations platform designed to revolutionize how revenue teams analyze data, assess leads, manage deals, and optimize business performance. Built on Amazon Bedrock with a multi-agent architecture, it provides intelligent automation and insights across the entire revenue lifecycle.

## What This System Does

### For RevOps Teams
This system acts as your intelligent assistant for revenue operations. Instead of manually analyzing data across multiple systems, you can simply ask questions in plain English through Slack and get comprehensive answers. The system automatically pulls data from your Firebolt Data Warehouse, Salesforce CRM, and Gong call recordings to provide complete insights about customers, deals, and revenue performance.

### Technical Implementation
The system uses four specialized AI agents working together: a Decision Agent that coordinates everything, a Data Agent that retrieves information from your databases, a WebSearch Agent that researches companies and prospects, and an Execution Agent that can take actions like sending notifications or updating systems. This multi-agent approach ensures accurate, comprehensive responses while maintaining security and performance.

## Solution Overview

### Core Problem Solved
Revenue teams struggle with:
- Manual analysis of vast amounts of customer and prospect data
- Time-intensive lead qualification and assessment processes
- Fragmented insights across multiple data sources (Firebolt Data Warehouse, Salesforce, Gong)
- Reactive rather than proactive revenue management
- Inconsistent decision-making processes

### Our Solution
An intelligent AI framework that:
- Automates complex revenue operations analysis using specialized AI agents
- Provides real-time insights from multiple data sources
- Enables natural language interactions through Slack integration
- Delivers consistent, data-driven recommendations for revenue optimization
- Scales seamlessly with enterprise-grade AWS infrastructure

## Architecture Overview

### Multi-Agent Collaboration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACES                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐           │
│  │    Slack    │    │   Direct    │    │   Future    │           │
│  │ Integration │    │ API Calls   │    │ Interfaces  │           │
│  └─────────────┘    └─────────────┘    └─────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DECISION AGENT (SUPERVISOR)                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ • Orchestrates multi-agent collaboration                     │ │
│  │ • Processes complex revenue operations queries               │ │
│  │ • Synthesizes insights from multiple sources                 │ │
│  │ • Delivers strategic recommendations                         │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │   DATA AGENT    │ │ WEBSEARCH AGENT │ │ EXECUTION AGENT │
    │                 │ │                 │ │                 │
    │ • Firebolt DWH  │ │ • External      │ │ • Webhooks      │
    │ • Salesforce    │ │   Intelligence  │ │ • Notifications │
    │ • Gong Calls    │ │ • Company       │ │ • CRM Updates   │
    │ • Knowledge     │ │   Research      │ │ • Data Writes   │
    │   Base Queries  │ │ • Market Data   │ │ • Triggers      │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
            │                   │                   │
            ▼                   ▼                   ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │ DATA SOURCES    │ │ EXTERNAL APIs   │ │ ACTION SYSTEMS  │
    │                 │ │                 │ │                 │
    │ • Firebolt DWH  │ │ • Web Search    │ │ • Slack         │
    │ • Salesforce    │ │ • Company DBs   │ │ • Webhooks      │
    │ • Gong          │ │ • Market APIs   │ │ • Firebolt      │
    │ • Knowledge     │ │ • LinkedIn      │ │ • Salesforce    │
    │   Base          │ │ • News Sources  │ │ • Email         │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Technology Stack

- AI/ML Platform: Amazon Bedrock (Claude 3.5 Sonnet)
- Agent Framework: Amazon Bedrock Agents with SUPERVISOR collaboration
- Data Platform: Firebolt Data Warehouse
- CRM Integration: Salesforce
- Conversation Intelligence: Gong
- Knowledge Management: Amazon Bedrock Knowledge Bases
- Integration Layer: AWS Lambda, API Gateway, SQS
- User Interface: Slack (AWS best practices architecture)
- Infrastructure: AWS (CloudFormation, IAM, Secrets Manager, CloudWatch)

## Core Use Cases

### 1. Data Analysis on Specific Topics
```
Query: "Analyze Q4 consumption trends for EMEA customers"
Process: Decision Agent → Data Agent → Firebolt DWH → Analysis → Insights
Output: Detailed consumption analysis with trends, anomalies, and recommendations
```

### 2. Lead Assessment and Qualification
```
Query: "Assess if John Smith from TechCorp is a good lead"
Process: Decision Agent → Data Agent (CRM check) → WebSearch Agent (research) → Assessment
Output: Comprehensive lead score with ICP alignment and engagement strategy
```

### 3. Deal Health and Risk Assessment
```
Query: "Analyze the Acme Corp opportunity and assess deal risk"
Process: Decision Agent → Data Agent (Salesforce + Gong) → Analysis → Risk scoring
Output: Deal health assessment with risk factors and mitigation strategies
```

### 4. Customer Churn Risk Analysis
```
Query: "Which customers are at highest churn risk this quarter?"
Process: Decision Agent → Data Agent (usage patterns) → WebSearch (company health) → Risk scoring
Output: Prioritized churn risk list with intervention recommendations
```

### 5. Forecasting and Pipeline Reviews
```
Query: "Review Q1 pipeline forecast and identify gaps"
Process: Decision Agent → Data Agent (pipeline data) → Analysis → Gap identification
Output: Pipeline health assessment with gap analysis and strategies
```

### 6. Consumption Pattern Analysis
```
Query: "Analyze FBU utilization trends for commit customers"
Process: Decision Agent → Data Agent (consumption data) → Pattern analysis
Output: Usage optimization recommendations and expansion opportunities
```

## Key Capabilities

### Intelligence and Analytics
- Multi-source Data Integration: Seamlessly combines data from Firebolt Data Warehouse, Salesforce, Gong, and external sources
- Temporal Analysis: Advanced time-series analysis with proper handling of incomplete periods
- Customer Segmentation: Intelligent classification (Commit, Product-Led Growth, Prospects) with appropriate business logic
- Anomaly Detection: Automated identification of unusual patterns requiring investigation
- Predictive Analytics: Churn risk scoring, deal probability assessment, consumption forecasting

### Natural Language Processing
- Conversational Interface: Natural language queries through Slack integration
- Context Awareness: Maintains conversation history for follow-up questions
- Intent Recognition: Understands complex revenue operations requests
- Multi-turn Conversations: Supports interactive analysis sessions

### Automation and Actions
- Automated Insights: Proactive identification of opportunities and risks
- Stakeholder Notifications: Intelligent alerting based on analysis results
- CRM Updates: Automated data enrichment and field updates
- Workflow Triggers: Integration with existing revenue operations processes

### Enterprise Features
- Security: IAM-based access control with Slack signature verification
- Scalability: Serverless AWS architecture with auto-scaling
- Monitoring: Comprehensive CloudWatch integration
- Error Handling: Dead letter queues and retry mechanisms
- Audit Trail: Complete logging of all agent interactions

## Business Value

### Revenue Impact
- Faster Lead Qualification: Reduce lead assessment time from hours to minutes
- Improved Deal Conversion: Data-driven insights increase win rates
- Churn Prevention: Proactive risk identification and intervention
- Pipeline Optimization: Better forecasting and gap identification
- Consumption Growth: Usage pattern analysis drives expansion opportunities

### Operational Efficiency
- Automated Analysis: Eliminate manual data gathering and analysis
- Consistent Decision-Making: Standardized assessment criteria and processes
- Real-time Insights: Immediate access to critical revenue data
- Reduced Context Switching: All insights available through familiar Slack interface

### Strategic Advantages
- Data-Driven Culture: Promote evidence-based revenue decisions
- Competitive Intelligence: External research capabilities for market insights
- Scalable Operations: Handle growing data volumes without proportional team growth
- Knowledge Democratization: Make revenue insights accessible to entire team

## Deployment

### Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured with `FireboltSystemAdministrator-740202120544` profile
- Python 3.9+ with pip
- Firebolt Data Warehouse access
- Salesforce integration
- Gong API access
- Slack workspace administration rights

### Complete Clean Environment Deployment

#### Step 1: Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd revops_ai_framework/V2

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure AWS SSO (recommended)
aws configure sso --profile FireboltSystemAdministrator-740202120544
# OR configure with access keys
aws configure --profile FireboltSystemAdministrator-740202120544
```

#### Step 2: Configure Secrets
```bash
# Copy secrets template
cp deployment/secrets.template.json deployment/secrets.json

# Edit secrets.json with your actual credentials:
# - Firebolt client_id and client_secret
# - Gong API credentials
# - Slack signing secret and bot token
```

#### Step 3: Deploy Core Infrastructure
```bash
cd deployment

# Install deployment dependencies
pip install -r requirements.txt

# Deploy all agents and Lambda functions
python3 deploy_production.py
```

#### Step 4: Deploy Slack Integration
```bash
cd ../integrations/slack-bedrock-gateway

# Deploy Slack-Bedrock gateway
python3 deploy.py

# Note the API Gateway URL from output
```

#### Step 5: Deploy Enhanced Monitoring
```bash
cd ../../monitoring

# Deploy comprehensive monitoring and logging
python3 deploy-monitoring.py
```

#### Step 6: Configure Slack App
1. Create Slack App at https://api.slack.com/apps
2. Configure Event Subscriptions:
   - URL: `https://YOUR-API-GATEWAY-ID.execute-api.us-east-1.amazonaws.com/prod/slack-events`
   - Subscribe to: `app_mention`
3. Install app to workspace
4. Update secrets in AWS Secrets Manager with Slack credentials

#### Step 7: Test and Validate
```bash
# Test Slack integration
cd integrations/slack-bedrock-gateway
python3 tests/test_integration.py

# Monitor logs
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow --profile FireboltSystemAdministrator-740202120544

# Test in Slack
@RevBot test connectivity
```

### Production Usage
```bash
# Complex revenue analysis
@RevBot analyze Q2-2025 revenue by customer segment with month-over-month trends

# Lead assessment
@RevBot assess if John Smith from DataCorp is a good lead

# Customer risk analysis
@RevBot analyze churn risk for enterprise customers with declining usage
```

### Monitoring and Troubleshooting

#### CloudWatch Dashboard
Access real-time monitoring at:
`https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-slack-bedrock-monitoring`

#### Common Commands
```bash
# Check system health
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-processing-queue \
  --attribute-names ApproximateNumberOfMessages \
  --profile FireboltSystemAdministrator-740202120544

# View recent errors
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'ERROR' \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --profile FireboltSystemAdministrator-740202120544

# Check dead letter queue
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-dlq \
  --attribute-names ApproximateNumberOfMessages \
  --profile FireboltSystemAdministrator-740202120544
```

### Important Notes
- The system is fully production-ready with enterprise monitoring
- Lambda timeout set to 5 minutes for complex analyses
- All components follow AWS best practices
- Comprehensive error handling and dead letter queues
- Enhanced monitoring with CloudWatch dashboards and alerts

## Project Structure

```
revops_ai_framework/V2/
├── agents/                          # AI Agent Definitions
│   ├── data_agent/                  # Data retrieval and analysis
│   │   ├── data_agent.py           # Agent implementation
│   │   └── instructions.md         # Agent instructions
│   ├── decision_agent/              # Main orchestrator (SUPERVISOR)
│   │   ├── decision_agent.py       # Agent implementation  
│   │   ├── instructions.md         # Current agent instructions
│   │   └── instructions_concise.md # Concise version
│   ├── execution_agent/             # Action execution
│   │   ├── execution_agent.py      # Agent implementation
│   │   └── instructions.md         # Agent instructions
│   └── web_search_agent/            # External intelligence
│       ├── web_search_agent.py     # Agent implementation
│       └── instructions.md         # Agent instructions
├── deployment/                      # Infrastructure deployment
│   ├── config.json                 # Agent configuration (git-ignored)
│   ├── deploy_production.py        # Main deployment script
│   ├── README.md                   # Deployment documentation
│   ├── requirements.txt            # Deployment dependencies
│   └── secrets.template.json      # Secrets template
├── integrations/                    # External integrations
│   └── slack-bedrock-gateway/       # Slack integration (AWS best practices)
│       ├── config/                 # Configuration files
│       ├── deploy.py               # Slack integration deployment
│       ├── DEPLOYMENT_NOTES.md     # Deployment notes
│       ├── infrastructure/         # CloudFormation templates
│       ├── lambdas/                # Handler and processor functions
│       ├── README.md               # Integration documentation
│       └── tests/                  # Integration tests
├── knowledge_base/                  # Knowledge management
│   ├── business_logic/             # Business rules and logic
│   │   ├── customer_classification.md
│   │   ├── revenue_logic.md
│   │   ├── churn_risk_logic.md
│   │   └── ... (other business logic files)
│   ├── firebolt_schema/            # Data warehouse schema
│   │   ├── firebolt_schema.json
│   │   └── firebolt_schema.md
│   ├── icp_and_reachout/          # Customer profiling
│   │   ├── firebolt_icp.md
│   │   └── firebolt_messeging.md
│   ├── sql_patterns/              # Query templates
│   │   ├── customer_segmentation.md
│   │   └── temporal_analysis.md
│   ├── workflows/                 # Process documentation
│   │   ├── lead_assessment_workflow.md
│   │   ├── comprehensive_deal_assessment_workflow.md
│   │   └── ... (other workflow files)
│   └── schema_knowledge_base.py   # Knowledge base utilities
├── monitoring/                     # Enhanced monitoring and logging
│   ├── deploy-monitoring.py       # Monitoring deployment script
│   ├── enhanced-logging-solution.yaml # CloudFormation template
│   └── troubleshooting-runbook.md # Operations runbook
├── tools/                         # Supporting Lambda functions
│   ├── firebolt/                  # Data warehouse integration
│   │   ├── metadata_lambda/       # Schema metadata
│   │   ├── query_lambda/          # SQL query execution
│   │   └── writer_lambda/         # Data writing
│   ├── gong/                      # Conversation intelligence
│   │   └── retrieval_lambda/      # Call data retrieval
│   ├── web_search/                # External search capabilities
│   │   └── lambda_function.py     # Web search implementation
│   └── webhook/                   # Action execution functions
│       ├── lambda_function.py     # Main webhook handler
│       ├── modules/               # Supporting modules
│       ├── requirements.txt       # Dependencies
│       └── utils/                 # Utility functions
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
└── requirements.txt               # Main project dependencies
```

## Usage Examples

### Slack Commands

#### Revenue Analysis
```
@RevBot analyze Q4 revenue performance by customer segment

@RevBot compare consumption patterns between commit and PLG customers

@RevBot identify top 10 expansion opportunities based on usage trends
```

#### Lead Management
```
@RevBot assess if Sarah Johnson from DataTech is a good lead

@RevBot research competing solutions at prospect companies in our pipeline

@RevBot score our MQL leads from this week against ICP criteria
```

#### Deal Analysis
```
@RevBot analyze the Microsoft Enterprise deal and provide deal health assessment

@RevBot what are the main risk factors for deals closing this quarter?

@RevBot compare our win rates by deal size and industry vertical
```

#### Customer Success
```
@RevBot which customers show declining engagement patterns?

@RevBot analyze churn risk indicators for enterprise customers

@RevBot identify customers ready for upsell based on consumption patterns
```

### Follow-up Conversations
```
User: @RevBot analyze EMEA consumption trends
RevBot: [Provides detailed EMEA analysis]

User: Now do the same for JAPAC
RevBot: [Automatically understands context and provides JAPAC analysis]

User: What's the difference between these two regions?
RevBot: [Compares both regions with previous context]
```

## Deployment Status

### Current Infrastructure

| Component | Status | Details |
|-----------|--------|---------|
| Decision Agent | ✅ Production Ready | SUPERVISOR mode with 3 collaborators (NO action groups) |
| Data Agent | ✅ Production Ready | Firebolt, Salesforce, Gong integration |
| WebSearch Agent | ✅ Production Ready | External intelligence gathering |
| Execution Agent | ✅ Production Ready | Webhook and notification capabilities |
| Knowledge Base | ✅ Production Ready | Business logic and schema documentation |
| Slack Integration | ✅ Production Ready | Full end-to-end working integration |

### Recent Fixes Applied (July 6, 2025)
- ✅ **Fixed Bedrock Agent Permissions**: Created missing IAM service role `AmazonBedrockExecutionRoleForAgents_TCX9CGOKBR`
- ✅ **Corrected Decision Agent Configuration**: Removed inappropriate action groups, now works exclusively through collaborators
- ✅ **Resolved Model Compatibility**: Updated alias to use Claude 3.5 Sonnet v1 (compatible with on-demand throughput)
- ✅ **Validated Complete Flow**: Slack → API Gateway → Lambda → SQS → Processor → Bedrock Agent → Response

### Architecture Metrics

- Agent Response Time: 10-60 seconds (depending on query complexity)
- Data Sources: 4 primary (Firebolt, Salesforce, Gong, Web)
- Conversation Memory: Native Bedrock session management
- Error Rate: Less than 1% with automatic retry mechanisms
- Scalability: Auto-scaling serverless architecture
- Availability: 99.9% (AWS Service Level Agreement)

## Security and Compliance

### Access Control
- IAM Roles: Least privilege access for all components
- Secrets Management: AWS Secrets Manager for credentials
- API Security: Slack signature verification
- Network Security: Virtual Private Cloud isolation for sensitive operations

### Data Protection
- Encryption: At-rest and in-transit encryption
- Audit Logging: Complete CloudWatch audit trail
- Data Residency: US-East-1 AWS region
- Access Monitoring: CloudWatch and CloudTrail integration

### Compliance Features
- Data Lineage: Tracked through all agent interactions
- Retention Policies: Configurable log retention (30 days default)
- Privacy Controls: No Personally Identifiable Information storage in conversation logs
- Secure Communication: HTTPS/TLS for all integrations

## Development and Maintenance

### Monitoring and Observability
```bash
# Agent performance monitoring
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow

# System health checks
cd integrations/slack-bedrock-gateway
python3 tests/test_integration.py

# Agent collaboration tracing
aws logs filter-log-events --log-group-name /aws/lambda/revops-slack-bedrock-processor --filter-pattern "collaboration"
```

### Configuration Management
- **Agent Instructions**: Stored in `agents/*/instructions.md`
- **Deployment Config**: Centralized in `deployment/config.json`
- **Infrastructure**: CloudFormation templates for reproducible deployments

### Testing Strategy
- **Unit Tests**: Individual agent function testing
- **Integration Tests**: End-to-end workflow validation
- **Performance Tests**: Load testing for scalability
- **User Acceptance**: Business stakeholder validation

## Future Roadmap

### Planned Enhancements
- Additional Integrations: HubSpot, Outreach, LinkedIn Sales Navigator
- API Gateway: Public API for third-party integrations

### Scalability Improvements
- Batch Processing: Large-scale analysis capabilities
- Real-time Streaming: Event-driven architecture for immediate insights

## Contributing and Enhancement

### For RevOps Teams - Adding Business Logic
You can enhance the system's intelligence by adding business rules and context to the knowledge base:

1. Update Business Logic: Add new rules to `knowledge_base/business_logic/` directory
2. Add SQL Patterns: Create query templates in `knowledge_base/sql_patterns/` for common analyses  
3. Enhance ICP Definitions: Update ideal customer profile criteria in `knowledge_base/icp_and_reachout/`
4. Document Workflows: Add process documentation to `knowledge_base/workflows/`

### For Technical Teams - System Extensions
Software engineers and solution architects can extend the system by:

1. Adding New Data Sources: Create Lambda functions in `tools/` directory for new integrations
2. Enhancing Agent Capabilities: Update agent instructions in `agents/*/instructions.md`
3. Building New Integrations: Follow the pattern in `integrations/slack-bedrock-gateway/` for new interfaces
4. Scaling Infrastructure: Update CloudFormation templates for additional regions or environments

### Development Guidelines
1. Follow AWS best practices for all integrations
2. Maintain comprehensive documentation for new features
3. Include tests for all new capabilities
4. Use semantic versioning for releases
5. Ensure security review for all changes

### Architecture Principles
- Modularity: Each agent handles specific responsibilities
- Scalability: Serverless-first approach
- Security: Zero-trust security model
- Observability: Comprehensive logging and monitoring
- Maintainability: Clear separation of concerns

## Support

### Documentation
- Architecture Details: `integrations/slack-bedrock-gateway/README.md`
- Agent Instructions: `agents/*/instructions.md`
- Deployment Guide: `deployment/README.md`
- API Reference: `tools/*/README.md`

### Monitoring
- CloudWatch Dashboards: Real-time system metrics
- Log Analysis: Structured logging for troubleshooting
- Performance Metrics: Agent response times and success rates
- Error Tracking: Automated alerting for system issues

### Troubleshooting

#### Common Issues Resolution
- **Bedrock Agent Access Denied**: Ensure `AmazonBedrockExecutionRoleForAgents_TCX9CGOKBR` role exists with proper permissions
- **Decision Agent Action Groups**: Verify agent has NO action groups (should use collaborators only)
- **Model Compatibility**: Check agent alias points to version using `anthropic.claude-3-5-sonnet-20240620-v1:0`
- **Lambda Permissions**: Verify `revops-slack-bedrock-processor` role has `bedrock:InvokeAgent` permission

#### Monitoring Commands
```bash
# Check Slack integration flow
cd integrations/slack-bedrock-gateway
python3 tests/test_integration.py

# Monitor processor Lambda logs
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow --profile FireboltSystemAdministrator-740202120544

# Verify Decision Agent configuration
aws bedrock-agent get-agent --agent-id TCX9CGOKBR --profile FireboltSystemAdministrator-740202120544 --region us-east-1
```

#### Performance Monitoring
- Monitor Lambda cold starts and memory usage
- Check API Gateway response times
- Verify SQS queue processing rates
- Track Bedrock Agent response times

---

## License

This RevOps AI Framework is proprietary software designed for enterprise revenue operations. All rights reserved.

---

Built for Revenue Teams - Powered by Amazon Bedrock

*Last Updated: July 6, 2025 | Version: 2.1 | Status: Production Ready with Full Slack Integration*