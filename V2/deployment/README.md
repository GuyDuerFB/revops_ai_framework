# RevOps AI Framework V2 - AWS Deployment

This directory contains scripts and configuration for deploying the RevOps AI Framework V2 to AWS. The deployment has been organized into a clear structure to make maintenance and updates easier.

## Directory Structure

```
/deployment/
├── README.md               # This file
├── deploy.py              # Symlink to scripts/deployment/deploy.py (main entry point)
├── validate_deployment.py # Symlink to scripts/utilities/validate_deployment.py
├── config.json            # Current deployment configuration
├── secrets.json           # Current deployment secrets (not in version control)
├── requirements.txt       # Python dependencies for deployment
│
├── config/                # Configuration templates and examples
│   ├── config_template.json
│   ├── secrets_template.json
│   ├── example_config.json
│   └── example_secrets.json
│
├── scripts/
│   ├── deployment/        # Core deployment scripts
│   │   ├── deploy.py             # Main deployment orchestrator
│   │   ├── lambda_deployer.py    # Lambda function deployment (includes Gong Lambda handling)
│   │   ├── knowledge_base_deployer.py  # Knowledge base deployment
│   │   ├── agent_deployer.py     # Agent deployment
│   │   └── delete_and_redeploy.py # Deletes and redeploys Lambda functions
│   │
│   ├── utilities/         # Helper scripts for deployment and maintenance
│   │   ├── validate_deployment.py    # Validates deployment configuration
│   │   ├── update_config.py          # Updates configuration settings
│   │   ├── update_lambda_env.py      # Updates Lambda environment variables
│   │   └── update_firebolt_metadata.py # Updates firebolt_metadata Lambda
│   │
│   └── testing/           # Scripts for testing deployed components
│       ├── test_firebolt_writer.py   # Tests the firebolt_writer Lambda
│       └── test_gong_lambda.py      # Tests the Gong call retrieval Lambda
│
└── backups/               # Backup files and deployment responses
    ├── config.json.YYYYMMDD
    ├── secrets.json.YYYYMMDD
    └── *_response.json    # Lambda test responses
```

## Prerequisites

1. **Environment Setup**
   ```bash
   # Create a Python virtual environment (if not already created)
   python3 -m venv venv
   
   # Activate the virtual environment
   source venv/bin/activate  # On macOS/Linux
   # OR
   # venv\Scripts\activate  # On Windows
   
   # Install required packages
   pip install -r requirements.txt
   ```

   - Python 3.9+ is required
   - AWS CLI must be installed and configured with profile `FireboltSystemAdministrator-740202120544`
   - **Important**: Always ensure your virtual environment is activated before running any deployment scripts

2. **Configuration**
   ```bash
   # Create configuration files from templates (first-time setup)
   cp config/config_template.json config.json
   cp config/secrets_template.json secrets.json
   ```
   
   - Update both files with your specific configuration
   - These files are excluded from version control (.gitignore) to protect sensitive information

## Deployment Workflow

### 1. Validate Configuration

Always validate your configuration before deployment:

```bash
# Check for common configuration issues
python validate_deployment.py
```

This script checks for:
- Required environment variables in Lambda configurations
- Required dependencies in Lambda function directories
- Valid source paths and configurations

### 2. Deployment Options

#### Complete Deployment

```bash
# Deploy all components
python deploy.py --deploy
```

#### Component Deployment

```bash
# Deploy specific components
python deploy.py --deploy lambda kb data_agent
```

Options:
- `lambda`: Deploy all Lambda functions
- `kb`: Deploy knowledge base
- `data_agent`: Deploy data agent
- `decision_agent`: Deploy decision agent
- `execution_agent`: Deploy execution agent

#### Specific Lambda Deployment

```bash
# Deploy a specific Lambda function (e.g., Gong retrieval)
python deploy.py --deploy lambda --lambda_name gong_retrieval

# Deploy another specific Lambda function
python deploy.py --deploy lambda --lambda_name firebolt_query
```

The `--lambda_name` parameter works with both deployment and testing:
```bash
# Deploy and test a specific Lambda function
python deploy.py --deploy lambda --test lambda --lambda_name gong_retrieval
```

### 3. Testing Components after deployment

```bash
# Test components after deployment
python deploy.py --test lambda data_agent

# Deploy and test in one command
python deploy.py --deploy lambda --test lambda
```

### 4. Special Cases

#### Gong Lambda Deployment

The Gong Lambda has special handling integrated into the main deployment script:

```bash
# Deploy only the Gong Lambda
python deploy.py --deploy lambda --lambda_name gong_retrieval
```

This approach handles setting the correct source directory path and AWS credential setup automatically.

## Component Details

### Lambda Functions

| Function Name | Description | Required Environment Variables | Dependencies |
|---------------|-------------|-------------------------------|---------------|
| firebolt_query | Executes SQL queries | FIREBOLT_ACCOUNT_NAME, FIREBOLT_ACCOUNT, FIREBOLT_ENGINE, FIREBOLT_DATABASE | - |
| firebolt_metadata | Retrieves schema info | FIREBOLT_ACCOUNT, FIREBOLT_ENGINE, FIREBOLT_DATABASE | requests |
| firebolt_writer | Executes write operations | FIREBOLT_ACCOUNT, FIREBOLT_ENGINE, FIREBOLT_DATABASE | - |
| gong_retrieval | Retrieves Gong call data | GONG_CREDENTIALS_SECRET | boto3 |
| webhook | Sends data to webhooks | - | requests |

### Knowledge Base

The knowledge base contains schema information for Firebolt tables and columns.

### Agents

| Agent | Description | Dependencies |
|-------|-------------|---------------|
| data_agent | Retrieves and analyzes data | firebolt_query, gong_retrieval, schema_lookup |
| decision_agent | Makes decisions based on data | data_agent |
| execution_agent | Executes actions | webhook |

## Important Notes

- **Environment Variables**: All Firebolt Lambda functions require specific environment variables to connect to Firebolt.
  - FIREBOLT_ACCOUNT_NAME and FIREBOLT_ACCOUNT must be the same value (e.g., 'firebolt-dwh')
  - FIREBOLT_ENGINE should match your Firebolt engine name (e.g., 'dwh_prod_analytics')
  - FIREBOLT_DATABASE should match your Firebolt database name (e.g., 'dwh_prod')

- **Dependencies**: Lambda functions require specific dependencies to function correctly.
  - firebolt_metadata requires the requests package
  - webhook requires the requests package

- **AWS Region**: All deployments use the AWS region specified in config.json (default: us-east-1)

- **API Formats**: 
  - Firebolt Lambda functions expect raw SQL queries with Content-Type: text/plain
  - Responses are returned in JSON format

- **Deployment Order**: The recommended deployment order is:
  1. Lambda functions (tools)
  2. Knowledge base
  3. Data agent
  4. Decision agent
  5. Execution agent

## Gong Lambda Deployment and Testing

The Gong Lambda function requires special handling due to its authentication requirements:

1. **AWS Secret Setup:**
   - Create a secret in AWS Secrets Manager named `gong-credentials` with two fields:
     - `access_key`: Your Gong API access key
     - `access_key_secret`: Your Gong API access key secret

2. **Deployment:**
   ```bash
   source venv/bin/activate
   python deploy.py --deploy lambda --lambda_name gong_retrieval
   python scripts/deployment/deploy_gong.py
   ```

3. **Testing:**
   ```bash
   source venv/bin/activate
   python scripts/testing/test_gong_lambda.py
   ```

4. **Authentication Notes:**
   - The Gong Lambda uses Basic Authentication with the credentials from AWS Secrets Manager
   - The Lambda accesses Gong's API endpoints via GET requests
   - Environment variable `GONG_CREDENTIALS_SECRET` must be set to `gong-credentials`

## Troubleshooting

### Common Issues

1. **ResourceConflictException during Lambda deployment**
   - The Lambda function is currently being updated
   - Solution: Wait a few minutes or use the delete_and_redeploy.py script

2. **Missing dependencies in Lambda functions**
   - Solution: Ensure each Lambda function directory has a requirements.txt file with necessary dependencies
   - Run validate_deployment.py to check for missing dependencies

3. **Environment variable configuration issues**
   - Solution: Check config.json for missing environment variables
   - Use update_lambda_env.py to update environment variables for deployed Lambdas

4. **Gong API 401 errors**
   - Verify that the AWS secret is correctly configured with valid Gong API credentials
