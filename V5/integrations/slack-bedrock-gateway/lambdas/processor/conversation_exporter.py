"""
S3 Conversation Export Tool
Exports conversations in multiple formats optimized for different use cases
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from conversation_transformer import ConversationTransformer

class ConversationExporter:
    """Handles exporting conversations to S3 in multiple formats"""
    
    def __init__(self, s3_bucket: str, s3_prefix: str = "conversation-history/"):
        self.s3_client = boto3.client('s3')
        self.bucket = s3_bucket
        self.prefix = s3_prefix
        self.logger = logging.getLogger(__name__)
        self.transformer = ConversationTransformer()
    
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
                
                # Upload to S3
                s3_key = f"{base_path}{filename}"
                
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=content.encode('utf-8'),
                    ContentType='application/json' if filename.endswith('.json') else 'text/plain',
                    Metadata={
                        'conversation-id': getattr(conversation, 'conversation_id', conversation.get('conversation_id', 'unknown') if isinstance(conversation, dict) else 'unknown'),
                        'export-timestamp': datetime.utcnow().isoformat(),
                        'format': format_name
                    }
                )
                
                exported_urls[format_name] = f"s3://{self.bucket}/{s3_key}"
                self.logger.info(f"Exported {format_name} to {exported_urls[format_name]}")
                
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
            
            # Transform to enhanced structure
            enhanced_data = self.transformer.transform_to_enhanced_structure(conversation_data)
            
            # Validate the structure
            validation = self.transformer.validate_enhanced_structure(enhanced_data)
            
            # Add validation info to metadata
            enhanced_data["export_metadata"]["validation"] = {
                "valid": validation["valid"],
                "warnings": validation.get("warnings", []),
                "statistics": validation.get("statistics", {})
            }
            
            if not validation["valid"]:
                enhanced_data["export_metadata"]["validation"]["errors"] = validation["errors"]
                self.logger.warning(f"Enhanced structure validation failed: {validation['errors']}")
            
            return json.dumps(enhanced_data, indent=2, default=str)
            
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
            
            return json.dumps(fallback_data, indent=2, default=str)