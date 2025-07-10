#!/usr/bin/env python3
"""
Simplified RevOps Agent Debug Tool for Claude Code
Provides debugging analysis for the RevOps AI Framework
"""

import boto3
import json
from datetime import datetime, timedelta
from pathlib import Path

class RevOpsDebugger:
    def __init__(self):
        self.aws_profile = "FireboltSystemAdministrator-740202120544"
        self.aws_region = "us-east-1"
        
        # Agent configuration
        self.agents = {
            "decision_agent": {"id": "TCX9CGOKBR", "type": "bedrock"},
            "data_agent": {"id": "9B8EGU46UV", "type": "bedrock"}, 
            "websearch_agent": {"id": "83AGBVJLEB", "type": "bedrock"},
            "execution_agent": {"id": "UWMCP4AYZX", "type": "bedrock"}
        }
        
        # Initialize AWS session
        try:
            self.session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
            self.bedrock_client = self.session.client('bedrock-agent')
            self.logs_client = self.session.client('logs')
            print("✅ AWS connection established")
        except Exception as e:
            print(f"❌ AWS setup failed: {e}")
            print("💡 Run: aws sso login --profile FireboltSystemAdministrator-740202120544")
            return

    def check_agent_status(self):
        """Check current status of all agents"""
        print("\n🤖 Agent Status Check")
        print("-" * 50)
        
        for agent_name, config in self.agents.items():
            try:
                response = self.bedrock_client.get_agent(agentId=config["id"])
                agent = response["agent"]
                status = agent["agentStatus"]
                updated = agent.get("updatedAt", "Unknown")
                model = agent.get("foundationModel", "Unknown")
                print(f"✅ {agent_name}:")
                print(f"   Status: {status}")
                print(f"   Model: {model}")
                print(f"   Updated: {updated}")
                print()
            except Exception as e:
                print(f"❌ {agent_name}: Error - {e}")

    def check_recent_logs(self, hours_back=2):
        """Check recent logs for errors"""
        print(f"\n📊 Recent Logs Analysis (Last {hours_back} hours)")
        print("-" * 50)
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        log_groups = [
            "/aws/lambda/revops-slack-bedrock-processor",
            "/aws/lambda/revops-firebolt-query", 
            "/aws/lambda/revops-web-search",
            "/aws/lambda/revops-webhook"
        ]
        
        for log_group in log_groups:
            try:
                response = self.logs_client.filter_log_events(
                    logGroupName=log_group,
                    startTime=start_ms,
                    endTime=end_ms,
                    filterPattern="ERROR"
                )
                
                events = response.get('events', [])
                if events:
                    print(f"🚨 {log_group}: {len(events)} errors found")
                    for event in events[-3:]:  # Show last 3 errors
                        timestamp = datetime.fromtimestamp(event['timestamp']/1000)
                        print(f"   {timestamp}: {event['message'][:100]}...")
                else:
                    print(f"✅ {log_group}: No errors")
            except Exception as e:
                print(f"⚠️  {log_group}: Could not access - {e}")

    def check_knowledge_base_status(self):
        """Check knowledge base status"""
        print("\n📚 Knowledge Base Status")
        print("-" * 50)
        
        try:
            kb_response = self.bedrock_client.list_knowledge_bases()
            knowledge_bases = kb_response.get('knowledgeBaseSummaries', [])
            
            for kb in knowledge_bases:
                if 'revops' in kb['name'].lower() or 'firebolt' in kb['name'].lower():
                    print(f"✅ Knowledge Base: {kb['name']}")
                    print(f"   ID: {kb['knowledgeBaseId']}")
                    print(f"   Status: {kb['status']}")
                    print(f"   Updated: {kb.get('updatedAt', 'Unknown')}")
                    
        except Exception as e:
            print(f"❌ Could not check knowledge base: {e}")

    def generate_debug_commands(self):
        """Generate useful debug commands"""
        print("\n🔧 Debug Commands")
        print("-" * 50)
        
        print("# Check recent Slack interactions:")
        print("aws logs filter-log-events \\")
        print("  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \\")
        print("  --start-time $(date -d '2 hours ago' +%s)000 \\")
        print(f"  --profile {self.aws_profile}")
        print()
        
        print("# Test agent status:")
        for agent_name, config in self.agents.items():
            print(f"aws bedrock-agent get-agent --agent-id {config['id']} --profile {self.aws_profile}")
        print()
        
        print("# Sync knowledge base:")
        print("cd V3/deployment && python3 sync_knowledge_base.py")
        print()
        
        print("# Test specific query:")
        print("# Use Slack to test: @RevBot [your test query]")

    def run_quick_debug(self):
        """Run a quick debug session"""
        print("🔧" + "="*70)
        print("🚀 RevOps Agent Quick Debug Tool")
        print("="*72)
        
        self.check_agent_status()
        self.check_recent_logs()
        self.check_knowledge_base_status()
        self.generate_debug_commands()
        
        print("\n" + "="*72)
        print("🎉 Quick debug analysis complete!")
        print("📝 For specific issue analysis, provide:")
        print("   - Slack conversation text")
        print("   - Timestamp of the issue")
        print("   - Expected vs actual behavior")
        print("="*72)

if __name__ == "__main__":
    debugger = RevOpsDebugger()
    debugger.run_quick_debug()