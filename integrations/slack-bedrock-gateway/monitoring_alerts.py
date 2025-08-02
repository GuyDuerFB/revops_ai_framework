#!/usr/bin/env python3
"""
CloudWatch Monitoring Alerts for RevOps AI Framework
Creates alarms for conversation schema import failures and monitoring system issues
"""

import boto3
import json
from datetime import datetime

AWS_PROFILE = "FireboltSystemAdministrator-740202120544"
AWS_REGION = "us-east-1"

def create_schema_import_alarm():
    """Create CloudWatch alarm for conversation schema import failures"""
    
    session = boto3.Session(profile_name=AWS_PROFILE)
    cloudwatch = session.client('cloudwatch', region_name=AWS_REGION)
    
    alarm_name = "RevOps-ConversationSchemaImportFailure"
    
    try:
        response = cloudwatch.put_metric_alarm(
            AlarmName=alarm_name,
            ComparisonOperator='LessThanThreshold',
            EvaluationPeriods=1,
            MetricName='ConversationSchemaImportSuccess',
            Namespace='RevOps-AI/Monitoring',
            Period=300,  # 5 minutes
            Statistic='Average',
            Threshold=1.0,
            ActionsEnabled=True,
            AlarmActions=[
                # Add SNS topic ARN here if you want email/SMS notifications
                # 'arn:aws:sns:us-east-1:740202120544:revops-alerts'
            ],
            AlarmDescription='Alerts when conversation schema import fails in Lambda functions',
            Dimensions=[
                {
                    'Name': 'Environment',
                    'Value': 'Production'
                }
            ],
            Unit='Count',
            TreatMissingData='breaching'  # Treat missing data as alarm condition
        )
        
        print(f"✅ Created CloudWatch alarm: {alarm_name}")
        print(f"   Alarm ARN: {response.get('ResponseMetadata', {}).get('RequestId', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create alarm {alarm_name}: {e}")
        return False

def create_conversation_tracking_dashboard():
    """Create CloudWatch dashboard for monitoring conversation tracking health"""
    
    session = boto3.Session(profile_name=AWS_PROFILE)
    cloudwatch = session.client('cloudwatch', region_name=AWS_REGION)
    
    dashboard_name = "RevOps-ConversationTracking"
    
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        [ "RevOps-AI/Monitoring", "ConversationSchemaImportSuccess", "Environment", "Production" ]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": AWS_REGION,
                    "title": "Conversation Schema Import Success Rate",
                    "period": 300,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 1
                        }
                    }
                }
            },
            {
                "type": "log",
                "x": 0,
                "y": 6,
                "width": 24,
                "height": 6,
                "properties": {
                    "query": "SOURCE '/aws/lambda/revops-slack-bedrock-processor'\n| fields @timestamp, @message\n| filter @message like /schema/\n| sort @timestamp desc\n| limit 20",
                    "region": AWS_REGION,
                    "title": "Recent Schema Import Log Messages",
                    "view": "table"
                }
            },
            {
                "type": "log",
                "x": 0,
                "y": 12,
                "width": 24,
                "height": 6,
                "properties": {
                    "query": "SOURCE '/aws/revops-ai/conversation-units'\n| fields @timestamp, @message\n| filter @message like /\"id\":/\n| stats count() by bin(5m)\n| sort @timestamp desc",
                    "region": AWS_REGION,
                    "title": "Conversation Units Created (Per 5 Minutes)",
                    "view": "table"
                }
            }
        ]
    }
    
    try:
        response = cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_body)
        )
        
        print(f"✅ Created CloudWatch dashboard: {dashboard_name}")
        print(f"   Dashboard URL: https://console.aws.amazon.com/cloudwatch/home?region={AWS_REGION}#dashboards:name={dashboard_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create dashboard {dashboard_name}: {e}")
        return False

def create_log_metric_filter():
    """Create CloudWatch log metric filter to detect fallback usage"""
    
    session = boto3.Session(profile_name=AWS_PROFILE)
    logs_client = session.client('logs', region_name=AWS_REGION)
    
    log_group_name = '/aws/lambda/revops-slack-bedrock-processor'
    filter_name = 'ConversationSchemaFallbackDetection'
    
    try:
        # Create metric filter that detects when fallback dictionary tracking is used
        response = logs_client.put_metric_filter(
            logGroupName=log_group_name,
            filterName=filter_name,
            filterPattern='[timestamp, requestId, level="WARNING", message="conversation_schema import failed*"]',
            metricTransformations=[
                {
                    'metricName': 'ConversationSchemaImportFailures',
                    'metricNamespace': 'RevOps-AI/Monitoring',
                    'metricValue': '1'
                }
            ]
        )
        
        print(f"✅ Created log metric filter: {filter_name}")
        print(f"   Log Group: {log_group_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create log metric filter {filter_name}: {e}")
        return False

def main():
    """Set up all monitoring alerts and dashboards"""
    print("🚨 Setting up RevOps AI Monitoring Alerts")
    print("=" * 60)
    
    success_count = 0
    total_count = 3
    
    # Create schema import alarm
    print("📊 Creating schema import failure alarm...")
    if create_schema_import_alarm():
        success_count += 1
    
    # Create monitoring dashboard
    print("📈 Creating conversation tracking dashboard...")
    if create_conversation_tracking_dashboard():
        success_count += 1
    
    # Create log metric filter
    print("🔍 Creating fallback detection metric filter...")
    if create_log_metric_filter():
        success_count += 1
    
    print(f"\n✅ Monitoring setup completed: {success_count}/{total_count} successful")
    
    if success_count == total_count:
        print("🎉 All monitoring alerts and dashboards created successfully!")
        print("\n📋 What's been set up:")
        print("   ✅ CloudWatch alarm for schema import failures")
        print("   ✅ Conversation tracking health dashboard")
        print("   ✅ Log metric filter for fallback detection")
        print("\n🔗 Access your dashboard:")
        print(f"   https://console.aws.amazon.com/cloudwatch/home?region={AWS_REGION}#dashboards:name=RevOps-ConversationTracking")
    else:
        print("⚠️  Some monitoring components failed to create - check error messages above")

if __name__ == "__main__":
    main()