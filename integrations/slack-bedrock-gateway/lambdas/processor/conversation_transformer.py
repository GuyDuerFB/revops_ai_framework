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
    """Transforms conversation data into enhanced LLM-readable format with full processing pipeline"""
    
    def __init__(self, s3_bucket: Optional[str] = None):
        self.parser = ReasoningTextParser()
        
        # Initialize all processing components
        try:
            from system_prompt_manager import SystemPromptStripper
            from agent_attribution_engine import AgentAttributionEngine
            from tool_execution_normalizer import ToolExecutionNormalizer
            from user_query_extractor import UserQueryExtractor
            from response_content_parser import ResponseContentParser
            from conversation_quality_analyzer import ConversationQualityAnalyzer
            
            self.system_prompt_stripper = SystemPromptStripper(s3_bucket)
            self.agent_attribution_engine = AgentAttributionEngine()
            self.tool_normalizer = ToolExecutionNormalizer()
            self.query_extractor = UserQueryExtractor()
            self.response_parser = ResponseContentParser()
            self.quality_analyzer = ConversationQualityAnalyzer()
            
            self.full_pipeline_available = True
            logger.info("ConversationTransformer initialized with full processing pipeline")
            
        except ImportError as e:
            logger.warning(f"Some processing components not available: {e}")
            self.system_prompt_stripper = None
            self.agent_attribution_engine = None
            self.tool_normalizer = None
            self.query_extractor = None
            self.response_parser = None
            self.quality_analyzer = None
            self.full_pipeline_available = False
    
    def transform_to_enhanced_structure(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform conversation data to enhanced LLM-readable structure with full processing pipeline"""
        
        try:
            # Apply full processing pipeline if available
            if self.full_pipeline_available:
                processed_data = self._apply_full_processing_pipeline(conversation_data)
            else:
                processed_data = conversation_data
            
            # Extract base conversation info
            if isinstance(processed_data, dict) and 'conversation' in processed_data:
                conversation = processed_data['conversation']
            else:
                conversation = processed_data
            
            # Build enhanced structure
            enhanced_structure = {
                "export_metadata": {
                    "format": "enhanced_structured_json",
                    "version": "3.0",  # Updated version for new pipeline
                    "exported_at": datetime.utcnow().isoformat(),
                    "deduplication_applied": processed_data.get('export_metadata', {}).get('deduplication_applied', False),
                    "system_prompts_excluded": True,
                    "full_pipeline_applied": self.full_pipeline_available,
                    "note": "Enhanced LLM-readable format with comprehensive processing pipeline"
                },
                "conversation": self._transform_conversation(conversation)
            }
            
            # Add pipeline processing metadata if available
            if self.full_pipeline_available and 'export_metadata' in processed_data:
                pipeline_metadata = processed_data['export_metadata']
                enhanced_structure['export_metadata'].update({
                    "system_prompt_stripping": pipeline_metadata.get('system_prompt_stripping'),
                    "agent_attribution": pipeline_metadata.get('agent_attribution'),
                    "tool_normalization": pipeline_metadata.get('tool_normalization'),
                    "query_standardization": pipeline_metadata.get('user_query_standardization'),
                    "response_standardization": pipeline_metadata.get('response_standardization'),
                    "quality_analysis": pipeline_metadata.get('quality_analysis')
                })
            
            return enhanced_structure
            
        except Exception as e:
            logger.error(f"Failed to transform conversation to enhanced structure: {e}")
            # Return minimal structure to prevent total failure
            return {
                "export_metadata": {
                    "format": "enhanced_structured_json",
                    "version": "2.0",
                    "exported_at": datetime.utcnow().isoformat(),
                    "error": f"Transformation failed: {str(e)}",
                    "fallback_mode": True
                },
                "conversation": conversation_data if isinstance(conversation_data, dict) else {"error": "Invalid conversation data"}
            }
    
    def validate_enhanced_structure(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate enhanced structure and provide quality assessment"""
        
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "statistics": {},
            "quality_assessment": {}
        }
        
        try:
            # Basic structure validation
            if not isinstance(enhanced_data, dict):
                validation_result["valid"] = False
                validation_result["errors"].append("Enhanced data is not a dictionary")
                return validation_result
            
            # Check required top-level keys
            required_keys = ["export_metadata", "conversation"]
            for key in required_keys:
                if key not in enhanced_data:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Missing required key: {key}")
            
            if not validation_result["valid"]:
                return validation_result
            
            # Validate conversation structure
            conversation = enhanced_data.get("conversation", {})
            if not isinstance(conversation, dict):
                validation_result["valid"] = False
                validation_result["errors"].append("Conversation is not a dictionary")
                return validation_result
            
            # Extract statistics
            agent_flow = conversation.get("agent_flow", [])
            validation_result["statistics"] = {
                "agent_steps": len(agent_flow),
                "steps_with_enhanced_reasoning": sum(1 for step in agent_flow if isinstance(step, dict) and step.get("reasoning_breakdown")),
                "total_kb_searches": sum(len(step.get("reasoning_breakdown", {}).get("knowledge_base_searches", [])) for step in agent_flow if isinstance(step, dict)),
                "total_tool_executions": sum(len(step.get("reasoning_breakdown", {}).get("tool_executions", [])) for step in agent_flow if isinstance(step, dict)),
                "detected_handovers": len(conversation.get("detected_agent_handovers", [])),
                "agents_involved": len(conversation.get("agents_involved", []))
            }
            
            # Quality assessment
            stats = validation_result["statistics"]
            quality_score = 0.0
            
            # Agent flow quality
            if stats["agent_steps"] > 0:
                quality_score += 0.2
                if stats["steps_with_enhanced_reasoning"] > 0:
                    quality_score += 0.3
                if stats["detected_handovers"] > 0:
                    quality_score += 0.2
                if stats["total_tool_executions"] > 0:
                    quality_score += 0.2
                if stats["total_kb_searches"] > 0:
                    quality_score += 0.1
            
            validation_result["quality_assessment"] = {
                "overall_score": min(1.0, quality_score),
                "has_agent_flow": stats["agent_steps"] > 0,
                "has_enhanced_reasoning": stats["steps_with_enhanced_reasoning"] > 0,
                "has_handover_detection": stats["detected_handovers"] > 0,
                "has_tool_executions": stats["total_tool_executions"] > 0
            }
            
            # Add warnings for quality issues
            if quality_score < 0.5:
                validation_result["warnings"].append("Low quality score - limited data enrichment")
            if stats["agent_steps"] == 0:
                validation_result["warnings"].append("No agent steps found")
            if stats["detected_handovers"] == 0 and stats["agent_steps"] > 1:
                validation_result["warnings"].append("Multiple agent steps but no handovers detected")
                
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["quality_assessment"]["overall_score"] = 0.0
        
        return validation_result
    
    def _transform_agent_step(self, agent_step: Dict[str, Any]) -> Dict[str, Any]:
        """Transform individual agent step with enhanced reasoning breakdown"""
        
        if not isinstance(agent_step, dict):
            return agent_step
        
        # Start with basic step structure
        transformed_step = {
            "agent_name": agent_step.get("agent_name", "unknown"),
            "agent_id": agent_step.get("agent_id", ""),
            "timing": agent_step.get("timing", {}),
            "agent_handover_detected": agent_step.get("agent_handover_detected", False)
        }
        
        # Add handover information if detected
        if agent_step.get("agent_handover_detected"):
            transformed_step["original_agent_name"] = agent_step.get("original_agent_name", "")
            transformed_step["handover_evidence"] = agent_step.get("handover_evidence", {})
        
        # Parse reasoning text into structured breakdown
        reasoning_text = agent_step.get("reasoning_text", "")
        if reasoning_text and not agent_step.get("reasoning_breakdown"):
            # Use ReasoningTextParser to create structured breakdown
            reasoning_breakdown = self.parser.parse_reasoning_text(reasoning_text)
            transformed_step["reasoning_breakdown"] = reasoning_breakdown
        elif agent_step.get("reasoning_breakdown"):
            transformed_step["reasoning_breakdown"] = agent_step["reasoning_breakdown"]
        
        # Include tools and data operations
        transformed_step["tools_used"] = agent_step.get("tools_used", [])
        transformed_step["data_operations"] = agent_step.get("data_operations", [])
        
        # Include filtered trace content (no raw system prompts)
        if agent_step.get("bedrock_trace_content"):
            trace_content = agent_step["bedrock_trace_content"]
            # Only include safe trace content fields
            safe_trace = {}
            for key in ["invocationInput", "actionGroupInvocationInput", "observation"]:
                if key in trace_content:
                    safe_trace[key] = trace_content[key]
            if safe_trace:
                transformed_step["filtered_trace_content"] = safe_trace
        
        return transformed_step
    
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
            "conversation_summary": summary,
            "detected_agent_handovers": conversation.get('detected_agent_handovers', []),
            "agents_involved": conversation.get('agents_involved', [])
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
        
        # ENHANCED: Parse Bedrock trace content for agent handoffs and detailed tool info
        bedrock_trace_content = agent_step.get('bedrock_trace_content')
        if bedrock_trace_content:
            trace_parsed = self.parser.parse_bedrock_trace_content(bedrock_trace_content)
            
            # Add agent handoffs to collaboration data with enhanced detection
            agent_handoffs = trace_parsed.get('agent_handoffs', [])
            if agent_handoffs:
                transformed_step["agent_handoffs"] = agent_handoffs
                # Update agent name if we found better attribution
                for handoff in agent_handoffs:
                    if handoff.get('target_agent') and handoff['target_agent'] != 'unknown':
                        if transformed_step["agent_name"] == 'unknown':
                            transformed_step["agent_name"] = handoff['target_agent']
                            logger.info(f"Updated agent attribution from trace: {handoff['target_agent']}")
            
            # ENHANCED: Extract agent communications with better collaboration mapping
            agent_comms = trace_parsed.get('agent_communications', [])
            if agent_comms:
                transformed_step["agent_communications"] = agent_comms
                # Build collaboration map from communications
                collaboration_map = self._build_collaboration_map_from_communications(agent_comms)
                if collaboration_map:
                    transformed_step["collaboration_map"] = collaboration_map
            
            # Enhance tool executions from trace content
            trace_tools = trace_parsed.get('tool_executions', [])
            if trace_tools:
                transformed_step["trace_tool_executions"] = trace_tools
            
            # Add parsed messages for detailed analysis with agent communication extraction
            parsed_messages = trace_parsed.get('messages_parsed', [])
            if parsed_messages:
                transformed_step["parsed_messages"] = parsed_messages
                # Extract and consolidate agent communications from parsed messages
                all_agent_communications = []
                for msg in parsed_messages:
                    msg_comms = msg.get('parsed_content', {}).get('agent_communications', [])
                    all_agent_communications.extend(msg_comms)
                
                if all_agent_communications:
                    # Merge with existing communications
                    existing_comms = transformed_step.get("agent_communications", [])
                    merged_comms = self._merge_agent_communications(existing_comms, all_agent_communications)
                    transformed_step["agent_communications"] = merged_comms
            
            # Add routing decisions with agent context
            routing_decisions = trace_parsed.get('routing_decisions', [])
            if routing_decisions:
                transformed_step["routing_decisions"] = routing_decisions
                # Extract agent handover indicators from routing decisions
                handover_indicators = self._extract_handover_indicators_from_routing(routing_decisions)
                if handover_indicators:
                    transformed_step["handover_indicators"] = handover_indicators
        
        # Transform tools used (legacy format)
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
        
        # ENHANCED: Track agent attribution and handoffs
        agents_involved = set()
        agent_handoffs = []
        routing_decisions = []
        total_agent_communications = 0
        
        for step in agent_flow:
            # Track agent names
            agent_name = step.get('agent_name', 'unknown')
            if agent_name != 'unknown':
                agents_involved.add(agent_name)
            
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
            
            # Count tool executions with quality assessment
            tool_executions = step.get('reasoning_breakdown', {}).get('tool_executions', [])
            total_tool_executions += len(tool_executions)
            
            # ENHANCED: Count trace-based tool executions
            trace_tools = step.get('trace_tool_executions', [])
            total_tool_executions += len(trace_tools)
            
            # ENHANCED: Track tool execution quality
            high_quality_executions = 0
            failed_executions = 0
            for tool_exec in tool_executions:
                quality_score = tool_exec.get('quality_score', 0.0)
                if quality_score >= 0.7:
                    high_quality_executions += 1
                if tool_exec.get('execution_status') == 'failed':
                    failed_executions += 1
            
            # ENHANCED: Track agent handoffs
            step_handoffs = step.get('agent_handoffs', [])
            agent_handoffs.extend(step_handoffs)
            for handoff in step_handoffs:
                target_agent = handoff.get('target_agent', 'unknown')
                if target_agent != 'unknown':
                    agents_involved.add(target_agent)
            
            # ENHANCED: Track routing decisions
            step_routing = step.get('routing_decisions', [])
            routing_decisions.extend(step_routing)
            
            # ENHANCED: Count agent communications
            agent_comms = step.get('agent_communications', [])
            total_agent_communications += len(agent_comms)
            
            # Extract databases from data operations
            for op in step.get('data_operations', []):
                target = op.get('target', '')
                if target and target != 'unknown':
                    databases_queried.add(target)
        
        # Build detailed agent involvement summary
        agent_involvement_summary = {}
        for step in agent_flow:
            agent_name = step.get('agent_name', 'unknown')
            if agent_name not in agent_involvement_summary:
                agent_involvement_summary[agent_name] = {
                    "tool_executions": 0,
                    "kb_searches": 0,
                    "duration_ms": 0,
                    "handoffs_initiated": 0
                }
            
            # Count tools used by this agent
            tools_used = step.get('tools_used', [])
            trace_tools = step.get('trace_tool_executions', [])
            agent_involvement_summary[agent_name]["tool_executions"] += len(tools_used) + len(trace_tools)
            
            # Count KB searches by this agent
            kb_searches = step.get('reasoning_breakdown', {}).get('knowledge_base_searches', [])
            agent_involvement_summary[agent_name]["kb_searches"] += len(kb_searches)
            
            # Add duration
            agent_involvement_summary[agent_name]["duration_ms"] += step.get('timing', {}).get('duration_ms', 0)
            
            # Count handoffs initiated
            handoffs = step.get('agent_handoffs', [])
            agent_involvement_summary[agent_name]["handoffs_initiated"] += len(handoffs)
        
        return {
            "total_agents_involved": len(agents_involved),
            "agents_involved": list(agents_involved),
            "agent_involvement_summary": agent_involvement_summary,
            "total_knowledge_base_searches": total_kb_searches,
            "total_tool_executions": total_tool_executions,
            "total_data_operations": total_data_operations,
            "total_agent_communications": total_agent_communications,
            "total_agent_handoffs": len(agent_handoffs),
            "total_routing_decisions": len(routing_decisions),
            "knowledge_sources_accessed": list(knowledge_sources)[:10],  # Limit to top 10
            "databases_queried": list(databases_queried)[:10],
            "success": conversation.get('success', True),
            "processing_time_ms": conversation.get('processing_time_ms', 0),
            "collaboration_events": len(conversation.get('collaboration_map', {})),
            "error_details": conversation.get('error_details'),
            "agent_handoffs": agent_handoffs[:5],  # Show first 5 handoffs
            "routing_decisions": routing_decisions[:3],  # Show first 3 routing decisions
            "data_quality_metrics": {
                "high_quality_tool_executions": locals().get('high_quality_executions', 0),
                "failed_tool_executions": locals().get('failed_executions', 0),
                "tool_execution_success_rate": (total_tool_executions - locals().get('failed_executions', 0)) / max(total_tool_executions, 1),
                "average_agent_step_duration_ms": sum(step.get('timing', {}).get('duration_ms', 0) for step in agent_flow) / max(len(agent_flow), 1),
                "data_operations_per_agent": total_data_operations / max(len(agents_involved), 1)
            }
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
        """Validate the enhanced structure and return validation results with quality assessment"""
        
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {},
            "quality_assessment": {
                "overall_score": 0.0,
                "data_completeness": 0.0,
                "agent_attribution_quality": 0.0,
                "tool_execution_quality": 0.0,
                "reasoning_quality": 0.0
            }
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
                else:
                    validation['quality_assessment']['data_completeness'] += 0.2
                
                # ENHANCED: Check agent flow with quality assessment
                if 'agent_flow' in conv:
                    agent_flow = conv['agent_flow']
                    validation['statistics']['agent_steps'] = len(agent_flow)
                    
                    # Check reasoning breakdown in each step
                    steps_with_reasoning = 0
                    steps_with_agent_attribution = 0
                    steps_with_tool_executions = 0
                    high_quality_tool_executions = 0
                    total_tool_executions = 0
                    
                    for step in agent_flow:
                        # Check reasoning breakdown
                        if 'reasoning_breakdown' in step:
                            steps_with_reasoning += 1
                            reasoning = step['reasoning_breakdown']
                            
                            # Assess reasoning quality
                            if reasoning.get('knowledge_base_searches'):
                                validation['quality_assessment']['reasoning_quality'] += 0.1
                            if reasoning.get('decision_points'):
                                validation['quality_assessment']['reasoning_quality'] += 0.1
                            if reasoning.get('final_synthesis'):
                                validation['quality_assessment']['reasoning_quality'] += 0.1
                        
                        # Check agent attribution
                        agent_name = step.get('agent_name', 'unknown')
                        if agent_name != 'unknown':
                            steps_with_agent_attribution += 1
                        
                        # Check for enhanced agent data
                        if step.get('agent_handoffs') or step.get('agent_communications'):
                            validation['quality_assessment']['agent_attribution_quality'] += 0.1
                        
                        # Check tool execution quality
                        tool_executions = step.get('reasoning_breakdown', {}).get('tool_executions', [])
                        total_tool_executions += len(tool_executions)
                        
                        for tool_exec in tool_executions:
                            if tool_exec.get('quality_score', 0) >= 0.7:
                                high_quality_tool_executions += 1
                        
                        if tool_executions:
                            steps_with_tool_executions += 1
                    
                    # Calculate quality scores
                    if len(agent_flow) > 0:
                        validation['quality_assessment']['data_completeness'] += 0.3 * (steps_with_reasoning / len(agent_flow))
                        validation['quality_assessment']['agent_attribution_quality'] += 0.4 * (steps_with_agent_attribution / len(agent_flow))
                    
                    if total_tool_executions > 0:
                        validation['quality_assessment']['tool_execution_quality'] = high_quality_tool_executions / total_tool_executions
                    
                    validation['statistics'].update({
                        'steps_with_enhanced_reasoning': steps_with_reasoning,
                        'steps_with_agent_attribution': steps_with_agent_attribution,
                        'steps_with_tool_executions': steps_with_tool_executions,
                        'high_quality_tool_executions': high_quality_tool_executions,
                        'total_tool_executions': total_tool_executions
                    })
                    
                    # Generate warnings based on quality
                    if steps_with_reasoning == 0:
                        validation['warnings'].append("No steps have enhanced reasoning breakdown")
                    
                    if steps_with_agent_attribution / max(len(agent_flow), 1) < 0.5:
                        validation['warnings'].append("Less than 50% of steps have proper agent attribution")
                    
                    if total_tool_executions > 0 and high_quality_tool_executions / total_tool_executions < 0.3:
                        validation['warnings'].append("Less than 30% of tool executions have high quality data")
                
                # ENHANCED: Check conversation summary with quality metrics
                if 'conversation_summary' in conv:
                    summary = conv['conversation_summary']
                    validation['statistics'].update({
                        'total_kb_searches': summary.get('total_knowledge_base_searches', 0),
                        'total_tool_executions': summary.get('total_tool_executions', 0),
                        'knowledge_sources': len(summary.get('knowledge_sources_accessed', [])),
                        'databases_queried': len(summary.get('databases_queried', []))
                    })
                    
                    # Check for enhanced quality metrics
                    if 'data_quality_metrics' in summary:
                        validation['quality_assessment']['data_completeness'] += 0.2
                        quality_metrics = summary['data_quality_metrics']
                        if quality_metrics.get('tool_execution_success_rate', 0) > 0.8:
                            validation['quality_assessment']['tool_execution_quality'] += 0.2
                    
                    validation['quality_assessment']['data_completeness'] += 0.3
            
            # Calculate overall quality score
            quality_scores = validation['quality_assessment']
            overall_score = sum([quality_scores['data_completeness'], 
                               quality_scores['agent_attribution_quality'],
                               quality_scores['tool_execution_quality'],
                               quality_scores['reasoning_quality']]) / 4
            
            validation['quality_assessment']['overall_score'] = min(1.0, overall_score)
            
            # Add quality-based warnings
            if overall_score < 0.5:
                validation['warnings'].append(f"Overall data quality is below threshold (score: {overall_score:.2f})")
            
            # ENHANCED: System prompt filtering validation
            export_metadata = enhanced_data.get('export_metadata', {})
            if not export_metadata.get('system_prompts_excluded', False):
                validation['warnings'].append("System prompts may not have been properly filtered")
        
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f"Validation error: {str(e)}")
        
        return validation
    
    def _build_collaboration_map_from_communications(self, agent_communications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build collaboration map from agent communications"""
        
        collaboration_map = {
            "communication_count": len(agent_communications),
            "unique_recipients": set(),
            "communication_types": {},
            "message_flow": [],
            "collaboration_timeline": []
        }
        
        try:
            for comm in agent_communications:
                # Track recipients
                recipient = comm.get('recipient', comm.get('collaborator_name', comm.get('target_agent', 'unknown')))
                if recipient and recipient != 'unknown':
                    collaboration_map["unique_recipients"].add(recipient)
                
                # Track communication types
                comm_type = comm.get('type', 'unknown')
                if comm_type not in collaboration_map["communication_types"]:
                    collaboration_map["communication_types"][comm_type] = 0
                collaboration_map["communication_types"][comm_type] += 1
                
                # Build message flow
                flow_entry = {
                    "type": comm_type,
                    "recipient": recipient,
                    "content_preview": comm.get('content', '')[:100] + "..." if len(comm.get('content', '')) > 100 else comm.get('content', ''),
                    "timestamp": comm.get('timestamp', ''),
                    "data_source": comm.get('data_source', 'unknown')
                }
                collaboration_map["message_flow"].append(flow_entry)
                
                # Add to timeline
                timeline_entry = {
                    "timestamp": comm.get('timestamp', ''),
                    "event": f"{comm_type} to {recipient}",
                    "details": comm.get('content', '')[:50] + "..." if len(comm.get('content', '')) > 50 else comm.get('content', '')
                }
                collaboration_map["collaboration_timeline"].append(timeline_entry)
            
            # Convert set to list for JSON serialization
            collaboration_map["unique_recipients"] = list(collaboration_map["unique_recipients"])
            
            # Sort timeline by timestamp if available
            collaboration_map["collaboration_timeline"].sort(key=lambda x: x.get('timestamp', ''))
            
        except Exception as e:
            logger.warning(f"Error building collaboration map: {e}")
            collaboration_map["error"] = str(e)
        
        return collaboration_map
    
    def _merge_agent_communications(self, existing_comms: List[Dict[str, Any]], new_comms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge agent communications, avoiding duplicates"""
        
        merged = list(existing_comms)  # Start with existing
        
        try:
            # Create a set of signatures for existing communications to avoid duplicates
            existing_signatures = set()
            for comm in existing_comms:
                signature = f"{comm.get('type', '')}_{comm.get('recipient', '')}_{comm.get('content', '')[:50]}"
                existing_signatures.add(signature)
            
            # Add new communications that don't already exist
            for new_comm in new_comms:
                signature = f"{new_comm.get('type', '')}_{new_comm.get('recipient', '')}_{new_comm.get('content', '')[:50]}"
                if signature not in existing_signatures:
                    merged.append(new_comm)
                    existing_signatures.add(signature)
            
        except Exception as e:
            logger.warning(f"Error merging agent communications: {e}")
            # On error, just concatenate
            merged = existing_comms + new_comms
        
        return merged
    
    def _extract_handover_indicators_from_routing(self, routing_decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract agent handover indicators from routing decisions"""
        
        handover_indicators = []
        
        try:
            for decision in routing_decisions:
                # Look for agent selection or routing to specific agents
                if decision.get('selected_agent') or decision.get('target_agent'):
                    target_agent = decision.get('selected_agent') or decision.get('target_agent')
                    
                    indicator = {
                        "type": "routing_decision",
                        "target_agent": target_agent,
                        "confidence": decision.get('confidence', 0.0),
                        "reasoning": decision.get('reasoning', ''),
                        "timestamp": decision.get('timestamp', ''),
                        "source": "routing_decision"
                    }
                    
                    # Extract handover reasoning
                    reasoning = decision.get('reasoning', '').lower()
                    if any(keyword in reasoning for keyword in ['handover', 'transfer', 'route to', 'pass to', 'redirect to']):
                        indicator["handover_type"] = "explicit_routing"
                    elif any(keyword in reasoning for keyword in ['specialist', 'expert', 'better suited']):
                        indicator["handover_type"] = "expertise_based"
                    else:
                        indicator["handover_type"] = "implicit_routing"
                    
                    handover_indicators.append(indicator)
                
                # Look for workflow progression indicators
                if decision.get('workflow_step') or decision.get('next_action'):
                    workflow_indicator = {
                        "type": "workflow_progression",
                        "next_step": decision.get('workflow_step') or decision.get('next_action'),
                        "current_agent": decision.get('current_agent', 'unknown'),
                        "timestamp": decision.get('timestamp', ''),
                        "source": "workflow_decision"
                    }
                    handover_indicators.append(workflow_indicator)
            
        except Exception as e:
            logger.warning(f"Error extracting handover indicators: {e}")
        
        return handover_indicators
    
    def _apply_full_processing_pipeline(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the complete processing pipeline to conversation data"""
        
        processed_data = conversation_data.copy()
        
        try:
            # Step 1: System prompt stripping (pre-processing)
            if self.system_prompt_stripper:
                processed_data, stripping_stats = self.system_prompt_stripper.preprocess_conversation_data(processed_data)
                logger.info(f"System prompt stripping complete: {stripping_stats.get('total_prompts_removed', 0)} prompts removed")
            
            # Step 2: User query standardization
            if self.query_extractor:
                processed_data = self.query_extractor.standardize_conversation_query_field(processed_data)
                logger.info("User query standardization complete")
            
            # Step 3: Response content parsing
            if self.response_parser:
                processed_data = self.response_parser.standardize_conversation_response(processed_data)
                logger.info("Response content parsing complete")
            
            # Step 4: Agent attribution enhancement
            if self.agent_attribution_engine:
                processed_data = self._apply_enhanced_agent_attribution(processed_data)
                logger.info("Enhanced agent attribution complete")
            
            # Step 5: Tool execution normalization
            if self.tool_normalizer:
                processed_data = self._apply_tool_normalization(processed_data)
                logger.info("Tool execution normalization complete")
            
            # Step 6: Quality analysis
            if self.quality_analyzer:
                processed_data = self._apply_quality_analysis(processed_data)
                logger.info("Quality analysis complete")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error in processing pipeline: {e}")
            # Return original data if pipeline fails
            return conversation_data
    
    def _apply_enhanced_agent_attribution(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply enhanced agent attribution to conversation"""
        
        conversation = conversation_data.get('conversation', {})
        agent_flow = conversation.get('agent_flow', [])
        
        if not agent_flow:
            return conversation_data
        
        agents_involved = set()
        handoffs_detected = []
        attribution_stats = {
            'steps_processed': 0,
            'high_confidence_attributions': 0,
            'handoffs_detected': 0,
            'collaboration_events': 0
        }
        
        # Apply attribution to each step
        for step in agent_flow:
            attribution = self.agent_attribution_engine.detect_agent_from_multiple_sources(step)
            
            # Update step with enhanced attribution
            original_agent = step.get('agent_name', 'unknown')
            step['agent_name'] = attribution.attributed_agent
            step['enhanced_agent_attribution'] = {
                'attributed_agent': attribution.attributed_agent,
                'confidence_score': attribution.confidence_score,
                'evidence_sources': attribution.evidence_sources,
                'detection_methods': attribution.detection_methods,
                'original_agent': attribution.original_agent,
                'handoff_detected': attribution.handoff_detected,
                'collaboration_indicators': attribution.collaboration_indicators
            }
            
            agents_involved.add(attribution.attributed_agent)
            attribution_stats['steps_processed'] += 1
            
            if attribution.confidence_score >= 0.8:
                attribution_stats['high_confidence_attributions'] += 1
            
            if attribution.handoff_detected:
                attribution_stats['handoffs_detected'] += 1
            
            if attribution.collaboration_indicators:
                attribution_stats['collaboration_events'] += len(attribution.collaboration_indicators)
        
        # Detect conversation-level handoffs
        handoffs = self.agent_attribution_engine.detect_agent_handoffs_in_conversation(agent_flow)
        handoffs_detected = [{'from_agent': h.from_agent, 'to_agent': h.to_agent, 'handoff_reason': h.handoff_reason, 'confidence_score': h.confidence_score, 'handoff_type': h.handoff_type, 'timestamp': h.timestamp} for h in handoffs]
        
        # Update conversation with attribution results
        conversation['agents_involved'] = list(agents_involved)
        conversation['detected_agent_handovers'] = handoffs_detected
        
        # Add attribution metadata
        if 'export_metadata' not in conversation_data:
            conversation_data['export_metadata'] = {}
        
        conversation_data['export_metadata']['agent_attribution'] = {
            'applied': True,
            'attribution_engine_version': '1.0',
            'statistics': attribution_stats,
            'agents_identified': list(agents_involved),
            'handoffs_detected': len(handoffs_detected),
            'attribution_timestamp': datetime.utcnow().isoformat()
        }
        
        return conversation_data
    
    def _apply_tool_normalization(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply tool execution normalization to conversation"""
        
        conversation = conversation_data.get('conversation', {})
        agent_flow = conversation.get('agent_flow', [])
        
        if not agent_flow:
            return conversation_data
        
        # Normalize tool executions
        normalized_flow, normalization_stats = self.tool_normalizer.normalize_tool_executions(agent_flow)
        
        # Update conversation with normalized flow
        conversation['agent_flow'] = normalized_flow
        
        # Add normalization metadata
        if 'export_metadata' not in conversation_data:
            conversation_data['export_metadata'] = {}
        
        conversation_data['export_metadata']['tool_normalization'] = {
            'applied': True,
            'normalization_engine_version': '1.0',
            'statistics': {
                'original_executions': normalization_stats.original_executions,
                'normalized_executions': normalization_stats.normalized_executions,
                'duplicates_removed': normalization_stats.duplicates_removed,
                'failed_executions': normalization_stats.failed_executions,
                'high_quality_executions': normalization_stats.high_quality_executions,
                'tool_types_used': list(normalization_stats.tool_types_used),
                'total_execution_time_ms': normalization_stats.total_execution_time_ms
            },
            'normalization_timestamp': normalization_stats.normalization_timestamp
        }
        
        logger.info(f"Tool normalization: {normalization_stats.original_executions} -> {normalization_stats.normalized_executions} executions")
        
        return conversation_data
    
    def _apply_quality_analysis(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply comprehensive quality analysis to conversation"""
        
        # Perform quality analysis
        quality_analysis = self.quality_analyzer.analyze_conversation_quality(conversation_data)
        
        # Add quality analysis to conversation
        conversation = conversation_data.get('conversation', {})
        conversation['quality_analysis'] = {
            'overall_score': quality_analysis.quality_metrics.overall_score,
            'quality_metrics': {
                'completeness_score': quality_analysis.quality_metrics.completeness_score,
                'accuracy_score': quality_analysis.quality_metrics.accuracy_score,
                'timeliness_score': quality_analysis.quality_metrics.timeliness_score,
                'relevance_score': quality_analysis.quality_metrics.relevance_score,
                'user_satisfaction_score': quality_analysis.quality_metrics.user_satisfaction_score,
                'technical_quality_score': quality_analysis.quality_metrics.technical_quality_score,
                'business_impact_score': quality_analysis.quality_metrics.business_impact_score
            },
            'outcome_analysis': {
                'outcome': quality_analysis.outcome_analysis.outcome.value,
                'confidence': quality_analysis.outcome_analysis.confidence,
                'user_satisfaction': quality_analysis.outcome_analysis.user_satisfaction.value,
                'business_value_delivered': quality_analysis.outcome_analysis.business_value_delivered,
                'follow_up_needed': quality_analysis.outcome_analysis.follow_up_needed,
                'success_indicators': quality_analysis.outcome_analysis.success_indicators,
                'failure_indicators': quality_analysis.outcome_analysis.failure_indicators,
                'improvement_suggestions': quality_analysis.outcome_analysis.improvement_suggestions
            },
            'agent_performance': [
                {
                    'agent_name': perf.agent_name,
                    'effectiveness_score': perf.effectiveness_score,
                    'response_time_ms': perf.response_time_ms,
                    'tool_success_rate': perf.tool_success_rate,
                    'collaboration_score': perf.collaboration_score,
                    'business_contribution': perf.business_contribution
                } for perf in quality_analysis.agent_performance
            ],
            'system_performance': quality_analysis.system_performance,
            'recommendations': quality_analysis.recommendations
        }
        
        # Add quality analysis metadata
        if 'export_metadata' not in conversation_data:
            conversation_data['export_metadata'] = {}
        
        conversation_data['export_metadata']['quality_analysis'] = {
            'applied': True,
            'analyzer_version': '1.0',
            'analysis_timestamp': quality_analysis.analysis_timestamp,
            'overall_score': quality_analysis.quality_metrics.overall_score,
            'quality_category': quality_analysis.metadata.get('quality_category', 'unknown'),
            'business_relevance': quality_analysis.metadata.get('business_relevance', 0.0),
            'improvement_potential': quality_analysis.metadata.get('improvement_potential', 0.0)
        }
        
        logger.info(f"Quality analysis complete: overall score {quality_analysis.quality_metrics.overall_score:.2f}")
        
        return conversation_data