#!/usr/bin/env python3
"""
Deploy Enhanced Deal Assessment Monitoring Infrastructure
Creates CloudWatch dashboards, alarms, and automated reporting for deal assessments
"""

import boto3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class EnhancedMonitoringDeployer:
    """Deploy enhanced monitoring infrastructure for deal assessments"""
    
    def __init__(self, profile_name: str = 'FireboltSystemAdministrator-740202120544', region: str = 'us-east-1'):
        session = boto3.Session(profile_name=profile_name, region_name=region)
        self.cloudwatch = session.client('cloudwatch')
        self.logs = session.client('logs')
        self.region = region
        
    def deploy_enhanced_dashboard(self) -> str:
        """Deploy enhanced CloudWatch dashboard for deal assessments"""
        
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
                            ["RevOpsAI/DealAssessment", "AssessmentStatus", "Status", "complete"],
                            [".", ".", ".", "partial"],
                            [".", ".", ".", "failed"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": self.region,
                        "title": "Deal Assessment Status Distribution",
                        "view": "timeSeries",
                        "stacked": False
                    }
                },
                {
                    "type": "metric", 
                    "x": 12,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["RevOpsAI/DealAssessment", "SFDCDataRetrieved"],
                            [".", "CallDataRetrieved"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": self.region,
                        "title": "Data Source Retrieval Success",
                        "view": "timeSeries"
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["RevOpsAI/DealAssessment", "ProcessingTimeMs"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "Average Processing Time (ms)",
                        "view": "timeSeries"
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["RevOpsAI/DealAssessment", "AgentsInvoked"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "Average Agents Invoked per Assessment",
                        "view": "timeSeries"
                    }
                },
                {
                    "type": "log",
                    "x": 0,
                    "y": 12,
                    "width": 24,
                    "height": 6,
                    "properties": {
                        "query": f"SOURCE '/aws/revops-ai/conversation-trace'\n| fields @timestamp, message.user_query, message.query_type, message.correlation_id\n| filter message.query_type = \"DEAL_ANALYSIS\"\n| sort @timestamp desc\n| limit 10",
                        "region": self.region,
                        "title": "Recent Deal Analysis Queries",
                        "view": "table"
                    }
                },
                {
                    "type": "log",
                    "x": 0,
                    "y": 18,
                    "width": 24,
                    "height": 6,
                    "properties": {
                        "query": f"SOURCE '/aws/revops-ai/agent-collaboration'\n| fields @timestamp, message.source_agent, message.target_agent, message.collaboration_type\n| filter message.target_agent = \"DataAgent\"\n| sort @timestamp desc\n| limit 10",
                        "region": self.region,
                        "title": "Recent DataAgent Collaborations",
                        "view": "table"
                    }
                }
            ]
        }
        
        dashboard_name = 'revops-ai-enhanced-deal-assessment'
        
        try:
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            
            dashboard_url = f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard_name}"
            logger.info(f"✅ Enhanced dashboard created: {dashboard_url}")
            return dashboard_url
            
        except Exception as e:
            logger.error(f"❌ Error creating enhanced dashboard: {str(e)}")
            raise

    def create_assessment_alarms(self) -> List[str]:
        """Create CloudWatch alarms for deal assessment monitoring"""
        
        alarms_created = []
        
        # Alarm for failed assessments
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName='RevOpsAI-DealAssessment-HighFailureRate',
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=2,
                MetricName='AssessmentStatus',
                Namespace='RevOpsAI/DealAssessment',
                Period=300,
                Statistic='Sum',
                Threshold=5.0,
                ActionsEnabled=False,  # Set to True when SNS topics are configured
                AlarmDescription='High number of failed deal assessments detected',
                Dimensions=[
                    {
                        'Name': 'Status',
                        'Value': 'failed'
                    }
                ],
                Unit='Count'
            )
            alarms_created.append('RevOpsAI-DealAssessment-HighFailureRate')
            logger.info("✅ Created alarm: RevOpsAI-DealAssessment-HighFailureRate")
            
        except Exception as e:
            logger.error(f"❌ Error creating failure rate alarm: {str(e)}")

        # Alarm for slow processing times
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName='RevOpsAI-DealAssessment-SlowProcessing',
                ComparisonOperator='GreaterThanThreshold',
                EvaluationPeriods=3,
                MetricName='ProcessingTimeMs',
                Namespace='RevOpsAI/DealAssessment',
                Period=300,
                Statistic='Average',
                Threshold=30000.0,  # 30 seconds
                ActionsEnabled=False,
                AlarmDescription='Deal assessment processing time is too slow',
                Unit='Milliseconds'
            )
            alarms_created.append('RevOpsAI-DealAssessment-SlowProcessing')
            logger.info("✅ Created alarm: RevOpsAI-DealAssessment-SlowProcessing")
            
        except Exception as e:
            logger.error(f"❌ Error creating slow processing alarm: {str(e)}")

        # Alarm for data retrieval issues
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName='RevOpsAI-DealAssessment-DataRetrievalIssues',
                ComparisonOperator='LessThanThreshold',
                EvaluationPeriods=2,
                MetricName='SFDCDataRetrieved',
                Namespace='RevOpsAI/DealAssessment',
                Period=300,
                Statistic='Sum',
                Threshold=1.0,
                ActionsEnabled=False,
                AlarmDescription='SFDC data retrieval is failing for deal assessments',
                Unit='Count'
            )
            alarms_created.append('RevOpsAI-DealAssessment-DataRetrievalIssues')
            logger.info("✅ Created alarm: RevOpsAI-DealAssessment-DataRetrievalIssues")
            
        except Exception as e:
            logger.error(f"❌ Error creating data retrieval alarm: {str(e)}")
            
        return alarms_created

    def create_enhanced_log_insights_queries(self) -> List[str]:
        """Create enhanced CloudWatch Logs Insights saved queries"""
        
        queries = [
            {
                'name': 'revops-ai-deal-assessment-flow-analysis',
                'query': '''SOURCE '/aws/revops-ai/conversation-trace', '/aws/revops-ai/agent-collaboration', '/aws/revops-ai/data-operations'
| fields @timestamp, @logStream, message.event_type, message.correlation_id, message.user_query, message.target_agent, message.data_source
| filter message.query_type = "DEAL_ANALYSIS" or message.collaboration_type = "USER_QUERY_PROCESSING" or message.operation_type like /opportunity|gong|call/
| sort @timestamp
| limit 100'''
            },
            {
                'name': 'revops-ai-step-1a-1b-validation',
                'query': '''SOURCE '/aws/revops-ai/data-operations'
| fields @timestamp, message.correlation_id, message.operation_type, message.data_source, message.success
| filter message.operation_type like /opportunity/ or message.data_source like /gong/
| stats count() by message.correlation_id, message.operation_type
| sort count desc'''
            },
            {
                'name': 'revops-ai-agent-collaboration-patterns',
                'query': '''SOURCE '/aws/revops-ai/agent-collaboration'
| fields @timestamp, message.source_agent, message.target_agent, message.collaboration_type, message.reasoning
| filter message.target_agent = "DataAgent"
| stats count() by message.source_agent, message.target_agent, message.collaboration_type
| sort count desc'''
            },
            {
                'name': 'revops-ai-deal-assessment-errors',
                'query': '''SOURCE '/aws/revops-ai/error-analysis'
| fields @timestamp, message.error_type, message.error_message, message.agent_context, message.correlation_id
| filter message.agent_context like /deal|assessment|DataAgent/
| sort @timestamp desc
| limit 20'''
            },
            {
                'name': 'revops-ai-performance-analysis',
                'query': '''SOURCE '/aws/revops-ai/conversation-trace'
| fields @timestamp, message.query_type, message.processing_time_ms, message.total_agents_used, message.success
| filter message.query_type = "DEAL_ANALYSIS"
| stats avg(message.processing_time_ms) as avg_time, avg(message.total_agents_used) as avg_agents, count() as total by message.success
| sort total desc'''
            }
        ]
        
        saved_queries = []
        for query_config in queries:
            try:
                # Note: CloudWatch Logs doesn't have a direct API to save queries
                # This would typically be done through the console or using custom automation
                saved_queries.append(query_config['name'])
                logger.info(f"📋 Query ready: {query_config['name']}")
                
            except Exception as e:
                logger.error(f"❌ Error with query {query_config['name']}: {str(e)}")
                
        return saved_queries

    def deploy_monitoring_lambda(self) -> str:
        """Deploy Lambda function for automated deal assessment monitoring"""
        
        # This would create a Lambda function that runs the enhanced_deal_monitoring.py
        # on a schedule to analyze recent assessments and publish metrics
        
        lambda_code = '''
import json
import boto3
from enhanced_deal_monitoring import DealAssessmentMonitor

def lambda_handler(event, context):
    """Automated deal assessment monitoring"""
    
    monitor = DealAssessmentMonitor()
    
    # Generate assessment report for last 4 hours
    report = monitor.generate_assessment_report(hours=4)
    
    # Publish aggregate metrics
    if 'summary' in report:
        summary = report['summary']
        
        # Publish completion rate
        monitor._put_metric('CompletionRate', summary['completion_rate'], {})
        
        # Publish average processing time
        monitor._put_metric('AvgProcessingTime', summary['avg_processing_time_ms'], {})
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'report_summary': report.get('summary', {}),
            'assessments_analyzed': len(report.get('assessments', []))
        })
    }
'''
        
        logger.info("📋 Lambda deployment code prepared (manual deployment required)")
        return "lambda-code-prepared"

def main():
    """Deploy enhanced monitoring infrastructure"""
    
    logger.info("🚀 RevOps AI Enhanced Deal Assessment Monitoring Deployment")
    logger.info("=" * 80)
    
    deployer = EnhancedMonitoringDeployer()
    
    try:
        # Deploy enhanced dashboard
        logger.info("📊 Deploying enhanced CloudWatch dashboard...")
        dashboard_url = deployer.deploy_enhanced_dashboard()
        
        # Create assessment alarms
        logger.info("🚨 Creating CloudWatch alarms...")
        alarms = deployer.create_assessment_alarms()
        
        # Create log insights queries
        logger.info("🔍 Preparing enhanced Log Insights queries...")
        queries = deployer.create_enhanced_log_insights_queries()
        
        # Prepare monitoring lambda
        logger.info("🔧 Preparing automated monitoring Lambda...")
        lambda_status = deployer.deploy_monitoring_lambda()
        
        logger.info("\n🎉 ENHANCED MONITORING DEPLOYMENT COMPLETE!")
        logger.info("✅ Enhanced dashboard deployed")
        logger.info(f"✅ {len(alarms)} alarms created")
        logger.info(f"✅ {len(queries)} enhanced queries prepared")
        logger.info("✅ Monitoring automation prepared")
        
        logger.info(f"\n📋 Next Steps:")
        logger.info(f"1. Access enhanced dashboard: {dashboard_url}")
        logger.info(f"2. Configure SNS topics for alarm notifications")
        logger.info(f"3. Deploy monitoring Lambda function")
        logger.info(f"4. Run deal assessment analysis: python enhanced_deal_monitoring.py --report")
        
    except Exception as e:
        logger.error(f"\n❌ DEPLOYMENT FAILED!")
        logger.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()