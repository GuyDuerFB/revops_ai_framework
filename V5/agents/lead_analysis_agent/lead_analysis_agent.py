"""
Lead Analysis Agent for RevOps AI Framework V4

This agent specializes in comprehensive lead assessment and engagement strategy development,
providing structured insights with ICP fit analysis and personalized outreach recommendations.
"""

import json
import os
import sys
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any
import re

# Add the tools directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))

class LeadAnalysisAgent:
    """
    Specialized agent for lead analysis with ICP assessment and engagement strategy development
    """
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize the Lead Analysis Agent"""
        self.region_name = region_name
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        
        # Claude 3.7 with inference profile configuration
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        self.inference_profile_id = os.environ.get('INFERENCE_PROFILE_ID', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0')
        
        # Tool configurations
        self.firebolt_query_function = os.environ.get('FIREBOLT_QUERY_FUNCTION', 'revops-firebolt-query')
        
        # Agent collaboration endpoints
        self.data_agent_function = os.environ.get('DATA_AGENT_FUNCTION', 'revops-data-agent')
        self.web_search_agent_function = os.environ.get('WEB_SEARCH_AGENT_FUNCTION', 'revops-web-search-agent')
        self.execution_agent_function = os.environ.get('EXECUTION_AGENT_FUNCTION', 'revops-execution-agent')
    
    def get_contact_data(self, contact_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Retrieve comprehensive contact data using embedded SQL query
        """
        # Build query based on available information
        where_conditions = []
        
        if contact_info.get('email'):
            where_conditions.append(f"c.contact_email ILIKE '%{contact_info['email']}%'")
        
        if contact_info.get('first_name') and contact_info.get('last_name'):
            where_conditions.append(f"(c.contact_first_name ILIKE '%{contact_info['first_name']}%' AND c.contact_last_name ILIKE '%{contact_info['last_name']}%')")
        
        if contact_info.get('company_name'):
            where_conditions.append(f"sa.sf_account_name ILIKE '%{contact_info['company_name']}%'")
        
        if not where_conditions:
            return {"success": False, "error": "Insufficient contact information provided"}
        
        query = f"""
        SELECT 
          c.contact_id,
          c.contact_first_name,
          c.contact_last_name, 
          c.contact_title,
          c.contact_email,
          c.contact_phone,
          c.contact_linkedin,
          c.lead_source,
          c.contact_source_campaign,
          c.created_at_ts,
          c.dbt_last_updated_ts,
          sa.sf_account_name,
          sa.sf_industry,
          sa.sf_sub_industry,
          sa.sf_account_type_custom,
          sa.account_region,
          sa.sf_company_domain,
          sa.sf_annual_revenue,
          sa.sf_number_of_employees,
          sa.sf_open_opportunities
        FROM contact_d c
        LEFT JOIN salesforce_account_d sa ON c.sf_account_id = sa.sf_account_id
        WHERE {' OR '.join(where_conditions)}
        ORDER BY c.dbt_last_updated_ts DESC
        LIMIT 50;
        """
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.firebolt_query_function,
                Payload=json.dumps({"query": query})
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error retrieving contact data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_lead_data(self, lead_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Retrieve comprehensive lead data using embedded SQL query
        """
        # Build query based on available information
        where_conditions = []
        
        if lead_info.get('email'):
            where_conditions.append(f"l.lead_email ILIKE '%{lead_info['email']}%'")
        
        if lead_info.get('first_name') and lead_info.get('last_name'):
            where_conditions.append(f"(l.lead_first_name ILIKE '%{lead_info['first_name']}%' AND l.lead_last_name ILIKE '%{lead_info['last_name']}%')")
        
        if lead_info.get('company_name'):
            where_conditions.append(f"l.lead_company ILIKE '%{lead_info['company_name']}%'")
        
        if not where_conditions:
            return {"success": False, "error": "Insufficient lead information provided"}
        
        query = f"""
        SELECT 
          l.lead_id,
          l.lead_first_name,
          l.lead_last_name,
          l.lead_title,
          l.lead_email,
          l.lead_phone,
          l.lead_company,
          l.lead_industry,
          l.lead_source,
          l.lead_source_campaign,
          l.lead_status,
          l.lead_rating,
          l.created_at_ts,
          l.dbt_last_updated_ts,
          l.company_domain,
          l.annual_revenue,
          l.number_of_employees
        FROM lead_d l
        WHERE {' OR '.join(where_conditions)}
        ORDER BY l.dbt_last_updated_ts DESC
        LIMIT 50;
        """
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.firebolt_query_function,
                Payload=json.dumps({"query": query})
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error retrieving lead data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def collaborate_with_data_agent(self, request: str) -> Dict[str, Any]:
        """
        Collaborate with Data Agent for complex Salesforce queries
        """
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.data_agent_function,
                Payload=json.dumps({"request": request})
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error collaborating with Data Agent: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def collaborate_with_web_search_agent(self, request: str) -> Dict[str, Any]:
        """
        Collaborate with Web Search Agent for external intelligence
        """
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
    
    def extract_lead_info(self, query: str) -> Dict[str, str]:
        """
        Extract lead information from user queries
        """
        lead_info = {}
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, query)
        if emails:
            lead_info['email'] = emails[0]
        
        # Extract names (basic pattern matching)
        # Look for patterns like "John Smith from", "Sarah Johnson at"
        name_patterns = [
            r'(?:assess|analyze|research|about)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:from|at)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:from|at)\s+([A-Z][A-Za-z\s]+)',
            r'lead\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'contact\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, query)
            if matches:
                if isinstance(matches[0], tuple):
                    full_name = matches[0][0]
                    if len(matches[0]) > 1:
                        lead_info['company_name'] = matches[0][1].strip()
                else:
                    full_name = matches[0]
                
                name_parts = full_name.strip().split()
                if len(name_parts) >= 2:
                    lead_info['first_name'] = name_parts[0]
                    lead_info['last_name'] = name_parts[-1]
                break
        
        # Extract company names
        company_patterns = [
            r'(?:from|at)\s+([A-Z][A-Za-z\s]+?)(?:\s|$|\?)',
            r'company\s+([A-Z][A-Za-z\s]+?)(?:\s|$|\?)',
            r'(?:lead|contact)\s+at\s+([A-Z][A-Za-z\s]+?)(?:\s|$|\?)'
        ]
        
        if not lead_info.get('company_name'):
            for pattern in company_patterns:
                matches = re.findall(pattern, query)
                if matches:
                    lead_info['company_name'] = matches[0].strip()
                    break
        
        return lead_info
    
    def assess_icp_fit(self, lead_data: Dict, company_data: Dict, web_research: Dict = None) -> Dict[str, str]:
        """
        Assess ICP fit based on gathered data
        """
        # Company information analysis
        company_name = company_data.get('sf_account_name') or lead_data.get('lead_company', '')
        industry = company_data.get('sf_industry') or lead_data.get('lead_industry', '')
        sub_industry = company_data.get('sf_sub_industry', '')
        employees = company_data.get('sf_number_of_employees') or lead_data.get('number_of_employees', 0)
        revenue = company_data.get('sf_annual_revenue') or lead_data.get('annual_revenue', 0)
        
        # Person information analysis
        title = lead_data.get('contact_title') or lead_data.get('lead_title', '')
        
        # ICP scoring logic
        company_score = 0
        authority_score = 0
        technical_score = 0
        
        # Company scoring
        high_fit_industries = ['technology', 'software', 'saas', 'fintech', 'gaming', 'e-commerce', 'adtech', 'martech']
        medium_fit_industries = ['financial services', 'retail', 'media', 'healthcare', 'telecommunications']
        
        industry_lower = industry.lower() if industry else ''
        if any(keyword in industry_lower for keyword in high_fit_industries):
            company_score += 3
        elif any(keyword in industry_lower for keyword in medium_fit_industries):
            company_score += 2
        
        # Size scoring
        if employees:
            if employees > 1000:  # Enterprise
                company_score += 3
            elif employees > 100:  # Mid-market
                company_score += 2
            elif employees > 10:   # Small company
                company_score += 1
        
        # Authority scoring
        title_lower = title.lower() if title else ''
        high_authority = ['cto', 'chief technology', 'chief data', 'vp engineering', 'vp data', 'director of data', 'head of data']
        medium_authority = ['principal engineer', 'staff engineer', 'engineering manager', 'data engineering manager', 'analytics manager']
        
        if any(keyword in title_lower for keyword in high_authority):
            authority_score = 3
        elif any(keyword in title_lower for keyword in medium_authority):
            authority_score = 2
        elif 'engineer' in title_lower or 'developer' in title_lower:
            authority_score = 1
        
        # Technical scoring from web research
        if web_research and web_research.get('success'):
            research_text = str(web_research.get('results', {})).lower()
            technical_indicators = ['analytics', 'data warehouse', 'real-time', 'api', 'scale', 'performance', 'dashboard', 'ml', 'ai']
            technical_score = sum(1 for indicator in technical_indicators if indicator in research_text)
            technical_score = min(technical_score, 3)  # Cap at 3
        
        # Overall scoring
        total_score = company_score + authority_score + technical_score
        
        # Determine ICP fit
        if total_score >= 7 and company_score >= 2 and authority_score >= 2:
            icp_fit = "High"
        elif total_score >= 4 and (company_score >= 1 or authority_score >= 1):
            icp_fit = "Medium"
        else:
            icp_fit = "Low"
        
        # Determine confidence
        data_completeness = sum([
            1 if company_name else 0,
            1 if industry else 0,
            1 if title else 0,
            1 if employees else 0,
            1 if web_research and web_research.get('success') else 0
        ])
        
        if data_completeness >= 4:
            confidence = "High"
        elif data_completeness >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Generate reasoning
        reasoning_parts = []
        
        if company_score >= 2:
            reasoning_parts.append(f"Company operates in {industry} industry which aligns with Firebolt's target verticals")
        
        if authority_score >= 2:
            reasoning_parts.append(f"Contact holds {title} position indicating decision-making authority")
        
        if employees and employees > 100:
            reasoning_parts.append(f"Company size ({employees:,} employees) suggests complex data infrastructure needs")
        
        if technical_score >= 2:
            reasoning_parts.append("Web research indicates technical requirements aligned with Firebolt's capabilities")
        
        if not reasoning_parts:
            reasoning_parts.append("Limited data available for comprehensive ICP assessment")
        
        reasoning = "; ".join(reasoning_parts[:3])  # Limit to 3 main points
        
        # Generate confidence reasoning
        confidence_reasoning_parts = []
        
        if data_completeness >= 4:
            confidence_reasoning_parts.append("Comprehensive data available from multiple sources")
        elif data_completeness >= 2:
            confidence_reasoning_parts.append("Moderate data availability with some missing elements")
        else:
            confidence_reasoning_parts.append("Limited data available, assessment based on partial information")
        
        if not web_research or not web_research.get('success'):
            confidence_reasoning_parts.append("external research unavailable")
        
        confidence_reasoning = "; ".join(confidence_reasoning_parts)
        
        return {
            'icp_fit': icp_fit,
            'reasoning': reasoning,
            'confidence': confidence,
            'confidence_reasoning': confidence_reasoning,
            'scores': {
                'company': company_score,
                'authority': authority_score,
                'technical': technical_score,
                'total': total_score,
                'data_completeness': data_completeness
            }
        }
    
    def analyze_lead(self, lead_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Perform comprehensive lead analysis
        """
        print(f"Starting lead analysis for: {lead_info}")
        
        # Step 1A: Get Salesforce data (try both contact and lead tables)
        contact_data = self.get_contact_data(lead_info)
        lead_data = self.get_lead_data(lead_info)
        
        # Determine which dataset to use
        salesforce_data = None
        data_source = None
        
        if contact_data.get("success") and contact_data.get("results"):
            salesforce_data = contact_data["results"][0]  # Use first result
            data_source = "contact"
        elif lead_data.get("success") and lead_data.get("results"):
            salesforce_data = lead_data["results"][0]  # Use first result
            data_source = "lead"
        
        # Step 1B: Web research if Salesforce data is incomplete
        web_research = None
        if not salesforce_data or not salesforce_data.get('sf_account_name') and not salesforce_data.get('lead_company'):
            # Need web research
            if lead_info.get('company_name'):
                web_research = self.collaborate_with_web_search_agent(
                    f"Research company {lead_info['company_name']} - find industry, size, technology stack, and data infrastructure needs"
                )
            elif lead_info.get('email'):
                domain = lead_info['email'].split('@')[-1] if '@' in lead_info['email'] else ''
                if domain:
                    web_research = self.collaborate_with_web_search_agent(
                        f"Research company with domain {domain} - find company name, industry, size, and technology needs"
                    )
        
        # Step 2: ICP Assessment
        company_data = salesforce_data or {}
        lead_assessment = self.assess_icp_fit(salesforce_data or lead_info, company_data, web_research)
        
        return {
            "success": True,
            "lead_info": lead_info,
            "salesforce_data": salesforce_data,
            "data_source": data_source,
            "web_research": web_research,
            "assessment": lead_assessment,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def format_lead_analysis(self, analysis_result: Dict[str, Any], is_multiple: bool = False) -> str:
        """
        Format the lead analysis in the required structure
        """
        if not analysis_result.get("success"):
            return f"Error: {analysis_result.get('error', 'Unknown error occurred')}"
        
        salesforce_data = analysis_result.get("salesforce_data", {})
        assessment = analysis_result.get("assessment", {})
        lead_info = analysis_result.get("lead_info", {})
        
        # Extract person and company info
        if salesforce_data:
            first_name = salesforce_data.get('contact_first_name') or salesforce_data.get('lead_first_name', '')
            last_name = salesforce_data.get('contact_last_name') or salesforce_data.get('lead_last_name', '')
            title = salesforce_data.get('contact_title') or salesforce_data.get('lead_title', 'Unknown Title')
            company = salesforce_data.get('sf_account_name') or salesforce_data.get('lead_company', 'Unknown Company')
        else:
            first_name = lead_info.get('first_name', '')
            last_name = lead_info.get('last_name', '')
            title = 'Unknown Title'
            company = lead_info.get('company_name', 'Unknown Company')
        
        name = f"{first_name} {last_name}".strip() if first_name or last_name else "Name not provided"
        
        analysis = []
        
        # Lead/Contact Analysis Section
        if not is_multiple and (first_name or last_name):
            analysis.append(f"**Name:** {name}")
        
        analysis.append(f"**Title and Company:** {title} at {company}")
        analysis.append(f"**ICP Fit:** {assessment.get('icp_fit', 'Unknown')}")
        analysis.append(f"**Reasoning:** {assessment.get('reasoning', 'Unable to assess due to insufficient data')}")
        analysis.append(f"**Confidence:** {assessment.get('confidence', 'Low')}")
        analysis.append(f"**Confidence Reasoning:** {assessment.get('confidence_reasoning', 'Assessment based on limited available data')}")
        
        analysis.append("")
        
        # Engagement Strategy Section
        analysis.append("**Question:** \"Is there specific context about your outreach goals, timing, or company priorities that would help me create the most effective engagement approach for this lead?\"")
        
        return "\n".join(analysis)
    
    def invoke_claude_with_inference_profile(self, messages: List[Dict], system_prompt: str = "") -> Dict[str, Any]:
        """
        Invoke Claude 3.7 using inference profile for enhanced analysis
        """
        try:
            # Prepare the request payload
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": 0.1,
                "messages": messages
            }
            
            # Add system prompt if provided
            if system_prompt:
                request_body["system"] = system_prompt
            
            # Use inference profile for Claude 3.7
            response = self.bedrock_client.invoke_model(
                modelId=self.inference_profile_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            return {
                "success": True,
                "content": response_body['content'][0]['text'],
                "usage": response_body.get('usage', {})
            }
            
        except Exception as e:
            print(f"Error invoking Claude 3.7: {str(e)}")
            return {
                "success": False,
                "error": f"Error invoking Claude 3.7: {str(e)}"
            }
    
    def process_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for processing lead analysis requests
        """
        try:
            # Extract user query
            user_query = event.get("query", event.get("user_query", ""))
            
            if not user_query:
                return {
                    "success": False,
                    "error": "No query provided for lead analysis"
                }
            
            # Extract lead information
            lead_info = self.extract_lead_info(user_query)
            
            if not lead_info:
                return {
                    "success": False,
                    "error": "Could not extract lead information from query. Please specify the lead name, email, or company clearly."
                }
            
            # Check if this is a multiple lead analysis request
            is_multiple = any(word in user_query.lower() for word in ['leads', 'contacts', 'group', 'multiple', 'batch'])
            
            # For now, handle single lead analysis
            # TODO: Implement multiple lead analysis
            if is_multiple:
                return {
                    "success": False,
                    "error": "Multiple lead analysis not yet implemented. Please analyze one lead at a time."
                }
            
            # Perform lead analysis
            analysis_result = self.analyze_lead(lead_info)
            
            if not analysis_result.get("success"):
                return analysis_result
            
            # Format the response
            formatted_analysis = self.format_lead_analysis(analysis_result, is_multiple)
            
            return {
                "success": True,
                "analysis": formatted_analysis,
                "lead_info": lead_info,
                "assessment": analysis_result.get("assessment", {}),
                "data_sources": {
                    "salesforce_found": bool(analysis_result.get("salesforce_data")),
                    "web_research_performed": bool(analysis_result.get("web_research", {}).get("success"))
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing lead analysis request: {str(e)}"
            }

def lambda_handler(event, context):
    """
    AWS Lambda handler for Lead Analysis Agent
    """
    print(f"Lead Analysis Agent invoked with event: {json.dumps(event)}")
    
    agent = LeadAnalysisAgent()
    result = agent.process_request(event)
    
    print(f"Lead Analysis Agent result: {json.dumps(result)}")
    return result

if __name__ == "__main__":
    # Test the agent locally
    test_event = {
        "query": "Assess John Smith from DataCorp as a lead"
    }
    
    agent = LeadAnalysisAgent()
    result = agent.process_request(test_event)
    print(json.dumps(result, indent=2))