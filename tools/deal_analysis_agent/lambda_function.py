"""
Deal Analysis Agent Lambda Function

AWS Lambda function for the Deal Analysis Agent that specializes in 
comprehensive deal assessment with embedded SQL queries and Claude 3.7 analysis.
"""

import json
import os
import sys
import boto3
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Import the Deal Analysis Agent
current_dir = os.path.dirname(os.path.abspath(__file__))
agents_dir = os.path.join(current_dir, '..', '..', 'agents', 'deal_analysis_agent')
sys.path.insert(0, agents_dir)

try:
    from deal_analysis_agent import DealAnalysisAgent
except ImportError:
    print("Warning: Could not import DealAnalysisAgent, defining fallback class")
    
    class DealAnalysisAgent:
        def __init__(self):
            self.region_name = 'us-east-1'
            self.lambda_client = boto3.client('lambda')
            self.firebolt_query_function = os.environ.get('FIREBOLT_QUERY_FUNCTION', 'revops-firebolt-query')
        
        def process_request(self, event):
            return {"success": False, "error": "DealAnalysisAgent class not properly imported"}

class DealAnalysisLambdaHandler:
    """
    Lambda handler wrapper for Deal Analysis Agent
    """
    
    def __init__(self):
        """Initialize the handler"""
        self.agent = DealAnalysisAgent()
        
        # Environment configuration
        self.function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'revops-deal-analysis-agent')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Claude 3.7 inference profile
        self.inference_profile_id = os.environ.get('INFERENCE_PROFILE_ID', 'us.anthropic.claude-3-5-sonnet-20241022-v2:0')
        
        # Firebolt query function
        self.firebolt_query_function = os.environ.get('FIREBOLT_QUERY_FUNCTION', 'revops-firebolt-query')
        
        print(f"Deal Analysis Agent initialized")
        print(f"Function: {self.function_name}")
        print(f"Region: {self.region}")
        print(f"Inference Profile: {self.inference_profile_id}")
        print(f"Firebolt Function: {self.firebolt_query_function}")
    
    def validate_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Validate incoming request"""
        try:
            # Extract query from various possible formats
            query = event.get("query", event.get("user_query", event.get("inputText", "")))
            
            if not query:
                return {
                    "valid": False,
                    "error": "No query provided. Expected 'query', 'user_query', or 'inputText' field."
                }
            
            return {
                "valid": True,
                "query": query,
                "context": event.get("context", {}),
                "session_id": event.get("sessionId", event.get("session_id", "default"))
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Request validation failed: {str(e)}"
            }
    
    def extract_company_name(self, query: str) -> str:
        """Extract company name from deal analysis queries"""
        import re
        
        # Common patterns for deal queries
        patterns = [
            r"status of the (\w+)",
            r"status of (\w+)",
            r"deal with (\w+)",
            r"deal for (\w+)",
            r"analyze the (\w+)",
            r"analyze (\w+)",
            r"review the (\w+)",
            r"review (\w+)",
            r"about the (\w+)",
            r"about (\w+)"
        ]
        
        query_lower = query.lower()
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                company_name = match.group(1)
                # Clean up common words
                if company_name not in ["deal", "opportunity", "status", "company"]:
                    return company_name.upper()
        
        # Fallback: look for known company names
        known_companies = ["IXIS", "ACME", "MICROSOFT", "GOOGLE", "SALESFORCE", "SNOWFLAKE"]
        for company in known_companies:
            if company.lower() in query_lower:
                return company
        
        return ""
    
    def format_response(self, result: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Format the response for consistent output"""
        try:
            if result.get("success"):
                return {
                    "statusCode": 200,
                    "success": True,
                    "analysis": result.get("analysis", ""),
                    "company_name": result.get("company_name", ""),
                    "data_sources": result.get("data_sources", {}),
                    "processing_time_ms": int(processing_time * 1000),
                    "agent": "deal_analysis_agent",
                    "version": "V4",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "statusCode": 400,
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "details": result.get("details", {}),
                    "processing_time_ms": int(processing_time * 1000),
                    "agent": "deal_analysis_agent",
                    "version": "V4",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            return {
                "statusCode": 500,
                "success": False,
                "error": f"Error formatting response: {str(e)}",
                "processing_time_ms": int(processing_time * 1000),
                "agent": "deal_analysis_agent",
                "version": "V4",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def handle_request(self, event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Main request handler"""
        start_time = time.time()
        
        try:
            print(f"Deal Analysis Agent processing request: {json.dumps(event)}")
            
            # Validate request
            validation = self.validate_request(event)
            if not validation["valid"]:
                processing_time = time.time() - start_time
                return self.format_response(
                    {"success": False, "error": validation["error"]},
                    processing_time
                )
            
            # Extract validated data
            query = validation["query"]
            context = validation["context"]
            session_id = validation["session_id"]
            
            # Extract company name for logging
            company_name = self.extract_company_name(query)
            print(f"Extracted company name: {company_name}")
            
            # Process the request through the Deal Analysis Agent
            result = self.agent.process_request({
                "query": query,
                "context": context,
                "sessionId": session_id
            })
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Format and return response
            formatted_response = self.format_response(result, processing_time)
            
            print(f"Deal Analysis Agent completed in {processing_time:.2f}s")
            print(f"Response success: {formatted_response.get('success')}")
            
            return formatted_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Unhandled error in Deal Analysis Agent: {str(e)}"
            print(error_msg)
            
            return self.format_response(
                {"success": False, "error": error_msg},
                processing_time
            )

# Global handler instance
handler = DealAnalysisLambdaHandler()

def lambda_handler(event, context):
    """
    AWS Lambda entry point for Deal Analysis Agent
    """
    return handler.handle_request(event, context)

def test_locally():
    """Test the agent locally"""
    test_events = [
        {
            "query": "What is the status of the IXIS deal?",
            "context": {"test": True}
        },
        {
            "query": "Analyze the Microsoft opportunity",
            "context": {"test": True}
        },
        {
            "query": "Review the ACME deal status",
            "context": {"test": True}
        }
    ]
    
    print("Testing Deal Analysis Agent locally...")
    
    for i, event in enumerate(test_events, 1):
        print(f"\n--- Test {i}: {event['query']} ---")
        
        # Mock context
        mock_context = type('MockContext', (), {
            'function_name': 'test-deal-analysis-agent',
            'function_version': '1',
            'invoked_function_arn': 'arn:aws:lambda:us-east-1:123456789012:function:test-deal-analysis-agent',
            'memory_limit_in_mb': '512',
            'remaining_time_in_millis': lambda: 30000
        })()
        
        try:
            result = lambda_handler(event, mock_context)
            print(f"Success: {result.get('success')}")
            if result.get('success'):
                print(f"Analysis: {result.get('analysis', '')[:200]}...")
            else:
                print(f"Error: {result.get('error')}")
                
        except Exception as e:
            print(f"Test failed: {str(e)}")

if __name__ == "__main__":
    test_locally()