#!/bin/bash
# RevOps AI Framework - AWS Deployment Script
# This script handles the deployment of the RevOps AI Framework components using AWS CLI
# It replaces the previous Terraform-based deployment approach

set -e  # Exit on error

# Default values
CONFIG_FILE="config.json"
SECRETS_FILE="secrets.json"
DEPLOY_STATE_FILE="deploy_state.json"
ACTION=""

# Display help
function show_help {
    echo "RevOps AI Framework - AWS CLI Deployment"
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --config FILE     Use specified config file (default: config.json)"
    echo "  --secrets FILE    Use specified secrets file (default: secrets.json)"
    echo "  --deploy-data     Deploy the data agent and supporting infrastructure"
    echo "  --deploy-decision Deploy the decision agent and supporting infrastructure"
    echo "  --deploy-exec     Deploy the execution agent and supporting infrastructure"
    echo "  --deploy-all      Deploy all components"
    echo "  --help            Show this help message"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --secrets)
            SECRETS_FILE="$2"
            shift 2
            ;;
        --deploy-data)
            ACTION="deploy_data"
            shift
            ;;
        --deploy-decision)
            ACTION="deploy_decision"
            shift
            ;;
        --deploy-exec)
            ACTION="deploy_exec"
            shift
            ;;
        --deploy-all)
            ACTION="deploy_all"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if required files exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file '$CONFIG_FILE' not found."
    echo "Please copy config_template.json to $CONFIG_FILE and fill in the required values."
    exit 1
fi

if [ ! -f "$SECRETS_FILE" ]; then
    echo "Error: Secrets file '$SECRETS_FILE' not found."
    echo "Please copy secrets_template.json to $SECRETS_FILE and fill in the required values."
    exit 1
fi

# Display deployment information
echo "=== RevOps AI Framework AWS CLI Deployment ==="
echo "Config file: $CONFIG_FILE"
echo "Secrets file: $SECRETS_FILE"
echo "Deployment state: $DEPLOY_STATE_FILE"
echo "Action: $ACTION"
echo "=============================================="

# Check if an action was specified
if [ -z "$ACTION" ]; then
    echo "No action specified. Please use --deploy-data, --deploy-decision, --deploy-exec or --deploy-all"
    echo "Run $0 --help for more information"
    exit 1
fi

# Get AWS profile from config file
AWS_PROFILE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['aws_cli_profile'])")
if [ -z "$AWS_PROFILE" ]; then
    echo "Error: aws_cli_profile not set in $CONFIG_FILE"
    exit 1
fi

echo "Using AWS profile: $AWS_PROFILE"

# Create S3 bucket for knowledge base
function create_kb_bucket {
    # Generate a unique S3 bucket name with revops-ai-kb prefix
    local bucket_name="revops-ai-kb-$(date +%s)"
    echo "Creating S3 bucket for knowledge base: $bucket_name"
    
    aws s3api create-bucket \
        --bucket "$bucket_name" \
        --profile "$AWS_PROFILE"
        
    # Save bucket name to state file
    local state_data='{}'
    if [ -f "$DEPLOY_STATE_FILE" ]; then
        state_data=$(cat "$DEPLOY_STATE_FILE")
    fi
    
    echo "$state_data" | jq --arg bucket "$bucket_name" '.kb_bucket_name = $bucket' > "$DEPLOY_STATE_FILE"
    
    echo "Knowledge base S3 bucket created: $bucket_name"
    return 0
}

# Upload schema files to knowledge base bucket
function upload_kb_files {
    if [ ! -f "$DEPLOY_STATE_FILE" ]; then
        echo "Error: Deployment state file not found. Please run create_kb_bucket first."
        return 1
    fi
    
    local bucket_name=$(jq -r '.kb_bucket_name' "$DEPLOY_STATE_FILE")
    if [ -z "$bucket_name" ] || [ "$bucket_name" == "null" ]; then
        echo "Error: Knowledge base bucket not found in deployment state"
        return 1
    fi
    
    echo "Uploading knowledge base files to S3 bucket: $bucket_name"
    
    # Upload Firebolt schema files
    aws s3 sync "../knowledge_base/firebolt_schema/" "s3://$bucket_name/firebolt_schema/source/" \
        --profile "$AWS_PROFILE"
    
    echo "Knowledge base files uploaded successfully"
    return 0
}

# Create IAM role for Lambda functions
function create_lambda_role {
    local role_name="revops-ai-lambda-role"
    echo "Creating IAM role for Lambda functions: $role_name"
    
    # Create trust policy document
    cat > /tmp/lambda-trust-policy.json << EOL
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOL
    
    # Create the IAM role
    aws iam create-role \
        --role-name "$role_name" \
        --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
        --profile "$AWS_PROFILE"
    
    # Attach basic Lambda execution policy
    aws iam attach-role-policy \
        --role-name "$role_name" \
        --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
        --profile "$AWS_PROFILE"
    
    # Attach S3 read policy
    aws iam attach-role-policy \
        --role-name "$role_name" \
        --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
        --profile "$AWS_PROFILE"
    
    # Save role name to state file
    local state_data='{}'
    if [ -f "$DEPLOY_STATE_FILE" ]; then
        state_data=$(cat "$DEPLOY_STATE_FILE")
    fi
    
    echo "$state_data" | jq --arg role "$role_name" '.lambda_role_name = $role' > "$DEPLOY_STATE_FILE"
    
    echo "Lambda IAM role created: $role_name"
    return 0
}

# Deploy Lambda functions
function deploy_lambda_functions {
    if [ ! -f "$DEPLOY_STATE_FILE" ]; then
        echo "Error: Deployment state file not found. Please run create_lambda_role first."
        return 1
    fi
    
    local role_name=$(jq -r '.lambda_role_name' "$DEPLOY_STATE_FILE")
    if [ -z "$role_name" ] || [ "$role_name" == "null" ]; then
        echo "Error: Lambda role not found in deployment state"
        return 1
    fi
    
    # Get the role ARN
    local role_arn=$(aws iam get-role --role-name "$role_name" --query 'Role.Arn' --output text --profile "$AWS_PROFILE")
    
    echo "Deploying Lambda functions with role ARN: $role_arn"
    
    # Build and deploy firebolt_reader Lambda
    echo "Deploying firebolt_reader Lambda..."
    
    # Create deployment package
    mkdir -p /tmp/lambda_packages/firebolt_reader
    cp -r "../lambdas/firebolt_reader/"* /tmp/lambda_packages/firebolt_reader/
    pip install -r /tmp/lambda_packages/firebolt_reader/requirements.txt -t /tmp/lambda_packages/firebolt_reader/
    
    cd /tmp/lambda_packages/firebolt_reader
    zip -r ../firebolt_reader.zip ./*
    cd -
    
    # Create or update Lambda function
    if aws lambda get-function --function-name firebolt-reader-lambda --profile "$AWS_PROFILE" &>/dev/null; then
        # Update existing function
        aws lambda update-function-code \
            --function-name firebolt-reader-lambda \
            --zip-file fileb:///tmp/lambda_packages/firebolt_reader.zip \
            --profile "$AWS_PROFILE"
    else
        # Create new function
        aws lambda create-function \
            --function-name firebolt-reader-lambda \
            --zip-file fileb:///tmp/lambda_packages/firebolt_reader.zip \
            --handler lambda_function.lambda_handler \
            --runtime python3.8 \
            --role "$role_arn" \
            --profile "$AWS_PROFILE"
    fi
    
    # Update state file
    local state_data='{}'
    if [ -f "$DEPLOY_STATE_FILE" ]; then
        state_data=$(cat "$DEPLOY_STATE_FILE")
    fi
    
    # Get function ARN
    local reader_lambda_arn=$(aws lambda get-function --function-name firebolt-reader-lambda --query 'Configuration.FunctionArn' --output text --profile "$AWS_PROFILE")
    
    echo "$state_data" | jq --arg arn "$reader_lambda_arn" '.lambda_functions.firebolt_reader = $arn' > "$DEPLOY_STATE_FILE"
    
    echo "Lambda functions deployed successfully"
    return 0
}

# Create Bedrock knowledge base
function create_bedrock_kb {
    if [ ! -f "$DEPLOY_STATE_FILE" ]; then
        echo "Error: Deployment state file not found."
        return 1
    fi
    
    local bucket_name=$(jq -r '.kb_bucket_name' "$DEPLOY_STATE_FILE")
    if [ -z "$bucket_name" ] || [ "$bucket_name" == "null" ]; then
        echo "Error: Knowledge base bucket not found in deployment state"
        return 1
    fi
    
    # Get bucket ARN
    local bucket_arn="arn:aws:s3:::$bucket_name"
    
    echo "Creating Bedrock knowledge base using S3 bucket: $bucket_name"
    
    # Create data source configuration file
    cat > /tmp/kb-datasource.json << EOL
{
  "name": "firebolt-schema-datasource",
  "dataSourceConfiguration": {
    "type": "S3",
    "s3Configuration": {
      "bucketArn": "$bucket_arn",
      "inclusionPrefixes": ["firebolt_schema/source/"]
    }
  }
}
EOL
    
    # Create knowledge base configuration file
    cat > /tmp/kb-config.json << EOL
{
  "name": "firebolt-schema-kb",
  "description": "Firebolt schema knowledge base for data agent",
  "roleArn": "$role_arn",
  "knowledgeBaseConfiguration": {
    "type": "VECTOR",
    "vectorKnowledgeBaseConfiguration": {
      "embeddingModelArn": "arn:aws:bedrock::foundation-model/anthropic.claude-3-7-sonnet-20250219-v1:0"
    }
  }
}
EOL
    
    # Create the knowledge base
    local kb_response=$(aws bedrock create-knowledge-base \
        --cli-input-json file:///tmp/kb-config.json \
        --profile "$AWS_PROFILE")
    
    # Extract knowledge base ID
    local kb_id=$(echo "$kb_response" | jq -r '.knowledgeBase.knowledgeBaseId')
    
    # Add data source to knowledge base
    aws bedrock create-data-source \
        --knowledge-base-id "$kb_id" \
        --cli-input-json file:///tmp/kb-datasource.json \
        --profile "$AWS_PROFILE"
    
    # Update state file
    local state_data='{}'
    if [ -f "$DEPLOY_STATE_FILE" ]; then
        state_data=$(cat "$DEPLOY_STATE_FILE")
    fi
    
    echo "$state_data" | jq --arg id "$kb_id" '.knowledge_bases.firebolt_schema = $id' > "$DEPLOY_STATE_FILE"
    
    echo "Bedrock knowledge base created: $kb_id"
    return 0
}

# Create Bedrock agent
function create_bedrock_agent {
    if [ ! -f "$DEPLOY_STATE_FILE" ]; then
        echo "Error: Deployment state file not found."
        return 1
    fi
    
    local kb_id=$(jq -r '.knowledge_bases.firebolt_schema' "$DEPLOY_STATE_FILE")
    if [ -z "$kb_id" ] || [ "$kb_id" == "null" ]; then
        echo "Error: Knowledge base ID not found in deployment state"
        return 1
    fi
    
    local reader_lambda_arn=$(jq -r '.lambda_functions.firebolt_reader' "$DEPLOY_STATE_FILE")
    if [ -z "$reader_lambda_arn" ] || [ "$reader_lambda_arn" == "null" ]; then
        echo "Error: Firebolt reader Lambda ARN not found in deployment state"
        return 1
    fi
    
    echo "Creating Bedrock agent with knowledge base ID: $kb_id"
    
    # Read agent instructions
    local instructions=$(cat "../agents/data_agent/instructions.md")
    
    # Create agent configuration file
    cat > /tmp/agent-config.json << EOL
{
  "agentName": "firebolt-data-agent",
  "description": "Agent for retrieving and writing Firebolt data",
  "foundationModel": "anthropic.claude-3-7-sonnet-20250219-v1:0",
  "instruction": "$instructions",
  "customerEncryptionKeyArn": "",
  "idleSessionTTLInSeconds": 1800
}
EOL
    
    # Create the agent
    local agent_response=$(aws bedrock create-agent \
        --cli-input-json file:///tmp/agent-config.json \
        --profile "$AWS_PROFILE")
    
    # Extract agent ID
    local agent_id=$(echo "$agent_response" | jq -r '.agent.agentId')
    
    # Associate knowledge base with agent
    aws bedrock associate-agent-knowledge-base \
        --agent-id "$agent_id" \
        --knowledge-base-id "$kb_id" \
        --description "Firebolt schema knowledge base" \
        --profile "$AWS_PROFILE"
    
    # Create action group for firebolt reader
    aws bedrock create-agent-action-group \
        --agent-id "$agent_id" \
        --action-group-name "firebolt-reader-action" \
        --action-group-executor "firebolt_reader" \
        --description "Actions for querying Firebolt database" \
        --function-schema file://../lambdas/firebolt_reader/api_schema.json \
        --lambda-function "$reader_lambda_arn" \
        --profile "$AWS_PROFILE"
    
    # Create agent alias for deployment
    local alias_response=$(aws bedrock create-agent-alias \
        --agent-id "$agent_id" \
        --agent-alias-name "data-agent-prod" \
        --description "Production alias for data agent" \
        --profile "$AWS_PROFILE")
    
    # Extract alias ID
    local alias_id=$(echo "$alias_response" | jq -r '.agentAlias.agentAliasId')
    
    # Update state file
    local state_data='{}'
    if [ -f "$DEPLOY_STATE_FILE" ]; then
        state_data=$(cat "$DEPLOY_STATE_FILE")
    fi
    
    echo "$state_data" | jq --arg id "$agent_id" --arg alias "$alias_id" \
        '.agents.data_agent.id = $id | .agents.data_agent.alias_id = $alias' > "$DEPLOY_STATE_FILE"
    
    echo "Bedrock agent created: $agent_id"
    echo "Agent alias created: $alias_id"
    return 0
}

# Main execution logic
if [ "$ACTION" == "deploy_data" ] || [ "$ACTION" == "deploy_all" ]; then
    echo "Deploying data agent and infrastructure..."
    create_kb_bucket
    upload_kb_files
    create_lambda_role
    deploy_lambda_functions
    create_bedrock_kb
    create_bedrock_agent
    echo "Data agent deployment completed successfully!"
fi

if [ "$ACTION" == "deploy_decision" ] || [ "$ACTION" == "deploy_all" ]; then
    echo "Deploying decision agent and infrastructure..."
    # Implementation for decision agent will be added later
    echo "Decision agent deployment not implemented yet"
fi

if [ "$ACTION" == "deploy_exec" ] || [ "$ACTION" == "deploy_all" ]; then
    echo "Deploying execution agent and infrastructure..."
    # Implementation for execution agent will be added later
    echo "Execution agent deployment not implemented yet"
fi

echo "AWS CLI Deployment completed"
exit 0
