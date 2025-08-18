"""
Response Content Parser
Standardizes final response extraction and parsing from JSON containers
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ResponseFormat(Enum):
    JSON_CONTAINER = "json_container"
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    STRUCTURED_DATA = "structured_data"
    ERROR_RESPONSE = "error_response"
    MIXED_FORMAT = "mixed_format"

@dataclass
class ParsedResponse:
    """Parsed and standardized response content"""
    content: str
    format_type: ResponseFormat
    parsing_method: str
    confidence_score: float
    response_quality_score: float
    content_length: int
    contains_data: bool
    contains_analysis: bool
    contains_error: bool
    structured_elements: Dict[str, Any]
    metadata: Dict[str, Any]
    parsing_timestamp: str

class ResponseContentParser:
    """Parses and standardizes final response content"""
    
    def __init__(self):
        # JSON container patterns
        self.json_container_patterns = [
            r'^\s*\{\s*"[^"]+"\s*:\s*".*"\s*\}\s*$',
            r'^\s*\{\s*"status"\s*:\s*"[^"]+".*\}\s*$',
            r'^\s*\{\s*"response"\s*:\s*".*"\s*\}\s*$',
            r'^\s*\{\s*"message"\s*:\s*".*"\s*\}\s*$',
            r'^\s*\{\s*"content"\s*:\s*".*"\s*\}\s*$'
        ]
        
        # Response field priorities for content extraction
        self.content_field_priorities = [
            'content',
            'message', 
            'response',
            'text',
            'result',
            'answer',
            'output',
            'data',
            'payload'
        ]
        
        # Quality indicators
        self.quality_indicators = {
            'high_quality': [
                r'based on.*analysis',
                r'according to.*data',
                r'the results show',
                r'analysis reveals',
                r'key findings',
                r'recommendations?',
                r'summary:',
                r'conclusion:',
                r'\d+%',  # Percentages
                r'\$[\d,]+',  # Dollar amounts
                r'\d{4}-\d{2}-\d{2}',  # Dates
                r'(increase|decrease|growth|decline).*\d+',
                r'compared to',
                r'year over year',
                r'month over month'
            ],
            'low_quality': [
                r'^(ok|okay|yes|no)\.?$',
                r'^(sure|alright)\.?$',
                r'^error',
                r'something went wrong',
                r'try again',
                r'i don\'t (know|understand)',
                r'not available',
                r'no data found',
                r'unable to'
            ]
        }
        
        # Content type detection patterns
        self.content_type_patterns = {
            'data_analysis': [
                r'(revenue|sales|mrr|arr)',
                r'(customer|client|account)',
                r'(conversion|pipeline|funnel)',
                r'(metric|kpi|performance)',
                r'(growth|decline|trend)',
                r'(quarter|month|year)',
                r'\d+%',
                r'\$[\d,]+',
                r'(increase|decrease).*\d+'
            ],
            'deal_analysis': [
                r'(deal|opportunity|pipeline)',
                r'(meddpicc|qualification)',
                r'(competitive|competitor)',
                r'(stage|status)',
                r'(win rate|close rate)',
                r'(forecast|projection)',
                r'(proposal|quote)'
            ],
            'lead_analysis': [
                r'(lead|prospect|contact)',
                r'(scoring|qualification)',
                r'(disqualification|disqualified)',
                r'(conversion|nurturing)',
                r'(source|campaign)',
                r'(mql|sql|opportunity)'
            ],
            'error_content': [
                r'error',
                r'failed',
                r'exception',
                r'timeout',
                r'unavailable',
                r'not found',
                r'unable to'
            ]
        }
        
        # Structured element patterns
        self.structured_patterns = {
            'bullet_points': r'^[-*•]\s+(.+)$',
            'numbered_lists': r'^\d+\.\s+(.+)$',
            'headers': r'^#+\s+(.+)$',
            'key_value_pairs': r'^([^:]+):\s*(.+)$',
            'percentages': r'(\d+(?:\.\d+)?%)',
            'dollar_amounts': r'(\$[\d,]+(?:\.\d{2})?)',
            'dates': r'(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})',
            'metrics': r'(increase|decrease|growth|decline|up|down)\s*(?:by\s*)?(\d+(?:\.\d+)?%?)'
        }
    
    def parse_final_response(self, raw_response: str, conversation_context: Optional[Dict[str, Any]] = None) -> ParsedResponse:
        """Parse and standardize final response content"""
        
        if not raw_response:
            return self._create_empty_response()
        
        # Detect response format
        format_type = self._detect_response_format(raw_response)
        
        # Extract content based on format
        if format_type == ResponseFormat.JSON_CONTAINER:
            content, method, confidence = self._extract_from_json_container(raw_response)
        elif format_type == ResponseFormat.STRUCTURED_DATA:
            content, method, confidence = self._extract_from_structured_data(raw_response)
        elif format_type == ResponseFormat.ERROR_RESPONSE:
            content, method, confidence = self._extract_from_error_response(raw_response)
        else:
            content, method, confidence = self._extract_from_plain_text(raw_response)
        
        # Calculate quality score
        quality_score = self._calculate_response_quality(content, conversation_context)
        
        # Detect content characteristics
        contains_data = self._contains_data_elements(content)
        contains_analysis = self._contains_analysis_elements(content)
        contains_error = self._contains_error_elements(content)
        
        # Extract structured elements
        structured_elements = self._extract_structured_elements(content)
        
        # Create metadata
        metadata = self._create_response_metadata(raw_response, content, conversation_context)
        
        return ParsedResponse(
            content=content,
            format_type=format_type,
            parsing_method=method,
            confidence_score=confidence,
            response_quality_score=quality_score,
            content_length=len(content),
            contains_data=contains_data,
            contains_analysis=contains_analysis,
            contains_error=contains_error,
            structured_elements=structured_elements,
            metadata=metadata,
            parsing_timestamp=datetime.utcnow().isoformat()
        )
    
    def _detect_response_format(self, response: str) -> ResponseFormat:
        """Detect the format of the response"""
        
        response_stripped = response.strip()
        
        # Check for JSON container
        for pattern in self.json_container_patterns:
            if re.match(pattern, response_stripped, re.DOTALL):
                return ResponseFormat.JSON_CONTAINER
        
        # Check if it's valid JSON at all
        try:
            json.loads(response_stripped)
            return ResponseFormat.STRUCTURED_DATA
        except json.JSONDecodeError:
            pass
        
        # Check for error indicators
        if any(indicator in response.lower() for indicator in ['error', 'failed', 'exception', 'timeout']):
            return ResponseFormat.ERROR_RESPONSE
        
        # Check for markdown elements
        if any(indicator in response for indicator in ['##', '**', '*', '```', '1.', '-']):
            return ResponseFormat.MARKDOWN
        
        return ResponseFormat.PLAIN_TEXT
    
    def _extract_from_json_container(self, response: str) -> Tuple[str, str, float]:
        """Extract content from JSON container format"""
        
        try:
            response_data = json.loads(response.strip())
            
            if isinstance(response_data, dict):
                # Try priority fields for content extraction
                for field in self.content_field_priorities:
                    if field in response_data and response_data[field]:
                        content = str(response_data[field])
                        
                        # Clean up escaped characters
                        content = content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                        
                        return content.strip(), 'json_field_extraction', 0.9
                
                # If no priority fields, try to reconstruct from all non-metadata fields
                content_parts = []
                metadata_fields = ['status', 'correlation_id', 'processing_time_ms', 'timestamp', 'response_sent']
                
                for key, value in response_data.items():
                    if key not in metadata_fields and value:
                        if isinstance(value, (str, int, float)):
                            content_parts.append(f"{key}: {value}")
                        elif isinstance(value, (list, dict)):
                            content_parts.append(f"{key}: {json.dumps(value, indent=2)}")
                
                if content_parts:
                    return '\n'.join(content_parts), 'json_reconstruction', 0.7
            
            # Fallback: return the entire JSON as formatted string
            return json.dumps(response_data, indent=2), 'json_fallback', 0.5
            
        except json.JSONDecodeError:
            # Not valid JSON despite pattern match
            return response.strip(), 'json_parse_failed', 0.3
    
    def _extract_from_structured_data(self, response: str) -> Tuple[str, str, float]:
        """Extract content from structured JSON data"""
        
        try:
            response_data = json.loads(response.strip())
            
            # Format structured data nicely
            if isinstance(response_data, dict):
                formatted_parts = []
                
                for key, value in response_data.items():
                    if isinstance(value, (list, dict)):
                        formatted_parts.append(f"## {key.title()}")
                        formatted_parts.append(json.dumps(value, indent=2))
                    else:
                        formatted_parts.append(f"**{key.title()}**: {value}")
                
                return '\n\n'.join(formatted_parts), 'structured_formatting', 0.8
            
            elif isinstance(response_data, list):
                formatted_items = []
                for i, item in enumerate(response_data):
                    formatted_items.append(f"{i+1}. {json.dumps(item, indent=2) if isinstance(item, (dict, list)) else item}")
                
                return '\n'.join(formatted_items), 'list_formatting', 0.8
            
            else:
                return str(response_data), 'simple_value', 0.9
                
        except json.JSONDecodeError:
            return response.strip(), 'structured_parse_failed', 0.4
    
    def _extract_from_error_response(self, response: str) -> Tuple[str, str, float]:
        """Extract content from error response"""
        
        # Try to parse as JSON first
        try:
            error_data = json.loads(response.strip())
            if isinstance(error_data, dict):
                error_fields = ['error', 'message', 'error_message', 'details', 'description']
                for field in error_fields:
                    if field in error_data and error_data[field]:
                        return f"Error: {error_data[field]}", 'error_field_extraction', 0.8
        except json.JSONDecodeError:
            pass
        
        # Extract error from plain text
        lines = response.strip().split('\n')
        error_content = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('{') and not line.endswith('}'):
                error_content.append(line)
        
        if error_content:
            return '\n'.join(error_content), 'error_text_extraction', 0.6
        
        return response.strip(), 'error_fallback', 0.4
    
    def _extract_from_plain_text(self, response: str) -> Tuple[str, str, float]:
        """Extract content from plain text response"""
        
        content = response.strip()
        
        # Clean up common artifacts
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        content = re.sub(r'^["\']+|["\']+$', '', content)  # Remove surrounding quotes
        
        # Check if it's mostly readable content
        if len(content) > 10 and not content.startswith('{'):
            return content, 'plain_text_extraction', 0.8
        
        return content, 'plain_text_fallback', 0.5
    
    def _calculate_response_quality(self, content: str, context: Optional[Dict[str, Any]]) -> float:
        """Calculate response quality score"""
        
        score = 0.5  # Base score
        content_lower = content.lower()
        
        # High quality indicators
        high_quality_matches = 0
        for pattern in self.quality_indicators['high_quality']:
            if re.search(pattern, content_lower):
                high_quality_matches += 1
        
        if high_quality_matches > 0:
            score += min(high_quality_matches * 0.1, 0.4)  # Max 0.4 from high quality
        
        # Low quality penalties
        low_quality_matches = 0
        for pattern in self.quality_indicators['low_quality']:
            if re.search(pattern, content_lower):
                low_quality_matches += 1
        
        if low_quality_matches > 0:
            score -= min(low_quality_matches * 0.2, 0.4)  # Max 0.4 penalty
        
        # Length-based quality
        if len(content) > 500:
            score += 0.1  # Comprehensive responses
        elif len(content) < 50:
            score -= 0.1  # Very short responses
        
        # Context relevance (if conversation context provided)
        if context:
            user_query = context.get('user_query', '').lower()
            if user_query and len(user_query) > 10:
                # Check if response addresses query terms
                query_words = set(re.findall(r'\w+', user_query))
                content_words = set(re.findall(r'\w+', content_lower))
                
                overlap = len(query_words.intersection(content_words))
                relevance_score = overlap / len(query_words) if query_words else 0
                score += relevance_score * 0.2  # Max 0.2 from relevance
        
        return max(0.0, min(1.0, score))
    
    def _contains_data_elements(self, content: str) -> bool:
        """Check if response contains data elements"""
        
        content_lower = content.lower()
        
        # Check for data indicators
        data_indicators = [
            r'\d+%',  # Percentages
            r'\$[\d,]+',  # Dollar amounts
            r'\d{4}-\d{2}-\d{2}',  # Dates
            r'(revenue|sales|conversion|growth|rate)',
            r'(total|count|number|amount)',
            r'(increase|decrease|up|down).*\d+',
            r'compared to',
            r'vs\.?\s',
            r'year over year',
            r'month over month'
        ]
        
        for pattern in data_indicators:
            if re.search(pattern, content_lower):
                return True
        
        return False
    
    def _contains_analysis_elements(self, content: str) -> bool:
        """Check if response contains analysis elements"""
        
        content_lower = content.lower()
        
        # Check for analysis indicators
        analysis_indicators = [
            r'analysis',
            r'findings?',
            r'results? show',
            r'indicates?',
            r'reveals?',
            r'suggests?',
            r'conclusions?',
            r'recommendations?',
            r'insights?',
            r'trends?',
            r'patterns?',
            r'based on',
            r'according to',
            r'the data shows',
            r'key takeaways?'
        ]
        
        for pattern in analysis_indicators:
            if re.search(pattern, content_lower):
                return True
        
        return False
    
    def _contains_error_elements(self, content: str) -> bool:
        """Check if response contains error elements"""
        
        content_lower = content.lower()
        
        error_indicators = [
            r'error',
            r'failed',
            r'exception',
            r'timeout',
            r'unable to',
            r'not available',
            r'not found',
            r'something went wrong',
            r'try again',
            r'unavailable'
        ]
        
        for pattern in error_indicators:
            if re.search(pattern, content_lower):
                return True
        
        return False
    
    def _extract_structured_elements(self, content: str) -> Dict[str, Any]:
        """Extract structured elements from content"""
        
        elements = {
            'bullet_points': [],
            'numbered_lists': [],
            'headers': [],
            'key_value_pairs': [],
            'percentages': [],
            'dollar_amounts': [],
            'dates': [],
            'metrics': []
        }
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Extract different structured elements
            for element_type, pattern in self.structured_patterns.items():
                matches = re.findall(pattern, line)
                if matches:
                    if element_type in ['bullet_points', 'numbered_lists', 'headers', 'key_value_pairs']:
                        elements[element_type].extend([match[0] if isinstance(match, tuple) else match for match in matches])
                    else:
                        elements[element_type].extend([match if isinstance(match, str) else str(match) for match in matches])
        
        # Remove empty elements
        elements = {k: v for k, v in elements.items() if v}
        
        return elements
    
    def _create_response_metadata(self, raw_response: str, parsed_content: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create response metadata"""
        
        metadata = {
            'original_length': len(raw_response),
            'parsed_length': len(parsed_content),
            'compression_ratio': len(parsed_content) / len(raw_response) if raw_response else 1.0,
            'content_type': self._classify_content_type(parsed_content),
            'complexity_score': self._calculate_complexity_score(parsed_content)
        }
        
        # Add context-based metadata
        if context:
            metadata['context_relevance'] = self._calculate_context_relevance(parsed_content, context)
        
        return metadata
    
    def _classify_content_type(self, content: str) -> Optional[str]:
        """Classify content type based on patterns"""
        
        content_lower = content.lower()
        type_scores = {}
        
        for content_type, patterns in self.content_type_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    score += 1
            
            if score > 0:
                type_scores[content_type] = score / len(patterns)
        
        if type_scores:
            best_type = max(type_scores.items(), key=lambda x: x[1])
            if best_type[1] >= 0.2:  # At least 20% of patterns matched
                return best_type[0]
        
        return None
    
    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate content complexity score"""
        
        score = 0.5  # Base score
        
        # Length-based complexity
        if len(content) > 1000:
            score += 0.2
        elif len(content) > 200:
            score += 0.1
        
        # Structural complexity
        lines = content.split('\n')
        if len(lines) > 10:
            score += 0.1
        
        # Data complexity
        if re.search(r'\d+', content):
            score += 0.1
        
        # Analytical complexity
        analysis_terms = ['analysis', 'comparison', 'trend', 'pattern', 'insight', 'recommendation']
        for term in analysis_terms:
            if term in content.lower():
                score += 0.02  # Small boost per analytical term
        
        return min(1.0, score)
    
    def _calculate_context_relevance(self, content: str, context: Dict[str, Any]) -> float:
        """Calculate how relevant the response is to the conversation context"""
        
        # Extract query terms from context
        user_query = context.get('user_query', '')
        agents_involved = context.get('agents_involved', [])
        
        relevance_score = 0.0
        
        # Query term relevance
        if user_query:
            query_words = set(re.findall(r'\w+', user_query.lower()))
            content_words = set(re.findall(r'\w+', content.lower()))
            
            if query_words:
                overlap = len(query_words.intersection(content_words))
                relevance_score += (overlap / len(query_words)) * 0.5
        
        # Agent relevance
        if agents_involved:
            agent_terms = {
                'data': ['data', 'analysis', 'sql', 'query', 'metrics', 'revenue'],
                'deal': ['deal', 'opportunity', 'pipeline', 'meddpicc', 'qualification'],
                'lead': ['lead', 'prospect', 'contact', 'scoring', 'disqualification']
            }
            
            content_lower = content.lower()
            for agent in agents_involved:
                agent_key = agent.lower().replace('agent', '').strip()
                if agent_key in agent_terms:
                    for term in agent_terms[agent_key]:
                        if term in content_lower:
                            relevance_score += 0.05  # Small boost per relevant term
        
        return min(1.0, relevance_score)
    
    def _create_empty_response(self) -> ParsedResponse:
        """Create empty response for null input"""
        
        return ParsedResponse(
            content="",
            format_type=ResponseFormat.PLAIN_TEXT,
            parsing_method='empty_input',
            confidence_score=0.0,
            response_quality_score=0.0,
            content_length=0,
            contains_data=False,
            contains_analysis=False,
            contains_error=False,
            structured_elements={},
            metadata={
                'original_length': 0,
                'parsed_length': 0,
                'compression_ratio': 1.0,
                'content_type': None,
                'complexity_score': 0.0
            },
            parsing_timestamp=datetime.utcnow().isoformat()
        )
    
    def standardize_conversation_response(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize final_response field in conversation data"""
        
        conversation = conversation_data.get('conversation', {})
        raw_response = conversation.get('final_response', '')
        
        # Parse response
        parsed_response = self.parse_final_response(raw_response, conversation)
        
        # Update conversation with standardized response
        conversation['final_response'] = parsed_response.content
        conversation['response_parsing'] = {
            'original_response': raw_response,
            'format_type': parsed_response.format_type.value,
            'parsing_method': parsed_response.parsing_method,
            'confidence_score': parsed_response.confidence_score,
            'quality_score': parsed_response.response_quality_score,
            'content_characteristics': {
                'contains_data': parsed_response.contains_data,
                'contains_analysis': parsed_response.contains_analysis,
                'contains_error': parsed_response.contains_error
            },
            'structured_elements': parsed_response.structured_elements,
            'metadata': parsed_response.metadata,
            'parsing_timestamp': parsed_response.parsing_timestamp
        }
        
        # Add to export metadata
        if 'export_metadata' not in conversation_data:
            conversation_data['export_metadata'] = {}
        
        conversation_data['export_metadata']['response_standardization'] = {
            'applied': True,
            'format_detected': parsed_response.format_type.value,
            'quality_score': parsed_response.response_quality_score,
            'parsing_confidence': parsed_response.confidence_score
        }
        
        logger.info(f"Standardized response: format={parsed_response.format_type.value}, quality={parsed_response.response_quality_score:.2f}, length={parsed_response.content_length}")
        
        return conversation_data