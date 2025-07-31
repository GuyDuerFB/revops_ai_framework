"""
Enhanced Conversation Transformer
Transforms raw conversation data into LLM-readable enhanced structure
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from reasoning_parser import ReasoningTextParser

logger = logging.getLogger(__name__)

class ConversationTransformer:
    """Transforms conversation data into enhanced LLM-readable format"""
    
    def __init__(self):
        self.parser = ReasoningTextParser()
    
    def transform_to_enhanced_structure(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform conversation data to enhanced LLM-readable structure"""
        
        try:
            # Extract base conversation info
            if isinstance(conversation_data, dict) and 'conversation' in conversation_data:
                conversation = conversation_data['conversation']
            else:
                conversation = conversation_data
            
            # Build enhanced structure
            enhanced_structure = {
                "export_metadata": {
                    "format": "enhanced_structured_json",
                    "version": "2.0",
                    "exported_at": datetime.utcnow().isoformat(),
                    "deduplication_applied": conversation_data.get('export_metadata', {}).get('deduplication_applied', False),
                    "system_prompts_excluded": True,
                    "note": "Enhanced LLM-readable format with structured reasoning breakdown"
                },
                "conversation": self._transform_conversation(conversation)
            }
            
            return enhanced_structure
            
        except Exception as e:
            logger.error(f"Error transforming conversation structure: {e}")
            # Return fallback structure
            return {
                "export_metadata": {
                    "format": "enhanced_structured_json",
                    "version": "2.0",
                    "exported_at": datetime.utcnow().isoformat(),
                    "transformation_error": str(e),
                    "note": "Transformation failed, using fallback structure"
                },
                "conversation": self._create_fallback_structure(conversation_data)
            }
    
    def _transform_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Transform the main conversation structure"""
        
        # Extract metadata
        metadata = self._extract_conversation_metadata(conversation)
        
        # Transform agent flow
        transformed_agent_flow = []
        if 'agent_flow' in conversation:
            for agent_step in conversation['agent_flow']:
                transformed_step = self._transform_agent_step(agent_step)
                transformed_agent_flow.append(transformed_step)
        
        # Generate conversation summary
        summary = self._generate_conversation_summary(conversation, transformed_agent_flow)
        
        return {
            "conversation_id": conversation.get('conversation_id', 'unknown'),
            "metadata": metadata,
            "agent_flow": transformed_agent_flow,
            "conversation_summary": summary
        }
    
    def _extract_conversation_metadata(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure conversation metadata"""
        
        metadata = {
            "start_timestamp": conversation.get('start_timestamp', ''),
            "end_timestamp": conversation.get('end_timestamp', ''),
            "duration_ms": 0,
            "success": conversation.get('success', True),
            "user_query": conversation.get('user_query', ''),
            "final_response": conversation.get('final_response', ''),
            "channel": conversation.get('channel', ''),
            "user_id": conversation.get('user_id', ''),
            "session_id": conversation.get('session_id', '')
        }
        
        # Calculate duration if timestamps available
        if metadata['start_timestamp'] and metadata['end_timestamp']:
            try:
                start_dt = datetime.fromisoformat(metadata['start_timestamp'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(metadata['end_timestamp'].replace('Z', '+00:00'))
                metadata['duration_ms'] = int((end_dt - start_dt).total_seconds() * 1000)
            except:
                metadata['duration_ms'] = conversation.get('processing_time_ms', 0)
        
        return metadata
    
    def _transform_agent_step(self, agent_step: Dict[str, Any]) -> Dict[str, Any]:
        """Transform individual agent step to enhanced structure"""
        
        # Extract basic agent info
        transformed_step = {
            "agent_name": agent_step.get('agent_name', 'unknown'),
            "agent_id": agent_step.get('agent_id', 'unknown'),
            "timing": {
                "start_time": agent_step.get('start_time', ''),
                "end_time": agent_step.get('end_time', ''),
                "duration_ms": self._calculate_step_duration(agent_step)
            }
        }
        
        # Parse reasoning text into structured format
        reasoning_text = agent_step.get('reasoning_text', '')
        if reasoning_text:
            transformed_step["reasoning_breakdown"] = self.parser.parse_reasoning_text(reasoning_text)
        else:
            transformed_step["reasoning_breakdown"] = {
                "context_setup": {},
                "knowledge_base_searches": [],
                "tool_executions": [],
                "decision_points": [],
                "final_synthesis": {}
            }
        
        # Transform tools used
        transformed_step["tools_used"] = self._transform_tools_used(agent_step.get('tools_used', []))
        
        # Transform data operations
        transformed_step["data_operations"] = self._transform_data_operations(agent_step.get('data_operations', []))
        
        # Extract routing decisions and analysis
        if 'routing_decision' in agent_step:
            transformed_step["routing_decision"] = agent_step['routing_decision']
        
        if 'meddpicc_analysis' in agent_step:
            transformed_step["meddpicc_analysis"] = agent_step['meddpicc_analysis']
        
        # Extract collaboration data
        transformed_step["collaboration"] = {
            "sent": agent_step.get('collaboration_sent', []),
            "received": agent_step.get('collaboration_received', [])
        }
        
        return transformed_step
    
    def _calculate_step_duration(self, agent_step: Dict[str, Any]) -> int:
        """Calculate duration for agent step"""
        
        try:
            start_time = agent_step.get('start_time', '')
            end_time = agent_step.get('end_time', '')
            
            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                return int((end_dt - start_dt).total_seconds() * 1000)
        except:
            pass
        
        return 0
    
    def _transform_tools_used(self, tools_used: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform tools used into structured format"""
        
        transformed_tools = []
        
        for tool in tools_used:
            if isinstance(tool, dict):
                transformed_tool = {
                    "tool_name": tool.get('tool_name', 'unknown'),
                    "execution_time_ms": tool.get('execution_time_ms', 0),
                    "success": tool.get('success', True),
                    "parameters_summary": tool.get('parameters_summary', ''),
                    "result_summary": tool.get('result_summary', ''),
                    "error_message": tool.get('error_message')
                }
                transformed_tools.append(transformed_tool)
            else:
                # Handle object-based tools
                transformed_tool = {
                    "tool_name": getattr(tool, 'tool_name', 'unknown'),
                    "execution_time_ms": getattr(tool, 'execution_time_ms', 0),
                    "success": getattr(tool, 'success', True),
                    "result_summary": getattr(tool, 'result_summary', ''),
                    "error_message": getattr(tool, 'error_message', None)
                }
                transformed_tools.append(transformed_tool)
        
        return transformed_tools
    
    def _transform_data_operations(self, data_operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform data operations into structured format"""
        
        transformed_ops = []
        
        for op in data_operations:
            if isinstance(op, dict):
                transformed_op = {
                    "operation": op.get('operation', 'unknown'),
                    "target": op.get('target', 'unknown'),
                    "execution_time_ms": op.get('execution_time_ms', 0),
                    "result_count": op.get('result_count', 0),
                    "query_summary": op.get('query_summary', ''),
                    "success": True  # Assume success unless indicated otherwise
                }
                transformed_ops.append(transformed_op)
            else:
                # Handle object-based operations
                transformed_op = {
                    "operation": getattr(op, 'operation', 'unknown'),
                    "target": getattr(op, 'target', 'unknown'),
                    "execution_time_ms": getattr(op, 'execution_time_ms', 0),
                    "result_count": getattr(op, 'result_count', 0),
                    "success": getattr(op, 'success', True)
                }
                transformed_ops.append(transformed_op)
        
        return transformed_ops
    
    def _generate_conversation_summary(self, conversation: Dict[str, Any], agent_flow: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive conversation summary"""
        
        # Count statistics
        total_kb_searches = 0
        total_tool_executions = 0
        total_data_operations = len(conversation.get('function_audit', {}).get('data_operations', []))
        knowledge_sources = set()
        databases_queried = set()
        
        for step in agent_flow:
            # Count KB searches
            kb_searches = step.get('reasoning_breakdown', {}).get('knowledge_base_searches', [])
            total_kb_searches += len(kb_searches)
            
            # Extract knowledge sources
            for search in kb_searches:
                for ref in search.get('references_found', []):
                    source_uri = ref.get('location', {}).get('s3_uri', '')
                    if source_uri:
                        # Extract meaningful part of S3 path
                        source_name = source_uri.split('/')[-1] if '/' in source_uri else source_uri
                        knowledge_sources.add(source_name)
            
            # Count tool executions
            tool_executions = step.get('reasoning_breakdown', {}).get('tool_executions', [])
            total_tool_executions += len(tool_executions)
            
            # Extract databases from data operations
            for op in step.get('data_operations', []):
                target = op.get('target', '')
                if target and target != 'unknown':
                    databases_queried.add(target)
        
        return {
            "total_agents_involved": len(agent_flow),
            "total_knowledge_base_searches": total_kb_searches,
            "total_tool_executions": total_tool_executions,
            "total_data_operations": total_data_operations,
            "knowledge_sources_accessed": list(knowledge_sources)[:10],  # Limit to top 10
            "databases_queried": list(databases_queried)[:10],
            "success": conversation.get('success', True),
            "processing_time_ms": conversation.get('processing_time_ms', 0),
            "agents_involved": conversation.get('agents_involved', []),
            "collaboration_events": len(conversation.get('collaboration_map', {})),
            "error_details": conversation.get('error_details')
        }
    
    def _create_fallback_structure(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback structure when transformation fails"""
        
        if isinstance(conversation_data, dict) and 'conversation' in conversation_data:
            conversation = conversation_data['conversation']
        else:
            conversation = conversation_data
        
        return {
            "conversation_id": conversation.get('conversation_id', 'unknown'),
            "metadata": {
                "start_timestamp": conversation.get('start_timestamp', ''),
                "end_timestamp": conversation.get('end_timestamp', ''),
                "success": conversation.get('success', True),
                "user_query": conversation.get('user_query', ''),
                "final_response": conversation.get('final_response', ''),
                "processing_time_ms": conversation.get('processing_time_ms', 0)
            },
            "agent_flow": conversation.get('agent_flow', []),
            "conversation_summary": {
                "total_agents_involved": len(conversation.get('agent_flow', [])),
                "success": conversation.get('success', True),
                "processing_time_ms": conversation.get('processing_time_ms', 0),
                "fallback_structure": True
            },
            "original_structure_preserved": True
        }
    
    def validate_enhanced_structure(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the enhanced structure and return validation results"""
        
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        
        try:
            # Check required top-level keys
            required_keys = ['export_metadata', 'conversation']
            for key in required_keys:
                if key not in enhanced_data:
                    validation['errors'].append(f"Missing required key: {key}")
                    validation['valid'] = False
            
            # Check conversation structure
            if 'conversation' in enhanced_data:
                conv = enhanced_data['conversation']
                
                # Check metadata
                if 'metadata' not in conv:
                    validation['warnings'].append("Missing conversation metadata")
                
                # Check agent flow
                if 'agent_flow' in conv:
                    agent_flow = conv['agent_flow']
                    validation['statistics']['agent_steps'] = len(agent_flow)
                    
                    # Check reasoning breakdown in each step
                    steps_with_reasoning = 0
                    for step in agent_flow:
                        if 'reasoning_breakdown' in step:
                            steps_with_reasoning += 1
                    
                    validation['statistics']['steps_with_enhanced_reasoning'] = steps_with_reasoning
                    
                    if steps_with_reasoning == 0:
                        validation['warnings'].append("No steps have enhanced reasoning breakdown")
                
                # Check conversation summary
                if 'conversation_summary' in conv:
                    summary = conv['conversation_summary']
                    validation['statistics'].update({
                        'total_kb_searches': summary.get('total_knowledge_base_searches', 0),
                        'total_tool_executions': summary.get('total_tool_executions', 0),
                        'knowledge_sources': len(summary.get('knowledge_sources_accessed', [])),
                        'databases_queried': len(summary.get('databases_queried', []))
                    })
        
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f"Validation error: {str(e)}")
        
        return validation