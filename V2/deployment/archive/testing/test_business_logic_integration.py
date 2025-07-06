#!/usr/bin/env python3
"""
Focused Business Logic Integration Testing
==========================================

Tests specific business logic integration patterns with scoring and optimization tracking.
"""

import boto3
import json
import logging
import time
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class BusinessLogicTester:
    """Focused testing for business logic integration"""
    
    def __init__(self, profile_name: str = "revops-dev-profile"):
        session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
        self.bedrock_runtime = session.client('bedrock-agent-runtime')
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        self.agent_id = config.get('data_agent', {}).get('agent_id')
        self.agent_alias_id = config.get('data_agent', {}).get('agent_alias_id')
    
    def test_single_business_logic_pattern(self, test_name: str, query: str, expected_patterns: List[str]) -> Dict[str, Any]:
        """Test a single business logic pattern with detailed analysis"""
        
        logger.info(f"🧪 Testing: {test_name}")
        
        try:
            session_id = f"bl-test-{int(time.time())}"
            
            response = self.bedrock_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=query
            )
            
            # Collect response
            full_response = ""
            for event in response['completion']:
                if 'chunk' in event and 'bytes' in event['chunk']:
                    full_response += event['chunk']['bytes'].decode('utf-8')
            
            # Analyze patterns
            found_patterns = []
            missing_patterns = []
            
            for pattern in expected_patterns:
                if pattern.lower() in full_response.lower():
                    found_patterns.append(pattern)
                else:
                    missing_patterns.append(pattern)
            
            # Calculate scores
            pattern_score = len(found_patterns) / len(expected_patterns)
            
            # Business logic structure analysis
            structure_checks = {
                "has_customer_segmentation": any(term in full_response.lower() for term in ["commit", "plg", "prospect", "customer_type"]),
                "has_temporal_analysis": any(term in full_response.lower() for term in ["daily_rate", "4 days", "temporal", "incomplete"]),
                "has_business_context": any(term in full_response.lower() for term in ["benchmark", "threshold", "health", "risk"]),
                "structured_output": any(term in full_response.lower() for term in ["json", "analysis_summary", "customer_segmentation"])
            }
            
            structure_score = sum(structure_checks.values()) / len(structure_checks)
            overall_score = (pattern_score + structure_score) / 2
            
            result = {
                "test_name": test_name,
                "query": query,
                "overall_score": overall_score,
                "pattern_score": pattern_score,
                "structure_score": structure_score,
                "found_patterns": found_patterns,
                "missing_patterns": missing_patterns,
                "structure_analysis": structure_checks,
                "response_length": len(full_response),
                "response_preview": full_response[:400] + "..." if len(full_response) > 400 else full_response
            }
            
            # Log results
            status = "✅ EXCELLENT" if overall_score >= 0.8 else "✅ GOOD" if overall_score >= 0.6 else "⚠️ NEEDS WORK" if overall_score >= 0.4 else "❌ POOR"
            logger.info(f"📊 {status} - Overall: {overall_score:.2f}, Patterns: {pattern_score:.2f}, Structure: {structure_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return {
                "test_name": test_name,
                "error": str(e),
                "overall_score": 0.0
            }
    
    def run_optimization_tests(self) -> Dict[str, Any]:
        """Run focused optimization tests"""
        
        logger.info("🚀 Starting Business Logic Integration Tests")
        logger.info("=" * 60)
        
        test_cases = [
            {
                "name": "Customer Segmentation Enforcement",
                "query": "Show me Q2 2025 revenue by customer type",
                "patterns": ["commit", "plg", "prospect", "customer_type", "sf_account_type_custom"]
            },
            {
                "name": "Temporal Analysis Integration", 
                "query": "Compare Q3 2025 vs Q2 2025 revenue with proper temporal analysis",
                "patterns": ["daily_rate", "4 days", "temporal", "incomplete", "projection"]
            },
            {
                "name": "Knowledge Base Integration",
                "query": "What business logic should I apply for customer classification?",
                "patterns": ["knowledge", "$200", "credits", "commit customer", "plg customer"]
            },
            {
                "name": "Structured Output Format",
                "query": "Analyze revenue trends and provide structured business analysis",
                "patterns": ["analysis_summary", "customer_segmentation", "business_context", "json"]
            }
        ]
        
        results = []
        total_score = 0
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"🧪 Test {i}/{len(test_cases)}: {test_case['name']}")
            
            result = self.test_single_business_logic_pattern(
                test_case['name'],
                test_case['query'], 
                test_case['patterns']
            )
            
            results.append(result)
            total_score += result.get('overall_score', 0)
            
            logger.info("-" * 40)
        
        # Calculate overall optimization score
        avg_score = total_score / len(results)
        
        logger.info("=" * 60)
        logger.info(f"🎯 OPTIMIZATION SCORE: {avg_score:.2f}/1.00")
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(results, avg_score)
        
        # Save detailed report
        self.save_optimization_report(results, avg_score, recommendations)
        
        return {
            "overall_score": avg_score,
            "test_results": results,
            "recommendations": recommendations
        }
    
    def generate_optimization_recommendations(self, results: List[Dict], overall_score: float) -> List[str]:
        """Generate specific optimization recommendations"""
        
        recommendations = []
        
        # Overall score recommendations
        if overall_score < 0.6:
            recommendations.append("🚨 URGENT: Update agent instructions with enhanced v3 optimized version")
            recommendations.append("🔧 Add explicit business logic enforcement in instructions")
        
        # Pattern-specific recommendations
        pattern_issues = {}
        for result in results:
            for missing in result.get('missing_patterns', []):
                pattern_issues[missing] = pattern_issues.get(missing, 0) + 1
        
        # Most common missing patterns
        for pattern, count in sorted(pattern_issues.items(), key=lambda x: x[1], reverse=True)[:3]:
            if count >= 2:  # Missing in 2+ tests
                recommendations.append(f"🎯 Focus on integrating '{pattern}' - missing in {count} tests")
        
        # Structure-specific recommendations
        structure_issues = []
        for result in results:
            structure = result.get('structure_analysis', {})
            for check, passed in structure.items():
                if not passed:
                    structure_issues.append(check)
        
        structure_counts = {}
        for issue in structure_issues:
            structure_counts[issue] = structure_counts.get(issue, 0) + 1
        
        for issue, count in structure_counts.items():
            if count >= 2:
                issue_name = issue.replace('has_', '').replace('_', ' ').title()
                recommendations.append(f"📊 Improve {issue_name} - failing in {count} tests")
        
        # Specific optimization tactics
        if overall_score < 0.8:
            recommendations.extend([
                "📚 Add knowledge base query examples to instructions",
                "🔍 Include mandatory pre-analysis checklists",
                "📋 Enforce structured JSON output format",
                "⚡ Add validation steps before response generation"
            ])
        
        return recommendations
    
    def save_optimization_report(self, results: List[Dict], overall_score: float, recommendations: List[str]) -> None:
        """Save detailed optimization report"""
        
        report = f"""# Data Agent Business Logic Integration Optimization Report

## 🎯 Overall Optimization Score: {overall_score:.2f}/1.00

### Score Interpretation:
- **0.8-1.0**: Excellent integration - minimal optimization needed
- **0.6-0.8**: Good integration - minor improvements recommended  
- **0.4-0.6**: Needs work - moderate optimization required
- **0.0-0.4**: Poor integration - major optimization needed

## 📊 Test Results Summary

| Test Name | Overall Score | Pattern Score | Structure Score | Status |
|-----------|---------------|---------------|-----------------|---------|
"""
        
        for result in results:
            overall = result.get('overall_score', 0)
            pattern = result.get('pattern_score', 0) 
            structure = result.get('structure_score', 0)
            status = "✅ Excellent" if overall >= 0.8 else "✅ Good" if overall >= 0.6 else "⚠️ Needs Work" if overall >= 0.4 else "❌ Poor"
            
            report += f"| {result.get('test_name', 'Unknown')} | {overall:.2f} | {pattern:.2f} | {structure:.2f} | {status} |\n"
        
        report += f"""
## 🔍 Detailed Test Analysis

"""
        
        for result in results:
            report += f"""
### {result.get('test_name', 'Unknown Test')}
- **Overall Score**: {result.get('overall_score', 0):.2f}
- **Query**: {result.get('query', 'N/A')}
- **Found Patterns**: {', '.join(result.get('found_patterns', []))}
- **Missing Patterns**: {', '.join(result.get('missing_patterns', []))}
- **Structure Analysis**: {result.get('structure_analysis', {})}
- **Response Preview**: {result.get('response_preview', 'No response')[:300]}
"""
        
        report += f"""
## 🎯 Optimization Recommendations

"""
        
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
        
        report += f"""
## 🚀 Next Steps

### Immediate Actions (if score < 0.6):
1. Update Data Agent with `instructions_v3_optimized.md`
2. Test with simplified queries to validate basic integration
3. Re-run optimization tests to measure improvement

### Ongoing Optimization (if score 0.6-0.8):
1. Fine-tune specific missing patterns
2. Enhance knowledge base query examples
3. Add more explicit business logic triggers

### Maintenance (if score > 0.8):
1. Regular testing to maintain performance
2. Monitor for regression after updates
3. Add new business logic patterns as needed

---
**Report Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Test Environment**: Data Agent {self.agent_id}
"""
        
        with open('business_logic_optimization_report.md', 'w') as f:
            f.write(report)
        
        logger.info("📄 Optimization report saved: business_logic_optimization_report.md")

def main():
    tester = BusinessLogicTester()
    results = tester.run_optimization_tests()
    
    score = results['overall_score']
    if score >= 0.8:
        logger.info("🎉 Excellent business logic integration!")
    elif score >= 0.6:
        logger.info("✅ Good integration - minor optimization recommended")
    elif score >= 0.4:
        logger.info("⚠️ Needs optimization work")
    else:
        logger.info("🚨 Major optimization required")

if __name__ == "__main__":
    main()