# IXIS Data Check Guide

## Overview
This guide provides comprehensive instructions for checking IXIS deal data in the Firebolt data warehouse using the existing Lambda function infrastructure.

## Firebolt Query Lambda Function

### Function Location
- **Main Function**: `/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/V3/tools/firebolt/query_lambda/lambda_function.py`
- **Function Name**: `query_fire`
- **Handler**: `lambda_handler`

### Function Capabilities
- Executes SQL queries against Firebolt data warehouse
- Supports both direct invocation and Bedrock Agent format
- Handles OAuth authentication automatically
- Returns structured JSON results
- Includes error handling and tracing

### Configuration Requirements
The Lambda function requires these environment variables:
- `FIREBOLT_ACCOUNT_NAME` - Your Firebolt account name
- `FIREBOLT_ENGINE_NAME` - Your Firebolt engine name
- `FIREBOLT_DATABASE` - Your Firebolt database name
- `FIREBOLT_CREDENTIALS_SECRET` - AWS Secret Manager secret name containing client_id and client_secret
- `AWS_REGION` - AWS region (default: us-east-1)

## IXIS Data Search Strategy

### Target Tables
1. **opportunity_d** - Opportunity/deal data
2. **gong_call_f** - Gong call recordings and metadata
3. **salesforce_account_d** - Salesforce account information

### Search Criteria
- Account names containing "IXIS"
- Opportunity names containing "IXIS"
- Call titles containing "IXIS"
- Attendees containing "IXIS"
- Parent account names containing "IXIS"
- Owner names containing "IXIS"

## Test Queries

### 1. IXIS Opportunities Check
```sql
SELECT 
    account_name,
    opportunity_name,
    opportunity_id,
    stage_name,
    close_date,
    amount,
    probability,
    created_date,
    owner_name
FROM opportunity_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(opportunity_name) LIKE '%IXIS%'
ORDER BY created_date DESC
LIMIT 20;
```

### 2. IXIS Gong Calls Check
```sql
SELECT 
    account_name,
    call_title,
    call_date,
    call_duration_minutes,
    host_name,
    attendees,
    opportunity_name,
    call_type,
    created_date
FROM gong_call_f 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(call_title) LIKE '%IXIS%'
   OR UPPER(attendees) LIKE '%IXIS%'
ORDER BY call_date DESC
LIMIT 20;
```

### 3. IXIS Salesforce Accounts Check
```sql
SELECT 
    account_name,
    account_id,
    account_type,
    industry,
    account_owner,
    created_date,
    last_modified_date,
    parent_account_name,
    account_status
FROM salesforce_account_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(parent_account_name) LIKE '%IXIS%'
ORDER BY last_modified_date DESC
LIMIT 20;
```

### 4. IXIS Record Count Summary
```sql
SELECT 
    'opportunity_d' as table_name,
    COUNT(*) as ixis_record_count
FROM opportunity_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(opportunity_name) LIKE '%IXIS%'

UNION ALL

SELECT 
    'gong_call_f' as table_name,
    COUNT(*) as ixis_record_count
FROM gong_call_f 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(call_title) LIKE '%IXIS%'
   OR UPPER(attendees) LIKE '%IXIS%'

UNION ALL

SELECT 
    'salesforce_account_d' as table_name,
    COUNT(*) as ixis_record_count
FROM salesforce_account_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(parent_account_name) LIKE '%IXIS%'

ORDER BY ixis_record_count DESC;
```

## Testing Methods

### Method 1: Direct Lambda Invocation via AWS CLI
```bash
# Run the automated test script
./test_ixis_data.sh [lambda_function_name]

# Or manually invoke with specific query
aws lambda invoke \
    --function-name "your-firebolt-query-lambda" \
    --payload '{"query": "SELECT * FROM opportunity_d WHERE UPPER(account_name) LIKE '\''%IXIS%'\'' LIMIT 10;"}' \
    --cli-binary-format raw-in-base64-out \
    response.json
```

### Method 2: Using the Python Test Script
```python
# Run the comprehensive test
python3 ixis_data_check.py
```

### Method 3: Direct Function Call
```python
import sys
sys.path.append('/path/to/query_lambda')
from lambda_function import query_fire

# Test a specific query
result = query_fire(query="SELECT * FROM opportunity_d WHERE UPPER(account_name) LIKE '%IXIS%' LIMIT 10;")
print(result)
```

### Method 4: Through Bedrock Agent
If using through the Bedrock Agent system:
```json
{
  "actionGroup": "firebolt_query",
  "action": "query_fire",
  "parameters": {
    "query": "SELECT * FROM opportunity_d WHERE UPPER(account_name) LIKE '%IXIS%' LIMIT 10;"
  }
}
```

## Expected Response Format

### Success Response
```json
{
  "success": true,
  "results": [
    {
      "account_name": "IXIS Example Corp",
      "opportunity_name": "IXIS Data Platform Deal",
      "opportunity_id": "12345",
      "stage_name": "Negotiation",
      "close_date": "2024-03-15",
      "amount": 250000,
      "probability": 75,
      "created_date": "2024-01-10",
      "owner_name": "John Smith"
    }
  ],
  "columns": [
    {"name": "account_name", "type": "string"},
    {"name": "opportunity_name", "type": "string"},
    {"name": "opportunity_id", "type": "string"},
    {"name": "stage_name", "type": "string"},
    {"name": "close_date", "type": "date"},
    {"name": "amount", "type": "number"},
    {"name": "probability", "type": "number"},
    {"name": "created_date", "type": "date"},
    {"name": "owner_name", "type": "string"}
  ],
  "row_count": 1,
  "column_count": 9
}
```

### Error Response
```json
{
  "success": false,
  "error": "Authentication failed",
  "message": "Failed to execute query against Firebolt",
  "results": [],
  "columns": []
}
```

## Files Created

1. **`ixis_data_check.py`** - Python script for comprehensive testing
2. **`ixis_test_queries.sql`** - SQL queries for manual testing
3. **`ixis_lambda_test.json`** - JSON test cases for Lambda function
4. **`test_ixis_data.sh`** - Bash script for automated AWS CLI testing
5. **`IXIS_DATA_CHECK_GUIDE.md`** - This documentation file

## Troubleshooting

### Common Issues

1. **Authentication Error**
   - Check AWS credentials are configured
   - Verify FIREBOLT_CREDENTIALS_SECRET exists in AWS Secrets Manager
   - Ensure secret contains valid client_id and client_secret

2. **Table Not Found**
   - Verify table names match your Firebolt schema
   - Check database name in environment variables
   - Ensure engine has access to the specified database

3. **Permission Denied**
   - Lambda execution role needs secretsmanager:GetSecretValue permission
   - Firebolt credentials need appropriate database permissions

4. **Timeout Errors**
   - Increase Lambda timeout settings
   - Optimize queries with appropriate LIMIT clauses
   - Check Firebolt engine status

### Query Optimization Tips

1. **Use LIMIT** - Always limit results for testing
2. **Case Insensitive Search** - Use UPPER() for consistent matching
3. **Index Columns** - Search on indexed columns when possible
4. **Specific Date Ranges** - Add date filters to improve performance

## Next Steps

1. **Run the Count Summary Query First** - This will give you an overview of how much IXIS data exists
2. **Review Individual Tables** - Use the specific table queries to examine data quality
3. **Analyze Results** - Look for patterns in account names, opportunity stages, call frequency
4. **Expand Search** - If needed, modify queries to search additional fields or related tables
5. **Create Custom Queries** - Based on findings, create more specific queries for detailed analysis

## Security Considerations

- All queries are executed with the permissions of the Firebolt user credentials
- Sensitive data should be handled according to your organization's policies
- Test queries return limited results to avoid data exposure
- Consider using parameterized queries for production use

## Support

For issues with:
- **Lambda Function**: Check CloudWatch logs for detailed error messages
- **Firebolt Connection**: Verify credentials and network connectivity
- **Query Syntax**: Refer to Firebolt SQL documentation
- **AWS Integration**: Check IAM permissions and resource configurations