# Firebolt Query Executor Tool

## Overview

This tool provides schema-aware SQL query execution capabilities for the RevOps AI Framework's Data Agent. It interfaces with the Firebolt data warehouse to retrieve, process, and format data according to the agent's requests.

## Key Features

- **Schema-Aware Query Execution**: Processes SQL queries against the Firebolt data warehouse
- **Chunking Strategy**: Handles large result sets through efficient chunking mechanism
- **Secure Authentication**: Uses AWS Secrets Manager for secure credential management
- **API Region Configuration**: Supports specifying Firebolt API region for optimal connectivity
- **Error Handling**: Comprehensive error handling and reporting

## Technical Implementation

### Query Execution Flow

1. The Data Agent constructs a SQL query based on the business request
2. The query is sent to this tool with proper authentication parameters
3. The tool executes the query against the Firebolt database
4. Results are processed and chunked if necessary
5. The response, with appropriate metadata, is returned to the calling agent

### API Endpoint Structure

The tool uses the following API endpoint structure to connect to Firebolt:

```
https://{account_name}-firebolt.api.{api_region}.app.firebolt.io?engine={engine_name}&database={database}
```

This represents an improvement over the previous endpoint structure, fixing the "Device or resource busy" error in AWS Lambda and ensuring reliable data retrieval across different environments. The structure has been validated to work with the Firebolt API in production scenarios.

### Chunking Implementation

For large result sets that would exceed Lambda's payload limits:

1. Results are automatically split into configurable chunks
2. Each chunk contains positional metadata (chunk_index, total_chunks)
3. The first chunk (index 0) also contains query metadata for subsequent requests
4. No intermediate storage is used, improving performance and reducing complexity

## Configuration Parameters

| Parameter | Description | Default | Required |
|-----------|-------------|---------|----------|
| `query` | SQL query to execute | - | Yes |
| `secret_name` | Name of AWS Secrets Manager secret containing Firebolt credentials | firebolt-api-credentials | No |
| `region_name` | AWS region for Secrets Manager | eu-north-1 | No |
| `api_region` | Firebolt API region | us-east-1 | No |
| `chunk_index` | For chunked results, the index of chunk to retrieve | 0 | No |
| `max_rows_per_chunk` | Maximum number of rows per chunk | 1000 | No |

> **Note**: The parameters have been standardized across the codebase for consistency. Users only need to provide the SQL query, with all other parameters using sensible defaults.

## Authentication

The tool expects the following credentials to be stored in AWS Secrets Manager:

```json
{
  "username": "firebolt_username",
  "password": "firebolt_password",
  "account_name": "firebolt_account_name",
  "engine_name": "firebolt_engine_name", 
  "database": "firebolt_database_name"
}
```

## Error Handling

The tool provides structured error responses with:
- Error code
- Human-readable error message
- Debugging information when applicable
- Suggestions for resolving common issues

## Usage Example

```json
// Request
{
  "query": "SELECT * FROM consumption_daily_d WHERE consumption_date >= CURRENT_DATE - INTERVAL '30 DAYS'",
  "secret_name": "firebolt-api-credentials",
  "region_name": "eu-north-1",
  "api_region": "us-east-1",
  "chunk_index": 0,
  "max_rows_per_chunk": 1000
}

// Response (chunked)
{
  "success": true,
  "error": null,
  "chunked": true,
  "chunk_index": 0,
  "total_chunks": 3,
  "total_rows": 2850,
  "rows_per_chunk": 1000,
  "columns": ["consumption_date", "sf_account_id", "engine_hours", "query_count", "data_scanned_bytes"],
  "results": [...],  // First 1000 rows
  "query_info": {
    "query": "SELECT * FROM consumption_daily_d WHERE consumption_date >= CURRENT_DATE - INTERVAL '30 DAYS'",
    "secret_name": "firebolt-api-credentials",
    "region_name": "eu-north-1",
    "api_region": "us-east-1"
  }
}
```
