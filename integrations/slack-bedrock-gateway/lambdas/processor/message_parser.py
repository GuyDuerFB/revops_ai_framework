"""
Enhanced Bedrock Message Parser
Handles complex Bedrock message formats and converts them to structured data
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageParser:
    """Parses complex Bedrock message formats into structured data"""
    
    def __init__(self):
        # Patterns for different message components
        self.tool_use_pattern = re.compile(r'\{toolUse=\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\}', re.DOTALL)
        self.tool_result_pattern = re.compile(r'\{toolResult=\{([^}]+(?:\{[^}]*\}[^}]*)*)\}\}', re.DOTALL)
        
        # Patterns for parameter extraction
        self.input_pattern = re.compile(r'input=\{([^}]+)\}')
        self.name_pattern = re.compile(r'name=([^,}\s]+)')
        self.tool_use_id_pattern = re.compile(r'toolUseId=([^,}\s]+)')
        self.content_pattern = re.compile(r'content=\[(.*?)\]', re.DOTALL)
        self.status_pattern = re.compile(r'status=([^,}\s]+)')
        
        # Patterns for nested content
        self.json_content_pattern = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}')
        self.error_pattern = re.compile(r'"error":\s*"([^"]*)"')
        self.success_pattern = re.compile(r'"success":\s*(true|false)')
        
        # Agent communication patterns
        self.agent_send_pattern = re.compile(r'AgentCommunication__sendMessage.*?name="([^"]+)"', re.DOTALL)
        
    def parse_message_content(self, content: str) -> Dict[str, Any]:
        """Parse message content into structured format"""
        
        if not content:
            return {"type": "empty", "parsed_content": {}}
        
        parsed_data = {
            "type": self._classify_content_type(content),
            "tool_uses": [],
            "tool_results": [],
            "agent_communications": [],
            "raw_content_preview": content[:200] + "..." if len(content) > 200 else content,
            "parsing_timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Parse tool uses
            tool_uses = self._extract_tool_uses(content)
            parsed_data["tool_uses"] = tool_uses
            
            # Parse tool results
            tool_results = self._extract_tool_results(content)
            parsed_data["tool_results"] = tool_results
            
            # Parse agent communications
            agent_comms = self._extract_agent_communications(content)
            parsed_data["agent_communications"] = agent_comms
            
            # Extract structured JSON if present
            json_content = self._extract_json_content(content)
            if json_content:
                parsed_data["structured_content"] = json_content
            
            # Parse error information
            error_info = self._extract_error_information(content)
            if error_info:
                parsed_data["error_information"] = error_info
                
        except Exception as e:
            logger.error(f"Error parsing message content: {e}")
            parsed_data["parsing_error"] = str(e)
        
        return parsed_data
    
    def _classify_content_type(self, content: str) -> str:
        """Classify the type of message content"""
        
        content_lower = content.lower()
        
        if "tooluse" in content_lower and "toolresult" in content_lower:
            return "tool_conversation"
        elif "tooluse" in content_lower:
            return "tool_execution"
        elif "toolresult" in content_lower:
            return "tool_result"
        elif "agentcommunication" in content_lower:
            return "agent_communication"
        elif "error" in content_lower and ("failed" in content_lower or "exception" in content_lower):
            return "error_message"
        elif content.startswith("[{text="):
            return "structured_text"
        elif content.startswith('{"system":'):
            return "system_prompt"
        elif len(content) > 1000:
            return "complex_content"
        else:
            return "simple_text"
    
    def _extract_tool_uses(self, content: str) -> List[Dict[str, Any]]:
        """Extract tool use information from content"""
        
        tool_uses = []
        
        # Find all tool use blocks
        matches = self.tool_use_pattern.findall(content)
        
        for match in matches:
            try:
                tool_use = self._parse_tool_use_block(match)
                if tool_use:
                    tool_uses.append(tool_use)
            except Exception as e:
                logger.warning(f"Failed to parse tool use block: {e}")
                tool_uses.append({
                    "parsing_error": str(e),
                    "raw_block": match[:200] + "..." if len(match) > 200 else match
                })
        
        return tool_uses
    
    def _parse_tool_use_block(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse individual tool use block"""
        
        tool_use = {
            "tool_name": "unknown",
            "parameters": {},
            "raw_parameters": "",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Extract tool name
        name_match = self.name_pattern.search(block)
        if name_match:
            tool_use["tool_name"] = name_match.group(1).strip()
        
        # Extract parameters
        input_match = self.input_pattern.search(block)
        if input_match:
            raw_params = input_match.group(1)
            tool_use["raw_parameters"] = raw_params
            
            # Try to parse parameters into structured format
            parsed_params = self._parse_tool_parameters(raw_params)
            tool_use["parameters"] = parsed_params
        
        return tool_use
    
    def _parse_tool_parameters(self, raw_params: str) -> Dict[str, Any]:
        """Parse tool parameters from raw string"""
        
        parsed = {}
        
        try:
            # Handle common parameter patterns
            if "query=" in raw_params:
                # SQL query parameter
                query_match = re.search(r'query=([^,}]+)', raw_params)
                if query_match:
                    query = query_match.group(1).strip()
                    # Clean up query formatting
                    query = query.replace('\\n', '\n').replace('\\"', '"')
                    parsed["query"] = query
            
            if "searchQuery=" in raw_params:
                # Knowledge base search parameter
                search_match = re.search(r'searchQuery=([^,}]+)', raw_params)
                if search_match:
                    search_query = search_match.group(1).strip()
                    parsed["searchQuery"] = search_query
            
            # Extract other key-value pairs
            kv_pattern = re.compile(r'(\w+)=([^,}]+)')
            matches = kv_pattern.findall(raw_params)
            
            for key, value in matches:
                if key not in parsed:  # Don't overwrite already parsed values
                    # Clean up value
                    value = value.strip().strip('"\'')
                    parsed[key] = value
                    
        except Exception as e:
            logger.warning(f"Failed to parse tool parameters: {e}")
            parsed["parsing_error"] = str(e)
            parsed["raw_params"] = raw_params
        
        return parsed
    
    def _extract_tool_results(self, content: str) -> List[Dict[str, Any]]:
        """Extract tool result information from content"""
        
        tool_results = []
        
        # Find all tool result blocks
        matches = self.tool_result_pattern.findall(content)
        
        for match in matches:
            try:
                tool_result = self._parse_tool_result_block(match)
                if tool_result:
                    tool_results.append(tool_result)
            except Exception as e:
                logger.warning(f"Failed to parse tool result block: {e}")
                tool_results.append({
                    "parsing_error": str(e),
                    "raw_block": match[:200] + "..." if len(match) > 200 else match
                })
        
        return tool_results
    
    def _parse_tool_result_block(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse individual tool result block"""
        
        tool_result = {
            "tool_use_id": "unknown",
            "status": "unknown",
            "content": "",
            "success": None,
            "error_details": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Extract tool use ID
        id_match = self.tool_use_id_pattern.search(block)
        if id_match:
            tool_result["tool_use_id"] = id_match.group(1).strip()
        
        # Extract status
        status_match = self.status_pattern.search(block)
        if status_match:
            tool_result["status"] = status_match.group(1).strip()
        
        # Extract content
        content_match = self.content_pattern.search(block)
        if content_match:
            raw_content = content_match.group(1)
            tool_result["content"] = raw_content
            
            # Parse structured content if it's JSON
            structured_content = self._parse_tool_result_content(raw_content)
            if structured_content:
                tool_result["structured_content"] = structured_content
                
                # Extract success/error information
                if "success" in structured_content:
                    tool_result["success"] = structured_content["success"]
                
                if "error" in structured_content:
                    tool_result["error_details"] = structured_content["error"]
        
        return tool_result
    
    def _parse_tool_result_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse tool result content into structured format"""
        
        try:
            # Look for JSON patterns in the content
            json_matches = self.json_content_pattern.findall(content)
            
            for json_str in json_matches:
                try:
                    # Try to parse as JSON
                    parsed = json.loads(json_str)
                    return parsed
                except json.JSONDecodeError:
                    # Try to clean up and parse
                    cleaned = self._clean_json_string(json_str)
                    try:
                        parsed = json.loads(cleaned)
                        return parsed
                    except json.JSONDecodeError:
                        continue
            
            # If no JSON found, try to extract key information manually
            manual_parsed = {}
            
            # Extract success status
            success_match = self.success_pattern.search(content)
            if success_match:
                manual_parsed["success"] = success_match.group(1).lower() == "true"
            
            # Extract error message
            error_match = self.error_pattern.search(content)
            if error_match:
                manual_parsed["error"] = error_match.group(1)
            
            # Extract message if present
            message_match = re.search(r'"message":\s*"([^"]*)"', content)
            if message_match:
                manual_parsed["message"] = message_match.group(1)
            
            return manual_parsed if manual_parsed else None
            
        except Exception as e:
            logger.warning(f"Failed to parse tool result content: {e}")
            return {"parsing_error": str(e)}
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean up malformed JSON strings"""
        
        # Remove common issues
        cleaned = json_str.strip()
        
        # Fix escaped quotes
        cleaned = cleaned.replace('\\"', '"')
        
        # Fix trailing commas
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        
        return cleaned
    
    def _extract_agent_communications(self, content: str) -> List[Dict[str, Any]]:
        """Extract agent communication information"""
        
        communications = []
        
        # Find agent communication patterns
        matches = self.agent_send_pattern.findall(content)
        
        for target_agent in matches:
            communications.append({
                "type": "sendMessage",
                "target_agent": target_agent,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return communications
    
    def _extract_json_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract and parse any JSON content in the message"""
        
        try:
            # Try to parse the entire content as JSON first
            if content.strip().startswith('{') and content.strip().endswith('}'):
                return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Look for JSON blocks within the content
        json_matches = self.json_content_pattern.findall(content)
        
        for json_str in json_matches:
            try:
                parsed = json.loads(json_str)
                return parsed
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _extract_error_information(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract error information from content"""
        
        if "error" not in content.lower():
            return None
        
        error_info = {
            "has_error": True,
            "error_messages": [],
            "error_type": "unknown"
        }
        
        # Extract error messages
        error_matches = self.error_pattern.findall(content)
        error_info["error_messages"] = error_matches
        
        # Classify error type
        content_lower = content.lower()
        if "column" in content_lower and "does not exist" in content_lower:
            error_info["error_type"] = "sql_column_error"
        elif "http 400" in content_lower or "http 404" in content_lower:
            error_info["error_type"] = "http_error"
        elif "failed to execute" in content_lower:
            error_info["error_type"] = "execution_error"
        elif "timeout" in content_lower:
            error_info["error_type"] = "timeout_error"
        
        return error_info
    
    def parse_messages_array(self, messages) -> List[Dict[str, Any]]:
        """Parse an array of messages into structured format"""
        
        if not messages:
            return []
        
        # Handle string representation of messages
        if isinstance(messages, str):
            try:
                messages = json.loads(messages)
            except json.JSONDecodeError:
                logger.warning("Failed to parse messages string as JSON")
                return [{"parsing_error": "Invalid JSON format", "raw_content": messages[:200]}]
        
        parsed_messages = []
        
        if isinstance(messages, list):
            for i, msg in enumerate(messages):
                try:
                    parsed_msg = self._parse_single_message(msg, i)
                    parsed_messages.append(parsed_msg)
                except Exception as e:
                    logger.warning(f"Failed to parse message {i}: {e}")
                    parsed_messages.append({
                        "message_index": i,
                        "parsing_error": str(e),
                        "raw_message": str(msg)[:200] if msg else "None"
                    })
        
        return parsed_messages
    
    def _parse_single_message(self, message, index: int) -> Dict[str, Any]:
        """Parse a single message into structured format"""
        
        parsed = {
            "message_index": index,
            "role": "unknown",
            "content_type": "unknown",
            "parsed_content": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if isinstance(message, dict):
            # Extract role
            parsed["role"] = message.get("role", "unknown")
            
            # Extract and parse content
            content = message.get("content", "")
            if content:
                parsed["content_type"] = self._classify_content_type(str(content))
                parsed["parsed_content"] = self.parse_message_content(str(content))
        
        elif isinstance(message, str):
            # Handle string messages
            parsed["parsed_content"] = self.parse_message_content(message)
            parsed["content_type"] = parsed["parsed_content"].get("type", "unknown")
        
        return parsed