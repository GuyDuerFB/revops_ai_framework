"""
User Query Extractor
Standardizes user query extraction across Slack and API conversations
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractedQuery:
    """Standardized extracted user query"""
    query_text: str
    extraction_method: str
    confidence_score: float
    query_intent: Optional[str]
    source_field: str
    cleaned_query: str
    query_length: int
    extraction_timestamp: str

class UserQueryExtractor:
    """Standardized user query extraction for all conversation types"""
    
    def __init__(self):
        # Query field priorities for different sources
        self.slack_field_priorities = [
            'user_query',
            'text', 
            'message',
            'input_text',
            'original_message',
            'user_input'
        ]
        
        self.api_field_priorities = [
            'user_message',
            'message',
            'query',
            'input',
            'question',
            'text',
            'prompt',
            'request'
        ]
        
        self.reasoning_extraction_patterns = [
            r'user_request["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'user.{0,20}query["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'question["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'\[USER\]\s*\n(.*?)(?=\n\[|$)',
            r'User.{0,10}(?:asked|requesting|wants)[:\s]+(.*?)(?=\.|$)',
            r'(?:please|can you|could you|help me)\s+(.*?)(?:[.!?]|$)',
        ]
        
        # Intent classification patterns
        self.intent_patterns = {
            'data_analysis': [
                r'analyz[e|ing]',
                r'data.*report',
                r'show me.*data',
                r'query.*database',
                r'sql.*query',
                r'numbers?.*for',
                r'metrics?',
                r'performance',
                r'revenue',
                r'conversion'
            ],
            'deal_analysis': [
                r'deal[s]?',
                r'opportunit[y|ies]',
                r'pipeline',
                r'sales.*analysis',
                r'meddpicc',
                r'qualification',
                r'competitive',
                r'win.*rate',
                r'close.*rate'
            ],
            'lead_analysis': [
                r'lead[s]?',
                r'prospect[s]?',
                r'contact[s]?',
                r'lead.*scoring',
                r'qualification',
                r'disqualification',
                r'lead.*conversion'
            ],
            'general_inquiry': [
                r'what.*is',
                r'how.*do',
                r'can.*you',
                r'explain',
                r'help.*me',
                r'information.*about',
                r'tell.*me'
            ],
            'status_check': [
                r'status',
                r'progress',
                r'update',
                r'summary',
                r'current.*state',
                r'what.*happened'
            ]
        }
        
        # Query cleaning patterns
        self.cleaning_patterns = [
            (r'\s+', ' '),  # Multiple spaces to single
            (r'^\s*[\[\(].*?[\]\)]\s*', ''),  # Remove bracketed prefixes
            (r'^["\']|["\']$', ''),  # Remove quotes
            (r'^\s*[-*•]\s*', ''),  # Remove bullet points
            (r'^\s*\d+\.\s*', ''),  # Remove numbered list prefixes
            (r'\s*[}]?\s*$', ''),  # Remove trailing artifacts
        ]
    
    def extract_user_query_from_conversation(self, conversation_data: Dict[str, Any]) -> ExtractedQuery:
        """Extract user query from any conversation format"""
        
        # Determine conversation source type
        export_metadata = conversation_data.get('export_metadata', {})
        source_type = export_metadata.get('source', 'unknown')
        
        if source_type == 'slack' or 'slack' in str(conversation_data).lower():
            return self._extract_from_slack_conversation(conversation_data)
        elif source_type == 'http_api' or 'api' in str(conversation_data).lower():
            return self._extract_from_api_conversation(conversation_data)
        else:
            return self._extract_from_generic_conversation(conversation_data)
    
    def _extract_from_slack_conversation(self, conversation_data: Dict[str, Any]) -> ExtractedQuery:
        """Extract user query from Slack conversation"""
        
        conversation = conversation_data.get('conversation', {})
        
        # Method 1: Direct field extraction
        for field in self.slack_field_priorities:
            if field in conversation and conversation[field]:
                query_text = str(conversation[field]).strip()
                if len(query_text) > 5:  # Minimum viable query length
                    return self._create_extracted_query(
                        query_text, 'direct_field_extraction', 0.9, field
                    )
        
        # Method 2: Metadata extraction
        metadata = conversation.get('metadata', {})
        for field in self.slack_field_priorities:
            if field in metadata and metadata[field]:
                query_text = str(metadata[field]).strip()
                if len(query_text) > 5:
                    return self._create_extracted_query(
                        query_text, 'metadata_extraction', 0.8, f'metadata.{field}'
                    )
        
        # Method 3: Agent flow reasoning extraction
        agent_flow = conversation.get('agent_flow', [])
        if agent_flow:
            reasoning_query = self._extract_from_reasoning_breakdown(agent_flow[0])
            if reasoning_query:
                return reasoning_query
        
        # Method 4: Function audit extraction
        function_audit = conversation.get('function_audit', {})
        if 'user_query' in function_audit and function_audit['user_query']:
            query_text = str(function_audit['user_query']).strip()
            if len(query_text) > 5:
                return self._create_extracted_query(
                    query_text, 'function_audit_extraction', 0.7, 'function_audit.user_query'
                )
        
        # Fallback: Generate query from context
        return self._generate_fallback_query(conversation_data, 'slack')
    
    def _extract_from_api_conversation(self, conversation_data: Dict[str, Any]) -> ExtractedQuery:
        """Extract user query from API conversation"""
        
        conversation = conversation_data.get('conversation', {})
        
        # Method 1: API metadata extraction
        api_metadata = conversation.get('api_metadata', {})
        if 'user_query' in api_metadata and api_metadata['user_query']:
            query_text = str(api_metadata['user_query']).strip()
            if len(query_text) > 5:
                return self._create_extracted_query(
                    query_text, 'api_metadata_extraction', 0.9, 'api_metadata.user_query'
                )
        
        # Method 2: Direct conversation field extraction
        for field in self.api_field_priorities:
            if field in conversation and conversation[field]:
                query_text = str(conversation[field]).strip()
                if len(query_text) > 5:
                    return self._create_extracted_query(
                        query_text, 'direct_field_extraction', 0.9, field
                    )
        
        # Method 3: Function audit API trace events
        function_audit = conversation.get('function_audit', {})
        api_trace_events = function_audit.get('api_trace_events', [])
        for event in api_trace_events:
            if event.get('event_type') == 'agent_invocation_started':
                details = event.get('details', {})
                if 'user_message' in details:
                    return self._create_extracted_query(
                        details['user_message'], 'api_trace_extraction', 0.8, 'api_trace_events'
                    )
        
        # Method 4: Agent flow reasoning extraction  
        agent_flow = conversation.get('agent_flow', [])
        if agent_flow:
            reasoning_query = self._extract_from_reasoning_breakdown(agent_flow[0])
            if reasoning_query:
                return reasoning_query
        
        # Fallback: Generate query from context
        return self._generate_fallback_query(conversation_data, 'api')
    
    def _extract_from_generic_conversation(self, conversation_data: Dict[str, Any]) -> ExtractedQuery:
        """Extract user query from generic conversation format"""
        
        conversation = conversation_data.get('conversation', {})
        
        # Try all common field names
        all_field_priorities = list(set(self.slack_field_priorities + self.api_field_priorities))
        
        for field in all_field_priorities:
            if field in conversation and conversation[field]:
                query_text = str(conversation[field]).strip()
                if len(query_text) > 5:
                    return self._create_extracted_query(
                        query_text, 'generic_field_extraction', 0.7, field
                    )
        
        # Try agent flow
        agent_flow = conversation.get('agent_flow', [])
        if agent_flow:
            reasoning_query = self._extract_from_reasoning_breakdown(agent_flow[0])
            if reasoning_query:
                return reasoning_query
        
        # Fallback
        return self._generate_fallback_query(conversation_data, 'generic')
    
    def _extract_from_reasoning_breakdown(self, first_step: Dict[str, Any]) -> Optional[ExtractedQuery]:
        """Extract user query from reasoning breakdown"""
        
        reasoning_breakdown = first_step.get('reasoning_breakdown', {})
        
        # Check context_setup first
        context_setup = reasoning_breakdown.get('context_setup', {})
        if 'user_request' in context_setup and context_setup['user_request']:
            query_text = str(context_setup['user_request']).strip()
            # Clean common artifacts
            query_text = re.sub(r'^["\']|["\']$', '', query_text)
            query_text = re.sub(r'[}]?\s*$', '', query_text)
            
            if len(query_text) > 5:
                return self._create_extracted_query(
                    query_text, 'reasoning_context_extraction', 0.8, 'reasoning_breakdown.context_setup.user_request'
                )
        
        # Check reasoning_text with patterns
        reasoning_text = first_step.get('reasoning_text', '')
        if reasoning_text:
            for pattern in self.reasoning_extraction_patterns:
                match = re.search(pattern, reasoning_text, re.IGNORECASE | re.DOTALL)
                if match:
                    query_text = match.group(1).strip()
                    if len(query_text) > 5:
                        return self._create_extracted_query(
                            query_text, 'reasoning_pattern_extraction', 0.7, 'reasoning_text'
                        )
        
        return None
    
    def _create_extracted_query(
        self, 
        raw_query: str, 
        method: str, 
        confidence: float, 
        source_field: str
    ) -> ExtractedQuery:
        """Create standardized extracted query object"""
        
        # Clean the query
        cleaned_query = self._clean_query(raw_query)
        
        # Classify intent
        intent = self._classify_query_intent(cleaned_query)
        
        return ExtractedQuery(
            query_text=raw_query,
            extraction_method=method,
            confidence_score=confidence,
            query_intent=intent,
            source_field=source_field,
            cleaned_query=cleaned_query,
            query_length=len(cleaned_query),
            extraction_timestamp=datetime.utcnow().isoformat()
        )
    
    def _clean_query(self, raw_query: str) -> str:
        """Clean and normalize user query"""
        
        cleaned = raw_query.strip()
        
        # Apply cleaning patterns
        for pattern, replacement in self.cleaning_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # Remove common conversation artifacts
        cleaned = re.sub(r'^(user|human|question|query|request):\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^\s*[>-]\s*', '', cleaned)  # Remove quote/dash prefixes
        
        # Ensure first letter is capitalized
        if cleaned and not cleaned[0].isupper():
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        # Ensure proper ending punctuation
        if cleaned and cleaned[-1] not in '.!?':
            cleaned += '.'
        
        return cleaned.strip()
    
    def _classify_query_intent(self, query: str) -> Optional[str]:
        """Classify user query intent"""
        
        query_lower = query.lower()
        intent_scores = {}
        
        # Score each intent category
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            
            if score > 0:
                intent_scores[intent] = score / len(patterns)  # Normalize by pattern count
        
        # Return highest scoring intent if above threshold
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            if best_intent[1] >= 0.1:  # At least 10% of patterns matched
                return best_intent[0]
        
        return None
    
    def _generate_fallback_query(self, conversation_data: Dict[str, Any], source_type: str) -> ExtractedQuery:
        """Generate fallback query when extraction fails"""
        
        conversation = conversation_data.get('conversation', {})
        
        # Try to construct from available metadata
        fallback_elements = []
        
        # Add source information
        if source_type == 'slack':
            channel = conversation.get('channel', 'unknown_channel')
            fallback_elements.append(f"Slack message from {channel}")
        elif source_type == 'api':
            api_metadata = conversation.get('api_metadata', {})
            endpoint = api_metadata.get('api_endpoint', 'unknown_endpoint')
            fallback_elements.append(f"API request to {endpoint}")
        
        # Add timing context
        start_timestamp = conversation.get('start_timestamp', '')
        if start_timestamp:
            try:
                dt = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
                fallback_elements.append(f"at {dt.strftime('%Y-%m-%d %H:%M UTC')}")
            except:
                pass
        
        # Add agent involvement
        agents_involved = conversation.get('agents_involved', [])
        if agents_involved:
            agents_str = ', '.join(agents_involved[:3])  # Limit to first 3
            if len(agents_involved) > 3:
                agents_str += f" and {len(agents_involved) - 3} more"
            fallback_elements.append(f"involving {agents_str}")
        
        # Add processing context
        agent_flow = conversation.get('agent_flow', [])
        if agent_flow:
            tools_used = []
            for step in agent_flow[:3]:  # Check first 3 steps
                step_tools = step.get('tools_used', [])
                for tool in step_tools[:2]:  # Max 2 tools per step
                    tool_name = tool.get('tool_name', 'unknown')
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)
            
            if tools_used:
                tools_str = ', '.join(tools_used)
                fallback_elements.append(f"using tools: {tools_str}")
        
        # Construct fallback query
        if fallback_elements:
            fallback_query = "User interaction: " + ", ".join(fallback_elements) + "."
        else:
            fallback_query = f"User interaction via {source_type} interface."
        
        return ExtractedQuery(
            query_text=fallback_query,
            extraction_method='fallback_generation',
            confidence_score=0.3,
            query_intent='general_inquiry',
            source_field='generated_from_context',
            cleaned_query=fallback_query,
            query_length=len(fallback_query),
            extraction_timestamp=datetime.utcnow().isoformat()
        )
    
    def standardize_conversation_query_field(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize user_query field across all conversation formats"""
        
        # Extract query
        extracted_query = self.extract_user_query_from_conversation(conversation_data)
        
        # Update conversation data
        if 'conversation' not in conversation_data:
            conversation_data['conversation'] = {}
        
        conversation = conversation_data['conversation']
        
        # Set standardized user_query field
        conversation['user_query'] = extracted_query.cleaned_query
        
        # Add extraction metadata
        conversation['user_query_extraction'] = {
            'original_query': extracted_query.query_text,
            'extraction_method': extracted_query.extraction_method,
            'confidence_score': extracted_query.confidence_score,
            'query_intent': extracted_query.query_intent,
            'source_field': extracted_query.source_field,
            'query_length': extracted_query.query_length,
            'extraction_timestamp': extracted_query.extraction_timestamp
        }
        
        # Update metadata if exists
        if 'metadata' in conversation:
            conversation['metadata']['user_query'] = extracted_query.cleaned_query
        
        # Add to export metadata
        if 'export_metadata' not in conversation_data:
            conversation_data['export_metadata'] = {}
        
        conversation_data['export_metadata']['user_query_standardization'] = {
            'applied': True,
            'extraction_method': extracted_query.extraction_method,
            'confidence_score': extracted_query.confidence_score,
            'query_intent': extracted_query.query_intent
        }
        
        logger.info(f"Standardized user query: '{extracted_query.cleaned_query}' (method: {extracted_query.extraction_method}, confidence: {extracted_query.confidence_score})")
        
        return conversation_data