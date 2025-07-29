from dataclasses import dataclass, field
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