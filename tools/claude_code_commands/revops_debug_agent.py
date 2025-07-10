#!/usr/bin/env python3
"""
Claude Code Slash Command: /revops debug_agent

Systematically debug and fix unexpected agent behavior in the RevOps AI Framework
by analyzing conversation logs, AWS traces, and agent configurations.
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Add the parent directory to the path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

class RevOpsDebugAgent:
    def __init__(self):
        self.aws_profile = "FireboltSystemAdministrator-740202120544"
        self.aws_region = "us-east-1"
        self.project_root = Path(__file__).parent.parent.parent
        
        # Agent configuration
        self.agents = {
            "decision_agent": {
                "id": "TCX9CGOKBR",
                "type": "bedrock",
                "log_group": "/aws/bedrock/agent/TCX9CGOKBR",
                "instructions_path": "agents/decision_agent/instructions.md"
            },
            "data_agent": {
                "id": "9B8EGU46UV", 
                "type": "bedrock",
                "log_group": "/aws/lambda/revops-firebolt-query",
                "instructions_path": "agents/data_agent/instructions.md"
            },
            "websearch_agent": {
                "id": "83AGBVJLEB",
                "type": "bedrock",
                "log_group": "/aws/lambda/revops-web-search",
                "instructions_path": "agents/web_search_agent/instructions.md"
            },
            "execution_agent": {
                "id": "UWMCP4AYZX",
                "type": "bedrock", 
                "log_group": "/aws/lambda/revops-webhook",
                "instructions_path": "agents/execution_agent/instructions.md"
            }
        }
        
        # Initialize AWS session
        try:
            self.session = boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
            self.logs_client = self.session.client('logs')
            self.bedrock_client = self.session.client('bedrock-agent')
        except Exception as e:
            print(f"❌ AWS setup failed: {e}")
            print("💡 Run: aws sso login --profile FireboltSystemAdministrator-740202120544")
            sys.exit(1)

    def print_banner(self):
        """Print the debug banner"""
        print("🔧" + "="*70)
        print("🚀 RevOps Agent Debug Tool - Enhanced Analysis")
        print("="*72)

    def gather_conversation_context(self):
        """Step 1: Gather conversation context from user"""
        print("\n📋 STEP 1: Conversation Analysis")
        print("-" * 50)
        
        conversation = input("📝 Paste the Slack conversation (or path to file): ").strip()
        
        if conversation.startswith('/') or conversation.endswith('.txt'):
            # Read from file
            try:
                with open(conversation, 'r') as f:
                    conversation = f.read()
            except FileNotFoundError:
                print(f"❌ File not found: {conversation}")
                return None
        
        # Extract key information
        context = {
            "conversation": conversation,
            "timestamp_israel": input("⏰ Timestamp (Israel time, e.g., '2025-07-07 15:24'): ").strip(),
            "expected_behavior": input("🎯 Expected behavior: ").strip(),
            "user_query": self.extract_user_query(conversation),
            "agent_response": self.extract_agent_response(conversation)
        }
        
        # Convert Israel time to UTC (Israel is UTC+2 in winter, UTC+3 in summer)
        try:
            israel_dt = datetime.strptime(context["timestamp_israel"], "%Y-%m-%d %H:%M")
            # Assuming UTC+2 for simplicity (adjust for daylight saving if needed)
            utc_dt = israel_dt - timedelta(hours=2)
            context["timestamp_utc"] = utc_dt
            context["start_time"] = int((utc_dt - timedelta(minutes=5)).timestamp() * 1000)
            context["end_time"] = int((utc_dt + timedelta(minutes=5)).timestamp() * 1000)
        except ValueError:
            print("❌ Invalid timestamp format. Use: YYYY-MM-DD HH:MM")
            return None
        
        print(f"✅ User Query: {context['user_query'][:100]}...")
        print(f"✅ UTC Time Window: {context['timestamp_utc']} ± 5 minutes")
        
        return context

    def extract_user_query(self, conversation):
        """Extract user query from conversation"""
        lines = conversation.split('\n')
        for line in lines:
            if '@RevBot' in line or line.strip().startswith('how') or line.strip().startswith('what'):
                return line.strip().replace('@RevBot', '').strip()
        return "Query not found"

    def extract_agent_response(self, conversation):
        """Extract agent response from conversation"""
        lines = conversation.split('\n')
        response_lines = []
        in_response = False
        
        for line in lines:
            if 'RevBot' in line and 'APP' in line:
                in_response = True
                continue
            if in_response and line.strip():
                response_lines.append(line.strip())
            elif in_response and not line.strip():
                break
                
        return ' '.join(response_lines) if response_lines else "Response not found"

    def gather_additional_context(self, context):
        """Step 2: Gather additional context"""
        print("\n🔍 STEP 2: Additional Context Gathering")
        print("-" * 50)
        
        additional = {
            "data_sources_expected": input("📊 Expected data sources (Firebolt/Salesforce/Gong/Web): ").strip(),
            "similar_working_queries": input("✅ Similar working queries (examples): ").strip(),
            "specific_issue": input("🐛 Specific issue observed: ").strip()
        }
        
        # Identify involved agents based on query type
        involved_agents = self.identify_involved_agents(context["user_query"])
        additional["involved_agents"] = involved_agents
        
        print(f"🤖 Identified involved agents: {', '.join(involved_agents)}")
        
        return additional

    def identify_involved_agents(self, query):
        """Identify which agents should be involved based on query"""
        query_lower = query.lower()
        agents = ["decision_agent"]  # Always involved as supervisor
        
        # Data-related queries
        if any(keyword in query_lower for keyword in ["revenue", "leads", "opportunities", "customers", "sql", "data", "analysis", "metrics"]):
            agents.append("data_agent")
        
        # Web search queries  
        if any(keyword in query_lower for keyword in ["research", "company", "web", "search", "intelligence", "competitor"]):
            agents.append("websearch_agent")
        
        # Execution queries
        if any(keyword in query_lower for keyword in ["notify", "send", "update", "webhook", "action", "execute"]):
            agents.append("execution_agent")
        
        return agents

    def analyze_aws_logs(self, context, additional_context):
        """Step 3: Comprehensive AWS CloudWatch Log Analysis"""
        print("\n📊 STEP 3: AWS CloudWatch Log Analysis")
        print("-" * 50)
        
        logs_analysis = {}
        
        # Analyze Slack processor logs first
        print("🔍 Analyzing Slack processor logs...")
        slack_logs = self.get_log_events(
            "/aws/lambda/revops-slack-bedrock-processor",
            context["start_time"],
            context["end_time"],
            filter_pattern=f'"{context["user_query"][:20]}"'
        )
        logs_analysis["slack_processor"] = self.analyze_slack_logs(slack_logs)
        
        # Analyze each involved agent
        for agent_name in additional_context["involved_agents"]:
            if agent_name in self.agents:
                print(f"🔍 Analyzing {agent_name} logs...")
                agent_config = self.agents[agent_name]
                
                logs = self.get_log_events(
                    agent_config["log_group"],
                    context["start_time"], 
                    context["end_time"]
                )
                
                logs_analysis[agent_name] = self.analyze_agent_logs(agent_name, logs)
        
        return logs_analysis

    def get_log_events(self, log_group, start_time, end_time, filter_pattern=None):
        """Get log events from CloudWatch"""
        try:
            params = {
                'logGroupName': log_group,
                'startTime': start_time,
                'endTime': end_time
            }
            
            if filter_pattern:
                params['filterPattern'] = filter_pattern
            
            response = self.logs_client.filter_log_events(**params)
            return response.get('events', [])
            
        except ClientError as e:
            print(f"⚠️  Could not access log group {log_group}: {e}")
            return []

    def analyze_slack_logs(self, logs):
        """Analyze Slack processor logs"""
        analysis = {
            "total_events": len(logs),
            "errors": [],
            "function_calls": [],
            "agent_invocations": []
        }
        
        for event in logs:
            message = event.get('message', '')
            
            # Look for errors
            if 'ERROR' in message or 'error' in message:
                analysis["errors"].append(message)
            
            # Look for function calls
            if 'function' in message.lower() or 'invoke' in message.lower():
                analysis["function_calls"].append(message)
                
            # Look for agent invocations
            if 'agent' in message.lower() and 'invoke' in message.lower():
                analysis["agent_invocations"].append(message)
        
        return analysis

    def analyze_agent_logs(self, agent_name, logs):
        """Analyze individual agent logs"""
        analysis = {
            "agent": agent_name,
            "total_events": len(logs),
            "errors": [],
            "sql_queries": [],
            "function_calls": [],
            "response_times": []
        }
        
        for event in logs:
            message = event.get('message', '')
            
            # Look for errors
            if any(keyword in message for keyword in ['ERROR', 'error', 'failed', 'exception']):
                analysis["errors"].append(message)
            
            # Look for SQL queries (for data agent)
            if 'SELECT' in message or 'FROM' in message:
                analysis["sql_queries"].append(message)
            
            # Look for function calls
            if 'function' in message.lower():
                analysis["function_calls"].append(message)
        
        return analysis

    def perform_root_cause_analysis(self, context, additional_context, logs_analysis):
        """Step 4: Root Cause Analysis Framework"""
        print("\n🔍 STEP 4: Root Cause Analysis")
        print("-" * 50)
        
        root_causes = {}
        
        # Check agent collaboration
        decision_logs = logs_analysis.get("decision_agent", {})
        if not decision_logs.get("function_calls") and len(additional_context["involved_agents"]) > 1:
            root_causes["collaboration"] = {
                "issue": "Decision agent may not be properly invoking collaborators",
                "evidence": "No function calls found in decision agent logs",
                "fix": "Review decision_agent/instructions.md collaboration rules"
            }
        
        # Check data retrieval
        data_logs = logs_analysis.get("data_agent", {})
        if "data_agent" in additional_context["involved_agents"]:
            if not data_logs.get("sql_queries"):
                root_causes["data_retrieval"] = {
                    "issue": "Data agent not executing SQL queries",
                    "evidence": "No SQL queries found in data agent logs",
                    "fix": "Check schema documentation and SQL patterns"
                }
            elif data_logs.get("errors"):
                root_causes["sql_errors"] = {
                    "issue": "SQL execution errors",
                    "evidence": f"Found {len(data_logs['errors'])} errors",
                    "fix": "Review SQL syntax and schema availability"
                }
        
        # Check for general errors
        total_errors = sum(len(analysis.get("errors", [])) for analysis in logs_analysis.values())
        if total_errors > 0:
            root_causes["general_errors"] = {
                "issue": f"Found {total_errors} total errors across all agents",
                "evidence": "Multiple error messages in logs",
                "fix": "Review individual agent configurations and permissions"
            }
        
        # Print root cause analysis
        if root_causes:
            print("🚨 Root Causes Identified:")
            for cause, details in root_causes.items():
                print(f"  • {details['issue']}")
                print(f"    Evidence: {details['evidence']}")
                print(f"    Fix: {details['fix']}")
        else:
            print("✅ No obvious root causes found in logs")
        
        return root_causes

    def review_knowledge_base(self, additional_context):
        """Step 5: Review relevant knowledge base files"""
        print("\n📚 STEP 5: Knowledge Base Review")
        print("-" * 50)
        
        kb_files_to_check = []
        
        for agent_name in additional_context["involved_agents"]:
            if agent_name in self.agents:
                # Add agent instructions
                kb_files_to_check.append(self.agents[agent_name]["instructions_path"])
                
                # Add agent-specific knowledge base files
                if agent_name == "data_agent":
                    kb_files_to_check.extend([
                        "knowledge_base/firebolt_schema/firebolt_schema.md",
                        "knowledge_base/sql_patterns/temporal_analysis.md",
                        "knowledge_base/sql_patterns/regional_analysis.md",
                        "knowledge_base/sql_patterns/lead_analysis.md",
                        "knowledge_base/sql_patterns/gong_call_analysis.md"
                    ])
                elif agent_name == "websearch_agent":
                    kb_files_to_check.extend([
                        "knowledge_base/icp_and_reachout/firebolt_icp.md"
                    ])
                elif agent_name == "execution_agent":
                    kb_files_to_check.extend([
                        "knowledge_base/icp_and_reachout/firebolt_messeging.md"
                    ])
        
        print("📋 Knowledge base files to review:")
        for file_path in kb_files_to_check:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"  ✅ {file_path}")
            else:
                print(f"  ❌ {file_path} (missing)")
        
        return kb_files_to_check

    def suggest_fixes(self, root_causes, additional_context):
        """Step 6: Suggest specific fixes"""
        print("\n🔧 STEP 6: Suggested Fixes")
        print("-" * 50)
        
        fixes = []
        
        if "collaboration" in root_causes:
            fixes.append({
                "type": "instructions",
                "file": "agents/decision_agent/instructions.md",
                "action": "Update collaboration patterns and agent invocation logic"
            })
        
        if "data_retrieval" in root_causes or "sql_errors" in root_causes:
            fixes.append({
                "type": "knowledge_base",
                "file": "knowledge_base/sql_patterns/",
                "action": "Add or update SQL patterns for the specific query type"
            })
            fixes.append({
                "type": "instructions", 
                "file": "agents/data_agent/instructions.md",
                "action": "Ensure proper reference to knowledge base files"
            })
        
        if "websearch_agent" in additional_context["involved_agents"]:
            fixes.append({
                "type": "instructions",
                "file": "agents/web_search_agent/instructions.md", 
                "action": "Review search patterns and API integration"
            })
        
        # Always suggest testing
        fixes.append({
            "type": "testing",
            "file": "test_scenario.py",
            "action": "Create comprehensive test cases for the specific scenario"
        })
        
        print("🎯 Recommended fixes:")
        for i, fix in enumerate(fixes, 1):
            print(f"  {i}. {fix['action']}")
            print(f"     File: {fix['file']}")
            print(f"     Type: {fix['type']}")
        
        return fixes

    def check_agent_status(self):
        """Check current status of all agents"""
        print("\n🤖 STEP 7: Agent Status Check")
        print("-" * 50)
        
        for agent_name, config in self.agents.items():
            try:
                if config["type"] == "bedrock":
                    response = self.bedrock_client.get_agent(agentId=config["id"])
                    agent = response["agent"]
                    status = agent["agentStatus"]
                    updated = agent.get("updatedAt", "Unknown")
                    print(f"✅ {agent_name}: {status} (Updated: {updated})")
                else:
                    print(f"⏩ {agent_name}: Lambda function (status check not implemented)")
            except Exception as e:
                print(f"❌ {agent_name}: Error checking status - {e}")

    def generate_deployment_commands(self, fixes):
        """Generate deployment commands"""
        print("\n🚀 STEP 8: Deployment Commands")
        print("-" * 50)
        
        print("Run these commands to deploy fixes:")
        print()
        
        # Knowledge base sync
        print("# 1. Sync knowledge base (if KB files were updated)")
        print("cd V3/deployment")
        print("python3 sync_knowledge_base.py")
        print()
        
        # Agent updates
        print("# 2. Update agent instructions")
        for agent_name in self.agents.keys():
            agent_id = self.agents[agent_name]["id"]
            print(f"# Update {agent_name}")
            print(f"aws bedrock-agent update-agent --agent-id {agent_id} \\")
            print(f"  --instruction \"$(cat {self.agents[agent_name]['instructions_path']})\" \\")
            print(f"  --profile {self.aws_profile}")
            print(f"aws bedrock-agent prepare-agent --agent-id {agent_id} --profile {self.aws_profile}")
            print()
        
        # Test command
        print("# 3. Test the fix")
        print("# Create a test with the original failing query and verify the response")

    def run_debug_session(self):
        """Main debug session workflow"""
        self.print_banner()
        
        # Step 1: Gather conversation context
        context = self.gather_conversation_context()
        if not context:
            return
        
        # Step 2: Gather additional context
        additional_context = self.gather_additional_context(context)
        
        # Step 3: Analyze AWS logs
        logs_analysis = self.analyze_aws_logs(context, additional_context)
        
        # Step 4: Root cause analysis
        root_causes = self.perform_root_cause_analysis(context, additional_context, logs_analysis)
        
        # Step 5: Review knowledge base
        kb_files = self.review_knowledge_base(additional_context)
        
        # Step 6: Suggest fixes
        fixes = self.suggest_fixes(root_causes, additional_context)
        
        # Step 7: Check agent status
        self.check_agent_status()
        
        # Step 8: Generate deployment commands
        self.generate_deployment_commands(fixes)
        
        print("\n" + "="*72)
        print("🎉 Debug analysis complete!")
        print("📝 Review the suggested fixes and run the deployment commands.")
        print("🧪 Don't forget to test the original failing scenario after deployment.")
        print("="*72)

def main():
    """Main entry point for the slash command"""
    parser = argparse.ArgumentParser(description="RevOps Agent Debug Tool")
    parser.add_argument("--conversation", help="Path to conversation file or text")
    parser.add_argument("--timestamp", help="Timestamp in Israel time (YYYY-MM-DD HH:MM)")
    parser.add_argument("--agent", help="Specific agent to focus on", choices=["decision", "data", "websearch", "execution"])
    
    args = parser.parse_args()
    
    debugger = RevOpsDebugAgent()
    debugger.run_debug_session()

if __name__ == "__main__":
    main()