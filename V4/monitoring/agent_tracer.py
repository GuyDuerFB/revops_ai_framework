"""
Enhanced Agent Tracing Library for RevOps AI Framework
Provides structured logging for debugging agent chain-of-thought and interactions.
"""

import json
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
import boto3
from contextlib import contextmanager

class EventType(Enum):
    """Types of events to trace"""
    CONVERSATION_START = "CONVERSATION_START"
    CONVERSATION_END = "CONVERSATION_END"
    AGENT_INVOKE = "AGENT_INVOKE"
    AGENT_RESPONSE = "AGENT_RESPONSE"
    DATA_OPERATION = "DATA_OPERATION"
    DECISION_LOGIC = "DECISION_LOGIC"
    ERROR = "ERROR"
    TEMPORAL_CONTEXT = "TEMPORAL_CONTEXT"
    WORKFLOW_SELECTION = "WORKFLOW_SELECTION"

class AgentTracer:
    """Enhanced tracing for agent interactions and decisions"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.session_start = datetime.now(timezone.utc)
        
        # Initialize CloudWatch loggers for different trace levels
        self._setup_loggers()
        
    def _setup_loggers(self):
        """Setup structured loggers for different trace categories"""
        
        # Conversation-level logger
        self.conversation_logger = logging.getLogger('revops-ai.conversation-trace')
        self.conversation_logger.setLevel(logging.INFO)
        
        # Agent collaboration logger  
        self.collaboration_logger = logging.getLogger('revops-ai.agent-collaboration')
        self.collaboration_logger.setLevel(logging.INFO)
        
        # Data operations logger
        self.data_logger = logging.getLogger('revops-ai.data-operations')
        self.data_logger.setLevel(logging.INFO)
        
        # Decision logic logger
        self.decision_logger = logging.getLogger('revops-ai.decision-logic') 
        self.decision_logger.setLevel(logging.INFO)
        
        # Error analysis logger
        self.error_logger = logging.getLogger('revops-ai.error-analysis')
        self.error_logger.setLevel(logging.ERROR)
        
        # Configure CloudWatch handlers if not already configured
        if not self.conversation_logger.handlers:
            self._configure_cloudwatch_handlers()
    
    def _configure_cloudwatch_handlers(self):
        """Configure CloudWatch log handlers for each logger"""
        try:
            # This would typically use boto3 CloudWatch Logs handler
            # For now, configure standard logging that will be picked up by CloudWatch
            
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
            )
            
            # In production, these would route to specific CloudWatch log groups
            for logger in [self.conversation_logger, self.collaboration_logger, 
                          self.data_logger, self.decision_logger, self.error_logger]:
                if not logger.handlers:
                    handler = logging.StreamHandler()
                    handler.setFormatter(formatter)
                    logger.addHandler(handler)
                    
        except Exception as e:
            print(f"Failed to configure CloudWatch handlers: {e}")
    
    def trace_conversation_start(self, user_query: str, user_id: str, channel: str, 
                                temporal_context: Optional[str] = None):
        """Trace the start of a conversation"""
        event_data = {
            "event_type": EventType.CONVERSATION_START.value,
            "correlation_id": self.correlation_id,
            "user_query": user_query,
            "user_id": user_id,
            "channel": channel,
            "temporal_context": temporal_context,
            "session_start": self.session_start.isoformat(),
            "query_length": len(user_query),
            "query_type": self._classify_query_type(user_query)
        }
        
        self.conversation_logger.info(json.dumps(event_data))
        
    def trace_conversation_end(self, response_summary: str, total_agents_used: int,
                              processing_time_ms: int, success: bool):
        """Trace the end of a conversation"""
        event_data = {
            "event_type": EventType.CONVERSATION_END.value,
            "correlation_id": self.correlation_id,
            "response_summary": response_summary[:200] + "..." if len(response_summary) > 200 else response_summary,
            "total_agents_used": total_agents_used,
            "processing_time_ms": processing_time_ms,
            "success": success,
            "session_duration_ms": int((datetime.now(timezone.utc) - self.session_start).total_seconds() * 1000)
        }
        
        self.conversation_logger.info(json.dumps(event_data))
    
    def trace_agent_invocation(self, source_agent: str, target_agent: str, 
                              collaboration_type: str, reasoning: str, 
                              context_passed: Optional[Dict] = None):
        """Trace agent-to-agent collaboration"""
        event_data = {
            "event_type": EventType.AGENT_INVOKE.value,
            "correlation_id": self.correlation_id,
            "source_agent": source_agent,
            "target_agent": target_agent,
            "collaboration_type": collaboration_type,
            "reasoning": reasoning,
            "context_size": len(str(context_passed)) if context_passed else 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.collaboration_logger.info(json.dumps(event_data))
        
    def trace_agent_response(self, agent_name: str, response_type: str, 
                           data_sources_used: List[str], processing_time_ms: int,
                           success: bool, result_summary: str):
        """Trace agent response details"""
        event_data = {
            "event_type": EventType.AGENT_RESPONSE.value,
            "correlation_id": self.correlation_id,
            "agent_name": agent_name,
            "response_type": response_type,
            "data_sources_used": data_sources_used,
            "processing_time_ms": processing_time_ms,
            "success": success,
            "result_summary": result_summary[:300] + "..." if len(result_summary) > 300 else result_summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.collaboration_logger.info(json.dumps(event_data))
    
    def trace_data_operation(self, operation_type: str, data_source: str, 
                           query_summary: str, result_count: Optional[int] = None,
                           execution_time_ms: Optional[int] = None, 
                           error_message: Optional[str] = None):
        """Trace data retrieval operations"""
        event_data = {
            "event_type": EventType.DATA_OPERATION.value,
            "correlation_id": self.correlation_id,
            "operation_type": operation_type,  # SQL_QUERY, API_CALL, KB_LOOKUP
            "data_source": data_source,  # FIREBOLT, GONG, SALESFORCE, WEB
            "query_summary": query_summary,
            "result_count": result_count,
            "execution_time_ms": execution_time_ms,
            "success": error_message is None,
            "error_message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.data_logger.info(json.dumps(event_data))
    
    def trace_decision_logic(self, decision_point: str, workflow_selected: str,
                           reasoning: str, confidence_score: Optional[float] = None,
                           alternatives_considered: Optional[List[str]] = None):
        """Trace decision agent logic and workflow selection"""
        event_data = {
            "event_type": EventType.DECISION_LOGIC.value,
            "correlation_id": self.correlation_id,
            "decision_point": decision_point,
            "workflow_selected": workflow_selected,
            "reasoning": reasoning,
            "confidence_score": confidence_score,
            "alternatives_considered": alternatives_considered or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.decision_logger.info(json.dumps(event_data))
    
    def trace_temporal_context(self, current_date: str, time_references: List[str],
                             temporal_adjustments: Dict[str, Any]):
        """Trace temporal context handling"""
        event_data = {
            "event_type": EventType.TEMPORAL_CONTEXT.value,
            "correlation_id": self.correlation_id,
            "current_date": current_date,
            "time_references": time_references,
            "temporal_adjustments": temporal_adjustments,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.decision_logger.info(json.dumps(event_data))
    
    def trace_error(self, error_type: str, error_message: str, 
                   agent_context: str, stack_trace: Optional[str] = None,
                   recovery_attempted: bool = False):
        """Trace errors for analysis"""
        event_data = {
            "event_type": EventType.ERROR.value,
            "correlation_id": self.correlation_id,
            "error_type": error_type,
            "error_message": error_message,
            "agent_context": agent_context,
            "stack_trace": stack_trace,
            "recovery_attempted": recovery_attempted,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.error_logger.error(json.dumps(event_data))
    
    def _classify_query_type(self, query: str) -> str:
        """Classify query type for analysis"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['deal', 'opportunity', 'status', 'probability']):
            return 'DEAL_ANALYSIS'
        elif any(word in query_lower for word in ['lead', 'assess', 'qualify']):
            return 'LEAD_ASSESSMENT'
        elif any(word in query_lower for word in ['consumption', 'usage', 'fbu', 'revenue']):
            return 'CONSUMPTION_ANALYSIS'
        elif any(word in query_lower for word in ['churn', 'risk', 'health']):
            return 'RISK_ASSESSMENT'
        elif any(word in query_lower for word in ['call', 'conversation', 'gong']):
            return 'CALL_ANALYSIS'
        else:
            return 'GENERAL_QUERY'
    
    @contextmanager
    def trace_agent_operation(self, agent_name: str, operation_name: str):
        """Context manager for tracing agent operations"""
        start_time = time.time()
        try:
            yield self
            end_time = time.time()
            self.trace_agent_response(
                agent_name=agent_name,
                response_type=operation_name,
                data_sources_used=[],
                processing_time_ms=int((end_time - start_time) * 1000),
                success=True,
                result_summary="Operation completed successfully"
            )
        except Exception as e:
            end_time = time.time()
            self.trace_error(
                error_type=type(e).__name__,
                error_message=str(e),
                agent_context=f"{agent_name}.{operation_name}",
                stack_trace=None,  # Could add traceback.format_exc() if needed
                recovery_attempted=False
            )
            raise

# Global tracer instance for easy access
_current_tracer: Optional[AgentTracer] = None

def get_tracer() -> Optional[AgentTracer]:
    """Get the current tracer instance"""
    return _current_tracer

def set_tracer(tracer: AgentTracer):
    """Set the current tracer instance"""
    global _current_tracer
    _current_tracer = tracer

def create_tracer(correlation_id: Optional[str] = None) -> AgentTracer:
    """Create and set a new tracer instance"""
    tracer = AgentTracer(correlation_id)
    set_tracer(tracer)
    return tracer

# Convenience functions for common tracing operations
def trace_conversation_start(user_query: str, user_id: str, channel: str, 
                           temporal_context: Optional[str] = None):
    """Convenience function for tracing conversation start"""
    if _current_tracer:
        _current_tracer.trace_conversation_start(user_query, user_id, channel, temporal_context)

def trace_agent_invocation(source_agent: str, target_agent: str, 
                         collaboration_type: str, reasoning: str):
    """Convenience function for tracing agent invocation"""
    if _current_tracer:
        _current_tracer.trace_agent_invocation(source_agent, target_agent, collaboration_type, reasoning)

def trace_data_operation(operation_type: str, data_source: str, query_summary: str, 
                       result_count: Optional[int] = None, execution_time_ms: Optional[int] = None):
    """Convenience function for tracing data operations"""
    if _current_tracer:
        _current_tracer.trace_data_operation(operation_type, data_source, query_summary, 
                                           result_count, execution_time_ms)

def trace_error(error_type: str, error_message: str, agent_context: str):
    """Convenience function for tracing errors"""
    if _current_tracer:
        _current_tracer.trace_error(error_type, error_message, agent_context)