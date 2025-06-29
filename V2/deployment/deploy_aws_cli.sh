#!/bin/bash
# RevOps AI Framework - AWS Deployment Script
# This script handles the deployment of the RevOps AI Framework components using AWS CLI
# It replaces the previous Terraform-based deployment approach

# Add process lock to prevent multiple simultaneous script runs
LOCKFILE="/tmp/deploy_aws_cli.lock"
if [ -e "$LOCKFILE" ]; then
    pid=$(cat "$LOCKFILE")
    if ps -p "$pid" > /dev/null; then
        echo "Error: Another instance of deploy_aws_cli.sh is already running (PID: $pid)"
        echo "If this is an error, manually remove $LOCKFILE"
        exit 1
    else
        # Stale lock file - previous process crashed
        echo "Removing stale lock file from previous run"
        rm -f "$LOCKFILE"
    fi
fi

# Create lock file
echo $$ > "$LOCKFILE"

# Ensure lock file is removed on exit
trap 'rm -f "$LOCKFILE"' EXIT

set -e  # Exit on error

# Default values
CONFIG_FILE="config.json"
SECRETS_FILE="secrets.json"
DEPLOY_STATE_FILE="deploy_state.json"
AWS_PROFILE="FireboltSystemAdministrator-740202120544" # Default AWS profile
ACTION=""

# Display help
function show_help {
    echo "RevOps AI Framework - AWS CLI Deployment"
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --config FILE     Use specified config file (default: config.json)"
    echo "  --secrets FILE    Use specified secrets file (default: secrets.json)"
    echo "  --profile NAME    Use specified AWS CLI profile (default: FireboltSystemAdministrator-740202120544)"
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
        --profile)
            AWS_PROFILE="$2"
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
echo "AWS Profile: ${AWS_CLI_PROFILE:-$AWS_PROFILE}"
echo "Action: $ACTION"
echo "=============================================="

# Check if an action was specified
if [ -z "$ACTION" ]; then
    echo "No action specified. Please use --deploy-data, --deploy-decision, --deploy-exec or --deploy-all"
    echo "Run $0 --help for more information"
    exit 1
fi

# Use the specified AWS profile
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
    echo "Checking/creating IAM role for Lambda functions: $role_name"
    
    # Check if role already exists
    if aws iam get-role --role-name "$role_name" --profile "$AWS_PROFILE" &>/dev/null; then
        echo "IAM role already exists: $role_name"
    else
        # Create IAM role with trust policy for Lambda
        cat > /tmp/trust-policy.json << EOL
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

        # Create the role
        local role_response=$(aws iam create-role \
            --role-name "$role_name" \
            --assume-role-policy-document file:///tmp/trust-policy.json \
            --profile "$AWS_PROFILE")
            
        echo "IAM role created: $role_name"
    fi
    
    # Ensure policies are attached (idempotent operation)
    echo "Attaching policies to IAM role..."
    
    aws iam attach-role-policy \
        --role-name "$role_name" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole" \
        --profile "$AWS_PROFILE" || echo "Policy AWSLambdaBasicExecutionRole may already be attached"
        
    aws iam attach-role-policy \
        --role-name "$role_name" \
        --policy-arn "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess" \
        --profile "$AWS_PROFILE" || echo "Policy AmazonS3ReadOnlyAccess may already be attached"
    
    # Save role name to state file
    local state_data='{}'
    if [ -f "$DEPLOY_STATE_FILE" ]; then
        state_data=$(cat "$DEPLOY_STATE_FILE")
    fi
    
    echo "$state_data" | jq --arg role "$role_name" '.lambda_role_name = $role' > "$DEPLOY_STATE_FILE"
    
    echo "Lambda IAM role setup complete: $role_name"
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
    
    # Build and deploy firebolt_reader Lambda (query_lambda)
    echo "Deploying firebolt_reader Lambda..."
    
    # Create deployment package
    mkdir -p /tmp/lambda_packages/firebolt_reader
    cp -r "../tools/firebolt/query_lambda/"* /tmp/lambda_packages/firebolt_reader/ || {
        echo "Error copying Lambda function files. Check if the directory exists."
        ls -la "../tools/firebolt/"
        return 1
    }
    
    echo "Creating basic Lambda package without external dependencies..."
    
    # Skip installing external dependencies for now to avoid long-running pip installs
    # Just package the Lambda function code itself
    
    # Create a minimal requirements.txt if it doesn't exist
    # Note: We're intentionally excluding firebolt-sdk here to speed up deployment
    # Lambda will rely on boto3 which is included in the Lambda runtime
    echo "Packaging Lambda with minimal dependencies..."
    echo "boto3" > /tmp/lambda_packages/firebolt_reader/requirements.txt
    
    # Zip only the Lambda function code without dependencies
    cd /tmp/lambda_packages/firebolt_reader
    zip -r ../firebolt_reader.zip ./*
    cd - || return 1
    
    echo "Lambda package created: /tmp/lambda_packages/firebolt_reader.zip"
    
    # Create or update Lambda function
    if aws lambda get-function --function-name firebolt-reader-lambda --profile "$AWS_PROFILE" &>/dev/null; then
        # Update existing function
        echo "Updating existing Lambda function: firebolt-reader-lambda"
        aws lambda update-function-code \
            --function-name firebolt-reader-lambda \
            --zip-file fileb:///tmp/lambda_packages/firebolt_reader.zip \
            --profile "$AWS_PROFILE"
    else
        # Create new function
        echo "Creating new Lambda function: firebolt-reader-lambda"
        aws lambda create-function \
            --function-name firebolt-reader-lambda \
            --runtime python3.9 \
            --role "$role_arn" \
            --handler lambda_function.lambda_handler \
            --zip-file fileb:///tmp/lambda_packages/firebolt_reader.zip \
            --timeout 30 \
            --memory-size 256 \
            --profile "$AWS_PROFILE"
    fi
    
    echo "Lambda function deployment completed"
    
    # Clean up
    rm -rf /tmp/lambda_packages/firebolt_reader
    
    # Note for user about Lambda dependencies
    echo "NOTE: The Lambda function has been deployed with minimal dependencies."
    echo "You may need to add the firebolt-sdk as a Lambda layer for full functionality."
    echo "Alternatively, add firebolt-sdk back to the requirements.txt for a full deployment."
    if [ -f "$DEPLOY_STATE_FILE" ]; then
        state_data=$(cat "$DEPLOY_STATE_FILE")
    fi
    
    # Get function ARN
    local reader_lambda_arn=$(aws lambda get-function --function-name firebolt-reader-lambda --query 'Configuration.FunctionArn' --output text --profile "$AWS_PROFILE")
    
    echo "$state_data" | jq --arg arn "$reader_lambda_arn" '.lambda_functions.firebolt_reader = $arn' > "$DEPLOY_STATE_FILE"
    
    echo "Lambda functions deployed successfully"
    return 0
}

# Create Bedrock knowledge base using Python script
function create_bedrock_kb {
    if [ ! -f "$DEPLOY_STATE_FILE" ]; then
        echo "Error: Deployment state file not found."
        return 1
    fi
    
    echo "Creating Bedrock knowledge base using Python script..."
    
    # Make the Python script executable
    chmod +x ./deploy_bedrock.py
    
    # Ensure required Python packages are installed
    echo "Checking and installing required Python packages..."
    pip3 install boto3 --quiet || { echo "Failed to install boto3. Please install it manually with: pip3 install boto3"; return 1; }
    
    # Call the Python script
    if [ -n "$AWS_PROFILE" ]; then
        ./deploy_bedrock.py --create-kb --profile "$AWS_PROFILE" --state-file "$DEPLOY_STATE_FILE"
    else
        ./deploy_bedrock.py --create-kb --state-file "$DEPLOY_STATE_FILE"
    fi
    
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Failed to create Bedrock knowledge base"
        return 1
    fi
    
    echo "Bedrock knowledge base created successfully"
    return 0
}

# Create Bedrock agent using Python script
function create_bedrock_agent {
    if [ ! -f "$DEPLOY_STATE_FILE" ]; then
        echo "Error: Deployment state file not found."
        return 1
    fi
    
    echo "Creating Bedrock agent using Python script..."
    
    # Ensure required Python packages are installed
    echo "Checking and installing required Python packages..."
    pip3 install boto3 --quiet || { echo "Failed to install boto3. Please install it manually with: pip3 install boto3"; return 1; }
    
    # Call the Python script
    if [ -n "$AWS_PROFILE" ]; then
        ./deploy_bedrock.py --create-agent --profile "$AWS_PROFILE" --state-file "$DEPLOY_STATE_FILE"
    else
        ./deploy_bedrock.py --create-agent --state-file "$DEPLOY_STATE_FILE"
    fi
    
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Error: Failed to create Bedrock agent"
        return 1
    fi
    
    echo "Bedrock agent created successfully"
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
