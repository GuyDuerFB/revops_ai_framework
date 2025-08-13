"""
Webhook Conversation Schema Extension
Extends the existing ConversationUnit to support webhook-specific metadata
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

# Import existing schema components
import sys
import os
sys.path.append('/Users/firebolt/firebolt_coding/1_fb_code/revops_ai_framework/integrations/slack-bedrock-gateway/lambdas/processor')

try:
    from conversation_schema import ConversationUnit, AgentFlowStep, ToolExecution, DataOperation, BedrockTraceContent
except ImportError:
    # Fallback for deployment environments
    pass

@dataclass
class WebhookMetadata:
    """Webhook-specific metadata for conversation tracking"""
    source_system: str
    source_process: str
    webhook_type: Optional[str] = None  # deal_analysis, data_analysis, lead_analysis, general
    target_webhook_url: Optional[str] = None
    delivery_status: str = "pending"  # pending, queued, delivered, failed, retrying
    delivery_attempts: int = 0
    delivery_id: Optional[str] = None
    processing_time_ms: Optional[int] = None
    outbound_payload_size: Optional[int] = None
    http_status_code: Optional[int] = None
    error_details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert WebhookMetadata to dictionary"""
        return {
            "source_system": self.source_system,
            "source_process": self.source_process,
            "webhook_type": self.webhook_type,
            "target_webhook_url": self.target_webhook_url,
            "delivery_status": self.delivery_status,
            "delivery_attempts": self.delivery_attempts,
            "delivery_id": self.delivery_id,
            "processing_time_ms": self.processing_time_ms,
            "outbound_payload_size": self.outbound_payload_size,
            "http_status_code": self.http_status_code,
            "error_details": self.error_details
        }

@dataclass
class WebhookConversationUnit:
    """Extended ConversationUnit with webhook-specific fields"""
    
    # Core conversation fields (matching existing schema)
    conversation_id: str
    session_id: str
    user_id: str = "webhook_user"  # Default for webhook requests
    channel: str = "webhook"  # Channel type identifier
    start_timestamp: str = ""
    end_timestamp: str = ""
    user_query: str = ""
    temporal_context: str = ""
    agents_involved: List[str] = field(default_factory=list)
    agent_flow: List[AgentFlowStep] = field(default_factory=list)
    final_response: str = ""
    collaboration_map: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    function_audit: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    processing_time_ms: int = 0
    error_details: Optional[Dict[str, Any]] = None
    prompt_references: Dict[str, str] = field(default_factory=dict)
    system_prompts: Dict[str, str] = field(default_factory=dict)
    
    # Webhook-specific fields
    webhook_metadata: Optional[WebhookMetadata] = None
    
    def to_conversation_unit(self) -> 'ConversationUnit':
        """Convert to standard ConversationUnit for compatibility with existing export pipeline"""
        try:
            from conversation_schema import ConversationUnit
            return ConversationUnit(
                conversation_id=self.conversation_id,
                session_id=self.session_id,
                user_id=self.user_id,
                channel=self.channel,
                start_timestamp=self.start_timestamp,
                end_timestamp=self.end_timestamp,
                user_query=self.user_query,
                temporal_context=self.temporal_context,
                agents_involved=self.agents_involved,
                agent_flow=self.agent_flow,
                final_response=self.final_response,
                collaboration_map=self.collaboration_map,
                function_audit=self.function_audit,
                success=self.success,
                processing_time_ms=self.processing_time_ms,
                error_details=self.error_details,
                prompt_references=self.prompt_references,
                system_prompts=self.system_prompts
            )
        except ImportError:
            # Return self if schema import fails
            return self
    
    def to_webhook_structured_json(self) -> Dict[str, Any]:
        """Convert to webhook-optimized structured JSON"""
        base_structure = {
            "metadata": {
                "conversation_id": self.conversation_id,
                "session_id": self.session_id,
                "channel": self.channel,
                "timestamps": {
                    "start": self.start_timestamp,
                    "end": self.end_timestamp
                },
                "performance": {
                    "processing_time_ms": self.processing_time_ms,
                    "success": self.success
                },
                "agents_count": len(self.agents_involved),
                "steps_count": len(self.agent_flow)
            },
            "webhook_context": self.webhook_metadata.to_dict() if self.webhook_metadata else {},
            "conversation": {
                "user_query": self.user_query,
                "temporal_context": self.temporal_context,
                "agents_involved": self.agents_involved,
                "final_response": self.final_response
            },
            "execution": {
                "agent_flow": [step.to_dict(include_traces=False) for step in self.agent_flow] if self.agent_flow else [],
                "collaboration_map": self.collaboration_map,
                "function_audit": self.function_audit
            },
            "error_details": self.error_details
        }
        
        return base_structure
    
    def to_compact_webhook_log(self) -> Dict[str, Any]:
        """Convert to compact format for CloudWatch logging"""
        return {
            "event_type": "WEBHOOK_CONVERSATION_COMPLETE",
            "conversation_id": self.conversation_id,
            "session_id": self.session_id,
            "channel": self.channel,
            "timestamps": {
                "start": self.start_timestamp,
                "end": self.end_timestamp,
                "duration_ms": self.processing_time_ms
            },
            "query_summary": (self.user_query[:100] + "..." if len(self.user_query) > 100 else self.user_query),
            "agents": self.agents_involved,
            "success": self.success,
            "response_summary": (self.final_response[:200] + "..." if len(self.final_response) > 200 else self.final_response),
            "webhook_metadata": self.webhook_metadata.to_dict() if self.webhook_metadata else {},
            "tools_used": sum(len(getattr(step, 'tools_used', [])) for step in self.agent_flow),
            "data_ops": sum(len(getattr(step, 'data_operations', [])) for step in self.agent_flow)
        }

def create_webhook_conversation_id(source_system: str, source_process: str) -> str:
    """Generate webhook conversation ID following existing patterns"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    # Format: webhook_YYYYMMDD_HHMMSS_system_process_uuid
    clean_system = source_system.replace('-', '').replace('_', '')[:10]
    clean_process = source_process.replace('-', '').replace('_', '')[:10]
    
    return f"webhook_{timestamp}_{clean_system}_{clean_process}_{unique_id}"

def create_webhook_session_id(conversation_id: str) -> str:
    """Generate session ID for webhook conversations"""
    return f"{conversation_id}_session"