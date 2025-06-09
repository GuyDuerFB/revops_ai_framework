# Deploy Schema-Aware Bedrock Agent for RevOps AI Framework

## Prerequisites

✅ **You already have:**
- Lambda function deployed and working
- Firebolt credentials in AWS Secrets Manager
- AWS Console access
- Schema knowledge document (`schema_knowledge.md`)

## Step 1: Update Agent Configuration

Before deploying, update the configuration file with your actual values:

### 1.1 Get Your Lambda Function ARN
```bash
# In AWS Console: Go to Lambda → Your Function → Copy the Function ARN
# Format: arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME
```

### 1.2 Update Configuration
In the agent configuration JSON, replace:
- `REGION` → Your AWS region (e.g., `eu-north-1`)
- `ACCOUNT` → Your AWS account ID
- `YOUR_LAMBDA_FUNCTION_NAME` → Your actual Lambda function name

## Step 2: Create Knowledge Base

### 2.1 Navigate to Bedrock Knowledge Bases
1. Go to **AWS Console** → **Amazon Bedrock**
2. In the left sidebar, click **Knowledge bases**
3. Click **Create knowledge base**

### 2.2 Basic Configuration
1. **Knowledge base name**: `revops-firebolt-schema`
2. **Knowledge base description**: `Comprehensive schema knowledge for Firebolt data warehouse tables and analysis patterns`
3. **IAM role**: Create new role or select existing with Bedrock permissions

### 2.3 Configure Data Source
1. **Data source name**: `schema-documentation`
2. **Data source connector**: Choose **Upload files**
3. **File upload**: Upload the `schema_knowledge.md` file
4. **Chunking strategy**: Select **Default**

### 2.4 Complete Knowledge Base Creation
1. Click **Create knowledge base**
2. Wait for indexing to complete (status will change to **Available**)

## Step 3: Create Bedrock Agent via AWS Console

### 3.1 Navigate to Bedrock
1. Go to **AWS Console** → **Amazon Bedrock**
2. In the left sidebar, click **Agents**
3. Click **Create Agent**

### 3.2 Basic Configuration
1. **Agent name**: `revops-data-agent`
2. **Agent description**: `Schema-aware data agent for RevOps analysis with chunking support for large result sets`
3. **Foundation model**: Select **Claude 3 Sonnet**
4. **Agent instructions**: Copy the entire instruction text from `instructions.md`
5. Click **Next**

### 3.3 Add Knowledge Base
1. Under **Knowledge bases**, click **Add knowledge base**
2. Select the `revops-firebolt-schema` knowledge base you created earlier
3. Click **Add**

### 3.4 Add Action Group
1. Click **Add action group**
2. **Action group name**: `firebolt-query`
3. **Action group type**: **Define with function details**
4. **Lambda function**: Select your deployed Lambda function
5. **Action group invocation**: Choose **Return control**
6. **Action group description**: `Execute SQL queries against Firebolt data warehouse with chunking support for large result sets`

### 3.5 Define API Schema
1. **API Schema**: Choose **Define with in-line OpenAPI schema editor**
2. Copy and paste the OpenAPI schema from `openapi_schema.json`
3. Click **Add action group**

### 2.5 Advanced Prompts (Optional)
1. **Advanced prompts**: Toggle **ON**
2. **Pre-processing**: Add this prompt:

```
You are a data retrieval agent that specializes in building SQL queries for Firebolt. When users ask questions about data, follow these steps:

1. Determine which tables and columns are needed to answer the question
2. Build a SQL query using proper JOINs, WHERE clauses, and aggregations
3. Explain your query approach before executing it
4. Execute the query using the firebolt-query action group
5. Format and explain the results

For large result sets, your response will be chunked. Inform users about the chunking and guide them on how to request additional chunks if needed.
```

3. **Orchestration**: Add this prompt:

```
When working with large result sets that are chunked:


1. Once agent is created, go to **Aliases** tab
2. Click **Create alias**
3. **Alias name**: `production`
4. **Description**: `Production version of schema-aware agent`

## Step 5: Test the Agent

### 4.1 Use AWS Console Test Interface
1. Go to your agent → **Test** tab
2. Try these test requests:

**Test 1: Simple Schema Understanding**
```
Get me the last 5 closed-lost opportunities with account names and closure reasons
```

**Expected Agent Behavior:**
- Should understand this needs opportunity_d + salesforce_account_d tables
- Should build proper JOIN statement
- Should filter for stage_name = 'Closed Lost'
- Should include closure reasons

**Test 2: Business Logic Application**
```
Show me high-touch accounts that have had opportunities in the last 6 months, excluding PLG customers
```

**Expected Agent Behavior:**
- Should apply account_tier = 'High-Touch' filter
- Should exclude sf_account_type_custom = 'PLG Customer'
- Should use proper date filtering
- Should JOIN opportunities with accounts

**Test 3: Usage Analysis with Chunking**
```
Find all accounts with usage anomalies - show accounts that used more than 100 engine hours in the last 30 days
```

**Expected Agent Behavior:**
- Should query consumption_daily_d table
- Should apply date filter for last 30 days
- Should aggregate engine_hours by account
- Should JOIN with account info for context
- Should handle chunking if result set is large

### 4.2 Expected Response Format

Your agent should build queries like:

```sql
-- For Test 1:
SELECT 
    sf.sf_account_name,
    o.opportunity_name,
    o.closed_at_date,
    o.closed_won_lost_reason
FROM opportunity_d o
JOIN salesforce_account_d sf ON sf.sf_account_id = o.sf_account_id
WHERE o.stage_name = 'Closed Lost'
ORDER BY o.closed_at_date DESC
LIMIT 5
```

And call your Lambda with:
```json
{
  "query": "SELECT sf.sf_account_name, o.opportunity_name...",
  "secret_name": "firebolt-api-credentials",
  "region_name": "eu-north-1",
  "max_rows_per_chunk": 1000,
  "chunk_index": 0
}
```

## Step 5: Verify Chunking Support

Test the agent's ability to handle large result sets:

### ✅ Chunking Tests

1. **"Get all opportunities from the last 12 months with full details"**
   - Should detect this could be a large result set
   - Should mention chunking in its response
   - Should return the first chunk with metadata
   - Should explain how to request additional chunks

2. **"Continue with the next chunk of data"**
   - Should retrieve the next chunk using chunk_index=1
   - Should maintain context between chunks

3. **"Show me account usage for all enterprise customers over the past 6 months"**
   - Should recognize this as a large result set
   - Should use chunking automatically
   - Should explain the total rows and chunks available

## Step 6: Verify Schema Awareness

Test the agent's schema understanding with these questions:

### ✅ Schema Intelligence Tests

1. **"What tables would I need to join to get opportunity data with account information?"**
   - Should mention opportunity_d and salesforce_account_d
   - Should explain the JOIN on sf_account_id

2. **"How do I filter for high-touch accounts only?"**
   - Should mention account_tier = 'High-Touch'

3. **"What's the difference between closed_at_date and created_at_ts?"**
   - Should explain these are different timestamps for different events

4. **"Build a query for A1 analysis"**
   - Should understand A1 = At-risk account identification
   - Should build appropriate filters and JOINs

## Step 7: Configure Your Secret Name

Make sure to update your test requests with your actual secret name:

```
Get me closed-lost opportunities using secret name "firebolt-credentials"
```

Or set a default in your agent configuration.

## Troubleshooting

### Common Issues

#### Error: "Resource not found"
- **Cause**: Lambda function doesn't exist or IAM permissions are insufficient
- **Solution**: Double-check Lambda ARN and IAM roles

#### Error: "Invalid OpenAPI schema"
- **Cause**: OpenAPI schema has syntax errors
- **Solution**: Validate schema using an OpenAPI validator
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com
```

### ❌ "Response payload size exceeded" error
- **Check**: The chunking parameter settings in the query
- **Fix**: Reduce max_rows_per_chunk value or add more filtering to the query

### ❌ "Secret not found" errors
- **Check**: Secret name is correct and accessible from Lambda
- **Fix**: Verify secret exists and Lambda has permissions

## Success Criteria

✅ **Agent is working correctly when:**
- Builds proper SQL with JOINs based on requests
- Applies business logic filters (high-touch, exclude PLG, etc.)
- Responds with actual data from your Firebolt instance
- Explains its query logic before executing
- Handles different analysis types (A1-A6) appropriately
- Properly chunks large result sets and guides users on navigating chunks

## Next Steps

Once your schema-aware agent is working:
1. **Test complex scenarios** with multiple table JOINs
2. **Add more tools** (Slack, Gong, Salesforce) using same pattern
3. **Create Step Functions workflow** for full orchestration
4. **Build analysis agents** that consume this data

Your foundation is now **truly intelligent** - it understands your business data model, handles large result sets efficiently, and can adapt to any data request!
