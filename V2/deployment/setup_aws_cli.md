# AWS CLI Setup for RevOps AI Framework Deployment

This document provides instructions for setting up AWS CLI credentials for deploying the RevOps AI Framework.

## Prerequisites

- AWS CLI version 2 installed (check with `aws --version`)
- Access to AWS SSO (Single Sign-On) or IAM credentials
- Appropriate permissions to deploy AWS resources (Lambda, Bedrock, IAM, S3, etc.)

## Option 1: Setup with AWS SSO (Recommended)

AWS SSO is the recommended approach as it provides temporary credentials with automatic rotation.

### Steps

1. Run the AWS SSO configuration command:
   ```bash
   aws configure sso
   ```

2. Follow the prompts:
   - **SSO session name**: Enter a descriptive name (e.g., `revops-framework-deployment`)
   - **SSO start URL**: Your organization's SSO URL (e.g., `https://d-90670a1316.awsapps.com/start/#`)
   - **SSO region**: The region where your SSO directory is located (e.g., `us-east-1`)
   - **SSO registration scopes**: Leave as default (`sso:account:access`)

3. A browser window will open (or you'll be provided a URL and code to enter)
   - Sign in with your SSO credentials
   - Authorize the AWS CLI application

4. Select an AWS account and role:
   - Choose the appropriate account (e.g., `740202120544`)
   - Select a role with sufficient permissions (e.g., `FireboltSystemAdministrator`)

5. Configure CLI defaults:
   - **CLI default client Region**: Region for AWS resources (e.g., `us-east-1`)
   - **CLI default output format**: Recommended format is `json`
   - **CLI profile name**: Accept the default or enter a custom name

6. Verify the profile has been created:
   ```bash
   aws configure list-profiles
   ```

7. To use this profile with deployment scripts, either:
   - Specify it with the `--profile` flag:
     ```bash
     aws s3 ls --profile FireboltSystemAdministrator-740202120544
     ```
   - Or set it as an environment variable:
     ```bash
     export AWS_PROFILE=FireboltSystemAdministrator-740202120544
     ```

8. Update the `profile_name` in your `config.json` to match this profile name.

## Option 2: Setup with IAM Access Keys

If SSO is not available, you can use IAM access keys (less secure for long-term use).

### Steps

1. Run the AWS configuration command:
   ```bash
   aws configure
   ```

2. Follow the prompts:
   - **AWS Access Key ID**: Enter your IAM access key ID
   - **AWS Secret Access Key**: Enter your IAM secret access key
   - **Default region name**: Enter the region for your resources (e.g., `us-east-1`)
   - **Default output format**: Recommended format is `json`

3. Verify the configuration:
   ```bash
   aws configure list
   ```

## Checking Your Configuration

Verify your AWS CLI is properly configured:

```bash
# List all configured profiles
aws configure list-profiles

# Check current profile's configuration
aws configure list

# Test authorization with a basic command
aws sts get-caller-identity
```

## Using AWS CLI with RevOps AI Framework Deployment

1. Make sure the `profile_name` in your `config.json` matches your AWS CLI profile name
2. Run the deployment scripts which will use this profile for authentication

## Refreshing SSO Credentials

SSO credentials expire after a certain period (typically 8-12 hours). To refresh:

```bash
aws sso login --profile FireboltSystemAdministrator-740202120544
```
