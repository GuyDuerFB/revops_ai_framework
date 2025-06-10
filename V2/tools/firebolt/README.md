# Firebolt Service Components

This directory contains Lambda functions and supporting code for interacting with the Firebolt data warehouse.

## Components

### 1. Writer Lambda

The Firebolt Writer Lambda handles all data write operations to Firebolt, including inserts, updates, and deletes.

#### Key Features

- **Format-aware SQL generation**: Automatically formats values appropriately for SQL insertion, including proper handling of JSON as TEXT fields
- **Connection management**: Secure OAuth token retrieval and connection handling
- **Error handling**: Robust error handling with detailed response codes
- **API compatibility**: Compatible with AWS Bedrock Agent function calling format

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

The Firebolt Metadata Lambda provides schema and catalog information.

## RevOps AI Insights Table Schema

The `revops_ai_insights` table provides a centralized storage system for AI-generated insights across agents.

### Schema Definition

```sql
CREATE TABLE IF NOT EXISTS revops_ai_insights (
    -- Identifiers
    insight_id VARCHAR NOT NULL,
    correlation_id VARCHAR,
    
    -- Classification
    insight_category VARCHAR NOT NULL,
    insight_type VARCHAR NOT NULL,
    source_agent VARCHAR NOT NULL,
    
    -- Source tracking
    agent_id VARCHAR,
    flow_id VARCHAR,
    
    -- Operational management
    insight_title VARCHAR NOT NULL,
    insight_description TEXT NOT NULL,
    status VARCHAR NOT NULL,
    priority_level VARCHAR,
    
    -- Content (JSON stored as TEXT)
    insight_payload TEXT,
    evidence_data TEXT,
    
    -- Scoring
    confidence_score FLOAT,
    impact_score FLOAT,
    urgency_score FLOAT,
    
    -- Temporal fields
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Analytical dimensions
    tags TEXT,  -- JSON array stored as TEXT
    
    -- Action tracking
    recommended_actions TEXT,  -- JSON array stored as TEXT
    actions_taken TEXT,  -- JSON array stored as TEXT
    
    PRIMARY KEY (insight_id)
);
```

### Validation Rules

The Writer Lambda enforces the following validation rules for insights:

1. **Required Fields**: insight_id (generated if not provided), category, type, source, title, description, status
2. **Categorical Fields**:
   - category: ['deal_quality', 'consumption_pattern', 'churn_risk', 'growth_opportunity', 'engagement', 'product_usage']
   - type: ['risk_assessment', 'opportunity', 'anomaly', 'trend', 'recommendation', 'prediction']
   - source: ['consumption_analysis', 'conversation_analysis', 'crm_data', 'usage_metrics', 'manual_entry']
   - status: ['open', 'in_progress', 'resolved', 'dismissed', 'escalated']
   - priority: ['critical', 'high', 'medium', 'low']
3. **Numeric Fields**:
   - score: Float between 0.0 and 1.0
   - confidence: Float between 0.0 and 1.0

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
