"""
Enhanced Reasoning Text Parser
Parses raw reasoning_text into structured components for LLM-readable format
"""

import re
import json
import ast
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from message_parser import MessageParser

logger = logging.getLogger(__name__)

class ReasoningTextParser:
    """Parses reasoning_text into structured components"""
    
    def __init__(self):
        # Initialize message parser for complex content
        self.message_parser = MessageParser()
        
        # Regex patterns for different blocks
        self.user_pattern = re.compile(r'\[USER\]\s*\n(.*?)(?=\n\[(?:KNOWLEDGE BASE SEARCH|ASSISTANT|OBSERVATION|USER|$))', re.DOTALL)
        self.kb_search_pattern = re.compile(r'\[KNOWLEDGE BASE SEARCH\]\s*\n(.*?)(?=\n\[(?:OBSERVATION|ASSISTANT|USER|KNOWLEDGE BASE SEARCH|$))', re.DOTALL)
        self.observation_pattern = re.compile(r'\[OBSERVATION\]\s*\n(.*?)(?=\n\[(?:USER|ASSISTANT|KNOWLEDGE BASE SEARCH|OBSERVATION|$))', re.DOTALL)
        self.assistant_pattern = re.compile(r'\[ASSISTANT\]\s*\n(.*?)(?=\n\[(?:USER|KNOWLEDGE BASE SEARCH|OBSERVATION|ASSISTANT|$))', re.DOTALL)
        
        # Knowledge base reference patterns
        self.kb_id_pattern = re.compile(r'knowledgeBaseId:\s*([A-Z0-9]+)')
        self.search_query_pattern = re.compile(r'Search query:\s*\n(.*?)(?=\n|$)', re.DOTALL)
        self.reference_pattern = re.compile(r"Reference (\d+):\s*\n(\{.*?\})\n", re.DOTALL)
        self.metadata_pattern = re.compile(r"metadata:\s*(\{.*?\})", re.DOTALL)
        
        # Tool execution patterns
        self.tool_use_pattern = re.compile(r'\{toolUse=\{(.*?)\}\}', re.DOTALL)
        self.tool_result_pattern = re.compile(r'\{toolResult=\{(.*?)\}\}', re.DOTALL)
        
        # Timing patterns
        self.timing_pattern = re.compile(r"'(?:startTime|endTime)': datetime\.datetime\((\d+), (\d+), (\d+), (\d+), (\d+), (\d+), (\d+)")
        
        # Agent communication patterns
        self.agent_comm_pattern = re.compile(r'AgentCommunication__sendMessage.*?name="([^"]+)"', re.DOTALL)
        self.agent_handoff_pattern = re.compile(r'"agent":\s*"([^"]+)"', re.DOTALL)
        self.agent_routing_pattern = re.compile(r'Route to ([A-Za-z\s]+) Agent', re.DOTALL)
        
        # Bedrock message patterns
        self.bedrock_message_pattern = re.compile(r'"messages":\s*\[(.*?)\]', re.DOTALL)
        self.tool_invocation_pattern = re.compile(r'"tool_name":\s*"([^"]+)"', re.DOTALL)
    
    def parse_reasoning_text(self, reasoning_text: str) -> Dict[str, Any]:
        """Parse reasoning text into structured components"""
        
        try:
            structured_reasoning = {
                "context_setup": self._extract_context_setup(reasoning_text),
                "knowledge_base_searches": self._extract_kb_searches(reasoning_text),
                "tool_executions": self._extract_tool_executions(reasoning_text),
                "decision_points": self._extract_decision_points(reasoning_text),
                "final_synthesis": self._extract_final_synthesis(reasoning_text)
            }
            
            return structured_reasoning
            
        except Exception as e:
            logger.error(f"Error parsing reasoning text: {e}")
            # Return fallback structure with original text
            return {
                "parsing_error": str(e),
                "original_reasoning_text": reasoning_text[:1000] + "..." if len(reasoning_text) > 1000 else reasoning_text,
                "context_setup": {},
                "knowledge_base_searches": [],
                "tool_executions": [],
                "decision_points": [],
                "final_synthesis": {}
            }
    
    def _extract_context_setup(self, text: str) -> Dict[str, Any]:
        """Extract context and user request information"""
        
        context = {}
        
        # Extract current date/time context
        date_match = re.search(r'Current Date:\s*([^-\n]+)', text)
        if date_match:
            context["current_date"] = date_match.group(1).strip()
        
        time_match = re.search(r'Current Time:\s*([^-\n]+)', text)
        if time_match:
            context["current_time"] = time_match.group(1).strip()
            
        quarter_match = re.search(r'Current Quarter:\s*([^-\n]+)', text)
        if quarter_match:
            context["quarter"] = quarter_match.group(1).strip()
            
        month_match = re.search(r'Current Month:\s*([^-\n]+)', text)
        if month_match:
            context["month"] = month_match.group(1).strip()
        
        # Extract user request
        user_request_match = re.search(r'USER REQUEST[:\*]*\s*([^\n]+)', text)
        if user_request_match:
            context["user_request"] = user_request_match.group(1).strip()
        
        return context
    
    def _extract_kb_searches(self, text: str) -> List[Dict[str, Any]]:
        """Extract knowledge base search information"""
        
        searches = []
        search_id = 1
        
        # Find all knowledge base search blocks
        kb_blocks = self.kb_search_pattern.findall(text)
        obs_blocks = self.observation_pattern.findall(text)
        
        # Pair KB searches with their observations
        for i, kb_block in enumerate(kb_blocks):
            search_info = {
                "search_id": search_id,
                "query": "",
                "knowledge_base_id": "",
                "timing": {},
                "references_found": []
            }
            
            # Extract search query
            query_match = self.search_query_pattern.search(kb_block)
            if query_match:
                search_info["query"] = query_match.group(1).strip()
            
            # Extract knowledge base ID
            kb_id_match = self.kb_id_pattern.search(kb_block)
            if kb_id_match:
                search_info["knowledge_base_id"] = kb_id_match.group(1)
            
            # Extract timing from metadata if available
            if i < len(obs_blocks):
                search_info["timing"] = self._extract_timing_from_text(obs_blocks[i])
                search_info["references_found"] = self._extract_references(obs_blocks[i])
            
            searches.append(search_info)
            search_id += 1
        
        return searches
    
    def _extract_references(self, observation_text: str) -> List[Dict[str, Any]]:
        """Extract knowledge base references from observation text"""
        
        references = []
        
        # Find all reference blocks
        ref_matches = self.reference_pattern.findall(observation_text)
        
        for ref_num, ref_content in ref_matches:
            try:
                # Try to parse the reference as a Python literal
                ref_dict = ast.literal_eval(ref_content.strip())
                
                reference = {
                    "reference_id": int(ref_num),
                    "content": {
                        "text": ref_dict.get('content', {}).get('text', '')[:500] + "..." if len(ref_dict.get('content', {}).get('text', '')) > 500 else ref_dict.get('content', {}).get('text', ''),
                        "type": ref_dict.get('content', {}).get('type', 'TEXT')
                    },
                    "location": {
                        "s3_uri": ref_dict.get('location', {}).get('s3Location', {}).get('uri', ''),
                        "type": ref_dict.get('location', {}).get('type', 'S3')
                    },
                    "metadata": {
                        "source_uri": ref_dict.get('metadata', {}).get('x-amz-bedrock-kb-source-uri', ''),
                        "chunk_id": ref_dict.get('metadata', {}).get('x-amz-bedrock-kb-chunk-id', ''),
                        "data_source_id": ref_dict.get('metadata', {}).get('x-amz-bedrock-kb-data-source-id', '')
                    }
                }
                
                references.append(reference)
                
            except Exception as e:
                logger.warning(f"Could not parse reference {ref_num}: {e}")
                # Add a fallback reference
                references.append({
                    "reference_id": int(ref_num),
                    "content": {
                        "text": ref_content[:500] + "..." if len(ref_content) > 500 else ref_content,
                        "type": "TEXT"
                    },
                    "location": {"s3_uri": "", "type": "S3"},
                    "metadata": {"parsing_error": str(e)}
                })
        
        return references
    
    def _extract_tool_executions(self, text: str) -> List[Dict[str, Any]]:
        """Extract tool execution information with enhanced data quality"""
        
        executions = []
        tool_id = 1
        
        # Find tool use patterns
        tool_uses = self.tool_use_pattern.findall(text)
        tool_results = self.tool_result_pattern.findall(text)
        
        # ENHANCED: Also look for MessageParser parsed tool executions
        parsed_tool_executions = self._extract_parsed_tool_executions(text)
        
        # Pair tool uses with results
        for i, tool_use in enumerate(tool_uses):
            execution = {
                "tool_id": tool_id,
                "tool_name": "",
                "parameters": {},
                "timing": {},
                "result": {},
                "execution_status": "unknown",
                "quality_score": 0.0
            }
            
            # Extract tool name and parameters from tool use
            try:
                # Parse tool use content
                if 'name=' in tool_use and 'input=' in tool_use:
                    name_match = re.search(r'name=([^,}]+)', tool_use)
                    if name_match:
                        execution["tool_name"] = name_match.group(1).strip()
                        execution["quality_score"] += 0.3  # Has tool name
                    
                    # ENHANCED: Extract parameters with better parsing
                    execution["parameters"] = self._extract_enhanced_tool_parameters(tool_use)
                    if execution["parameters"]:
                        execution["quality_score"] += 0.2  # Has parameters
                
                # ENHANCED: Extract result with better parsing and validation
                if i < len(tool_results):
                    result_content = tool_results[i]
                    execution["result"] = self._parse_enhanced_tool_result(result_content)
                    
                    # Update execution status based on result
                    if execution["result"].get("success") is not None:
                        execution["execution_status"] = "success" if execution["result"]["success"] else "failed"
                        execution["quality_score"] += 0.3  # Has result status
                    
                    # Check for actual data in result
                    if execution["result"].get("data") or execution["result"].get("row_count", 0) > 0:
                        execution["quality_score"] += 0.2  # Has actual result data
                
                # ENHANCED: Try to find better tool execution data from parsed content
                better_execution = self._find_matching_parsed_execution(execution, parsed_tool_executions)
                if better_execution:
                    execution.update(better_execution)
                    execution["quality_score"] = min(1.0, execution["quality_score"] + 0.3)
                    execution["data_source"] = "enhanced_parsing"
                
                executions.append(execution)
                tool_id += 1
                
            except Exception as e:
                logger.warning(f"Could not parse tool execution {tool_id}: {e}")
                # Still add a fallback execution entry
                executions.append({
                    "tool_id": tool_id,
                    "tool_name": "unknown",
                    "parameters": {"raw_tool_use": tool_use[:200]},
                    "result": {"parsing_error": str(e)},
                    "execution_status": "parsing_failed",
                    "quality_score": 0.1
                })
                tool_id += 1
        
        # ENHANCED: Add any parsed executions that weren't matched
        for parsed_exec in parsed_tool_executions:
            if not any(exec_data.get("data_source") == "enhanced_parsing" for exec_data in executions):
                parsed_exec["tool_id"] = tool_id
                parsed_exec["quality_score"] = 0.8  # High quality from structured parsing
                parsed_exec["data_source"] = "message_parser"
                executions.append(parsed_exec)
                tool_id += 1
        
        return executions
    
    def _parse_enhanced_tool_result(self, result_text: str) -> Dict[str, Any]:
        """Parse tool result content with enhanced data extraction"""
        
        result = {
            "success": True,
            "data": [],
            "error": None,
            "metadata": {},
            "execution_details": {}
        }
        
        try:
            # ENHANCED: Try to parse as JSON first
            if result_text.strip().startswith('{') and result_text.strip().endswith('}'):
                try:
                    parsed_json = json.loads(result_text)
                    result.update(parsed_json)
                    result["parsing_method"] = "json"
                    return result
                except json.JSONDecodeError:
                    pass
            
            # ENHANCED: Look for success/failure indicators with better patterns
            success_patterns = [
                r'"success":\s*(true|false)',
                r'"status":\s*"(success|failed|error)"',
                r'"state":\s*"(completed|failed|error)"'
            ]
            
            for pattern in success_patterns:
                match = re.search(pattern, result_text, re.IGNORECASE)
                if match:
                    value = match.group(1).lower()
                    result["success"] = value in ["true", "success", "completed"]
                    break
            
            # ENHANCED: Extract error information with better patterns
            error_patterns = [
                r'"error":\s*"([^"]+)"',
                r'"error_message":\s*"([^"]+)"',
                r'"message":\s*"([^"]+)".*(?:error|failed)',
                r'Error:\s*([^\n\r]+)',
                r'Exception:\s*([^\n\r]+)'
            ]
            
            for pattern in error_patterns:
                error_match = re.search(pattern, result_text, re.IGNORECASE)
                if error_match:
                    result["error"] = error_match.group(1)
                    result["success"] = False
                    break
            
            # ENHANCED: Extract data with comprehensive patterns
            data_patterns = {
                "row_count": [r'"row_count":\s*(\d+)', r'"rows":\s*(\d+)', r'(\d+)\s*rows?'],
                "column_count": [r'"column_count":\s*(\d+)', r'"columns":\s*(\d+)', r'(\d+)\s*columns?'],
                "record_count": [r'"record_count":\s*(\d+)', r'"records":\s*(\d+)', r'(\d+)\s*records?'],
                "execution_time_ms": [r'"execution_time_ms":\s*(\d+)', r'"duration":\s*(\d+)', r'(\d+)\s*ms'],
                "query_time": [r'"query_time":\s*([\d.]+)', r'executed in ([\d.]+)s']
            }
            
            for key, patterns in data_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, result_text)
                    if match:
                        try:
                            result[key] = int(float(match.group(1)))
                        except ValueError:
                            result[key] = match.group(1)
                        break
            
            # ENHANCED: Extract actual data arrays/objects
            data_array_match = re.search(r'"data":\s*\[(.*?)\]', result_text, re.DOTALL)
            if data_array_match:
                data_content = data_array_match.group(1).strip()
                if data_content:
                    try:
                        # Try to parse as JSON array
                        result["data"] = json.loads(f"[{data_content}]")
                    except json.JSONDecodeError:
                        # Store as string if not valid JSON
                        result["data"] = [data_content[:500] + "..." if len(data_content) > 500 else data_content]
            
            # ENHANCED: Extract metadata information
            metadata_patterns = {
                "table_name": r'"table[_-]?name":\s*"([^"]+)"',
                "database": r'"database":\s*"([^"]+)"',
                "schema": r'"schema":\s*"([^"]+)"',
                "query_type": r'"query[_-]?type":\s*"([^"]+)"',
                "tool_version": r'"version":\s*"([^"]+)"'
            }
            
            for key, pattern in metadata_patterns.items():
                match = re.search(pattern, result_text, re.IGNORECASE)
                if match:
                    result["metadata"][key] = match.group(1)
            
            # ENHANCED: Extract execution details
            if "query" in result_text.lower():
                query_match = re.search(r'"query":\s*"([^"]+)"', result_text)
                if query_match:
                    query_text = query_match.group(1)
                    result["execution_details"]["query_preview"] = query_text[:200] + "..." if len(query_text) > 200 else query_text
            
            # ENHANCED: Add result quality assessment
            quality_indicators = {
                "has_row_count": "row_count" in result,
                "has_data": bool(result.get("data")),
                "has_execution_time": "execution_time_ms" in result,
                "has_metadata": bool(result.get("metadata")),
                "has_clear_status": result.get("success") is not None
            }
            
            result["quality_indicators"] = quality_indicators
            result["quality_score"] = sum(quality_indicators.values()) / len(quality_indicators)
            result["parsing_method"] = "enhanced_regex"
        
        except Exception as e:
            result["parsing_error"] = str(e)
            result["quality_score"] = 0.0
        
        return result
    
    def _extract_timing_from_text(self, text: str) -> Dict[str, Any]:
        """Extract timing information from text"""
        
        timing = {}
        
        # Look for metadata timing
        metadata_match = self.metadata_pattern.search(text)
        if metadata_match:
            try:
                metadata_str = metadata_match.group(1)
                
                # Extract start/end times if present
                start_match = re.search(r"'startTime': datetime\.datetime\(([^)]+)\)", metadata_str)
                end_match = re.search(r"'endTime': datetime\.datetime\(([^)]+)\)", metadata_str)
                
                if start_match:
                    timing["start_time"] = self._parse_datetime_components(start_match.group(1))
                if end_match:
                    timing["end_time"] = self._parse_datetime_components(end_match.group(1))
                
                # Calculate duration if both times available
                if "start_time" in timing and "end_time" in timing:
                    try:
                        start_dt = datetime.fromisoformat(timing["start_time"].replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(timing["end_time"].replace('Z', '+00:00'))
                        timing["duration_ms"] = int((end_dt - start_dt).total_seconds() * 1000)
                    except:
                        timing["duration_ms"] = 0
                        
            except Exception as e:
                logger.warning(f"Could not parse timing: {e}")
        
        return timing
    
    def _parse_datetime_components(self, components: str) -> str:
        """Parse datetime components into ISO format"""
        
        try:
            parts = [int(x.strip()) for x in components.split(',')]
            if len(parts) >= 6:
                dt = datetime(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5])
                return dt.isoformat() + 'Z'
        except:
            pass
        
        return ""
    
    def _extract_decision_points(self, text: str) -> List[Dict[str, Any]]:
        """Extract decision points from reasoning flow"""
        
        decisions = []
        
        # Look for decision-making patterns (simplified heuristics)
        decision_patterns = [
            r'Based on (.*?), I (?:will|should|need to) (.*?)(?:\.|$)',
            r'(?:Since|Because) (.*?), (?:I will|let me|I should) (.*?)(?:\.|$)',
            r'The (.*?) (?:shows|indicates|confirms) (.*?)(?:\.|$)'
        ]
        
        decision_id = 1
        
        for pattern in decision_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                decision = {
                    "decision_id": decision_id,
                    "analysis": match.group(1).strip()[:200],
                    "decision": match.group(2).strip()[:200]
                }
                decisions.append(decision)
                decision_id += 1
        
        return decisions[:5]  # Limit to 5 most relevant decisions
    
    def _extract_final_synthesis(self, text: str) -> Dict[str, Any]:
        """Extract final synthesis and approach summary"""
        
        synthesis = {
            "approach": "",
            "data_sources_used": [],
            "confidence_level": "medium",
            "reasoning": ""
        }
        
        # Extract approach summary (look for concluding patterns)
        approach_patterns = [
            r'Based on (?:the )?(.*?), (?:I|we) (?:can|will|have) (.*?)(?:\.|$)',
            r'(?:Using|From) the (.*?), (?:I|we) (?:found|determined|concluded) (.*?)(?:\.|$)'
        ]
        
        for pattern in approach_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                synthesis["approach"] = f"{match.group(1).strip()} to {match.group(2).strip()}"
                break
        
        # Extract data sources mentioned
        source_patterns = [
            r'(?:from|in|using) (?:the )?([a-zA-Z_]+(?:_[a-z])?)(?: table| database| schema)',
            r'(?:query|querying|from) ([a-zA-Z_]+_[a-z])',
            r'knowledge base.*?([A-Z0-9]{10})'
        ]
        
        sources = set()
        for pattern in source_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                sources.add(match.group(1))
        
        synthesis["data_sources_used"] = list(sources)[:5]
        
        # Determine confidence level based on success indicators
        if 'successfully' in text.lower() or 'confirmed' in text.lower():
            synthesis["confidence_level"] = "high"
        elif 'error' in text.lower() or 'failed' in text.lower():
            synthesis["confidence_level"] = "low"
        
        # Extract reasoning summary
        synthesis["reasoning"] = text.split('\n')[-1][:300] if text.split('\n') else ""
        
        return synthesis
    
    def parse_bedrock_trace_content(self, trace_content) -> Dict[str, Any]:
        """Parse Bedrock trace content to extract agent handoffs and tool executions"""
        
        if not trace_content:
            return {"agent_handoffs": [], "tool_executions": [], "messages_parsed": []}
        
        parsed_content = {
            "agent_handoffs": [],
            "tool_executions": [],
            "messages_parsed": [],
            "routing_decisions": []
        }
        
        # Handle different trace content types
        if isinstance(trace_content, dict):
            # Parse messages from trace content
            if "messages" in trace_content:
                parsed_content["messages_parsed"] = self._parse_bedrock_messages(trace_content["messages"])
            
            # Parse model invocation input
            if "modelInvocationInput" in trace_content:
                model_input_data = self._parse_model_invocation_input(trace_content["modelInvocationInput"])
                parsed_content["tool_executions"].extend(model_input_data.get("tool_executions", []))
                parsed_content["agent_handoffs"].extend(model_input_data.get("agent_handoffs", []))
            
            # Parse observation content
            if "observation" in trace_content:
                obs_data = self._parse_observation_content(trace_content["observation"])
                parsed_content["routing_decisions"].extend(obs_data.get("routing_decisions", []))
        
        elif isinstance(trace_content, str):
            # Parse string-based trace content
            string_data = self._parse_string_trace_content(trace_content)
            parsed_content.update(string_data)
        
        return parsed_content
    
    def _parse_bedrock_messages(self, messages) -> List[Dict[str, Any]]:
        """Parse Bedrock messages array for tool executions and agent communications"""
        
        # Use the enhanced MessageParser for better parsing
        parsed_messages = self.message_parser.parse_messages_array(messages)
        
        # Enhance the parsed messages with additional analysis
        enhanced_messages = []
        
        for parsed_msg in parsed_messages:
            # Add additional analysis from the original parsing logic
            enhanced_msg = parsed_msg.copy()
            
            # Extract parsed content details
            parsed_content = parsed_msg.get("parsed_content", {})
            
            # Consolidate tool information
            tool_uses = parsed_content.get("tool_uses", [])
            tool_results = parsed_content.get("tool_results", [])
            agent_comms = parsed_content.get("agent_communications", [])
            
            # Add summary statistics
            enhanced_msg["summary"] = {
                "tool_uses_count": len(tool_uses),
                "tool_results_count": len(tool_results),
                "agent_communications_count": len(agent_comms),
                "has_errors": any(tr.get("error_details") for tr in tool_results),
                "content_size": len(str(parsed_content.get("raw_content_preview", "")))
            }
            
            # Extract agent names from communications
            if agent_comms:
                agents_mentioned = set()
                for comm in agent_comms:
                    target_agent = comm.get("target_agent", "")
                    if target_agent:
                        agents_mentioned.add(target_agent)
                enhanced_msg["agents_mentioned"] = list(agents_mentioned)
            
            enhanced_messages.append(enhanced_msg)
        
        return enhanced_messages
    
    def _parse_model_invocation_input(self, model_input) -> Dict[str, Any]:
        """Parse modelInvocationInput for agent handoffs and tool information"""
        
        parsed_data = {
            "agent_handoffs": [],
            "tool_executions": []
        }
        
        if isinstance(model_input, str):
            try:
                input_data = json.loads(model_input)
                
                # Check for agent routing in messages
                if "messages" in input_data:
                    messages = input_data["messages"]
                    for msg in messages:
                        if isinstance(msg, dict) and "content" in msg:
                            content = str(msg["content"])
                            
                            # Extract agent routing decisions
                            routing_matches = self.agent_routing_pattern.findall(content)
                            for match in routing_matches:
                                parsed_data["agent_handoffs"].append({
                                    "target_agent": match.strip(),
                                    "routing_reason": self._extract_routing_reason(content, match),
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                            
                            # Extract agent communications
                            comm_matches = self.agent_comm_pattern.findall(content)
                            for match in comm_matches:
                                parsed_data["agent_handoffs"].append({
                                    "target_agent": match,
                                    "communication_type": "agent_communication",
                                    "timestamp": datetime.utcnow().isoformat()
                                })
                
            except json.JSONDecodeError:
                pass
        
        return parsed_data
    
    def _parse_observation_content(self, observation) -> Dict[str, Any]:
        """Parse observation content for routing decisions and agent responses"""
        
        parsed_data = {
            "routing_decisions": [],
            "agent_responses": []
        }
        
        if isinstance(observation, str):
            # Look for routing decisions
            if "Route to" in observation:
                routing_matches = self.agent_routing_pattern.findall(observation)
                for match in routing_matches:
                    parsed_data["routing_decisions"].append({
                        "decision": f"Route to {match} Agent",
                        "reasoning": self._extract_routing_reason(observation, match),
                        "timestamp": datetime.utcnow().isoformat()
                    })
        
        return parsed_data
    
    def _parse_string_trace_content(self, trace_content: str) -> Dict[str, Any]:
        """Parse string-based trace content"""
        
        parsed_data = {
            "agent_handoffs": [],
            "tool_executions": [],
            "messages_parsed": []
        }
        
        # Extract agent handoffs from string content
        handoff_matches = self.agent_handoff_pattern.findall(trace_content)
        for match in handoff_matches:
            parsed_data["agent_handoffs"].append({
                "target_agent": match,
                "source": "string_trace_content",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Extract tool invocations
        tool_matches = self.tool_invocation_pattern.findall(trace_content)
        for match in tool_matches:
            parsed_data["tool_executions"].append({
                "tool_name": match,
                "source": "string_trace_content",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return parsed_data
    
    def _classify_message_content(self, content: str) -> str:
        """Classify the type of message content"""
        
        if not content:
            return "empty"
        
        content_str = str(content).lower()
        
        if "tooluse" in content_str:
            return "tool_execution"
        elif "toolresult" in content_str:
            return "tool_result"
        elif "agentcommunication" in content_str:
            return "agent_communication"
        elif len(content_str) > 1000 and any(indicator in content_str for indicator in ["agent purpose", "instructions", "guidelines"]):
            return "system_prompt"
        else:
            return "user_message"
    
    def _extract_tool_uses_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract tool use information from message content"""
        
        tool_uses = []
        
        # Look for toolUse patterns in the content
        if "toolUse" in content:
            # Try to extract structured tool use data
            try:
                # Pattern for toolUse with parameters
                tool_pattern = re.compile(r'toolUse=\{input=\{([^}]+)\}, name=([^}]+)\}')
                matches = tool_pattern.findall(content)
                
                for params, tool_name in matches:
                    tool_uses.append({
                        "tool_name": tool_name.strip(),
                        "parameters": params.strip(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.warning(f"Failed to parse tool use from content: {e}")
        
        return tool_uses
    
    def _extract_tool_results_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract tool result information from message content"""
        
        tool_results = []
        
        if "toolResult" in content:
            try:
                # Pattern for toolResult with content
                result_pattern = re.compile(r'toolResult=\{toolUseId=([^,]+),.*?content=\[(.*?)\]')
                matches = result_pattern.findall(content)
                
                for tool_use_id, result_content in matches:
                    tool_results.append({
                        "tool_use_id": tool_use_id.strip(),
                        "result_content": result_content.strip()[:500],  # Limit content size
                        "success": "error" not in result_content.lower(),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.warning(f"Failed to parse tool result from content: {e}")
        
        return tool_results
    
    def _extract_agent_communications_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract agent communication information from message content"""
        
        communications = []
        
        if "AgentCommunication" in content:
            try:
                # Extract target agent name
                comm_matches = self.agent_comm_pattern.findall(content)
                for target_agent in comm_matches:
                    communications.append({
                        "target_agent": target_agent,
                        "communication_type": "sendMessage",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.warning(f"Failed to parse agent communication from content: {e}")
        
        return communications
    
    def _extract_enhanced_tool_parameters(self, tool_use: str) -> Dict[str, Any]:
        """Extract tool parameters with enhanced parsing"""
        
        parameters = {}
        
        try:
            # Enhanced parameter extraction patterns
            param_patterns = {
                "query": [r'query=([^,}]+)', r'"query":\s*"([^"]+)"'],
                "searchQuery": [r'searchQuery=([^,}]+)', r'"searchQuery":\s*"([^"]+)"'],
                "table": [r'table=([^,}]+)', r'"table":\s*"([^"]+)"'],
                "database": [r'database=([^,}]+)', r'"database":\s*"([^"]+)"'],
                "limit": [r'limit=(\d+)', r'"limit":\s*(\d+)'],
                "offset": [r'offset=(\d+)', r'"offset":\s*(\d+)']
            }
            
            for param_name, patterns in param_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, tool_use)
                    if match:
                        value = match.group(1).strip().strip('"\'')
                        # Clean up common formatting issues
                        if param_name == "query":
                            value = value.replace('\\n', '\n').replace('\\"', '"')
                        parameters[param_name] = value
                        break
            
            # Extract all key-value pairs as fallback
            if not parameters:
                kv_pattern = re.compile(r'(\w+)=([^,}]+)')
                matches = kv_pattern.findall(tool_use)
                for key, value in matches:
                    if key not in parameters:
                        parameters[key] = value.strip().strip('"\'')
        
        except Exception as e:
            logger.warning(f"Failed to extract enhanced tool parameters: {e}")
            parameters["parsing_error"] = str(e)
            parameters["raw_tool_use"] = tool_use[:200]
        
        return parameters
    
    def _extract_parsed_tool_executions(self, text: str) -> List[Dict[str, Any]]:
        """Extract tool executions using MessageParser for better quality"""
        
        parsed_executions = []
        
        try:
            # Use MessageParser to parse tool execution blocks
            parsed_content = self.message_parser.parse_message_content(text)
            
            # Extract tool uses and results
            tool_uses = parsed_content.get("tool_uses", [])
            tool_results = parsed_content.get("tool_results", [])
            
            # Create enhanced tool execution entries
            for i, tool_use in enumerate(tool_uses):
                execution = {
                    "tool_name": tool_use.get("tool_name", "unknown"),
                    "parameters": tool_use.get("parameters", {}),
                    "raw_parameters": tool_use.get("raw_parameters", ""),
                    "timestamp": tool_use.get("timestamp", ""),
                    "execution_status": "executed"
                }
                
                # Find matching result
                matching_result = None
                for result in tool_results:
                    if result.get("tool_use_id") == tool_use.get("tool_use_id"):
                        matching_result = result
                        break
                
                if matching_result:
                    execution["result"] = {
                        "success": matching_result.get("success", True),
                        "content": matching_result.get("content", ""),
                        "structured_content": matching_result.get("structured_content", {}),
                        "error_details": matching_result.get("error_details"),
                        "status": matching_result.get("status", "unknown")
                    }
                    execution["execution_status"] = "success" if matching_result.get("success") else "failed"
                
                parsed_executions.append(execution)
        
        except Exception as e:
            logger.warning(f"Failed to extract parsed tool executions: {e}")
        
        return parsed_executions
    
    def _find_matching_parsed_execution(self, basic_execution: Dict[str, Any], parsed_executions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find matching parsed execution to enhance basic execution data"""
        
        basic_tool_name = basic_execution.get("tool_name", "unknown")
        
        for parsed_exec in parsed_executions:
            parsed_tool_name = parsed_exec.get("tool_name", "unknown")
            
            # Match by tool name and check if parsed version has better data
            if (basic_tool_name == parsed_tool_name or 
                (basic_tool_name == "unknown" and parsed_tool_name != "unknown")):
                
                # Check if parsed version has better result data
                parsed_result = parsed_exec.get("result", {})
                basic_result = basic_execution.get("result", {})
                
                if (parsed_result.get("structured_content") or 
                    parsed_result.get("success") is not None or
                    len(str(parsed_result.get("content", ""))) > len(str(basic_result.get("data", "")))):
                    
                    return {
                        "tool_name": parsed_exec.get("tool_name", basic_tool_name),
                        "parameters": parsed_exec.get("parameters", basic_execution.get("parameters", {})),
                        "result": parsed_result,
                        "execution_status": parsed_exec.get("execution_status", "enhanced")
                    }
        
        return None
    
    def _extract_routing_reason(self, content: str, agent_name: str) -> str:
        """Extract the reason for routing to a specific agent"""
        
        # Look for context around the routing decision
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if agent_name in line and "Route to" in line:
                # Get surrounding context
                start = max(0, i-2)
                end = min(len(lines), i+3)
                context = ' '.join(lines[start:end])
                return context[:200]  # Limit context size
        
        return f"Routing to {agent_name} Agent"