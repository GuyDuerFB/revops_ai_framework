"""
Tool Execution Normalizer
Deduplicates and contextualizes tool executions for accurate conversation monitoring
"""

import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ToolExecutionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

@dataclass
class NormalizedToolExecution:
    """Normalized tool execution with full context"""
    execution_id: str
    tool_name: str
    initiating_agent: str
    execution_purpose: str
    parameters_hash: str
    result_summary: str
    execution_status: ToolExecutionStatus
    execution_time_ms: int
    timestamp: str
    quality_score: float
    error_details: Optional[str]
    related_executions: List[str]
    business_context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['execution_status'] = self.execution_status.value
        return result

@dataclass
class ToolNormalizationStats:
    """Statistics from tool execution normalization"""
    original_executions: int
    normalized_executions: int
    duplicates_removed: int
    failed_executions: int
    high_quality_executions: int
    tool_types_used: Set[str]
    total_execution_time_ms: int
    normalization_timestamp: str

class ToolExecutionNormalizer:
    """Normalizes and deduplicates tool executions"""
    
    def __init__(self):
        # Tool categorization for better normalization
        self.tool_categories = {
            'data_query': [
                'firebolt_query', 'query_fire', 'FireboltQuery',
                'sql_query', 'database_query'
            ],
            'api_call': [
                'gong_retrieval', 'GongRetrieval',
                'salesforce_query', 'SalesforceQuery',
                'web_api_call'
            ],
            'web_search': [
                'web_search', 'WebSearch', 'search_web',
                'internet_search'
            ],
            'communication': [
                'webhook', 'send_webhook',
                'email', 'notification',
                'slack_message'
            ],
            'analysis': [
                'deal_analysis', 'lead_analysis',
                'data_analysis', 'competitive_analysis'
            ]
        }
        
        # Tool quality indicators
        self.quality_indicators = {
            'high_quality': [
                'successful_execution',
                'comprehensive_results',
                'structured_output',
                'timely_response'
            ],
            'low_quality': [
                'execution_failed',
                'timeout_occurred',
                'partial_results',
                'error_encountered'
            ]
        }
        
        # Deduplication time windows (in seconds)
        self.deduplication_windows = {
            'data_query': 30,      # SQL queries within 30s likely duplicates
            'api_call': 60,        # API calls within 1min likely duplicates  
            'web_search': 120,     # Web searches within 2min likely duplicates
            'communication': 5,     # Communications within 5s likely duplicates
            'analysis': 180        # Analysis within 3min likely duplicates
        }
    
    def normalize_tool_executions(self, agent_flow: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], ToolNormalizationStats]:
        """
        Normalize tool executions across entire agent flow
        Returns (normalized_agent_flow, normalization_stats)
        """
        stats = ToolNormalizationStats(
            original_executions=0,
            normalized_executions=0,
            duplicates_removed=0,
            failed_executions=0,
            high_quality_executions=0,
            tool_types_used=set(),
            total_execution_time_ms=0,
            normalization_timestamp=datetime.utcnow().isoformat()
        )
        
        # Collect all tool executions across steps
        all_executions = []
        execution_to_step_map = {}
        
        for step_idx, step in enumerate(agent_flow):
            step_executions = self._extract_all_executions_from_step(step, step_idx)
            
            for exec_data in step_executions:
                all_executions.append(exec_data)
                execution_to_step_map[exec_data['execution_id']] = step_idx
                stats.original_executions += 1
                stats.tool_types_used.add(exec_data['tool_name'])
        
        # Normalize and deduplicate
        normalized_executions = self._deduplicate_and_normalize(all_executions)
        
        # Update stats
        stats.normalized_executions = len(normalized_executions)
        stats.duplicates_removed = stats.original_executions - stats.normalized_executions
        
        for norm_exec in normalized_executions:
            if norm_exec.execution_status == ToolExecutionStatus.FAILED:
                stats.failed_executions += 1
            if norm_exec.quality_score >= 0.7:
                stats.high_quality_executions += 1
            stats.total_execution_time_ms += norm_exec.execution_time_ms
        
        # Reconstruct agent flow with normalized executions
        normalized_agent_flow = self._reconstruct_agent_flow_with_normalized_tools(
            agent_flow, normalized_executions, execution_to_step_map
        )
        
        logger.info(f"Tool normalization complete: {stats.original_executions} -> {stats.normalized_executions} executions")
        
        return normalized_agent_flow, stats
    
    def _extract_all_executions_from_step(self, step: Dict[str, Any], step_idx: int) -> List[Dict[str, Any]]:
        """Extract all tool executions from a step (multiple sources)"""
        executions = []
        step_agent = step.get('agent_name', 'unknown')
        step_timestamp = step.get('timing', {}).get('start_time', '')
        
        # Source 1: tools_used array
        tools_used = step.get('tools_used', [])
        for tool_idx, tool in enumerate(tools_used):
            exec_data = self._normalize_single_execution(
                tool, f"step_{step_idx}_tool_{tool_idx}", step_agent, step_timestamp, "tools_used"
            )
            if exec_data:
                executions.append(exec_data)
        
        # Source 2: reasoning_breakdown.tool_executions
        reasoning = step.get('reasoning_breakdown', {})
        tool_executions = reasoning.get('tool_executions', [])
        for tool_idx, tool in enumerate(tool_executions):
            exec_data = self._normalize_single_execution(
                tool, f"step_{step_idx}_reasoning_{tool_idx}", step_agent, step_timestamp, "reasoning_breakdown"
            )
            if exec_data:
                executions.append(exec_data)
        
        # Source 3: trace_tool_executions (from enhanced parsing)
        trace_tools = step.get('trace_tool_executions', [])
        for tool_idx, tool in enumerate(trace_tools):
            exec_data = self._normalize_single_execution(
                tool, f"step_{step_idx}_trace_{tool_idx}", step_agent, step_timestamp, "trace_content"
            )
            if exec_data:
                executions.append(exec_data)
        
        return executions
    
    def _normalize_single_execution(self, tool_data: Any, execution_id: str, agent: str, timestamp: str, source: str) -> Optional[Dict[str, Any]]:
        """Normalize a single tool execution"""
        if not tool_data:
            return None
        
        # Handle different tool data formats
        if isinstance(tool_data, dict):
            tool_name = tool_data.get('tool_name', 'unknown')
            execution_time = tool_data.get('execution_time_ms', 0)
            success = tool_data.get('success', True)
            result_summary = tool_data.get('result_summary', '')
            error_message = tool_data.get('error_message')
            parameters = tool_data.get('parameters', {})
        else:
            # Handle object-based tools
            tool_name = getattr(tool_data, 'tool_name', 'unknown')
            execution_time = getattr(tool_data, 'execution_time_ms', 0)
            success = getattr(tool_data, 'success', True)
            result_summary = getattr(tool_data, 'result_summary', '')
            error_message = getattr(tool_data, 'error_message', None)
            parameters = getattr(tool_data, 'parameters', {})
        
        # Calculate parameters hash for deduplication
        params_str = json.dumps(parameters, sort_keys=True, default=str) if parameters else ""
        params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:16]
        
        # Determine execution status
        if error_message:
            status = ToolExecutionStatus.FAILED
        elif not success:
            status = ToolExecutionStatus.FAILED
        elif execution_time > 300000:  # 5+ minutes might indicate timeout
            status = ToolExecutionStatus.TIMEOUT
        elif result_summary and len(result_summary) > 10:
            status = ToolExecutionStatus.SUCCESS
        else:
            status = ToolExecutionStatus.UNKNOWN
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(tool_data, status, result_summary)
        
        # Extract execution purpose from context
        purpose = self._infer_execution_purpose(tool_name, parameters, result_summary)
        
        return {
            'execution_id': execution_id,
            'tool_name': tool_name,
            'initiating_agent': agent,
            'execution_purpose': purpose,
            'parameters_hash': params_hash,
            'result_summary': result_summary[:500] + "..." if len(result_summary) > 500 else result_summary,
            'execution_status': status,
            'execution_time_ms': execution_time,
            'timestamp': timestamp,
            'quality_score': quality_score,
            'error_details': error_message,
            'source': source,
            'original_data': tool_data,
            'parameters': parameters
        }
    
    def _calculate_quality_score(self, tool_data: Any, status: ToolExecutionStatus, result_summary: str) -> float:
        """Calculate quality score for tool execution"""
        score = 0.5  # Base score
        
        # Status-based scoring
        if status == ToolExecutionStatus.SUCCESS:
            score += 0.3
        elif status == ToolExecutionStatus.FAILED:
            score -= 0.2
        elif status == ToolExecutionStatus.TIMEOUT:
            score -= 0.1
        
        # Result quality scoring
        if result_summary:
            if len(result_summary) > 100:
                score += 0.2  # Comprehensive results
            if "successful" in result_summary.lower():
                score += 0.1
            if "error" in result_summary.lower():
                score -= 0.1
        
        # Execution time scoring (reasonable execution times get higher scores)
        if isinstance(tool_data, dict):
            exec_time = tool_data.get('execution_time_ms', 0)
        else:
            exec_time = getattr(tool_data, 'execution_time_ms', 0)
        
        if 1000 <= exec_time <= 30000:  # 1-30 seconds is reasonable
            score += 0.1
        elif exec_time > 120000:  # > 2 minutes might indicate issues
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _infer_execution_purpose(self, tool_name: str, parameters: Dict[str, Any], result_summary: str) -> str:
        """Infer the purpose of tool execution from context"""
        tool_lower = tool_name.lower()
        
        # Data query tools
        if any(keyword in tool_lower for keyword in ['query', 'sql', 'firebolt']):
            if parameters and 'query' in str(parameters).lower():
                # Try to extract query intent
                query_str = str(parameters).lower()
                if 'select' in query_str:
                    if any(table in query_str for table in ['deal', 'opportunity']):
                        return "deal_data_retrieval"
                    elif any(table in query_str for table in ['lead', 'contact']):
                        return "lead_data_retrieval"
                    elif any(word in query_str for word in ['revenue', 'mrr', 'arr']):
                        return "revenue_analysis"
                    else:
                        return "data_query"
                else:
                    return "database_operation"
            else:
                return "data_query"
        
        # API tools
        elif any(keyword in tool_lower for keyword in ['api', 'gong', 'salesforce']):
            if 'gong' in tool_lower:
                return "conversation_data_retrieval"
            elif 'salesforce' in tool_lower:
                return "crm_data_retrieval"
            else:
                return "external_api_call"
        
        # Communication tools  
        elif any(keyword in tool_lower for keyword in ['webhook', 'notification', 'email']):
            return "external_communication"
        
        # Search tools
        elif any(keyword in tool_lower for keyword in ['search', 'web']):
            return "information_lookup"
        
        # Analysis tools
        elif any(keyword in tool_lower for keyword in ['analysis', 'score', 'qualify']):
            return "data_analysis"
        
        else:
            return f"tool_execution_{tool_lower}"
    
    def _deduplicate_and_normalize(self, all_executions: List[Dict[str, Any]]) -> List[NormalizedToolExecution]:
        """Deduplicate and normalize tool executions"""
        # Group by tool type and parameters for deduplication
        execution_groups = {}
        
        for exec_data in all_executions:
            tool_name = exec_data['tool_name']
            params_hash = exec_data['parameters_hash']
            timestamp = exec_data['timestamp']
            
            # Determine tool category
            tool_category = self._get_tool_category(tool_name)
            
            # Create grouping key
            group_key = f"{tool_category}_{tool_name}_{params_hash}"
            
            if group_key not in execution_groups:
                execution_groups[group_key] = []
            
            execution_groups[group_key].append(exec_data)
        
        normalized_executions = []
        
        # Process each group
        for group_key, group_executions in execution_groups.items():
            if len(group_executions) == 1:
                # Single execution, just normalize
                normalized_exec = self._create_normalized_execution(group_executions[0], [])
                normalized_executions.append(normalized_exec)
            else:
                # Multiple executions, check for duplicates
                deduplicated_group = self._deduplicate_execution_group(group_executions)
                for exec_data, related in deduplicated_group:
                    normalized_exec = self._create_normalized_execution(exec_data, related)
                    normalized_executions.append(normalized_exec)
        
        # Sort by timestamp
        normalized_executions.sort(key=lambda x: x.timestamp or '')
        
        return normalized_executions
    
    def _get_tool_category(self, tool_name: str) -> str:
        """Get tool category for normalization"""
        tool_lower = tool_name.lower()
        
        for category, tools in self.tool_categories.items():
            if any(tool.lower() in tool_lower for tool in tools):
                return category
        
        return 'other'
    
    def _deduplicate_execution_group(self, group_executions: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], List[str]]]:
        """Deduplicate executions within a group"""
        if len(group_executions) <= 1:
            return [(group_executions[0], [])] if group_executions else []
        
        # Sort by timestamp
        group_executions.sort(key=lambda x: x['timestamp'] or '')
        
        deduplicated = []
        tool_category = self._get_tool_category(group_executions[0]['tool_name'])
        dedup_window = self.deduplication_windows.get(tool_category, 60)
        
        i = 0
        while i < len(group_executions):
            current_exec = group_executions[i]
            related_executions = []
            
            # Look for duplicates within time window
            j = i + 1
            current_time = self._parse_timestamp(current_exec['timestamp'])
            
            while j < len(group_executions):
                next_exec = group_executions[j]
                next_time = self._parse_timestamp(next_exec['timestamp'])
                
                if next_time and current_time:
                    time_diff = abs((next_time - current_time).total_seconds())
                    if time_diff <= dedup_window:
                        # This is likely a duplicate
                        related_executions.append(next_exec['execution_id'])
                        j += 1
                    else:
                        break
                else:
                    j += 1
            
            # Use the execution with best quality score as the primary
            candidates = [current_exec] + [group_executions[k] for k in range(i+1, j)]
            best_exec = max(candidates, key=lambda x: x['quality_score'])
            
            deduplicated.append((best_exec, related_executions))
            i = j
        
        return deduplicated
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return None
        
        try:
            # Handle different timestamp formats
            if 'T' in timestamp_str:
                if '+' in timestamp_str:
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    return datetime.fromisoformat(timestamp_str.replace('Z', ''))
            else:
                return datetime.fromisoformat(timestamp_str)
        except:
            return None
    
    def _create_normalized_execution(self, exec_data: Dict[str, Any], related_executions: List[str]) -> NormalizedToolExecution:
        """Create normalized tool execution object"""
        # Extract business context
        business_context = self._extract_business_context(exec_data)
        
        return NormalizedToolExecution(
            execution_id=exec_data['execution_id'],
            tool_name=exec_data['tool_name'],
            initiating_agent=exec_data['initiating_agent'],
            execution_purpose=exec_data['execution_purpose'],
            parameters_hash=exec_data['parameters_hash'],
            result_summary=exec_data['result_summary'],
            execution_status=exec_data['execution_status'],
            execution_time_ms=exec_data['execution_time_ms'],
            timestamp=exec_data['timestamp'],
            quality_score=exec_data['quality_score'],
            error_details=exec_data['error_details'],
            related_executions=related_executions,
            business_context=business_context
        )
    
    def _extract_business_context(self, exec_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract business context from execution data"""
        context = {
            "tool_category": self._get_tool_category(exec_data['tool_name']),
            "execution_source": exec_data['source'],
            "complexity_score": self._calculate_complexity_score(exec_data)
        }
        
        # Add parameter-based context
        parameters = exec_data.get('parameters', {})
        if parameters:
            # Check for business entities
            param_str = str(parameters).lower()
            
            if any(entity in param_str for entity in ['deal', 'opportunity', 'pipeline']):
                context["business_entity"] = "deal"
            elif any(entity in param_str for entity in ['lead', 'contact', 'prospect']):
                context["business_entity"] = "lead"  
            elif any(entity in param_str for entity in ['account', 'company', 'customer']):
                context["business_entity"] = "account"
            elif any(entity in param_str for entity in ['revenue', 'mrr', 'arr']):
                context["business_entity"] = "revenue"
            
            # Check for time-based queries
            if any(time_word in param_str for time_word in ['month', 'quarter', 'year', 'week', 'date']):
                context["temporal_query"] = True
        
        return context
    
    def _calculate_complexity_score(self, exec_data: Dict[str, Any]) -> float:
        """Calculate complexity score for execution"""
        score = 0.5  # Base score
        
        # Parameter complexity
        parameters = exec_data.get('parameters', {})
        if parameters:
            param_count = len(parameters)
            if param_count > 5:
                score += 0.2
            elif param_count > 2:
                score += 0.1
        
        # Result complexity
        result_length = len(exec_data.get('result_summary', ''))
        if result_length > 1000:
            score += 0.2
        elif result_length > 200:
            score += 0.1
        
        # Execution time complexity
        exec_time = exec_data.get('execution_time_ms', 0)
        if exec_time > 30000:  # 30+ seconds
            score += 0.2
        elif exec_time > 10000:  # 10+ seconds
            score += 0.1
        
        return min(1.0, score)
    
    def _reconstruct_agent_flow_with_normalized_tools(
        self, 
        original_agent_flow: List[Dict[str, Any]], 
        normalized_executions: List[NormalizedToolExecution],
        execution_to_step_map: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Reconstruct agent flow with normalized tool executions"""
        
        # Map normalized executions back to steps
        step_to_normalized_tools = {}
        for norm_exec in normalized_executions:
            # Find which step this belongs to from the execution ID
            for exec_id, step_idx in execution_to_step_map.items():
                if norm_exec.execution_id == exec_id:
                    if step_idx not in step_to_normalized_tools:
                        step_to_normalized_tools[step_idx] = []
                    step_to_normalized_tools[step_idx].append(norm_exec)
                    break
        
        # Reconstruct agent flow
        normalized_agent_flow = []
        
        for step_idx, step in enumerate(original_agent_flow):
            normalized_step = step.copy()
            
            # Replace tool arrays with normalized versions
            if step_idx in step_to_normalized_tools:
                normalized_tools = step_to_normalized_tools[step_idx]
                
                # Update tools_used with normalized data
                normalized_step['tools_used'] = [tool.to_dict() for tool in normalized_tools]
                
                # Update reasoning_breakdown.tool_executions
                if 'reasoning_breakdown' in normalized_step:
                    normalized_step['reasoning_breakdown']['tool_executions'] = [tool.to_dict() for tool in normalized_tools]
                
                # Add normalization metadata
                normalized_step['tool_normalization'] = {
                    "normalized_tool_count": len(normalized_tools),
                    "high_quality_tools": sum(1 for tool in normalized_tools if tool.quality_score >= 0.7),
                    "failed_tools": sum(1 for tool in normalized_tools if tool.execution_status == ToolExecutionStatus.FAILED),
                    "total_execution_time_ms": sum(tool.execution_time_ms for tool in normalized_tools),
                    "normalization_timestamp": datetime.utcnow().isoformat()
                }
            else:
                # No tools for this step, clean up tool arrays
                normalized_step['tools_used'] = []
                if 'reasoning_breakdown' in normalized_step:
                    normalized_step['reasoning_breakdown']['tool_executions'] = []
            
            normalized_agent_flow.append(normalized_step)
        
        return normalized_agent_flow