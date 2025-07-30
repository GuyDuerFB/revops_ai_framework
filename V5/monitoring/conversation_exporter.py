"""
S3 Conversation Export Tool
Exports conversations in multiple formats optimized for different use cases
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

class ConversationExporter:
    """Handles exporting conversations to S3 in multiple formats"""
    
    def __init__(self, s3_bucket: str, s3_prefix: str = "conversation-history/"):
        self.s3_client = boto3.client('s3')
        self.bucket = s3_bucket
        self.prefix = s3_prefix
        self.logger = logging.getLogger(__name__)
    
    def export_conversation(self, conversation, formats: List[str]) -> Dict[str, str]:
        """Export conversation in specified formats and return S3 URLs"""
        
        exported_urls = {}
        
        # Generate base path: conversation-history/2025-07-29/conv-id/
        base_path = self._get_s3_path(conversation, "")
        
        format_handlers = {
            'structured_json': ('conversation.json', self._to_structured_json),
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
                        'conversation-id': conversation.conversation_id,
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
        """Generate S3 path: conversation-history/YYYY-MM-DD/conversation-id/filename"""
        
        # Extract date from timestamp
        date_part = conversation.start_timestamp[:10]  # YYYY-MM-DD
        
        return f"{self.prefix}{date_part}/{conversation.conversation_id}/{filename}"
    
    def _to_structured_json(self, conversation) -> str:
        """Convert to structured JSON format - complete data preservation"""
        
        structured_data = {
            "export_metadata": {
                "format": "structured_json",
                "version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "deduplication_applied": bool(conversation.prompt_references)
            },
            "conversation": conversation.to_analysis_json(),
            "system_prompts": conversation.system_prompts,  # Full prompts for analysis
            "prompt_references": conversation.prompt_references
        }
        
        return json.dumps(structured_data, indent=2, default=str)
    
    def _to_llm_readable_text(self, conversation) -> str:
        """Convert to LLM-readable text format - optimized for AI consumption"""
        
        lines = [
            "# Conversation Analysis",
            f"**Conversation ID**: {conversation.conversation_id}",
            f"**Date**: {conversation.start_timestamp}",
            f"**Duration**: {conversation.processing_time_ms}ms",
            f"**Success**: {conversation.success}",
            "",
            "## User Query",
            conversation.user_query,
            "",
            "## Temporal Context", 
            conversation.temporal_context,
            "",
            "## Agent Flow"
        ]
        
        for i, step in enumerate(conversation.agent_flow, 1):
            lines.extend([
                f"### Step {i}: {step.agent_name} ({step.agent_id})",
                f"**Duration**: {step.end_time} - {step.start_time}",
                "",
                "**Agent Reasoning**:",
                step.reasoning_text,
                ""
            ])
            
            if step.tools_used:
                lines.append("**Tools Used**:")
                for tool in step.tools_used:
                    lines.append(f"- {tool.tool_name}: {tool.result_summary}")
                lines.append("")
                
            if step.data_operations:
                lines.append("**Data Operations**:")
                for op in step.data_operations:
                    lines.append(f"- {op.operation} on {op.target}: {op.result_count} results")
                lines.append("")
        
        lines.extend([
            "## Final Response",
            conversation.final_response,
            "",
            "## Collaboration Summary",
            f"Agents involved: {', '.join(conversation.agents_involved)}",
            json.dumps(conversation.collaboration_map, indent=2)
        ])
        
        return "\n".join(lines)
    
    def _to_analysis_format(self, conversation) -> str:
        """Convert to analysis-optimized format - metrics and patterns"""
        
        analysis_data = {
            "conversation_metrics": {
                "id": conversation.conversation_id,
                "duration_ms": conversation.processing_time_ms,
                "success": conversation.success,
                "agent_count": len(conversation.agents_involved),
                "step_count": len(conversation.agent_flow),
                "tool_usage_count": sum(len(step.tools_used) for step in conversation.agent_flow),
                "data_operations_count": sum(len(step.data_operations) for step in conversation.agent_flow)
            },
            "agent_performance": [
                {
                    "agent_name": step.agent_name,
                    "agent_id": step.agent_id,
                    "step_duration_ms": self._calculate_step_duration(step),
                    "tools_used": len(step.tools_used),
                    "data_operations": len(step.data_operations),
                    "reasoning_length": len(step.reasoning_text)
                }
                for step in conversation.agent_flow
            ],
            "patterns": {
                "query_type": self._classify_query_type(conversation.user_query),
                "routing_pattern": self._analyze_routing_pattern(conversation.agent_flow),
                "data_access_pattern": self._analyze_data_access(conversation.agent_flow)
            },
            "raw_conversation": conversation.to_structured_json()
        }
        
        return json.dumps(analysis_data, indent=2, default=str)
    
    def _to_metadata_only(self, conversation) -> str:
        """Convert to metadata-only format - lightweight summary"""
        
        metadata = {
            "conversation_id": conversation.conversation_id,
            "session_id": conversation.session_id,
            "user_id": conversation.user_id,
            "channel": conversation.channel,
            "timestamps": {
                "start": conversation.start_timestamp,
                "end": conversation.end_timestamp,
                "duration_ms": conversation.processing_time_ms
            },
            "summary": {
                "query_length": len(conversation.user_query),
                "response_length": len(conversation.final_response),
                "agents_involved": conversation.agents_involved,
                "step_count": len(conversation.agent_flow),
                "success": conversation.success,
                "has_errors": bool(conversation.error_details)
            },
            "performance": {
                "tool_calls": sum(len(step.tools_used) for step in conversation.agent_flow),
                "data_operations": sum(len(step.data_operations) for step in conversation.agent_flow),
                "total_reasoning_length": sum(len(step.reasoning_text) for step in conversation.agent_flow)
            }
        }
        
        return json.dumps(metadata, indent=2, default=str)
    
    def _to_agent_traces(self, conversation) -> str:
        """Convert to agent traces format - debugging and analysis"""
        
        traces_data = {
            "conversation_id": conversation.conversation_id,
            "total_steps": len(conversation.agent_flow),
            "agent_traces": []
        }
        
        for i, step in enumerate(conversation.agent_flow):
            trace_info = {
                "step_number": i + 1,
                "agent_name": step.agent_name,
                "agent_id": step.agent_id,
                "timing": {
                    "start": step.start_time,
                    "end": step.end_time,
                    "duration_ms": self._calculate_step_duration(step)
                },
                "reasoning_text": step.reasoning_text,
                "trace_content": {
                    "has_model_input": bool(step.bedrock_trace_content.modelInvocationInput),
                    "model_input_length": len(step.bedrock_trace_content.modelInvocationInput or ""),
                    "has_observation": bool(step.bedrock_trace_content.observation),
                    "observation": step.bedrock_trace_content.observation,
                    "raw_trace_keys": list(step.bedrock_trace_content.raw_trace_data.keys()) if step.bedrock_trace_content.raw_trace_data else []
                },
                "tools": [
                    {
                        "tool_name": tool.tool_name,
                        "execution_time_ms": tool.execution_time_ms,
                        "success": tool.success,
                        "result_summary": tool.result_summary
                    }
                    for tool in step.tools_used
                ],
                "data_operations": [
                    {
                        "operation": op.operation,
                        "target": op.target,
                        "execution_time_ms": op.execution_time_ms,
                        "result_count": op.result_count
                    }
                    for op in step.data_operations
                ]
            }
            
            traces_data["agent_traces"].append(trace_info)
        
        return json.dumps(traces_data, indent=2, default=str)
    
    def _calculate_step_duration(self, step) -> int:
        """Calculate step duration in milliseconds"""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(step.start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(step.end_time.replace('Z', '+00:00'))
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
        total_data_ops = sum(len(step.data_operations) for step in agent_flow)
        
        if total_data_ops == 0:
            return 'no_data_access'
        elif total_data_ops <= 2:
            return 'light_data_access'
        elif total_data_ops <= 5:
            return 'moderate_data_access'
        else:
            return 'heavy_data_access'