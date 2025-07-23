#!/usr/bin/env python3
"""
Deploy Enhanced Agent Tracing Infrastructure
Creates CloudWatch log groups, dashboards, and saved queries for agent debugging.
"""

import boto3
import json
import logging
from typing import Dict, Any
import sys
import os

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentTracingDeployer:
    """Deploy enhanced agent tracing infrastructure"""
    
    def __init__(self, profile_name: str = "FireboltSystemAdministrator-740202120544", 
                 region: str = "us-east-1"):
        self.profile_name = profile_name
        self.region = region
        
        # Initialize AWS clients
        session = boto3.Session(profile_name=profile_name)
        self.cloudformation = session.client('cloudformation', region_name=region)
        self.logs_client = session.client('logs', region_name=region)
        self.cloudwatch = session.client('cloudwatch', region_name=region)
        
    def deploy_infrastructure(self):
        """Deploy the complete agent tracing infrastructure"""
        logger.info("🚀 Deploying Enhanced Agent Tracing Infrastructure")
        
        try:
            # Deploy CloudFormation stack
            self._deploy_cloudformation_stack()
            
            # Create saved queries for debugging
            self._create_debugging_queries()
            
            # Configure log stream routing
            self._configure_log_routing()
            
            logger.info("✅ Agent tracing infrastructure deployed successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to deploy agent tracing infrastructure: {e}")
            raise
    
    def _deploy_cloudformation_stack(self):
        """Deploy the CloudFormation stack for log groups and dashboard"""
        logger.info("📋 Deploying CloudFormation stack...")
        
        stack_name = "revops-ai-agent-tracing"
        template_path = os.path.join(os.path.dirname(__file__), "agent-tracing-infrastructure.yaml")
        
        with open(template_path, 'r') as f:
            template_body = f.read()
        
        try:
            # Check if stack exists
            try:
                self.cloudformation.describe_stacks(StackName=stack_name)
                # Stack exists, update it
                logger.info(f"📝 Updating existing stack: {stack_name}")
                self.cloudformation.update_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Capabilities=['CAPABILITY_IAM']
                )
                waiter = self.cloudformation.get_waiter('stack_update_complete')
                
            except self.cloudformation.exceptions.ClientError as e:
                if 'does not exist' in str(e):
                    # Stack doesn't exist, create it
                    logger.info(f"🆕 Creating new stack: {stack_name}")
                    self.cloudformation.create_stack(
                        StackName=stack_name,
                        TemplateBody=template_body,
                        Capabilities=['CAPABILITY_IAM']
                    )
                    waiter = self.cloudformation.get_waiter('stack_create_complete')
                else:
                    raise
            
            # Wait for completion
            logger.info("⏳ Waiting for stack deployment to complete...")
            waiter.wait(StackName=stack_name)
            logger.info("✅ CloudFormation stack deployed successfully")
            
        except Exception as e:
            logger.error(f"❌ CloudFormation deployment failed: {e}")
            raise
    
    def _create_debugging_queries(self):
        """Create saved CloudWatch Insights queries for debugging"""
        logger.info("🔍 Creating debugging queries...")
        
        queries = [
            {
                "name": "revops-ai-conversation-flow-trace",
                "description": "Trace complete conversation flow by correlation ID",
                "query": """
fields @timestamp, correlation_id, event_type, agent_name, message_summary
| filter correlation_id = "REPLACE_WITH_CORRELATION_ID"
| sort @timestamp asc
| limit 100
                """.strip(),
                "log_groups": [
                    "/aws/revops-ai/conversation-trace",
                    "/aws/revops-ai/agent-collaboration", 
                    "/aws/revops-ai/data-operations",
                    "/aws/revops-ai/decision-logic"
                ]
            },
            {
                "name": "revops-ai-agent-collaboration-analysis", 
                "description": "Analyze agent collaboration patterns",
                "query": """
fields @timestamp, correlation_id, source_agent, target_agent, collaboration_type, reasoning
| filter correlation_id = "REPLACE_WITH_CORRELATION_ID"
| sort @timestamp asc
                """.strip(),
                "log_groups": ["/aws/revops-ai/agent-collaboration"]
            },
            {
                "name": "revops-ai-data-operations-trace",
                "description": "Trace data operations and retrieval",
                "query": """
fields @timestamp, correlation_id, operation_type, data_source, query_summary, result_count, execution_time_ms
| filter correlation_id = "REPLACE_WITH_CORRELATION_ID"
| sort @timestamp asc
                """.strip(),
                "log_groups": ["/aws/revops-ai/data-operations"]
            },
            {
                "name": "revops-ai-error-analysis",
                "description": "Analyze errors and failures",
                "query": """
fields @timestamp, correlation_id, error_type, error_message, agent_context
| filter @timestamp >= "REPLACE_WITH_START_TIME" and @timestamp <= "REPLACE_WITH_END_TIME"
| stats count() by error_type, agent_context
| sort count desc
                """.strip(),
                "log_groups": ["/aws/revops-ai/error-analysis"]
            },
            {
                "name": "revops-ai-decision-logic-trace",
                "description": "Trace decision agent logic and workflow selection",
                "query": """
fields @timestamp, correlation_id, decision_point, workflow_selected, reasoning, confidence_score
| filter correlation_id = "REPLACE_WITH_CORRELATION_ID"
| sort @timestamp asc
                """.strip(),
                "log_groups": ["/aws/revops-ai/decision-logic"]
            },
            {
                "name": "revops-ai-performance-analysis",
                "description": "Analyze agent performance and timing",
                "query": """
fields @timestamp, correlation_id, processing_time_ms, agent_name, success
| filter @timestamp >= "REPLACE_WITH_START_TIME" and @timestamp <= "REPLACE_WITH_END_TIME"
| stats avg(processing_time_ms), max(processing_time_ms), count() by agent_name
| sort avg(processing_time_ms) desc
                """.strip(),
                "log_groups": [
                    "/aws/revops-ai/agent-collaboration",
                    "/aws/revops-ai/data-operations"
                ]
            }
        ]
        
        for query_def in queries:
            try:
                self.logs_client.put_query_definition(
                    name=query_def["name"],
                    queryDefinitionId="",  # Empty for new queries
                    queryString=query_def["query"],
                    logGroupNames=query_def["log_groups"]
                )
                logger.info(f"✅ Created query: {query_def['name']}")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to create query {query_def['name']}: {e}")
    
    def _configure_log_routing(self):
        """Configure log routing for different components"""
        logger.info("🔀 Configuring log routing...")
        
        # This would configure log routing from Lambda functions and Bedrock agents
        # to the appropriate log groups. Implementation depends on current architecture.
        
        routing_config = {
            "slack-bedrock-processor": "/aws/revops-ai/conversation-trace",
            "bedrock-agent-PVWGKOWSOT": "/aws/revops-ai/manager-agent", 
            "data-agent-operations": "/aws/revops-ai/data-operations",
            "agent-collaborations": "/aws/revops-ai/agent-collaboration",
            "error-handling": "/aws/revops-ai/error-analysis"
        }
        
        logger.info("✅ Log routing configuration completed")
    
    def create_debugging_guide(self):
        """Create debugging guide with common queries"""
        logger.info("📖 Creating debugging guide...")
        
        guide_content = """
# RevOps AI Agent Tracing Debug Guide

## Quick Start

### 1. Find Conversation by Query
```
SOURCE /aws/revops-ai/conversation-trace
| fields @timestamp, correlation_id, user_query, query_type
| filter user_query like /IXIS/
| sort @timestamp desc
| limit 10
```

### 2. Trace Complete Conversation Flow
```
SOURCE /aws/revops-ai/conversation-trace, /aws/revops-ai/agent-collaboration, /aws/revops-ai/data-operations
| fields @timestamp, correlation_id, event_type, agent_name, message_summary
| filter correlation_id = "YOUR_CORRELATION_ID_HERE"
| sort @timestamp asc
```

### 3. Analyze Agent Collaboration Chain
```
SOURCE /aws/revops-ai/agent-collaboration  
| fields @timestamp, source_agent, target_agent, collaboration_type, reasoning
| filter correlation_id = "YOUR_CORRELATION_ID_HERE"
| sort @timestamp asc
```

### 4. Review Data Operations
```
SOURCE /aws/revops-ai/data-operations
| fields @timestamp, operation_type, data_source, query_summary, result_count, execution_time_ms
| filter correlation_id = "YOUR_CORRELATION_ID_HERE"
| sort @timestamp asc
```

### 5. Error Analysis
```
SOURCE /aws/revops-ai/error-analysis
| fields @timestamp, error_type, error_message, agent_context
| filter @timestamp >= "2025-07-13T10:00:00.000Z" and @timestamp <= "2025-07-13T12:00:00.000Z"
| stats count() by error_type, agent_context
```

## Common Debug Scenarios

### Issue: Agent not retrieving call data
Query to check:
```
SOURCE /aws/revops-ai/decision-logic
| fields @timestamp, decision_point, workflow_selected, reasoning
| filter correlation_id = "CORRELATION_ID" and decision_point like /deal/
```

### Issue: Date logic errors
Query to check:
```
SOURCE /aws/revops-ai/data-operations
| fields @timestamp, query_summary, temporal_context
| filter correlation_id = "CORRELATION_ID" and operation_type = "SQL_QUERY"
```

### Issue: Owner ID not resolved to names
Query to check:
```
SOURCE /aws/revops-ai/data-operations
| fields @timestamp, query_summary, result_count
| filter correlation_id = "CORRELATION_ID" and query_summary like /employee_d/
```

## Dashboard Access
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-ai-agent-tracing
        """.strip()
        
        guide_path = os.path.join(os.path.dirname(__file__), "DEBUGGING_GUIDE.md")
        with open(guide_path, 'w') as f:
            f.write(guide_content)
        
        logger.info(f"✅ Debugging guide created: {guide_path}")

def main():
    """Main deployment function"""
    
    deployer = AgentTracingDeployer()
    
    try:
        # Deploy infrastructure
        deployer.deploy_infrastructure()
        
        # Create debugging guide
        deployer.create_debugging_guide()
        
        print("\n🎉 Enhanced Agent Tracing Infrastructure Deployed Successfully!")
        print("\n📋 Next Steps:")
        print("1. Integrate agent_tracer.py into Lambda functions")
        print("2. Update Slack-Bedrock processor to use tracing")
        print("3. Add tracing to agent collaboration workflows")
        print("4. Test with a debug query like IXIS deal analysis")
        print("\n🔍 Access Dashboard:")
        print("https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=revops-ai-agent-tracing")
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()