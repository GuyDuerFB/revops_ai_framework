# RevOps AI Framework - Conversation Monitoring

## Overview

This monitoring system captures complete conversation units from Slack interactions with Bedrock agents, enabling comprehensive analysis of agent reasoning patterns, user needs, and system performance.

## Architecture

```
Slack Message → Lambda Processor → Bedrock Agent → Conversation Tracker → CloudWatch Logs
                       ↓
              Conversation Unit Schema
                       ↓
         /aws/revops-ai/conversation-units
```

## Core Components

### conversation_schema.py
Defines the complete data structure for conversation tracking:
- **ConversationUnit**: Complete conversation record with exact agent reasoning text
- **AgentFlowStep**: Individual agent execution with reasoning and tool usage
- **ToolExecution**: Tool call tracking with parameters and results
- **FunctionCall**: Function execution audit trail

### function_interceptor.py
Decorator system for tracking function calls across the codebase:
- Captures function parameters and responses
- Records execution timing and success status
- Integrates with conversation tracking system

### test_conversation_tracking.py
Comprehensive test suite validating all conversation tracking functionality:
- Unit tests for schema components
- Integration tests for CloudWatch logging
- JSON serialization validation

## CloudWatch Integration

**Primary Log Group**: `/aws/revops-ai/conversation-units`
- Contains complete conversation units with exact agent reasoning text
- Structured JSON events for analysis and querying
- 90-day retention for compliance and optimization

**Event Structure**:
```json
{
  "event_type": "CONVERSATION_UNIT_COMPLETE",
  "conversation_id": "slack_123456_U789012",
  "data": {
    "user_query": "What is the status of the IXIS deal?",
    "agent_flow": [...exact reasoning text...],
    "final_response": "...",
    "processing_time_ms": 15000,
    "success": true
  }
}
```

## Usage

The monitoring system operates automatically when the Slack-Bedrock processor handles conversations. No manual intervention required.

**Running Tests**:
```bash
python3 test_conversation_tracking.py
```

**Key Features**:
- Exact agent reasoning text capture (not summaries)
- Complete tool execution audit trail
- Agent collaboration mapping
- Real-time CloudWatch logging
- Comprehensive error tracking

## Integration

This monitoring system is integrated into:
- `/integrations/slack-bedrock-gateway/lambdas/processor/processor.py`
- All agent functions via function_interceptor decorators
- CloudWatch Logs for centralized analysis

The captured data enables future analysis of agent patterns, user behavior, and system optimization opportunities.

---

**Framework Version**: V5  
**Last Updated**: July 2025  
**Monitoring Region**: us-east-1