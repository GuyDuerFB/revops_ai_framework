"""
Manager Agent Wrapper Lambda Function
Wraps the Bedrock Manager Agent for use by the webhook gateway
"""

import json
import boto3
import os
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from decimal import Decimal
from botocore.exceptions import ClientError, BotoCoreError

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize Bedrock Agent Runtime client with longer timeout
bedrock_agent_runtime = boto3.client(
    'bedrock-agent-runtime',
    config=boto3.session.Config(
        read_timeout=900,  # 15 minutes
        retries={'max_attempts': 3}
    )
)

# Environment variables
BEDROCK_AGENT_ID = os.environ.get('BEDROCK_AGENT_ID')
BEDROCK_AGENT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')
MAX_RETRIES = 3
RETRY_DELAY = 2  # Initial retry delay in seconds

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime and other non-serializable objects"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, '__dict__'):
            return str(obj)  # Convert complex objects to string
        return str(obj)

def generate_session_id() -> str:
    """Generate a unique session ID for Bedrock Agent invocation"""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"webhook_{timestamp}_{unique_id}"

def get_current_date_context() -> str:
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

----

"""
    return date_context

def invoke_bedrock_agent(query: str, session_id: str) -> Dict[str, Any]:
    """
    Invoke the Bedrock Manager Agent with retry logic.
    
    Args:
        query: User query to process
        session_id: Session ID for conversation context
        
    Returns:
        Processed response from Bedrock Agent
    """
    # Add current date context to query
    date_context = get_current_date_context()
    enhanced_query = f"{date_context}**USER REQUEST:**\n{query}"
    
    logger.info(f"Invoking Bedrock Agent", extra={
        "agent_id": BEDROCK_AGENT_ID,
        "session_id": session_id,
        "query_length": len(enhanced_query),
        "has_date_context": True
    })
    
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            start_time = time.time()
            
            logger.info(f"Bedrock Agent attempt {attempt + 1}/{MAX_RETRIES}", extra={
                "session_id": session_id,
                "attempt": attempt + 1
            })
            
            # Invoke Bedrock Agent with enhanced query
            response = bedrock_agent_runtime.invoke_agent(
                agentId=BEDROCK_AGENT_ID,
                agentAliasId=BEDROCK_AGENT_ALIAS_ID,
                sessionId=session_id,
                inputText=enhanced_query,
                enableTrace=True
            )
            
            # Process the response stream
            response_text = ""
            traces = []
            
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
                elif 'trace' in event:
                    traces.append(event['trace'])
            
            execution_time = time.time() - start_time
            
            logger.info(f"Bedrock Agent response received", extra={
                "session_id": session_id,
                "response_length": len(response_text),
                "trace_count": len(traces),
                "execution_time_seconds": round(execution_time, 2),
                "attempt": attempt + 1
            })
            
            # Convert traces to JSON-serializable format
            serializable_traces = []
            for trace in traces:
                try:
                    # Use custom JSON encoder to handle datetime objects
                    serializable_traces.append(json.loads(json.dumps(trace, cls=CustomJSONEncoder)))
                except Exception as trace_error:
                    logger.warning(f"Error serializing trace: {str(trace_error)}")
                    # Fallback to string representation
                    serializable_traces.append(str(trace))
            
            return {
                "success": True,
                "response": response_text,
                "outputText": response_text,  # For compatibility
                "sessionId": session_id,
                "source": "manager_agent_bedrock",
                "traces": serializable_traces,
                "execution_time": execution_time,
                "attempts": attempt + 1,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except (ClientError, BotoCoreError) as e:
            last_error = e
            execution_time = time.time() - start_time
            
            # Check if this is a retryable error
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
            is_retryable = error_code in ['ThrottlingException', 'ServiceUnavailableException', 'InternalServerException']
            
            logger.warning(f"Bedrock Agent error (attempt {attempt + 1}/{MAX_RETRIES})", extra={
                "session_id": session_id,
                "error_code": error_code,
                "error_message": str(e),
                "execution_time_seconds": round(execution_time, 2),
                "is_retryable": is_retryable,
                "attempt": attempt + 1
            })
            
            # If it's the last attempt or non-retryable error, don't retry
            if attempt == MAX_RETRIES - 1 or not is_retryable:
                break
                
            # Wait before retrying with exponential backoff
            retry_wait = RETRY_DELAY * (2 ** attempt)
            logger.info(f"Retrying in {retry_wait} seconds", extra={
                "session_id": session_id,
                "retry_wait": retry_wait
            })
            time.sleep(retry_wait)
            
        except Exception as e:
            last_error = e
            execution_time = time.time() - start_time
            
            logger.error(f"Unexpected error (attempt {attempt + 1}/{MAX_RETRIES})", extra={
                "session_id": session_id,
                "error": str(e),
                "execution_time_seconds": round(execution_time, 2),
                "attempt": attempt + 1
            })
            
            # For unexpected errors, break on first attempt
            break
    
    # If we get here, all retries failed
    logger.error(f"All Bedrock Agent attempts failed", extra={
        "session_id": session_id,
        "total_attempts": MAX_RETRIES,
        "final_error": str(last_error)
    })
    
    return {
        "success": False,
        "error": f"Bedrock Agent failed after {MAX_RETRIES} attempts: {str(last_error)}",
        "sessionId": session_id,
        "source": "manager_agent_bedrock",
        "attempts": MAX_RETRIES,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def lambda_handler(event, context):
    """
    AWS Lambda handler for Manager Agent wrapper with full conversation tracing.
    
    Args:
        event: Lambda event containing the request
        context: Lambda context
        
    Returns:
        Manager Agent response with comprehensive tracing
    """
    
    # Initialize conversation adapter for full tracing
    conversation_adapter = None
    full_tracing_available = False
    
    try:
        from http_api_conversation_adapter import HTTPAPIConversationAdapter
        conversation_adapter = HTTPAPIConversationAdapter(s3_bucket=os.environ.get('S3_BUCKET'))
        full_tracing_available = True
        logger.info("Full conversation tracing enabled for Manager Agent wrapper")
    except ImportError as e:
        logger.warning(f"Conversation adapter not available: {e}")
    
    try:
        correlation_id = event.get("correlation_id") or str(uuid.uuid4())
        
        logger.info(f"Manager Agent wrapper invoked with full tracing", extra={
            "request_id": context.aws_request_id,
            "correlation_id": correlation_id,
            "full_tracing_enabled": full_tracing_available
        })
        
        # Extract query from event
        query = event.get("query") or event.get("user_query") or event.get("user_message") or event.get("inputText")
        if not query:
            return {
                "success": False,
                "error": "No query provided in event",
                "sessionId": None,
                "correlation_id": correlation_id
            }
        
        if full_tracing_available and conversation_adapter:
            # Use full conversation tracing
            start_time = time.time()
            
            # Create API conversation context
            api_metadata = conversation_adapter.create_api_conversation_context(event, correlation_id)
            
            # Trace Bedrock agent invocation with full monitoring
            response_text, trace_events = conversation_adapter.trace_bedrock_agent_invocation(
                api_metadata=api_metadata,
                agent_id=BEDROCK_AGENT_ID,
                agent_alias_id=BEDROCK_AGENT_ALIAS_ID,
                user_message=query
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Complete conversation tracking
            conversation_summary = conversation_adapter.complete_api_conversation(
                api_metadata=api_metadata,
                final_response=response_text,
                trace_events=trace_events,
                response_status=200
            )
            
            # Build comprehensive result with full trace data
            result = {
                "success": True,
                "response": response_text,
                "outputText": response_text,  # For compatibility
                "sessionId": api_metadata.conversation_id,
                "correlation_id": correlation_id,
                "source": "manager_agent_bedrock_enhanced",
                "processing_time_ms": processing_time_ms,
                "conversation_metadata": {
                    "conversation_id": api_metadata.conversation_id,
                    "api_endpoint": api_metadata.api_endpoint,
                    "client_identifier": api_metadata.client_identifier,
                    "trace_events_count": len(trace_events),
                    "conversation_summary": conversation_summary['summary_stats']
                },
                "trace_summary": {
                    "total_events": len(trace_events),
                    "agent_invocation_events": len([e for e in trace_events if 'agent_invocation' in e.event_type]),
                    "bedrock_trace_events": len([e for e in trace_events if e.event_type == 'bedrock_trace_captured']),
                    "processing_events": len([e for e in trace_events if 'processing' in e.event_type])
                },
                "full_tracing_enabled": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Manager Agent wrapper completed with full tracing", extra={
                "success": True,
                "session_id": api_metadata.conversation_id,
                "trace_events": len(trace_events),
                "processing_time_ms": processing_time_ms
            })
            
        else:
            # Fallback to basic invocation without full tracing
            session_id = event.get("sessionId") or correlation_id or generate_session_id()
            
            # Invoke Bedrock Agent with basic tracing
            result = invoke_bedrock_agent(query, session_id)
            result["correlation_id"] = correlation_id
            result["full_tracing_enabled"] = False
            
            logger.info(f"Manager Agent wrapper completed with basic tracing", extra={
                "success": result.get("success", False),
                "session_id": session_id,
                "correlation_id": correlation_id
            })
        
        # Add metadata from original event if available
        if "webhook_metadata" in event:
            result["webhook_metadata"] = event["webhook_metadata"]
        
        return result
        
    except Exception as e:
        logger.error(f"Error in Manager Agent wrapper: {str(e)}")
        return {
            "success": False,
            "error": f"Manager Agent wrapper error: {str(e)}",
            "sessionId": event.get("sessionId"),
            "correlation_id": event.get("correlation_id"),
            "full_tracing_enabled": full_tracing_available
        }