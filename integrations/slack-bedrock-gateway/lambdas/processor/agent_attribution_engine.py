"""
Agent Attribution Engine
Multi-source agent detection and handoff identification for conversation monitoring
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AgentType(Enum):
    MANAGER = "ManagerAgent"
    DATA = "DataAgent"
    DEAL_ANALYSIS = "DealAnalysisAgent"
    LEAD_ANALYSIS = "LeadAnalysisAgent"
    WEB_SEARCH = "WebSearchAgent"
    EXECUTION = "ExecutionAgent"
    UNKNOWN = "UnknownAgent"

@dataclass
class AgentHandoff:
    """Represents an agent handoff event"""
    from_agent: str
    to_agent: str
    handoff_reason: str
    confidence_score: float
    evidence_sources: List[str]
    timestamp: str
    handoff_type: str  # explicit_routing, expertise_based, workflow_progression
    context: Dict[str, Any]

@dataclass
class AgentAttribution:
    """Represents agent attribution for a conversation step"""
    attributed_agent: str
    confidence_score: float
    evidence_sources: List[str]
    detection_methods: List[str]
    original_agent: Optional[str]
    handoff_detected: bool
    collaboration_indicators: List[Dict[str, Any]]

class AgentRegistry:
    """Registry of agent capabilities and tool mappings"""
    
    def __init__(self):
        # Tool to agent mapping
        self.tool_agent_mapping = {
            # Data Agent tools
            'firebolt_query': AgentType.DATA,
            'query_fire': AgentType.DATA,
            'FireboltQuery': AgentType.DATA,
            'gong_retrieval': AgentType.DATA,
            'GongRetrieval': AgentType.DATA,
            'salesforce_query': AgentType.DATA,
            
            # Deal Analysis Agent tools
            'deal_analysis': AgentType.DEAL_ANALYSIS,
            'meddpicc_analysis': AgentType.DEAL_ANALYSIS,
            'competitive_analysis': AgentType.DEAL_ANALYSIS,
            
            # Lead Analysis Agent tools
            'lead_analysis': AgentType.LEAD_ANALYSIS,
            'lead_scoring': AgentType.LEAD_ANALYSIS,
            'lead_qualification': AgentType.LEAD_ANALYSIS,
            
            # Web Search Agent tools
            'web_search': AgentType.WEB_SEARCH,
            'WebSearch': AgentType.WEB_SEARCH,
            'search_web': AgentType.WEB_SEARCH,
            
            # Execution Agent tools
            'webhook': AgentType.EXECUTION,
            'send_webhook': AgentType.EXECUTION,
            'external_api': AgentType.EXECUTION,
            'notification': AgentType.EXECUTION
        }
        
        # Agent signature patterns in reasoning text
        self.agent_reasoning_patterns = {
            AgentType.DATA: [
                r"data analysis",
                r"sql query",
                r"firebolt",
                r"database",
                r"temporal analysis",
                r"customer segmentation",
                r"revenue analysis",
                r"cohort analysis"
            ],
            AgentType.DEAL_ANALYSIS: [
                r"deal analysis",
                r"meddpicc",
                r"opportunity",
                r"pipeline",
                r"competitive",
                r"deal stage",
                r"qualification"
            ],
            AgentType.LEAD_ANALYSIS: [
                r"lead analysis",
                r"lead scoring",
                r"disqualification",
                r"qualification",
                r"prospect",
                r"contact analysis"
            ],
            AgentType.WEB_SEARCH: [
                r"web search",
                r"internet search",
                r"online research",
                r"search results"
            ],
            AgentType.EXECUTION: [
                r"webhook",
                r"notification",
                r"external api",
                r"action execution",
                r"integration"
            ]
        }
        
        # Agent ID mappings (from actual Bedrock agent IDs)
        self.agent_id_mapping = {
            'PVWGKOWSOT': AgentType.MANAGER,  # Manager Agent
            '9B8EGU46UV': AgentType.DATA,    # Data Agent
            'TCX9CGOKBR': AgentType.DEAL_ANALYSIS,  # Deal Analysis Agent
            # Add other agent IDs as they're discovered
        }
        
        # Agent collaboration patterns
        self.collaboration_patterns = {
            AgentType.MANAGER: {
                'routes_to': [AgentType.DATA, AgentType.DEAL_ANALYSIS, AgentType.LEAD_ANALYSIS, AgentType.WEB_SEARCH],
                'coordinates': True,
                'initiates_handoffs': True
            },
            AgentType.DATA: {
                'collaborates_with': [AgentType.DEAL_ANALYSIS, AgentType.LEAD_ANALYSIS],
                'provides_data_to': [AgentType.DEAL_ANALYSIS, AgentType.LEAD_ANALYSIS, AgentType.EXECUTION],
                'initiates_handoffs': False
            },
            AgentType.DEAL_ANALYSIS: {
                'uses_data_from': [AgentType.DATA],
                'collaborates_with': [AgentType.EXECUTION],
                'initiates_handoffs': False
            }
        }

class AgentAttributionEngine:
    """Multi-source agent detection and attribution engine"""
    
    def __init__(self):
        self.registry = AgentRegistry()
        
        # Routing decision patterns
        self.routing_patterns = [
            r"Route to (\w+)\s*Agent",
            r"routing to (\w+)\s*Agent", 
            r"calling (\w+)\s*Agent",
            r"collaborate with (\w+)\s*Agent",
            r"pass to (\w+)\s*Agent",
            r"transfer to (\w+)\s*Agent"
        ]
        
        # Agent communication patterns
        self.agent_comm_patterns = [
            r'AgentCommunication__sendMessage.*?name="([^"]+)"',
            r'agentCollaboratorName:\s*([^\n\r]+)',
            r'"agent":\s*"([^"]+)"',
            r'recipient:\s*([^,}]+)'
        ]
        
        # Bedrock trace routing patterns
        self.trace_routing_patterns = [
            r'"agentId":\s*"([^"]+)"',
            r'"agentAliasId":\s*"([^"]+)"',
            r'"agentCollaboratorName":\s*"([^"]+)"'
        ]
    
    def detect_agent_from_multiple_sources(self, step_data: Dict[str, Any]) -> AgentAttribution:
        """
        Detect agent using multiple sources and consensus voting
        """
        detection_results = []
        evidence_sources = []
        detection_methods = []
        
        # Method 1: Tool usage patterns
        tools_result = self._detect_from_tool_usage(step_data.get('tools_used', []))
        if tools_result:
            detection_results.append(tools_result)
            evidence_sources.append("tool_usage")
            detection_methods.append("tool_mapping")
        
        # Method 2: Bedrock trace analysis
        trace_result = self._detect_from_trace_content(step_data.get('bedrock_trace_content', {}))
        if trace_result:
            detection_results.append(trace_result)
            evidence_sources.append("bedrock_trace")
            detection_methods.append("trace_analysis")
        
        # Method 3: Reasoning text patterns
        reasoning_result = self._detect_from_reasoning_text(step_data.get('reasoning_text', ''))
        if reasoning_result:
            detection_results.append(reasoning_result)
            evidence_sources.append("reasoning_text")
            detection_methods.append("reasoning_analysis")
        
        # Method 4: Agent ID mapping
        agent_id_result = self._detect_from_agent_id(step_data.get('agent_id', ''))
        if agent_id_result:
            detection_results.append(agent_id_result)
            evidence_sources.append("agent_id")
            detection_methods.append("id_mapping")
        
        # Method 5: Data operations analysis
        data_ops_result = self._detect_from_data_operations(step_data.get('data_operations', []))
        if data_ops_result:
            detection_results.append(data_ops_result)
            evidence_sources.append("data_operations")
            detection_methods.append("data_pattern_analysis")
        
        # Consensus voting
        attributed_agent, confidence = self._consensus_vote(detection_results)
        
        # Check for handoffs
        handoff_detected = self._detect_agent_handoff(step_data)
        
        # Find collaboration indicators
        collaboration_indicators = self._extract_collaboration_indicators(step_data)
        
        return AgentAttribution(
            attributed_agent=attributed_agent.value if attributed_agent != AgentType.UNKNOWN else step_data.get('agent_name', 'unknown'),
            confidence_score=confidence,
            evidence_sources=evidence_sources,
            detection_methods=detection_methods,
            original_agent=step_data.get('agent_name'),
            handoff_detected=handoff_detected,
            collaboration_indicators=collaboration_indicators
        )
    
    def _detect_from_tool_usage(self, tools_used: List[Dict[str, Any]]) -> Optional[Tuple[AgentType, float]]:
        """Detect agent from tool usage patterns"""
        if not tools_used:
            return None
        
        agent_votes = {}
        confidence_scores = []
        
        for tool in tools_used:
            tool_name = tool.get('tool_name', '') if isinstance(tool, dict) else str(tool)
            
            # Direct tool mapping
            for tool_pattern, agent_type in self.registry.tool_agent_mapping.items():
                if tool_pattern.lower() in tool_name.lower():
                    if agent_type not in agent_votes:
                        agent_votes[agent_type] = 0
                    agent_votes[agent_type] += 1
                    confidence_scores.append(0.8)  # High confidence for direct tool mapping
        
        if not agent_votes:
            return None
        
        # Select agent with most votes
        best_agent = max(agent_votes.items(), key=lambda x: x[1])
        confidence = min(sum(confidence_scores) / len(tools_used), 1.0)
        
        return best_agent[0], confidence
    
    def _detect_from_trace_content(self, trace_content: Dict[str, Any]) -> Optional[Tuple[AgentType, float]]:
        """Detect agent from Bedrock trace content"""
        if not trace_content:
            return None
        
        confidence_indicators = []
        detected_agents = []
        
        # Check modelInvocationInput for agent routing
        model_input = trace_content.get("modelInvocationInput", "")
        if model_input:
            for pattern in self.trace_routing_patterns:
                matches = re.findall(pattern, str(model_input))
                for match in matches:
                    if match in self.registry.agent_id_mapping:
                        detected_agents.append(self.registry.agent_id_mapping[match])
                        confidence_indicators.append(0.9)
        
        # Check observation for agent responses
        observation = trace_content.get("observation", "")
        if observation:
            for agent_type, patterns in self.registry.agent_reasoning_patterns.items():
                pattern_matches = sum(1 for pattern in patterns if re.search(pattern, str(observation), re.IGNORECASE))
                if pattern_matches > 0:
                    detected_agents.append(agent_type)
                    confidence_indicators.append(pattern_matches / len(patterns))
        
        # Check for agent communication patterns
        for key, value in trace_content.items():
            if isinstance(value, str):
                for pattern in self.agent_comm_patterns:
                    matches = re.findall(pattern, value)
                    for match in matches:
                        agent_name = self._normalize_agent_name(match)
                        if agent_name:
                            detected_agents.append(agent_name)
                            confidence_indicators.append(0.7)
        
        if not detected_agents:
            return None
        
        # Use most frequent agent
        agent_counts = {}
        for agent in detected_agents:
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        best_agent = max(agent_counts.items(), key=lambda x: x[1])[0]
        confidence = sum(confidence_indicators) / len(confidence_indicators) if confidence_indicators else 0.5
        
        return best_agent, min(confidence, 1.0)
    
    def _detect_from_reasoning_text(self, reasoning_text: str) -> Optional[Tuple[AgentType, float]]:
        """Detect agent from reasoning text patterns"""
        if not reasoning_text:
            return None
        
        # Check for explicit routing patterns
        for pattern in self.routing_patterns:
            matches = re.findall(pattern, reasoning_text, re.IGNORECASE)
            for match in matches:
                agent_type = self._normalize_agent_name(match)
                if agent_type:
                    return agent_type, 0.9  # High confidence for explicit routing
        
        # Check for agent-specific reasoning patterns
        agent_scores = {}
        for agent_type, patterns in self.registry.agent_reasoning_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, reasoning_text, re.IGNORECASE):
                    score += 1
            
            if score > 0:
                agent_scores[agent_type] = score / len(patterns)
        
        if not agent_scores:
            return None
        
        best_agent = max(agent_scores.items(), key=lambda x: x[1])
        return best_agent[0], min(best_agent[1], 0.8)  # Reasoning patterns max 0.8 confidence
    
    def _detect_from_agent_id(self, agent_id: str) -> Optional[Tuple[AgentType, float]]:
        """Detect agent from agent ID"""
        if agent_id in self.registry.agent_id_mapping:
            return self.registry.agent_id_mapping[agent_id], 1.0
        return None
    
    def _detect_from_data_operations(self, data_operations: List[Dict[str, Any]]) -> Optional[Tuple[AgentType, float]]:
        """Detect agent from data operations patterns"""
        if not data_operations:
            return None
        
        # Data operations strongly indicate Data Agent involvement
        sql_operations = sum(1 for op in data_operations if op.get('operation', '').upper() in ['SQL_QUERY', 'FIREBOLT_QUERY'])
        api_operations = sum(1 for op in data_operations if op.get('operation', '').upper() in ['GONG_API_CALL', 'SALESFORCE_QUERY'])
        
        if sql_operations > 0 or api_operations > 0:
            confidence = min((sql_operations + api_operations) / len(data_operations), 0.9)
            return AgentType.DATA, confidence
        
        return None
    
    def _consensus_vote(self, detection_results: List[Tuple[AgentType, float]]) -> Tuple[AgentType, float]:
        """Use consensus voting to determine final agent attribution"""
        if not detection_results:
            return AgentType.UNKNOWN, 0.0
        
        # Weighted voting based on confidence scores
        agent_scores = {}
        total_weight = 0
        
        for agent_type, confidence in detection_results:
            weight = confidence
            if agent_type not in agent_scores:
                agent_scores[agent_type] = 0
            agent_scores[agent_type] += weight
            total_weight += weight
        
        if not agent_scores:
            return AgentType.UNKNOWN, 0.0
        
        # Normalize scores
        for agent_type in agent_scores:
            agent_scores[agent_type] /= total_weight
        
        best_agent = max(agent_scores.items(), key=lambda x: x[1])
        return best_agent[0], min(best_agent[1], 1.0)
    
    def _normalize_agent_name(self, agent_name: str) -> Optional[AgentType]:
        """Normalize agent name to AgentType"""
        agent_name_lower = agent_name.lower().strip()
        
        mappings = {
            'data': AgentType.DATA,
            'deal': AgentType.DEAL_ANALYSIS,
            'lead': AgentType.LEAD_ANALYSIS,
            'web': AgentType.WEB_SEARCH,
            'search': AgentType.WEB_SEARCH,
            'execution': AgentType.EXECUTION,
            'manager': AgentType.MANAGER
        }
        
        for key, agent_type in mappings.items():
            if key in agent_name_lower:
                return agent_type
        
        return None
    
    def _detect_agent_handoff(self, step_data: Dict[str, Any]) -> bool:
        """Detect if an agent handoff occurred in this step"""
        reasoning_text = step_data.get('reasoning_text', '')
        trace_content = step_data.get('bedrock_trace_content', {})
        
        # Check reasoning text for handoff indicators
        handoff_indicators = [
            r"route to",
            r"routing to", 
            r"calling",
            r"collaborate with",
            r"pass to",
            r"transfer to",
            r"AgentCommunication",
            r"agentCollaborator"
        ]
        
        for indicator in handoff_indicators:
            if re.search(indicator, reasoning_text, re.IGNORECASE):
                return True
        
        # Check trace content for collaboration signals
        for key, value in trace_content.items():
            if isinstance(value, str) and any(pattern in value for pattern in ["agentCollaborator", "AgentCommunication"]):
                return True
        
        return False
    
    def _extract_collaboration_indicators(self, step_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract collaboration indicators from step data"""
        indicators = []
        reasoning_text = step_data.get('reasoning_text', '')
        trace_content = step_data.get('bedrock_trace_content', {})
        
        # Extract from reasoning text
        for pattern in self.agent_comm_patterns:
            matches = re.findall(pattern, reasoning_text)
            for match in matches:
                indicators.append({
                    "type": "agent_communication",
                    "target_agent": match,
                    "source": "reasoning_text",
                    "confidence": 0.7
                })
        
        # Extract from trace content
        for key, value in trace_content.items():
            if isinstance(value, str):
                if "agentCollaborator" in value:
                    indicators.append({
                        "type": "collaboration_signal",
                        "evidence": key,
                        "source": "trace_content",
                        "confidence": 0.8
                    })
        
        return indicators
    
    def detect_agent_handoffs_in_conversation(self, agent_flow: List[Dict[str, Any]]) -> List[AgentHandoff]:
        """Detect agent handoffs across the entire conversation"""
        handoffs = []
        
        if len(agent_flow) < 2:
            return handoffs
        
        for i in range(len(agent_flow) - 1):
            current_step = agent_flow[i]
            next_step = agent_flow[i + 1]
            
            current_attribution = self.detect_agent_from_multiple_sources(current_step)
            next_attribution = self.detect_agent_from_multiple_sources(next_step)
            
            # Check if agent changed
            if (current_attribution.attributed_agent != next_attribution.attributed_agent and 
                current_attribution.attributed_agent != 'unknown' and 
                next_attribution.attributed_agent != 'unknown'):
                
                # Analyze handoff reason and type
                handoff_reason = self._analyze_handoff_reason(current_step, next_step)
                handoff_type = self._classify_handoff_type(handoff_reason)
                
                handoff = AgentHandoff(
                    from_agent=current_attribution.attributed_agent,
                    to_agent=next_attribution.attributed_agent,
                    handoff_reason=handoff_reason,
                    confidence_score=min(current_attribution.confidence_score, next_attribution.confidence_score),
                    evidence_sources=current_attribution.evidence_sources + next_attribution.evidence_sources,
                    timestamp=next_step.get('timing', {}).get('start_time', ''),
                    handoff_type=handoff_type,
                    context={
                        "step_index": i + 1,
                        "current_step_tools": len(current_step.get('tools_used', [])),
                        "next_step_tools": len(next_step.get('tools_used', [])),
                        "reasoning_preview": next_step.get('reasoning_text', '')[:200] + "..."
                    }
                )
                
                handoffs.append(handoff)
        
        return handoffs
    
    def _analyze_handoff_reason(self, current_step: Dict[str, Any], next_step: Dict[str, Any]) -> str:
        """Analyze the reason for agent handoff"""
        reasoning_text = next_step.get('reasoning_text', '')
        
        # Look for explicit handoff reasoning
        routing_match = None
        for pattern in self.routing_patterns:
            match = re.search(pattern, reasoning_text, re.IGNORECASE)
            if match:
                routing_match = match.group(0)
                break
        
        if routing_match:
            return f"Explicit routing: {routing_match}"
        
        # Infer from tool usage changes
        current_tools = [tool.get('tool_name', '') for tool in current_step.get('tools_used', [])]
        next_tools = [tool.get('tool_name', '') for tool in next_step.get('tools_used', [])]
        
        if next_tools and set(next_tools) != set(current_tools):
            return f"Tool specialization change: {' -> '.join(next_tools[:2])}"
        
        return "Workflow progression"
    
    def _classify_handoff_type(self, handoff_reason: str) -> str:
        """Classify the type of handoff"""
        reason_lower = handoff_reason.lower()
        
        if any(keyword in reason_lower for keyword in ['route', 'routing', 'explicit']):
            return "explicit_routing"
        elif any(keyword in reason_lower for keyword in ['specialist', 'specialization', 'expert']):
            return "expertise_based"
        elif any(keyword in reason_lower for keyword in ['workflow', 'progression', 'next']):
            return "workflow_progression"
        else:
            return "implicit_routing"