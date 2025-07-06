#!/usr/bin/env python3
"""
Simple Compliance Test
=====================

Test basic instruction following with simple, direct queries.
"""

import boto3
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_simple_compliance():
    """Test with very direct, simple queries"""
    
    profile_name = "revops-dev-profile"
    session = boto3.Session(profile_name=profile_name, region_name="us-east-1")
    bedrock_runtime = session.client('bedrock-agent-runtime')
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    agent_id = config.get('data_agent', {}).get('agent_id')
    agent_alias_id = config.get('data_agent', {}).get('agent_alias_id')
    
    # Simple test queries with explicit instruction reference
    test_queries = [
        {
            "name": "Direct Instruction Test",
            "query": "Please follow your instructions exactly. Query the knowledge base for customer classification rules, then show Q2 2025 revenue by customer type in JSON format with temporal analysis.",
            "expected": ["json", "knowledge", "commit", "plg", "prospect", "customer_type"]
        },
        {
            "name": "Explicit JSON Request", 
            "query": "Provide your response in JSON format only. Start with: {\"knowledge_base_consultation\": \"...\", \"customer_segmentation\": {...}}",
            "expected": ["json", "{", "knowledge_base_consultation", "customer_segmentation"]
        },
        {
            "name": "Knowledge Base Direct",
            "query": "First, query your knowledge base for customer classification rules. Then explain what you found.",
            "expected": ["knowledge", "customer_classification", "commit customer", "plg customer", "$200"]
        }
    ]
    
    logger.info("🧪 Testing Simple Compliance with Direct Instructions")
    logger.info("=" * 60)
    
    results = []
    
    for i, test in enumerate(test_queries, 1):
        logger.info(f"🧪 Test {i}/3: {test['name']}")
        logger.info(f"📝 Query: {test['query']}")
        
        try:
            session_id = f"simple-test-{int(time.time())}-{i}"
            
            response = bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=test['query']
            )
            
            # Collect response
            full_response = ""
            for event in response['completion']:
                if 'chunk' in event and 'bytes' in event['chunk']:
                    full_response += event['chunk']['bytes'].decode('utf-8')
            
            # Check compliance
            found_patterns = []
            for pattern in test['expected']:
                if pattern.lower() in full_response.lower():
                    found_patterns.append(pattern)
            
            compliance_score = len(found_patterns) / len(test['expected'])
            
            result = {
                "test_name": test['name'],
                "compliance_score": compliance_score,
                "found_patterns": found_patterns,
                "missing_patterns": [p for p in test['expected'] if p not in found_patterns],
                "response_preview": full_response[:500] + "..." if len(full_response) > 500 else full_response
            }
            
            results.append(result)
            
            status = "✅ EXCELLENT" if compliance_score >= 0.8 else "✅ GOOD" if compliance_score >= 0.6 else "⚠️ NEEDS WORK" if compliance_score >= 0.4 else "❌ POOR"
            logger.info(f"📊 {status} - Compliance: {compliance_score:.2f} ({len(found_patterns)}/{len(test['expected'])})")
            logger.info(f"📋 Found: {', '.join(found_patterns)}")
            logger.info(f"❌ Missing: {', '.join([p for p in test['expected'] if p not in found_patterns])}")
            logger.info("-" * 40)
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            results.append({"test_name": test['name'], "error": str(e), "compliance_score": 0.0})
    
    # Overall assessment
    avg_score = sum(r.get('compliance_score', 0) for r in results) / len(results)
    
    logger.info("=" * 60)
    logger.info(f"🎯 OVERALL SIMPLE COMPLIANCE SCORE: {avg_score:.2f}/1.00")
    
    if avg_score >= 0.6:
        logger.info("✅ Agent is following instructions reasonably well")
        logger.info("💡 Recommendation: Fine-tune specific patterns")
    else:
        logger.warning("⚠️ Agent is not following instructions consistently")
        logger.info("💡 Recommendation: May need foundational instruction approach")
    
    # Save simple report
    with open('simple_compliance_report.md', 'w') as f:
        f.write(f"""# Simple Compliance Test Report

## Overall Score: {avg_score:.2f}/1.00

## Test Results:

""")
        for result in results:
            f.write(f"""
### {result.get('test_name', 'Unknown')}
- **Compliance Score**: {result.get('compliance_score', 0):.2f}
- **Found Patterns**: {', '.join(result.get('found_patterns', []))}
- **Missing Patterns**: {', '.join(result.get('missing_patterns', []))}
- **Response Preview**: {result.get('response_preview', 'No response')[:300]}

""")
    
    logger.info("📄 Simple compliance report saved: simple_compliance_report.md")
    
    return avg_score

def main():
    score = test_simple_compliance()
    return score >= 0.6

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)