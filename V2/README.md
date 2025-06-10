# Firebolt RevOps AI Framework V2

![Firebolt Logo](https://firebolt.io/static/firebolt-logo-light-80b11f708f.svg)

## Overview

The Firebolt RevOps AI Framework is an advanced multi-agent orchestration system built on AWS Bedrock that empowers Revenue Operations teams with AI-driven insights, recommendations, and automated actions. The framework processes and analyzes data from multiple sources to optimize deal quality assessment and consumption pattern analysis.

## Business Goals

### Primary Objectives

- **Improve Deal Quality**: Identify and prioritize high-value opportunities by analyzing deals against the Ideal Customer Profile (ICP) to focus sales efforts on the most promising prospects.

- **Enhance Customer Success**: Proactively monitor and respond to consumption patterns to identify churn risks and growth opportunities before they affect revenue.

- **Streamline Operations**: Automate repetitive analysis tasks and enable data-driven decision making across the revenue cycle.

- **Drive Revenue Growth**: Increase customer lifetime value through timely interventions based on AI-driven insights and recommendations.

### Key Performance Indicators (KPIs)

- Reduction in sales cycle length
- Improved forecast accuracy
- Increased deal win rates
- Decreased customer churn
- Enhanced upsell/cross-sell rates
- More efficient resource allocation

## Architecture Overview

The framework implements a sophisticated multi-agent system leveraging AWS Bedrock Agents and Flows to create an intelligent, collaborative workflow that processes information, makes decisions, and executes actions autonomously.

### System Architecture

```
┌─────────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│                     │    │                   │    │                   │
│  Data Analysis      │    │  Decision         │    │  Execution        │
│  Agent              ├───►│  Agent            ├───►│  Agent            │
│                     │    │                   │    │                   │
└─────────────────────┘    └───────────────────┘    └───────────────────┘
         ▲                          ▲                        │
         │                          │                        │
         │                          │                        ▼
┌─────────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│                     │    │                   │    │                   │
│  Knowledge Base     │    │  Action           │    │  Integration      │
│  (Schema/Queries)   │    │  Repository       │    │  Hub (Webhooks)   │
│                     │    │                   │    │                   │
└─────────────────────┘    └───────────────────┘    └───────────────────┘
```

### Core Components

#### 1. Specialized Agents

- **Data Analysis Agent**: Interfaces with Firebolt data warehouse to extract insights from customer data, usage patterns, and sales information. Leverages specialized knowledge about Firebolt's data schema to formulate complex analytical queries.

- **Decision Agent**: Evaluates insights against business rules and recommends appropriate actions based on contextual understanding of the business domain. Applies domain-specific knowledge to determine optimal interventions.

- **Execution Agent**: Implements recommended actions through integrations with external systems, converts decisions into executable operations, and provides feedback on action results.

#### 2. Centralized Insights Storage

The framework employs a centralized insights storage system using the `revops_ai_insights` table in Firebolt to maintain a cohesive view of all AI-generated findings, recommendations and actions:

```
┌─────────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│                     │    │                   │    │                   │
│  Data Analysis      │    │  Decision         │    │  Execution        │
│  Agent              ├───►│  Agent            ├───►│  Agent            │
│                     │    │                   │    │                   │
└─────────────────────┘    └───────────────────┘    └───────────────────┘
         │                          │                        │
         ▼                          ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                      RevOps AI Insights Table                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

- **Insight Schema**: Rich schema supporting identifier, classification, scoring, temporal tracking, business metrics, and action history
- **Lifecycle Management**: Insights flow through states (open → in_progress → resolved) with complete audit trail
- **Multi-Agent Collaboration**: All agents read from and write to this central repository, allowing efficient handoffs
- **Business Metrics**: Tracking of business impact, priority, and confidence scoring for insights
- **JSON Data Support**: Uses Firebolt's VARIANT type to store flexible JSON data structures for metadata, attributes, and action results

#### 3. Supporting Infrastructure

- **Knowledge Bases**: Specialized vector databases containing:
  - Firebolt schema information for intelligent data querying
  - Business rule documentation for decision context
  - Integration guidelines for execution capabilities

- **Lambda Function Tools**:
  - **Firebolt Reader**: Executes optimized read queries against Firebolt data warehouse
  - **Firebolt Writer**: Performs secure write operations with robust SQL generation and specialized insight validation
  - **Gong Analyzer**: Retrieves and processes conversational data from Gong
  - **Webhook Dispatcher**: Sends notifications and triggers external systems

- **Bedrock Flow Orchestration**: Manages the sequence and dependencies between agent operations, handling data passing and error management

#### 3. Integration Points

- **Data Sources**: Firebolt DWH, Salesforce, Gong, Customer Usage Metrics
- **Action Channels**: Slack alerts, Email notifications, CRM updates, Ticketing systems

### Technical Foundation

- **Compute Layer**: AWS Lambda for serverless operations
- **Security**: AWS Secrets Manager for credential management
- **Storage**: S3 for knowledge base source files
- **AI Backbone**: AWS Bedrock for foundation model inference
- **Orchestration**: AWS Bedrock Flows for agent sequencing

### Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Security Layer                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐   │
│ │ Authentication  │    │ Authorization   │    │  Data Protection    │   │
│ └────────┬────────┘    └────────┬────────┘    └─────────┬───────────┘   │
│          │                       │                       │               │
└──────────┼───────────────────────┼───────────────────────┼───────────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Agent Interactions                              │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Authentication & Authorization

- **Token-based Authentication**: All inter-agent communications authenticated with short-lived JWT tokens
- **Request Signing**: All Lambda invocations require AWS SigV4 signatures
- **Least Privilege IAM**: Each Lambda function has its own IAM role with minimal permissions
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["firehose:PutRecord", "firehose:PutRecordBatch"],
        "Resource": "arn:aws:firehose:region:account-id:deliverystream/revops-ai-logs"
      },
      {
        "Effect": "Allow",
        "Action": ["secretsmanager:GetSecretValue"],
        "Resource": "arn:aws:secretsmanager:region:account-id:secret:firebolt-credentials-*"
      }
    ]
  }
  ```
- **Credential Rotation**: Automatic rotation of service credentials using AWS Secrets Manager
- **Request Validation**: All incoming requests validated against schema before processing

#### Data Protection

- **Encryption at Rest**: All data stored in S3 and Firebolt encrypted
- **Encryption in Transit**: All communications use TLS 1.2+ with modern cipher suites
- **Secrets Isolation**: Credentials stored only in AWS Secrets Manager, never in code or environment variables
- **Secure Defaults**: All infrastructure deployed with security best practices by default

## Supported Scenarios & Use Cases

### 1. Deal Quality Assessment

Evaluates sales opportunities against Firebolt's Ideal Customer Profile (ICP) to optimize sales resource allocation and improve win rates.

**Capabilities:**
- **ICP Alignment Analysis**: Scores deals based on firmographic, technographic, and use case fit
- **Opportunity Data Health**: Identifies missing or inconsistent data in CRM records
- **Technical Qualification**: Evaluates technical requirements against Firebolt's capabilities
- **Conversation Intelligence**: Processes call transcripts to extract key technical requirements and objections
- **Risk Assessment**: Flags potential blockers and competitive threats

**Outputs:**
- Deal quality score (0-100)
- Prioritized action items to improve deal quality
- Suggested conversation topics for sales teams
- Risk mitigation recommendations

### 2. Consumption Pattern Analysis

Monitors and analyzes customer usage data to identify potential churn risks and growth opportunities.

**Capabilities:**
- **Usage Trend Analysis**: Tracks changes in query volume, data ingestion, and compute usage
- **Anomaly Detection**: Identifies unusual patterns in consumption metrics
- **Seasonal Adjustment**: Normalizes usage patterns accounting for known business cycles
- **Growth Opportunity Identification**: Highlights areas for potential upsell based on usage patterns
- **Customer Health Scoring**: Calculates overall health score based on multiple data points

**Outputs:**
- Consumption trend alerts with explanation
- Customer health dashboard updates
- Recommended intervention strategies
- Growth opportunity notifications

### 3. Custom Analysis Workflows

The framework is extensible to support additional use cases by adding new knowledge bases, Lambda functions, and agent instructions.

## Deployment & Configuration

### System Requirements

**AWS Environment:**
- AWS Account with access to Bedrock, Lambda, IAM, S3, and Secrets Manager
- AWS CLI version 2.0+ installed and configured with appropriate credentials
- Python 3.9+ for the deployment script

**Source Systems:**
- Firebolt account with OAuth credentials
- Gong account with API access (optional)
- Salesforce access for CRM data (optional)

**Destination Systems:**
- Slack workspace for notifications (optional)
- Email server configuration (optional)

### Configuration Files

- `config_template.json`: Main configuration file template
- `secrets_template.json`: Template for storing credentials securely
- `webhook_config_template.json`: Configuration for external integrations

### Deployment Process

#### Infrastructure as Code Approach

The framework uses Terraform for infrastructure provisioning to ensure consistency, version control, and auditability:

```
deployment/
├── terraform/
│   ├── modules/
│   │   ├── lambda/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── knowledge_base/
│   │   ├── agent/
│   │   └── flow/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── scripts/
    ├── generate_tf_config.py
    └── apply_terraform.sh
```

The `deploy.py` script has been refactored to generate Terraform configurations rather than directly calling AWS APIs:

```python
# Example of refactored deploy.py that generates Terraform
def deploy_lambda_function(lambda_config):
    """Generate Terraform config for Lambda instead of direct deployment"""
    lambda_tf_config = {
        "resource": {
            "aws_lambda_function": {
                lambda_config["name"]: {
                    "function_name": lambda_config["name"],
                    "handler": lambda_config["handler"],
                    "runtime": lambda_config["runtime"],
                    "role": f"${{aws_iam_role.{lambda_config['name']}_role.arn}}",
                    "filename": f"${{path.module}}/dist/{lambda_config['name']}.zip}",
                    "source_code_hash": f"${{filebase64sha256("${{path.module}}/dist/{lambda_config['name']}.zip}")}}",
                    "environment": {
                        "variables": lambda_config["environment_variables"]
                    },
                    "timeout": lambda_config.get("timeout", 30),
                    "memory_size": lambda_config.get("memory_size", 256),
                    "tracing_config": {
                        "mode": "Active"
                    }
                }
            },
            "aws_iam_role": {
                f"{lambda_config['name']}_role": generate_iam_role_config(lambda_config)
            }
        }
    }
    return lambda_tf_config
```

#### Deployment Steps

1. **Prepare Configuration**
   ```bash
   # Copy and edit configuration templates
   cp deployment/config_template.json deployment/config.json
   cp deployment/secrets_template.json deployment/secrets.json
   ```

2. **Generate Terraform Configuration**
   ```bash
   cd deployment
   # Generate Terraform configurations from high-level config
   python generate_tf_config.py --config config.json --output terraform/
   ```

3. **Review and Apply Infrastructure**
   ```bash
   cd terraform
   # Initialize Terraform modules and providers
   terraform init
   
   # Preview changes
   terraform plan -out=tfplan
   
   # Apply changes
   terraform apply tfplan
   ```

4. **Verify Deployment**
   ```bash
   # Check deployment status
   terraform output deployment_summary
   ```

5. **Destroy Resources (When Needed)**
   ```bash
   # Remove all deployed resources
   terraform destroy
   ```



## Usage

### Triggering the Framework

The RevOps AI Framework can be activated through multiple methods:

1. **Scheduled Analysis**
   ```bash
   # Configure an EventBridge rule (runs daily at 8am)
   aws events put-rule --name "RevOpsAIDailyAnalysis" --schedule-expression "cron(0 8 * * ? *)"
   
   # Set the target to the main flow
   aws events put-targets --rule "RevOpsAIDailyAnalysis" --targets "Id"="1","Arn"="arn:aws:bedrock:REGION:ACCOUNT_ID:flow/FLOW_ID"
   ```

2. **On-Demand Execution**
   ```bash
   # Via the provided CLI tool
   python tools/cli/invoke_flow.py --flow deal_quality --account_id 123456 --opportunity_id SF12345
   
   # Or directly via AWS CLI
   aws bedrock-agent invoke-flow --flow-id "FLOW_ID" --flow-alias-id "FLOW_ALIAS_ID" \
     --inputs '{"input": {"content": {"account_id": "123456", "opportunity_id": "SF12345"}}}'
   ```

3. **Webhook Integration**
   * Configure the provided webhook endpoints to receive events from external systems
   * For example, trigger analysis when a Salesforce opportunity reaches a specific stage

### Accessing Results

* **Slack Notifications**: Receive immediate alerts for critical insights
* **Email Reports**: Scheduled summaries of findings and recommendations
* **Firebolt Database**: Query detailed results stored in the analyses table

## Agent Flows & Orchestration

### Multi-Agent Orchestration

The RevOps AI Framework orchestrates a sequence of specialized agents that work together to analyze data, make decisions, and execute actions. Each agent has a specific role in the workflow and communicates with others through structured JSON payloads.

#### Flow Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│                         RevOps AI Framework Flow                          │
│                                                                           │
└─────────────────┬─────────────────────────────┬───────────────────────────┘
                  │                             │
          ┌───────▼───────┐           ┌─────────▼─────────┐
 ┌────────┤  Flow Input   ├───────────►  Input Processor  │
 │        └───────────────┘           └─────────┬─────────┘
 │                                              │
 │                                     ┌────────▼────────┐
 │                                     │                  │
 │                                     │   Data Agent     │
 │                                     │                  │
 │                                     └────────┬────────┘
 │                                              │
 │        ┌───────────────┐                     │
 │        │               │                     │
 │        │  Knowledge    │◄────────┐  ┌───────▼───────┐
 │        │  Base         │         │  │               │
 │        │               │         ├──┤ Decision Agent│
 │        └───────┬───────┘         │  │               │
 │                │                 │  └───────┬───────┘
 │                │                 │          │
 │        ┌───────▼───────┐         │  ┌───────▼───────┐
 │        │               │         │  │               │
 └────────┤   Execution   │◄────────┘  │   Analysis    │
          │   Agent       │            │   Results     │
          │               │            │               │
          └───────┬───────┘            └───────────────┘
                  │
          ┌───────▼───────┐
          │               │
          │  Flow Output  │
          │               │
          └───────────────┘
```

#### Data Flow & Transformations

1. **Input Processing Stage**
   - **Input Format**: Raw trigger payload (JSON)
   ```json
   {
     "trigger_type": "scheduled|event|manual",
     "parameters": {
       "account_id": "123456",
       "opportunity_id": "OP-789",
       "analysis_type": "deal_quality|consumption"
     }
   }
   ```
   - **Transformation**: Validates parameters, enriches with contextual metadata
   - **Output Format**: Enriched analysis request (JSON)
   ```json
   {
     "request_id": "req-uuid-1234",
     "timestamp": "2025-06-10T10:30:00Z",
     "analysis_type": "deal_quality",
     "parameters": {
       "account_id": "123456",
       "opportunity_id": "OP-789"
     },
     "context": {
       "requester": "scheduled_job",
       "priority": "normal"
     }
   }
   ```

2. **Data Agent Stage**
   - **Input Format**: Enriched analysis request (from Input Processor)
   - **Processing**:
     * Analyzes request to determine required data sources
     * Formulates optimal SQL queries using schema knowledge
     * Executes queries against Firebolt via Lambda function
     * Retrieves external data (Gong transcripts, CRM data)
     * Normalizes and merges data from multiple sources
     * Performs preliminary analysis (trends, anomalies)
   - **Output Format**: Structured analytical dataset (JSON)
   ```json
   {
     "request_id": "req-uuid-1234",
     "data_collection": {
       "status": "complete",
       "sources_accessed": ["firebolt", "gong", "salesforce"],
       "record_counts": {"opportunities": 1, "calls": 5, "usage_metrics": 90}
     },
     "preliminary_findings": [
       {"type": "data_gap", "description": "Missing technical requirements"},
       {"type": "anomaly", "description": "Usage spike on 2025-06-01"}
     ],
     "dataset": {
       "account": {...},
       "opportunity": {...},
       "usage_trends": [...],
       "conversations": [...]
     }
   }
   ```

3. **Decision Agent Stage**
   - **Input Format**: Structured analytical dataset (from Data Agent)
   - **Knowledge Base Access**:
     * Retrieves business rules from vector knowledge base
     * Accesses ICP criteria and scoring rubrics
     * Pulls historical patterns for comparative analysis
   - **Processing**:
     * Evaluates data against business rules and thresholds
     * Calculates scores and confidence levels
     * Identifies action triggers and priorities
     * Generates recommendations with supporting evidence
     * Formulates response strategies
   - **Output Format**: Analysis results with recommendations (JSON)
   ```json
   {
     "request_id": "req-uuid-1234",
     "analysis_results": {
       "scores": {
         "deal_quality": 72,
         "data_completeness": 85,
         "technical_fit": 68
       },
       "flags": [
         {"type": "risk", "severity": "medium", "description": "Competing solution mentioned"},
         {"type": "opportunity", "severity": "high", "description": "Multi-region expansion potential"}
       ]
     },
     "recommendations": [
       {
         "id": "rec-1",
         "priority": "high",
         "action": "technical_workshop",
         "description": "Schedule technical workshop to address performance concerns",
         "evidence": ["call_transcript_1", "usage_metric_3"],
         "assignee": "solutions_engineering"
       },
       {...}
     ]
   }
   ```

4. **Execution Agent Stage**
   - **Input Format**: Analysis results with recommendations (from Decision Agent)
   - **Knowledge Base Access**:
     * Retrieves integration specifications
     * Accesses notification templates
     * Pulls action execution patterns
   - **Processing**:
     * Transforms recommendations into executable actions
     * Prioritizes and sequences actions
     * Formats data for external system requirements
     * Executes system integrations via webhooks
     * Records actions and responses
     * Manages state and retries for reliability
   - **Output Format**: Execution results (JSON)
   ```json
   {
     "request_id": "req-uuid-1234",
     "execution_results": {
       "status": "complete",
       "timestamp": "2025-06-10T10:35:27Z",
       "actions_executed": [
         {
           "id": "action-1",
           "based_on": "rec-1",
           "type": "notification",
           "target": "slack",
           "status": "success",
           "response": {"channel": "#revops-alerts", "ts": "1623324927.001500"}
         },
         {
           "id": "action-2",
           "based_on": "rec-2",
           "type": "data_update",
           "target": "firebolt",
           "status": "success",
           "response": {"rows_affected": 1}
         }
       ],
       "persistent_storage": {
         "database": "firebolt",
         "table": "revops_ai_executions",
         "record_id": "exec-5678"
       }
     },
     "summary": {
       "total_actions": 5,
       "successful": 5,
       "failed": 0,
       "notifications_sent": 2,
       "data_updates": 3
     }
   }
   ```

5. **Flow Output Stage**
   - **Input Format**: Execution results (from Execution Agent)
   - **Processing**:
     * Compiles comprehensive execution summary
     * Formats final response
     * Archives complete flow record
   - **Output Format**: Final flow response (JSON)
   ```json
   {
     "flow_execution_id": "flow-12345",
     "request_id": "req-uuid-1234",
     "status": "success",
     "execution_time_ms": 4827,
     "summary": "Deal quality assessment completed with 5 actions executed",
     "results_location": {
       "database": "firebolt",
       "table": "revops_ai_executions",
       "query": "SELECT * FROM revops_ai_executions WHERE request_id = 'req-uuid-1234'"
     }
   }
   ```

### Inter-Agent Communication

#### Message Structure

All messages between agents use a standardized envelope format with required tracking fields:

```json
{
  "metadata": {
    "request_id": "req-uuid-1234",
    "flow_id": "flow-12345",
    "source_agent": "data_agent",
    "target_agent": "decision_agent",
    "message_id": "msg-6789",
    "timestamp": "2025-06-10T10:32:15Z",
    "idempotency_key": "idem-key-abcdef",
    "correlation_id": "corr-id-456789",
    "version": 1
  },
  "payload": {
    // Agent-specific content as shown above
  }
}
```

#### Robust Error Handling

##### Error Response Format

Agents implement a standardized error response format with detailed diagnostic information:

```json
{
  "metadata": { /* standard metadata */ },
  "error": {
    "code": "DATA_RETRIEVAL_ERROR",
    "message": "Failed to retrieve data from Firebolt",
    "details": "Connection timeout after 30 seconds",
    "recovery_action": "retry",
    "retry_strategy": {
      "max_attempts": 3,
      "backoff_rate": 2.0,
      "initial_delay_seconds": 1
    },
    "severity": "recoverable",
    "diagnostic_info": {
      "trace_id": "trace-123456",
      "service": "firebolt-reader",
      "operation": "execute_query",
      "timestamp": "2025-06-10T10:32:17Z"
    }
  }
}
```

##### Circuit Breaker Pattern

All service integrations implement the circuit breaker pattern to prevent cascading failures:

```
┌───────────────────┐     ┌──────────────┐     ┌───────────────┐
│                   │     │              │     │               │
│  Service Client   ├────►│Circuit Breaker├────►│External Service│
│                   │     │              │     │               │
└───────────────────┘     └──────────────┘     └───────────────┘
```

Circuit breaker configuration is specified per integration:

```json
{
  "circuit_breaker": {
    "failure_threshold": 5,
    "success_threshold": 3,
    "timeout_seconds": 60,
    "monitoring": {
      "alarm_sns_topic": "arn:aws:sns:region:account:revops-ai-alerts"
    }
  }
}
```

##### Retry Policies

Exponential backoff with jitter is implemented for all service calls:

```python
def get_backoff_duration(attempt, initial_delay=1, max_delay=60, jitter=0.1):
    delay = min(initial_delay * (2 ** attempt), max_delay)
    jitter_amount = random.uniform(-jitter * delay, jitter * delay)
    return delay + jitter_amount
```

##### Dead Letter Queues

All asynchronous operations have associated dead letter queues for failed operations:

```
┌───────────────┐     ┌─────────────┐     ┌──────────────┐
│  Operation    │     │  Max Retry  │     │ Dead Letter  │
│  Queue        ├────►│  Exceeded   ├────►│ Queue        │
└───────────────┘     └─────────────┘     └──────────────┘
```

Operations in dead letter queues trigger alerts and can be manually replayed after issue resolution.

#### Advanced State Management

##### Distributed Transaction Management

The framework uses a distributed transaction manager for operations that span multiple services:

```
┌───────────────────────────────────────────────────────────┐
│                Transaction Coordinator                     │
├───────────┬───────────┬───────────┬───────────┬───────────┤
│ Prepare   │ Commit    │ Rollback  │ Recovery  │ Timeout   │
└───────────┴───────────┴───────────┴───────────┴───────────┘
         ▲              │              ▲
         │              ▼              │
┌────────┴──────┐    ┌─────────────┐  └──────────────┐
│ Participant 1 │    │Participant 2│               │Participant 3│
└───────────────┘    └─────────────┘               └────────────┘
```

State management strategies by durability requirements:

1. **Durable Persistent State**
   - Stored in Firebolt tables with transaction guarantees
   - Schema includes version control fields for optimistic concurrency
   - Schema example:
     ```sql
     CREATE TABLE revops_ai_executions (
       request_id VARCHAR NOT NULL,
       flow_id VARCHAR,
       version INTEGER NOT NULL,
       created_at TIMESTAMP NOT NULL,
       updated_at TIMESTAMP NOT NULL,
       state_data VARIANT NOT NULL,
       execution_status VARCHAR NOT NULL,
       PRIMARY KEY (request_id)
     )
     ```

2. **Transient Flow State**
   - Maintained by Bedrock Flow service with checkpoint capability
   - Critical decision points create explicit state checkpoints
   - Recoverable from checkpoint in case of failure

3. **Volatile Agent State**
   - Temporarily stored in memory during agent execution
   - Periodically synced to persistent state for recovery
   - Implements lease mechanism for long-running operations

##### Idempotency Implementation

All stateful operations implement idempotency to prevent duplicate processing:

```json
{
  "idempotency": {
    "key": "idem-key-abcdef",
    "expires_at": "2025-06-10T11:32:15Z",
    "previous_response": {
      "status": "success",
      "result_id": "result-123"
    }
  }
}
```

##### Compensating Transactions

For multi-step operations that cannot be rolled back atomically, the framework implements compensating transactions:

```python
def execute_with_compensation(operations, compensation_handlers):
    results = []
    completed_ops = []
    
    try:
        for i, operation in enumerate(operations):
            result = operation.execute()
            results.append(result)
            completed_ops.append(i)
    except Exception as e:
        # Execute compensation handlers in reverse order
        for op_idx in reversed(completed_ops):
            compensation_handlers[op_idx](results[op_idx])
        raise e
    
    return results
```

This robust state management allows for:
- Recovery from failures at any point in the flow
- Asynchronous processing with guaranteed completion
- Complete audit trail of all decisions and actions
- Analytics on historical executions and outcomes
- Safe retries and reprocessing without side effects

## Agent Capabilities

### Data Agent

**Core Capabilities:**
* Schema-aware SQL query generation against Firebolt data warehouse
* Multi-model data aggregation across various sources
* Intelligent data transformation and preparation for analysis
* Historical data comparison and trend identification
* Data quality assessment and anomaly detection

**Knowledge Base:**
* Firebolt schema definitions and relationships
* Common query patterns and optimization techniques
* Data dictionary with business context for key metrics

**Tools:**
* `firebolt_reader`: Executes read queries against Firebolt
* `gong_analyzer`: Retrieves and analyzes conversation data
* `crm_connector`: Pulls opportunity and account data

### Decision Agent

**Core Capabilities:**
* Evaluation of data insights against business rules
* Risk scoring and opportunity assessment
* Recommendation generation with confidence levels
* Multi-factor decision making with weighted criteria
* Context-aware analysis considering customer history

**Knowledge Base:**
* Business rules and evaluation criteria
* Ideal Customer Profile (ICP) definition
* Risk factors and mitigation strategies
* Intervention threshold guidelines

**Tools:**
* `insight_analyzer`: Evaluates data against business rules
* `recommendation_generator`: Creates actionable recommendations

### Execution Agent

**Core Capabilities:**
* Transformation of recommendations into concrete actions
* Integration with external systems via webhooks
* Secure write operations to Firebolt database
* Notification routing based on severity and context
* Record-keeping of executed actions for accountability

**Knowledge Base:**
* Integration specifications and requirements
* Action templates and formats
* Escalation procedures and contact information

**Tools:**
* `firebolt_writer`: Performs write operations on Firebolt
* `webhook_dispatcher`: Sends notifications to external systems
* `action_logger`: Records executed actions for audit purposes

## Development and Extension

### Extending Agent Capabilities

1. **Add New Action Groups**
   ```bash
   # Create a new action group definition
   cp agents/templates/action_group_template.json agents/data_agent/actions/new_action.json
   
   # Edit the action group definition
   nano agents/data_agent/actions/new_action.json
   ```

2. **Implement Lambda Functions**
   ```bash
   # Create a new Lambda function from template
   mkdir -p tools/new_tool/lambda_function
   cp tools/templates/lambda_template.py tools/new_tool/lambda_function/lambda_function.py
   
   # Implement your custom logic
   nano tools/new_tool/lambda_function/lambda_function.py
   ```

3. **Update Knowledge Bases**
   ```bash
   # Add new knowledge base content
   nano knowledge/schema/new_entity_schema.md
   ```

4. **Modify Flow Definitions**
   ```bash
   # Update flow configuration
   nano deployment/config.json
   ```

### Testing Extensions

```bash
# Test Lambda function locally
python tools/test_lambda.py --function-name new_tool --event tests/events/sample_event.json

# Deploy and test specific components
python deploy.py --deploy-lambdas --function new_tool
```



## Lambda Function Design

### Function Separation by Responsibility

Lambda functions are designed following the single responsibility principle to improve maintainability, scalability, and fault isolation:

#### Firebolt Data Service

Rather than a monolithic writer Lambda, the framework implements specialized functions:

```
┌───────────────────────────────┐
│       Firebolt Data Service         │
└───────┬────────┬──────────┘
         │           │
┌────────▼────────┐ ┌────────▼────────┐ ┌──────────────────┐
│  firebolt-reader   │ │  firebolt-writer   │ │ firebolt-metadata │
└─────────────────┘ └─────────────────┘ └─────────────────┘

┌─────────────────┘ ┌─────────────────┘ ┌─────────────────┘
│ Read Queries      │ │ Write Operations  │ │ Schema Information│
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

1. **firebolt-reader**: Specialized for optimized read queries
   - SQL query generation for analytics
   - Result transformation and processing
   - Cursor pagination for large result sets
   - Query optimization for Firebolt engine

2. **firebolt-writer**: Specialized for data modification operations 
   - Broken down into specialized modules:
     ```python
     # Writer service architecture
     class FireboltWriterService:
         def __init__(self, connection_manager):
             self.connection = connection_manager
             self.insert_handler = InsertOperationHandler(connection_manager)
             self.update_handler = UpdateOperationHandler(connection_manager)
             self.upsert_handler = UpsertOperationHandler(connection_manager)
             self.transaction_manager = TransactionManager(connection_manager)
             
         def handle_operation(self, operation_type, params):
             # Dispatch to appropriate specialized handler
             if operation_type == 'INSERT':
                 return self.insert_handler.execute(params)
             elif operation_type == 'UPDATE':
                 return self.update_handler.execute(params)
             elif operation_type == 'UPSERT':
                 return self.upsert_handler.execute(params)
             else:
                 raise ValueError(f"Unsupported operation: {operation_type}")
     ```

3. **firebolt-metadata**: Manages schema information and metadata
   - Table definitions and relationships
   - Column data types and constraints
   - Index information
   - Schema change tracking

#### Integration Service Design

Webhook dispatching uses non-blocking, queue-based architecture:

```
┌─────────────────┐     ┌─────────────┐     ┌───────────────────┐
│ webhook-dispatcher ├───►│ Message Queue ├───►│ webhook-processor  │
└─────────────────┘     └─────────────┘     └───────────────────┘
                                                  │
                                                  ▼
                                     ┌───────────────────┐  
                                     │ External Services │
                                     └───────────────────┘
```

1. **webhook-dispatcher**: Queues notification requests
   - Validates webhook payload against schema
   - Attaches metadata and tracking information
   - Publishes to SQS with appropriate attributes
   - Returns immediately with acceptance receipt

2. **webhook-processor**: Processes notifications from queue
   - Implements specialized handlers per integration type
   - Manages rate limiting and throttling
   - Implements circuit breakers for external services
   - Provides status tracking and delivery guarantees

### Lambda Connection Pooling

Efficient connection management is implemented for database operations:

```python
class ConnectionManager:
    _instances = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_instance(cls, connection_id):
        with cls._lock:
            if connection_id not in cls._instances:
                cls._instances[connection_id] = ConnectionManager(connection_id)
            return cls._instances[connection_id]
    
    def __init__(self, connection_id):
        self.connection_id = connection_id
        self.pool = self._create_connection_pool()
        self.last_used = time.time()
        self.in_use_connections = 0
    
    def get_connection(self):
        with self._lock:
            self.in_use_connections += 1
            self.last_used = time.time()
            return self.pool.get_connection()
    
    def release_connection(self, conn):
        with self._lock:
            self.in_use_connections -= 1
            self.pool.release_connection(conn)
```



## Monitoring & Observability

### Comprehensive Observability Stack

The RevOps AI Framework implements a multi-layered observability stack:

```
┌─────────────────────────────────────────────────────────┐
│                    Observability Dashboard                │
└──────────────┬──────────────┬───────────────┬──────────┘
               │              │               │
┌──────────────▼┐    ┌────────▼─────┐    ┌────▼───────────┐
│    Metrics     │    │    Logging   │    │    Tracing     │
└──────────────┬┘    └────────┬─────┘    └────┬───────────┘
               │              │               │
┌──────────────▼┐    ┌────────▼─────┐    ┌────▼───────────┐
│  CloudWatch    │    │ CloudWatch   │    │  X-Ray         │
└───────────────┘    └──────────────┘    └────────────────┘
```

### Distributed Tracing

End-to-end tracing is implemented using AWS X-Ray to track requests across all components:

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch all supported libraries for X-Ray tracing
patch_all()

@xray_recorder.capture('firebolt_writer')
def lambda_handler(event, context):
    # Sub-segment for input validation
    with xray_recorder.in_subsegment('input_validation'):
        validate_input(event)
    
    # Sub-segment for authentication
    with xray_recorder.in_subsegment('authentication'):
        credentials = get_firebolt_credentials()
    
    # Sub-segment for database operation
    with xray_recorder.in_subsegment('database_operation'):
        result = execute_firebolt_operation(event, credentials)
    
    # Annotate the trace with additional metadata
    xray_recorder.current_subsegment().put_annotation('operation_type', event['operation_type'])
    xray_recorder.current_subsegment().put_annotation('table_name', event['table_name'])
    xray_recorder.current_subsegment().put_metadata('record_count', len(event['records']))
    
    return result
```

### CloudWatch Metrics & Alarms

Key operational metrics are collected and monitored through CloudWatch:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def emit_operation_metrics(operation_type, table_name, duration_ms, record_count, success):
    """Emit custom metrics to CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='RevOpsAI/Firebolt',
        MetricData=[
            {
                'MetricName': 'OperationDuration',
                'Dimensions': [
                    {'Name': 'OperationType', 'Value': operation_type},
                    {'Name': 'TableName', 'Value': table_name}
                ],
                'Value': duration_ms,
                'Unit': 'Milliseconds'
            },
            {
                'MetricName': 'RecordCount',
                'Dimensions': [
                    {'Name': 'OperationType', 'Value': operation_type},
                    {'Name': 'TableName', 'Value': table_name}
                ],
                'Value': record_count,
                'Unit': 'Count'
            },
            {
                'MetricName': 'OperationSuccess',
                'Dimensions': [
                    {'Name': 'OperationType', 'Value': operation_type},
                    {'Name': 'TableName', 'Value': table_name}
                ],
                'Value': 1 if success else 0,
                'Unit': 'Count'
            }
        ]
    )
```

Example of CloudWatch alarm configuration in Terraform:

```hcl
resource "aws_cloudwatch_metric_alarm" "firebolt_write_errors" {
  alarm_name          = "firebolt-write-errors-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "OperationSuccess"
  namespace           = "RevOpsAI/Firebolt"
  period              = "60"
  statistic           = "SampleCount"
  threshold           = "3"
  alarm_description   = "This metric monitors Firebolt write operation failures"
  dimensions = {
    OperationType = "INSERT"
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

### Structured Logging

The framework implements consistent structured logging across all components:

```python
import logging
import json
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_event(event_type, message, **kwargs):
    """Log a structured event with consistent format"""
    log_data = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "message": message,
        **kwargs
    }
    
    logger.info(json.dumps(log_data))
    return log_data

# Example usage
log_event(
    "database_operation",
    "Executing Firebolt query",
    operation_type="INSERT",
    table_name="deal_quality_scores",
    record_count=25,
    request_id=context.aws_request_id
)
```

### Service Health Dashboard

A real-time service health dashboard is provided for monitoring system status:

```python
class ServiceHealthCheck:
    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.s3_client = boto3.client('s3')
        self.bedrock_client = boto3.client('bedrock')
        self.firebolt_connection = FireboltConnection()
    
    def check_all_services(self):
        """Check health of all dependent services"""
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "overall_status": self._get_overall_status(),
            "components": {
                "lambda": self._check_lambda_health(),
                "s3": self._check_s3_health(),
                "bedrock": self._check_bedrock_health(),
                "firebolt": self._check_firebolt_health(),
            }
        }
    
    def _get_overall_status(self):
        # Determine overall status based on component health
        all_statuses = [component["status"] for component in self.check_all_components().values()]
        if "DOWN" in all_statuses:
            return "DOWN"
        elif "DEGRADED" in all_statuses:
            return "DEGRADED"
        else:
            return "HEALTHY"
```

### Performance Profiling

Automated performance profiling identifies optimization opportunities:

```python
from functools import wraps
import time
import cProfile
import io
import pstats

def profile_function(func):
    """Profile function execution time and resource usage"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Simple timing
        start_time = time.time()
        
        # Detailed profiling
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000
        
        # Format profiling stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        profile_data = s.getvalue()
        
        # Log performance data
        log_event(
            "performance_profile",
            f"Function {func.__name__} execution profile",
            function=func.__name__,
            duration_ms=duration_ms,
            profile_data=profile_data
        )
        
        return result
    return wrapper
```

## Troubleshooting

### Common Issues

* **Deployment Failures**
  * Check AWS IAM permissions
  * Verify connectivity to AWS services
  * Ensure secrets are properly formatted in the secrets.json file

* **Agent Execution Errors**
  * Check CloudWatch logs for Lambda function errors
  * Verify knowledge base ingestion completed successfully
  * Ensure Bedrock model access is configured correctly

* **Integration Issues**
  * Validate webhook URLs and authentication
  * Check API rate limits on external services
  * Verify network connectivity from AWS to external endpoints

### Logging and Monitoring

* **CloudWatch Logs**
  * All Lambda functions write logs to CloudWatch
  * Log groups follow the pattern `/aws/lambda/revops-ai-framework-*`

* **Deployment Logs**
  * Check `deployment/deployment.log` for detailed deployment information

* **Execution Tracking**
  * All flow executions are recorded in the `revops_ai_executions` table in Firebolt
