"""
Complete Slack-Bedrock Processor with Full Tracing
Combines working Slack integration with comprehensive agent tracing functionality.
"""

import json
import boto3
import time
import logging
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from contextlib import contextmanager
import sys
import os
import re

# Enhanced schema import with multiple fallback strategies
def import_conversation_schema():
    """Reliable schema import with comprehensive fallback paths"""
    current_dir = os.path.dirname(__file__)
    
    # Multiple import paths in priority order
    import_paths = [
        current_dir,                    # Lambda function directory (first priority)
        '/opt/python',                  # Lambda layers (second priority)
        '/var/task',                    # Lambda runtime directory
        os.path.join(current_dir, '..', '..', '..', 'monitoring'),  # Relative to monitoring
        '/opt/python/lib/python3.9/site-packages',  # Site packages
    ]
    
    print(f"Attempting schema import from {len(import_paths)} possible locations...")
    
    for i, path in enumerate(import_paths):
        try:
            # Temporarily add path to sys.path
            if path not in sys.path:
                sys.path.insert(0, path)
            
            # Attempt import
            from conversation_schema import (
                ConversationUnit, 
                AgentFlowStep, 
                ToolExecution, 
                BedrockTraceContent, 
                DataOperation, 
                FunctionCall
            )
            
            print(f"✅ Schema imported successfully from: {path}")
            
            # Verify imports work by testing a simple instantiation
            test_unit = ConversationUnit(
                conversation_id="test",
                session_id="test", 
                user_id="test",
                channel="test",
                start_timestamp="test",
                end_timestamp="test",
                user_query="test",
                temporal_context="test",
                agents_involved=[],
                agent_flow=[],
                final_response="test",
                collaboration_map={},
                function_audit={},
                success=True,
                processing_time_ms=0
            )
            print("✅ Schema verification successful")
            return True
            
        except ImportError as e:
            print(f"❌ Import attempt {i+1} failed from {path}: {e}")
            if path in sys.path:
                sys.path.remove(path)
            continue
        except Exception as e:
            print(f"❌ Schema verification failed from {path}: {e}")
            if path in sys.path:
                sys.path.remove(path)
            continue
    
    # If all attempts fail, provide detailed diagnostics
    print("🚨 All schema import attempts failed. Diagnostics:")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Current file directory: {current_dir}")
    print(f"Python path: {sys.path[:5]}...")  # Show first 5 for brevity
    
    print("Available Python files in current directory:")
    try:
        for file in os.listdir(current_dir):
            if file.endswith('.py'):
                print(f"  - {file}")
    except Exception as list_error:
        print(f"  Error listing files: {list_error}")
        
    # Check if monitoring directory exists relative to current location
    monitoring_paths = [
        os.path.join(current_dir, '..', '..', '..', 'monitoring'),
        os.path.join(current_dir, 'monitoring'),
        '/opt/python/monitoring'
    ]
    
    for mon_path in monitoring_paths:
        abs_path = os.path.abspath(mon_path)
        if os.path.exists(abs_path):
            print(f"Found monitoring directory at: {abs_path}")
            try:
                files = os.listdir(abs_path)[:5]  # First 5 files
                print(f"  Contains: {files}")
            except:
                print("  Could not list contents")
        else:
            print(f"Monitoring directory not found at: {abs_path}")
    
    print("⚠️  Falling back to dictionary-based tracking")
    return False

# Attempt schema import with enhanced reliability
schema_import_success = import_conversation_schema()

# CloudWatch client for monitoring metrics
cloudwatch = boto3.client('cloudwatch')

# Track schema import status on module load (inline to reduce function call overhead)
try:
    metric_value = 1.0 if schema_import_success else 0.0
    cloudwatch.put_metric_data(
        Namespace='RevOps-AI/Monitoring',
        MetricData=[
            {
                'MetricName': 'ConversationSchemaImportSuccess',
                'Value': metric_value,
                'Unit': 'Count',
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': 'Production'
                    }
                ]
            }
        ]
    )
    print(f"📊 Schema import status metric sent: {metric_value}")
except Exception as e:
    print(f"⚠️ Failed to send schema import metric: {e}")

# Try to import requests, install if missing
try:
    import requests
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--target", "/tmp"])
    sys.path.insert(0, "/tmp")
    import requests

# Enhanced AgentTracer for comprehensive monitoring
class EventType(Enum):
    """Types of events to trace"""
    CONVERSATION_START = "CONVERSATION_START"
    CONVERSATION_END = "CONVERSATION_END"
    AGENT_INVOKE = "AGENT_INVOKE"
    AGENT_RESPONSE = "AGENT_RESPONSE"
    AGENT_REASONING = "AGENT_REASONING"
    AGENT_TOOL_USE = "AGENT_TOOL_USE"
    DATA_OPERATION = "DATA_OPERATION"
    DECISION_LOGIC = "DECISION_LOGIC"
    ERROR = "ERROR"
    TEMPORAL_CONTEXT = "TEMPORAL_CONTEXT"
    WORKFLOW_SELECTION = "WORKFLOW_SELECTION"
    SLACK_INCOMING = "SLACK_INCOMING"
    SLACK_OUTGOING = "SLACK_OUTGOING"
    BEDROCK_REQUEST = "BEDROCK_REQUEST"
    BEDROCK_RESPONSE = "BEDROCK_RESPONSE"
    ROUTING_DECISION = "ROUTING_DECISION"
    TOOL_EXECUTION = "TOOL_EXECUTION"

class AgentTracer:
    """Enhanced tracing for agent interactions and decisions"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.session_start = datetime.now(timezone.utc)
        self._setup_loggers()
        
    def _setup_loggers(self):
        """Setup structured loggers for different trace categories"""
        self.conversation_logger = logging.getLogger('revops-ai.conversation-trace')
        self.collaboration_logger = logging.getLogger('revops-ai.agent-collaboration')
        self.data_logger = logging.getLogger('revops-ai.data-operations')
        self.decision_logger = logging.getLogger('revops-ai.decision-logic') 
        self.error_logger = logging.getLogger('revops-ai.error-analysis')
        
        for logger in [self.conversation_logger, self.collaboration_logger, 
                      self.data_logger, self.decision_logger, self.error_logger]:
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
    
    def trace_conversation_start(self, user_query: str, user_id: str, channel: str, 
                                temporal_context: Optional[str] = None):
        """Trace the start of a conversation"""
        event_data = {
            "event_type": EventType.CONVERSATION_START.value,
            "correlation_id": self.correlation_id,
            "user_query": user_query,
            "user_id": user_id,
            "channel": channel,
            "temporal_context": temporal_context,
            "session_start": self.session_start.isoformat(),
            "query_length": len(user_query),
            "query_type": self._classify_query_type(user_query)
        }
        self.conversation_logger.info(json.dumps(event_data))
        
    def trace_conversation_end(self, response_summary: str, total_agents_used: int,
                              processing_time_ms: int, success: bool):
        """Trace the end of a conversation"""
        event_data = {
            "event_type": EventType.CONVERSATION_END.value,
            "correlation_id": self.correlation_id,
            "response_summary": response_summary[:200] + "..." if len(response_summary) > 200 else response_summary,
            "total_agents_used": total_agents_used,
            "processing_time_ms": processing_time_ms,
            "success": success,
            "session_duration_ms": int((datetime.now(timezone.utc) - self.session_start).total_seconds() * 1000)
        }
        self.conversation_logger.info(json.dumps(event_data))
    
    def trace_agent_invocation(self, source_agent: str, target_agent: str, 
                              collaboration_type: str, reasoning: str):
        """Trace agent-to-agent collaboration"""
        event_data = {
            "event_type": EventType.AGENT_INVOKE.value,
            "correlation_id": self.correlation_id,
            "source_agent": source_agent,
            "target_agent": target_agent,
            "collaboration_type": collaboration_type,
            "reasoning": reasoning,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.collaboration_logger.info(json.dumps(event_data))
        
    def trace_data_operation(self, operation_type: str, data_source: str, 
                           query_summary: str, result_count: Optional[int] = None,
                           execution_time_ms: Optional[int] = None, 
                           error_message: Optional[str] = None):
        """Trace data retrieval operations"""
        event_data = {
            "event_type": EventType.DATA_OPERATION.value,
            "correlation_id": self.correlation_id,
            "operation_type": operation_type,
            "data_source": data_source,
            "query_summary": query_summary,
            "result_count": result_count,
            "execution_time_ms": execution_time_ms,
            "success": error_message is None,
            "error_message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.data_logger.info(json.dumps(event_data))
    
    def trace_slack_incoming(self, message_content: str, user_id: str, channel: str, 
                           message_ts: str, event_type: str = "app_mention"):
        """Trace incoming Slack messages with full context"""
        event_data = {
            "event_type": EventType.SLACK_INCOMING.value,
            "correlation_id": self.correlation_id,
            "message_content": message_content,
            "user_id": user_id,
            "channel": channel,
            "message_ts": message_ts,
            "slack_event_type": event_type,
            "message_length": len(message_content),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "contains_deal_keywords": self._contains_deal_keywords(message_content),
            "extracted_entities": self._extract_entities(message_content)
        }
        self.conversation_logger.info(json.dumps(event_data))
    
    def trace_slack_outgoing(self, response_content: str, channel: str, 
                           response_type: str, processing_time_ms: int):
        """Trace outgoing Slack responses"""
        event_data = {
            "event_type": EventType.SLACK_OUTGOING.value,
            "correlation_id": self.correlation_id,
            "response_content": response_content[:500] + "..." if len(response_content) > 500 else response_content,
            "response_length": len(response_content),
            "channel": channel,
            "response_type": response_type,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.conversation_logger.info(json.dumps(event_data))
    
    def trace_bedrock_request(self, agent_id: str, agent_alias_id: str, 
                            session_id: str, input_text: str, request_metadata: dict = None):
        """Trace Bedrock agent invocation requests"""
        event_data = {
            "event_type": EventType.BEDROCK_REQUEST.value,
            "correlation_id": self.correlation_id,
            "agent_id": agent_id,
            "agent_alias_id": agent_alias_id,
            "session_id": session_id,
            "input_text": input_text,
            "input_length": len(input_text),
            "request_metadata": request_metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.collaboration_logger.info(json.dumps(event_data))
    
    def trace_bedrock_response(self, agent_id: str, response_text: str, 
                             response_metadata: dict, processing_time_ms: int):
        """Trace Bedrock agent responses"""
        event_data = {
            "event_type": EventType.BEDROCK_RESPONSE.value,
            "correlation_id": self.correlation_id,
            "agent_id": agent_id,
            "response_text": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
            "response_length": len(response_text),
            "response_metadata": response_metadata,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.collaboration_logger.info(json.dumps(event_data))
    
    def trace_agent_reasoning(self, agent_id: str, reasoning_step: str, 
                            thought_process: str, decision_factors: dict = None):
        """Trace agent reasoning and thought process"""
        event_data = {
            "event_type": EventType.AGENT_REASONING.value,
            "correlation_id": self.correlation_id,
            "agent_id": agent_id,
            "reasoning_step": reasoning_step,
            "thought_process": thought_process,
            "decision_factors": decision_factors or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.decision_logger.info(json.dumps(event_data))
    
    def trace_routing_decision(self, router_agent: str, target_agent: str, 
                             routing_reason: str, query_classification: str):
        """Trace agent routing decisions"""
        event_data = {
            "event_type": EventType.ROUTING_DECISION.value,
            "correlation_id": self.correlation_id,
            "router_agent": router_agent,
            "target_agent": target_agent,
            "routing_reason": routing_reason,
            "query_classification": query_classification,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.decision_logger.info(json.dumps(event_data))
    
    def trace_tool_execution(self, agent_id: str, tool_name: str, 
                           tool_input: dict, tool_output: dict, execution_time_ms: int):
        """Trace tool execution by agents"""
        event_data = {
            "event_type": EventType.TOOL_EXECUTION.value,
            "correlation_id": self.correlation_id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "tool_input": str(tool_input)[:500] + "..." if len(str(tool_input)) > 500 else tool_input,
            "tool_output": str(tool_output)[:500] + "..." if len(str(tool_output)) > 500 else tool_output,
            "execution_time_ms": execution_time_ms,
            "success": "error" not in str(tool_output).lower(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.data_logger.info(json.dumps(event_data))
    
    def _contains_deal_keywords(self, text: str) -> bool:
        """Check if text contains deal analysis keywords"""
        deal_keywords = [
            "status of", "deal with", "deal for", "analyze the", "review the", 
            "about the", "opportunity", "deal", "assessment", "MEDDPICC", 
            "probability", "IXIS", "ACME", "Microsoft", "Salesforce"
        ]
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in deal_keywords)
    
    def _extract_entities(self, text: str) -> dict:
        """Extract entities from text for monitoring"""
        import re
        entities = {
            "company_names": [],
            "monetary_amounts": [],
            "time_references": [],
            "keywords": []
        }
        
        # Extract potential company names (capitalized words)
        company_pattern = r'\b[A-Z][a-zA-Z]+\b'
        entities["company_names"] = list(set(re.findall(company_pattern, text)))
        
        # Extract monetary amounts
        money_pattern = r'\$[\d,.]+'
        entities["monetary_amounts"] = re.findall(money_pattern, text)
        
        # Extract time references
        time_pattern = r'\b(Q[1-4]|quarter|month|year|week|day|today|yesterday|tomorrow)\b'
        entities["time_references"] = list(set(re.findall(time_pattern, text, re.IGNORECASE)))
        
        return entities
    
    def trace_error(self, error_type: str, error_message: str, 
                   agent_context: str, stack_trace: Optional[str] = None):
        """Trace errors for analysis"""
        event_data = {
            "event_type": EventType.ERROR.value,
            "correlation_id": self.correlation_id,
            "error_type": error_type,
            "error_message": error_message,
            "agent_context": agent_context,
            "stack_trace": stack_trace,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.error_logger.error(json.dumps(event_data))
    
    def _classify_query_type(self, query: str) -> str:
        """Classify query type for analysis"""
        query_lower = query.lower()
        if any(word in query_lower for word in ['deal', 'opportunity', 'status', 'probability']):
            return 'DEAL_ANALYSIS'
        elif any(word in query_lower for word in ['lead', 'assess', 'qualify']):
            return 'LEAD_ASSESSMENT'
        elif any(word in query_lower for word in ['consumption', 'usage', 'fbu', 'revenue']):
            return 'CONSUMPTION_ANALYSIS'
        elif any(word in query_lower for word in ['churn', 'risk', 'health']):
            return 'RISK_ASSESSMENT'
        elif any(word in query_lower for word in ['call', 'conversation', 'gong']):
            return 'CALL_ANALYSIS'
        else:
            return 'GENERAL_QUERY'

class AgentNarrationEngine:
    """Engine for converting technical agent reasoning into user-friendly narration"""
    
    def __init__(self):
        self.reasoning_patterns = {
            'analysis_start': r'(analyze|review|assess|examine|understand).*?(?:deal|status|request|question)',
            'data_retrieval': r'(need to|should|will|must|going to).*?(get|fetch|retrieve|query|access|pull).*?(data|information)',
            'agent_routing': r'(route|call|invoke|use|contact|collaborate).*?(agent|specialist|expert)',
            'risk_assessment': r'(risk|concern|issue|problem|competitive|challenge|threat)',
            'decision_making': r'(decide|determine|conclude|recommend|suggest|propose)',
            'completion': r'(complete|finished|ready|prepared|done|final)',
            'collaboration': r'(collaborat|work with|team up|coordinate)',
            'thinking': r'(think|consider|evaluate|analyze|ponder)',
            'found_data': r'(found|discovered|located|identified|retrieved).*?(deal|data|information)',
            'processing': r'(processing|working on|handling|managing)'
        }
        
        self.agent_mappings = {
            'DealAnalysisAgent': 'Deal Analysis Expert',
            'LeadAnalysisAgent': 'Lead Assessment Specialist', 
            'DataAgent': 'Data Specialist',
            'WebSearchAgent': 'Research Agent',
            'ExecutionAgent': 'Action Specialist'
        }
    
    def convert_reasoning_to_narration(self, rationale_text: str, context: dict) -> str:
        """Convert technical agent reasoning into user-friendly narration"""
        if not rationale_text or len(rationale_text.strip()) < 10:
            return None
            
        # Clean and prepare text
        clean_text = self._clean_reasoning_text(rationale_text)
        
        # Extract entities from reasoning and context
        entities = self._extract_entities(clean_text, context)
        
        # Classify reasoning type
        reasoning_type = self._classify_reasoning(clean_text)
        
        # Generate contextual narration
        return self._generate_narration(reasoning_type, entities, clean_text)
    
    def _clean_reasoning_text(self, text: str) -> str:
        """Clean technical reasoning text for processing"""
        # Remove excessive whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove technical artifacts
        cleaned = re.sub(r'\{[^}]*\}', '', cleaned)  # Remove JSON-like structures
        cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)  # Remove bracketed content
        
        return cleaned
    
    def _extract_entities(self, text: str, context: dict) -> dict:
        """Extract relevant entities for contextual narration"""
        entities = {
            'company': None,
            'deal_name': None,
            'person': None,
            'data_type': None,
            'agent_type': None,
            'action': None,
            'entity_type': 'request'
        }
        
        # Company/Deal extraction (common patterns)
        company_patterns = [
            r'\b([A-Z][a-zA-Z]+)\s+deal\b',
            r'\b([A-Z][a-zA-Z]+)\s+company\b',
            r'\b([A-Z][a-zA-Z]+)\s+opportunity\b',
            r'deal.*?([A-Z][a-zA-Z]+)',
            r'status.*?([A-Z][a-zA-Z]+)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                potential_company = match.group(1)
                # Filter out common false positives
                if potential_company.lower() not in ['deal', 'company', 'status', 'analysis']:
                    entities['company'] = potential_company
                    entities['entity_type'] = 'deal'
                    break
        
        # Data type extraction
        if re.search(r'(data|information|records|analytics)', text, re.IGNORECASE):
            entities['data_type'] = 'business data'
        
        # Agent collaboration detection
        for agent_key, agent_name in self.agent_mappings.items():
            if agent_key in text:
                entities['agent_type'] = agent_name
                break
        
        return entities
    
    def _classify_reasoning(self, text: str) -> str:
        """Classify the type of reasoning being performed"""
        text_lower = text.lower()
        
        # Check patterns in order of specificity
        for reasoning_type, pattern in self.reasoning_patterns.items():
            if re.search(pattern, text_lower):
                return reasoning_type
        
        return 'thinking'  # Default fallback
    
    def _generate_narration(self, reasoning_type: str, entities: dict, raw_text: str) -> str:
        """Generate user-friendly narration based on reasoning context"""
        
        company_context = f" about the {entities['company']} {entities['entity_type']}" if entities['company'] else f" about your {entities['entity_type']}"
        agent_context = f" - calling {entities['agent_type']}" if entities['agent_type'] else ""
        data_context = f" {entities['data_type']}" if entities['data_type'] else " information"
        
        narration_templates = {
            'analysis_start': f"🧠 Analyzing your request{company_context}...",
            'data_retrieval': f"📊 Getting latest{data_context} from our systems...",
            'agent_routing': f"🎯 This needs specialized analysis{agent_context}...",
            'collaboration': f"🤝 Coordinating with{agent_context} for comprehensive analysis...",
            'risk_assessment': f"⚠️ Evaluating potential risks and competitive factors...",
            'decision_making': f"💡 Analyzing options and preparing recommendations...",
            'found_data': f"📈 Found relevant data{company_context} - processing insights...",
            'processing': f"⚙️ Processing analysis{company_context}...",
            'completion': f"✅ Analysis complete - preparing comprehensive response...",
            'thinking': f"💭 {self._simplify_technical_reasoning(raw_text)[:100]}..."
        }
        
        return narration_templates.get(reasoning_type, f"💭 {self._simplify_technical_reasoning(raw_text)[:100]}...")
    
    def _simplify_technical_reasoning(self, text: str) -> str:
        """Simplify technical reasoning for user consumption"""
        # Replace technical terms with user-friendly equivalents
        simplifications = {
            r'invoke.*?agent': 'work with specialist',
            r'query.*?database': 'get data from systems',
            r'analyze.*?parameters': 'review the details',
            r'orchestrat.*?response': 'coordinate the analysis',
            r'process.*?request': 'handle your question'
        }
        
        simplified = text
        for pattern, replacement in simplifications.items():
            simplified = re.sub(pattern, replacement, simplified, flags=re.IGNORECASE)
        
        return simplified

class NarrationController:
    """Controller for managing intelligent narration updates"""
    
    def __init__(self):
        self.last_update_time = 0
        self.last_message_content = ""
        self.update_threshold = 2.5  # seconds between updates
        self.reasoning_history = []
        self.max_updates = 8  # Maximum updates per conversation
        self.update_count = 0
    
    def should_send_update(self, new_narration: str) -> bool:
        """Intelligent update decisions to prevent spam and ensure meaningful progress"""
        if not new_narration:
            return False
            
        current_time = time.time()
        
        # More generous rate limiting for granular updates
        granular_threshold = 0.6  # Reduced from 2.0 to 0.6 seconds
        if current_time - self.last_update_time < granular_threshold:
            return False
        
        # Higher maximum updates limit for granular narration
        max_granular_updates = 18  # Increased from 8
        if self.update_count >= max_granular_updates:
            return False
            
        # Content similarity check
        if self._is_similar_content(new_narration, self.last_message_content):
            return False
        
        # Meaningful progress check
        if self._is_meaningful_progress(new_narration):
            self.last_update_time = current_time
            self.last_message_content = new_narration
            self.update_count += 1
            return True
        
        return False
    
    def _is_similar_content(self, new_content: str, last_content: str) -> bool:
        """Check if content is too similar to warrant an update"""
        if not last_content:
            return False
        
        # Check for granular update patterns - be more permissive
        granular_patterns = ['🔍', '📊', '✅', '🛠️', '🤝', '📝', '🧠', '🎯', '📈', '⚠️', '🔧', '🌐', '📋']
        
        # If both are granular updates with different emojis, they're different enough
        new_emoji = next((p for p in granular_patterns if p in new_content), None)
        last_emoji = next((p for p in granular_patterns if p in last_content), None)
        
        if new_emoji and last_emoji and new_emoji != last_emoji:
            return False  # Different types of granular updates
        
        # Extract key words for comparison
        new_words = set(re.findall(r'\w+', new_content.lower()))
        last_words = set(re.findall(r'\w+', last_content.lower()))
        
        # Calculate similarity
        if len(new_words) == 0:
            return True
            
        intersection = new_words.intersection(last_words)
        similarity = len(intersection) / len(new_words)
        
        # More lenient similarity check for granular updates
        threshold = 0.8 if new_emoji else 0.7
        return similarity > threshold
    
    def _is_meaningful_progress(self, narration: str) -> bool:
        """Check if narration represents meaningful progress"""
        # Always meaningful if it contains specific progress indicators
        progress_indicators = [
            '🧠', '📊', '🎯', '⚠️', '💡', '📈', '⚙️', '✅', '🤝', '🔍',
            '🛠️', '📝', '🔧', '🌐', '📋'  # Added granular indicators
        ]
        
        # Also check for key action words
        action_words = ['executing', 'analyzing', 'processing', 'retrieving', 'coordinating', 'routing']
        
        return (any(indicator in narration for indicator in progress_indicators) or
                any(word in narration.lower() for word in action_words))
    
    def reset_for_new_conversation(self):
        """Reset controller state for new conversation"""
        self.last_update_time = 0
        self.last_message_content = ""
        self.reasoning_history = []
        self.update_count = 0

class ConversationTracker:
    """Enhanced conversation tracking for comprehensive agent analysis"""
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.start_time = datetime.now(timezone.utc)
        self.current_agent_step = None
        self.agent_start_times = {}
        self.function_calls = []
        
        # Initialize conversation unit with defaults
        try:
            self.conversation_unit = ConversationUnit(
                conversation_id=conversation_id,
                session_id="",
                user_id="",
                channel="",
                start_timestamp=self.start_time.isoformat(),
                end_timestamp="",
                user_query="",
                temporal_context="",
                agents_involved=[],
                agent_flow=[],
                final_response="",
                collaboration_map={},
                function_audit={},
                success=False,
                processing_time_ms=0,
                error_details=None
            )
        except NameError:
            # Fallback if schema classes not available
            self.conversation_unit = {
                "conversation_id": conversation_id,
                "start_timestamp": self.start_time.isoformat(),
                "agent_flow": [],
                "function_calls": []
            }
    
    def start_conversation(self, user_query: str, user_id: str, channel: str, session_id: str, temporal_context: str = ""):
        """Initialize conversation tracking"""
        if hasattr(self.conversation_unit, 'user_query'):
            self.conversation_unit.user_query = user_query
            self.conversation_unit.user_id = user_id
            self.conversation_unit.channel = channel
            self.conversation_unit.session_id = session_id
            self.conversation_unit.temporal_context = temporal_context
        else:
            self.conversation_unit.update({
                "user_query": user_query,
                "user_id": user_id,
                "channel": channel,
                "session_id": session_id,
                "temporal_context": temporal_context
            })
    
    def start_agent_execution(self, agent_name: str, agent_id: str, context: dict = None):
        """Called when agent execution begins"""
        start_time = datetime.now(timezone.utc).isoformat()
        self.agent_start_times[agent_name] = start_time
        
        try:
            self.current_agent_step = AgentFlowStep(
                agent_name=agent_name,
                agent_id=agent_id,
                start_time=start_time,
                end_time="",
                reasoning_text="",
                bedrock_trace_content=BedrockTraceContent(),
                tools_used=[],
                data_operations=[]
            )
        except NameError:
            # Fallback
            self.current_agent_step = {
                "agent_name": agent_name,
                "agent_id": agent_id,
                "start_time": start_time,
                "end_time": "",
                "reasoning_text": "",
                "tools_used": []
            }
        
        # Track agents involved
        if hasattr(self.conversation_unit, 'agents_involved'):
            if agent_name not in self.conversation_unit.agents_involved:
                self.conversation_unit.agents_involved.append(agent_name)
    
    def add_agent_reasoning(self, reasoning_text: str, trace_content: dict = None):
        """Add reasoning text and trace content to current agent"""
        if self.current_agent_step:
            if hasattr(self.current_agent_step, 'reasoning_text'):
                if not hasattr(self.current_agent_step, '_reasoning_parts'):
                    self.current_agent_step._reasoning_parts = [self.current_agent_step.reasoning_text] if self.current_agent_step.reasoning_text else []
                self.current_agent_step._reasoning_parts.append(reasoning_text)
                self.current_agent_step.reasoning_text = "\n".join(self.current_agent_step._reasoning_parts) + "\n"
            else:
                if "_reasoning_parts" not in self.current_agent_step:
                    existing_text = self.current_agent_step.get("reasoning_text", "")
                    self.current_agent_step["_reasoning_parts"] = [existing_text] if existing_text else []
                self.current_agent_step["_reasoning_parts"].append(reasoning_text)
                self.current_agent_step["reasoning_text"] = "\n".join(self.current_agent_step["_reasoning_parts"]) + "\n"
            
            # Add trace content if available
            if trace_content and hasattr(self.current_agent_step, 'bedrock_trace_content'):
                self._merge_trace_content(trace_content)
    
    def _merge_trace_content(self, trace_content: dict):
        """Merge trace content into current agent step"""
        if hasattr(self.current_agent_step.bedrock_trace_content, 'raw_trace_data'):
            if trace_content.get('modelInvocationInput'):
                self.current_agent_step.bedrock_trace_content.modelInvocationInput = str(trace_content['modelInvocationInput'])
            if trace_content.get('invocationInput'):
                self.current_agent_step.bedrock_trace_content.invocationInput = str(trace_content['invocationInput'])
            if trace_content.get('actionGroupInvocationInput'):
                self.current_agent_step.bedrock_trace_content.actionGroupInvocationInput = str(trace_content['actionGroupInvocationInput'])
            if trace_content.get('observation'):
                self.current_agent_step.bedrock_trace_content.observation = str(trace_content['observation'])
            
            self.current_agent_step.bedrock_trace_content.raw_trace_data = trace_content
    
    def add_tool_execution(self, tool_name: str, parameters: dict, result: str, execution_time_ms: int, success: bool = True):
        """Add tool execution to current agent"""
        try:
            tool_execution = ToolExecution(
                tool_name=tool_name,
                parameters=parameters,
                execution_time_ms=execution_time_ms,
                result_summary=result[:200] + "..." if len(result) > 200 else result,
                full_result=result,
                success=success
            )
        except NameError:
            tool_execution = {
                "tool_name": tool_name,
                "parameters": parameters,
                "execution_time_ms": execution_time_ms,
                "result_summary": result[:200] + "..." if len(result) > 200 else result,
                "success": success
            }
        
        if self.current_agent_step:
            if hasattr(self.current_agent_step, 'tools_used'):
                self.current_agent_step.tools_used.append(tool_execution)
            else:
                if "tools_used" not in self.current_agent_step:
                    self.current_agent_step["tools_used"] = []
                self.current_agent_step["tools_used"].append(tool_execution)
    
    def add_function_call(self, function_call):
        """Add function call to audit trail"""
        self.function_calls.append(function_call)
    
    def complete_agent_execution(self, agent_name: str):
        """Called when agent execution completes"""
        if self.current_agent_step:
            end_time = datetime.now(timezone.utc).isoformat()
            if hasattr(self.current_agent_step, 'end_time'):
                self.current_agent_step.end_time = end_time
            else:
                self.current_agent_step["end_time"] = end_time
            
            # Add to agent flow
            if hasattr(self.conversation_unit, 'agent_flow'):
                self.conversation_unit.agent_flow.append(self.current_agent_step)
            else:
                if "agent_flow" not in self.conversation_unit:
                    self.conversation_unit["agent_flow"] = []
                self.conversation_unit["agent_flow"].append(self.current_agent_step)
            
            self.current_agent_step = None
    
    def complete_conversation(self, final_response: str, success: bool, error_details: dict = None):
        """Complete conversation tracking"""
        end_time = datetime.now(timezone.utc)
        processing_time_ms = int((end_time - self.start_time).total_seconds() * 1000)
        
        if hasattr(self.conversation_unit, 'final_response'):
            self.conversation_unit.final_response = final_response
            self.conversation_unit.success = success
            self.conversation_unit.processing_time_ms = processing_time_ms
            self.conversation_unit.end_timestamp = end_time.isoformat()
            self.conversation_unit.error_details = error_details
            
            # Build collaboration map
            try:
                # Create a temporary processor instance to access collaboration methods
                temp_processor = CompleteSlackBedrockProcessor()
                self.conversation_unit.collaboration_map = temp_processor._build_collaboration_map(
                    self.conversation_unit.agent_flow
                )
            except Exception as e:
                print(f"Error building collaboration map: {e}")
                self.conversation_unit.collaboration_map = {}
            
            # Build function audit
            self.conversation_unit.function_audit = {
                "total_functions_called": len(self.function_calls),
                "total_execution_time_ms": sum(fc.execution_time_ms if hasattr(fc, 'execution_time_ms') else fc.get('execution_time_ms', 0) for fc in self.function_calls),
                "success_rate": sum(1 for fc in self.function_calls if (fc.success if hasattr(fc, 'success') else fc.get('success', True))) / len(self.function_calls) if self.function_calls else 1.0,
                "detailed_calls": self.function_calls
            }
        else:
            self.conversation_unit.update({
                "final_response": final_response,
                "success": success,
                "processing_time_ms": processing_time_ms,
                "end_timestamp": end_time.isoformat(),
                "error_details": error_details
            })

class CompleteSlackBedrockProcessor:
    """Complete processor with working Slack integration and full tracing"""
    
    def __init__(self):
        from botocore.config import Config
        
        AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Configure extended timeouts for Bedrock Agent
        bedrock_config = Config(
            region_name=AWS_REGION,
            read_timeout=540,  # 9 minutes for complex analysis
            connect_timeout=60,
            retries={'max_attempts': 2}
        )
        
        self.secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)
        self.bedrock_agent = boto3.client('bedrock-agent-runtime', config=bedrock_config)
        self.bedrock_client = boto3.client('bedrock', region_name=AWS_REGION)  # For memory configuration
        
        # Agent configuration
        # V4 Manager Agent - intelligent router for specialized agent architecture
        # Using Manager Agent with full collaboration capabilities
        self.decision_agent_id = os.environ.get('BEDROCK_AGENT_ID', 'PVWGKOWSOT')
        self.decision_agent_alias_id = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'LH87RBMCUQ')
        
        # Cache for secrets
        self._secrets_cache = {}
        self._cache_timestamp = 0
        self.CACHE_TTL = 300  # 5 minutes
        
        # Environment variables for Slack integration
        self.secrets_arn = os.environ.get('SECRETS_ARN', 'arn:aws:secretsmanager:us-east-1:740202120544:secret:revops-slack-bedrock-secrets-372buh')
        
        # Tracer for this session
        self.tracer = None
        
        # Conversation continuity settings
        self.memory_enabled = True
        self.memory_retention_days = 7  # Keep conversation context for 1 week
        
        # Real-time agent narration
        self.narration_engine = AgentNarrationEngine()
        self.narration_controller = NarrationController()
    
    def create_isolated_session_ids(self, user_id: str, thread_ts: str) -> Dict[str, str]:
        """
        Creates completely isolated session and memory IDs
        ensuring no cross-contamination between conversations
        """
        # Ensure we have valid identifiers
        safe_user_id = user_id or 'anonymous'
        safe_thread_ts = thread_ts or str(int(time.time()))
        
        # Create unique identifier for this specific conversation thread
        base_id = f"slack-{safe_user_id}-{safe_thread_ts}"
        
        return {
            "sessionId": base_id,
            "memoryId": base_id,  # Same as session for complete isolation
            "isolation_level": "thread-specific",
            "user_id": safe_user_id,
            "thread_ts": safe_thread_ts
        }
    
    def get_current_date_context(self) -> str:
        """Get current date and time context for agents"""
        now = datetime.now(timezone.utc)
        
        date_context = f"""
📅 **CURRENT DATE AND TIME CONTEXT:**
- Current Date: {now.strftime('%A, %B %d, %Y')}
- Current Time: {now.strftime('%H:%M UTC')}
- Current Quarter: Q{((now.month - 1) // 3) + 1} {now.year}
- Current Month: {now.strftime('%B %Y')}
- Current Year: {now.year}

**IMPORTANT**: Use this current date information to interpret all time-based references in the user's request.

---

"""
        return date_context

    def process_slack_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack event with full tracing and working Slack responses"""
        
        start_time = time.time()
        # Track processing start time for fallback narration
        self._processing_start_time = start_time
        
        try:
            print(f"Processing Slack event: {json.dumps(event)[:200]}...")
            
            # Extract event details - handle both SQS and direct formats
            if 'Records' in event and len(event['Records']) > 0:
                slack_event = json.loads(event['Records'][0]['body'])
            else:
                slack_event = event
                
            user_query = slack_event.get('message_text') or slack_event.get('text', '')
            user_id = slack_event.get('user_id') or slack_event.get('user', '')
            channel_id = slack_event.get('channel_id') or slack_event.get('channel', '')
            thread_ts = slack_event.get('thread_ts')
            response_message_ts = slack_event.get('response_message_ts')
            
            print(f"Extracted: user={user_id}, channel={channel_id}, thread={thread_ts}")
            
            # Create correlation ID and tracer
            correlation_id = f"slack_{thread_ts or int(time.time())}_{user_id}" if user_id else f"slack_{int(time.time())}"
            self.tracer = AgentTracer(correlation_id)
            
            # Reset narration controller for new conversation
            self.narration_controller.reset_for_new_conversation()
            
            # Add temporal context to query
            current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            date_context = self.get_current_date_context()
            enhanced_query = f"{date_context}**USER REQUEST:**\n{user_query}"
            
            print(f"Enhanced query with temporal context: {enhanced_query[:100]}...")
            
            # Trace incoming Slack message with comprehensive details
            self.tracer.trace_slack_incoming(
                message_content=user_query,
                user_id=user_id,
                channel=channel_id,
                message_ts=thread_ts or response_message_ts or str(int(time.time())),
                event_type="app_mention"
            )
            
            # Trace conversation start
            self.tracer.trace_conversation_start(
                user_query=user_query,
                user_id=user_id,
                channel=channel_id,
                temporal_context=current_date
            )
            
            # Create isolated session and memory IDs for conversation continuity
            session_config = self.create_isolated_session_ids(user_id, thread_ts)
            session_id = session_config["sessionId"]
            memory_id = session_config["memoryId"]
            
            print(f"Session config: {session_config}")
            
            # Call Bedrock Agent with progress updates and memory support
            response = self._invoke_bedrock_agent_with_progress(
                enhanced_query, 
                session_config,
                channel_id,
                response_message_ts,
                thread_ts
            )
            
            agent_response = response.get('output', {}).get('text', 'I encountered an issue processing your request.')
            print(f"Bedrock response received: {len(str(response))} characters")
            
            # Send final response back to Slack
            success = self._send_final_slack_response(slack_event, agent_response, response_message_ts)
            
            # Trace conversation end
            processing_time_ms = int((time.time() - start_time) * 1000)
            # Calculate actual agents used from response traces
            agents_used = self._count_agents_used(response)
            self.tracer.trace_conversation_end(
                response_summary=agent_response[:200],
                total_agents_used=agents_used,
                processing_time_ms=processing_time_ms,
                success=success
            )
            
            if success:
                print(f"Successfully sent response to Slack")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'success',
                        'correlation_id': correlation_id,
                        'processing_time_ms': processing_time_ms,
                        'response_sent': True
                    })
                }
            else:
                print(f"Failed to send response to Slack")
                return {
                    'statusCode': 200,  # Still 200 since processing succeeded
                    'body': json.dumps({
                        'status': 'success',
                        'correlation_id': correlation_id,
                        'processing_time_ms': processing_time_ms,
                        'response_sent': False,
                        'response': agent_response[:100] + '...' if len(agent_response) > 100 else agent_response
                    })
                }
            
        except Exception as e:
            print(f"Error processing Slack event: {str(e)}")
            import traceback
            stack_trace = traceback.format_exc()
            print(f"Full traceback: {stack_trace}")
            
            # Trace error
            if self.tracer:
                self.tracer.trace_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    agent_context="SlackBedrockProcessor.process_slack_event",
                    stack_trace=stack_trace
                )
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'error',
                    'error': str(e)
                })
            }
    
    def _invoke_bedrock_agent_with_progress(self, query: str, session_config: Dict[str, str], 
                                          channel_id: str, message_ts: str, thread_ts: str) -> Dict[str, Any]:
        """Invoke Bedrock agent with progress updates"""
        try:
            session_id = session_config["sessionId"]
            memory_id = session_config["memoryId"]
            print(f"Invoking Bedrock agent {self.decision_agent_id} with session {session_id} and memory {memory_id}")
            
            bedrock_start_time = time.time()
            self._trace_bedrock_request(session_id, query, channel_id, message_ts, thread_ts)
            self._send_initial_narration(channel_id, message_ts, thread_ts)
            
            session_state = self._prepare_session_state(session_config)
            response = self._invoke_bedrock_agent(session_id, memory_id, query, session_state)
            
            output_text = self._process_streaming_response(response, channel_id, message_ts, thread_ts, session_config)
            
            bedrock_processing_time = int((time.time() - bedrock_start_time) * 1000)
            self._trace_bedrock_response(session_id, output_text, bedrock_processing_time)
            
            return {
                'output': {'text': output_text},
                'sessionId': session_id,
                'memoryId': memory_id,
                'session_config': session_config
            }
            
        except Exception as e:
            print(f"Error invoking Bedrock agent: {str(e)}")
            if self.tracer:
                self.tracer.trace_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    agent_context="BedrockAgentInvocation"
                )
            raise
    
    def _trace_bedrock_request(self, session_id: str, query: str, channel_id: str, message_ts: str, thread_ts: str):
        """Trace Bedrock request initiation"""
        if not self.tracer:
            return
            
        self.tracer.trace_bedrock_request(
            agent_id=self.decision_agent_id,
            agent_alias_id=self.decision_agent_alias_id,
            session_id=session_id,
            input_text=query,
            request_metadata={
                "channel_id": channel_id,
                "message_ts": message_ts,
                "thread_ts": thread_ts,
                "agent_type": "V4_Manager_Agent"
            }
        )
        
        self.tracer.trace_agent_invocation(
            source_agent="SlackProcessor",
            target_agent=f"ManagerAgent-V4({self.decision_agent_id})",
            collaboration_type="USER_QUERY_PROCESSING",
            reasoning="Processing user query through V4 Manager Agent for intelligent routing and collaboration"
        )
    
    def _send_initial_narration(self, channel_id: str, message_ts: str, thread_ts: str):
        """Send initial progress narration"""
        if message_ts and channel_id:
            initial_narration = "🧠 Analyzing your request - determining best approach..."
            self._send_narration_update(channel_id, message_ts, initial_narration, thread_ts)
    
    def _prepare_session_state(self, session_config: Dict[str, str]) -> dict:
        """Prepare session state for Bedrock agent"""
        session_state = {
            "sessionAttributes": {
                "conversation_context": "enabled",
                "isolation_level": session_config["isolation_level"],
                "user_id": session_config["user_id"],
                "thread_ts": session_config["thread_ts"]
            }
        }
        
        if self.memory_enabled:
            session_state["sessionAttributes"]["memory_enabled"] = "true"
            
        return session_state
    
    def _invoke_bedrock_agent(self, session_id: str, memory_id: str, query: str, session_state: dict):
        """Invoke the Bedrock agent with given parameters"""
        return self.bedrock_agent.invoke_agent(
            agentId=self.decision_agent_id,
            agentAliasId=self.decision_agent_alias_id,
            sessionId=session_id,
            inputText=query,
            enableTrace=True,
            sessionState=session_state,
            memoryId=memory_id if self.memory_enabled else None
        )
    
    def _process_streaming_response(self, response, channel_id: str, message_ts: str, thread_ts: str, session_config: Dict[str, str]) -> str:
        """Process streaming response from Bedrock agent"""
        output_parts = []
        progress_sent = False
        
        for event in response['completion']:
            if 'chunk' in event:
                output_parts = self._process_chunk_event(event, output_parts, channel_id, message_ts, thread_ts, progress_sent)
                if len(''.join(output_parts)) > 50 and not progress_sent:
                    progress_sent = True
            
            if 'trace' in event:
                self._process_trace_event(event, channel_id, message_ts, thread_ts, session_config)
        
        return ''.join(output_parts)
    
    def _process_chunk_event(self, event, output_parts: list, channel_id: str, message_ts: str, thread_ts: str, progress_sent: bool) -> list:
        """Process chunk event from streaming response"""
        chunk_data = event['chunk'].get('bytes', b'')
        if not chunk_data:
            return output_parts
            
        try:
            chunk_json = json.loads(chunk_data.decode('utf-8'))
            if 'outputText' in chunk_json:
                output_parts.append(chunk_json['outputText'])
                
                # Send progress update if we have substantial content
                if not progress_sent and len(''.join(output_parts)) > 50 and message_ts:
                    self._send_narration_update(channel_id, message_ts, "📈 Processing results - preparing comprehensive response...", thread_ts)
                    
        except json.JSONDecodeError:
            output_parts.append(chunk_data.decode('utf-8', errors='ignore'))
            
        return output_parts
    
    def _process_trace_event(self, event, channel_id: str, message_ts: str, thread_ts: str, session_config: Dict[str, str]):
        """Process trace event from streaming response"""
        trace_data = event['trace']
        
        # Detailed trace logging for monitoring
        if self.tracer:
            self._trace_detailed_agent_activity(trace_data)
        
        # Process agent reasoning for real-time narration
        if message_ts:
            conversation_tracker = getattr(self, 'conversation_tracker', None)
            self._process_agent_reasoning_stream(trace_data, {
                'channel_id': channel_id,
                'message_ts': message_ts,
                'thread_ts': thread_ts,
                'session_config': session_config
            }, conversation_tracker)
    
    def _trace_bedrock_response(self, session_id: str, output_text: str, processing_time_ms: int):
        """Trace Bedrock response completion"""
        print(f"Agent response length: {len(output_text)} characters")
        print(f"Bedrock processing time: {processing_time_ms}ms")
        
        if self.tracer:
            self.tracer.trace_bedrock_response(
                agent_id=self.decision_agent_id,
                response_text=output_text,
                response_metadata={
                    "session_id": session_id,
                    "response_length": len(output_text),
                    "processing_time_ms": processing_time_ms,
                    "agent_type": "V4_Manager_Agent"
                },
                processing_time_ms=processing_time_ms
            )
    
    def _count_agents_used(self, response: Dict[str, Any]) -> int:
        """Count the number of agents used based on response traces"""
        try:
            agents_invoked = set(['DecisionAgent'])  # Always includes the main agent
            
            # Parse through completion traces to find agent invocations
            if 'completion' in response:
                for event in response['completion']:
                    if 'trace' in event and 'orchestrationTrace' in event['trace']:
                        orch_trace = event['trace']['orchestrationTrace']
                        
                        # Check for collaborator invocations
                        if 'invocationInput' in orch_trace:
                            invocation = orch_trace['invocationInput']
                            if 'collaboratorInvocationInput' in invocation:
                                collab = invocation['collaboratorInvocationInput']
                                agent_name = collab.get('collaboratorName', '')
                                if agent_name:
                                    agents_invoked.add(agent_name)
                                    
                                    # Trace the collaboration
                                    if self.tracer:
                                        self.tracer.trace_agent_invocation(
                                            source_agent="DecisionAgent",
                                            target_agent=agent_name,
                                            collaboration_type="AGENT_COLLABORATION",
                                            reasoning=f"Decision Agent calling {agent_name} for specialized task"
                                        )
            
            return len(agents_invoked)
            
        except Exception as e:
            print(f"Error counting agents used: {e}")
            return 1  # Default to 1 if counting fails
    
    def _extract_complete_reasoning_and_trace(self, orch_trace: dict) -> tuple:
        """
        Extract both reasoning text and complete trace content
        Returns: (reasoning_text: str, trace_content: dict)
        """
        reasoning_parts = []
        trace_content = {}
        
        # Extract modelInvocationInput
        if 'modelInvocationInput' in orch_trace:
            input_data = orch_trace['modelInvocationInput']
            if 'text' in input_data:
                trace_content['modelInvocationInput'] = input_data['text']
                # Extract reasoning from input text
                reasoning_parts.append(self._parse_reasoning_from_input(input_data['text']))
        
        # Extract invocationInput
        if 'invocationInput' in orch_trace:
            trace_content['invocationInput'] = str(orch_trace['invocationInput'])
            reasoning_parts.append(self._parse_reasoning_from_invocation(orch_trace['invocationInput']))
        
        # Extract actionGroupInvocationInput
        if 'actionGroupInvocationInput' in orch_trace:
            trace_content['actionGroupInvocationInput'] = str(orch_trace['actionGroupInvocationInput'])
            reasoning_parts.append(self._parse_reasoning_from_action_group(orch_trace['actionGroupInvocationInput']))
        
        # Extract observation
        if 'observation' in orch_trace:
            trace_content['observation'] = str(orch_trace['observation'])
            reasoning_parts.append(self._parse_reasoning_from_observation(orch_trace['observation']))
        
        reasoning_text = ''.join(reasoning_parts)
        
        # Store raw trace data
        trace_content['raw_trace_data'] = orch_trace
        
        return reasoning_text, trace_content
    
    def _parse_reasoning_from_input(self, input_text: str) -> str:
        """Extract FULL reasoning from model input text - capture complete agent thought process"""
        try:
            # Parse JSON structure if present
            if input_text.startswith('{"'):
                import json
                parsed_content = json.loads(input_text)
                
                # CAPTURE FULL AGENT REASONING - no truncation, no filtering
                reasoning_parts = []
                
                # Include ALL human/user content without truncation
                if 'human' in parsed_content:
                    human_content = parsed_content['human']
                    reasoning_parts.append(f"[USER REQUEST]\n{human_content}\n\n")
                
                if 'messages' in parsed_content:
                    # Extract ALL message content - both user and assistant reasoning
                    for msg in parsed_content['messages']:
                        if isinstance(msg, dict):
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', '')
                            reasoning_parts.append(f"[{role.upper()}]\n{content}\n\n")
                
                # Include relevant system context (agent identity) but not massive system prompts
                if 'system' in parsed_content:
                    system_content = parsed_content['system']
                    # Only add agent identity, not full prompt
                    if 'Manager Agent' in system_content and len(system_content) < 500:
                        reasoning_parts.append(f"[AGENT CONTEXT]\n{system_content}\n\n")
                    elif any(agent in system_content for agent in ['Deal Analysis', 'Lead Analysis', 'Data Agent', 'Web Search', 'Execution']) and len(system_content) < 500:
                        reasoning_parts.append(f"[AGENT CONTEXT]\n{system_content}\n\n")
                
                # If we have assistant/agent reasoning, capture it fully
                if 'assistant' in parsed_content:
                    assistant_content = parsed_content['assistant']
                    reasoning_parts.append(f"[AGENT REASONING]\n{assistant_content}\n\n")
                
                reasoning = ''.join(reasoning_parts)
                
                return reasoning if reasoning else input_text
            
            # For non-JSON input, return the full text (likely agent reasoning)
            return f"[FULL INPUT]\n{input_text}\n"
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return the raw input as it might be pure agent reasoning
            return f"[RAW REASONING]\n{input_text}\n"
        except Exception as e:
            return f"[PARSING ERROR] {str(e)}\n[RAW CONTENT]\n{input_text}\n"
    
    def _parse_reasoning_from_invocation(self, invocation_data: dict) -> str:
        """Extract FULL reasoning from invocation data - no truncation"""
        reasoning_parts = []
        
        # Agent collaboration - capture FULL collaboration details
        if 'agentCollaboratorInvocationInput' in invocation_data:
            collab = invocation_data['agentCollaboratorInvocationInput']
            agent_name = collab.get('agentCollaboratorName', 'specialist agent')
            reasoning_parts.append(f"[AGENT COLLABORATION]\nCollaborating with: {agent_name}\n")
            
            if 'input' in collab and 'text' in collab['input']:
                request_text = collab['input']['text']
                reasoning_parts.append(f"Full collaboration request:\n{request_text}\n\n")
            
            # Include any other collaboration data
            other_data = []
            for key, value in collab.items():
                if key not in ['agentCollaboratorName', 'input']:
                    other_data.append(f"{key}: {value}\n")
            if other_data:
                reasoning_parts.extend(other_data)
            reasoning_parts.append("\n")
        
        # Knowledge base lookup - capture FULL search content
        elif 'knowledgeBaseLookupInput' in invocation_data:
            kb_input = invocation_data['knowledgeBaseLookupInput']
            reasoning_parts.append(f"[KNOWLEDGE BASE SEARCH]\n")
            if 'text' in kb_input:
                search_text = kb_input['text']
                reasoning_parts.append(f"Search query:\n{search_text}\n\n")
            
            # Include all KB lookup details
            kb_data = []
            for key, value in kb_input.items():
                if key != 'text':
                    kb_data.append(f"{key}: {value}\n")
            if kb_data:
                reasoning_parts.extend(kb_data)
            reasoning_parts.append("\n")
        
        # Action group execution - capture FULL parameters
        elif 'actionGroupInvocationInput' in invocation_data:
            action_input = invocation_data['actionGroupInvocationInput']
            action_name = action_input.get('actionGroupName', 'unknown action')
            reasoning_parts.append(f"[ACTION GROUP EXECUTION]\nAction: {action_name}\n")
            
            if 'parameters' in action_input:
                reasoning_parts.append("Full Parameters:\n")
                for param in action_input['parameters']:
                    param_name = param.get('name', 'unknown')
                    param_value = str(param.get('value', ''))
                    reasoning_parts.append(f"  {param_name}: {param_value}\n")
            
            # Include all other action group data
            other_data = []
            for key, value in action_input.items():
                if key not in ['actionGroupName', 'parameters']:
                    other_data.append(f"{key}: {value}\n")
            if other_data:
                reasoning_parts.extend(other_data)
            reasoning_parts.append("\n")
        
        return ''.join(reasoning_parts)
    
    def _parse_reasoning_from_action_group(self, action_data: dict) -> str:
        """Extract FULL reasoning from action group invocations - no truncation"""
        action_name = action_data.get('actionGroupName', 'unknown')
        reasoning = f"[ACTION GROUP INVOCATION]\nInvoking: {action_name}\n"
        
        if 'parameters' in action_data:
            reasoning += "Full Parameters:\n"
            for param in action_data['parameters']:
                param_name = param.get('name', 'unknown')
                param_value = str(param.get('value', ''))
                reasoning += f"  {param_name}: {param_value}\n"
        
        # Include all other action group data
        for key, value in action_data.items():
            if key not in ['actionGroupName', 'parameters']:
                reasoning += f"{key}: {value}\n"
        
        return reasoning + "\n"
    
    def _parse_reasoning_from_observation(self, observation_data: dict) -> str:
        """Extract FULL reasoning from agent observations - no truncation"""
        if isinstance(observation_data, dict):
            reasoning = "[OBSERVATION]\n"
            
            # Action group output - capture FULL result
            if 'actionGroupInvocationOutput' in observation_data:
                output = observation_data['actionGroupInvocationOutput']
                reasoning += "Action Group Output:\n"
                if 'text' in output:
                    result_text = output['text']
                    reasoning += f"Result:\n{result_text}\n\n"
                
                # Include all other output data
                for key, value in output.items():
                    if key != 'text':
                        reasoning += f"{key}: {value}\n"
                reasoning += "\n"
            
            # Knowledge base output - capture FULL results
            elif 'knowledgeBaseLookupOutput' in observation_data:
                kb_output = observation_data['knowledgeBaseLookupOutput']
                reasoning += "Knowledge Base Lookup Output:\n"
                if 'retrievedReferences' in kb_output:
                    refs = kb_output['retrievedReferences']
                    reasoning += f"Found {len(refs)} references:\n"
                    for i, ref in enumerate(refs):
                        reasoning += f"Reference {i+1}:\n{ref}\n\n"
                
                # Include all other KB output data
                for key, value in kb_output.items():
                    if key != 'retrievedReferences':
                        reasoning += f"{key}: {value}\n"
                reasoning += "\n"
            
            # Agent collaboration output - capture FULL collaboration result
            elif 'agentCollaboratorInvocationOutput' in observation_data:
                collab_output = observation_data['agentCollaboratorInvocationOutput']
                reasoning += "Agent Collaboration Output:\n"
                if 'text' in collab_output:
                    collab_result = collab_output['text']
                    reasoning += f"Collaboration Result:\n{collab_result}\n\n"
                
                # Include all other collaboration output data
                for key, value in collab_output.items():
                    if key != 'text':
                        reasoning += f"{key}: {value}\n"
                reasoning += "\n"
            
            # Error information - capture FULL error details
            elif 'error' in observation_data:
                error_info = observation_data['error']
                reasoning += f"Error Details:\n{str(error_info)}\n\n"
            
            # Generic observation - capture ALL data
            else:
                reasoning += "Full Observation Data:\n"
                for key, value in observation_data.items():
                    reasoning += f"{key}: {value}\n"
                reasoning += "\n"
            
            return reasoning
        
        # For non-dict observations, capture the full content
        return f"[OBSERVATION]\nFull Content: {str(observation_data)}\n\n"

    def _extract_agent_collaborations(self, trace_data: dict, agent_name: str) -> tuple:
        """
        Extract sent and received agent communications
        Returns: (sent_messages, received_messages)
        """
        sent_messages = []
        received_messages = []
        
        # Look for AgentCommunication__sendMessage in trace
        if 'toolUse' in trace_data:
            for tool_use in trace_data.get('toolUse', []):
                if tool_use.get('name') == 'AgentCommunication__sendMessage':
                    sent_message = {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'recipient': tool_use.get('input', {}).get('recipient'),
                        'content': tool_use.get('input', {}).get('content'),
                        'tool_use_id': tool_use.get('toolUseId')
                    }
                    sent_messages.append(sent_message)
        
        # Look for incoming messages (would be in modelInvocationInput)
        if 'modelInvocationInput' in trace_data:
            input_text = trace_data['modelInvocationInput'].get('text', '')
            if 'from' in input_text.lower() and 'agent' in input_text.lower():
                received_message = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'sender': self._extract_sender_from_input(input_text),
                    'content': input_text,
                    'message_type': 'agent_communication'
                }
                received_messages.append(received_message)
        
        return sent_messages, received_messages
    
    def _extract_sender_from_input(self, input_text: str) -> str:
        """Extract sender agent name from input text"""
        # Look for patterns like "from DealAnalysisAgent" or "Agent: DealAnalysisAgent"
        import re
        patterns = [
            r'from\s+(\w+Agent)',
            r'Agent:\s*(\w+Agent)',
            r'(\w+Agent)\s+says',
            r'(\w+Agent)\s+responded'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, input_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return 'unknown_agent'

    def _build_collaboration_map(self, agent_flow) -> Dict[str, Dict[str, Any]]:
        """Enhanced collaboration map building from agent flow with better data extraction"""
        collaboration_map = {}
        
        try:
            for step in agent_flow:
                # Handle both dataclass and dict formats
                if hasattr(step, 'collaboration_sent'):
                    sent_msgs = step.collaboration_sent
                    received_msgs = step.collaboration_received
                    agent_name = step.agent_name
                    agent_comms = getattr(step, 'agent_communications', [])
                else:
                    sent_msgs = step.get('collaboration_sent', [])
                    received_msgs = step.get('collaboration_received', [])
                    agent_name = step.get('agent_name', 'unknown')
                    agent_comms = step.get('agent_communications', [])
                
                # ENHANCED: Extract collaborations from enhanced agent communications
                for comm in agent_comms:
                    if comm.get('type') in ['sendMessage_detailed', 'agent_communication']:
                        recipient = comm.get('recipient', comm.get('collaborator_name', 'unknown'))
                        content = comm.get('content', '')
                        
                        key = f"{agent_name} → {recipient}"
                        collaboration_map[key] = {
                            'timestamp': comm.get('timestamp', datetime.utcnow().isoformat()),
                            'message': content[:100] + '...' if len(content) > 100 else content,
                            'full_message': content,
                            'tool_name': comm.get('tool_name', 'AgentCommunication'),
                            'communication_type': comm.get('type', 'unknown'),
                            'data_source': comm.get('data_source', 'agent_communications'),
                            'response_time_ms': None
                        }
                    
                    elif comm.get('type') == 'collaboration_output':
                        # Track agent collaboration outputs (responses)
                        collaborator_name = comm.get('collaborator_name', 'unknown')
                        
                        # Try to find matching sent message and add response info
                        for key, collab in collaboration_map.items():
                            if collaborator_name in key and collab.get('response_time_ms') is None:
                                response_time = self._calculate_time_difference(
                                    collab['timestamp'], 
                                    comm.get('timestamp', datetime.utcnow().isoformat())
                                )
                                collab['response_time_ms'] = response_time
                                collab['response_agent'] = collaborator_name
                                break
                
                # ENHANCED: Extract from bedrock trace content if available
                bedrock_trace = step.get('bedrock_trace_content') if isinstance(step, dict) else getattr(step, 'bedrock_trace_content', None)
                if bedrock_trace:
                    trace_collaborations = self._extract_collaborations_from_trace(bedrock_trace, agent_name)
                    for collab_key, collab_data in trace_collaborations.items():
                        if collab_key not in collaboration_map:
                            collaboration_map[collab_key] = collab_data
                
                # Legacy: Track outgoing collaborations from sent_msgs
                for sent_msg in sent_msgs:
                    key = f"{agent_name} → {sent_msg.get('recipient', 'unknown')}"
                    if key not in collaboration_map:  # Don't overwrite enhanced data
                        collaboration_map[key] = {
                            'timestamp': sent_msg.get('timestamp', datetime.utcnow().isoformat()),
                            'message': sent_msg.get('content', '')[:100] + '...' if len(sent_msg.get('content', '')) > 100 else sent_msg.get('content', ''),
                            'full_message': sent_msg.get('content', ''),
                            'communication_type': 'legacy_sent',
                            'data_source': 'collaboration_sent',
                            'response_time_ms': None
                        }
                
                # Legacy: Calculate response times from received_msgs
                for received_msg in received_msgs:
                    for key, collab in collaboration_map.items():
                        if collab.get('response_time_ms') is None:
                            try:
                                if collab['timestamp'] < received_msg.get('timestamp', ''):
                                    time_diff = self._calculate_time_difference(
                                        collab['timestamp'], 
                                        received_msg['timestamp']
                                    )
                                    collab['response_time_ms'] = time_diff
                                    collab['response_agent'] = received_msg.get('sender', 'unknown')
                            except Exception:
                                pass
                                
        except Exception as e:
            print(f"Error building enhanced collaboration map: {e}")
        
        return collaboration_map
    
    def _extract_collaborations_from_trace(self, trace_content, agent_name: str) -> Dict[str, Dict[str, Any]]:
        """Extract collaboration data directly from bedrock trace content"""
        
        collaborations = {}
        
        try:
            trace_str = str(trace_content)
            
            # Look for AgentCommunication patterns
            import re
            comm_pattern = re.compile(r'AgentCommunication__sendMessage.*?recipient=([^,}]+).*?content=([^}]+)', re.DOTALL)
            matches = comm_pattern.findall(trace_str)
            
            for match in matches:
                recipient = match[0].strip().replace('"', '').replace("'", "")
                content = match[1].strip().replace('"', '').replace("'", "")
                
                key = f"{agent_name} → {recipient}"
                collaborations[key] = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': content[:100] + '...' if len(content) > 100 else content,
                    'full_message': content,
                    'tool_name': 'AgentCommunication__sendMessage',
                    'communication_type': 'trace_extracted',
                    'data_source': 'bedrock_trace',
                    'response_time_ms': None
                }
            
            # Look for agent collaboration outputs
            collab_pattern = re.compile(r'agentCollaboratorName:\s*([^\n\r]+)', re.DOTALL)
            collab_matches = collab_pattern.findall(trace_str)
            
            for collaborator_name in collab_matches:
                collaborator_name = collaborator_name.strip()
                # This indicates a response, try to match with existing collaborations
                for key, collab in collaborations.items():
                    if collaborator_name in key and collab.get('response_time_ms') is None:
                        # Estimate response time (trace parsing doesn't have precise timestamps)
                        collab['response_time_ms'] = 5000  # Placeholder estimate
                        collab['response_agent'] = collaborator_name
                        break
                        
        except Exception as e:
            print(f"Error extracting collaborations from trace: {e}")
        
        return collaborations
    
    def _calculate_time_difference(self, start_time: str, end_time: str) -> int:
        """Calculate time difference in milliseconds"""
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return int((end_dt - start_dt).total_seconds() * 1000)
        except Exception as e:
            print(f"Error calculating time difference: {e}")
            return 0

    def _extract_reasoning_from_any_trace(self, orch_trace: dict) -> str:
        """Extract reasoning content from any available trace type"""
        
        # Priority 1: Rationale (existing)
        if 'rationale' in orch_trace:
            return orch_trace['rationale'].get('text', '')
        
        # Priority 2: Model invocation input - extract actual reasoning from agent prompts
        elif 'modelInvocationInput' in orch_trace:
            input_data = orch_trace['modelInvocationInput']
            if 'text' in input_data:
                try:
                    # Parse the text to extract the actual user query or instruction
                    text_content = input_data['text']
                    
                    # Parse JSON structure if present
                    if text_content.startswith('{"'):
                        import json
                        parsed_content = json.loads(text_content)
                        
                        # Look for user instructions in the human field
                        if 'human' in parsed_content:
                            human_content = parsed_content['human']
                            
                            # Extract specific operations from agent instructions
                            if 'Please query the data warehouse to find how many deals are currently in the "Proof of Concept" stage' in human_content:
                                return "📊 Querying data warehouse for deals in PoC stage"
                            elif 'SQL query' in human_content and 'deals' in human_content:
                                return "🔍 Constructing SQL query to analyze deal data"
                            elif 'opportunity_d table' in human_content:
                                return "📈 Accessing opportunity database for analysis"
                            elif 'DataAgent' in human_content or 'data warehouse' in human_content:
                                return "🤝 Coordinating with Data Agent for comprehensive analysis"
                            elif any(word in human_content.lower() for word in ['pipeline', 'deals', 'opportunities']):
                                return "📊 Analyzing pipeline and opportunity data"
                            elif any(word in human_content.lower() for word in ['query', 'sql', 'database']):
                                return "🔍 Executing database queries for insights"
                        
                        # Look for system instructions to understand agent purpose
                        if 'system' in parsed_content:
                            system_content = parsed_content['system']
                            if 'Manager Agent' in system_content and 'SUPERVISOR' in system_content:
                                return "🧠 Manager Agent coordinating analysis approach"
                            elif 'Data Analysis Agent' in system_content:
                                return "📊 Data Agent processing analytical request"
                    
                    # Fallback to analyzing raw text content
                    text_lower = text_content.lower()
                    if 'poc stage' in text_lower or 'proof of concept' in text_lower:
                        return "📊 Analyzing deals in Proof of Concept stage"
                    elif 'pipeline' in text_lower and ('q3' in text_lower or 'q4' in text_lower):
                        return "📈 Analyzing quarterly pipeline performance"
                    elif 'deals' in text_lower and 'stage' in text_lower:
                        return "🤝 Analyzing deal stages and progression"
                    elif 'query' in text_lower and 'data' in text_lower:
                        return "🔍 Preparing data queries for analysis"
                    else:
                        return "🧠 Processing analytical request"
                        
                except Exception as e:
                    print(f"Error parsing modelInvocationInput text: {e}")
                    return "🧠 Processing request and determining approach"
            return "Processing input and planning analysis"
        
        # Priority 3: Invocation input (collaboration and tool calls)
        elif 'invocationInput' in orch_trace:
            invocation = orch_trace['invocationInput']
            
            # Agent collaboration
            if 'agentCollaboratorInvocationInput' in invocation:
                collab = invocation['agentCollaboratorInvocationInput']
                agent_name = collab.get('agentCollaboratorName', 'specialist agent')
                if 'input' in collab and 'text' in collab['input']:
                    request_text = collab['input']['text'].lower()
                    if 'proof of concept' in request_text or 'poc' in request_text:
                        return f"🤝 Collaborating with {agent_name} to analyze PoC deals"
                    elif 'query' in request_text and 'data warehouse' in request_text:
                        return f"📊 Working with {agent_name} to query data warehouse"
                    else:
                        return f"🤝 Collaborating with {agent_name} for analysis"
                return f"🤝 Coordinating with {agent_name}"
            
            # Knowledge base lookup
            elif 'knowledgeBaseLookupInput' in invocation:
                kb_input = invocation['knowledgeBaseLookupInput']
                if 'text' in kb_input:
                    search_text = kb_input['text'].lower()
                    if 'sql query' in search_text and 'poc stage' in search_text:
                        return "📚 Searching knowledge base for PoC stage query patterns"
                    elif 'opportunity table' in search_text or 'schema' in search_text:
                        return "📚 Looking up database schema information"
                    elif 'stage name' in search_text and 'poc' in search_text:
                        return "📚 Verifying PoC stage naming conventions"
                    else:
                        return "📚 Searching knowledge base for relevant information"
                return "📚 Querying knowledge base"
            
            # Action group (tool execution)
            elif 'actionGroupInvocationInput' in invocation:
                action_input = invocation['actionGroupInvocationInput']
                if 'parameters' in action_input:
                    params = action_input['parameters']
                    for param in params:
                        if param.get('name') == 'query' and 'value' in param:
                            query_text = param['value'].lower()
                            if 'proof of concept' in query_text:
                                return "⚙️ Executing SQL query for PoC stage deals"
                            elif 'count(*)' in query_text:
                                return "📊 Running count query on opportunity data"
                            elif 'opportunity_d' in query_text:
                                return "🔍 Querying opportunity database"
                            else:
                                return "⚙️ Executing data analysis query"
                return "⚙️ Executing data retrieval operations"
            
            # Generic invocation types
            elif 'invocationType' in invocation:
                inv_type = invocation['invocationType']
                if inv_type == "KNOWLEDGE_BASE":
                    return "📚 Searching knowledge base for context"
                elif inv_type == "ACTION_GROUP":
                    return "⚙️ Executing data operations"
                elif inv_type == "AGENT_COLLABORATOR":
                    return "🤝 Collaborating with specialist agent"
                else:
                    return f"⚙️ Performing {inv_type.lower()} operation"
        
        # Priority 4: Model invocation output
        elif 'modelInvocationOutput' in orch_trace:
            output = orch_trace['modelInvocationOutput']
            if 'rawResponse' in output:
                response = output['rawResponse']
                if 'content' in response:
                    content = str(response['content']).lower()
                    if 'poc' in content or 'proof of concept' in content:
                        return "💭 Analyzing PoC stage requirements"
                    elif 'sql' in content or 'query' in content:
                        return "💭 Formulating database query strategy"
                    elif 'data' in content and 'analysis' in content:
                        return "💭 Processing data analysis approach"
                    else:
                        return "💭 Generating analytical insights"
            return "💭 Processing model response"
        
        # Priority 5: Observation (tool results)
        elif 'observation' in orch_trace:
            obs = orch_trace['observation']
            if 'finalResponse' in obs:
                return "📋 Consolidating findings into final analysis"
            elif 'repromptResponse' in obs:
                return "🔄 Refining analysis based on additional context"
            elif 'actionGroupInvocationOutput' in obs:
                action_output = obs['actionGroupInvocationOutput']
                if 'text' in action_output:
                    output_text = str(action_output['text']).lower()
                    if 'success' in output_text and 'true' in output_text:
                        return "✅ Data retrieved successfully - analyzing results"
                    elif 'error' in output_text:
                        return "⚠️ Handling data query issue"
                    elif 'poc_deal_count' in output_text or 'count' in output_text:
                        return "📊 Processing deal count results"
                    else:
                        return "🔍 Processing query results"
                return "🔍 Processing analysis results"
            else:
                return "⚙️ Processing intermediate results"
        
        # Fallback for any other trace types
        return "🤔 Analyzing request and preparing response"

    def _extract_granular_updates(self, orch_trace: dict, reasoning: str, context: dict) -> list:
        """Extract granular, step-by-step updates from orchestration trace"""
        try:
            updates = []
            updates.extend(self._extract_invocation_updates(orch_trace))
            updates.extend(self._extract_model_output_updates(orch_trace))
            updates.extend(self._extract_observation_updates(orch_trace))
            updates.extend(self._extract_reasoning_updates(reasoning))
            return updates
        except Exception as e:
            print(f"Error extracting granular updates: {e}")
            return ["🔄 Processing your request..."]
    
    def _extract_invocation_updates(self, orch_trace: dict) -> list:
        """Extract updates from invocation input"""
        updates = []
        if 'invocationInput' not in orch_trace:
            return updates
            
        invocation = orch_trace['invocationInput']
        
        if 'actionGroupInvocationInput' in invocation:
            updates.extend(self._extract_action_group_updates(invocation['actionGroupInvocationInput']))
        elif 'collaboratorInvocationInput' in invocation:
            updates.extend(self._extract_collaboration_updates(invocation['collaboratorInvocationInput']))
            
        return updates
    
    def _extract_action_group_updates(self, action_input: dict) -> list:
        """Extract updates from action group invocation"""
        updates = []
        tool_name = action_input.get('actionGroupName', 'unknown_tool')
        
        # Extract parameters for context
        params = action_input.get('parameters', [])
        param_summary = {}
        for param in params[:3]:  # Limit to first 3 params for brevity
            param_name = param.get('name', 'param')
            param_value = param.get('value', '')
            if len(param_value) > 100:
                param_value = param_value[:100] + "..."
            param_summary[param_name] = param_value
        
        if tool_name == 'firebolt_query':
            query_hint = self._get_query_hint(param_summary)
            updates.append(f"🔍 Executing database query{query_hint}...")
            if len(str(param_summary)) < 200:
                updates.append(f"📊 Query parameters: {param_summary}")
        elif tool_name == 'web_search':
            search_terms = param_summary.get('query', 'unknown')
            updates.append(f"🌐 Searching web for: '{search_terms}'...")
        else:
            updates.append(f"🛠️ Using {tool_name} tool with parameters: {param_summary}")
            
        return updates
    
    def _get_query_hint(self, param_summary: dict) -> str:
        """Generate query hint based on parameters"""
        if 'query' not in param_summary:
            return ""
        
        query_text = param_summary['query'].lower()
        if 'opportunity' in query_text or 'deal' in query_text:
            return " (analyzing deals & opportunities)"
        elif 'lead' in query_text or 'contact' in query_text:
            return " (researching leads & contacts)"
        elif 'revenue' in query_text or 'forecast' in query_text:
            return " (examining revenue & forecasts)"
        return ""
    
    def _extract_collaboration_updates(self, collab: dict) -> list:
        """Extract updates from collaboration invocation"""
        updates = []
        agent_name = collab.get('collaboratorName', 'specialist agent')
        collab_input = collab.get('input', {})
        
        if isinstance(collab_input, dict) and 'query' in collab_input:
            query_snippet = collab_input['query'][:150] + "..." if len(collab_input['query']) > 150 else collab_input['query']
            updates.append(f"🤝 Routing to {agent_name}: '{query_snippet}'")
        else:
            updates.append(f"🤝 Collaborating with {agent_name} for specialized analysis...")
            
        return updates
    
    def _extract_model_output_updates(self, orch_trace: dict) -> list:
        """Extract updates from model invocation output"""
        updates = []
        if 'modelInvocationOutput' not in orch_trace:
            return updates
            
        model_output = orch_trace['modelInvocationOutput']
        response_text = model_output.get('text', '')
        
        if response_text:
            if len(response_text) > 500:
                updates.append("📝 Processing comprehensive analysis results...")
            elif "error" in response_text.lower() or "failed" in response_text.lower():
                updates.append("⚠️ Handling processing challenges, adapting approach...")
            elif "routing" in response_text.lower() or "collaborat" in response_text.lower():
                updates.append("🎯 Determining optimal routing strategy...")
            else:
                updates.append("💭 Analyzing data and formulating response...")
                
        return updates
    
    def _extract_observation_updates(self, orch_trace: dict) -> list:
        """Extract updates from observations (tool results)"""
        updates = []
        if 'observation' not in orch_trace:
            return updates
            
        obs = orch_trace['observation']
        
        if 'actionGroupInvocationOutput' in obs:
            updates.extend(self._extract_action_output_updates(obs['actionGroupInvocationOutput']))
        elif 'agentCollaboratorInvocationOutput' in obs:
            updates.extend(self._extract_collab_output_updates(obs['agentCollaboratorInvocationOutput']))
            
        return updates
    
    def _extract_action_output_updates(self, action_output: dict) -> list:
        """Extract updates from action group output"""
        updates = []
        result_text = action_output.get('text', '')
        
        try:
            result_data = json.loads(result_text)
            if isinstance(result_data, dict):
                if 'results' in result_data:
                    result_count = len(result_data['results'])
                    if result_count > 0:
                        updates.append(f"✅ Retrieved {result_count} records from database")
                    else:
                        updates.append("🔍 No matching records found, expanding search criteria...")
                elif 'error' in result_data:
                    updates.append("⚠️ Adjusting query parameters due to data constraints...")
                else:
                    updates.append("📈 Processing structured data results...")
            else:
                updates.append("✅ Tool execution completed successfully")
        except:
            # Not JSON, check for common patterns
            if len(result_text) > 1000:
                updates.append("📊 Processing large dataset results...")
            elif "error" in result_text.lower():
                updates.append("🔧 Handling data access issue, trying alternative approach...")
            else:
                updates.append("✅ Data retrieval completed")
                
        return updates
    
    def _extract_collab_output_updates(self, collab_output: dict) -> list:
        """Extract updates from collaboration output"""
        updates = []
        agent_name = collab_output.get('agentCollaboratorName', 'specialist')
        response_text = collab_output.get('text', '')
        
        if len(response_text) > 500:
            updates.append(f"📋 Receiving comprehensive analysis from {agent_name}...")
        else:
            updates.append(f"✅ {agent_name} analysis complete")
            
        return updates
    
    def _extract_reasoning_updates(self, reasoning: str) -> list:
        """Extract updates from reasoning text"""
        updates = []
        if not reasoning or len(reasoning) <= 100:
            return updates
            
        reasoning_lower = reasoning.lower()
        if 'executing' in reasoning_lower and 'query' in reasoning_lower:
            # Already handled above, skip
            pass
        elif 'analyzing' in reasoning_lower:
            updates.append("🧠 Performing detailed analysis...")
        elif 'routing' in reasoning_lower or 'collaborat' in reasoning_lower:
            updates.append("🎯 Optimizing response strategy...")
        elif 'consolidat' in reasoning_lower or 'summariz' in reasoning_lower:
            updates.append("📝 Synthesizing findings...")
            
        return updates
    
    def _process_agent_reasoning_stream(self, trace_data: dict, context: dict, conversation_tracker=None):
        """Process real-time agent reasoning into user-friendly narration"""
        try:
            print(f"[NARRATION DEBUG] Processing trace data keys: {list(trace_data.keys())}")
            
            # Check for trace key first, then orchestrationTrace
            if 'trace' in trace_data:
                trace_content = trace_data['trace']
                print(f"[NARRATION DEBUG] Found trace content keys: {list(trace_content.keys())}")
                
                if 'orchestrationTrace' in trace_content:
                    orch_trace = trace_content['orchestrationTrace']
                    print(f"[NARRATION DEBUG] orchestrationTrace keys: {list(orch_trace.keys())}")
                else:
                    print(f"[NARRATION DEBUG] No orchestrationTrace in trace content")
                    return
            elif 'orchestrationTrace' in trace_data:
                orch_trace = trace_data['orchestrationTrace']
                print(f"[NARRATION DEBUG] orchestrationTrace keys: {list(orch_trace.keys())}")
            else:
                print(f"[NARRATION DEBUG] No trace or orchestrationTrace found in trace_data")
                return
            
            # ENHANCED: Extract reasoning from any available trace type with conversation tracking
            reasoning, trace_content = self._extract_complete_reasoning_and_trace(orch_trace)
            print(f"[NARRATION DEBUG] Extracted reasoning: {reasoning}")
            
            # Add to conversation tracking if available
            if conversation_tracker and reasoning:
                conversation_tracker.add_agent_reasoning(reasoning, trace_content)
                
                # Extract and track tool executions
                if 'actionGroupInvocationInput' in orch_trace:
                    action_input = orch_trace['actionGroupInvocationInput']
                    tool_name = action_input.get('actionGroupName', 'unknown_tool')
                    parameters = {param.get('name', 'unknown'): param.get('value', '') 
                                for param in action_input.get('parameters', [])}
                    
                    # Look for observation to get results
                    result = "Tool execution in progress"
                    execution_time = 0  # Will be updated when observation is available
                    
                    if 'observation' in orch_trace:
                        obs = orch_trace['observation']
                        if 'actionGroupInvocationOutput' in obs:
                            output = obs['actionGroupInvocationOutput']
                            result = output.get('text', str(output))
                    
                    conversation_tracker.add_tool_execution(
                        tool_name=tool_name,
                        parameters=parameters,
                        result=result,
                        execution_time_ms=execution_time,
                        success=True
                    )
                
                # Extract and track agent collaborations
                sent_messages, received_messages = self._extract_agent_collaborations(orch_trace, "Manager")
                
                # Add collaboration messages to current agent step
                if conversation_tracker.current_agent_step:
                    if hasattr(conversation_tracker.current_agent_step, 'collaboration_sent'):
                        conversation_tracker.current_agent_step.collaboration_sent.extend(sent_messages)
                        conversation_tracker.current_agent_step.collaboration_received.extend(received_messages)
                    else:
                        if 'collaboration_sent' not in conversation_tracker.current_agent_step:
                            conversation_tracker.current_agent_step['collaboration_sent'] = []
                            conversation_tracker.current_agent_step['collaboration_received'] = []
                        conversation_tracker.current_agent_step['collaboration_sent'].extend(sent_messages)
                        conversation_tracker.current_agent_step['collaboration_received'].extend(received_messages)
            
            # ENHANCED: Generate granular, step-by-step updates
            granular_updates = self._extract_granular_updates(orch_trace, reasoning, context)
            
            # Send granular updates with intelligent spacing
            for i, update in enumerate(granular_updates):
                if self.narration_controller.should_send_update(update):
                    print(f"[GRANULAR DEBUG] Sending update {i+1}/{len(granular_updates)}: {update}")
                    start_send_time = time.time()
                    success = self._send_narration_update(
                        context['channel_id'], 
                        context['message_ts'], 
                        update, 
                        context.get('thread_ts')
                    )
                    send_time_ms = int((time.time() - start_send_time) * 1000)
                    self._record_narration_metrics(success, "granular_trace", send_time_ms)
                    
                    # Brief delay between updates for readability (only if multiple updates)
                    # Temporarily disabled to avoid import issues
                    # if len(granular_updates) > 1 and i < len(granular_updates) - 1:
                    #     time.sleep(0.8)
                        
            # Fallback to original narration if no granular updates were generated
            if not granular_updates and reasoning:
                narration = self.narration_engine.convert_reasoning_to_narration(
                    reasoning, context
                )
                
                if narration and self.narration_controller.should_send_update(narration):
                    print(f"[NARRATION DEBUG] Sending fallback narration: {narration}")
                    start_send_time = time.time()
                    success = self._send_narration_update(
                        context['channel_id'], 
                        context['message_ts'], 
                        narration, 
                        context.get('thread_ts')
                    )
                    send_time_ms = int((time.time() - start_send_time) * 1000)
                    self._record_narration_metrics(success, "fallback_trace", send_time_ms)
            
            # Handle agent collaboration events (existing logic)
            if 'invocationInput' in orch_trace:
                invocation = orch_trace['invocationInput']
                
                if 'collaboratorInvocationInput' in invocation:
                    collab = invocation['collaboratorInvocationInput']
                    agent_name = collab.get('collaboratorName', 'agent')
                    
                    # Generate collaboration narration
                    collaboration_narration = f"🎯 Coordinating with {self.narration_engine.agent_mappings.get(agent_name, agent_name)} for specialized analysis..."
                    
                    if self.narration_controller.should_send_update(collaboration_narration):
                        start_collab_time = time.time()
                        success = self._send_narration_update(
                            context['channel_id'],
                            context['message_ts'],
                            collaboration_narration,
                            context.get('thread_ts')
                        )
                        collab_time_ms = int((time.time() - start_collab_time) * 1000)
                        self._record_narration_metrics(success, "collaboration", collab_time_ms)
                        
        except Exception as e:
            print(f"Error processing agent reasoning stream: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            # ENHANCED: Robust fallback error handling
            self._send_fallback_progress_update(trace_data, context)
    
    def _send_fallback_progress_update(self, trace_data: dict, context: dict):
        """Send intelligent fallback progress update when reasoning extraction fails"""
        try:
            fallback_message = self._generate_fallback_narration(trace_data, context)
            
            if self.narration_controller.should_send_update(fallback_message):
                print(f"[NARRATION DEBUG] Sending fallback update: {fallback_message}")
                self._send_narration_update(
                    context['channel_id'],
                    context['message_ts'],
                    fallback_message,
                    context.get('thread_ts')
                )
            else:
                # Last resort - basic progress update
                self._send_basic_progress_update(context)
                
        except Exception as e:
            print(f"Error in fallback progress update: {e}")
            self._send_basic_progress_update(context)
    
    def _generate_fallback_narration(self, trace_data: dict, context: dict) -> str:
        """Generate intelligent fallback narration based on trace type"""
        try:
            # Check user query context for intelligent fallback
            if 'session_config' in context:
                user_query = context.get('user_query', '').lower()
                
                # Enhanced contextual fallback narration
                if 'deal' in user_query and 'toyota' in user_query:
                    return "🤝 Analyzing Toyota North America deal status and assessment..."
                elif 'deal' in user_query and 'status' in user_query:
                    return "🤝 Retrieving deal information and MEDDPICC analysis..."
                elif 'pipeline' in user_query and ('q3' in user_query or 'q4' in user_query):
                    return "📈 Analyzing quarterly pipeline performance and key metrics..."
                elif 'pipeline' in user_query and 'forecast' in user_query:
                    return "🔮 Generating pipeline forecasts and trend analysis..."
                elif 'pipeline' in user_query:
                    return "📊 Processing pipeline metrics and deal progression..."
                elif 'customer' in user_query and 'health' in user_query:
                    return "👥 Calculating customer health scores and risk indicators..."
                elif 'customer' in user_query:
                    return "👥 Reviewing customer data and engagement patterns..."
                elif 'revenue' in user_query or 'consumption' in user_query:
                    return "💰 Analyzing revenue patterns and consumption trends..."
                elif 'analyze' in user_query:
                    return "🔍 Conducting comprehensive data analysis..."
                else:
                    return "🧠 Processing your request with intelligent agent routing..."
            
            # Time-based fallback messages
            import time
            current_time = time.time()
            if hasattr(self, '_processing_start_time'):
                elapsed = current_time - self._processing_start_time
                if elapsed > 10:
                    return "📈 Generating comprehensive analysis - almost ready..."
                elif elapsed > 5:
                    return "🔍 Gathering relevant data and insights..."
            
            return "🧠 Analyzing your request with intelligent routing..."
            
        except Exception as e:
            print(f"Error generating fallback narration: {e}")
            return "🧠 Processing your request..."
    
    def _send_basic_progress_update(self, context: dict):
        """Send basic progress update as last resort"""
        try:
            basic_message = "🧠 *Agent processing* - analyzing your request..."
            self._send_progress_update(
                context['channel_id'],
                context['message_ts'],
                basic_message,
                context.get('thread_ts')
            )
            print(f"[NARRATION DEBUG] Sent basic progress update")
        except Exception as e:
            print(f"Error sending basic progress update: {e}")
    
    def _record_narration_metrics(self, success: bool, narration_type: str, processing_time_ms: int):
        """Record narration success/failure metrics to CloudWatch"""
        try:
            # Record success/failure metric
            cloudwatch.put_metric_data(
                Namespace='RevOps/AgentNarration',
                MetricData=[
                    {
                        'MetricName': 'NarrationSuccess' if success else 'NarrationFailure',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'NarrationType',
                                'Value': narration_type
                            }
                        ]
                    },
                    {
                        'MetricName': 'NarrationProcessingTime',
                        'Value': processing_time_ms,
                        'Unit': 'Milliseconds',
                        'Dimensions': [
                            {
                                'Name': 'NarrationType', 
                                'Value': narration_type
                            }
                        ]
                    }
                ]
            )
            print(f"[METRICS] Recorded narration metrics: success={success}, type={narration_type}, time={processing_time_ms}ms")
        except Exception as e:
            print(f"Error recording narration metrics: {e}")
    
    def _record_slack_api_metrics(self, api_call: str, success: bool, response_time_ms: int):
        """Record Slack API response times and error rates"""
        try:
            cloudwatch.put_metric_data(
                Namespace='RevOps/SlackIntegration',
                MetricData=[
                    {
                        'MetricName': 'SlackAPISuccess' if success else 'SlackAPIFailure',
                        'Value': 1,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'APICall',
                                'Value': api_call
                            }
                        ]
                    },
                    {
                        'MetricName': 'SlackAPIResponseTime',
                        'Value': response_time_ms,
                        'Unit': 'Milliseconds',
                        'Dimensions': [
                            {
                                'Name': 'APICall',
                                'Value': api_call
                            }
                        ]
                    }
                ]
            )
            print(f"[METRICS] Recorded Slack API metrics: {api_call}, success={success}, time={response_time_ms}ms")
        except Exception as e:
            print(f"Error recording Slack API metrics: {e}")
    
    def _trace_detailed_agent_activity(self, trace_data: dict):
        """Parse and trace detailed agent activity from Bedrock traces"""
        try:
            if not self.tracer:
                return
                
            # Parse orchestration traces
            if 'orchestrationTrace' in trace_data:
                orch_trace = trace_data['orchestrationTrace']
                
                # Trace reasoning steps
                if 'rationale' in orch_trace:
                    rationale = orch_trace['rationale']
                    if 'text' in rationale:
                        self.tracer.trace_agent_reasoning(
                            agent_id=self.decision_agent_id,
                            reasoning_step="rationale",
                            thought_process=rationale['text'],
                            decision_factors={"trace_type": "orchestration_rationale"}
                        )
                
                # Trace invocation inputs
                if 'invocationInput' in orch_trace:
                    inv_input = orch_trace['invocationInput']
                    if 'invocationType' in inv_input:
                        invocation_type = inv_input['invocationType']
                        
                        # Trace routing decisions for agent collaborations
                        if invocation_type == "AGENT_COLLABORATOR":
                            collaborator_name = inv_input.get('collaboratorName', 'Unknown')
                            input_text = inv_input.get('inputText', '')
                            
                            self.tracer.trace_routing_decision(
                                router_agent=f"ManagerAgent-V4({self.decision_agent_id})",
                                target_agent=collaborator_name,
                                routing_reason=f"Manager Agent routing to {collaborator_name}",
                                query_classification=self._classify_query_for_routing(input_text)
                            )
                        
                        # Trace tool invocations
                        elif invocation_type == "ACTION_GROUP":
                            action_group = inv_input.get('actionGroupName', 'Unknown')
                            function_name = inv_input.get('function', '')
                            parameters = inv_input.get('parameters', {})
                            
                            self.tracer.trace_tool_execution(
                                agent_id=self.decision_agent_id,
                                tool_name=f"{action_group}.{function_name}",
                                tool_input=parameters,
                                tool_output={"status": "invoked"},
                                execution_time_ms=0  # Will be updated when response comes
                            )
                
                # Trace model invocation details
                if 'modelInvocationInput' in orch_trace:
                    model_input = orch_trace['modelInvocationInput']
                    if 'text' in model_input:
                        # This is the actual prompt sent to the model
                        self.tracer.trace_agent_reasoning(
                            agent_id=self.decision_agent_id,
                            reasoning_step="model_prompt",
                            thought_process=model_input['text'][:1000] + "..." if len(model_input['text']) > 1000 else model_input['text'],
                            decision_factors={
                                "trace_type": "model_invocation_input",
                                "prompt_length": len(model_input['text'])
                            }
                        )
                
                # Trace model responses
                if 'modelInvocationOutput' in orch_trace:
                    model_output = orch_trace['modelInvocationOutput']
                    if 'rawResponse' in model_output:
                        response_content = model_output['rawResponse'].get('content', [])
                        if response_content and len(response_content) > 0:
                            response_text = response_content[0].get('text', '')
                            
                            self.tracer.trace_agent_reasoning(
                                agent_id=self.decision_agent_id,
                                reasoning_step="model_response",
                                thought_process=response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                                decision_factors={
                                    "trace_type": "model_invocation_output",
                                    "response_length": len(response_text)
                                }
                            )
                
                # Trace observation details (tool results)
                if 'observation' in orch_trace:
                    observation = orch_trace['observation']
                    if 'actionGroupInvocationOutput' in observation:
                        action_output = observation['actionGroupInvocationOutput']
                        tool_response = action_output.get('text', '')
                        
                        self.tracer.trace_tool_execution(
                            agent_id=self.decision_agent_id,
                            tool_name=observation.get('type', 'unknown_tool'),
                            tool_input={"observation": True},
                            tool_output={"response": tool_response[:500] + "..." if len(tool_response) > 500 else tool_response},
                            execution_time_ms=0
                        )
                    
                    elif 'collaboratorInvocationOutput' in observation:
                        collab_output = observation['collaboratorInvocationOutput']
                        collaborator_response = collab_output.get('text', '')
                        
                        # Use the agent_response method if it exists, otherwise add it
                        if hasattr(self.tracer, 'trace_agent_response'):
                            self.tracer.trace_agent_response(
                                agent_id=collab_output.get('collaboratorName', 'Unknown'),
                                response_content=collaborator_response[:1000] + "..." if len(collaborator_response) > 1000 else collaborator_response,
                                response_metadata={
                                    "trace_type": "collaborator_response",
                                    "response_length": len(collaborator_response)
                                }
                            )
                        else:
                            # Fallback to reasoning trace
                            self.tracer.trace_agent_reasoning(
                                agent_id=collab_output.get('collaboratorName', 'Unknown'),
                                reasoning_step="collaborator_response",
                                thought_process=collaborator_response[:1000] + "..." if len(collaborator_response) > 1000 else collaborator_response,
                                decision_factors={
                                    "trace_type": "collaborator_response",
                                    "response_length": len(collaborator_response)
                                }
                            )
                        
        except Exception as e:
            print(f"Error tracing detailed agent activity: {str(e)}")
    
    def _classify_query_for_routing(self, query_text: str) -> str:
        """Classify query type for routing decisions - consolidated method"""
        # Use the existing _classify_query_type method with mapping
        query_type = self._classify_query_type(query_text)
        
        # Map AgentTracer classifications to routing classifications
        routing_map = {
            'DEAL_ANALYSIS': 'deal_analysis',
            'LEAD_ASSESSMENT': 'deal_analysis', 
            'CONSUMPTION_ANALYSIS': 'data_analysis',
            'RISK_ASSESSMENT': 'data_analysis',
            'CALL_ANALYSIS': 'data_analysis',
            'GENERAL_QUERY': 'general_query'
        }
        
        return routing_map.get(query_type, 'general_query')
    
    def _send_narration_update(self, channel_id: str, message_ts: str, narration_text: str, thread_ts: str = None) -> bool:
        """Send intelligent agent narration update to Slack"""
        try:
            secrets = self._get_slack_secrets()
            bot_token = secrets.get('bot_token')
            
            if not bot_token:
                print("Bot token not found in secrets")
                return False
            
            # Format narration message
            formatted_message = f"*RevOps Analysis:* 🔍\n\n{narration_text}"
            
            payload = {
                'channel': channel_id,
                'ts': message_ts,
                'text': formatted_message,
                'mrkdwn': True
            }
            
            api_start_time = time.time()
            response = requests.post(
                'https://slack.com/api/chat.update',
                headers={
                    'Authorization': f'Bearer {bot_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=10
            )
            api_time_ms = int((time.time() - api_start_time) * 1000)
            
            response_data = response.json()
            success = response_data.get('ok', False)
            self._record_slack_api_metrics('chat.update', success, api_time_ms)
            
            if success:
                return True
            else:
                print(f"Failed to send narration update: {response_data.get('error')}")
                return False
                
        except Exception as e:
            print(f"Error sending narration update: {e}")
            return False
    
    def _send_progress_update(self, channel_id: str, message_ts: str, progress_text: str, thread_ts: str = None) -> bool:
        """Send a progress update to Slack by updating the message"""
        try:
            secrets = self._get_slack_secrets()
            bot_token = secrets.get('bot_token')
            
            if not bot_token:
                print("Bot token not found in secrets")
                return False
            
            # Progress updates are typically short and don't need markdown conversion
            formatted_message = f"*RevOps Analysis:* 🔍\n\n{progress_text}"
            
            payload = {
                'channel': channel_id,
                'ts': message_ts,
                'text': formatted_message,
                'mrkdwn': True
            }
            
            response = requests.post(
                'https://slack.com/api/chat.update',
                headers={
                    'Authorization': f'Bearer {bot_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=10
            )
            
            response_data = response.json()
            if response_data.get('ok'):
                return True
            else:
                print(f"Failed to send progress update: {response_data.get('error')}")
                return False
                
        except Exception as e:
            print(f"Error sending progress update: {e}")
            return False
    
    def _convert_markdown_to_slack(self, markdown_text: str) -> str:
        """Convert markdown formatting to Slack mrkdwn format"""
        import re
        
        # Start with the original text
        slack_text = markdown_text
        
        # Convert headers - Slack uses *bold* for headers
        slack_text = re.sub(r'^### (.*?)$', r'*\1*', slack_text, flags=re.MULTILINE)
        slack_text = re.sub(r'^## (.*?)$', r'*\1*\n', slack_text, flags=re.MULTILINE)
        slack_text = re.sub(r'^# (.*?)$', r'*\1*\n', slack_text, flags=re.MULTILINE)
        
        # Convert bold text - **text** to *text*
        slack_text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', slack_text)
        
        # Convert tables to formatted text blocks
        lines = slack_text.split('\n')
        formatted_lines = []
        in_table = False
        
        for line in lines:
            # Detect table rows (lines with |)
            if '|' in line and len(line.split('|')) > 2:
                if not in_table:
                    in_table = True
                    formatted_lines.append('')  # Add spacing before table
                
                # Clean up table row - remove outer pipes and format
                cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove first/last empty cells
                
                # Skip separator lines (lines with just dashes)
                if all(cell.replace('-', '').replace(' ', '') == '' for cell in cells):
                    continue
                    
                # Format as aligned text
                formatted_row = '  '.join(f'{cell:<20}' for cell in cells)
                formatted_lines.append(f'`{formatted_row}`')
            else:
                if in_table:
                    formatted_lines.append('')  # Add spacing after table
                    in_table = False
                formatted_lines.append(line)
        
        slack_text = '\n'.join(formatted_lines)
        
        # Convert numbered lists - keep as is, Slack handles them
        # Convert bullet points - ensure consistent formatting
        slack_text = re.sub(r'^- (.*?)$', r'• \1', slack_text, flags=re.MULTILINE)
        
        # Convert code blocks - keep as is, Slack handles ```
        
        # Clean up excessive line breaks but preserve intentional spacing
        slack_text = re.sub(r'\n{4,}', '\n\n\n', slack_text)
        
        # Ensure proper spacing around headers and sections
        slack_text = re.sub(r'(\*[^*]+\*)\n([^*\n])', r'\1\n\n\2', slack_text)
        
        return slack_text.strip()
    
    def _send_final_slack_response(self, slack_event: Dict[str, Any], response_text: str, message_ts: str = None) -> bool:
        """Send final response back to Slack (update existing or send new)"""
        response_start_time = time.time()
        
        try:
            secrets = self._get_slack_secrets()
            bot_token = secrets.get('bot_token')
            
            if not bot_token:
                print("Bot token not found in secrets")
                return False
            
            channel_id = slack_event.get('channel_id') or slack_event.get('channel')
            thread_ts = slack_event.get('thread_ts')
            
            if not channel_id:
                print("No channel ID found in slack event")
                return False
            
            # Convert markdown to Slack format
            slack_formatted_text = self._convert_markdown_to_slack(response_text)
            formatted_response = f"*RevOps Analysis:* ✨\n\n{slack_formatted_text}"
            
            # Try to update existing message first
            success = False
            response_type = "update"
            if message_ts:
                success = self._update_slack_message(channel_id, message_ts, formatted_response)
                if success:
                    response_type = "message_update"
                    
            if not success:
                # Fallback: send new message
                success = self._send_new_slack_message(channel_id, formatted_response, thread_ts)
                response_type = "new_message"
            
            # Trace outgoing Slack response
            processing_time_ms = int((time.time() - response_start_time) * 1000)
            if self.tracer:
                self.tracer.trace_slack_outgoing(
                    response_content=response_text,
                    channel=channel_id,
                    response_type=response_type,
                    processing_time_ms=processing_time_ms
                )
            
            return success
                
        except Exception as e:
            print(f"Error sending final Slack response: {e}")
            return False
    
    def _update_slack_message(self, channel_id: str, message_ts: str, formatted_response: str) -> bool:
        """Update an existing Slack message"""
        try:
            secrets = self._get_slack_secrets()
            bot_token = secrets.get('bot_token')
            
            payload = {
                'channel': channel_id,
                'ts': message_ts,
                'text': formatted_response,
                'mrkdwn': True
            }
            
            response = requests.post(
                'https://slack.com/api/chat.update',
                headers={
                    'Authorization': f'Bearer {bot_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=30
            )
            
            response_data = response.json()
            return response_data.get('ok', False)
            
        except Exception as e:
            print(f"Error updating Slack message: {e}")
            return False
    
    def _send_new_slack_message(self, channel_id: str, formatted_response: str, thread_ts: str = None) -> bool:
        """Send a new message to Slack"""
        message_start_time = time.time()
        
        try:
            secrets = self._get_slack_secrets()
            bot_token = secrets.get('bot_token')
            
            payload = {
                'channel': channel_id,
                'text': formatted_response,
                'mrkdwn': True
            }
            
            if thread_ts:
                payload['thread_ts'] = thread_ts
            
            response = requests.post(
                'https://slack.com/api/chat.postMessage',
                headers={
                    'Authorization': f'Bearer {bot_token}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=30
            )
            
            response_data = response.json()
            success = response_data.get('ok', False)
            
            # Trace the new message send
            processing_time_ms = int((time.time() - message_start_time) * 1000)
            if self.tracer:
                self.tracer.trace_slack_outgoing(
                    response_content=formatted_response,
                    channel=channel_id,
                    response_type="new_message_standalone",
                    processing_time_ms=processing_time_ms
                )
            
            return success
            
        except Exception as e:
            print(f"Error sending new Slack message: {e}")
            return False
    
    def _get_slack_secrets(self) -> Dict[str, Any]:
        """Get Slack secrets from cache or Secrets Manager"""
        current_time = time.time()
        if current_time - self._cache_timestamp > self.CACHE_TTL:
            try:
                response = self.secrets_client.get_secret_value(SecretId=self.secrets_arn)
                self._secrets_cache = json.loads(response['SecretString'])
                self._cache_timestamp = current_time
                print("Refreshed secrets cache")
            except Exception as e:
                print(f"Error retrieving secrets: {e}")
                raise
        
        return self._secrets_cache

def lambda_handler(event, context):
    """Enhanced lambda handler with conversation tracking support"""
    print(f"Lambda invoked with event: {json.dumps(event)[:500]}...")
    
    processor = CompleteSlackBedrockProcessor()
    
    # Handle SQS events (multiple records)
    if 'Records' in event:
        print(f"Processing {len(event['Records'])} SQS records")
        
        success_count = 0
        failure_count = 0
        
        for record in event['Records']:
            # Initialize conversation tracking for each record
            correlation_id = str(uuid.uuid4())
            conversation_tracker = ConversationTracker(correlation_id)
            
            try:
                # Extract message body for conversation tracking
                message_body = json.loads(record['body'])
                
                # Start conversation tracking
                current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                conversation_tracker.start_conversation(
                    user_query=message_body.get('text', ''),
                    user_id=message_body.get('user', ''),
                    channel=message_body.get('channel', ''),
                    session_id=message_body.get('thread_ts', message_body.get('ts', '')),
                    temporal_context=current_date
                )
                
                # Process with tracking
                record_event = {'Records': [record]}
                result = process_slack_event_with_tracking(processor, record_event, conversation_tracker)
                
                # Complete conversation tracking
                conversation_tracker.complete_conversation(
                    final_response=result.get('body', ''),
                    success=result['statusCode'] == 200
                )
                
                # Determine export formats based on conversation characteristics
                export_formats = []
                conversation_unit = conversation_tracker.conversation_unit
                
                # Export ONLY enhanced structured JSON for LLM analysis
                export_formats.append('enhanced_structured_json')
                
                # Export LLM-readable format for complex conversations (>3 steps)
                agent_flow = getattr(conversation_unit, 'agent_flow', conversation_unit.get('agent_flow', []) if isinstance(conversation_unit, dict) else [])
                if len(agent_flow) > 3:
                    export_formats.append('llm_readable')
                
                # Export analysis format for failed conversations
                success = getattr(conversation_unit, 'success', conversation_unit.get('success', True) if isinstance(conversation_unit, dict) else True)
                if not success:
                    export_formats.append('analysis_format')
                    export_formats.append('agent_traces')
                
                # Export metadata for all conversations for analytics
                export_formats.append('metadata_only')
                
                # Log conversation unit to CloudWatch with export
                safe_log_conversation_unit(conversation_unit, export_formats)
                
                if result['statusCode'] == 200:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                failure_count += 1
                error_msg = f"Error processing record {record.get('messageId', 'unknown')}: {str(e)}"
                print(error_msg)
                
                # Log error conversation
                conversation_tracker.complete_conversation(
                    final_response="",
                    success=False,
                    error_details={'error': str(e), 'traceback': traceback.format_exc()}
                )
                # Export with basic formats for error cases
                safe_log_conversation_unit(conversation_tracker.conversation_unit, ['structured_json', 'metadata_only'])
        
        print(f"Processing complete: {success_count} successful, {failure_count} failed")
        
        if failure_count == 0:
            return {'statusCode': 200, 'processedRecords': success_count}
        else:
            raise Exception(f"Failed to process {failure_count} records")
    
    # Handle direct invocation
    else:
        correlation_id = str(uuid.uuid4())
        conversation_tracker = ConversationTracker(correlation_id)
        
        try:
            result = process_slack_event_with_tracking(processor, event, conversation_tracker)
            
            conversation_tracker.complete_conversation(
                final_response=result.get('body', ''),
                success=result['statusCode'] == 200
            )
            # Export with standard formats for direct invocation
            safe_log_conversation_unit(conversation_tracker.conversation_unit, ['structured_json', 'llm_readable', 'metadata_only'])
            
            return result
            
        except Exception as e:
            conversation_tracker.complete_conversation(
                final_response="",
                success=False,
                error_details={'error': str(e), 'traceback': traceback.format_exc()}
            )
            # Export with error formats for failed direct invocation
            safe_log_conversation_unit(conversation_tracker.conversation_unit, ['structured_json', 'analysis_format', 'agent_traces'])
            raise

def process_slack_event_with_tracking(processor, event, conversation_tracker):
    """Process Slack event with conversation tracking"""
    # Attach conversation tracker to processor instance for trace processing
    processor.conversation_tracker = conversation_tracker
    
    # Start agent execution tracking for Manager Agent
    conversation_tracker.start_agent_execution("Manager", processor.decision_agent_id)
    
    try:
        # Process the event using existing processor logic
        result = processor.process_slack_event(event)
    except Exception as e:
        # Add error to current agent tracking
        conversation_tracker.add_agent_reasoning(f"Error during processing: {str(e)}")
        raise
    finally:
        # Complete agent execution tracking
        conversation_tracker.complete_agent_execution("Manager")
        # Clean up tracker reference
        processor.conversation_tracker = None
    
    return result

def safe_log_conversation_unit(conversation_data, export_formats: List[str] = None):
    """
    ALWAYS export full conversation structure to S3 with hierarchical directory structure.
    No CloudWatch conversation units, no fallbacks, no compromises - always full data to S3.
    """
    try:
        # Step 1: Determine conversation ID
        if hasattr(conversation_data, 'conversation_id'):
            conv_id = conversation_data.conversation_id
        elif isinstance(conversation_data, dict) and 'conversation_id' in conversation_data:
            conv_id = conversation_data['conversation_id']
        else:
            print("Error: Invalid conversation data format - no conversation_id")
            return False
        
        # Step 2: Apply system prompt deduplication if available
        if hasattr(conversation_data, 'deduplicate_system_prompts'):
            try:
                dedup_stats = conversation_data.deduplicate_system_prompts()
                print(f"DEDUP_STATS: {json.dumps(dedup_stats)}")
            except Exception as e:
                print(f"Deduplication failed: {e}")
        
        # Step 3: ALWAYS export full conversation to S3
        print(f"Exporting full conversation {conv_id[:8]} to S3...")
        
        # Default export format: ONLY enhanced structured JSON
        if not export_formats:
            export_formats = ['enhanced_structured_json']
        
        try:
            # Export to S3 with hierarchical structure
            s3_urls = export_conversation_to_s3(conversation_data, export_formats)
            
            if s3_urls:
                print(f"SUCCESS: Exported conversation {conv_id[:8]} to S3:")
                for format_name, url in s3_urls.items():
                    print(f"  {format_name}: {url}")
                
                # Create minimal CloudWatch notification for operational visibility
                s3_notification = {
                    "conversation_id": conv_id,
                    "exported_to_s3": True,
                    "s3_locations": s3_urls,
                    "export_formats": export_formats,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Full conversation exported to S3 (standard operation)"
                }
                
                # Send notification to operational CloudWatch log (NOT conversation units)
                _send_to_cloudwatch(s3_notification, f"s3-export-{conv_id[:8]}")
                return True
            else:
                print(f"ERROR: S3 export returned no URLs for conversation {conv_id[:8]}")
                return False
                
        except Exception as s3_error:
            print(f"CRITICAL: S3 export failed for conversation {conv_id[:8]}: {s3_error}")
            import traceback
            print(f"S3 export traceback: {traceback.format_exc()}")
            
            # Emergency minimal logging to CloudWatch
            emergency_log = {
                "conversation_id": conv_id,
                "export_failed": True,
                "error": str(s3_error),
                "timestamp": datetime.now().isoformat(),
                "note": "CRITICAL: S3 export failed - conversation data may be lost"
            }
            _send_to_cloudwatch(emergency_log, f"s3-export-failed-{conv_id[:8]}")
            return False
        
    except Exception as e:
        print(f"CRITICAL: Conversation logging failed completely: {e}")
        import traceback
        print(f"Complete failure traceback: {traceback.format_exc()}")
        
        # Emergency logging
        try:
            emergency_log = {
                "conversation_id": conv_id if 'conv_id' in locals() else "unknown",
                "critical_failure": True,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            _send_to_cloudwatch(emergency_log, "critical-failure")
        except:
            pass  # Don't crash on emergency logging failure
        return False

def _create_optimized_dict(data):
    """Create size-optimized dictionary representation"""
    if isinstance(data, dict):
        optimized = {}
        # Keep essential fields, summarize large ones
        essential_fields = ['conversation_id', 'session_id', 'user_id', 'channel', 
                          'start_timestamp', 'end_timestamp', 'success', 'processing_time_ms']
        
        for field in essential_fields:
            if field in data:
                optimized[field] = data[field]
        
        # Summarize large text fields
        if 'user_query' in data:
            query = data['user_query']
            optimized['user_query'] = query[:200] + "..." if len(query) > 200 else query
        
        if 'final_response' in data:
            response = data['final_response']
            optimized['final_response'] = response[:300] + "..." if len(response) > 300 else response
        
        # Summarize agent flow
        if 'agent_flow' in data and isinstance(data['agent_flow'], list):
            optimized['agent_flow_summary'] = {
                "steps_count": len(data['agent_flow']),
                "agents": [step.get('agent_name', 'unknown') if isinstance(step, dict) else 'unknown' 
                          for step in data['agent_flow'][:5]]  # First 5 agents only
            }
        
        # Add error details if present
        if 'error_details' in data:
            optimized['error_details'] = data['error_details']
        
        return optimized
    else:
        # Try to extract basic info from object
        return {
            "conversation_id": getattr(data, 'conversation_id', 'unknown'),
            "object_type": type(data).__name__,
            "timestamp": datetime.now().isoformat()
        }

def _send_to_cloudwatch(log_data, conv_id):
    """Send log data to CloudWatch"""
    try:
        logs_client = boto3.client('logs', region_name='us-east-1')
        
        # Prepare log message
        if isinstance(log_data, str):
            log_message = log_data
        else:
            log_message = json.dumps(log_data, default=str, separators=(',', ':'))
        
        # Create log event
        log_event = {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'message': log_message
        }
        
        # Generate log stream name
        stream_name = f"conversation-{datetime.now().strftime('%Y%m%d')}-{conv_id[:8]}"
        
        # Create log stream if needed
        try:
            logs_client.create_log_stream(
                logGroupName='/aws/revops-ai/conversation-units',
                logStreamName=stream_name
            )
        except logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        
        # Send log event
        logs_client.put_log_events(
            logGroupName='/aws/revops-ai/conversation-units',
            logStreamName=stream_name,
            logEvents=[log_event]
        )
        
        print(f"Successfully logged conversation {conv_id[:8]} to CloudWatch ({len(log_message)} bytes)")
        return True
        
    except Exception as e:
        print(f"CloudWatch logging failed: {e}")
        return False

def log_conversation_unit(conversation_unit, export_formats: List[str] = None):
    """Enhanced conversation logging with deduplication and optional S3 export"""
    try:
        # Initialize CloudWatch Logs client
        logs_client = boto3.client('logs', region_name='us-east-1')
        
        # Step 1: Deduplicate system prompts
        if hasattr(conversation_unit, 'deduplicate_system_prompts'):
            try:
                dedup_stats = conversation_unit.deduplicate_system_prompts()
                print(f"DEDUP_STATS: {json.dumps(dedup_stats)}")
            except Exception as e:
                print(f"Deduplication failed: {e}")
                dedup_stats = {}
        else:
            dedup_stats = {}
        
        # Step 2: Create structured JSON for CloudWatch (comprehensive)
        if hasattr(conversation_unit, 'to_structured_json'):
            structured_data = conversation_unit.to_structured_json(include_full_traces=True)
            log_message = json.dumps(structured_data, indent=2, default=str)
        elif hasattr(conversation_unit, 'to_analysis_json'):
            analysis_data = conversation_unit.to_analysis_json()
            log_message = json.dumps(analysis_data, indent=2, default=str)
        elif hasattr(conversation_unit, 'to_json'):
            log_message = conversation_unit.to_json()
        else:
            log_message = json.dumps(conversation_unit, default=str, indent=2)
        
        # Create log event
        log_event = {
            'timestamp': int(datetime.now().timestamp() * 1000),
            'message': log_message
        }
        
        # Generate log stream name
        if hasattr(conversation_unit, 'conversation_id'):
            conv_id = conversation_unit.conversation_id
        else:
            conv_id = conversation_unit.get('conversation_id', 'unknown')
        
        stream_name = f"conversation-{datetime.now().strftime('%Y%m%d')}-{conv_id[:8]}"
        
        # Create log stream if needed
        try:
            logs_client.create_log_stream(
                logGroupName='/aws/revops-ai/conversation-units',
                logStreamName=stream_name
            )
        except logs_client.exceptions.ResourceAlreadyExistsException:
            pass
        
        # Send log event
        logs_client.put_log_events(
            logGroupName='/aws/revops-ai/conversation-units',
            logStreamName=stream_name,
            logEvents=[log_event]
        )
        
        # Step 3: Optional S3 export (if formats specified)
        if export_formats:
            export_conversation_to_s3(conversation_unit, export_formats)
        
        # Step 4: Legacy logging for backward compatibility
        try:
            if hasattr(conversation_unit, 'to_json'):
                legacy_json = conversation_unit.to_json()
                print(f"LEGACY_FORMAT: {legacy_json[:200]}...")  # Truncated for logs
        except Exception as e:
            print(f"Legacy logging failed: {e}")
        
        print(f"Successfully logged conversation unit {conv_id[:8]} to CloudWatch")
        
    except Exception as e:
        print(f"Failed to log conversation unit: {e}")
        # Don't raise exception - logging failure shouldn't break the main flow

def export_conversation_to_s3(conversation_unit, formats: List[str]):
    """Export conversation to S3 in specified formats"""
    try:
        # Import here to avoid startup overhead
        import sys
        sys.path.append('/opt/python')
        from conversation_exporter import ConversationExporter
        
        # Configure S3 bucket (from environment or config)
        s3_bucket = os.environ.get('CONVERSATION_EXPORT_BUCKET', 'revops-ai-framework-kb-740202120544')
        
        # Create exporter
        exporter = ConversationExporter(s3_bucket)
        
        # Export conversation
        exported_urls = exporter.export_conversation(conversation_unit, formats)
        
        # Log export results
        print(f"EXPORT_RESULTS: {json.dumps(exported_urls)}")
        
        return exported_urls
        
    except Exception as e:
        print(f"S3 export failed: {e}")
        import traceback
        print(f"S3 export traceback: {traceback.format_exc()}")
        return {}