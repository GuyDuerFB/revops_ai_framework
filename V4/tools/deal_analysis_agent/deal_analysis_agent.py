"""
Deal Analysis Agent for RevOps AI Framework V4

This agent specializes in comprehensive deal assessment and status analysis,
providing structured insights with MEDDPICC evaluation and risk/opportunity assessment.
"""

import json
import os
import sys
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the tools directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))

class DealAnalysisAgent:
    """
    Specialized agent for deal analysis with embedded SQL queries and MEDDPICC framework
    """
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize the Deal Analysis Agent"""
        self.region_name = region_name
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        
        # Claude 3.7 with inference profile configuration
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        self.inference_profile_id = os.environ.get('INFERENCE_PROFILE_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        
        # Tool configurations
        self.firebolt_query_function = os.environ.get('FIREBOLT_QUERY_FUNCTION', 'revops-firebolt-query')
        
        # Agent collaboration endpoints
        self.data_agent_function = os.environ.get('DATA_AGENT_FUNCTION', 'revops-data-agent')
        self.web_search_agent_function = os.environ.get('WEB_SEARCH_AGENT_FUNCTION', 'revops-web-search-agent')
        self.execution_agent_function = os.environ.get('EXECUTION_AGENT_FUNCTION', 'revops-execution-agent')
    
    def get_opportunity_data(self, company_name: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive opportunity data using embedded SQL query
        """
        query = f"""
        SELECT 
          o.opportunity_id, 
          o.opportunity_name, 
          o.stage_name, 
          o.amount as tcv,
          (o.amount/o.contract_duration_months) * 12 as acv,
          o.closed_at_date, 
          o.probability, 
          o.metrics,
          o.metrics_status,
          o.economic_buyer,
          o.economic_buyer_status,
          o.identify_pain,
          o.identify_pain_status,
          o.champion,
          o.champion_status,
          o.decision_criteria,
          o.decision_criteria_status,
          o.competition,
          o.competition_status,
          o.competitors,
          o.decision_making_process,
          o.decision_making_process_status,
          o.decision_timeline_date,
          o.paper_process,
          o.paper_process_status,
          o.next_step,
          o.created_at_ts, 
          o.dbt_last_updated_ts, 
          opp_owner.first_name || ' ' || opp_owner.last_name as opportunity_owner,
          account_owner.first_name || ' ' || account_owner.last_name as account_owner,
          s.sf_account_name, 
          s.sf_account_id 
        FROM 
          opportunity_d o 
        JOIN 
          salesforce_account_d s ON s.sf_account_id = o.sf_account_id 
        JOIN
          employee_d opp_owner ON o.owner_id = opp_owner.sf_user_id
        JOIN 
          employee_d account_owner ON account_owner.sf_user_id = s.sf_owner_id
        WHERE UPPER(s.sf_account_name) ILIKE '%{company_name.upper()}%' OR UPPER(o.opportunity_name) ILIKE '%{company_name.upper()}%' 
        ORDER BY o.dbt_last_updated_ts DESC
        """
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.firebolt_query_function,
                Payload=json.dumps({"query": query})
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error retrieving opportunity data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_call_data(self, company_name: str) -> Dict[str, Any]:
        """
        Retrieve call data using embedded SQL query
        """
        query = f"""
        SELECT 
          gong_call_name, 
          gong_call_start_ts, 
          gong_call_brief, 
          gong_participants_emails 
        FROM gong_call_f g 
          left join salesforce_account_d p_sf on p_sf.sf_account_id = g.gong_primary_account 
          left join salesforce_account_d a_sf on a_sf.sf_account_id = g.gong_related_account 
          left join opportunity_d a_o on a_o.opportunity_id = g.gong_related_opportunity
          left join opportunity_d p_o on p_o.opportunity_id = g.gong_primary_opportunity
          left join lead_d l on l.lead_id = g.gong_related_lead
          left join contact_d c on c.contact_id = g.gong_related_contact
          WHERE p_sf.sf_account_name ILIKE '%{company_name}%' 
              OR a_sf.sf_account_name ILIKE '%{company_name}%'
              OR UPPER(gong_title) ILIKE '%{company_name.upper()}%'
              OR a_o.opportunity_name ILIKE '%{company_name}%'
              OR p_o.opportunity_name ILIKE '%{company_name}%'
              OR l.email ILIKE '%{company_name}%'
              OR c.contact_email ILIKE '%{company_name}%'
        ORDER BY gong_call_start_ts DESC LIMIT 10
        """
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.firebolt_query_function,
                Payload=json.dumps({"query": query})
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            print(f"Error retrieving call data: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def collaborate_with_data_agent(self, request: str) -> Dict[str, Any]:
        """
        Collaborate with Data Agent for complex queries
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
    
    def extract_company_name(self, query: str) -> str:
        """
        Extract company name from deal analysis queries
        """
        # Common patterns for deal queries
        patterns = [
            "status of the",
            "status of",
            "deal with",
            "deal for",
            "analyze the",
            "analyze",
            "review the",
            "review",
            "about the",
            "about"
        ]
        
        query_lower = query.lower()
        
        for pattern in patterns:
            if pattern in query_lower:
                # Extract company name after pattern
                start_idx = query_lower.find(pattern) + len(pattern)
                remaining = query[start_idx:].strip()
                
                # Clean up common words
                remaining = remaining.replace(" deal", "").replace(" opportunity", "")
                remaining = remaining.replace("?", "").replace(".", "").strip()
                
                if remaining:
                    return remaining
        
        # Fallback: look for company names in the query
        words = query.split()
        for word in words:
            if word.upper() in ["IXIS", "ACME", "MICROSOFT", "GOOGLE", "SALESFORCE"]:
                return word
        
        return ""
    
    def analyze_deal(self, company_name: str) -> Dict[str, Any]:
        """
        Perform comprehensive deal analysis
        """
        print(f"Starting deal analysis for: {company_name}")
        
        # Step 1A: Get opportunity data
        opportunity_data = self.get_opportunity_data(company_name)
        
        if not opportunity_data.get("success", False):
            return {
                "success": False,
                "error": "Failed to retrieve opportunity data",
                "details": opportunity_data
            }
        
        # Step 1B: Get call data
        call_data = self.get_call_data(company_name)
        
        if not call_data.get("success", False):
            print(f"Warning: Failed to retrieve call data for {company_name}")
            call_data = {"success": True, "results": []}
        
        # Step 2: Analyze and format response using Claude 3.7
        analysis = self.enhance_analysis_with_claude(opportunity_data, call_data, company_name)
        
        return {
            "success": True,
            "analysis": analysis,
            "company_name": company_name,
            "data_sources": {
                "opportunity_count": len(opportunity_data.get("results", [])),
                "call_count": len(call_data.get("results", []))
            }
        }
    
    def format_deal_analysis(self, opportunity_data: Dict, call_data: Dict, company_name: str) -> str:
        """
        Format the deal analysis in the required structure
        """
        opportunities = opportunity_data.get("results", [])
        calls = call_data.get("results", [])
        
        if not opportunities:
            return f"No active opportunities found for {company_name}. Please verify the company name or check if there are any deals in the system."
        
        # Get the most recent opportunity
        primary_opp = opportunities[0]
        
        # Format the response according to user requirements
        analysis = []
        
        # A. The Dry Numbers
        analysis.append("## A. The Dry Numbers")
        
        acv = primary_opp.get("acv", 0)
        if acv and acv > 0:
            analysis.append(f"- **Deal Size (ACV)**: ${acv:,.0f}")
        else:
            tcv = primary_opp.get("tcv", 0)
            analysis.append(f"- **Deal Size (TCV)**: ${tcv:,.0f}")
        
        close_date = primary_opp.get("closed_at_date", "")
        if close_date:
            try:
                date_obj = datetime.strptime(close_date, "%Y-%m-%d")
                quarter = f"Q{((date_obj.month - 1) // 3) + 1}"
                analysis.append(f"- **Close Quarter**: {quarter} {date_obj.year}")
            except:
                analysis.append(f"- **Close Quarter**: {close_date}")
        
        owner = primary_opp.get("opportunity_owner", "Unknown")
        analysis.append(f"- **Owner**: {owner}")
        
        account_name = primary_opp.get("sf_account_name", company_name)
        stage = primary_opp.get("stage_name", "Unknown")
        pain = primary_opp.get("identify_pain", "")
        
        if pain:
            pain_summary = pain.replace("<br>", " ").replace("&#39;", "'")[:200] + "..." if len(pain) > 200 else pain.replace("<br>", " ").replace("&#39;", "'")
            analysis.append(f"- **Account Description**: {account_name} is in {stage} stage. {pain_summary}")
        else:
            analysis.append(f"- **Account Description**: {account_name} opportunity in {stage} stage.")
        
        analysis.append("")
        
        # B. Bottom Line Assessment
        analysis.append("## B. Bottom Line Assessment")
        
        probability = primary_opp.get("probability", 0)
        stage = primary_opp.get("stage_name", "")
        
        # Analyze call data for realistic assessment
        recent_calls = len([call for call in calls if call.get("gong_call_start_ts")])
        
        if recent_calls > 0 and stage == "Negotiate":
            analysis.append(f"**Honest Assessment**: Deal shows strong engagement with {recent_calls} recent calls and progression to {stage} stage. Based on active customer interaction and current stage, this appears to be a legitimate opportunity with good momentum, though specific risks need monitoring.")
        elif recent_calls > 0:
            analysis.append(f"**Honest Assessment**: Deal has {recent_calls} recent calls indicating active engagement, currently in {stage} stage. Engagement level suggests genuine interest, but progression to advanced stages still needs validation.")
        else:
            analysis.append(f"**Honest Assessment**: Limited recent call activity detected for a deal in {stage} stage. This raises concerns about actual customer engagement and deal momentum. Recommend immediate outreach to validate opportunity status.")
        
        analysis.append("")
        
        # C. Risks and Opportunities
        analysis.append("## C. Risks and Opportunities")
        
        # C.1 Major Risks
        analysis.append("### C.1 Major Risks")
        
        # Analyze MEDDPICC gaps
        meddpicc_risks = []
        
        economic_buyer_status = primary_opp.get("economic_buyer_status", "")
        if economic_buyer_status in ["No Assessment", "Partial Understanding", ""]:
            meddpicc_risks.append("**Economic Buyer Risk**: Economic buyer not clearly identified or engaged")
        
        decision_criteria_status = primary_opp.get("decision_criteria_status", "")
        if decision_criteria_status in ["No Assessment", ""]:
            meddpicc_risks.append("**Decision Criteria Risk**: Unclear decision criteria may lead to unexpected evaluation factors")
        
        competition = primary_opp.get("competitors", "")
        if competition and "Snowflake" in competition:
            meddpicc_risks.append("**Competitive Risk**: Competing against established incumbents like Snowflake")
        
        # Add call-based risks
        if recent_calls == 0:
            meddpicc_risks.append("**Engagement Risk**: No recent call activity suggests limited stakeholder engagement")
        
        for risk in meddpicc_risks[:3]:  # Limit to 3 risks
            analysis.append(f"- {risk}")
        
        analysis.append("")
        
        # C.2 Major Opportunities
        analysis.append("### C.2 Major Opportunities/Positive Points")
        
        opportunities_list = []
        
        champion = primary_opp.get("champion", "")
        if champion and "CTO" in champion:
            opportunities_list.append("**Champion Strength**: CTO-level champion provides technical decision-making authority")
        
        pain = primary_opp.get("identify_pain", "")
        if pain and "cost" in pain.lower():
            opportunities_list.append("**Pain Alignment**: Clear cost pain with current solution creates strong motivation to switch")
        
        if recent_calls > 3:
            opportunities_list.append(f"**Engagement Quality**: {recent_calls} recent calls demonstrate sustained customer interest and active evaluation")
        
        # Add more opportunities based on data
        if stage == "Negotiate":
            opportunities_list.append("**Stage Progression**: Deal has progressed to negotiation stage indicating serious buyer intent")
        
        for opp in opportunities_list[:3]:  # Limit to 3 opportunities
            analysis.append(f"- {opp}")
        
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
    
    def enhance_analysis_with_claude(self, opportunity_data: Dict, call_data: Dict, company_name: str) -> str:
        """
        Use Claude 3.7 to enhance the deal analysis with deeper insights
        """
        # Prepare context for Claude
        context = f"""
        Company: {company_name}
        
        Opportunity Data:
        {json.dumps(opportunity_data.get('results', []), indent=2)}
        
        Call Data:
        {json.dumps(call_data.get('results', []), indent=2)}
        """
        
        system_prompt = """
        You are a Deal Analysis Agent specializing in MEDDPICC evaluation and deal assessment.
        
        Your task is to analyze the provided opportunity and call data to generate a comprehensive deal assessment.
        
        REQUIRED OUTPUT FORMAT:
        
        ## A. The Dry Numbers
        - **Deal Size (ACV)**: $X,XXX 
        - **Close Quarter**: QX 20XX
        - **Owner**: [Opportunity Owner Name]
        - **Account Description**: [2-3 sentence summary]
        
        ## B. Bottom Line Assessment
        **Honest Assessment**: [Realistic assessment in 2-3 sentences, disregarding CRM probability]
        
        ## C. Risks and Opportunities
        ### C.1 Major Risks
        - **[Risk Category]**: [Specific risk based on data]
        - **[Risk Category]**: [Specific risk based on data]
        - **[Risk Category]**: [Specific risk based on data]
        
        ### C.2 Major Opportunities/Positive Points
        - **[Opportunity Category]**: [Specific opportunity based on data]
        - **[Opportunity Category]**: [Specific opportunity based on data]
        - **[Opportunity Category]**: [Specific opportunity based on data]
        
        Be direct, data-driven, and honest in your assessment.
        """
        
        messages = [
            {
                "role": "user",
                "content": f"Analyze this deal data and provide a comprehensive assessment:\n\n{context}"
            }
        ]
        
        # Invoke Claude 3.7
        result = self.invoke_claude_with_inference_profile(messages, system_prompt)
        
        if result.get("success"):
            return result["content"]
        else:
            # Fallback to the original analysis method
            return self.format_deal_analysis(opportunity_data, call_data, company_name)
    
    def process_request(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for processing deal analysis requests
        """
        try:
            # Extract user query
            user_query = event.get("query", event.get("user_query", ""))
            
            if not user_query:
                return {
                    "success": False,
                    "error": "No query provided for deal analysis"
                }
            
            # Extract company name
            company_name = self.extract_company_name(user_query)
            
            if not company_name:
                return {
                    "success": False,
                    "error": "Could not extract company name from query. Please specify the company name clearly."
                }
            
            # Perform deal analysis
            result = self.analyze_deal(company_name)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing deal analysis request: {str(e)}"
            }

def lambda_handler(event, context):
    """
    AWS Lambda handler for Deal Analysis Agent
    """
    print(f"Deal Analysis Agent invoked with event: {json.dumps(event)}")
    
    agent = DealAnalysisAgent()
    result = agent.process_request(event)
    
    print(f"Deal Analysis Agent result: {json.dumps(result)}")
    return result

if __name__ == "__main__":
    # Test the agent locally
    test_event = {
        "query": "What is the status of the IXIS deal?"
    }
    
    agent = DealAnalysisAgent()
    result = agent.process_request(test_event)
    print(json.dumps(result, indent=2))