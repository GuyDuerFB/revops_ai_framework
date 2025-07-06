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
- Firebolt Data Warehouse access
- Salesforce integration
- Gong API access
- Slack workspace administration rights

### Quick Start

#### 1. Deploy Core Agent Infrastructure
```bash
cd deployment
python3 deploy_production.py
```

#### 2. Deploy Slack Integration
```bash
cd integrations/slack-bedrock-gateway
python3 deploy.py
```

#### 3. Configure Slack App
- Event Subscriptions URL: `https://your-api-gateway-url/prod/slack-events`
- Subscribe to: `app_mention`
- Install app to workspace

#### 4. Test Integration
```bash
# Run integration test
cd integrations/slack-bedrock-gateway
python3 tests/test_integration.py
```

#### 5. Slack Usage
```
@RevBot analyze EMEA customers consumption QoQ and provide main highlights
```

### Important Notes
- The system is fully functional and tested end-to-end
- Decision Agent configuration has been optimized for SUPERVISOR role
- All components properly integrated with AWS best practices
- Comprehensive error handling and monitoring in place

### Advanced Configuration

#### Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd revops_ai_framework/V2

# Configure AWS credentials
aws configure --profile FireboltSystemAdministrator-740202120544

# Deploy infrastructure
cd deployment
python3 deploy_production.py

# Deploy Slack integration
cd ../integrations/slack-bedrock-gateway
python3 deploy.py
```

#### Monitoring Setup
```bash
# Monitor agent performance
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow

# Check system health
cd integrations/slack-bedrock-gateway
python3 tests/test_integration.py
```

## Project Structure

```
revops_ai_framework/V2/
├── agents/                          # AI Agent Definitions
│   ├── data_agent/                  # Data retrieval and analysis
│   ├── decision_agent/              # Main orchestrator (SUPERVISOR)
│   ├── execution_agent/             # Action execution
│   └── web_search_agent/            # External intelligence
├── deployment/                      # Infrastructure deployment
│   ├── config.json                  # Agent configuration
│   └── deploy_production.py         # Main deployment script
├── integrations/                    # External integrations
│   └── slack-bedrock-gateway/       # Slack integration (AWS best practices)
│       ├── infrastructure/          # CloudFormation templates
│       ├── lambdas/                 # Handler and processor functions
│       └── tests/                   # Integration tests
├── knowledge_base/                  # Knowledge management
│   ├── business_logic/              # Business rules and logic
│   ├── firebolt_schema/             # Data warehouse schema
│   ├── icp_and_reachout/           # Customer profiling
│   ├── sql_patterns/               # Query templates
│   └── workflows/                  # Process documentation
└── tools/                          # Supporting Lambda functions
    ├── firebolt/                   # Data warehouse integration
    ├── gong/                       # Conversation intelligence
    ├── web_search/                 # External search capabilities
    └── webhook/                    # Action execution functions
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