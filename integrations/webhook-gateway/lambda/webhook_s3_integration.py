"""
Webhook S3 Integration
Integrates webhook conversations with existing S3 export pipeline
"""

import json
import logging
import boto3
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from webhook_conversation_schema import WebhookConversationUnit

# Set up logging
logger = logging.getLogger(__name__)

class WebhookS3Exporter:
    """
    Exports webhook conversations to S3 using the existing export infrastructure
    """
    
    def __init__(self, s3_bucket: str, s3_prefix: str = "conversation-history/"):
        self.s3_client = boto3.client('s3')
        self.bucket = s3_bucket
        self.prefix = s3_prefix
        self.logger = logging.getLogger(__name__)
    
    def export_webhook_conversation(
        self, 
        webhook_conversation: WebhookConversationUnit,
        export_formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Export webhook conversation in multiple formats
        
        Args:
            webhook_conversation: WebhookConversationUnit to export
            export_formats: List of formats to export
            
        Returns:
            Dictionary mapping format names to S3 URLs
        """
        
        if export_formats is None:
            export_formats = [
                'webhook_structured_json',
                'metadata_only', 
                'compact_summary'
            ]
        
        exported_urls = {}
        
        # Generate base S3 path
        base_path = self._get_webhook_s3_path(webhook_conversation)
        
        # Define format handlers
        format_handlers = {
            'webhook_structured_json': ('conversation.json', self._to_webhook_structured_json),
            'metadata_only': ('metadata.json', self._to_metadata_only),
            'compact_summary': ('summary.json', self._to_compact_summary),
            'compatibility_format': ('legacy_conversation.json', self._to_compatibility_format),
            'analysis_format': ('analysis.json', self._to_analysis_format)
        }
        
        # Export each requested format
        for format_name in export_formats:
            if format_name not in format_handlers:
                self.logger.warning(f"Unknown export format: {format_name}")
                continue
            
            filename, handler = format_handlers[format_name]
            
            try:
                # Generate content
                content = handler(webhook_conversation)
                
                # Upload to S3
                s3_key = f"{base_path}{filename}"
                
                # Prepare metadata
                metadata = {
                    'conversation-id': webhook_conversation.conversation_id,
                    'export-timestamp': datetime.utcnow().isoformat(),
                    'format': format_name,
                    'channel': 'webhook',
                    'webhook-type': webhook_conversation.webhook_metadata.webhook_type if webhook_conversation.webhook_metadata else 'unknown',
                    'source-system': webhook_conversation.webhook_metadata.source_system if webhook_conversation.webhook_metadata else 'unknown',
                    'content-size-bytes': str(len(content.encode('utf-8')))
                }
                
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=content.encode('utf-8'),
                    ContentType='application/json' if filename.endswith('.json') else 'text/plain',
                    Metadata=metadata
                )
                
                exported_urls[format_name] = f"s3://{self.bucket}/{s3_key}"
                self.logger.info(f"Exported webhook {format_name} to {exported_urls[format_name]}")
                
            except Exception as e:
                self.logger.error(f"Failed to export webhook {format_name}: {e}")
        
        return exported_urls
    
    def _get_webhook_s3_path(self, webhook_conversation: WebhookConversationUnit) -> str:
        """
        Generate S3 path for webhook conversation following existing pattern
        
        Returns:
            S3 path: conversation-history/YYYY/MM/DD/webhook_timestamp/
        """
        
        # Use start timestamp
        timestamp = webhook_conversation.start_timestamp
        
        # Parse timestamp to get date components
        date_str = timestamp[:10]  # YYYY-MM-DD
        year, month, day = date_str.split('-')
        
        # Create filesystem-safe timestamp directory
        # Convert "2025-08-13T10:30:45.123456+00:00" to "webhook_20250813_103045_id"
        timestamp_clean = timestamp.replace(':', '-').split('.')[0]  # Remove microseconds
        if '+' in timestamp_clean:
            timestamp_clean = timestamp_clean.split('+')[0]  # Remove timezone
        
        # Include conversation ID for uniqueness
        conv_id_suffix = webhook_conversation.conversation_id.split('_')[-1]  # Last part of UUID
        timestamp_dir = f"webhook_{timestamp_clean.replace('-', '').replace('T', '_')}_{conv_id_suffix}"
        
        return f"{self.prefix}{year}/{month}/{day}/{timestamp_dir}/"
    
    def _to_webhook_structured_json(self, webhook_conversation: WebhookConversationUnit) -> str:
        """Convert to webhook-optimized structured JSON format"""
        
        export_data = {
            "export_metadata": {
                "format": "webhook_structured_json",
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "channel": "webhook",
                "source": "webhook_gateway",
                "conversation_type": "webhook_interaction"
            },
            "conversation": webhook_conversation.to_webhook_structured_json()
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def _to_metadata_only(self, webhook_conversation: WebhookConversationUnit) -> str:
        """Export only metadata and summary information"""
        
        metadata = {
            "export_metadata": {
                "format": "metadata_only",
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "channel": "webhook"
            },
            "conversation_metadata": {
                "conversation_id": webhook_conversation.conversation_id,
                "session_id": webhook_conversation.session_id,
                "timestamps": {
                    "start": webhook_conversation.start_timestamp,
                    "end": webhook_conversation.end_timestamp
                },
                "performance": {
                    "processing_time_ms": webhook_conversation.processing_time_ms,
                    "success": webhook_conversation.success
                },
                "agents_involved": webhook_conversation.agents_involved,
                "query_summary": webhook_conversation.user_query[:200] + "..." if len(webhook_conversation.user_query) > 200 else webhook_conversation.user_query,
                "response_summary": webhook_conversation.final_response[:300] + "..." if len(webhook_conversation.final_response) > 300 else webhook_conversation.final_response
            },
            "webhook_metadata": webhook_conversation.webhook_metadata.to_dict() if webhook_conversation.webhook_metadata else {}
        }
        
        return json.dumps(metadata, indent=2, default=str)
    
    def _to_compact_summary(self, webhook_conversation: WebhookConversationUnit) -> str:
        """Export compact summary for monitoring and analytics"""
        
        summary = {
            "id": webhook_conversation.conversation_id,
            "timestamp": webhook_conversation.start_timestamp,
            "source_system": webhook_conversation.webhook_metadata.source_system if webhook_conversation.webhook_metadata else "unknown",
            "webhook_type": webhook_conversation.webhook_metadata.webhook_type if webhook_conversation.webhook_metadata else "unknown",
            "success": webhook_conversation.success,
            "processing_ms": webhook_conversation.processing_time_ms,
            "query_len": len(webhook_conversation.user_query),
            "response_len": len(webhook_conversation.final_response),
            "agents_count": len(webhook_conversation.agents_involved),
            "delivery_status": webhook_conversation.webhook_metadata.delivery_status if webhook_conversation.webhook_metadata else "unknown",
            "delivery_attempts": webhook_conversation.webhook_metadata.delivery_attempts if webhook_conversation.webhook_metadata else 0
        }
        
        return json.dumps(summary, default=str)
    
    def _to_compatibility_format(self, webhook_conversation: WebhookConversationUnit) -> str:
        """
        Convert to format compatible with existing Slack conversation analysis tools
        """
        
        # Convert to standard ConversationUnit format for compatibility
        standard_conversation = webhook_conversation.to_conversation_unit()
        
        # Create compatibility export
        compatibility_data = {
            "export_metadata": {
                "format": "compatibility_format", 
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "channel": "webhook",
                "note": "Converted from webhook format for compatibility with existing analysis tools"
            },
            "conversation": {
                "metadata": {
                    "conversation_id": standard_conversation.conversation_id,
                    "session_id": standard_conversation.session_id,
                    "user_id": standard_conversation.user_id,
                    "channel": standard_conversation.channel,
                    "timestamps": {
                        "start": standard_conversation.start_timestamp,
                        "end": standard_conversation.end_timestamp
                    },
                    "performance": {
                        "processing_time_ms": standard_conversation.processing_time_ms,
                        "success": standard_conversation.success
                    }
                },
                "context": {
                    "user_query": standard_conversation.user_query,
                    "temporal_context": standard_conversation.temporal_context,
                    "agents_involved": standard_conversation.agents_involved
                },
                "execution": {
                    "agent_flow": [step.to_dict(include_traces=False) for step in standard_conversation.agent_flow],
                    "final_response": standard_conversation.final_response,
                    "collaboration_map": standard_conversation.collaboration_map,
                    "function_audit": standard_conversation.function_audit
                },
                "webhook_specific": webhook_conversation.webhook_metadata.to_dict() if webhook_conversation.webhook_metadata else {}
            }
        }
        
        return json.dumps(compatibility_data, indent=2, default=str)
    
    def _to_analysis_format(self, webhook_conversation: WebhookConversationUnit) -> str:
        """Export format optimized for analysis and reporting"""
        
        analysis_data = {
            "export_metadata": {
                "format": "analysis_format",
                "version": "1.0", 
                "exported_at": datetime.utcnow().isoformat(),
                "optimized_for": "analysis_and_reporting"
            },
            "conversation_analysis": {
                "identifiers": {
                    "conversation_id": webhook_conversation.conversation_id,
                    "session_id": webhook_conversation.session_id
                },
                "timing": {
                    "start_timestamp": webhook_conversation.start_timestamp,
                    "end_timestamp": webhook_conversation.end_timestamp,
                    "total_duration_ms": webhook_conversation.processing_time_ms,
                    "date": webhook_conversation.start_timestamp[:10]
                },
                "webhook_context": webhook_conversation.webhook_metadata.to_dict() if webhook_conversation.webhook_metadata else {},
                "query_analysis": {
                    "original_query": webhook_conversation.user_query,
                    "query_length": len(webhook_conversation.user_query),
                    "temporal_context_provided": bool(webhook_conversation.temporal_context)
                },
                "response_analysis": {
                    "response_text": webhook_conversation.final_response,
                    "response_length": len(webhook_conversation.final_response),
                    "success": webhook_conversation.success
                },
                "agent_analysis": {
                    "agents_involved": webhook_conversation.agents_involved,
                    "agent_count": len(webhook_conversation.agents_involved),
                    "agent_steps": len(webhook_conversation.agent_flow)
                },
                "delivery_analysis": {
                    "webhook_type": webhook_conversation.webhook_metadata.webhook_type if webhook_conversation.webhook_metadata else None,
                    "target_url": webhook_conversation.webhook_metadata.target_webhook_url if webhook_conversation.webhook_metadata else None,
                    "delivery_status": webhook_conversation.webhook_metadata.delivery_status if webhook_conversation.webhook_metadata else None,
                    "delivery_attempts": webhook_conversation.webhook_metadata.delivery_attempts if webhook_conversation.webhook_metadata else 0,
                    "http_status": webhook_conversation.webhook_metadata.http_status_code if webhook_conversation.webhook_metadata else None
                }
            }
        }
        
        return json.dumps(analysis_data, indent=2, default=str)

def get_s3_export_config() -> Tuple[Optional[str], bool]:
    """
    Get S3 export configuration from environment variables
    
    Returns:
        Tuple of (bucket_name, export_enabled)
    """
    
    # Check for S3 bucket configuration
    s3_bucket = os.environ.get('CONVERSATION_EXPORT_S3_BUCKET')
    export_enabled = os.environ.get('ENABLE_CONVERSATION_EXPORT', 'true').lower() == 'true'
    
    if not s3_bucket and export_enabled:
        # Try to get from existing Slack integration config
        try:
            # This would be set by existing infrastructure
            s3_bucket = os.environ.get('S3_BUCKET_NAME')
        except:
            pass
    
    return s3_bucket, export_enabled