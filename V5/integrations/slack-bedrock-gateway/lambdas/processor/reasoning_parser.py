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

logger = logging.getLogger(__name__)

class ReasoningTextParser:
    """Parses reasoning_text into structured components"""
    
    def __init__(self):
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
        """Extract tool execution information"""
        
        executions = []
        tool_id = 1
        
        # Find tool use patterns
        tool_uses = self.tool_use_pattern.findall(text)
        tool_results = self.tool_result_pattern.findall(text)
        
        # Pair tool uses with results
        for i, tool_use in enumerate(tool_uses):
            execution = {
                "tool_id": tool_id,
                "tool_name": "",
                "parameters": {},
                "timing": {},
                "result": {}
            }
            
            # Extract tool name and parameters from tool use
            try:
                # Parse tool use content
                if 'name=' in tool_use and 'input=' in tool_use:
                    name_match = re.search(r'name=([^,}]+)', tool_use)
                    if name_match:
                        execution["tool_name"] = name_match.group(1).strip()
                    
                    # Extract parameters (simplified)
                    input_match = re.search(r'input=\{([^}]+)\}', tool_use)
                    if input_match:
                        execution["parameters"] = {"raw_input": input_match.group(1).strip()}
                
                # Extract result if available
                if i < len(tool_results):
                    result_content = tool_results[i]
                    execution["result"] = self._parse_tool_result(result_content)
                
                executions.append(execution)
                tool_id += 1
                
            except Exception as e:
                logger.warning(f"Could not parse tool execution {tool_id}: {e}")
        
        return executions
    
    def _parse_tool_result(self, result_text: str) -> Dict[str, Any]:
        """Parse tool result content"""
        
        result = {
            "success": True,
            "data": [],
            "error": None
        }
        
        try:
            # Look for success/failure indicators
            if 'success": false' in result_text:
                result["success"] = False
            
            # Extract error information
            error_match = re.search(r'"error":\s*"([^"]+)"', result_text)
            if error_match:
                result["error"] = error_match.group(1)
                result["success"] = False
            
            # Extract data (simplified)
            if 'row_count' in result_text:
                row_match = re.search(r'"row_count":\s*(\d+)', result_text)
                if row_match:
                    result["row_count"] = int(row_match.group(1))
            
            if 'column_count' in result_text:
                col_match = re.search(r'"column_count":\s*(\d+)', result_text)
                if col_match:
                    result["column_count"] = int(col_match.group(1))
        
        except Exception as e:
            result["parsing_error"] = str(e)
        
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