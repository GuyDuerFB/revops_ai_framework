#!/usr/bin/env python3
"""
Enhanced Monitoring Deployment Script
Deploy comprehensive logging and monitoring for RevOps Slack-Bedrock Integration
"""

import boto3
import json
import logging
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def deploy_monitoring_stack():
    """Deploy the enhanced monitoring CloudFormation stack"""
    
    logger.info("🚀 Deploying Enhanced Monitoring Stack")
    
    # AWS configuration
    profile_name = "FireboltSystemAdministrator-740202120544"
    region_name = "us-east-1"
    stack_name = "revops-slack-bedrock-monitoring"
    
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    cf_client = session.client('cloudformation')
    
    # Read CloudFormation template
    template_path = Path(__file__).parent / "enhanced-logging-solution.yaml"
    with open(template_path, 'r') as f:
        template_body = f.read()
    
    try:
        # Check if stack exists
        try:
            cf_client.describe_stacks(StackName=stack_name)
            stack_exists = True
            logger.info(f"Stack {stack_name} exists, updating...")
        except cf_client.exceptions.ClientError:
            stack_exists = False
            logger.info(f"Stack {stack_name} does not exist, creating...")
        
        # Deploy or update stack
        if stack_exists:
            response = cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=[
                    {
                        'ParameterKey': 'ProjectName',
                        'ParameterValue': 'revops-slack-bedrock'
                    }
                ],
                Capabilities=['CAPABILITY_IAM']
            )
            operation = "UPDATE"
        else:
            response = cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=[
                    {
                        'ParameterKey': 'ProjectName',
                        'ParameterValue': 'revops-slack-bedrock'
                    }
                ],
                Capabilities=['CAPABILITY_IAM']
            )
            operation = "CREATE"
        
        logger.info(f"Stack {operation} initiated: {response['StackId']}")
        
        # Wait for stack completion
        waiter = cf_client.get_waiter(f'stack_{operation.lower()}_complete')
        logger.info("Waiting for stack operation to complete...")
        
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 30,
                'MaxAttempts': 40
            }
        )
        
        # Get stack outputs
        stack_info = cf_client.describe_stacks(StackName=stack_name)
        outputs = stack_info['Stacks'][0].get('Outputs', [])
        
        logger.info("✅ Monitoring stack deployed successfully!")
        logger.info("\n📊 Monitoring Resources Created:")
        
        for output in outputs:
            logger.info(f"  • {output['Description']}: {output['OutputValue']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to deploy monitoring stack: {str(e)}")
        return False

def setup_log_insights_queries():
    """Set up additional CloudWatch Insights queries for troubleshooting"""
    
    logger.info("🔍 Setting up CloudWatch Insights queries")
    
    profile_name = "FireboltSystemAdministrator-740202120544"
    region_name = "us-east-1"
    
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    logs_client = session.client('logs')
    
    # Queries for different failure scenarios
    queries = [
        {
            'name': 'revops-bedrock-timeout-analysis',
            'queryString': '''
                fields @timestamp, @message, @requestId
                | filter @message like /ReadTimeoutError/ or @message like /timed out/
                | parse @message /RequestId: (?<reqId>[a-f0-9-]+)/
                | parse @message /Message preview: (?<userQuery>.*?)\\.\\.\\./
                | stats count() by userQuery, reqId
                | sort count desc
            ''',
            'logGroups': ['/aws/lambda/revops-slack-bedrock-processor']
        },
        {
            'name': 'revops-user-request-complexity',
            'queryString': '''
                fields @timestamp, @message
                | filter @message like /Message preview:/
                | parse @message "Message preview: *" as userQuery
                | fields @timestamp, userQuery, strlen(userQuery) as queryLength
                | stats avg(queryLength), count() by bin(1h)
                | sort @timestamp desc
            ''',
            'logGroups': ['/aws/lambda/revops-slack-bedrock-processor']
        },
        {
            'name': 'revops-collaboration-patterns',
            'queryString': '''
                fields @timestamp, @message
                | filter @message like /collaborator/ or @message like /DataAgent/ or @message like /WebSearchAgent/
                | parse @message /(?<agent>DataAgent|WebSearchAgent|ExecutionAgent)/
                | stats count() by agent, bin(1h)
                | sort @timestamp desc
            ''',
            'logGroups': ['/aws/lambda/revops-slack-bedrock-processor']
        },
        {
            'name': 'revops-error-correlation',
            'queryString': '''
                fields @timestamp, @message, @requestId
                | filter @message like /ERROR/ or @message like /Exception/
                | parse @message /(?<errorType>\\w+Error|\\w+Exception)/
                | stats count() by errorType, bin(1h)
                | sort count desc
            ''',
            'logGroups': [
                '/aws/lambda/revops-slack-bedrock-processor',
                '/aws/lambda/revops-slack-bedrock-handler'
            ]
        }
    ]
    
    created_queries = []
    
    for query in queries:
        try:
            response = logs_client.put_query_definition(
                name=query['name'],
                queryString=query['queryString'],
                logGroupNames=query['logGroups']
            )
            created_queries.append(query['name'])
            logger.info(f"  ✅ Created query: {query['name']}")
        except Exception as e:
            logger.warning(f"  ⚠️ Failed to create query {query['name']}: {str(e)}")
    
    logger.info(f"📋 Created {len(created_queries)} CloudWatch Insights queries")
    return created_queries

def create_troubleshooting_runbook():
    """Create a troubleshooting runbook with common scenarios"""
    
    runbook_content = """# RevOps Slack Bot Troubleshooting Runbook

## Quick Diagnosis Commands

### 1. Check Recent Errors
```bash
aws logs filter-log-events \\
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \\
  --start-time $(date -u -d '1 hour ago' +%s)000 \\
  --filter-pattern 'ERROR' \\
  --region us-east-1 \\
  --profile FireboltSystemAdministrator-740202120544
```

### 2. Check Dead Letter Queue
```bash
aws sqs get-queue-attributes \\
  --queue-url 'https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-dlq' \\
  --attribute-names ApproximateNumberOfMessages \\
  --region us-east-1 \\
  --profile FireboltSystemAdministrator-740202120544
```

### 3. Check Lambda Metrics
```bash
aws cloudwatch get-metric-statistics \\
  --namespace AWS/Lambda \\
  --metric-name Duration \\
  --dimensions Name=FunctionName,Value=revops-slack-bedrock-processor \\
  --start-time $(date -u -d '1 hour ago' --iso-8601) \\
  --end-time $(date -u --iso-8601) \\
  --period 300 \\
  --statistics Maximum,Average \\
  --region us-east-1 \\
  --profile FireboltSystemAdministrator-740202120544
```

## Common Failure Scenarios

### Scenario 1: Bedrock Agent Timeout (Primary Issue)
**Symptoms**: ReadTimeoutError, 60+ second duration
**Root Cause**: Complex queries requiring multi-agent coordination
**Solutions**:
1. Increase Lambda timeout to 5 minutes (300s)
2. Implement query complexity analysis
3. Add Bedrock client timeout configuration
4. Implement query breaking for complex analyses

### Scenario 2: High Dead Letter Queue Messages
**Symptoms**: Messages in DLQ, repeated failures
**Root Cause**: Systematic issues with Bedrock connectivity
**Solutions**:
1. Check Bedrock agent health
2. Verify IAM permissions
3. Check for service limits

### Scenario 3: Slack Signature Verification Failures
**Symptoms**: 401 errors, invalid signature
**Root Cause**: Clock skew or secret rotation
**Solutions**:
1. Verify secrets in AWS Secrets Manager
2. Check timestamp tolerance
3. Validate Slack app configuration

## CloudWatch Insights Queries

### Find Timeout Patterns
```
fields @timestamp, @message, @requestId
| filter @message like /ReadTimeoutError/
| parse @message /Message preview: (?<query>.*?)\\.\\.\\./
| stats count() by query
| sort count desc
```

### Analyze Request Complexity
```
fields @timestamp, @message
| filter @message like /Message preview:/
| parse @message "Message preview: *" as userQuery
| fields strlen(userQuery) as queryLength, userQuery
| sort queryLength desc
```

## Immediate Actions for Timeout Issues

1. **Increase Lambda Timeout**:
```bash
aws lambda update-function-configuration \\
  --function-name revops-slack-bedrock-processor \\
  --timeout 300 \\
  --region us-east-1 \\
  --profile FireboltSystemAdministrator-740202120544
```

2. **Monitor Queue Backlog**:
```bash
aws sqs get-queue-attributes \\
  --queue-url 'https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-processing-queue' \\
  --attribute-names ApproximateNumberOfMessages \\
  --region us-east-1 \\
  --profile FireboltSystemAdministrator-740202120544
```

3. **Clear Dead Letter Queue** (if needed):
```bash
aws sqs purge-queue \\
  --queue-url 'https://sqs.us-east-1.amazonaws.com/740202120544/revops-slack-bedrock-dlq' \\
  --region us-east-1 \\
  --profile FireboltSystemAdministrator-740202120544
```

## Prevention Strategies

1. **Query Complexity Analysis**: Implement pre-processing to estimate query complexity
2. **Progressive Timeouts**: Start with shorter timeouts for simple queries
3. **Query Breaking**: Split complex analyses into smaller chunks
4. **Caching**: Cache common analysis results
5. **Circuit Breaker**: Implement failure detection and recovery
"""
    
    runbook_path = Path(__file__).parent / "troubleshooting-runbook.md"
    with open(runbook_path, 'w') as f:
        f.write(runbook_content)
    
    logger.info(f"📖 Created troubleshooting runbook: {runbook_path}")
    return runbook_path

def main():
    """Main deployment function"""
    
    logger.info("🌟 RevOps Enhanced Monitoring Deployment")
    logger.info("=" * 60)
    
    # Step 1: Deploy monitoring stack
    monitoring_success = deploy_monitoring_stack()
    
    if not monitoring_success:
        logger.error("❌ Failed to deploy monitoring stack")
        return False
    
    # Step 2: Set up CloudWatch Insights queries
    time.sleep(10)  # Allow stack to fully deploy
    queries_created = setup_log_insights_queries()
    
    # Step 3: Create troubleshooting runbook
    runbook_path = create_troubleshooting_runbook()
    
    logger.info("\n🎉 Enhanced Monitoring Deployment Complete!")
    logger.info("📊 CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-slack-bedrock-monitoring")
    logger.info(f"📖 Troubleshooting Runbook: {runbook_path}")
    logger.info(f"🔍 CloudWatch Insights Queries: {len(queries_created)} created")
    
    logger.info("\n🔧 Immediate Actions Required:")
    logger.info("1. Increase processor Lambda timeout to 300 seconds")
    logger.info("2. Subscribe to SNS alerts topic for notifications")
    logger.info("3. Review troubleshooting runbook for common scenarios")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)