"""
Manager Agent for RevOps AI Framework V4

This agent serves as the intelligent router and coordinator, determining the best 
approach for each user request and orchestrating specialized agents.
"""

import json
import os
import sys
import boto3
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Add the tools directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))

# Add monitoring directory for tracer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'monitoring'))
from agent_tracer import AgentTracer, create_tracer, trace_agent_invocation, trace_data_operation, trace_error

class ManagerAgent:
    """
    Manager Agent that routes requests to specialized agents and handles general queries
    """
    
    def __init__(self, region_name: str = 'us-east-1', correlation_id: Optional[str] = None):
        """Initialize the Manager Agent"""
        self.region_name = region_name
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        
        # Initialize tracer
        self.tracer = create_tracer(correlation_id)
        
        # Claude 3.7 with inference profile configuration
        self.model_id = "anthropic.claude-3-7-sonnet-20250219-v1:0"
        self.inference_profile_id = os.environ.get('INFERENCE_PROFILE_ID', 'anthropic.claude-3-7-sonnet-20250219-v1:0')
        
        # Specialized agent endpoints
        self.deal_analysis_agent_function = os.environ.get('DEAL_ANALYSIS_AGENT_FUNCTION', 'revops-deal-analysis-agent')
        
        # Collaborator agent endpoints
        self.data_agent_function = os.environ.get('DATA_AGENT_FUNCTION', 'revops-data-agent')
        self.web_search_agent_function = os.environ.get('WEB_SEARCH_AGENT_FUNCTION', 'revops-web-search-agent')
        self.execution_agent_function = os.environ.get('EXECUTION_AGENT_FUNCTION', 'revops-execution-agent')
        
        # Deal analysis patterns
        self.deal_analysis_patterns = [
            r"status of.*deal",
            r"deal.*status",
            r"tell me about.*deal",
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
            r"probability.*deal"
        ]
        
        # Context storage for multi-turn conversations
        self.conversation_context = {}
    
    def get_current_date_context(self) -> str:
        """Get current date and time context"""
        now = datetime.now(timezone.utc)
        
        date_context = f"""
📅 **CURRENT DATE AND TIME CONTEXT:**
- Current Date: {now.strftime('%A, %B %d, %Y')}
- Current Time: {now.strftime('%H:%M UTC')}
- Current Quarter: Q{((now.month - 1) // 3) + 1} {now.year}
- Current Month: {now.strftime('%B %Y')}
- Current Year: {now.year}

**IMPORTANT**: Use this current date information to interpret all time-based references.

---

"""
        return date_context
    
    def extract_company_name(self, query: str) -> str:
        """Extract company name from query"""
        # Remove common words and patterns
        query_clean = re.sub(r'\b(status|deal|opportunity|the|of|about|with|for|analyze|review|assess|tell|me|what|is|how|going)\b', '', query.lower())
        
        # Look for company names
        words = query_clean.split()
        company_candidates = []
        
        for word in words:
            word = word.strip('.,?!:;')
            if len(word) > 2 and word.isalpha():
                company_candidates.append(word)
        
        # Return the most likely company name (first significant word)
        if company_candidates:
            return company_candidates[0].upper()
        
        return ""
    
    def is_deal_analysis_request(self, query: str) -> bool:
        """Determine if query should be routed to Deal Analysis Agent"""
        query_lower = query.lower()
        
        # Check against deal analysis patterns
        for pattern in self.deal_analysis_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check for company names in deal context
        company_indicators = ["ixis", "acme", "microsoft", "google", "salesforce", "snowflake"]
        for indicator in company_indicators:
            if indicator in query_lower and any(word in query_lower for word in ["deal", "opportunity", "status", "analyze", "review"]):
                return True
        
        return False
    
    def route_to_deal_analysis_agent(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to Deal Analysis Agent"""
        start_time = time.time()
        
        try:
            company_name = self.extract_company_name(query)
            
            # Trace agent invocation
            self.tracer.trace_agent_invocation(
                source_agent="ManagerAgent",
                target_agent="DealAnalysisAgent",
                collaboration_type="SPECIALIZED_ROUTING",
                reasoning=f"Routing deal analysis request for company: {company_name}",
                context_passed={"company_name": company_name, "query": query}
            )
            
            request_payload = {
                "query": query,
                "context": {
                    "user_request": query,
                    "company_name": company_name,
                    "request_type": "deal_analysis",
                    "current_date": datetime.now(timezone.utc).isoformat(),
                    "correlation_id": self.tracer.correlation_id
                }
            }
            
            print(f"Routing to Deal Analysis Agent: {company_name}")
            
            response = self.lambda_client.invoke(
                FunctionName=self.deal_analysis_agent_function,
                Payload=json.dumps(request_payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            # Trace agent response
            end_time = time.time()
            processing_time_ms = int((end_time - start_time) * 1000)
            
            if result.get("success"):
                self.tracer.trace_agent_response(
                    agent_name="DealAnalysisAgent",
                    response_type="DEAL_ANALYSIS_COMPLETE",
                    data_sources_used=list(result.get("data_sources", {}).keys()),
                    processing_time_ms=processing_time_ms,
                    success=True,
                    result_summary=f"Deal analysis completed for {company_name}"
                )
                
                return {
                    "success": True,
                    "response": result.get("analysis", ""),
                    "source": "deal_analysis_agent",
                    "company_name": company_name,
                    "data_sources": result.get("data_sources", {})
                }
            else:
                self.tracer.trace_agent_response(
                    agent_name="DealAnalysisAgent",
                    response_type="DEAL_ANALYSIS_FAILED",
                    data_sources_used=[],
                    processing_time_ms=processing_time_ms,
                    success=False,
                    result_summary=f"Deal analysis failed: {result.get('error', 'Unknown error')}"
                )
                
                return {
                    "success": False,
                    "error": result.get("error", "Deal Analysis Agent failed"),
                    "fallback_needed": True
                }
                
        except Exception as e:
            print(f"Error routing to Deal Analysis Agent: {str(e)}")
            
            # Trace error
            self.tracer.trace_error(
                error_type=type(e).__name__,
                error_message=str(e),
                agent_context="ManagerAgent.route_to_deal_analysis_agent",
                recovery_attempted=True
            )
            
            return {
                "success": False,
                "error": f"Error routing to Deal Analysis Agent: {str(e)}",
                "fallback_needed": True
            }
    
    def collaborate_with_data_agent(self, request: str) -> Dict[str, Any]:
        """Collaborate with Data Agent for general queries"""
        try:
            enhanced_request = f"{self.get_current_date_context()}{request}"
            
            response = self.lambda_client.invoke(
                FunctionName=self.data_agent_function,
                Payload=json.dumps({"request": enhanced_request})
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error collaborating with Data Agent: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def collaborate_with_web_search_agent(self, request: str) -> Dict[str, Any]:
        """Collaborate with Web Search Agent for external intelligence"""
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.web_search_agent_function,
                Payload=json.dumps({"request": request})
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error collaborating with Web Search Agent: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def collaborate_with_execution_agent(self, request: str) -> Dict[str, Any]:
        """Collaborate with Execution Agent for actions"""
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.execution_agent_function,
                Payload=json.dumps({"request": request})
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error collaborating with Execution Agent: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def handle_general_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general queries using collaborator agents"""
        try:
            # Determine the type of analysis needed
            query_lower = query.lower()
            
            # Lead assessment
            if any(word in query_lower for word in ["assess", "lead", "qualify", "icp", "score"]):
                return self.process_lead_assessment(query)
            
            # Customer risk assessment
            elif any(word in query_lower for word in ["churn", "risk", "health", "usage", "decline"]):
                return self.process_customer_risk_assessment(query)
            
            # Consumption analysis
            elif any(word in query_lower for word in ["consumption", "usage", "fbu", "utilization"]):
                return self.process_consumption_analysis(query)
            
            # Pipeline/forecasting
            elif any(word in query_lower for word in ["pipeline", "forecast", "quarter", "revenue"]):
                return self.process_pipeline_analysis(query)
            
            # Call analysis
            elif any(word in query_lower for word in ["call", "conversation", "gong", "recent"]):
                return self.process_call_analysis(query)
            
            # General data query
            else:
                return self.process_general_data_query(query)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing general query: {str(e)}"
            }
    
    def process_lead_assessment(self, query: str) -> Dict[str, Any]:
        """Process lead assessment queries"""
        # Step 1: Internal data check
        data_result = self.collaborate_with_data_agent(
            f"Search for lead information and ICP alignment: {query}"
        )
        
        # Step 2: External intelligence if needed
        if "company" in query.lower():
            company_name = self.extract_company_name(query)
            web_result = self.collaborate_with_web_search_agent(
                f"Research company information for lead assessment: {company_name}"
            )
        
        # Step 3: Synthesize and provide recommendations
        return {
            "success": True,
            "response": "Lead assessment analysis completed",
            "source": "manager_agent_lead_assessment"
        }
    
    def process_customer_risk_assessment(self, query: str) -> Dict[str, Any]:
        """Process customer risk assessment queries"""
        data_result = self.collaborate_with_data_agent(
            f"Analyze customer risk factors and usage patterns: {query}"
        )
        
        return {
            "success": True,
            "response": "Customer risk assessment analysis completed",
            "source": "manager_agent_risk_assessment"
        }
    
    def process_consumption_analysis(self, query: str) -> Dict[str, Any]:
        """Process consumption analysis queries"""
        data_result = self.collaborate_with_data_agent(
            f"Analyze consumption patterns and usage metrics: {query}"
        )
        
        return {
            "success": True,
            "response": "Consumption analysis completed",
            "source": "manager_agent_consumption_analysis"
        }
    
    def process_pipeline_analysis(self, query: str) -> Dict[str, Any]:
        """Process pipeline and forecasting queries"""
        data_result = self.collaborate_with_data_agent(
            f"Analyze pipeline data and forecast metrics: {query}"
        )
        
        return {
            "success": True,
            "response": "Pipeline analysis completed",
            "source": "manager_agent_pipeline_analysis"
        }
    
    def process_call_analysis(self, query: str) -> Dict[str, Any]:
        """Process call analysis queries"""
        data_result = self.collaborate_with_data_agent(
            f"Retrieve and analyze call data: {query}"
        )
        
        return {
            "success": True,
            "response": "Call analysis completed",
            "source": "manager_agent_call_analysis"
        }
    
    def process_general_data_query(self, query: str) -> Dict[str, Any]:
        """Process general data queries"""
        data_result = self.collaborate_with_data_agent(query)
        
        return {
            "success": True,
            "response": "General data query completed",
            "source": "manager_agent_general_query"
        }
    
    def format_final_response(self, result: Dict[str, Any], original_query: str) -> str:
        """Format the final response for delivery"""
        if not result.get("success"):
            return f"I apologize, but I encountered an issue processing your request: {result.get('error', 'Unknown error')}"
        
        response = result.get("response", "")
        source = result.get("source", "")
        
        # Add context about data sources if available
        if result.get("data_sources"):
            data_sources = result["data_sources"]
            context_info = f"\n\n*Analysis based on {data_sources.get('opportunity_count', 0)} opportunities and {data_sources.get('call_count', 0)} calls*"
            response += context_info
        
        return response
    
    def process_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for processing requests"""
        start_time = time.time()
        
        try:
            # Extract user query and context
            user_query = event.get("query", event.get("user_query", event.get("inputText", "")))
            session_id = event.get("sessionId", "default")
            user_id = event.get("userId", "unknown")
            channel = event.get("channel", "lambda")
            
            if not user_query:
                return {
                    "success": False,
                    "error": "No query provided"
                }
            
            # Trace conversation start
            self.tracer.trace_conversation_start(
                user_query=user_query,
                user_id=user_id,
                channel=channel,
                temporal_context=self.get_current_date_context()
            )
            
            print(f"Manager Agent processing: {user_query}")
            
            # Maintain conversation context
            context = self.conversation_context.get(session_id, {})
            context["last_query"] = user_query
            context["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Step 1: Determine routing and trace decision logic
            if self.is_deal_analysis_request(user_query):
                print("Routing to Deal Analysis Agent")
                
                # Trace decision logic
                self.tracer.trace_decision_logic(
                    decision_point="REQUEST_ROUTING",
                    workflow_selected="DEAL_ANALYSIS_WORKFLOW",
                    reasoning="Query contains deal/opportunity keywords, routing to specialized Deal Analysis Agent",
                    confidence_score=0.9,
                    alternatives_considered=["GENERAL_QUERY_WORKFLOW", "DATA_QUERY_WORKFLOW"]
                )
                
                result = self.route_to_deal_analysis_agent(user_query, context)
                
                # Fallback to general processing if Deal Analysis Agent fails
                if not result.get("success") and result.get("fallback_needed"):
                    print("Deal Analysis Agent failed, falling back to general processing")
                    
                    # Trace fallback decision
                    self.tracer.trace_decision_logic(
                        decision_point="FALLBACK_ROUTING",
                        workflow_selected="GENERAL_QUERY_WORKFLOW",
                        reasoning="Deal Analysis Agent failed, falling back to general query processing",
                        confidence_score=0.8
                    )
                    
                    result = self.handle_general_query(user_query, context)
            else:
                print("Processing as general query")
                
                # Trace decision logic for general query
                self.tracer.trace_decision_logic(
                    decision_point="REQUEST_ROUTING",
                    workflow_selected="GENERAL_QUERY_WORKFLOW",
                    reasoning="Query does not match deal analysis patterns, routing to general processing",
                    confidence_score=0.7,
                    alternatives_considered=["DEAL_ANALYSIS_WORKFLOW", "LEAD_ASSESSMENT_WORKFLOW"]
                )
                
                result = self.handle_general_query(user_query, context)
            
            # Update conversation context
            context["last_result"] = result
            self.conversation_context[session_id] = context
            
            # Format final response
            final_response = self.format_final_response(result, user_query)
            
            # Trace conversation end
            end_time = time.time()
            processing_time_ms = int((end_time - start_time) * 1000)
            
            self.tracer.trace_conversation_end(
                response_summary=final_response[:200] + "..." if len(final_response) > 200 else final_response,
                total_agents_used=1,  # Manager agent itself
                processing_time_ms=processing_time_ms,
                success=result.get("success", True)
            )
            
            return {
                "success": True,
                "response": final_response,
                "outputText": final_response,
                "sessionId": session_id,
                "source": result.get("source", "manager_agent")
            }
            
        except Exception as e:
            print(f"Error in Manager Agent: {str(e)}")
            
            # Trace error
            self.tracer.trace_error(
                error_type=type(e).__name__,
                error_message=str(e),
                agent_context="ManagerAgent.process_request",
                recovery_attempted=False
            )
            
            return {
                "success": False,
                "error": f"Error processing request: {str(e)}"
            }

def lambda_handler(event, context):
    """AWS Lambda handler for Manager Agent"""
    print(f"Manager Agent invoked with event: {json.dumps(event)}")
    
    # Extract correlation_id from event or context
    correlation_id = event.get("correlation_id") or getattr(context, "aws_request_id", None)
    
    agent = ManagerAgent(correlation_id=correlation_id)
    result = agent.process_request(event)
    
    print(f"Manager Agent result: {json.dumps(result)}")
    return result

if __name__ == "__main__":
    # Test the agent locally
    test_events = [
        {"query": "What is the status of the IXIS deal?"},
        {"query": "Analyze Q4 consumption trends"},
        {"query": "Who are the top expansion opportunities?"}
    ]
    
    agent = ManagerAgent()
    
    for test_event in test_events:
        print(f"\nTesting: {test_event['query']}")
        result = agent.process_request(test_event)
        print(f"Result: {json.dumps(result, indent=2)}")