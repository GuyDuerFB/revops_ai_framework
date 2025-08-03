"""
S3 Conversation Export Tool
Exports conversations in multiple formats optimized for different use cases
"""

import boto3
import json
import logging
import base64
import copy
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from conversation_transformer import ConversationTransformer
from prompt_deduplicator import PromptDeduplicator

class ConversationExporter:
    """Handles exporting conversations to S3 in multiple formats"""
    
    def __init__(self, s3_bucket: str, s3_prefix: str = "conversation-history/"):
        self.s3_client = boto3.client('s3')
        self.bucket = s3_bucket
        self.prefix = s3_prefix
        self.logger = logging.getLogger(__name__)
        self.transformer = ConversationTransformer()
        self.prompt_deduplicator = PromptDeduplicator()
    
    def export_conversation(self, conversation, formats: List[str]) -> Dict[str, str]:
        """Export conversation in specified formats and return S3 URLs"""
        
        exported_urls = {}
        
        # Generate base path: conversation-history/2025/07/29/conv-id/
        base_path = self._get_s3_path(conversation, "")
        
        format_handlers = {
            'enhanced_structured_json': ('conversation.json', self._to_enhanced_structured_json),
            'structured_json': ('legacy_conversation.json', self._to_structured_json),
            'llm_readable': ('conversation.txt', self._to_llm_readable_text),
            'analysis_format': ('analysis.json', self._to_analysis_format),
            'metadata_only': ('metadata.json', self._to_metadata_only),
            'agent_traces': ('traces.json', self._to_agent_traces)
        }
        
        for format_name in formats:
            if format_name not in format_handlers:
                self.logger.warning(f"Unknown format: {format_name}")
                continue
                
            filename, handler = format_handlers[format_name]
            
            try:
                # Generate content
                content = handler(conversation)
                
                # ENHANCED: Validate content before upload
                is_valid, validation_errors = self.validate_export_before_upload(content, format_name)
                
                if not is_valid:
                    self.logger.error(f"Export validation failed for {format_name}: {validation_errors}")
                    # Still upload but mark as having issues
                    validation_status = "failed"
                else:
                    validation_status = "passed"
                
                # Upload to S3
                s3_key = f"{base_path}{filename}"
                
                # ENHANCED: Add validation status to metadata
                metadata = {
                    'conversation-id': getattr(conversation, 'conversation_id', conversation.get('conversation_id', 'unknown') if isinstance(conversation, dict) else 'unknown'),
                    'export-timestamp': datetime.utcnow().isoformat(),
                    'format': format_name,
                    'validation-status': validation_status,
                    'content-size-bytes': str(len(content.encode('utf-8')))
                }
                
                if validation_errors:
                    metadata['validation-errors'] = str(len(validation_errors))
                
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=content.encode('utf-8'),
                    ContentType='application/json' if filename.endswith('.json') else 'text/plain',
                    Metadata=metadata
                )
                
                exported_urls[format_name] = f"s3://{self.bucket}/{s3_key}"
                self.logger.info(f"Exported {format_name} to {exported_urls[format_name]} (validation: {validation_status})")
                
            except Exception as e:
                self.logger.error(f"Failed to export {format_name}: {e}")
                
        return exported_urls
    
    def _get_s3_path(self, conversation, filename: str) -> str:
        """Generate S3 path: conversation-history/YYYY/MM/DD/timestamp/filename"""
        
        # Extract timestamp from conversation
        if hasattr(conversation, 'start_timestamp'):
            timestamp = conversation.start_timestamp
        elif isinstance(conversation, dict) and 'start_timestamp' in conversation:
            timestamp = conversation['start_timestamp']
        else:
            # Fallback to current timestamp
            timestamp = datetime.utcnow().isoformat()
        
        # Parse timestamp to get date components
        date_str = timestamp[:10]  # YYYY-MM-DD
        year, month, day = date_str.split('-')
        
        # Use full timestamp as directory name (clean it for filesystem)
        # Convert from "2025-07-31T08:00:17.939954+00:00" to "2025-07-31T08-00-17"
        timestamp_dir = timestamp.replace(':', '-').split('.')[0]  # Remove microseconds and timezone
        if '+' in timestamp_dir:
            timestamp_dir = timestamp_dir.split('+')[0]  # Remove timezone
        
        return f"{self.prefix}{year}/{month}/{day}/{timestamp_dir}/{filename}"
    
    def _to_structured_json(self, conversation) -> str:
        """Convert to structured JSON format - complete data preservation"""
        
        # Safe access to conversation attributes
        prompt_references = getattr(conversation, 'prompt_references', conversation.get('prompt_references', {}) if isinstance(conversation, dict) else {})
        system_prompts = getattr(conversation, 'system_prompts', conversation.get('system_prompts', {}) if isinstance(conversation, dict) else {})
        
        structured_data = {
            "export_metadata": {
                "format": "structured_json",
                "version": "1.0", 
                "exported_at": datetime.utcnow().isoformat(),
                "deduplication_applied": bool(prompt_references),
                "system_prompts_excluded": True,
                "note": "System prompts excluded from export for size optimization"
            },
            "prompt_references": prompt_references  # Only references, not full prompts
        }
        
        # Get conversation data safely
        if hasattr(conversation, 'to_analysis_json'):
            structured_data["conversation"] = conversation.to_analysis_json()
        elif hasattr(conversation, 'to_structured_json'):
            structured_data["conversation"] = conversation.to_structured_json(include_full_traces=True)
        elif isinstance(conversation, dict):
            structured_data["conversation"] = conversation
        else:
            # Convert object to dict as fallback
            structured_data["conversation"] = {
                "conversation_id": getattr(conversation, 'conversation_id', 'unknown'),
                "object_type": type(conversation).__name__,
                "export_note": "Object could not be serialized to structured format"
            }
        
        return json.dumps(structured_data, indent=2, default=str)
    
    def _to_llm_readable_text(self, conversation) -> str:
        """Convert to LLM-readable text format - optimized for AI consumption"""
        
        # Safe access to conversation attributes
        conv_id = getattr(conversation, 'conversation_id', conversation.get('conversation_id', 'unknown') if isinstance(conversation, dict) else 'unknown')
        start_time = getattr(conversation, 'start_timestamp', conversation.get('start_timestamp', 'unknown') if isinstance(conversation, dict) else 'unknown')
        duration = getattr(conversation, 'processing_time_ms', conversation.get('processing_time_ms', 0) if isinstance(conversation, dict) else 0)
        success = getattr(conversation, 'success', conversation.get('success', True) if isinstance(conversation, dict) else True)
        user_query = getattr(conversation, 'user_query', conversation.get('user_query', '') if isinstance(conversation, dict) else '')
        temporal_context = getattr(conversation, 'temporal_context', conversation.get('temporal_context', '') if isinstance(conversation, dict) else '')
        agent_flow = getattr(conversation, 'agent_flow', conversation.get('agent_flow', []) if isinstance(conversation, dict) else [])
        
        lines = [
            "# Conversation Analysis",
            f"**Conversation ID**: {conv_id}",
            f"**Date**: {start_time}",
            f"**Duration**: {duration}ms",
            f"**Success**: {success}",
            "",
            "## User Query",
            user_query,
            "",
            "## Temporal Context", 
            temporal_context,
            "",
            "## Agent Flow"
        ]
        
        for i, step in enumerate(agent_flow, 1):
            # Safe access to step attributes
            if isinstance(step, dict):
                step_name = step.get('agent_name', 'unknown')
                step_id = step.get('agent_id', 'unknown')
                end_time = step.get('end_time', 'unknown')
                start_time = step.get('start_time', 'unknown')
                reasoning = step.get('reasoning_text', '')
                tools_used = step.get('tools_used', [])
                data_operations = step.get('data_operations', [])
            else:
                step_name = getattr(step, 'agent_name', 'unknown')
                step_id = getattr(step, 'agent_id', 'unknown')
                end_time = getattr(step, 'end_time', 'unknown')
                start_time = getattr(step, 'start_time', 'unknown')
                reasoning = getattr(step, 'reasoning_text', '')
                tools_used = getattr(step, 'tools_used', [])
                data_operations = getattr(step, 'data_operations', [])
            
            lines.extend([
                f"### Step {i}: {step_name} ({step_id})",
                f"**Duration**: {end_time} - {start_time}",
                "",
                "**Agent Reasoning**:",
                reasoning,
                ""
            ])
            
            if tools_used:
                lines.append("**Tools Used**:")
                for tool in tools_used:
                    if isinstance(tool, dict):
                        tool_name = tool.get('tool_name', 'unknown')
                        result_summary = tool.get('result_summary', '')
                    else:
                        tool_name = getattr(tool, 'tool_name', 'unknown')
                        result_summary = getattr(tool, 'result_summary', '')
                    lines.append(f"- {tool_name}: {result_summary}")
                lines.append("")
                
            if data_operations:
                lines.append("**Data Operations**:")
                for op in data_operations:
                    if isinstance(op, dict):
                        operation = op.get('operation', 'unknown')
                        target = op.get('target', 'unknown')
                        result_count = op.get('result_count', 0)
                    else:
                        operation = getattr(op, 'operation', 'unknown')
                        target = getattr(op, 'target', 'unknown')
                        result_count = getattr(op, 'result_count', 0)
                    lines.append(f"- {operation} on {target}: {result_count} results")
                lines.append("")
        
        # Safe access to final attributes
        final_response = getattr(conversation, 'final_response', conversation.get('final_response', '') if isinstance(conversation, dict) else '')
        agents_involved = getattr(conversation, 'agents_involved', conversation.get('agents_involved', []) if isinstance(conversation, dict) else [])
        collaboration_map = getattr(conversation, 'collaboration_map', conversation.get('collaboration_map', {}) if isinstance(conversation, dict) else {})
        
        lines.extend([
            "## Final Response",
            final_response,
            "",
            "## Collaboration Summary",
            f"Agents involved: {', '.join(agents_involved)}",
            json.dumps(collaboration_map, indent=2)
        ])
        
        return "\n".join(lines)
    
    def _to_analysis_format(self, conversation) -> str:
        """Convert to analysis-optimized format - metrics and patterns"""
        
        # Safe access to conversation attributes
        conv_id = getattr(conversation, 'conversation_id', conversation.get('conversation_id', 'unknown') if isinstance(conversation, dict) else 'unknown')
        duration = getattr(conversation, 'processing_time_ms', conversation.get('processing_time_ms', 0) if isinstance(conversation, dict) else 0)
        success = getattr(conversation, 'success', conversation.get('success', True) if isinstance(conversation, dict) else True)
        agents_involved = getattr(conversation, 'agents_involved', conversation.get('agents_involved', []) if isinstance(conversation, dict) else [])
        agent_flow = getattr(conversation, 'agent_flow', conversation.get('agent_flow', []) if isinstance(conversation, dict) else [])
        user_query = getattr(conversation, 'user_query', conversation.get('user_query', '') if isinstance(conversation, dict) else '')
        
        analysis_data = {
            "conversation_metrics": {
                "id": conv_id,
                "duration_ms": duration,
                "success": success,
                "agent_count": len(agents_involved),
                "step_count": len(agent_flow),
                "tool_usage_count": sum(len(step.get('tools_used', []) if isinstance(step, dict) else getattr(step, 'tools_used', [])) for step in agent_flow),
                "data_operations_count": sum(len(step.get('data_operations', []) if isinstance(step, dict) else getattr(step, 'data_operations', [])) for step in agent_flow)
            },
            "agent_performance": [
                {
                    "agent_name": step.get('agent_name', 'unknown') if isinstance(step, dict) else getattr(step, 'agent_name', 'unknown'),
                    "agent_id": step.get('agent_id', 'unknown') if isinstance(step, dict) else getattr(step, 'agent_id', 'unknown'),
                    "step_duration_ms": self._calculate_step_duration(step),
                    "tools_used": len(step.get('tools_used', []) if isinstance(step, dict) else getattr(step, 'tools_used', [])),
                    "data_operations": len(step.get('data_operations', []) if isinstance(step, dict) else getattr(step, 'data_operations', [])),
                    "reasoning_length": len(step.get('reasoning_text', '') if isinstance(step, dict) else getattr(step, 'reasoning_text', ''))
                }
                for step in agent_flow
            ],
            "patterns": {
                "query_type": self._classify_query_type(user_query),
                "routing_pattern": self._analyze_routing_pattern(agent_flow),
                "data_access_pattern": self._analyze_data_access(agent_flow)
            }
        }
        
        # Add raw conversation data safely  
        if hasattr(conversation, 'to_structured_json'):
            analysis_data["raw_conversation"] = conversation.to_structured_json()
        elif isinstance(conversation, dict):
            analysis_data["raw_conversation"] = conversation
        else:
            analysis_data["raw_conversation"] = {"note": "Could not serialize conversation object"}
        
        return json.dumps(analysis_data, indent=2, default=str)
    
    def _to_metadata_only(self, conversation) -> str:
        """Convert to metadata-only format - lightweight summary"""
        
        # Safe access to conversation attributes
        conv_id = getattr(conversation, 'conversation_id', conversation.get('conversation_id', 'unknown') if isinstance(conversation, dict) else 'unknown')
        session_id = getattr(conversation, 'session_id', conversation.get('session_id', 'unknown') if isinstance(conversation, dict) else 'unknown')
        user_id = getattr(conversation, 'user_id', conversation.get('user_id', 'unknown') if isinstance(conversation, dict) else 'unknown')
        channel = getattr(conversation, 'channel', conversation.get('channel', 'unknown') if isinstance(conversation, dict) else 'unknown')
        start_timestamp = getattr(conversation, 'start_timestamp', conversation.get('start_timestamp', 'unknown') if isinstance(conversation, dict) else 'unknown')
        end_timestamp = getattr(conversation, 'end_timestamp', conversation.get('end_timestamp', 'unknown') if isinstance(conversation, dict) else 'unknown')
        processing_time_ms = getattr(conversation, 'processing_time_ms', conversation.get('processing_time_ms', 0) if isinstance(conversation, dict) else 0)
        user_query = getattr(conversation, 'user_query', conversation.get('user_query', '') if isinstance(conversation, dict) else '')
        final_response = getattr(conversation, 'final_response', conversation.get('final_response', '') if isinstance(conversation, dict) else '')
        agents_involved = getattr(conversation, 'agents_involved', conversation.get('agents_involved', []) if isinstance(conversation, dict) else [])
        agent_flow = getattr(conversation, 'agent_flow', conversation.get('agent_flow', []) if isinstance(conversation, dict) else [])
        success = getattr(conversation, 'success', conversation.get('success', True) if isinstance(conversation, dict) else True)
        error_details = getattr(conversation, 'error_details', conversation.get('error_details', None) if isinstance(conversation, dict) else None)
        
        metadata = {
            "conversation_id": conv_id,
            "session_id": session_id,
            "user_id": user_id,
            "channel": channel,
            "timestamps": {
                "start": start_timestamp,
                "end": end_timestamp,
                "duration_ms": processing_time_ms
            },
            "summary": {
                "query_length": len(user_query),
                "response_length": len(final_response),
                "agents_involved": agents_involved,
                "step_count": len(agent_flow),
                "success": success,
                "has_errors": bool(error_details)
            },
            "performance": {
                "tool_calls": sum(len(step.get('tools_used', []) if isinstance(step, dict) else getattr(step, 'tools_used', [])) for step in agent_flow),
                "data_operations": sum(len(step.get('data_operations', []) if isinstance(step, dict) else getattr(step, 'data_operations', [])) for step in agent_flow),
                "total_reasoning_length": sum(len(step.get('reasoning_text', '') if isinstance(step, dict) else getattr(step, 'reasoning_text', '')) for step in agent_flow)
            }
        }
        
        return json.dumps(metadata, indent=2, default=str)
    
    def _to_agent_traces(self, conversation) -> str:
        """Convert to agent traces format - debugging and analysis"""
        
        # Safe access to conversation attributes
        conv_id = getattr(conversation, 'conversation_id', conversation.get('conversation_id', 'unknown') if isinstance(conversation, dict) else 'unknown')
        agent_flow = getattr(conversation, 'agent_flow', conversation.get('agent_flow', []) if isinstance(conversation, dict) else [])
        
        traces_data = {
            "conversation_id": conv_id,
            "total_steps": len(agent_flow),
            "agent_traces": []
        }
        
        for i, step in enumerate(agent_flow):
            # Safe access to step attributes
            if isinstance(step, dict):
                step_name = step.get('agent_name', 'unknown')
                step_id = step.get('agent_id', 'unknown')
                start_time = step.get('start_time', 'unknown')
                end_time = step.get('end_time', 'unknown')
                reasoning = step.get('reasoning_text', '')
                trace_content = step.get('bedrock_trace_content', {})
                tools_used = step.get('tools_used', [])
                data_operations = step.get('data_operations', [])
            else:
                step_name = getattr(step, 'agent_name', 'unknown')
                step_id = getattr(step, 'agent_id', 'unknown')
                start_time = getattr(step, 'start_time', 'unknown')
                end_time = getattr(step, 'end_time', 'unknown')
                reasoning = getattr(step, 'reasoning_text', '')
                trace_content = getattr(step, 'bedrock_trace_content', {})
                tools_used = getattr(step, 'tools_used', [])
                data_operations = getattr(step, 'data_operations', [])
            
            # Safe access to trace content
            if isinstance(trace_content, dict):
                model_input = trace_content.get('modelInvocationInput', '')
                observation = trace_content.get('observation', '')
                raw_trace_data = trace_content.get('raw_trace_data', {})
            else:
                model_input = getattr(trace_content, 'modelInvocationInput', '') if trace_content else ''
                observation = getattr(trace_content, 'observation', '') if trace_content else ''
                raw_trace_data = getattr(trace_content, 'raw_trace_data', {}) if trace_content else {}
            
            trace_info = {
                "step_number": i + 1,
                "agent_name": step_name,
                "agent_id": step_id,
                "timing": {
                    "start": start_time,
                    "end": end_time,
                    "duration_ms": self._calculate_step_duration(step)
                },
                "reasoning_text": reasoning,
                "trace_content": {
                    "has_model_input": bool(model_input),
                    "model_input_length": len(model_input or ""),
                    "has_observation": bool(observation),
                    "observation": observation,
                    "raw_trace_keys": list(raw_trace_data.keys()) if raw_trace_data else []
                },
                "tools": [
                    {
                        "tool_name": tool.get('tool_name', 'unknown') if isinstance(tool, dict) else getattr(tool, 'tool_name', 'unknown'),
                        "execution_time_ms": tool.get('execution_time_ms', 0) if isinstance(tool, dict) else getattr(tool, 'execution_time_ms', 0),
                        "success": tool.get('success', True) if isinstance(tool, dict) else getattr(tool, 'success', True),
                        "result_summary": tool.get('result_summary', '') if isinstance(tool, dict) else getattr(tool, 'result_summary', '')
                    }
                    for tool in tools_used
                ],
                "data_operations": [
                    {
                        "operation": op.get('operation', 'unknown') if isinstance(op, dict) else getattr(op, 'operation', 'unknown'),
                        "target": op.get('target', 'unknown') if isinstance(op, dict) else getattr(op, 'target', 'unknown'),
                        "execution_time_ms": op.get('execution_time_ms', 0) if isinstance(op, dict) else getattr(op, 'execution_time_ms', 0),
                        "result_count": op.get('result_count', 0) if isinstance(op, dict) else getattr(op, 'result_count', 0)
                    }
                    for op in data_operations
                ]
            }
            
            traces_data["agent_traces"].append(trace_info)
        
        return json.dumps(traces_data, indent=2, default=str)
    
    def _calculate_step_duration(self, step) -> int:
        """Calculate step duration in milliseconds"""
        try:
            from datetime import datetime
            # Safe access to timing attributes
            if isinstance(step, dict):
                start_time = step.get('start_time', '')
                end_time = step.get('end_time', '')
            else:
                start_time = getattr(step, 'start_time', '')
                end_time = getattr(step, 'end_time', '')
            
            if not start_time or not end_time:
                return 0
                
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return int((end - start).total_seconds() * 1000)
        except:
            return 0
    
    def _classify_query_type(self, user_query: str) -> str:
        """Classify the type of user query"""
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ['deal', 'opportunity', 'prospect']):
            return 'deal_analysis'
        elif any(word in query_lower for word in ['lead', 'contact', 'person']):
            return 'lead_analysis'
        elif any(word in query_lower for word in ['data', 'query', 'sql', 'table']):
            return 'data_query'
        elif any(word in query_lower for word in ['trend', 'analysis', 'report']):
            return 'analytics'
        else:
            return 'general'
    
    def _analyze_routing_pattern(self, agent_flow) -> str:
        """Analyze the routing pattern used"""
        if len(agent_flow) == 1:
            return 'direct'
        elif len(agent_flow) == 2:
            return 'simple_routing'
        elif len(agent_flow) > 5:
            return 'complex_multi_agent'
        else:
            return 'standard_routing'
    
    def _analyze_data_access(self, agent_flow) -> str:
        """Analyze data access patterns"""
        total_data_ops = sum(len(step.get('data_operations', []) if isinstance(step, dict) else getattr(step, 'data_operations', [])) for step in agent_flow)
        
        if total_data_ops == 0:
            return 'no_data_access'
        elif total_data_ops <= 2:
            return 'light_data_access'
        elif total_data_ops <= 5:
            return 'moderate_data_access'
        else:
            return 'heavy_data_access'
    
    def _to_enhanced_structured_json(self, conversation) -> str:
        """Convert to enhanced structured JSON format - LLM-optimized with parsed reasoning"""
        
        try:
            # Prepare conversation data for transformation
            if hasattr(conversation, 'to_structured_json'):
                conversation_data = {
                    "export_metadata": {
                        "format": "structured_json",
                        "version": "1.0",
                        "exported_at": datetime.utcnow().isoformat(),
                        "deduplication_applied": bool(getattr(conversation, 'prompt_references', {})),
                        "system_prompts_excluded": True
                    },
                    "conversation": conversation.to_structured_json(include_full_traces=True)
                }
            elif isinstance(conversation, dict):
                conversation_data = conversation
            else:
                # Convert object to dict as fallback
                conversation_data = {
                    "conversation": {
                        "conversation_id": getattr(conversation, 'conversation_id', 'unknown'),
                        "start_timestamp": getattr(conversation, 'start_timestamp', ''),
                        "end_timestamp": getattr(conversation, 'end_timestamp', ''),
                        "user_query": getattr(conversation, 'user_query', ''),
                        "final_response": getattr(conversation, 'final_response', ''),
                        "success": getattr(conversation, 'success', True),
                        "processing_time_ms": getattr(conversation, 'processing_time_ms', 0),
                        "agent_flow": getattr(conversation, 'agent_flow', []),
                        "agents_involved": getattr(conversation, 'agents_involved', []),
                        "collaboration_map": getattr(conversation, 'collaboration_map', {}),
                        "function_audit": getattr(conversation, 'function_audit', {}),
                        "error_details": getattr(conversation, 'error_details', None)
                    }
                }
            
            # CRITICAL: Enhanced system prompt filtering with aggressive detection (safe copy)
            conversation_data_copy = self._deep_copy_with_safety(conversation_data)
            conversation_data_filtered = self._aggressively_filter_system_prompts(conversation_data_copy)
            
            # ENHANCED: Advanced agent handover detection (safe copy)
            conversation_data_enhanced = self._detect_and_parse_agent_handovers(conversation_data_filtered)
            
            # Transform to enhanced structure with better parsing
            enhanced_data = self.transformer.transform_to_enhanced_structure(conversation_data_enhanced)
            
            # ENHANCED: Comprehensive validation and quality assessment
            validation = self.transformer.validate_enhanced_structure(enhanced_data)
            
            # ENHANCED: Add comprehensive validation info to metadata
            enhanced_data["export_metadata"]["validation"] = {
                "valid": validation["valid"],
                "warnings": validation.get("warnings", []),
                "statistics": validation.get("statistics", {}),
                "quality_assessment": validation.get("quality_assessment", {})
            }
            
            # ENHANCED: Add export quality metrics
            export_quality = self._assess_export_quality(enhanced_data, validation)
            enhanced_data["export_metadata"]["export_quality"] = export_quality
            
            if not validation["valid"]:
                enhanced_data["export_metadata"]["validation"]["errors"] = validation["errors"]
                self.logger.error(f"Enhanced structure validation failed: {validation['errors']}")
            
            # ENHANCED: Log quality assessment
            overall_score = validation.get("quality_assessment", {}).get("overall_score", 0.0)
            if overall_score < 0.5:
                self.logger.warning(f"Export quality below threshold: {overall_score:.2f}")
            else:
                self.logger.info(f"Export quality assessment: {overall_score:.2f}")
            
            # ENHANCED: Safe JSON serialization with proper error handling
            return self._safe_json_dumps(enhanced_data)
            
        except Exception as e:
            self.logger.error(f"Error creating enhanced structured JSON: {e}")
            
            # Return fallback structure
            fallback_data = {
                "export_metadata": {
                    "format": "enhanced_structured_json",
                    "version": "2.0",
                    "exported_at": datetime.utcnow().isoformat(),
                    "transformation_error": str(e),
                    "note": "Transformation failed, using fallback structure"
                },
                "conversation": {
                    "conversation_id": getattr(conversation, 'conversation_id', conversation.get('conversation_id', 'unknown') if isinstance(conversation, dict) else 'unknown'),
                    "error": "Enhanced transformation failed",
                    "original_data_preserved": False
                }
            }
            
            return self._safe_json_dumps(fallback_data)
    
    def _filter_system_prompts_from_conversation_data(self, conversation_data: Dict) -> Dict:
        """Filter system prompts from all parts of conversation data"""
        
        if not conversation_data:
            return conversation_data
        
        filtered_data = {}
        system_prompts_filtered = 0
        
        for key, value in conversation_data.items():
            if key == "conversation" and isinstance(value, dict):
                # Filter conversation content
                filtered_conversation = {}
                
                for conv_key, conv_value in value.items():
                    if conv_key == "agent_flow" and isinstance(conv_value, list):
                        # Filter agent flow for system prompts
                        filtered_agent_flow = []
                        for step in conv_value:
                            filtered_step = self._filter_system_prompts_from_agent_step(step)
                            if filtered_step:  # Only include non-empty steps
                                filtered_agent_flow.append(filtered_step)
                        filtered_conversation[conv_key] = filtered_agent_flow
                    
                    elif conv_key in ["bedrock_trace_content", "trace_content"] and conv_value:
                        # Filter Bedrock trace content
                        filtered_trace, had_prompts = self._filter_system_prompts_from_trace_content(conv_value)
                        if had_prompts:
                            system_prompts_filtered += 1
                        filtered_conversation[conv_key] = filtered_trace
                    
                    else:
                        # Keep other conversation fields as-is
                        filtered_conversation[conv_key] = conv_value
                
                filtered_data[key] = filtered_conversation
                
            else:
                # Keep other top-level fields as-is
                filtered_data[key] = value
        
        # Update metadata to reflect actual filtering
        if "export_metadata" in filtered_data:
            filtered_data["export_metadata"]["system_prompts_filtered"] = system_prompts_filtered
            filtered_data["export_metadata"]["system_prompts_excluded"] = True
        
        self.logger.info(f"Filtered {system_prompts_filtered} system prompts from conversation data")
        return filtered_data
    
    def _filter_system_prompts_from_agent_step(self, step) -> Optional[Dict]:
        """Filter system prompts from individual agent step"""
        
        if not step:
            return step
        
        if isinstance(step, dict):
            filtered_step = {}
            
            for key, value in step.items():
                # Filter specific fields that may contain system prompts
                if key == "bedrock_trace_content" and value:
                    filtered_trace, _ = self._filter_system_prompts_from_trace_content(value)
                    filtered_step[key] = filtered_trace
                    
                elif key == "reasoning_text" and isinstance(value, str):
                    # Check if reasoning text is actually a system prompt
                    if not self.prompt_deduplicator._is_system_prompt_content(value):
                        filtered_step[key] = value
                    else:
                        self.logger.info(f"Filtered system prompt from reasoning_text (size: {len(value)})")
                        
                elif key in ["messages", "message_content"] and value:
                    # Filter messages content
                    filtered_messages, had_system = self.prompt_deduplicator.filter_system_prompts_from_messages(value)
                    if filtered_messages:
                        filtered_step[key] = filtered_messages
                
                else:
                    # Keep other fields
                    filtered_step[key] = value
            
            return filtered_step if filtered_step else None
        
        return step
    
    def _filter_system_prompts_from_trace_content(self, trace_content) -> Tuple[any, bool]:
        """Filter system prompts from Bedrock trace content"""
        
        if not trace_content:
            return trace_content, False
        
        system_prompts_found = False
        
        # Handle different trace content formats
        if isinstance(trace_content, dict):
            filtered_trace = {}
            
            for key, value in trace_content.items():
                if key == "messages" and value:
                    # Filter messages in trace content
                    filtered_messages, had_system = self.prompt_deduplicator.filter_system_prompts_from_messages(value)
                    system_prompts_found = system_prompts_found or had_system
                    if filtered_messages:
                        filtered_trace[key] = filtered_messages
                
                elif key == "modelInvocationInput" and isinstance(value, str):
                    # Check if model input contains system prompts
                    try:
                        input_data = json.loads(value)
                        if "system" in input_data and self.prompt_deduplicator._is_system_prompt_content(input_data["system"]):
                            # Remove system prompt, keep rest
                            del input_data["system"]
                            system_prompts_found = True
                            self.logger.info("Filtered system prompt from modelInvocationInput")
                            if input_data:  # If there's still content
                                filtered_trace[key] = json.dumps(input_data)
                        else:
                            filtered_trace[key] = value
                    except json.JSONDecodeError:
                        # Not JSON, keep as-is
                        filtered_trace[key] = value
                
                else:
                    # Keep other trace fields
                    filtered_trace[key] = value
            
            return filtered_trace, system_prompts_found
        
        return trace_content, False
    
    def _assess_export_quality(self, enhanced_data: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the overall quality of the enhanced export"""
        
        quality_assessment = {
            "overall_score": 0.0,
            "data_completeness_score": 0.0,
            "agent_attribution_score": 0.0,
            "tool_execution_score": 0.0,
            "system_prompt_filtering_score": 0.0,
            "issues_found": [],
            "recommendations": []
        }
        
        try:
            # Get quality scores from validation
            validation_quality = validation.get("quality_assessment", {})
            quality_assessment.update(validation_quality)
            
            # Assess system prompt filtering quality
            export_metadata = enhanced_data.get("export_metadata", {})
            if export_metadata.get("system_prompts_excluded", False):
                quality_assessment["system_prompt_filtering_score"] = 1.0
            else:
                quality_assessment["issues_found"].append("System prompts may not have been properly filtered")
                quality_assessment["recommendations"].append("Enable system prompt filtering to reduce export size")
            
            # Assess conversation structure quality
            conversation = enhanced_data.get("conversation", {})
            
            # Check for agent flow quality
            agent_flow = conversation.get("agent_flow", [])
            if not agent_flow:
                quality_assessment["issues_found"].append("No agent flow data found")
                quality_assessment["recommendations"].append("Verify conversation data collection is working properly")
            else:
                # Check for unknown agents
                unknown_agents = sum(1 for step in agent_flow if step.get("agent_name") == "unknown")
                if unknown_agents > 0:
                    quality_assessment["issues_found"].append(f"{unknown_agents} steps have unknown agent attribution")
                    quality_assessment["recommendations"].append("Improve agent attribution parsing from Bedrock traces")
            
            # Check conversation summary quality
            summary = conversation.get("conversation_summary", {})
            if "data_quality_metrics" in summary:
                data_quality = summary["data_quality_metrics"]
                success_rate = data_quality.get("tool_execution_success_rate", 0)
                if success_rate < 0.8:
                    quality_assessment["issues_found"].append(f"Tool execution success rate is low: {success_rate:.2f}")
                    quality_assessment["recommendations"].append("Investigate tool execution failures and improve error handling")
            
            # Check for enhanced parsing usage
            enhanced_parsing_used = False
            for step in agent_flow:
                if step.get("parsed_messages") or step.get("trace_tool_executions"):
                    enhanced_parsing_used = True
                    break
            
            if not enhanced_parsing_used:
                quality_assessment["issues_found"].append("Enhanced parsing features not utilized")
                quality_assessment["recommendations"].append("Verify MessageParser and enhanced ReasoningParser are working")
            
            # Calculate final scores
            scores = [
                quality_assessment.get("data_completeness", 0.0),
                quality_assessment.get("agent_attribution_quality", 0.0),
                quality_assessment.get("tool_execution_quality", 0.0),
                quality_assessment.get("reasoning_quality", 0.0),
                quality_assessment.get("system_prompt_filtering_score", 0.0)
            ]
            
            quality_assessment["overall_score"] = sum(scores) / len(scores)
            
            # Generate overall recommendations
            if quality_assessment["overall_score"] < 0.3:
                quality_assessment["recommendations"].append("Consider investigating conversation data collection pipeline")
            elif quality_assessment["overall_score"] < 0.6:
                quality_assessment["recommendations"].append("Review parser configurations and improve data extraction")
            elif quality_assessment["overall_score"] >= 0.8:
                quality_assessment["recommendations"].append("Export quality is excellent - maintain current configuration")
        
        except Exception as e:
            self.logger.error(f"Error assessing export quality: {e}")
            quality_assessment["assessment_error"] = str(e)
        
        return quality_assessment
    
    def _aggressively_filter_system_prompts(self, conversation_data: Dict) -> Dict:
        """Aggressively filter system prompts with enhanced detection for large instruction blocks"""
        
        if not conversation_data:
            return conversation_data
        
        filtered_data = {}
        total_prompts_filtered = 0
        bytes_saved = 0
        
        for key, value in conversation_data.items():
            if key == "conversation" and isinstance(value, dict):
                filtered_conversation = {}
                
                for conv_key, conv_value in value.items():
                    if conv_key == "agent_flow" and isinstance(conv_value, list):
                        # Enhanced agent flow filtering
                        filtered_agent_flow = []
                        for step in conv_value:
                            filtered_step = self._aggressively_filter_agent_step(step)
                            if filtered_step:
                                filtered_agent_flow.append(filtered_step)
                        filtered_conversation[conv_key] = filtered_agent_flow
                    
                    elif conv_key in ["bedrock_trace_content", "trace_content"] and conv_value:
                        # Enhanced trace content filtering
                        filtered_trace, prompts_removed, bytes_removed = self._aggressively_filter_trace_content(conv_value)
                        total_prompts_filtered += prompts_removed
                        bytes_saved += bytes_removed
                        filtered_conversation[conv_key] = filtered_trace
                    
                    else:
                        filtered_conversation[conv_key] = conv_value
                
                filtered_data[key] = filtered_conversation
            else:
                filtered_data[key] = value
        
        # Update metadata with filtering statistics
        if "export_metadata" in filtered_data:
            filtered_data["export_metadata"]["aggressive_filtering"] = {
                "system_prompts_filtered": total_prompts_filtered,
                "bytes_saved": bytes_saved,
                "filtering_method": "aggressive_detection"
            }
        
        self.logger.info(f"Aggressively filtered {total_prompts_filtered} system prompts, saved {bytes_saved} bytes")
        return filtered_data
    
    def _aggressively_filter_agent_step(self, step) -> Optional[Dict]:
        """Aggressively filter system prompts from agent step with enhanced detection"""
        
        if not step:
            return step
        
        if isinstance(step, dict):
            filtered_step = {}
            
            for key, value in step.items():
                # Enhanced reasoning text filtering
                if key == "reasoning_text" and isinstance(value, str):
                    if self._is_massive_system_prompt(value):
                        self.logger.info(f"Filtered massive system prompt from reasoning_text (size: {len(value)})")
                        # Replace with summary
                        filtered_step[key] = "[SYSTEM PROMPT FILTERED - Original size: {} characters]".format(len(value))
                    else:
                        filtered_step[key] = value
                
                # Enhanced bedrock trace content filtering
                elif key == "bedrock_trace_content" and value:
                    filtered_trace, _, _ = self._aggressively_filter_trace_content(value)
                    filtered_step[key] = filtered_trace
                
                # Enhanced messages filtering
                elif key in ["messages", "message_content"] and value:
                    filtered_messages, _ = self._aggressively_filter_messages(value)
                    if filtered_messages:
                        filtered_step[key] = filtered_messages
                
                # ENHANCED: Tool execution filtering for embedded system prompts
                elif key == "tools_used" and isinstance(value, list):
                    filtered_tools = self._filter_tool_execution_prompts(value)
                    filtered_step[key] = filtered_tools
                
                # ENHANCED: Data operations filtering
                elif key == "data_operations" and isinstance(value, list):
                    filtered_ops = self._filter_data_operations_prompts(value) 
                    filtered_step[key] = filtered_ops
                
                else:
                    filtered_step[key] = value
            
            return filtered_step if filtered_step else None
        
        return step
    
    def _aggressively_filter_trace_content(self, trace_content) -> Tuple[any, int, int]:
        """Aggressively filter system prompts from Bedrock trace content"""
        
        if not trace_content:
            return trace_content, 0, 0
        
        prompts_removed = 0
        bytes_saved = 0
        
        if isinstance(trace_content, dict):
            filtered_trace = {}
            
            for key, value in trace_content.items():
                if key == "modelInvocationInput" and isinstance(value, str):
                    # Enhanced modelInvocationInput filtering
                    if self._is_massive_system_prompt(value):
                        # This is likely the massive system prompt we saw in logs
                        bytes_saved += len(value)
                        prompts_removed += 1
                        self.logger.info(f"Filtered massive modelInvocationInput (size: {len(value)})")
                        # Replace with minimal reference
                        filtered_trace[key] = '{"filtered": "system_prompt_removed", "original_size": ' + str(len(value)) + '}'
                    else:
                        # Try to parse and filter JSON content
                        filtered_input, prompt_found, bytes_removed = self._filter_json_system_prompts(value)
                        if prompt_found:
                            prompts_removed += 1
                            bytes_saved += bytes_removed
                        filtered_trace[key] = filtered_input
                
                elif key == "messages" and value:
                    # Enhanced messages filtering
                    filtered_messages, had_system = self._aggressively_filter_messages(value)
                    if had_system:
                        prompts_removed += 1
                    if filtered_messages:
                        filtered_trace[key] = filtered_messages
                
                else:
                    filtered_trace[key] = value
            
            return filtered_trace, prompts_removed, bytes_saved
        
        return trace_content, prompts_removed, bytes_saved
    
    def _aggressively_filter_messages(self, messages_data) -> Tuple[any, bool]:
        """Aggressively filter system prompts from messages with enhanced detection"""
        
        if not messages_data:
            return messages_data, False
        
        system_prompts_found = False
        
        if isinstance(messages_data, list):
            filtered_messages = []
            for message in messages_data:
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                    if self._is_massive_system_prompt(str(content)):
                        system_prompts_found = True
                        self.logger.info(f"Filtered system prompt message (size: {len(str(content))})")
                        # Skip this message entirely or replace with reference
                        continue
                    else:
                        filtered_messages.append(message)
                else:
                    filtered_messages.append(message)
            return filtered_messages, system_prompts_found
        
        elif isinstance(messages_data, dict):
            if "content" in messages_data:
                content = messages_data["content"]
                if self._is_massive_system_prompt(str(content)):
                    self.logger.info(f"Filtered system prompt from single message (size: {len(str(content))})")
                    return None, True
            return messages_data, False
        
        return messages_data, False
    
    def _is_massive_system_prompt(self, content: str) -> bool:
        """Enhanced detection for massive system prompts like the Data Analysis Agent instructions"""
        
        if not content or len(content) < 500:
            return False
        
        # ENHANCED: Data Analysis Agent specific indicators (more comprehensive)
        data_agent_indicators = [
            "# Data Analysis Agent Instructions",
            "## Agent Purpose", 
            "You are the Data Analysis Agent for Firebolt",
            "You are a specialized Data Analysis Agent",
            "## Core Capabilities",
            "## CRITICAL: Temporal Context Awareness",
            "**ALWAYS REMEMBER THE CURRENT DATE AND TIME CONTEXT**",
            "## Business Context and Customer Segmentation", 
            "### Customer Type Classification in SQL",
            "**CRITICAL**: Always segment analysis by customer type",
            "### Required Analysis Patterns",
            "### SQL Query Patterns for Temporal Analysis",
            "### Customer Lifecycle Analysis",
            "## Best Practices",
            "## Function Calling",
            "### Firebolt SQL Query", 
            "### Gong Data Analysis",
            "### Regional Analysis",
            "### Lead Analysis",
            "### Owner and User Name Resolution",
            "## Temporal Analysis Guidelines"
        ]
        
        # ENHANCED: Lower threshold for faster detection
        indicator_count = sum(1 for indicator in data_agent_indicators if indicator in content)
        
        # AGGRESSIVE: If it has multiple indicators and is moderately large, it's a system prompt
        if indicator_count >= 2 and len(content) > 10000:
            return True
            
        # AGGRESSIVE: If it has even one key indicator and is very large, it's a system prompt  
        if indicator_count >= 1 and len(content) > 30000:
            return True
        
        # AGGRESSIVE: Size-based detection for very large content (lowered threshold)
        if len(content) > 40000:
            return True
        
        # ENHANCED: More comprehensive system prompt patterns
        system_patterns = [
            r"You are the .* Agent",
            r"You are a specialized .* Agent", 
            r"## Agent Purpose",
            r"## Core Capabilities", 
            r"### Required .* Format",
            r"CRITICAL.*:",
            r"ALWAYS.*:",
            r"NEVER.*:",
            r"### Customer Type Classification",
            r"## Function Calling",
            r"### Firebolt SQL Query",
            r"## Temporal Analysis Guidelines",
            r"### Owner and User Name Resolution",
            r"## Business Context"
        ]
        
        import re
        pattern_matches = sum(1 for pattern in system_patterns if re.search(pattern, content, re.IGNORECASE))
        
        # AGGRESSIVE: Lower thresholds for pattern-based detection
        if len(content) > 5000 and pattern_matches >= 3:
            return True
        elif len(content) > 15000 and pattern_matches >= 2:
            return True
        elif len(content) > 25000 and pattern_matches >= 1:
            return True
        
        return False
    
    def _filter_tool_execution_prompts(self, tools_used: List) -> List:
        """Filter system prompts from tool execution parameters and results"""
        
        filtered_tools = []
        
        for tool in tools_used:
            if isinstance(tool, dict):
                filtered_tool = {}
                
                for key, value in tool.items():
                    if key == "parameters" and isinstance(value, str):
                        # Check if parameters contain system prompts
                        if self._is_massive_system_prompt(value):
                            filtered_tool[key] = f"[SYSTEM PROMPT FILTERED - {len(value)} chars]"
                        else:
                            filtered_tool[key] = value
                    elif key == "result" and isinstance(value, str):
                        # Check if result contains system prompts
                        if self._is_massive_system_prompt(value):
                            filtered_tool[key] = f"[SYSTEM PROMPT FILTERED - {len(value)} chars]"
                        else:
                            filtered_tool[key] = value
                    elif key == "parameters_summary" and isinstance(value, str):
                        # Check parameter summaries for embedded prompts
                        if self._is_massive_system_prompt(value):
                            filtered_tool[key] = f"[SYSTEM PROMPT FILTERED - {len(value)} chars]"
                        else:
                            filtered_tool[key] = value
                    else:
                        filtered_tool[key] = value
                
                filtered_tools.append(filtered_tool)
            else:
                # Handle non-dict tools (objects)
                filtered_tools.append(tool)
        
        return filtered_tools
    
    def _filter_data_operations_prompts(self, data_operations: List) -> List:
        """Filter system prompts from data operation details"""
        
        filtered_ops = []
        
        for op in data_operations:
            if isinstance(op, dict):
                filtered_op = {}
                
                for key, value in op.items():
                    if key in ["query", "query_summary", "result_summary"] and isinstance(value, str):
                        if self._is_massive_system_prompt(value):
                            filtered_op[key] = f"[SYSTEM PROMPT FILTERED - {len(value)} chars]"
                        else:
                            filtered_op[key] = value
                    else:
                        filtered_op[key] = value
                
                filtered_ops.append(filtered_op)
            else:
                filtered_ops.append(op)
        
        return filtered_ops
    
    def _filter_json_system_prompts(self, json_content: str) -> Tuple[str, bool, int]:
        """Filter system prompts from JSON content"""
        
        try:
            data = json.loads(json_content)
            original_size = len(json_content)
            prompt_found = False
            
            if isinstance(data, dict):
                if "system" in data:
                    system_content = data["system"]
                    if self._is_massive_system_prompt(str(system_content)):
                        # Remove the system prompt
                        del data["system"]
                        prompt_found = True
                        self.logger.info("Filtered system prompt from JSON content")
                
                # Check messages array for system prompts
                if "messages" in data and isinstance(data["messages"], list):
                    filtered_messages = []
                    for msg in data["messages"]:
                        if isinstance(msg, dict) and msg.get("role") == "system":
                            if self._is_massive_system_prompt(str(msg.get("content", ""))):
                                prompt_found = True
                                continue  # Skip system message
                        filtered_messages.append(msg)
                    data["messages"] = filtered_messages
            
            filtered_json = json.dumps(data)
            bytes_saved = original_size - len(filtered_json) if prompt_found else 0
            
            return filtered_json, prompt_found, bytes_saved
            
        except json.JSONDecodeError:
            return json_content, False, 0
    
    def _detect_and_parse_agent_handovers(self, conversation_data: Dict) -> Dict:
        """Enhanced agent handover detection from Bedrock traces"""
        
        if not conversation_data or "conversation" not in conversation_data:
            return conversation_data
        
        conversation = conversation_data["conversation"]
        agent_flow = conversation.get("agent_flow", [])
        
        enhanced_agent_flow = []
        detected_handovers = []
        
        for i, step in enumerate(agent_flow):
            enhanced_step = step.copy() if isinstance(step, dict) else step
            
            # Enhanced agent detection from multiple sources
            detected_agent = self._detect_actual_agent_from_step(step)
            
            if detected_agent and detected_agent != step.get("agent_name", "unknown"):
                # Found an agent handover!
                handover_info = {
                    "step_index": i,
                    "detected_agent": detected_agent,
                    "original_agent": step.get("agent_name", "unknown"),
                    "handover_evidence": self._extract_handover_evidence(step)
                }
                detected_handovers.append(handover_info)
                
                # Update the step with correct agent information
                if isinstance(enhanced_step, dict):
                    enhanced_step["agent_name"] = detected_agent
                    enhanced_step["agent_handover_detected"] = True
                    enhanced_step["original_agent_name"] = step.get("agent_name", "unknown")
                    enhanced_step["handover_evidence"] = handover_info["handover_evidence"]
            
            enhanced_agent_flow.append(enhanced_step)
        
        # Update conversation data
        conversation["agent_flow"] = enhanced_agent_flow
        if detected_handovers:
            conversation["detected_agent_handovers"] = detected_handovers
            conversation["agents_involved"] = list(set(
                conversation.get("agents_involved", []) + 
                [handover["detected_agent"] for handover in detected_handovers]
            ))
        
        self.logger.info(f"Detected {len(detected_handovers)} agent handovers")
        return conversation_data
    
    def _detect_actual_agent_from_step(self, step) -> Optional[str]:
        """Detect the actual agent from step content using multiple detection methods"""
        
        if not isinstance(step, dict):
            return None
        
        # Method 1: Check reasoning text for agent routing patterns
        reasoning_text = step.get("reasoning_text", "")
        if reasoning_text:
            agent_from_reasoning = self._extract_agent_from_reasoning(reasoning_text)
            if agent_from_reasoning:
                return agent_from_reasoning
        
        # Method 2: Check bedrock trace content
        trace_content = step.get("bedrock_trace_content", {})
        if trace_content:
            agent_from_trace = self._extract_agent_from_trace(trace_content)
            if agent_from_trace:
                return agent_from_trace
        
        # Method 3: Check tools used (certain tools indicate specific agents)
        tools_used = step.get("tools_used", [])
        if tools_used:
            agent_from_tools = self._infer_agent_from_tools(tools_used)
            if agent_from_tools:
                return agent_from_tools
        
        return None
    
    def _extract_agent_from_reasoning(self, reasoning_text: str) -> Optional[str]:
        """Extract agent name from reasoning text patterns"""
        
        agent_patterns = [
            r"Route to (\w+)\s*Agent",
            r"routing to (\w+)\s*Agent",
            r"calling (\w+)\s*Agent",
            r"AgentCommunication.*name=\"(\w+)\"",
            r"\"agent\":\s*\"(\w+)\"",
            r"collaborate with (\w+)\s*Agent"
        ]
        
        import re
        for pattern in agent_patterns:
            match = re.search(pattern, reasoning_text, re.IGNORECASE)
            if match:
                agent_name = match.group(1)
                # Map common agent names
                agent_mapping = {
                    "Data": "DataAgent", 
                    "Deal": "DealAnalysisAgent",
                    "Lead": "LeadAnalysisAgent",
                    "Web": "WebSearchAgent",
                    "Execution": "ExecutionAgent"
                }
                return agent_mapping.get(agent_name, agent_name + "Agent")
        
        return None
    
    def _extract_agent_from_trace(self, trace_content) -> Optional[str]:
        """Extract agent information from Bedrock trace content"""
        
        if isinstance(trace_content, dict):
            # Check modelInvocationInput for agent routing
            model_input = trace_content.get("modelInvocationInput", "")
            if model_input:
                try:
                    if isinstance(model_input, str):
                        input_data = json.loads(model_input)
                        messages = input_data.get("messages", [])
                        for msg in messages:
                            if isinstance(msg, dict):
                                content = str(msg.get("content", ""))
                                agent = self._extract_agent_from_reasoning(content)
                                if agent:
                                    return agent
                except json.JSONDecodeError:
                    pass
            
            # Check observation for agent responses
            observation = trace_content.get("observation", "")
            if observation and isinstance(observation, str):
                agent = self._extract_agent_from_reasoning(observation)
                if agent:
                    return agent
        
        return None
    
    def _infer_agent_from_tools(self, tools_used) -> Optional[str]:
        """Infer agent type from tools used"""
        
        tool_agent_mapping = {
            "firebolt_query": "DataAgent",
            "query_fire": "DataAgent", 
            "gong_retrieval": "DataAgent",
            "deal_analysis": "DealAnalysisAgent",
            "lead_analysis": "LeadAnalysisAgent",
            "web_search": "WebSearchAgent",
            "webhook": "ExecutionAgent"
        }
        
        for tool in tools_used:
            if isinstance(tool, dict):
                tool_name = tool.get("tool_name", "")
            else:
                tool_name = str(tool)
            
            for tool_pattern, agent in tool_agent_mapping.items():
                if tool_pattern in tool_name.lower():
                    return agent
        
        return None
    
    def _extract_handover_evidence(self, step) -> Dict[str, Any]:
        """Extract evidence of agent handover for debugging"""
        
        evidence = {
            "reasoning_snippets": [],
            "trace_indicators": [],
            "tool_indicators": []
        }
        
        # Extract reasoning evidence
        reasoning_text = step.get("reasoning_text", "")
        if reasoning_text:
            import re
            routing_matches = re.findall(r"(Route to \w+|routing to \w+|calling \w+|AgentCommunication)", reasoning_text, re.IGNORECASE)
            evidence["reasoning_snippets"] = routing_matches[:3]  # Limit to first 3
        
        # Extract trace evidence
        trace_content = step.get("bedrock_trace_content", {})
        if isinstance(trace_content, dict):
            if trace_content.get("modelInvocationInput"):
                evidence["trace_indicators"].append("modelInvocationInput_present")
            if trace_content.get("observation"):
                evidence["trace_indicators"].append("observation_present")
        
        # Extract tool evidence
        tools_used = step.get("tools_used", [])
        for tool in tools_used:
            if isinstance(tool, dict):
                tool_name = tool.get("tool_name", "")
                evidence["tool_indicators"].append(tool_name)
        
        return evidence
    
    def _safe_json_dumps(self, data: Any) -> str:
        """Safely serialize data to JSON with proper error handling and type conversion"""
        
        def json_serializer(obj):
            """Custom JSON serializer for complex objects"""
            
            # Handle datetime objects
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            
            # Handle sets
            if isinstance(obj, set):
                return list(obj)
            
            # Handle complex objects with __dict__
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            
            # Handle bytes
            if isinstance(obj, bytes):
                try:
                    return obj.decode('utf-8')
                except UnicodeDecodeError:
                    return base64.b64encode(obj).decode('utf-8')
            
            # Fallback to string representation
            return str(obj)
        
        try:
            # First attempt: Direct serialization
            return json.dumps(data, indent=2, separators=(',', ': '), ensure_ascii=False, default=json_serializer)
            
        except (TypeError, ValueError) as e:
            self.logger.warning(f"Initial JSON serialization failed: {e}. Attempting cleanup.")
            
            try:
                # Second attempt: Clean the data first
                cleaned_data = self._clean_data_for_json(data)
                return json.dumps(cleaned_data, indent=2, separators=(',', ': '), ensure_ascii=False, default=json_serializer)
                
            except Exception as e2:
                self.logger.error(f"JSON serialization failed after cleanup: {e2}")
                
                # Final fallback: Minimal structure
                fallback = {
                    "export_metadata": {
                        "format": "enhanced_structured_json",
                        "version": "2.0",
                        "exported_at": datetime.utcnow().isoformat(),
                        "serialization_error": str(e2),
                        "note": "JSON serialization failed, minimal structure provided"
                    },
                    "conversation": {
                        "error": "Serialization failed",
                        "original_error": str(e),
                        "cleanup_error": str(e2)
                    }
                }
                
                return json.dumps(fallback, indent=2, default=str)
    
    def _clean_data_for_json(self, data: Any, max_depth: int = 10, current_depth: int = 0) -> Any:
        """Recursively clean data to ensure JSON serialization"""
        
        if current_depth > max_depth:
            return f"[MAX_DEPTH_EXCEEDED: {type(data).__name__}]"
        
        if data is None:
            return None
        
        # Handle primitive types
        if isinstance(data, (str, int, float, bool)):
            return data
        
        # Handle lists
        if isinstance(data, (list, tuple)):
            try:
                return [self._clean_data_for_json(item, max_depth, current_depth + 1) for item in data[:1000]]  # Limit list size
            except Exception:
                return f"[LIST_CLEANUP_FAILED: {len(data)} items]"
        
        # Handle dictionaries
        if isinstance(data, dict):
            try:
                cleaned = {}
                for key, value in list(data.items())[:100]:  # Limit dict size
                    try:
                        # Ensure key is string
                        str_key = str(key) if not isinstance(key, str) else key
                        cleaned[str_key] = self._clean_data_for_json(value, max_depth, current_depth + 1)
                    except Exception as e:
                        cleaned[f"cleanup_error_{str(key)}"] = f"Failed to clean: {str(e)}"
                return cleaned
            except Exception:
                return f"[DICT_CLEANUP_FAILED: {len(data)} items]"
        
        # Handle datetime objects
        if hasattr(data, 'isoformat'):
            try:
                return data.isoformat()
            except Exception:
                return str(data)
        
        # Handle objects with __dict__
        if hasattr(data, '__dict__'):
            try:
                return self._clean_data_for_json(data.__dict__, max_depth, current_depth + 1)
            except Exception:
                return f"[OBJECT_CLEANUP_FAILED: {type(data).__name__}]"
        
        # Handle everything else
        try:
            return str(data)
        except Exception:
            return f"[UNSERIALIZABLE: {type(data).__name__}]"
    
    def _deep_copy_with_safety(self, data: Any) -> Any:
        """Create a deep copy of data with safety checks to prevent corruption"""
        
        try:
            import copy
            return copy.deepcopy(data)
        except Exception as e:
            self.logger.warning(f"Deep copy failed: {e}. Using shallow copy.")
            try:
                return copy.copy(data) if hasattr(copy, 'copy') else data
            except Exception:
                self.logger.warning("Shallow copy failed. Returning original data.")
                return data
    
    def validate_export_before_upload(self, content: str, format_name: str) -> Tuple[bool, List[str]]:
        """ENHANCED: Validate export content before uploading to S3 with dynamic thresholds and comprehensive quality assessment"""
        
        validation_errors = []
        validation_warnings = []
        
        try:
            # Basic content validation with dynamic thresholds
            if not content:
                validation_errors.append("Export content is empty")
                return False, validation_errors
            
            content_size = len(content.encode('utf-8'))
            
            # ENHANCED: Dynamic size validation based on format type
            size_thresholds = {
                'enhanced_structured_json': {'min': 500, 'max': 75 * 1024 * 1024},  # 500 bytes to 75MB
                'structured_json': {'min': 300, 'max': 50 * 1024 * 1024},         # 300 bytes to 50MB
                'llm_readable': {'min': 200, 'max': 25 * 1024 * 1024},            # 200 bytes to 25MB
                'analysis_format': {'min': 250, 'max': 10 * 1024 * 1024},         # 250 bytes to 10MB
                'metadata_only': {'min': 100, 'max': 1 * 1024 * 1024},           # 100 bytes to 1MB
                'agent_traces': {'min': 150, 'max': 15 * 1024 * 1024}            # 150 bytes to 15MB
            }
            
            threshold = size_thresholds.get(format_name, {'min': 100, 'max': 50 * 1024 * 1024})
            
            if content_size < threshold['min']:
                validation_errors.append(f"Export content too small: {content_size} bytes (minimum: {threshold['min']} bytes)")
                return False, validation_errors
            
            if content_size > threshold['max']:
                validation_errors.append(f"Export content too large: {content_size / (1024*1024):.1f}MB (maximum: {threshold['max'] / (1024*1024):.1f}MB)")
            
            # JSON format validation with enhanced checks
            if format_name.endswith('json'):
                try:
                    parsed_content = json.loads(content)
                    
                    # ENHANCED: Comprehensive structure validation for enhanced JSON
                    if format_name == 'enhanced_structured_json':
                        # Check required top-level keys
                        required_keys = ["export_metadata", "conversation"]
                        for key in required_keys:
                            if key not in parsed_content:
                                validation_errors.append(f"Missing required key: {key}")
                        
                        if "export_metadata" in parsed_content:
                            export_metadata = parsed_content["export_metadata"]
                            
                            # Validate export metadata structure
                            metadata_validation = self._validate_export_metadata(export_metadata)
                            validation_errors.extend(metadata_validation.get("errors", []))
                            validation_warnings.extend(metadata_validation.get("warnings", []))
                            
                            # Check system prompt filtering
                            if not export_metadata.get("system_prompts_excluded", False):
                                validation_warnings.append("System prompts may not have been properly excluded")
                        
                        if "conversation" in parsed_content:
                            conversation = parsed_content["conversation"]
                            
                            # ENHANCED: Validate conversation structure and quality
                            conversation_validation = self._validate_conversation_structure(conversation)
                            validation_errors.extend(conversation_validation.get("errors", []))
                            validation_warnings.extend(conversation_validation.get("warnings", []))
                            
                            # Check for data quality indicators
                            quality_indicators = self._assess_conversation_quality(conversation)
                            if quality_indicators["overall_score"] < 0.3:
                                validation_errors.append(f"Conversation quality score too low: {quality_indicators['overall_score']:.2f}")
                            elif quality_indicators["overall_score"] < 0.5:
                                validation_warnings.append(f"Conversation quality score below recommended threshold: {quality_indicators['overall_score']:.2f}")
                    
                    # ENHANCED: Check for system prompt leakage with multiple detection methods
                    leakage_detection = self._detect_system_prompt_leakage(content, parsed_content)
                    if leakage_detection["has_leakage"]:
                        validation_errors.append(f"System prompt leakage detected: {leakage_detection['evidence']}")
                    if leakage_detection["suspicious_patterns"]:
                        validation_warnings.append(f"Suspicious patterns found: {', '.join(leakage_detection['suspicious_patterns'])}")
                
                except json.JSONDecodeError as e:
                    validation_errors.append(f"Invalid JSON format: {e}")
            
            # ENHANCED: Text format validation for non-JSON formats
            elif format_name in ['llm_readable']:
                text_validation = self._validate_text_format(content)
                validation_errors.extend(text_validation.get("errors", []))
                validation_warnings.extend(text_validation.get("warnings", []))
            
            # ENHANCED: Final quality gate with adjustable thresholds
            if len(validation_errors) == 0:
                # Apply quality gates based on content type
                quality_gates = self._apply_quality_gates(content, format_name, parsed_content if format_name.endswith('json') else None)
                validation_errors.extend(quality_gates.get("errors", []))
                validation_warnings.extend(quality_gates.get("warnings", []))
            
            # Log warnings but don't fail validation
            if validation_warnings:
                self.logger.warning(f"Export validation warnings for {format_name}: {'; '.join(validation_warnings)}")
            
            return len(validation_errors) == 0, validation_errors
        
        except Exception as e:
            validation_errors.append(f"Validation error: {e}")
            self.logger.error(f"Export validation failed for {format_name}: {e}")
            return False, validation_errors
    
    def _validate_export_metadata(self, export_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate export metadata structure and content"""
        
        validation_result = {
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check required metadata fields
            required_fields = ["format", "version", "exported_at"]
            for field in required_fields:
                if field not in export_metadata:
                    validation_result["errors"].append(f"Missing required metadata field: {field}")
            
            # Validate format
            if "format" in export_metadata:
                valid_formats = ["enhanced_structured_json", "structured_json", "llm_readable", "analysis_format", "metadata_only", "agent_traces"]
                if export_metadata["format"] not in valid_formats:
                    validation_result["warnings"].append(f"Unknown format: {export_metadata['format']}")
            
            # Validate version
            if "version" in export_metadata:
                version = export_metadata["version"]
                if not isinstance(version, str) or not version:
                    validation_result["warnings"].append("Invalid version format")
            
            # Check validation results if present
            if "validation" in export_metadata:
                validation_data = export_metadata["validation"]
                if isinstance(validation_data, dict):
                    if validation_data.get("valid") is False:
                        validation_result["errors"].append("Validation marked as failed in metadata")
                    
                    # Check quality assessment
                    if "quality_assessment" in validation_data:
                        quality = validation_data["quality_assessment"]
                        overall_score = quality.get("overall_score", 0)
                        if overall_score < 0.2:
                            validation_result["errors"].append(f"Very low quality assessment score: {overall_score:.2f}")
                        elif overall_score < 0.4:
                            validation_result["warnings"].append(f"Low quality assessment score: {overall_score:.2f}")
            
            # Check export quality if present
            if "export_quality" in export_metadata:
                export_quality = export_metadata["export_quality"]
                if isinstance(export_quality, dict):
                    overall_score = export_quality.get("overall_score", 0)
                    if overall_score < 0.3:
                        validation_result["errors"].append(f"Export quality score too low: {overall_score:.2f}")
                    elif overall_score < 0.5:
                        validation_result["warnings"].append(f"Export quality score below optimal: {overall_score:.2f}")
        
        except Exception as e:
            validation_result["errors"].append(f"Metadata validation error: {e}")
        
        return validation_result
    
    def _validate_conversation_structure(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate conversation structure and content quality"""
        
        validation_result = {
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check required conversation fields
            required_fields = ["conversation_id"]
            for field in required_fields:
                if field not in conversation:
                    validation_result["warnings"].append(f"Missing recommended field: {field}")
            
            # Validate agent flow
            if "agent_flow" in conversation:
                agent_flow = conversation["agent_flow"]
                if not isinstance(agent_flow, list):
                    validation_result["errors"].append("Agent flow must be a list")
                elif len(agent_flow) == 0:
                    validation_result["warnings"].append("Agent flow is empty")
                else:
                    # Validate each agent step
                    for i, step in enumerate(agent_flow):
                        step_validation = self._validate_agent_step(step, i)
                        validation_result["errors"].extend(step_validation.get("errors", []))
                        validation_result["warnings"].extend(step_validation.get("warnings", []))
            else:
                validation_result["warnings"].append("No agent flow found")
            
            # Validate metadata
            if "metadata" in conversation:
                metadata = conversation["metadata"]
                if not isinstance(metadata, dict):
                    validation_result["warnings"].append("Conversation metadata should be a dictionary")
                else:
                    # Check for essential metadata
                    if not metadata.get("user_query"):
                        validation_result["warnings"].append("No user query found in metadata")
                    if not metadata.get("final_response"):
                        validation_result["warnings"].append("No final response found in metadata")
            
            # Validate conversation summary
            if "conversation_summary" in conversation:
                summary = conversation["conversation_summary"]
                if isinstance(summary, dict):
                    # Check summary quality indicators
                    if summary.get("total_agents_involved", 0) == 0:
                        validation_result["warnings"].append("No agents involved according to summary")
                    if summary.get("total_tool_executions", 0) == 0:
                        validation_result["warnings"].append("No tool executions found in summary")
                    
                    # Check for data quality metrics
                    if "data_quality_metrics" in summary:
                        quality_metrics = summary["data_quality_metrics"]
                        success_rate = quality_metrics.get("tool_execution_success_rate", 0)
                        if success_rate < 0.5:
                            validation_result["warnings"].append(f"Low tool execution success rate: {success_rate:.2f}")
        
        except Exception as e:
            validation_result["errors"].append(f"Conversation structure validation error: {e}")
        
        return validation_result
    
    def _validate_agent_step(self, step: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """Validate individual agent step"""
        
        validation_result = {
            "errors": [],
            "warnings": []
        }
        
        try:
            if not isinstance(step, dict):
                validation_result["errors"].append(f"Agent step {step_index} is not a dictionary")
                return validation_result
            
            # Check agent attribution
            agent_name = step.get("agent_name", "unknown")
            if agent_name == "unknown":
                validation_result["warnings"].append(f"Step {step_index} has unknown agent attribution")
            
            # Check for reasoning breakdown
            if "reasoning_breakdown" not in step:
                validation_result["warnings"].append(f"Step {step_index} missing reasoning breakdown")
            else:
                reasoning = step["reasoning_breakdown"]
                if not isinstance(reasoning, dict):
                    validation_result["warnings"].append(f"Step {step_index} reasoning breakdown is not a dictionary")
                else:
                    # Check reasoning quality
                    if not reasoning.get("knowledge_base_searches") and not reasoning.get("tool_executions"):
                        validation_result["warnings"].append(f"Step {step_index} has no knowledge searches or tool executions")
            
            # Check timing information
            if "timing" in step:
                timing = step["timing"]
                if isinstance(timing, dict):
                    duration = timing.get("duration_ms", 0)
                    if duration <= 0:
                        validation_result["warnings"].append(f"Step {step_index} has invalid duration: {duration}ms")
                    elif duration > 300000:  # 5 minutes
                        validation_result["warnings"].append(f"Step {step_index} has unusually long duration: {duration}ms")
        
        except Exception as e:
            validation_result["errors"].append(f"Agent step {step_index} validation error: {e}")
        
        return validation_result
    
    def _assess_conversation_quality(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall conversation quality with comprehensive metrics"""
        
        quality_assessment = {
            "overall_score": 0.0,
            "data_completeness": 0.0,
            "agent_attribution_quality": 0.0,
            "reasoning_quality": 0.0,
            "tool_execution_quality": 0.0,
            "structure_quality": 0.0
        }
        
        try:
            # Data completeness assessment
            completeness_score = 0.0
            if conversation.get("metadata"):
                completeness_score += 0.2
                if conversation["metadata"].get("user_query"):
                    completeness_score += 0.1
                if conversation["metadata"].get("final_response"):
                    completeness_score += 0.1
            
            if conversation.get("agent_flow"):
                completeness_score += 0.3
            
            if conversation.get("conversation_summary"):
                completeness_score += 0.2
            
            if conversation.get("detected_agent_handovers"):
                completeness_score += 0.1
            
            quality_assessment["data_completeness"] = min(1.0, completeness_score)
            
            # Agent attribution quality
            agent_flow = conversation.get("agent_flow", [])
            if agent_flow:
                attributed_steps = sum(1 for step in agent_flow if step.get("agent_name", "unknown") != "unknown")
                quality_assessment["agent_attribution_quality"] = attributed_steps / len(agent_flow)
            
            # Reasoning quality assessment
            reasoning_scores = []
            for step in agent_flow:
                reasoning = step.get("reasoning_breakdown", {})
                step_reasoning_score = 0.0
                
                if reasoning.get("knowledge_base_searches"):
                    step_reasoning_score += 0.3
                if reasoning.get("tool_executions"):
                    step_reasoning_score += 0.3
                if reasoning.get("decision_points"):
                    step_reasoning_score += 0.2
                if reasoning.get("final_synthesis"):
                    step_reasoning_score += 0.2
                
                reasoning_scores.append(step_reasoning_score)
            
            if reasoning_scores:
                quality_assessment["reasoning_quality"] = sum(reasoning_scores) / len(reasoning_scores)
            
            # Tool execution quality
            total_tool_executions = 0
            successful_tool_executions = 0
            
            for step in agent_flow:
                tools = step.get("reasoning_breakdown", {}).get("tool_executions", [])
                for tool in tools:
                    total_tool_executions += 1
                    if tool.get("execution_status") != "failed":
                        successful_tool_executions += 1
            
            if total_tool_executions > 0:
                quality_assessment["tool_execution_quality"] = successful_tool_executions / total_tool_executions
            else:
                quality_assessment["tool_execution_quality"] = 1.0  # No tools, no failures
            
            # Structure quality assessment
            structure_score = 0.0
            if conversation.get("conversation_id"):
                structure_score += 0.2
            if conversation.get("agents_involved"):
                structure_score += 0.2
            if conversation.get("detected_agent_handovers") is not None:
                structure_score += 0.2
            if conversation.get("conversation_summary", {}).get("data_quality_metrics"):
                structure_score += 0.4
            
            quality_assessment["structure_quality"] = structure_score
            
            # Calculate overall score
            quality_assessment["overall_score"] = sum([
                quality_assessment["data_completeness"] * 0.3,
                quality_assessment["agent_attribution_quality"] * 0.2,
                quality_assessment["reasoning_quality"] * 0.25,
                quality_assessment["tool_execution_quality"] * 0.15,
                quality_assessment["structure_quality"] * 0.1
            ])
        
        except Exception as e:
            self.logger.warning(f"Quality assessment error: {e}")
            quality_assessment["error"] = str(e)
        
        return quality_assessment
    
    def _detect_system_prompt_leakage(self, content: str, parsed_content: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhanced detection of system prompt leakage using multiple methods"""
        
        detection_result = {
            "has_leakage": False,
            "evidence": [],
            "suspicious_patterns": [],
            "confidence": 0.0
        }
        
        try:
            content_lower = content.lower()
            
            # High-confidence leakage indicators
            high_confidence_patterns = [
                "agent purpose",
                "you are an ai assistant",
                "your role is to",
                "system instruction",
                "prompt template",
                "follow these instructions",
                "you must always",
                "never reveal that you are",
                "do not mention that you are an ai"
            ]
            
            # Medium-confidence suspicious patterns
            medium_confidence_patterns = [
                "ai assistant",
                "language model",
                "instructions:",
                "guidelines:",
                "constraints:",
                "you should always",
                "remember to",
                "important notes"
            ]
            
            # Check for high-confidence leakage
            for pattern in high_confidence_patterns:
                if pattern in content_lower:
                    detection_result["has_leakage"] = True
                    detection_result["evidence"].append(f"Found pattern: '{pattern}'")
                    detection_result["confidence"] += 0.2
            
            # Check for suspicious patterns
            for pattern in medium_confidence_patterns:
                if pattern in content_lower:
                    detection_result["suspicious_patterns"].append(pattern)
                    detection_result["confidence"] += 0.1
            
            # Size-based detection for JSON content
            if parsed_content:
                # Check for very large agent steps that might contain system prompts
                agent_flow = parsed_content.get("conversation", {}).get("agent_flow", [])
                for i, step in enumerate(agent_flow):
                    step_str = json.dumps(step, default=str)
                    if len(step_str) > 100000:  # 100KB threshold
                        detection_result["suspicious_patterns"].append(f"Very large agent step {i}")
                        detection_result["confidence"] += 0.05
            
            # Pattern density check
            total_patterns = len(detection_result["evidence"]) + len(detection_result["suspicious_patterns"])
            content_kb = len(content) / 1024
            if content_kb > 0:
                pattern_density = total_patterns / content_kb
                if pattern_density > 0.5:  # More than 0.5 patterns per KB
                    detection_result["confidence"] += 0.1
            
            # Final confidence assessment
            detection_result["confidence"] = min(1.0, detection_result["confidence"])
            
            # If confidence is very high, mark as definite leakage
            if detection_result["confidence"] > 0.7:
                detection_result["has_leakage"] = True
        
        except Exception as e:
            self.logger.warning(f"System prompt leakage detection error: {e}")
        
        return detection_result
    
    def _validate_text_format(self, content: str) -> Dict[str, Any]:
        """Validate text format content"""
        
        validation_result = {
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check for basic readability
            if not content.strip():
                validation_result["errors"].append("Text content is empty")
                return validation_result
            
            # Check for reasonable structure
            lines = content.split('\n')
            if len(lines) < 5:
                validation_result["warnings"].append("Text content has very few lines")
            
            # Check for extremely long lines that might indicate formatting issues
            long_lines = sum(1 for line in lines if len(line) > 1000)
            if long_lines > len(lines) * 0.5:
                validation_result["warnings"].append("Many lines are extremely long - possible formatting issues")
            
            # Check for reasonable character distribution
            total_chars = len(content)
            if total_chars > 0:
                printable_chars = sum(1 for c in content if c.isprintable() or c in '\n\r\t')
                printable_ratio = printable_chars / total_chars
                if printable_ratio < 0.95:
                    validation_result["warnings"].append("High ratio of non-printable characters")
        
        except Exception as e:
            validation_result["errors"].append(f"Text format validation error: {e}")
        
        return validation_result
    
    def _apply_quality_gates(self, content: str, format_name: str, parsed_content: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply final quality gates based on format and content"""
        
        quality_result = {
            "errors": [],
            "warnings": []
        }
        
        try:
            content_size = len(content.encode('utf-8'))
            
            # Format-specific quality gates
            if format_name == 'enhanced_structured_json':
                if parsed_content:
                    # Check for minimum expected structure
                    conversation = parsed_content.get("conversation", {})
                    agent_flow = conversation.get("agent_flow", [])
                    
                    if len(agent_flow) == 0:
                        quality_result["warnings"].append("No agent steps found")
                    elif len(agent_flow) == 1:
                        # Single agent - check if it has meaningful content
                        step = agent_flow[0]
                        reasoning = step.get("reasoning_breakdown", {})
                        if not reasoning.get("tool_executions") and not reasoning.get("knowledge_base_searches"):
                            quality_result["warnings"].append("Single agent step with minimal activity")
                    
                    # Check for conversation completeness
                    metadata = conversation.get("metadata", {})
                    if not metadata.get("final_response"):
                        quality_result["warnings"].append("No final response found")
                    
                    # Size-based quality check
                    if content_size < 5000:  # Less than 5KB for enhanced JSON is suspicious
                        quality_result["warnings"].append("Enhanced JSON export is unusually small")
            
            elif format_name == 'llm_readable':
                # Check for reasonable text structure
                if content_size < 1000:  # Less than 1KB for readable text
                    quality_result["warnings"].append("LLM readable format is very short")
                
                # Check for conversation markers
                if "conversation:" not in content.lower() and "user:" not in content.lower():
                    quality_result["warnings"].append("No clear conversation structure found in readable format")
            
            # Universal quality gates
            if content_size > 10 * 1024 * 1024:  # 10MB
                quality_result["warnings"].append(f"Export is very large: {content_size / (1024*1024):.1f}MB")
            
        except Exception as e:
            quality_result["errors"].append(f"Quality gate error: {e}")
        
        return quality_result