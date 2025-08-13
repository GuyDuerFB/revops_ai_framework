"""
Webhook Gateway - Response Classifier
Determines response type and target webhook URL based on manager agent response
"""

import os
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Classification patterns for different response types
CLASSIFICATION_PATTERNS = {
    'deal_analysis': [
        r"status of.*deal",
        r"deal.*status", 
        r"analyze.*deal",
        r"review.*deal",
        r"assess.*deal",
        r"status of.*opportunity",
        r"opportunity.*status",
        r"analyze.*opportunity",
        r"review.*opportunity",
        r"assess.*opportunity",
        r"deal with \w+",
        r"deal for \w+",
        r"about.*deal",
        r"how is.*deal",
        r"what.*status.*deal",
        r"meddpicc",
        r"probability.*deal",
        r"ixis",
        r"acme",
        r"microsoft.*deal",
        r"google.*deal"
    ],
    'lead_analysis': [
        r"assess.*lead",
        r"lead.*quality",
        r"icp.*fit",
        r"lead.*assessment",
        r"qualify.*lead",
        r"what do you think about.*from",
        r"tell me about.*at",
        r"evaluate.*lead",
        r"score.*lead",
        r"research.*contact",
        r"background.*on",
        r"opinion.*on.*from"
    ],
    'data_analysis': [
        r"how many.*opportunities",
        r"consumption.*trends",
        r"pipeline.*analysis", 
        r"revenue.*forecast",
        r"quarterly.*data",
        r"sales.*metrics",
        r"usage.*patterns",
        r"churn.*risk",
        r"expansion.*opportunities",
        r"analyze.*q\d",
        r"trends.*in",
        r"statistics.*for",
        r"count.*of",
        r"total.*revenue",
        r"forecast.*for"
    ]
}

def classify_response_type(manager_response: Dict[str, Any], original_query: str) -> str:
    """
    Classify the response type based on manager agent response and original query.
    
    Args:
        manager_response: Response from manager agent
        original_query: Original user query
        
    Returns:
        Response type: 'deal_analysis', 'lead_analysis', 'data_analysis', or 'general'
    """
    try:
        # Check if manager agent routed to a specific agent based on source
        source = manager_response.get('source', '')
        if 'deal_analysis' in source:
            return 'deal_analysis'
        elif 'lead_analysis' in source:
            return 'lead_analysis'
        elif 'data_agent' in source or 'consumption' in source or 'pipeline' in source:
            return 'data_analysis'
        
        # Fall back to pattern matching on original query
        query_lower = original_query.lower()
        
        # Check each pattern category
        for response_type, patterns in CLASSIFICATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    logger.info(f"Classified as {response_type} based on pattern: {pattern}")
                    return response_type
        
        # Default classification
        logger.info(f"No specific pattern matched, classifying as general")
        return 'general'
        
    except Exception as e:
        logger.error(f"Error classifying response: {str(e)}")
        return 'general'

def get_target_webhook_url(response_type: str) -> Optional[str]:
    """
    Get target webhook URL from environment variables based on response type.
    
    Args:
        response_type: Classified response type
        
    Returns:
        Webhook URL or None if not configured
    """
    env_mapping = {
        'deal_analysis': 'DEAL_ANALYSIS_WEBHOOK_URL',
        'lead_analysis': 'LEAD_ANALYSIS_WEBHOOK_URL', 
        'data_analysis': 'DATA_ANALYSIS_WEBHOOK_URL',
        'general': 'GENERAL_WEBHOOK_URL'
    }
    
    env_var = env_mapping.get(response_type, 'GENERAL_WEBHOOK_URL')
    webhook_url = os.environ.get(env_var)
    
    if not webhook_url:
        logger.warning(f"No webhook URL configured for {response_type} (env var: {env_var})")
        # Try fallback to general webhook
        fallback_url = os.environ.get('GENERAL_WEBHOOK_URL')
        if fallback_url:
            logger.info(f"Using fallback general webhook URL")
            return fallback_url
    
    return webhook_url

def format_webhook_response(manager_response: Dict[str, Any], response_type: str, 
                          conversation_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the outbound webhook payload according to specification.
    
    Args:
        manager_response: Response from manager agent
        response_type: Classified response type
        conversation_metadata: Metadata about the conversation
        
    Returns:
        Formatted webhook payload
    """
    try:
        # Extract response text
        response_text = manager_response.get('response', manager_response.get('outputText', ''))
        
        # Create plain text version (strip markdown)
        plain_text = _strip_markdown(response_text)
        
        # Extract agents used - look in multiple possible locations
        agents_used = []
        
        # Check direct agents_used field
        if 'agents_used' in manager_response:
            agents_used = manager_response['agents_used']
        else:
            # Infer from source field
            source = manager_response.get('source', '')
            if source:
                if 'deal_analysis' in source:
                    agents_used = ['ManagerAgent', 'DealAnalysisAgent']
                elif 'lead_analysis' in source:
                    agents_used = ['ManagerAgent', 'LeadAnalysisAgent']
                elif 'data' in source:
                    agents_used = ['ManagerAgent', 'DataAgent']
                else:
                    agents_used = ['ManagerAgent']
            else:
                agents_used = ['ManagerAgent']
        
        # Create webhook payload
        webhook_payload = {
            "header": response_type,
            "response_rich": response_text,
            "response_plain": plain_text,
            "agents_used": agents_used,
            "metadata": {
                "conversation_id": conversation_metadata.get("conversation_id"),
                "processing_time_ms": conversation_metadata.get("processing_time_ms", 0),
                "timestamp": conversation_metadata.get("timestamp"),
                "source_system": conversation_metadata.get("source_system"),
                "source_process": conversation_metadata.get("source_process"),
                "original_timestamp": conversation_metadata.get("original_timestamp")
            }
        }
        
        return webhook_payload
        
    except Exception as e:
        logger.error(f"Error formatting webhook response: {str(e)}")
        raise Exception(f"Response formatting failed: {str(e)}")

def _strip_markdown(text: str) -> str:
    """
    Strip markdown formatting to create plain text version.
    
    Args:
        text: Text with markdown formatting
        
    Returns:
        Plain text without markdown
    """
    if not text:
        return ""
    
    # Remove markdown formatting
    # Bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
    
    # Headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # # headers
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url)
    
    # Code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)  # ```code```
    text = re.sub(r'`([^`]+)`', r'\1', text)  # `inline code`
    
    # Lists
    text = re.sub(r'^\s*[-*+]\s*', '', text, flags=re.MULTILINE)  # - list items
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)  # 1. numbered lists
    
    # Clean up extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines
    text = text.strip()
    
    return text