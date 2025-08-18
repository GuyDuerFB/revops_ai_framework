from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json

@dataclass
class ToolExecution:
    tool_name: str
    parameters: Dict[str, Any]
    execution_time_ms: int
    result_summary: str
    full_result: str
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ToolExecution to dictionary"""
        return {
            "tool_name": self.tool_name,
            "execution_time_ms": self.execution_time_ms,
            "success": self.success,
            "parameters_summary": self._summarize_parameters(),
            "result_summary": self.result_summary,
            "error_message": self.error_message
        }
    
    def _summarize_parameters(self) -> str:
        """Extract first 200 chars of parameters for summary"""
        if not self.parameters:
            return ""
        param_str = json.dumps(self.parameters, default=str)
        return param_str[:200] + "..." if len(param_str) > 200 else param_str

@dataclass
class BedrockTraceContent:
    modelInvocationInput: Optional[str] = None
    invocationInput: Optional[str] = None
    actionGroupInvocationInput: Optional[str] = None
    observation: Optional[str] = None
    raw_trace_data: Optional[Dict[str, Any]] = None

@dataclass
class DataOperation:
    operation: str  # SQL_QUERY, GONG_API_CALL, SALESFORCE_QUERY
    target: str
    query: str
    result_count: int
    execution_time_ms: int
    full_response: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DataOperation to dictionary"""
        return {
            "operation": self.operation,
            "target": self.target,
            "execution_time_ms": self.execution_time_ms,
            "result_count": self.result_count,
            "query_summary": self.query[:100] + "..." if len(self.query) > 100 else self.query
        }

@dataclass
class AgentFlowStep:
    agent_name: str
    agent_id: str
    start_time: str
    end_time: str
    reasoning_text: str
    bedrock_trace_content: BedrockTraceContent
    tools_used: List[ToolExecution]
    data_operations: List[DataOperation] = field(default_factory=list)
    routing_decision: Optional[Dict[str, Any]] = None
    meddpicc_analysis: Optional[Dict[str, str]] = None
    collaboration_sent: List[Dict[str, Any]] = field(default_factory=list)
    collaboration_received: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self, include_traces: bool = True) -> Dict[str, Any]:
        """Convert AgentFlowStep to dictionary with optional trace inclusion"""
        base_dict = {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "timing": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration_ms": self._calculate_duration_ms()
            },
            "tools_used": [tool.to_dict() for tool in self.tools_used],
            "data_operations": [op.to_dict() for op in self.data_operations],
            "routing_decision": self.routing_decision,
            "meddpicc_analysis": self.meddpicc_analysis
        }
        
        if include_traces:
            # Include FULL reasoning text (after system prompt deduplication)
            base_dict["reasoning_text"] = self.reasoning_text
            base_dict["bedrock_trace_content"] = self._trace_to_dict()
        else:
            # Include only summary for compact format
            base_dict["reasoning_summary"] = self._extract_reasoning_summary()
        
        return base_dict
    
    def _calculate_duration_ms(self) -> int:
        """Calculate step duration in milliseconds"""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))
            return int((end - start).total_seconds() * 1000)
        except:
            return 0
    
    def _extract_reasoning_summary(self) -> str:
        """Extract first 200 chars of reasoning for summary"""
        if not self.reasoning_text:
            return ""
        # Clean up the reasoning text and extract summary
        cleaned = self.reasoning_text.replace('\\n', ' ').replace('\\\\', '\\')
        return cleaned[:200] + "..." if len(cleaned) > 200 else cleaned
    
    def _trace_to_dict(self) -> Dict[str, Any]:
        """Convert trace content to dictionary"""
        if not self.bedrock_trace_content:
            return {}
        return {
            "modelInvocationInput_length": len(self.bedrock_trace_content.modelInvocationInput or ""),
            "has_invocationInput": bool(self.bedrock_trace_content.invocationInput),
            "has_actionGroupInput": bool(self.bedrock_trace_content.actionGroupInvocationInput),
            "has_observation": bool(self.bedrock_trace_content.observation),
            "observation_summary": (self.bedrock_trace_content.observation[:100] + "..." 
                                  if self.bedrock_trace_content.observation and len(self.bedrock_trace_content.observation) > 100
                                  else self.bedrock_trace_content.observation or "")
        }

@dataclass
class FunctionCall:
    function: str
    agent: str
    full_parameters: Dict[str, Any]
    full_response: Dict[str, Any]
    execution_time_ms: int
    success: bool
    timestamp: str

@dataclass
class ConversationUnit:
    conversation_id: str
    session_id: str
    user_id: str
    channel: str
    start_timestamp: str
    end_timestamp: str
    user_query: str
    temporal_context: str
    agents_involved: List[str]
    agent_flow: List[AgentFlowStep]
    final_response: str
    collaboration_map: Dict[str, Dict[str, Any]]
    function_audit: Dict[str, Any]
    success: bool
    processing_time_ms: int
    error_details: Optional[Dict[str, Any]] = None
    # System prompts are now handled separately by SystemPromptStripper
    # prompt_references and system_prompts fields removed to prevent contamination
    
    def to_json(self) -> str:
        """Convert to JSON for CloudWatch logging"""
        return json.dumps(self, default=str, indent=2)
    
    def to_cloudwatch_event(self) -> Dict[str, Any]:
        """Convert to CloudWatch structured event"""
        return {
            "timestamp": self.end_timestamp,
            "event_type": "CONVERSATION_UNIT_COMPLETE",
            "conversation_id": self.conversation_id,
            "data": self.__dict__
        }
    
    def to_structured_json(self, include_full_traces: bool = False) -> Dict[str, Any]:
        """Convert to structured JSON optimized for storage and analysis"""
        return {
            "metadata": {
                "conversation_id": self.conversation_id,
                "session_id": self.session_id,
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
            "context": {
                "user_id": self.user_id,
                "channel": self.channel,
                "user_query": self.user_query,
                "temporal_context": self.temporal_context,
                "agents_involved": self.agents_involved
            },
            "execution": {
                "agent_flow": [step.to_dict(include_traces=include_full_traces) for step in self.agent_flow],
                "final_response": self.final_response,
                "collaboration_map": self.collaboration_map,
                "function_audit": self.function_audit
            },
            "error_details": self.error_details
        }
    
    def to_compact_json(self) -> Dict[str, Any]:
        """Convert to compact JSON for CloudWatch (minimal data)"""
        return {
            "id": self.conversation_id,
            "session": self.session_id,
            "user": self.user_id,
            "channel": self.channel,
            "timestamps": {
                "start": self.start_timestamp,
                "end": self.end_timestamp,
                "duration_ms": self.processing_time_ms
            },
            "query_summary": (self.user_query[:100] + "..." if len(self.user_query) > 100 else self.user_query),
            "agents": self.agents_involved,
            "steps": len(self.agent_flow),
            "success": self.success,
            "response_summary": (self.final_response[:200] + "..." if len(self.final_response) > 200 else self.final_response),
            "tools_used": sum(len(step.tools_used) for step in self.agent_flow),
            "data_ops": sum(len(step.data_operations) for step in self.agent_flow),
            "has_errors": bool(self.error_details)
        }
    
    def to_analysis_json(self) -> Dict[str, Any]:
        """Convert to analysis-ready JSON for S3 export"""
        return self.to_structured_json(include_full_traces=True)
    
    # System prompt deduplication is now handled by SystemPromptStripper during preprocessing
    # This method has been removed to prevent system prompt contamination