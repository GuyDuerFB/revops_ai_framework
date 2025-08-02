"""
System prompt deduplication for conversation tracking
Reduces storage by 60-80% by extracting and referencing system prompts
"""

import hashlib
import json
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PromptReference:
    prompt_id: str
    prompt_hash: str
    prompt_length: int
    first_seen: str
    usage_count: int = 0

class PromptDeduplicator:
    """Handles deduplication of system prompts in Bedrock traces"""
    
    def __init__(self, max_cache_size: int = 100):
        self.prompt_cache: Dict[str, PromptReference] = {}
        self.prompt_store: Dict[str, str] = {}  # prompt_id -> full_prompt
        self.max_cache_size = max_cache_size
        self.logger = logging.getLogger(__name__)
    
    def process_trace_content(self, trace_content) -> Tuple[any, Optional[str]]:
        """Process trace content and return deduplicated version + prompt_id"""
        
        if not trace_content.modelInvocationInput:
            return trace_content, None
        
        # Step 1: Extract system prompt
        extracted = self._extract_system_prompt(trace_content.modelInvocationInput)
        if not extracted:
            return trace_content, None
        
        system_prompt, remaining_input = extracted
        
        # Step 2: Generate/get prompt ID
        prompt_id = self._cache_prompt(system_prompt)
        
        # Step 3: Create deduplicated trace content
        # Import BedrockTraceContent here to avoid circular imports
        from conversation_schema import BedrockTraceContent
        
        # Replace the placeholder with actual prompt_id
        remaining_input = remaining_input.replace('"system_prompt_ref":"PLACEHOLDER"', f'"system_prompt_ref":"{prompt_id}"')
        
        deduplicated_trace = BedrockTraceContent(
            modelInvocationInput=remaining_input,
            invocationInput=trace_content.invocationInput,
            actionGroupInvocationInput=trace_content.actionGroupInvocationInput,
            observation=trace_content.observation,
            raw_trace_data=trace_content.raw_trace_data
        )
        
        return deduplicated_trace, prompt_id
    
    def filter_system_prompts_from_messages(self, messages_data) -> Tuple[any, bool]:
        """Filter system prompts from messages array - main source of leakage"""
        
        if not messages_data:
            return messages_data, False
        
        filtered_messages = []
        system_prompts_found = False
        
        # Handle different message formats
        if isinstance(messages_data, list):
            for message in messages_data:
                filtered_msg, had_system = self._filter_message_content(message)
                if filtered_msg:  # Only add non-empty messages
                    filtered_messages.append(filtered_msg)
                system_prompts_found = system_prompts_found or had_system
        elif isinstance(messages_data, dict):
            # Single message format
            filtered_msg, had_system = self._filter_message_content(messages_data)
            if filtered_msg:
                filtered_messages = filtered_msg
            system_prompts_found = had_system
        else:
            # String format - check if it's a system prompt
            if self._is_system_prompt_content(str(messages_data)):
                self.logger.info("Filtered out system prompt from string message content")
                return None, True
            filtered_messages = messages_data
        
        return filtered_messages, system_prompts_found
    
    def _filter_message_content(self, message) -> Tuple[any, bool]:
        """Filter system prompts from individual message"""
        
        if not message:
            return message, False
        
        system_prompt_found = False
        
        # Handle string message content
        if isinstance(message, str):
            if self._is_system_prompt_content(message):
                self.logger.info("Filtered out system prompt from string message")
                return None, True
            return message, False
        
        # Handle dict message format
        if isinstance(message, dict):
            filtered_message = {}
            
            for key, value in message.items():
                # Check for system role
                if key == "role" and value == "system":
                    system_prompt_found = True
                    continue
                
                # Check content field for system prompts
                if key == "content" and isinstance(value, str):
                    if self._is_system_prompt_content(value):
                        system_prompt_found = True
                        self.logger.info(f"Filtered out system prompt from message content (size: {len(value)})")
                        continue
                
                # Check for nested system prompts in JSON content
                if key == "content" and isinstance(value, str) and value.startswith("{"):
                    try:
                        content_data = json.loads(value)
                        if isinstance(content_data, dict) and "system" in content_data:
                            system_prompt_text = content_data["system"]
                            if self._is_system_prompt_content(system_prompt_text):
                                system_prompt_found = True
                                self.logger.info(f"Filtered out nested system prompt (size: {len(system_prompt_text)})")
                                # Remove system prompt from nested JSON
                                del content_data["system"]
                                if content_data:  # If there's still content left
                                    filtered_message[key] = json.dumps(content_data)
                                continue
                    except json.JSONDecodeError:
                        pass  # Not JSON, treat as regular content
                
                # Keep non-system content
                filtered_message[key] = value
            
            # Return None if entire message was system prompt
            if not filtered_message and system_prompt_found:
                return None, True
            
            return filtered_message if filtered_message else message, system_prompt_found
        
        return message, False
    
    def _is_system_prompt_content(self, content: str) -> bool:
        """Detect if content is a system prompt"""
        
        if not content or len(content) < 100:  # Too short to be a system prompt
            return False
        
        # System prompt indicators
        system_indicators = [
            "# Manager Agent Instructions",
            "# Data Analysis Agent Instructions", 
            "## Agent Purpose",
            "You are the **Manager Agent**",
            "You are the Data Analysis Agent",
            "## Your Role as SUPERVISOR",
            "Agent Collaboration Architecture",
            "## Agent Purpose You are the",
            "RevOps AI Framework",
            "## Core Capabilities",
            "ALWAYS follow these additional guidelines",
            "You MUST follow these additional guidelines"
        ]
        
        # Size-based detection (system prompts are typically very large)
        if len(content) > 5000:
            # Check for multiple system prompt indicators
            indicator_count = sum(1 for indicator in system_indicators if indicator in content)
            if indicator_count >= 2:
                return True
        
        # Content pattern detection
        if len(content) > 1000:
            for indicator in system_indicators:
                if indicator in content:
                    return True
        
        # JSON system field detection  
        if content.strip().startswith('{"system":'):
            return True
            
        return False
    
    def _extract_system_prompt(self, model_input: str) -> Optional[Tuple[str, str]]:
        """Extract system prompt from modelInvocationInput JSON"""
        try:
            input_data = json.loads(model_input)
            
            if 'system' in input_data:
                system_prompt = input_data['system']
                
                # Remove system prompt and add reference
                input_data['system_prompt_ref'] = "PLACEHOLDER"  # Will be replaced
                del input_data['system']
                
                remaining_input = json.dumps(input_data, separators=(',', ':'))
                return system_prompt, remaining_input
                
            return None
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to extract system prompt: {e}")
            return None
    
    def _generate_prompt_id(self, prompt_text: str) -> str:
        """Generate unique ID for system prompt"""
        # Create hash of the prompt text
        prompt_hash = hashlib.md5(prompt_text.encode('utf-8')).hexdigest()
        # Use first 8 chars for brevity
        return f"prompt_{prompt_hash[:8]}"
    
    def _cache_prompt(self, prompt_text: str) -> str:
        """Cache prompt and return prompt_id"""
        prompt_hash = hashlib.md5(prompt_text.encode('utf-8')).hexdigest()
        
        # Check if prompt already exists
        for ref in self.prompt_cache.values():
            if ref.prompt_hash == prompt_hash:
                ref.usage_count += 1
                return ref.prompt_id
        
        # Generate new prompt ID
        prompt_id = self._generate_prompt_id(prompt_text)
        
        # Handle cache size limit
        if len(self.prompt_cache) >= self.max_cache_size:
            # Remove least used prompt
            least_used_id = min(self.prompt_cache.keys(), 
                              key=lambda k: self.prompt_cache[k].usage_count)
            del self.prompt_cache[least_used_id]
            del self.prompt_store[least_used_id]
        
        # Store prompt
        from datetime import datetime
        self.prompt_cache[prompt_id] = PromptReference(
            prompt_id=prompt_id,
            prompt_hash=prompt_hash,
            prompt_length=len(prompt_text),
            first_seen=datetime.utcnow().isoformat(),
            usage_count=1
        )
        self.prompt_store[prompt_id] = prompt_text
        
        self.logger.info(f"Cached new prompt {prompt_id} (length: {len(prompt_text)})")
        return prompt_id
    
    def get_prompt_by_id(self, prompt_id: str) -> Optional[str]:
        """Retrieve full prompt by ID"""
        return self.prompt_store.get(prompt_id)
    
    def get_cache_stats(self) -> Dict:
        """Get deduplication statistics"""
        total_usage = sum(ref.usage_count for ref in self.prompt_cache.values())
        total_original_size = sum(ref.prompt_length * ref.usage_count for ref in self.prompt_cache.values())
        total_deduplicated_size = sum(ref.prompt_length for ref in self.prompt_cache.values())
        
        return {
            "unique_prompts": len(self.prompt_cache),
            "total_usage_count": total_usage,
            "original_size_bytes": total_original_size,
            "deduplicated_size_bytes": total_deduplicated_size,
            "compression_ratio": (1 - total_deduplicated_size / total_original_size) if total_original_size > 0 else 0,
            "average_prompt_length": sum(ref.prompt_length for ref in self.prompt_cache.values()) / len(self.prompt_cache) if self.prompt_cache else 0
        }