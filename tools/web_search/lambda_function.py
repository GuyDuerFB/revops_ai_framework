"""
RevOps AI Framework V2 - Web Search Lambda

This Lambda function provides web search capabilities for the RevOps AI Framework,
enabling agents to research companies, leads, and market information.
Compatible with AWS Bedrock Agent function calling format.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import agent tracer for debugging
try:
    import sys
    sys.path.append('/opt/python')
    from agent_tracer import trace_data_operation, trace_error, get_tracer
except ImportError:
    # Fallback if agent_tracer not available
    def trace_data_operation(*args, **kwargs): pass
    def trace_error(*args, **kwargs): pass
    def get_tracer(): return None

def search_web(query: str, num_results: int = 5, region: str = "us") -> Dict[str, Any]:
    """
    Perform web search using DuckDuckGo Instant Answer API
    
    Args:
        query (str): Search query
        num_results (int): Number of results to return (default: 5)
        region (str): Search region (default: "us")
        
    Returns:
        Dict[str, Any]: Search results in structured format
    """
    start_time = time.time()
    try:
        print(f"Performing web search for: {query}")
        
        # Use DuckDuckGo Instant Answer API (no API key required)
        base_url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_html': '1',
            'skip_disambig': '1'
        }
        
        url = base_url + '?' + urllib.parse.urlencode(params)
        
        # Make request
        req = urllib.request.Request(url, headers={
            'User-Agent': 'RevOps-AI-Framework/1.0'
        })
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                
                # Format results
                results = []
                
                # Add instant answer if available
                if data.get('Answer'):
                    results.append({
                        'title': 'Instant Answer',
                        'content': data.get('Answer'),
                        'url': data.get('AnswerURL', ''),
                        'source': 'DuckDuckGo Instant Answer'
                    })
                
                # Add abstract if available
                if data.get('Abstract'):
                    results.append({
                        'title': data.get('Heading', 'Abstract'),
                        'content': data.get('Abstract'),
                        'url': data.get('AbstractURL', ''),
                        'source': data.get('AbstractSource', 'Unknown')
                    })
                
                # Add related topics
                for topic in data.get('RelatedTopics', [])[:num_results-len(results)]:
                    if isinstance(topic, dict) and topic.get('Text'):
                        results.append({
                            'title': topic.get('Text', '')[:100] + '...' if len(topic.get('Text', '')) > 100 else topic.get('Text', ''),
                            'content': topic.get('Text', ''),
                            'url': topic.get('FirstURL', ''),
                            'source': 'DuckDuckGo Related'
                        })
                
                # If no results from instant API, create a structured response
                if not results:
                    results.append({
                        'title': f'Search: {query}',
                        'content': f'Search performed for "{query}". For detailed results, consider using specialized research tools or visiting search engines directly.',
                        'url': f'https://duckduckgo.com/?q={urllib.parse.quote(query)}',
                        'source': 'DuckDuckGo Search'
                    })
                
                # Trace successful operation
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                trace_data_operation(
                    operation_type="WEB_SEARCH",
                    data_source="DUCKDUCKGO",
                    query_summary=f"web_search: {query[:50]}...",
                    result_count=len(results),
                    execution_time_ms=execution_time_ms
                )
                
                return {
                    'success': True,
                    'query': query,
                    'results': results[:num_results],
                    'result_count': len(results),
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': f'Found {len(results)} results for "{query}"'
                }
            else:
                raise Exception(f"HTTP {response.status}: Failed to fetch search results")
                
    except Exception as e:
        print(f"Error in web search: {str(e)}")
        
        # Trace the error
        trace_error(
            error_type=type(e).__name__,
            error_message=str(e),
            agent_context=f"WebSearchAgent.search_web"
        )
        
        return {
            'success': False,
            'error': str(e),
            'query': query,
            'results': [],
            'result_count': 0,
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Search failed for "{query}": {str(e)}'
        }

def research_company(company_name: str, focus_area: str = "general") -> Dict[str, Any]:
    """
    Research a specific company with focused queries
    
    Args:
        company_name (str): Name of company to research
        focus_area (str): Area of focus (general, funding, technology, size, news)
        
    Returns:
        Dict[str, Any]: Company research results
    """
    focus_queries = {
        "general": f"{company_name} company overview business",
        "funding": f"{company_name} funding investment series revenue",
        "technology": f"{company_name} technology stack platform architecture",
        "size": f"{company_name} employees headcount company size",
        "news": f"{company_name} news recent updates 2024 2025"
    }
    
    start_time = time.time()
    
    query = focus_queries.get(focus_area, f"{company_name} {focus_area}")
    result = search_web(query, num_results=3)
    
    # Trace company research operation
    execution_time_ms = int((time.time() - start_time) * 1000)
    result_count = result.get('result_count', 0) if result.get('success') else 0
    
    trace_data_operation(
        operation_type="COMPANY_RESEARCH",
        data_source="DUCKDUCKGO",
        query_summary=f"research_company: {company_name} ({focus_area})",
        result_count=result_count,
        execution_time_ms=execution_time_ms
    )
    
    return result

def lambda_handler(event, context):
    """
    AWS Lambda handler for web search functionality
    Compatible with Bedrock Agent function calling format
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        print(f"Event keys: {list(event.keys())}")
        print(f"Event type check - function: {'function' in event}, actionGroup: {'actionGroup' in event}")
        
        # 1. Check if this is a new Bedrock Agent format with 'function' field
        if 'function' in event and 'actionGroup' in event:
            function_name = event.get('function')
            
            if function_name in ['search_web', 'research_company']:
                # Handle new Bedrock agent format
                if 'parameters' in event and isinstance(event['parameters'], list):
                    params = {param.get('name'): param.get('value') for param in event['parameters']}
                    
                    if function_name == 'search_web':
                        query = params.get('query')
                        num_results = int(params.get('num_results', 5))
                        region = params.get('region', 'us')
                        
                        result = search_web(query, num_results, region)
                        
                    elif function_name == 'research_company':
                        company_name = params.get('company_name')
                        focus_area = params.get('focus_area', 'general')
                        
                        result = research_company(company_name, focus_area)
                    
                    # Return in new Bedrock agent format
                    response_body = {
                        'messageVersion': '1.0',
                        'response': {
                            'actionGroup': event.get('actionGroup'),
                            'function': function_name,
                            'functionResponse': {
                                'responseBody': {
                                    'TEXT': {
                                        'body': json.dumps(result)
                                    }
                                }
                            }
                        }
                    }
                    
                    print(f"Lambda returning response: {json.dumps(response_body)}")
                    return response_body
                    
        # 2. Check if this is an old Bedrock Agent invocation with 'action' field
        elif 'actionGroup' in event and 'action' in event:
            action_name = event.get('action')
            
            if action_name in ['search_web', 'research_company']:
                body = event.get('body', {})
                parameters = body.get('parameters', {})
                
                if action_name == 'search_web':
                    query = parameters.get('query')
                    num_results = int(parameters.get('num_results', 5))
                    region = parameters.get('region', 'us')
                    
                    result = search_web(query, num_results, region)
                    
                elif action_name == 'research_company':
                    company_name = parameters.get('company_name')
                    focus_area = parameters.get('focus_area', 'general')
                    
                    result = research_company(company_name, focus_area)
                
                # Return in old Bedrock agent format
                return {
                    'actionGroup': event.get('actionGroup'),
                    'action': action_name,
                    'actionGroupOutput': {
                        'body': json.dumps(result)
                    }
                }
                
        # 3. Check if this is a direct invocation
        elif 'query' in event or 'company_name' in event:
            if 'query' in event:
                # Direct web search
                query = event.get('query')
                num_results = int(event.get('num_results', 5))
                region = event.get('region', 'us')
                
                return search_web(query, num_results, region)
                
            elif 'company_name' in event:
                # Direct company research
                company_name = event.get('company_name')
                focus_area = event.get('focus_area', 'general')
                
                return research_company(company_name, focus_area)
        
        # 4. No recognizable format
        return {
            'success': False,
            'error': 'Invalid request format',
            'message': 'Request format not recognized. Please provide query or company_name parameter.',
            'results': [],
            'result_count': 0
        }
        
    except Exception as e:
        # Log the full error for debugging
        print(f"Lambda handler error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Return error response in the expected format
        error_response = {
            'success': False,
            'error': str(e),
            'results': [],
            'result_count': 0,
            'message': f'Web search failed: {str(e)}'
        }
        print(f"Returning error response: {json.dumps(error_response)}")
        return error_response