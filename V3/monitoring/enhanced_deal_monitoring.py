"""
Enhanced Deal Assessment Monitoring
Provides specialized monitoring for deal review workflows and data completeness
"""

import boto3
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class DealAssessmentStatus(Enum):
    """Deal assessment completion status"""
    COMPLETE = "complete"          # Both SFDC and call data retrieved
    PARTIAL = "partial"           # Only one data source retrieved
    FAILED = "failed"             # No data retrieved
    IN_PROGRESS = "in_progress"   # Assessment ongoing

@dataclass
class DealAssessmentMetrics:
    """Metrics for a single deal assessment"""
    correlation_id: str
    company_name: str
    assessment_status: DealAssessmentStatus
    sfdc_data_retrieved: bool
    call_data_retrieved: bool
    agents_invoked: List[str]
    total_processing_time_ms: int
    step_1a_time_ms: Optional[int] = None
    step_1b_time_ms: Optional[int] = None
    data_sources_accessed: List[str] = None
    error_messages: List[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.data_sources_accessed is None:
            self.data_sources_accessed = []
        if self.error_messages is None:
            self.error_messages = []

class DealAssessmentMonitor:
    """Enhanced monitoring for deal assessment workflows"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region_name)
        self.logs_client = boto3.client('logs', region_name=region_name)
        
        # CloudWatch metric namespace
        self.namespace = 'RevOpsAI/DealAssessment'
        
        # Log groups to monitor
        self.log_groups = {
            'conversation': '/aws/revops-ai/conversation-trace',
            'collaboration': '/aws/revops-ai/agent-collaboration', 
            'data_operations': '/aws/revops-ai/data-operations',
            'decision_logic': '/aws/revops-ai/decision-logic',
            'errors': '/aws/revops-ai/error-analysis'
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def analyze_deal_assessment(self, correlation_id: str, 
                               lookback_minutes: int = 30) -> DealAssessmentMetrics:
        """
        Analyze a specific deal assessment by correlation ID
        
        Args:
            correlation_id: Unique identifier for the conversation
            lookback_minutes: How far back to search for logs
            
        Returns:
            DealAssessmentMetrics object with assessment analysis
        """
        start_time = int((datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)).timestamp() * 1000)
        
        # Initialize metrics
        metrics = DealAssessmentMetrics(
            correlation_id=correlation_id,
            company_name="Unknown",
            assessment_status=DealAssessmentStatus.FAILED,
            sfdc_data_retrieved=False,
            call_data_retrieved=False,
            agents_invoked=[],
            total_processing_time_ms=0
        )
        
        try:
            # Analyze conversation logs
            conversation_events = self._get_log_events(
                self.log_groups['conversation'], 
                correlation_id, 
                start_time
            )
            
            # Analyze collaboration logs  
            collaboration_events = self._get_log_events(
                self.log_groups['collaboration'],
                correlation_id,
                start_time
            )
            
            # Analyze data operation logs
            data_events = self._get_log_events(
                self.log_groups['data_operations'],
                correlation_id, 
                start_time
            )
            
            # Process conversation events
            self._process_conversation_events(conversation_events, metrics)
            
            # Process collaboration events  
            self._process_collaboration_events(collaboration_events, metrics)
            
            # Process data operation events
            self._process_data_events(data_events, metrics)
            
            # Determine assessment status
            self._determine_assessment_status(metrics)
            
            # Extract company name from user query
            self._extract_company_name(conversation_events, metrics)
            
        except Exception as e:
            self.logger.error(f"Error analyzing deal assessment {correlation_id}: {str(e)}")
            metrics.error_messages.append(str(e))
            
        return metrics

    def _get_log_events(self, log_group: str, correlation_id: str, 
                       start_time: int) -> List[Dict]:
        """Retrieve log events for a specific correlation ID"""
        try:
            response = self.logs_client.filter_log_events(
                logGroupName=log_group,
                startTime=start_time,
                filterPattern=correlation_id
            )
            return response.get('events', [])
        except Exception as e:
            self.logger.warning(f"Could not retrieve logs from {log_group}: {str(e)}")
            return []

    def _process_conversation_events(self, events: List[Dict], 
                                   metrics: DealAssessmentMetrics) -> None:
        """Process conversation trace events"""
        for event in events:
            try:
                message_data = json.loads(event['message'])
                if isinstance(message_data, dict) and 'message' in message_data:
                    event_data = message_data['message']
                    
                    if event_data.get('event_type') == 'CONVERSATION_START':
                        # Extract query type and user query
                        if 'deal' in event_data.get('user_query', '').lower():
                            pass  # This is a deal query
                            
                    elif event_data.get('event_type') == 'CONVERSATION_END':
                        metrics.total_processing_time_ms = event_data.get('processing_time_ms', 0)
                        
            except (json.JSONDecodeError, KeyError) as e:
                continue

    def _process_collaboration_events(self, events: List[Dict], 
                                    metrics: DealAssessmentMetrics) -> None:
        """Process agent collaboration events"""
        for event in events:
            try:
                message_data = json.loads(event['message'])
                if isinstance(message_data, dict) and 'message' in message_data:
                    event_data = message_data['message']
                    
                    if event_data.get('event_type') == 'AGENT_INVOKE':
                        target_agent = event_data.get('target_agent')
                        if target_agent and target_agent not in metrics.agents_invoked:
                            metrics.agents_invoked.append(target_agent)
                            
            except (json.JSONDecodeError, KeyError):
                continue

    def _process_data_events(self, events: List[Dict], 
                           metrics: DealAssessmentMetrics) -> None:
        """Process data operation events"""
        for event in events:
            try:
                message_data = json.loads(event['message'])
                if isinstance(message_data, dict) and 'message' in message_data:
                    event_data = message_data['message']
                    
                    if event_data.get('event_type') == 'DATA_OPERATION':
                        data_source = event_data.get('data_source', '')
                        operation_type = event_data.get('operation_type', '')
                        
                        # Track data source access
                        if data_source not in metrics.data_sources_accessed:
                            metrics.data_sources_accessed.append(data_source)
                        
                        # Check for SFDC/opportunity data
                        if 'opportunity' in operation_type.lower() or 'sfdc' in data_source.lower():
                            metrics.sfdc_data_retrieved = True
                            
                        # Check for call/Gong data  
                        if 'gong' in data_source.lower() or 'call' in operation_type.lower():
                            metrics.call_data_retrieved = True
                            
            except (json.JSONDecodeError, KeyError):
                continue

    def _determine_assessment_status(self, metrics: DealAssessmentMetrics) -> None:
        """Determine the overall assessment status"""
        if metrics.sfdc_data_retrieved and metrics.call_data_retrieved:
            metrics.assessment_status = DealAssessmentStatus.COMPLETE
        elif metrics.sfdc_data_retrieved or metrics.call_data_retrieved:
            metrics.assessment_status = DealAssessmentStatus.PARTIAL
        elif metrics.agents_invoked:
            metrics.assessment_status = DealAssessmentStatus.IN_PROGRESS
        else:
            metrics.assessment_status = DealAssessmentStatus.FAILED

    def _extract_company_name(self, events: List[Dict], 
                            metrics: DealAssessmentMetrics) -> None:
        """Extract company name from user query"""
        for event in events:
            try:
                message_data = json.loads(event['message'])
                if isinstance(message_data, dict) and 'message' in message_data:
                    event_data = message_data['message']
                    
                    if event_data.get('event_type') == 'CONVERSATION_START':
                        user_query = event_data.get('user_query', '').lower()
                        
                        # Simple company name extraction
                        if 'ixis' in user_query:
                            metrics.company_name = 'IXIS'
                        elif 'bigabid' in user_query:
                            metrics.company_name = 'Bigabid'
                        # Add more company patterns as needed
                        
            except (json.JSONDecodeError, KeyError):
                continue

    def publish_metrics(self, metrics: DealAssessmentMetrics) -> None:
        """Publish metrics to CloudWatch"""
        try:
            # Basic assessment metrics
            self._put_metric('AssessmentStatus', 1, {
                'Status': metrics.assessment_status.value,
                'Company': metrics.company_name
            })
            
            # Data completeness metrics
            self._put_metric('SFDCDataRetrieved', 1 if metrics.sfdc_data_retrieved else 0, {
                'Company': metrics.company_name
            })
            
            self._put_metric('CallDataRetrieved', 1 if metrics.call_data_retrieved else 0, {
                'Company': metrics.company_name  
            })
            
            # Performance metrics
            self._put_metric('ProcessingTimeMs', metrics.total_processing_time_ms, {
                'Company': metrics.company_name
            })
            
            # Agent collaboration metrics
            self._put_metric('AgentsInvoked', len(metrics.agents_invoked), {
                'Company': metrics.company_name
            })
            
            self.logger.info(f"Published metrics for {metrics.correlation_id}")
            
        except Exception as e:
            self.logger.error(f"Error publishing metrics: {str(e)}")

    def _put_metric(self, metric_name: str, value: float, dimensions: Dict[str, str]) -> None:
        """Put a single metric to CloudWatch"""
        self.cloudwatch.put_metric_data(
            Namespace=self.namespace,
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Dimensions': [
                        {'Name': k, 'Value': v} for k, v in dimensions.items()
                    ],
                    'Value': value,
                    'Timestamp': datetime.now(timezone.utc)
                }
            ]
        )

    def generate_assessment_report(self, lookback_hours: int = 24) -> Dict[str, Any]:
        """Generate a comprehensive assessment report"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=lookback_hours)
        
        # Get recent deal assessments from conversation logs
        try:
            response = self.logs_client.filter_log_events(
                logGroupName=self.log_groups['conversation'],
                startTime=int(start_time.timestamp() * 1000),
                filterPattern='DEAL_ANALYSIS'
            )
            
            assessments = []
            for event in response.get('events', []):
                try:
                    message_data = json.loads(event['message'])
                    if isinstance(message_data, dict) and 'message' in message_data:
                        event_data = message_data['message']
                        if event_data.get('query_type') == 'DEAL_ANALYSIS':
                            correlation_id = event_data.get('correlation_id')
                            if correlation_id:
                                metrics = self.analyze_deal_assessment(correlation_id)
                                assessments.append(asdict(metrics))
                except:
                    continue
            
            # Generate summary statistics
            total_assessments = len(assessments)
            complete_assessments = len([a for a in assessments if a['assessment_status'] == 'complete'])
            partial_assessments = len([a for a in assessments if a['assessment_status'] == 'partial']) 
            failed_assessments = len([a for a in assessments if a['assessment_status'] == 'failed'])
            
            avg_processing_time = sum(a['total_processing_time_ms'] for a in assessments) / max(1, total_assessments)
            
            return {
                'report_period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'hours': lookback_hours
                },
                'summary': {
                    'total_assessments': total_assessments,
                    'complete_assessments': complete_assessments,
                    'partial_assessments': partial_assessments,
                    'failed_assessments': failed_assessments,
                    'completion_rate': complete_assessments / max(1, total_assessments),
                    'avg_processing_time_ms': avg_processing_time
                },
                'assessments': assessments
            }
            
        except Exception as e:
            self.logger.error(f"Error generating assessment report: {str(e)}")
            return {'error': str(e)}

def main():
    """CLI interface for deal assessment monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor deal assessment workflows')
    parser.add_argument('--correlation-id', help='Analyze specific correlation ID')
    parser.add_argument('--report', action='store_true', help='Generate assessment report')
    parser.add_argument('--hours', type=int, default=24, help='Lookback hours for report')
    
    args = parser.parse_args()
    
    monitor = DealAssessmentMonitor()
    
    if args.correlation_id:
        metrics = monitor.analyze_deal_assessment(args.correlation_id)
        monitor.publish_metrics(metrics)
        print(json.dumps(asdict(metrics), indent=2, default=str))
        
    elif args.report:
        report = monitor.generate_assessment_report(args.hours)
        print(json.dumps(report, indent=2, default=str))
    
    else:
        print("Use --correlation-id <id> to analyze specific assessment or --report for summary")

if __name__ == '__main__':
    main()