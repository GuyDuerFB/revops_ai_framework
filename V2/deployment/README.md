# RevOps AI Framework V2 - Deployment

This directory contains infrastructure as code (IaC) and deployment configurations for the RevOps AI Framework.

## Overview

The deployment directory provides configurations and scripts to deploy the RevOps AI Framework V2 to AWS. It uses Terraform as the primary Infrastructure as Code (IaC) tool to ensure consistent, repeatable deployments.

## Directory Structure

```
deployment/
├── README.md                 # This file
├── apply_terraform.sh        # Script to apply Terraform configurations
├── config_template.json      # Template for configuration settings
├── deploy.py                # Python deployment script
├── generate_tf_config.py    # Script to generate Terraform configuration
├── requirements.txt         # Python dependencies for deployment scripts
├── secrets_template.json    # Template for secrets configuration
└── terraform/                # Terraform IaC configurations
    ├── main.tf              # Main Terraform configuration
    ├── variables.tf         # Input variables definition
    ├── outputs.tf           # Output variables definition
    └── modules/             # Reusable Terraform modules
        ├── agent/            # Agent Bedrock configuration module
        ├── flow/             # Flow configuration module
        ├── knowledge_base/    # Knowledge base configuration module
        └── lambda/           # Lambda function deployment module
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

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0.0
- Python >= 3.8 (for deployment scripts)

### Deployment Steps

1. **Configure Settings**:

   Copy and customize the template files:
   - From `config_template.json` to create your configuration
   - From `secrets_template.json` to provide necessary credentials

2. **Generate Terraform Configuration**:

   ```bash
   python generate_tf_config.py
   ```

3. **Apply Terraform**:

   Either use the convenience script:
   ```bash
   ./apply_terraform.sh
   ```
   
   Or run the standard Terraform commands:
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

## Terraform Modules

The `terraform/modules/` directory contains reusable Terraform modules for framework components:

- `agent`: Configures AWS Bedrock agents for the framework
- `flow`: Provides flow orchestration infrastructure
- `knowledge_base`: Configures knowledge bases in Bedrock
- `lambda`: Deploys Lambda functions with standard configuration

## Security Considerations

- Secrets are stored using AWS Secrets Manager
- IAM policies follow least-privilege principles
- Encrypted data transmission between components

Future deployment plans are detailed in the ROADMAP.md file in the project root.
