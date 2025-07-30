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