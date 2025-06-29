#!/bin/bash
# Script to apply Terraform configuration for RevOps AI Framework

set -e

# Default values
CONFIG_FILE="config.json"
SECRETS_FILE="secrets.json"
TF_DIR="terraform"
DEPLOY_STATE="deploy_state.json"
ACTION="plan"

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
    --tf-dir)
      TF_DIR="$2"
      shift 2
      ;;
    --state)
      DEPLOY_STATE="$2"
      shift 2
      ;;
    --apply)
      ACTION="apply"
      shift
      ;;
    --destroy)
      ACTION="destroy"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--config config.json] [--secrets secrets.json] [--tf-dir terraform] [--state deploy_state.json] [--apply|--destroy]"
      exit 1
      ;;
  esac
done

echo "=== RevOps AI Framework Terraform Deployment ==="
echo "Config file: $CONFIG_FILE"
echo "Secrets file: $SECRETS_FILE"
echo "Terraform directory: $TF_DIR"
echo "Deployment state: $DEPLOY_STATE"
echo "Action: $ACTION"
echo "=============================================="

# Make sure the script is executable
chmod +x generate_tf_config.py

# Check if config files exist
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Config file not found: $CONFIG_FILE"
  exit 1
fi

if [ ! -f "$SECRETS_FILE" ]; then
  echo "Secrets file not found: $SECRETS_FILE"
  exit 1
fi

# Generate Terraform configuration
echo "Generating Terraform configuration..."
python3 generate_tf_config.py --config "$CONFIG_FILE" --output "$TF_DIR" --secrets "$SECRETS_FILE" --deploy-state "$DEPLOY_STATE"

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
  echo "Terraform not found. Please install Terraform first."
  exit 1
fi

# Change to Terraform directory
echo "Changing to Terraform directory: $TF_DIR"
cd "$TF_DIR"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Format Terraform files
echo "Formatting Terraform files..."
terraform fmt

# Validate Terraform configuration
echo "Validating Terraform configuration..."
terraform validate

# Perform requested action
if [ "$ACTION" = "plan" ]; then
  echo "Planning Terraform deployment..."
  terraform plan -out=tfplan
elif [ "$ACTION" = "apply" ]; then
  echo "Applying Terraform deployment..."
  terraform apply -auto-approve
elif [ "$ACTION" = "destroy" ]; then
  echo "WARNING: This will destroy all resources managed by Terraform!"
  read -p "Are you sure you want to continue? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Destroying Terraform deployment..."
    terraform destroy -auto-approve
  else
    echo "Destroy canceled."
    exit 0
  fi
fi

echo "Terraform action '$ACTION' completed."

# Update deployment state if we did an apply
if [ "$ACTION" = "apply" ]; then
  echo "Updating deployment state..."
  cd ..
  terraform_outputs=$(cd "$TF_DIR" && terraform output -json)
  
  # Read existing deploy state if it exists
  if [ -f "$DEPLOY_STATE" ]; then
    deploy_state=$(cat "$DEPLOY_STATE")
  else
    deploy_state="{}"
  fi
  
  # Merge Terraform outputs into deploy state
  echo "$deploy_state" | jq --argjson tf "$terraform_outputs" \
    '.terraform_resources = $tf | .last_updated = now' > "$DEPLOY_STATE"
  
  echo "Deployment state updated."
fi

echo "Done!"
