"""
Manager Agent Wrapper Lambda Function
Wraps the Bedrock Manager Agent for use by the webhook gateway
"""

import json
import boto3
import os
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Initialize Bedrock Agent Runtime client
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Environment variables
BEDROCK_AGENT_ID = os.environ.get('BEDROCK_AGENT_ID')
BEDROCK_AGENT_ALIAS_ID = os.environ.get('BEDROCK_AGENT_ALIAS_ID', 'TSTALIASID')

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
    Invoke the Bedrock Manager Agent.
    
    Args:
        query: User query to process
        session_id: Session ID for conversation context
        
    Returns:
        Processed response from Bedrock Agent
    """
    try:
        # Add current date context to query
        date_context = get_current_date_context()
        enhanced_query = f"{date_context}**USER REQUEST:**\n{query}"
        
        logger.info(f"Invoking Bedrock Agent", extra={
            "agent_id": BEDROCK_AGENT_ID,
            "session_id": session_id,
            "query_length": len(enhanced_query),
            "has_date_context": True
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
        
        logger.info(f"Bedrock Agent response received", extra={
            "session_id": session_id,
            "response_length": len(response_text),
            "trace_count": len(traces)
        })
        
        # Convert traces to JSON-serializable format
        serializable_traces = []
        for trace in traces:
            try:
                # Convert trace to string to avoid datetime serialization issues
                serializable_traces.append(str(trace))
            except Exception as trace_error:
                logger.warning(f"Error serializing trace: {str(trace_error)}")
        
        return {
            "success": True,
            "response": response_text,
            "outputText": response_text,  # For compatibility
            "sessionId": session_id,
            "source": "manager_agent_bedrock",
            "traces": serializable_traces,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error invoking Bedrock Agent: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "sessionId": session_id,
            "source": "manager_agent_bedrock",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

def lambda_handler(event, context):
    """
    AWS Lambda handler for Manager Agent wrapper.
    
    Args:
        event: Lambda event containing the request
        context: Lambda context
        
    Returns:
        Manager Agent response
    """
    try:
        logger.info(f"Manager Agent wrapper invoked", extra={
            "request_id": context.aws_request_id
        })
        
        # Extract query from event
        query = event.get("query") or event.get("user_query") or event.get("inputText")
        if not query:
            return {
                "success": False,
                "error": "No query provided in event",
                "sessionId": None
            }
        
        # Generate or extract session ID
        session_id = event.get("sessionId") or event.get("correlation_id") or generate_session_id()
        
        # Invoke Bedrock Agent
        result = invoke_bedrock_agent(query, session_id)
        
        # Add metadata from original event if available
        if "webhook_metadata" in event:
            result["webhook_metadata"] = event["webhook_metadata"]
        
        logger.info(f"Manager Agent wrapper completed", extra={
            "success": result.get("success", False),
            "session_id": session_id
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Error in Manager Agent wrapper: {str(e)}")
        return {
            "success": False,
            "error": f"Manager Agent wrapper error: {str(e)}",
            "sessionId": event.get("sessionId")
        }