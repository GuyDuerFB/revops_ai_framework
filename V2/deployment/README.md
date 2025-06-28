# RevOps AI Framework V2 - Deployment

This directory contains infrastructure as code (IaC) and deployment configurations for the RevOps AI Framework.

## Overview

The deployment directory provides all the necessary configurations and scripts to deploy the RevOps AI Framework V2 to AWS. It uses Terraform as the primary Infrastructure as Code (IaC) tool to ensure consistent, repeatable deployments.

## Directory Structure

```
deployment/
├── README.md                 # This file
├── terraform/                # Terraform IaC configurations
│   ├── main.tf              # Main Terraform configuration
│   ├── variables.tf         # Input variables definition
│   ├── outputs.tf           # Output variables definition
│   └── modules/             # Reusable Terraform modules
├── scripts/                  # Deployment and utility scripts
├── config/                   # Environment-specific configurations
└── templates/                # CloudFormation and other templates
```

## Deployment Components

The deployment configurations provision the following resources:

1. **Compute Resources**:
   - AWS Lambda functions for agents and tools
   - ECS containers for specific workloads (if applicable)

2. **Storage Resources**:
   - S3 buckets for artifacts and data
   - DynamoDB tables for state management

3. **Networking**:
   - API Gateway endpoints
   - VPC configuration (if applicable)
   - Security groups and access controls

4. **Integration Points**:
   - SQS queues for asynchronous processing
   - SNS topics for notifications
   - Event Bridge rules for event-driven workflows

5. **Security**:
   - IAM roles and policies
   - Secrets Manager secrets
   - KMS keys for encryption

## Deployment Instructions

### Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0.0
- Python >= 3.8 (for deployment scripts)

### Deployment Steps

1. **Configure Environment Variables**:

   Create a `.env` file in the root directory with the following variables:

   ```
   AWS_PROFILE=your-aws-profile
   ENVIRONMENT=dev|staging|prod
   REGION=us-west-2
   ```

2. **Initialize Terraform**:

   ```bash
   cd terraform
   terraform init
   ```

3. **Plan the Deployment**:

   ```bash
   terraform plan -var-file=../config/${ENVIRONMENT}.tfvars
   ```

4. **Apply the Deployment**:

   ```bash
   terraform apply -var-file=../config/${ENVIRONMENT}.tfvars
   ```

### Environment-Specific Configuration

Environment-specific variables are defined in the `config/` directory:

- `dev.tfvars`: Development environment configuration
- `staging.tfvars`: Staging environment configuration
- `prod.tfvars`: Production environment configuration

## CI/CD Integration

The deployment can be automated through CI/CD pipelines. Example workflows are provided for:

- GitHub Actions
- AWS CodePipeline
- GitLab CI

See the `ci` directory for example configurations.

## Monitoring and Observability

The deployment includes configuration for:

- CloudWatch Logs for logging
- CloudWatch Metrics for monitoring
- X-Ray for distributed tracing

## Rollback Procedures

In case of deployment issues:

1. **Terraform Rollback**:

   ```bash
   terraform apply -var-file=../config/${ENVIRONMENT}.tfvars -target=module.critical_component
   ```

2. **Manual Rollback**:

   Use the `scripts/rollback.py` script:

   ```bash
   python scripts/rollback.py --environment=${ENVIRONMENT} --version=previous
   ```

## Custom Modules

The `terraform/modules/` directory contains reusable Terraform modules for common components:

- `lambda`: Lambda function deployment with standard configuration
- `api`: API Gateway configuration with standard endpoints
- `storage`: Standard storage configuration
- `monitoring`: CloudWatch dashboards and alarms

## Security Considerations

- All secrets are stored in AWS Secrets Manager
- Least privilege IAM policies are applied
- Network access is restricted according to security best practices
- Encryption is applied to data at rest and in transit
