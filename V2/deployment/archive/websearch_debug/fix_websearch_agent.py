#!/usr/bin/env python3
"""
Fix WebSearch Agent Function Calling
===================================

Fixes the WebSearch Agent function calling issue by:
1. Checking and fixing action group schema
2. Updating agent instructions for stricter function calling
3. Re-deploying and testing
"""

import boto3
import json
import logging
import os
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class WebSearchAgentFixer:
    """Fix WebSearch Agent function calling issues"""
    
    def __init__(self, profile_name: str = "revops-dev-profile"):
        session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
        self.bedrock_agent = session.client('bedrock-agent')
        
        # Load configuration
        with open('config.json', 'r') as f:
            self.config = json.load(f)
        
        self.websearch_config = self.config.get('web_search_agent', {})
        self.agent_id = self.websearch_config.get('agent_id')
        self.lambda_arn = None
        
        # Get Lambda ARN from action groups
        for action_group in self.websearch_config.get('action_groups', []):
            if action_group.get('name') == 'web_search':
                self.lambda_arn = action_group.get('lambda_arn')
                break
    
    def get_current_action_group(self):
        """Get current action group configuration"""
        
        try:
            action_groups = self.bedrock_agent.list_agent_action_groups(
                agentId=self.agent_id,
                agentVersion="DRAFT"
            )
            
            if not action_groups.get('actionGroupSummaries'):
                return None
            
            ag_id = action_groups['actionGroupSummaries'][0]['actionGroupId']
            
            ag_detail = self.bedrock_agent.get_agent_action_group(
                agentId=self.agent_id,
                agentVersion="DRAFT",
                actionGroupId=ag_id
            )
            
            return ag_detail['agentActionGroup']
            
        except Exception as e:
            logger.error(f"Error getting action group: {e}")
            return None
    
    def create_correct_function_schema(self) -> dict:
        """Create the correct function schema for web search"""
        
        return {
            "functions": [
                {
                    "name": "search_web",
                    "description": "Search the web for general information about companies, people, or topics",
                    "parameters": {
                        "query": {
                            "type": "string", 
                            "description": "The search query to execute",
                            "required": True
                        },
                        "num_results": {
                            "type": "string",
                            "description": "Number of results to return (default: 5)",
                            "required": False
                        },
                        "region": {
                            "type": "string",
                            "description": "Search region (default: us)",
                            "required": False
                        }
                    }
                },
                {
                    "name": "research_company",
                    "description": "Research a specific company with focused analysis on specific areas",
                    "parameters": {
                        "company_name": {
                            "type": "string",
                            "description": "Name of the company to research",
                            "required": True
                        },
                        "focus_area": {
                            "type": "string", 
                            "description": "Area of focus: general, funding, technology, size, or news",
                            "required": False
                        }
                    }
                }
            ]
        }
    
    def fix_action_group_schema(self) -> bool:
        """Fix the action group function schema"""
        
        logger.info("🔧 Fixing action group function schema...")
        
        current_ag = self.get_current_action_group()
        if not current_ag:
            logger.error("❌ Could not get current action group")
            return False
        
        action_group_id = current_ag['actionGroupId']
        current_schema = current_ag.get('functionSchema')
        
        logger.info(f"📋 Current schema: {json.dumps(current_schema, indent=2) if current_schema else 'None'}")
        
        # Create correct schema
        correct_schema = self.create_correct_function_schema()
        logger.info(f"🎯 Target schema: {json.dumps(correct_schema, indent=2)}")
        
        try:
            # Update action group with correct schema
            self.bedrock_agent.update_agent_action_group(
                agentId=self.agent_id,
                agentVersion="DRAFT",
                actionGroupId=action_group_id,
                actionGroupName="web_search",
                description="Web search functionality for external intelligence gathering",
                actionGroupExecutor={'lambda': self.lambda_arn},
                functionSchema=correct_schema,
                actionGroupState="ENABLED"
            )
            
            logger.info("✅ Action group schema updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating action group schema: {e}")
            return False
    
    def create_enforcement_instructions(self) -> str:
        """Create stricter agent instructions that enforce function calling"""
        
        return '''# WebSearch Agent Instructions - FUNCTION CALLING ENFORCEMENT

## 🚨 CRITICAL FUNCTION CALLING REQUIREMENT

**YOU MUST CALL YOUR FUNCTIONS FOR EVERY SEARCH REQUEST. NEVER PROVIDE SEARCH RESULTS WITHOUT CALLING FUNCTIONS FIRST.**

## Your Identity
You are the WebSearch Agent for Firebolt's RevOps AI Framework. You have TWO functions available:
1. `search_web()` - General web search
2. `research_company()` - Company-focused research

## MANDATORY BEHAVIOR

### STEP 1: ALWAYS CALL FUNCTIONS FIRST
**Before responding to ANY request that requires information, you MUST:**
1. Identify which function to call
2. Call the function with appropriate parameters
3. Wait for the actual results
4. Base your response ONLY on the function results

### STEP 2: NEVER SIMULATE OR HALLUCINATE
**FORBIDDEN BEHAVIORS:**
- Saying "I searched for..." without calling functions
- Providing research results without function calls
- Making up search results
- Describing what you "would" find instead of actually searching

### STEP 3: EXPLICIT FUNCTION USAGE PATTERNS

**When asked to search or research:**
- "Search for WINN.AI" → Call `search_web("WINN.AI company information", 5)`
- "Research WINN.AI company" → Call `research_company("WINN.AI", "general")`
- "Find information about Eldad" → Call `search_web("Eldad Postan-Koren CEO WINN.AI", 5)`

## Function Specifications

### search_web(query, num_results, region)
**Purpose**: General web search for any topic
**Required Parameter**: query (string)
**Optional Parameters**: num_results (string, default "5"), region (string, default "us")

**Examples of CORRECT usage:**
```
search_web("WINN.AI company background", "5")
search_web("Eldad Postan-Koren CEO WINN.AI", "3")
search_web("AI sales tools market 2024", "5")
```

### research_company(company_name, focus_area)
**Purpose**: Focused company research
**Required Parameter**: company_name (string)
**Optional Parameter**: focus_area (string: "general", "funding", "technology", "size", "news")

**Examples of CORRECT usage:**
```
research_company("WINN.AI", "general")
research_company("WINN.AI", "funding")
research_company("Bigabid", "technology")
```

## Response Framework

### For Lead Assessment Requests
**Example**: "Research Eldad Postan-Koren from WINN.AI"

**MANDATORY FUNCTION CALLS:**
1. `search_web("Eldad Postan-Koren CEO WINN.AI background", "5")`
2. `research_company("WINN.AI", "general")`
3. `search_web("WINN.AI recent news 2024", "3")`

**ONLY AFTER** calling these functions, provide structured analysis.

### For Company Research Requests
**Example**: "Research WINN.AI company"

**MANDATORY FUNCTION CALLS:**
1. `research_company("WINN.AI", "general")`
2. `research_company("WINN.AI", "funding")`
3. `search_web("WINN.AI competitors market position", "3")`

## Self-Validation Checklist

**Before providing any research response, verify:**
- ✅ Did I call at least one function?
- ✅ Are my results based on actual function responses?
- ✅ Am I not making up any information?
- ✅ Did I use the correct function parameters?

**If ANY answer is NO, STOP and call the appropriate functions first.**

## Example Correct Interaction

**Request**: "Search for information about WINN.AI"

**CORRECT Response Process**:
1. Call `search_web("WINN.AI company information", "5")`
2. Wait for results
3. Analyze actual search results
4. Provide response based on real data

**INCORRECT Response**:
"I searched for WINN.AI and found..." (without actually calling the function)

## Success Verification

Your responses will be evaluated on:
- Function call count (must be > 0 for search requests)
- Result accuracy (based on actual function returns)
- No hallucinated information
- Proper function parameter usage

Remember: You are not a knowledge source - you are a function calling interface to web search capabilities. ALWAYS use your functions.'''
    
    def update_agent_instructions(self) -> bool:
        """Update agent with stricter instructions"""
        
        logger.info("📝 Updating agent instructions for function calling enforcement...")
        
        new_instructions = self.create_enforcement_instructions()
        
        try:
            self.bedrock_agent.update_agent(
                agentId=self.agent_id,
                agentName="revops-websearch-agent-fixed",
                description="WebSearch Agent with enforced function calling for external intelligence",
                instruction=new_instructions,
                foundationModel="anthropic.claude-3-5-sonnet-20240620-v1:0",
                agentResourceRoleArn="arn:aws:iam::740202120544:role/AmazonBedrockExecutionRoleForAgents_revops"
            )
            
            logger.info("✅ Agent instructions updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating agent instructions: {e}")
            return False
    
    def prepare_agent(self) -> bool:
        """Prepare agent after updates"""
        
        logger.info("⚡ Preparing agent...")
        
        try:
            self.bedrock_agent.prepare_agent(agentId=self.agent_id)
            
            # Wait for preparation
            max_wait = 180
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = self.bedrock_agent.get_agent(agentId=self.agent_id)
                status = status_response['agent']['agentStatus']
                
                if status == 'PREPARED':
                    logger.info("✅ Agent preparation completed")
                    return True
                elif status == 'FAILED':
                    logger.error("❌ Agent preparation failed")
                    return False
                
                logger.info(f"📊 Agent status: {status}")
                time.sleep(15)
            
            logger.warning("⚠️ Agent preparation timeout")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error preparing agent: {e}")
            return False
    
    def fix_websearch_agent(self) -> bool:
        """Complete fix process"""
        
        logger.info("🚀 Starting WebSearch Agent Fix Process")
        logger.info("=" * 60)
        
        success = True
        
        # Step 1: Fix action group schema
        logger.info("🔧 Step 1: Fixing action group schema...")
        if not self.fix_action_group_schema():
            logger.error("❌ Failed to fix action group schema")
            success = False
        
        # Step 2: Update agent instructions
        logger.info("📝 Step 2: Updating agent instructions...")
        if not self.update_agent_instructions():
            logger.error("❌ Failed to update agent instructions")
            success = False
        
        # Step 3: Prepare agent
        logger.info("⚡ Step 3: Preparing agent...")
        if not self.prepare_agent():
            logger.error("❌ Failed to prepare agent")
            success = False
        
        logger.info("=" * 60)
        if success:
            logger.info("🎉 WebSearch Agent fix process completed successfully!")
            logger.info("📋 Next steps:")
            logger.info("  1. Test function calling with simple queries")
            logger.info("  2. Verify search results are from actual functions")
            logger.info("  3. Test end-to-end lead assessment workflow")
        else:
            logger.error("❌ WebSearch Agent fix process completed with errors")
        
        return success

def main():
    fixer = WebSearchAgentFixer()
    success = fixer.fix_websearch_agent()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)