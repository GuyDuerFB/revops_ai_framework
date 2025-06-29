# RevOps AI Framework V2 - Deployment

This directory contains deployment configurations and scripts for the RevOps AI Framework.

## Overview

The deployment directory provides configurations and scripts to deploy the RevOps AI Framework V2 to AWS. It uses AWS CLI commands to ensure consistent, repeatable deployments.

## Directory Structure

```
deployment/
├── README.md                 # This file
├── deploy_aws_cli.sh         # Script for AWS CLI deployments
├── config_template.json      # Template for configuration settings
├── deploy.py                # Python deployment script
├── requirements.txt         # Python dependencies for deployment scripts
├── secrets_template.json    # Template for secrets configuration
└── terraform/                # DEPRECATED: Old Terraform configurations
```

## Deployment Components

The current deployment configurations provision the following resources:

1. **Compute Resources**:
   - AWS Lambda functions for agents and tools

2. **Storage Resources**:
   - S3 buckets for knowledge base artifacts

3. **AI Services**:
   - Amazon Bedrock agents and knowledge bases

4. **Security**:
   - IAM roles and policies
   - Secrets Manager secrets for credentials

## Deployment Instructions

### Prerequisites

#### Required Software

- **Python 3.8+**: Required for deployment scripts
  ```bash
  # Check your Python version
  python3 --version
  
  # macOS (using Homebrew)
  brew install python
  
  # Ubuntu/Debian
  sudo apt update && sudo apt install python3 python3-pip
  ```

- **AWS CLI v2**: Required for all deployments
  ```bash
  # Check AWS CLI version
  aws --version
  
  # macOS (using Homebrew)
  brew install awscli
  
  # Ubuntu/Debian
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip awscliv2.zip
  sudo ./aws/install
  
  # See detailed AWS CLI setup in deployment/setup_aws_cli.md
  ```

- **jq**: Required for JSON processing
  ```bash
  # macOS (using Homebrew)
  brew install jq
  
  # Ubuntu/Debian
  sudo apt update && sudo apt install jq
  ```

#### AWS CLI Configuration

See detailed instructions for AWS CLI setup in [setup_aws_cli.md](./setup_aws_cli.md). This includes:
- Installing AWS CLI
- Setting up credentials with SSO or access keys
- Configuring the appropriate region and profile

#### Python Dependencies

Install required Python packages for deployment scripts:
```bash
pip3 install -r requirements.txt
```

### Deployment Steps

1. **Configure Settings**:

   Copy and customize the template files:
   ```bash
   cp config_template.json config.json
   cp secrets_template.json secrets.json
   ```
   Edit the files to provide your AWS profile, region, and other required settings.

2. **Run AWS CLI Deployment Script**:

   ```bash
   # Deploy data agent and its infrastructure
   ./deploy_aws_cli.sh --deploy-data
   
   # Deploy decision agent (when ready)
   ./deploy_aws_cli.sh --deploy-decision
   
   # Deploy execution agent (when ready)
   ./deploy_aws_cli.sh --deploy-exec
   
   # Or deploy all components
   ./deploy_aws_cli.sh --deploy-all
   ```

3. **View Deployment State**:

   The deployment state is saved in `deploy_state.json`. You can view it with:
   ```bash
   cat deploy_state.json | jq
   ```

## AWS Resources

The deployment script creates and manages the following AWS resources:

- **S3 Buckets**: For storing knowledge base data
- **IAM Roles and Policies**: For secure access to AWS services
- **Lambda Functions**: For agent action groups and backend processing
- **Amazon Bedrock**: For AI agents, knowledge bases, and foundation models

## Security Considerations

- Secrets are stored using AWS Secrets Manager
- IAM policies follow least-privilege principles
- Encrypted data transmission between components
- AWS SSO is recommended for authentication

## Note on Terraform Files

The `terraform/` directory contains legacy deployment configurations that have been deprecated in favor of direct AWS CLI deployment. These files are kept for reference but should not be used.

Future deployment plans are detailed in the ROADMAP.md file in the project root.
