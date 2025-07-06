#!/usr/bin/env python3
"""
Data Agent Business Logic Integration Diagnostic
==============================================

Analyzes current Data Agent performance and identifies optimization opportunities.
"""

import boto3
import json
import logging
import time
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class DataAgentDiagnostic:
    """Diagnostic tool for Data Agent business logic integration"""
    
    def __init__(self, profile_name: str = "revops-dev-profile"):
        session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
        self.bedrock_runtime = session.client('bedrock-agent-runtime')
        self.bedrock_agent = session.client('bedrock-agent')
        
        # Load config
        with open('config.json', 'r') as f:
            self.config = json.load(f)
        
        self.agent_id = self.config.get('data_agent', {}).get('agent_id')
        self.agent_alias_id = self.config.get('data_agent', {}).get('agent_alias_id')
        self.kb_id = self.config.get('knowledge_base', {}).get('knowledge_base_id')
    
    def test_business_logic_queries(self) -> Dict[str, Any]:
        """Test specific business logic integration patterns"""
        
        test_cases = [
            {
                "name": "Customer Segmentation",
                "query": "Show me revenue breakdown by customer type (Commit, PLG, Prospect) for Q2 2025",
                "expected_elements": ["commit", "plg", "prospect", "customer_type", "sf_account_type_custom"],
                "business_logic": "Customer classification from knowledge base"
            },
            {
                "name": "Temporal Analysis", 
                "query": "Compare Q3 2025 vs Q2 2025 revenue accounting for incomplete period",
                "expected_elements": ["daily_rate", "temporal", "4 days", "incomplete", "projection"],
                "business_logic": "Temporal analysis patterns"
            },
            {
                "name": "Risk Assessment",
                "query": "Identify customers at risk of churn based on usage patterns", 
                "expected_elements": ["risk_score", "churn", "usage_trend", "engagement", "health"],
                "business_logic": "Risk assessment workflow"
            },
            {
                "name": "Knowledge Base Integration",
                "query": "What are the thresholds for customer type classification?",
                "expected_elements": ["$200", "credits", "contract", "threshold", "classification"],
                "business_logic": "Direct knowledge base retrieval"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            logger.info(f"🧪 Testing: {test_case['name']}")
            
            try:
                response = self.bedrock_runtime.invoke_agent(
                    agentId=self.agent_id,
                    agentAliasId=self.agent_alias_id,
                    sessionId=f"diagnostic-{int(time.time())}-{test_case['name'].lower().replace(' ', '-')}",
                    inputText=test_case['query']
                )
                
                # Collect full response
                full_response = ""
                for event in response['completion']:
                    if 'chunk' in event and 'bytes' in event['chunk']:
                        full_response += event['chunk']['bytes'].decode('utf-8')
                
                # Analyze response
                found_elements = []
                for element in test_case['expected_elements']:
                    if element.lower() in full_response.lower():
                        found_elements.append(element)
                
                integration_score = len(found_elements) / len(test_case['expected_elements'])
                
                result = {
                    "test_name": test_case['name'],
                    "query": test_case['query'],
                    "business_logic": test_case['business_logic'],
                    "integration_score": integration_score,
                    "found_elements": found_elements,
                    "missing_elements": [e for e in test_case['expected_elements'] if e not in found_elements],
                    "response_preview": full_response[:300] + "..." if len(full_response) > 300 else full_response
                }
                
                results.append(result)
                logger.info(f"📊 Score: {integration_score:.2f} ({len(found_elements)}/{len(test_case['expected_elements'])})")
                
            except Exception as e:
                logger.error(f"❌ Test failed: {e}")
                results.append({
                    "test_name": test_case['name'],
                    "error": str(e),
                    "integration_score": 0.0
                })
        
        return results
    
    def analyze_knowledge_base_usage(self) -> Dict[str, Any]:
        """Analyze how well the agent is using the knowledge base"""
        
        logger.info("🔍 Analyzing knowledge base integration...")
        
        # Test direct KB queries
        kb_queries = [
            "customer classification rules",
            "temporal analysis patterns", 
            "risk assessment criteria",
            "SQL query templates"
        ]
        
        kb_results = []
        
        for query in kb_queries:
            try:
                response = self.bedrock_runtime.retrieve(
                    knowledgeBaseId=self.kb_id,
                    retrievalQuery={'text': query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {'numberOfResults': 3}
                    }
                )
                
                results = response.get('retrievalResults', [])
                avg_score = sum(r.get('score', 0) for r in results) / max(len(results), 1)
                
                kb_results.append({
                    "query": query,
                    "results_count": len(results),
                    "avg_score": avg_score,
                    "top_score": max([r.get('score', 0) for r in results]) if results else 0
                })
                
            except Exception as e:
                logger.error(f"❌ KB query failed: {e}")
        
        return kb_results
    
    def check_agent_configuration(self) -> Dict[str, Any]:
        """Check agent configuration for optimization opportunities"""
        
        logger.info("⚙️ Checking agent configuration...")
        
        try:
            agent_info = self.bedrock_agent.get_agent(agentId=self.agent_id)
            agent = agent_info['agent']
            
            # Check knowledge base associations
            kb_associations = self.bedrock_agent.list_agent_knowledge_bases(
                agentId=self.agent_id,
                agentVersion="DRAFT"
            )
            
            config_analysis = {
                "foundation_model": agent.get('foundationModel'),
                "agent_status": agent.get('agentStatus'),
                "instructions_length": len(agent.get('instruction', '')),
                "knowledge_bases_count": len(kb_associations.get('agentKnowledgeBaseSummaries', [])),
                "kb_associated": len(kb_associations.get('agentKnowledgeBaseSummaries', [])) > 0
            }
            
            return config_analysis
            
        except Exception as e:
            logger.error(f"❌ Configuration check failed: {e}")
            return {"error": str(e)}
    
    def generate_optimization_report(self) -> None:
        """Generate comprehensive optimization report"""
        
        logger.info("📋 Generating optimization report...")
        
        # Run diagnostics
        business_logic_results = self.test_business_logic_queries()
        kb_analysis = self.analyze_knowledge_base_usage() 
        config_analysis = self.check_agent_configuration()
        
        # Calculate overall scores
        overall_integration_score = sum(r.get('integration_score', 0) for r in business_logic_results) / len(business_logic_results)
        avg_kb_score = sum(r.get('avg_score', 0) for r in kb_analysis) / max(len(kb_analysis), 1)
        
        # Generate report
        report = f"""
# Data Agent Business Logic Integration Diagnostic Report

## 📊 Overall Assessment
- **Business Logic Integration Score**: {overall_integration_score:.2f}/1.00
- **Knowledge Base Retrieval Score**: {avg_kb_score:.3f}
- **Agent Status**: {config_analysis.get('agent_status', 'Unknown')}
- **Knowledge Base Associated**: {config_analysis.get('kb_associated', False)}

## 🧪 Business Logic Test Results

"""
        
        for result in business_logic_results:
            status = "✅ GOOD" if result.get('integration_score', 0) >= 0.7 else "⚠️ NEEDS WORK" if result.get('integration_score', 0) >= 0.4 else "❌ POOR"
            report += f"""
### {result.get('test_name')} - {status}
- **Score**: {result.get('integration_score', 0):.2f}
- **Business Logic**: {result.get('business_logic')}
- **Found Elements**: {', '.join(result.get('found_elements', []))}
- **Missing Elements**: {', '.join(result.get('missing_elements', []))}
- **Response Preview**: {result.get('response_preview', 'No response')}
"""
        
        report += f"""
## 🔍 Knowledge Base Analysis

"""
        
        for kb_result in kb_analysis:
            report += f"""
- **Query**: "{kb_result.get('query')}"
- **Results**: {kb_result.get('results_count')} (avg score: {kb_result.get('avg_score', 0):.3f})
"""
        
        report += f"""
## ⚙️ Configuration Analysis
- **Foundation Model**: {config_analysis.get('foundation_model')}
- **Instructions Length**: {config_analysis.get('instructions_length', 0)} characters
- **Knowledge Bases**: {config_analysis.get('knowledge_bases_count', 0)} associated

## 🎯 Optimization Recommendations

"""
        
        recommendations = []
        
        if overall_integration_score < 0.7:
            recommendations.append("**Enhance Instructions**: Add more explicit business logic requirements")
            
        if avg_kb_score < 0.5:
            recommendations.append("**Improve KB Integration**: Add knowledge base query examples to instructions")
            
        if not config_analysis.get('kb_associated'):
            recommendations.append("**Associate Knowledge Base**: Ensure knowledge base is properly linked")
            
        # Add specific recommendations based on test results
        for result in business_logic_results:
            if result.get('integration_score', 0) < 0.5:
                test_name = result.get('test_name')
                missing = result.get('missing_elements', [])
                recommendations.append(f"**Fix {test_name}**: Focus on including {', '.join(missing[:3])}")
        
        for rec in recommendations:
            report += f"- {rec}\n"
        
        # Save report
        with open('data_agent_diagnostic_report.md', 'w') as f:
            f.write(report)
        
        logger.info("📄 Report saved to: data_agent_diagnostic_report.md")
        logger.info(f"🎯 Overall Integration Score: {overall_integration_score:.2f}/1.00")

def main():
    diagnostic = DataAgentDiagnostic()
    diagnostic.generate_optimization_report()

if __name__ == "__main__":
    main()