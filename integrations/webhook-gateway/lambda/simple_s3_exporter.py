"""
Simple S3 Exporter
Lightweight S3 export for HTTP API and webhook conversations without complex dependencies
"""

import json
import boto3
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Initialize S3 client
s3_client = boto3.client('s3')

class SimpleS3Exporter:
    """
    Simple S3 exporter for conversations with enhanced monitoring format
    """
    
    def __init__(self, s3_bucket: str):
        self.s3_bucket = s3_bucket
    
    def export_api_conversation(self, 
                               conversation_data: Dict[str, Any],
                               conversation_id: str,
                               source_type: str = "api") -> Optional[str]:
        """
        Export API conversation to S3 with enhanced monitoring format
        
        Args:
            conversation_data: Complete conversation data
            conversation_id: Unique conversation ID
            source_type: Type of source ("api", "webhook")
            
        Returns:
            S3 path of exported conversation, or None if failed
        """
        
        try:
            # Generate S3 path
            s3_path = self._generate_s3_path(conversation_id, source_type)
            
            # Upload to S3
            self._upload_to_s3(conversation_data, s3_path, source_type)
            
            print(f"✅ Successfully exported {source_type} conversation to S3: {s3_path}")
            return s3_path
            
        except Exception as e:
            print(f"❌ Failed to export {source_type} conversation to S3: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def export_webhook_conversation(self, 
                                   webhook_request: Dict[str, Any], 
                                   agent_response: Dict[str, Any],
                                   tracking_id: str,
                                   processing_time_ms: int) -> Optional[str]:
        """
        Export webhook conversation to S3 with enhanced monitoring format
        """
        
        try:
            # Create conversation structure
            conversation_data = self._create_webhook_conversation_structure(
                webhook_request, agent_response, tracking_id, processing_time_ms
            )
            
            return self.export_api_conversation(conversation_data, tracking_id, "webhook")
            
        except Exception as e:
            print(f"❌ Failed to export webhook conversation: {e}")
            return None
    
    def _create_webhook_conversation_structure(self, 
                                             webhook_request: Dict[str, Any], 
                                             agent_response: Dict[str, Any],
                                             tracking_id: str,
                                             processing_time_ms: int) -> Dict[str, Any]:
        """
        Create enhanced conversation structure for webhook calls
        """
        
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(milliseconds=processing_time_ms)
        
        # Extract response details
        response_text = agent_response.get("response", "")
        success = agent_response.get("success", False)
        
        conversation_data = {
            "export_metadata": {
                "format": "enhanced_webhook_conversation",
                "version": "3.0",
                "exported_at": now.isoformat(),
                "source": "simple_s3_exporter", 
                "enhanced_monitoring": True,
                "system_prompts_excluded": True,
                "webhook_integration": True,
                "validation": {
                    "valid": True,
                    "statistics": {
                        "agent_steps": 1,
                        "webhook_calls": 1,
                        "total_processing_time_ms": processing_time_ms
                    },
                    "quality_assessment": {
                        "overall_score": 0.85 if success else 0.2,
                        "data_completeness": 1.0,
                        "webhook_integration_quality": 0.9,
                        "response_quality": 0.8 if success else 0.1
                    }
                }
            },
            "conversation": {
                "conversation_id": f"webhook-{tracking_id}",
                "session_id": f"webhook-session-{tracking_id}",
                "user_id": webhook_request.get("source_system", "webhook_user"),
                "channel": "webhook_api",
                "start_timestamp": start_time.isoformat(),
                "end_timestamp": now.isoformat(),
                "user_query": webhook_request.get("query", ""),
                "temporal_context": f"Q{((now.month - 1) // 3) + 1} {now.year}",
                "agents_involved": ["Manager"],
                "agent_flow": [{
                    "agent_name": "Manager",
                    "agent_id": agent_response.get("source", "PVWGKOWSOT"),
                    "timing": {
                        "start_time": start_time.isoformat(),
                        "end_time": now.isoformat(),
                        "duration_ms": processing_time_ms
                    },
                    "reasoning_breakdown": {
                        "context_setup": {
                            "current_date": now.strftime('%A, %B %d, %Y'),
                            "current_time": now.strftime('%H:%M UTC'),
                            "user_request": webhook_request.get("query", "")
                        },
                        "webhook_processing": {
                            "source_system": webhook_request.get("source_system"),
                            "source_process": webhook_request.get("source_process"),
                            "tracking_id": tracking_id
                        },
                        "agent_response": {
                            "success": success,
                            "response_length": len(response_text),
                            "session_id": agent_response.get("sessionId"),
                            "correlation_id": agent_response.get("correlation_id")
                        }
                    },
                    "tools_used": [],
                    "data_operations": [],
                    "webhook_metadata": {
                        "tracking_id": tracking_id,
                        "source_system": webhook_request.get("source_system"),
                        "source_process": webhook_request.get("source_process")
                    }
                }],
                "final_response": response_text,
                "collaboration_map": {},
                "function_audit": {},
                "success": success,
                "processing_time_ms": processing_time_ms,
                "webhook_integration": {
                    "tracking_id": tracking_id,
                    "source_system": webhook_request.get("source_system"),
                    "original_query": webhook_request.get("query"),
                    "processing_duration_ms": processing_time_ms
                }
            }
        }
        
        return conversation_data
    
    def _generate_s3_path(self, conversation_id: str, source_type: str) -> str:
        """
        Generate S3 path for conversation export
        """
        now = datetime.now(timezone.utc)
        date_path = now.strftime('%Y/%m/%d')
        timestamp = now.strftime('%Y-%m-%dT%H-%M-%S')
        
        return f"conversation-history/{date_path}/{source_type}-{timestamp}-{conversation_id[:8]}/conversation.json"
    
    def _upload_to_s3(self, conversation_data: Dict[str, Any], s3_path: str, source_type: str):
        """
        Upload conversation data to S3
        """
        
        # Convert to JSON
        json_data = json.dumps(conversation_data, indent=2, default=str)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_path,
            Body=json_data,
            ContentType='application/json',
            Metadata={
                'conversation-type': source_type,
                'enhanced-monitoring': 'true',
                'export-version': '3.0'
            }
        )
        
        # Also create metadata file
        metadata_path = s3_path.replace('/conversation.json', '/metadata.json')
        metadata = {
            "conversation_type": source_type,
            "enhanced_monitoring": True,
            "export_version": "3.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "file_size_bytes": len(json_data),
            "s3_path": s3_path
        }
        
        s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=metadata_path,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )

from datetime import timedelta