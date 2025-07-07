# RevOps Slack-Bedrock Gateway

AWS Best Practices implementation for integrating Slack with Amazon Bedrock Agents, following the architecture recommended in [AWS Machine Learning Blog](https://aws.amazon.com/blogs/machine-learning/integrate-amazon-bedrock-agents-with-slack/).

## 🏗️ Architecture

```
Slack Events → API Gateway → Handler Lambda → SQS → Processor Lambda → Bedrock Agent → Response
                    ↓                             ↓              ↓
              CloudWatch Logs            Secrets Manager    CloudWatch Logs
```

### Key Components

1. **API Gateway**: Secure entry point for Slack events with request validation
2. **Handler Lambda**: Validates Slack signatures, sends immediate acknowledgment, queues processing
3. **SQS Queue**: Async message processing with dead letter queue for error handling
4. **Processor Lambda**: Invokes Bedrock Agent and sends responses back to Slack
5. **Secrets Manager**: Secure storage for Slack credentials
6. **CloudWatch**: Comprehensive logging and monitoring

## 🚀 Features

- ✅ **AWS Best Practices Architecture**: Follows official AWS recommendations
- ✅ **Conversation Continuity**: Built-in Bedrock session management
- ✅ **Async Processing**: Handles Slack's 3-second timeout requirement
- ✅ **Error Handling**: Dead letter queues and retry mechanisms
- ✅ **Security**: Slack signature verification and IAM least privilege
- ✅ **Monitoring**: CloudWatch integration for observability
- ✅ **Scalability**: Auto-scaling Lambda functions and SQS
- ✅ **Cost Optimization**: Pay-per-use serverless architecture

## 📁 Directory Structure

```
integrations/slack-bedrock-gateway/
├── infrastructure/
│   └── slack-bedrock-gateway.yaml     # CloudFormation template
├── lambdas/
│   ├── handler/
│   │   ├── handler.py                 # Slack events handler
│   │   └── requirements.txt
│   └── processor/
│       ├── processor.py               # Message processor with Bedrock Agent
│       └── requirements.txt
├── config/
│   └── deployment-config.json         # Configuration parameters
├── docs/
│   ├── architecture.md               # Detailed architecture docs
│   └── troubleshooting.md            # Common issues and solutions
├── tests/
│   └── test_integration.py           # Integration tests
├── deploy.py                         # Deployment script
└── README.md                         # This file
```

## 🔧 Prerequisites

1. **AWS Account**: With appropriate permissions for CloudFormation, Lambda, API Gateway, SQS, Secrets Manager
2. **AWS CLI**: Configured with `FireboltSystemAdministrator-740202120544` profile
3. **Slack App**: Created with the provided credentials
4. **Bedrock Agent**: RevOps Decision Agent (TCX9CGOKBR) already deployed

## 📦 Deployment

### Quick Start

```bash
cd integrations/slack-bedrock-gateway
python3 deploy.py
```

### Manual Steps

1. **Deploy Infrastructure**:
   ```bash
   aws cloudformation deploy \
     --template-file infrastructure/slack-bedrock-gateway.yaml \
     --stack-name revops-slack-bedrock-stack \
     --parameter-overrides \
       ProjectName=revops-slack-bedrock \
       BedrockAgentId=TCX9CGOKBR \
       BedrockAgentAliasId=RSYE8T5V96 \
       SlackSigningSecret=YOUR_SIGNING_SECRET \
       SlackBotToken=YOUR_BOT_TOKEN \
     --capabilities CAPABILITY_NAMED_IAM \
     --profile FireboltSystemAdministrator-740202120544
   ```

2. **Update Lambda Code**:
   ```bash
   # Handler Lambda
   cd lambdas/handler
   zip -r handler.zip .
   aws lambda update-function-code \
     --function-name revops-slack-bedrock-handler \
     --zip-file fileb://handler.zip \
     --profile FireboltSystemAdministrator-740202120544

   # Processor Lambda  
   cd ../processor
   zip -r processor.zip .
   aws lambda update-function-code \
     --function-name revops-slack-bedrock-processor \
     --zip-file fileb://processor.zip \
     --profile FireboltSystemAdministrator-740202120544
   ```

## ⚙️ Configuration

### Slack App Setup

1. **Event Subscriptions**:
   - Request URL: `https://{api-gateway-id}.execute-api.us-east-1.amazonaws.com/prod/slack-events`
   - Events: `app_mention`

2. **OAuth & Permissions**:
   - Bot Token Scopes: `chat:write`, `im:read`, `im:write`
   - Install app to workspace

3. **Update Secrets**:
   ```bash
   aws secretsmanager update-secret \
     --secret-id revops-slack-bedrock-secrets \
     --secret-string '{"signing_secret":"YOUR_SIGNING_SECRET","bot_token":"YOUR_BOT_TOKEN"}' \
     --profile FireboltSystemAdministrator-740202120544
   ```

### Environment Variables

The deployment automatically configures these environment variables:

**Handler Lambda**:
- `SECRETS_ARN`: Secrets Manager ARN
- `PROCESSING_QUEUE_URL`: SQS queue URL
- `LOG_LEVEL`: Logging level

**Processor Lambda**:
- `SECRETS_ARN`: Secrets Manager ARN  
- `BEDROCK_AGENT_ID`: Decision Agent ID
- `BEDROCK_AGENT_ALIAS_ID`: Agent alias ID
- `LOG_LEVEL`: Logging level

## 💬 Usage

### Basic Commands

```
@RevBot analyze EMEA customers consumption QoQ and provide main highlights
@RevBot Now do the same for JAPAC
@RevBot assess if John Smith from TechCorp is a good lead
@RevBot which customers are at highest churn risk this quarter?
```

### Conversation Flow

1. **User mentions @RevBot** in Slack channel
2. **Handler Lambda** validates request and sends "🤔 Processing..." 
3. **SQS Queue** receives processing request
4. **Processor Lambda** invokes Bedrock Agent with session context
5. **Bedrock Agent** (SUPERVISOR) orchestrates DataAgent, WebSearchAgent, ExecutionAgent as needed
6. **Response** updates the original "Processing..." message

### Session Management

- **Session ID**: `{user_id}:{channel_id}` for conversation continuity
- **Context Retention**: Bedrock maintains context for 1 hour of inactivity
- **Multi-turn Conversations**: Automatic context preservation across messages

## 🔍 Monitoring

### CloudWatch Logs

- **Handler Lambda**: `/aws/lambda/revops-slack-bedrock-handler`
- **Processor Lambda**: `/aws/lambda/revops-slack-bedrock-processor`

### Key Metrics

- **Handler Duration**: Should be < 5 seconds
- **Processor Duration**: Typically 10-60 seconds depending on query complexity
- **SQS Queue Depth**: Monitor for processing delays
- **Error Rates**: Track failed invocations

### Debugging

```bash
# Tail handler logs
aws logs tail /aws/lambda/revops-slack-bedrock-handler --follow

# Tail processor logs  
aws logs tail /aws/lambda/revops-slack-bedrock-processor --follow

# Check SQS queue metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfVisibleMessages \
  --dimensions Name=QueueName,Value=revops-slack-bedrock-processing-queue \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

## 🛠️ Troubleshooting

### Common Issues

1. **Slack URL Verification Fails**:
   - Check API Gateway URL is correct
   - Verify Handler Lambda has proper permissions

2. **No Response from Bot**:
   - Check Processor Lambda logs
   - Verify Bedrock Agent permissions
   - Confirm bot token is valid

3. **Messages Not Processing**:
   - Check SQS dead letter queue
   - Verify event source mapping is active
   - Monitor Lambda error rates

4. **Slow Responses**:
   - Check Bedrock Agent performance
   - Monitor Lambda cold starts
   - Review SQS queue depth

### Log Analysis

```bash
# Search for errors in handler
aws logs filter-log-events \
  --log-group-name /aws/lambda/revops-slack-bedrock-handler \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# Search for errors in processor
aws logs filter-log-events \
  --log-group-name /aws/lambda/revops-slack-bedrock-processor \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000
```

## 🔄 Migration from Previous Implementation

This implementation replaces the previous `tools/slack/` directory with:

- ✅ **Better Architecture**: API Gateway + SQS instead of Function URL
- ✅ **Improved Performance**: Direct Bedrock Agent invocation vs broken Flow
- ✅ **Enhanced Security**: Proper IAM roles and signature verification
- ✅ **Better Monitoring**: CloudWatch integration and structured logging
- ✅ **Conversation Management**: Native Bedrock sessions vs manual DynamoDB

### Migration Steps

1. Deploy new architecture
2. Update Slack app configuration
3. Test functionality
4. Clean up old resources (handled automatically by deployment script)

## 🏆 Benefits over Previous Implementation

| Feature | Previous | AWS Best Practices |
|---------|----------|-------------------|
| Entry Point | Function URL | API Gateway |
| Processing | Synchronous | Asynchronous (SQS) |
| Agent Integration | Broken Flow | Direct Agent |
| Conversation Context | Manual DynamoDB | Native Bedrock Sessions |
| Error Handling | Basic try/catch | Dead Letter Queues |
| Monitoring | Limited | Full CloudWatch |
| Security | Basic | IAM + Signature Verification |
| Scalability | Limited | Auto-scaling |

## 📚 Additional Documentation

- [Architecture Details](docs/architecture.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [API Reference](docs/api-reference.md)

## 🤝 Support

For issues or questions:
1. Check CloudWatch logs
2. Review troubleshooting guide
3. Monitor SQS queues and Lambda metrics
4. Verify Slack app configuration

## 📄 License

This implementation follows AWS best practices and is designed for the RevOps AI Framework integration.