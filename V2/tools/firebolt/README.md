# Firebolt Service Components

This directory contains Lambda functions and supporting code for interacting with the Firebolt data warehouse.

## Components

### 1. Writer Lambda

The Firebolt Writer Lambda handles all data write operations to Firebolt, including inserts, updates, and deletes.

#### Key Features

- **Format-aware SQL generation**: Automatically formats values appropriately for SQL insertion, including proper handling of JSON as TEXT fields
- **Connection management**: Secure OAuth token retrieval and connection handling with retry logic
- **Error handling**: Robust error handling with detailed response codes and logging
- **API compatibility**: Compatible with AWS Bedrock Agent function calling format
- **Raw SQL Support**: Sends raw SQL queries with Content-Type: text/plain for maximum compatibility with Firebolt's API

#### Special Support for RevOps AI Insights

The writer Lambda includes specialized support for the `revops_ai_insights` table through the following functions:

- `validate_insight_data()`: Validates insight data against the schema requirements
- `generate_insight_id()`: Creates unique insight IDs based on timestamp and UUID
- `write_insight()`: Specialized function for insight-specific write operations with validation

#### Invoking the Lambda

**Direct Invocation**:
```json
{
  "operation": "insight",
  "query_type": "insert|update|delete",
  "data": {
    "insight_id": "INS-20240601-123456",
    "category": "deal_quality",
    "type": "risk_assessment",
    "source": "consumption_analysis",
    "title": "Potential churn risk detected",
    "description": "Customer usage has declined by 35% over the past 30 days",
    "status": "open",
    "priority": "high",
    "score": 0.85,
    "metadata": {"account_id": "ACT-12345", "region": "EMEA"},
    "attributes": {"decline_percent": 35, "previous_baseline": 1250}
  },
  "where_clause": "insight_id = 'INS-20240601-123456'"
}
```

**Bedrock Agent Invocation**:
```json
{
  "actionGroup": "firebolt_writer",
  "action": "write_insight",
  "body": {
    "parameters": {
      "query_type": "insert|update|delete",
      "data": { /* insight data */ },
      "where_clause": "insight_id = 'INS-20240601-123456'"
    }
  }
}
```

### 2. Reader Lambda

The Firebolt Reader Lambda handles all data read operations from Firebolt.

#### Key Features

- **Query optimization**: Automatically optimizes common query patterns
- **Connection pooling**: Efficient connection management
- **Result pagination**: Handles large result sets with pagination
- **Advanced filtering**: Supports complex filtering operations

### 3. Metadata Lambda

The Firebolt Metadata Lambda provides schema and catalog information about Firebolt databases, tables, and columns.

#### Key Features

- **Schema discovery**: Retrieve table and column information from Firebolt
- **Retry logic**: Implements exponential backoff and multiple retry attempts
- **Endpoint flexibility**: Tries multiple endpoint formats to handle different Firebolt configurations
- **Error handling**: Detailed error reporting and metrics for debugging
- **Raw SQL Support**: Sends raw SQL queries with Content-Type: text/plain for maximum compatibility with Firebolt's API

## Firebolt Service Components
This directory contains Lambda functions and supporting code for interacting with the Firebolt data warehouse.

### Components

1. Writer Lambda
The Firebolt Writer Lambda handles all data write operations to Firebolt, including inserts, updates, and deletes.

#### Key Features

- Format-aware SQL generation: Automatically formats values appropriately for SQL insertion, including proper handling of JSON as TEXT fields
- Connection management: Secure OAuth token retrieval and connection handling
- Error handling: Robust error handling with detailed response codes
- API compatibility: Compatible with AWS Bedrock Agent function calling format

#### Special Support for RevOps AI Insights
The writer Lambda includes specialized support for the revops_ai_insights table through the following functions:

validate_insight_data(): Validates insight data against the schema requirements
generate_insight_id(): Creates unique insight IDs based on timestamp and UUID
write_insight(): Specialized function for insight-specific write operations with validation

#### Invoking the Lambda

Direct Invocation:

```json
{
  "operation": "insight",
  "query_type": "insert|update|delete",
  "data": {
    "insight_id": "insight_abc123-def456",
    "lead_id": "lead_789xyz",
    "sf_account_id": "0013000001XYZ123",
    "sf_opportunity_id": "0063000001ABC456",
    "customer_id": "cust_enterprise_001",
    "contact_id": "contact_primary_001",
    "insight_category": "churn_risk",
    "insight_type": "risk_assessment",
    "insight_subtype": "usage_decline",
    "source_agent": "consumption_analysis",
    "workflow_name": "churn_prediction_workflow",
    "workflow_execution_id": "exec_20250630_001",
    "priority_level": "high",
    "status": "open",
    "assigned_to": "csm_jane_doe",
    "insight_title": "High churn risk detected",
    "insight_description": "Customer usage has declined by 45% over past 30 days",
    "insight_payload": "{\"decline_pct\": 45, \"features_affected\": [\"api\", \"dashboard\"]}",
    "evidence_data": "{\"api_calls_30d\": 1250, \"baseline\": 2270}",
    "confidence_score": 0.85,
    "impact_score": 0.92,
    "urgency_score": 0.78,
    "geographic_region": "north_america",
    "customer_segment": "enterprise",
    "deal_amount": 125000.00,
    "customer_arr": 450000.00,
    "usage_metric_value": 0.55,
    "recommended_actions": "[\"schedule_check_in\", \"escalate_to_csm\"]",
    "data_version": "v2.1"
  },
  "where_clause": "insight_id = 'insight_abc123-def456'"
}
```

Bedrock Agent Invocation:

```json
{
  "actionGroup": "firebolt_writer",
  "action": "write_insight",
  "body": {
    "parameters": {
      "query_type": "insert|update|delete",
      "data": { /* insight data */ },
      "where_clause": "insight_id = 'insight_abc123-def456'"
    }
  }
}
```

####  2. Reader Lambda
The Firebolt Reader Lambda handles all data read operations from Firebolt.

#### Key Features

- Query optimization: Automatically optimizes common query patterns
- Connection pooling: Efficient connection management
Result pagination: Handles large result sets with pagination
Advanced filtering: Supports complex filtering operations

#### 3. Metadata Lambda
The Firebolt Metadata Lambda provides schema and catalog information.

#### RevOps AI Insights Table Schema

The revops_ai_insights table provides a centralized storage system for AI-generated insights across agents, with comprehensive business context and workflow tracking.

#### Schema Definition

```sql
CREATE TABLE IF NOT EXISTS revops_ai_insights (
    -- Primary Identifiers
    insight_id TEXT, -- Unique identifier for the insight
    lead_id TEXT, -- Unique identifier for the lead
    sf_account_id TEXT, -- Salesforce Account ID format (18-character alphanumeric)
    sf_opportunity_id TEXT, -- Salesforce Opportunity ID format (18-character alphanumeric)
    customer_id TEXT, -- Unique identifier for the customer
    contact_id TEXT, -- Unique identifier for the contact
    
    -- Classification (Required)
    insight_category TEXT NOT NULL, -- Category of the insight
    insight_type TEXT NOT NULL, -- Type of the insight
    insight_subtype TEXT, -- Subtype of the insight
    source_agent TEXT NOT NULL, -- Source agent that generated the insight
    
    -- Workflow Management (Required)
    workflow_name TEXT NOT NULL, -- Name of the workflow
    workflow_execution_id TEXT NOT NULL, -- Unique identifier for the workflow execution
    priority_level TEXT NOT NULL, -- Priority level of the insight
    status TEXT NOT NULL, -- Status of the insight
    assigned_to TEXT, -- User assigned to the insight
    
    -- Content (Required)
    insight_title TEXT NOT NULL, -- Title of the insight
    insight_description TEXT NOT NULL, -- Description of the insight
    
    -- Payload Data (JSON as TEXT)
    insight_payload TEXT, -- Payload data of the insight
    evidence_data TEXT, -- Evidence data of the insight
    
    -- Scoring Metrics
    confidence_score DOUBLE PRECISION, -- Confidence score of the insight
    impact_score DOUBLE PRECISION, -- Impact score of the insight
    urgency_score DOUBLE PRECISION, -- Urgency score of the insight
    
    -- Temporal Tracking
    created_at TIMESTAMP NOT NULL, -- Timestamp when the insight was created
    event_timestamp TIMESTAMP, -- Timestamp of the event that triggered the insight
    expires_at TIMESTAMP, -- Timestamp when the insight expires
    acknowledged_at TIMESTAMP, -- Timestamp when the insight was acknowledged
    resolved_at TIMESTAMP, -- Timestamp when the insight was resolved
    last_updated_at TIMESTAMP, -- Timestamp when the insight was last updated
    
    -- Business Context
    tags TEXT,  -- JSON array stored as TEXT
    source_system TEXT, -- Source system of the insight
    geographic_region TEXT, -- Geographic region of the insight
    customer_segment TEXT, -- Customer segment of the insight
    
    -- Financial Metrics
    deal_amount DOUBLE PRECISION, -- Deal amount of the insight
    customer_arr DOUBLE PRECISION, -- Customer ARR of the insight
    usage_metric_value DOUBLE PRECISION, -- Usage metric value of the insight
    
    -- Action Tracking
    recommended_actions TEXT,  -- JSON array stored as TEXT
    actions_taken TEXT,  -- JSON array stored as TEXT
    outcome_status TEXT,  -- Outcome status of the insight  
    outcome_notes TEXT, -- Outcome notes of the insight
    
    -- Data Lineage
    data_version TEXT, -- Data version of the insight
    source_query_hash TEXT, -- Source query hash of the insight
);
PRIMARY INDEX (insight_id)
```

#### Validation Rules

The Writer Lambda enforces the following validation rules for insights:

##### Required Fields:

insight_category, insight_type, source_agent
workflow_name, workflow_execution_id
priority_level, status
insight_title, insight_description
created_at


##### Categorical Fields:

insight_category: ['deal_quality', 'consumption_pattern', 'churn_risk', 'growth_opportunity', 'engagement', 'product_usage']
insight_type: ['risk_assessment', 'opportunity', 'anomaly', 'trend', 'recommendation', 'prediction']
source_agent: ['consumption_analysis', 'conversation_analysis', 'crm_data', 'usage_metrics', 'manual_entry']
status: ['open', 'in_progress', 'resolved', 'dismissed', 'escalated']
priority_level: ['critical', 'high', 'medium', 'low']
geographic_region: ['north_america', 'europe', 'asia_pacific', 'latin_america']
customer_segment: ['enterprise', 'mid_market', 'smb', 'startup']


##### Numeric Fields:

confidence_score: Float between 0.0 and 1.0
impact_score: Float between 0.0 and 1.0
urgency_score: Float between 0.0 and 1.0
deal_amount: Positive number representing deal value
customer_arr: Positive number representing Annual Recurring Revenue
usage_metric_value: Context-dependent metric value


##### Business Identifiers:

sf_account_id: Salesforce Account ID format (18-character alphanumeric)
sf_opportunity_id: Salesforce Opportunity ID format (18-character alphanumeric)
workflow_execution_id: Unique execution identifier for tracking

### Agent Integration Pattern

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

Typical agent flow:
1. **Data Analysis Agent** creates initial insights from data analysis with status="open"
2. **Decision Agent** enriches insights with recommendations and sets status="in_progress"
3. **Execution Agent** implements actions and updates with action_results, sets status="resolved"
