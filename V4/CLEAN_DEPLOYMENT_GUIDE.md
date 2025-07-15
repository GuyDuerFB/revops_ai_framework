# Clean Environment Deployment Guide

Complete step-by-step guide for deploying the RevOps AI Framework V2 from scratch in a clean environment.

## Prerequisites Checklist

### ✅ AWS Environment
- [ ] AWS Account with administrator privileges
- [ ] AWS CLI v2 installed and configured
- [ ] AWS SSO or IAM access keys configured
- [ ] Profile: `FireboltSystemAdministrator-740202120544`

### ✅ Development Environment
- [ ] Python 3.9+ installed
- [ ] pip package manager
- [ ] Git client installed
- [ ] Terminal/Command line access

### ✅ External Services
- [ ] Firebolt Data Warehouse account and credentials
- [ ] Salesforce API access (for CRM integration)
- [ ] Gong API credentials (for conversation intelligence)
- [ ] Slack workspace administrator access

### ✅ Credentials Required
- [ ] Firebolt client_id and client_secret
- [ ] Gong API credentials
- [ ] Slack app signing secret and bot token

## Step-by-Step Deployment

### Step 1: Repository Setup
```bash
# Clone the repository
git clone <repository-url>
cd revops_ai_framework/V2

# Verify clean state
ls -la
# Should see: agents/, deployment/, integrations/, knowledge_base/, monitoring/, tools/, README.md, requirements.txt, .gitignore
```

### Step 2: Python Environment
```bash
# Create isolated Python environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(boto3|requests|pyyaml)"
```

### Step 3: AWS Configuration
```bash
# Option A: AWS SSO (Recommended)
aws configure sso --profile FireboltSystemAdministrator-740202120544

# Option B: Access Keys
aws configure --profile FireboltSystemAdministrator-740202120544
# Enter: Access Key ID, Secret Access Key, us-east-1, json

# Test AWS connectivity
aws sts get-caller-identity --profile FireboltSystemAdministrator-740202120544

# Login to SSO (if using SSO)
aws sso login --profile FireboltSystemAdministrator-740202120544
```

### Step 4: Configure Secrets
```bash
cd deployment

# Copy secrets template
cp secrets.template.json secrets.json

# Edit secrets.json with your actual credentials
nano secrets.json  # or vim, code, etc.

# Required fields:
# {
#   "firebolt_credentials": {
#     "client_id": "your-firebolt-client-id",
#     "client_secret": "your-firebolt-client-secret"
#   },
#   "gong_credentials": {
#     "api_key": "your-gong-api-key",
#     "access_key": "your-gong-access-key"
#   },
#   "slack_credentials": {
#     "signing_secret": "your-slack-signing-secret",
#     "bot_token": "your-slack-bot-token"
#   }
# }

# Verify secrets file exists (but don't display contents)
ls -la secrets.json
```

### Step 5: Deploy Core Infrastructure
```bash
# Ensure you're in deployment directory
cd deployment

# Install deployment-specific dependencies
pip install -r requirements.txt

# Deploy all agents and Lambda functions
python3 deploy_production.py

# Expected output:
# ✅ WebSearch Agent configured
# ✅ Lambda functions ready  
# 🎉 CORE DEPLOYMENT SUCCESSFUL!

# Verify deployment
aws bedrock-agent list-agents --region us-east-1 --profile FireboltSystemAdministrator-740202120544
```

### Step 6: Deploy Slack Integration
```bash
# Navigate to Slack integration
cd ../integrations/slack-bedrock-gateway

# Deploy Slack-Bedrock gateway
python3 deploy.py

# Note the API Gateway URL from output
# Example: https://abcd1234.execute-api.us-east-1.amazonaws.com/prod/slack-events

# Verify Slack infrastructure
aws cloudformation describe-stacks \
  --stack-name revops-slack-bedrock-stack \
  --region us-east-1 \
  --profile FireboltSystemAdministrator-740202120544
```

### Step 7: Deploy Enhanced Monitoring
```bash
# Navigate to monitoring
cd ../../monitoring

# Deploy comprehensive monitoring
python3 deploy-monitoring.py

# Expected output:
# ✅ Monitoring stack deployed successfully!
# 📊 CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/...

# Access monitoring dashboard
open "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-slack-bedrock-monitoring"
```

### Step 8: Configure Slack App
```bash
# Create Slack app at https://api.slack.com/apps
# 1. Click "Create New App" > "From scratch"
# 2. App Name: "RevBot" 
# 3. Workspace: Select your workspace

# Configure OAuth & Permissions:
# Scopes needed:
# - chat:write
# - im:read  
# - im:write
# - app_mentions:read

# Configure Event Subscriptions:
# Enable Events: Yes
# Request URL: https://YOUR-API-GATEWAY-ID.execute-api.us-east-1.amazonaws.com/prod/slack-events
# Subscribe to events: app_mention

# Install app to workspace
# Copy Bot User OAuth Token and Signing Secret

# Update AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id revops-slack-bedrock-secrets \
  --secret-string '{"signing_secret":"YOUR_SIGNING_SECRET","bot_token":"YOUR_BOT_TOKEN"}' \
  --region us-east-1 \
  --profile FireboltSystemAdministrator-740202120544
```

### Step 9: Test and Validate
```bash
# Test Slack integration
cd integrations/slack-bedrock-gateway
python3 tests/test_integration.py

# Monitor logs in real-time
aws logs tail /aws/lambda/revops-slack-bedrock-processor \
  --follow \
  --profile FireboltSystemAdministrator-740202120544

# Test in Slack channel
# @RevBot test connectivity
# @RevBot analyze Q2-2025 revenue trends

# Verify system health
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-processing-queue \
  --attribute-names ApproximateNumberOfMessages \
  --profile FireboltSystemAdministrator-740202120544
```

## Verification Checklist

### ✅ Infrastructure Deployed
- [ ] 4 Bedrock Agents (Decision, Data, WebSearch, Execution)
- [ ] 8 Lambda Functions (all tools + Slack integration)
- [ ] 1 Knowledge Base (F61WLOYZSW)
- [ ] SQS Queues (processing + dead letter)
- [ ] API Gateway for Slack events
- [ ] CloudWatch monitoring dashboard

### ✅ Connectivity Tests
- [ ] AWS CLI connectivity confirmed
- [ ] Bedrock agents listed successfully
- [ ] Lambda functions deployed and accessible
- [ ] Slack app configured and installed
- [ ] API Gateway endpoint responding
- [ ] CloudWatch dashboard accessible

### ✅ End-to-End Tests
- [ ] Slack message triggers handler Lambda
- [ ] Handler queues message to SQS
- [ ] Processor Lambda invokes Bedrock agent
- [ ] Decision Agent coordinates with collaborators
- [ ] Response returns to Slack channel
- [ ] Monitoring captures all events

## Common Issues and Solutions

### Issue: AWS Permission Denied
```bash
# Check AWS credentials
aws sts get-caller-identity --profile FireboltSystemAdministrator-740202120544

# Refresh SSO token
aws sso login --profile FireboltSystemAdministrator-740202120544

# Verify profile exists
aws configure list-profiles | grep FireboltSystemAdministrator
```

### Issue: Lambda Timeout
```bash
# Check Lambda timeout settings
aws lambda get-function-configuration \
  --function-name revops-slack-bedrock-processor \
  --region us-east-1 \
  --profile FireboltSystemAdministrator-740202120544

# Should show: "Timeout": 300
```

### Issue: Slack App Not Responding  
```bash
# Check API Gateway
aws apigateway get-rest-apis \
  --region us-east-1 \
  --profile FireboltSystemAdministrator-740202120544

# Verify Slack secrets
aws secretsmanager get-secret-value \
  --secret-id revops-slack-bedrock-secrets \
  --region us-east-1 \
  --profile FireboltSystemAdministrator-740202120544
```

### Issue: Dead Letter Queue Messages
```bash
# Check DLQ
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-dlq \
  --attribute-names ApproximateNumberOfMessages \
  --region us-east-1 \
  --profile FireboltSystemAdministrator-740202120544

# If messages exist, check logs for root cause
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'ERROR' \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --region us-east-1 \
  --profile FireboltSystemAdministrator-740202120544
```

## Post-Deployment Maintenance

### Daily Monitoring
- Check CloudWatch dashboard for system health
- Monitor dead letter queue for failed messages
- Review error logs for any issues

### Weekly Maintenance  
- Review CloudWatch Insights queries for patterns
- Check Lambda function performance metrics
- Validate Slack integration functionality

### Monthly Review
- Analyze usage patterns and optimization opportunities
- Review and update agent instructions if needed
- Update dependencies and security patches

## Security Considerations

- ✅ Secrets stored in AWS Secrets Manager (not in code)
- ✅ IAM roles follow least privilege principle
- ✅ No hardcoded credentials in any files
- ✅ All communication encrypted (HTTPS/TLS)
- ✅ VPC isolation where appropriate
- ✅ CloudWatch audit logging enabled

## Cost Optimization

### Expected Monthly Costs (approximate)
- **Bedrock Agents**: $50-200 (depending on usage)
- **Lambda Functions**: $10-50 (pay per invocation)
- **CloudWatch**: $20-100 (logs and metrics)
- **SQS**: $1-10 (message processing)
- **API Gateway**: $5-25 (API calls)

### Cost Monitoring
```bash
# Monitor AWS costs
aws ce get-cost-and-usage \
  --time-period Start=2025-07-01,End=2025-07-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --profile FireboltSystemAdministrator-740202120544
```

## Support and Troubleshooting

### Documentation
- **Main README**: Complete system overview
- **Deployment README**: Infrastructure deployment details  
- **Slack Integration README**: AWS best practices implementation
- **Monitoring README**: Observability and troubleshooting
- **Troubleshooting Runbook**: Generated operational guide

### Getting Help
- Check CloudWatch logs for detailed error information
- Use CloudWatch Insights queries for pattern analysis
- Review troubleshooting runbook for common scenarios
- Monitor SNS alerts for critical issues

---

**Deployment Complete!** 🎉

Your RevOps AI Framework V2 is now fully operational with:
- ✅ Multi-agent AI collaboration
- ✅ Slack integration with AWS best practices
- ✅ Enterprise-grade monitoring and logging
- ✅ Comprehensive error handling and recovery
- ✅ Production-ready performance optimization

Test with: `@RevBot analyze Q2-2025 revenue by customer segment with recommendations`