# Thread-Based Conversation Behavior

## Overview

The RevOps AI Framework now supports thread-based conversations in Slack, providing a more organized and collaborative experience. When users mention @RevBot, the system intelligently handles thread creation and participation.

## Expected Behavior

### 1. Initial Bot Mention
- **User Action**: User mentions @RevBot in a channel message
- **Bot Response**: Bot replies in a thread attached to the original message
- **Result**: A new conversation thread is created

### 2. Thread Continuation
- **User Action**: User mentions @RevBot within an existing thread
- **Bot Response**: Bot replies within the same thread
- **Result**: Conversation continues in the established thread context

### 3. Multi-User Participation
- **User Action**: Multiple users mention @RevBot within the same thread
- **Bot Response**: Bot responds to each user within the thread
- **Result**: Collaborative conversation with multiple participants

## Implementation Details

### Thread Detection Logic

```python
# In handler.py - Extract thread information from Slack events
thread_ts = event_data.get('thread_ts')  # Existing thread
ts = event_data.get('ts')  # Message timestamp

# Determine reply context
reply_thread_ts = thread_ts if thread_ts else ts
```

### Session Management

The system creates thread-specific session IDs to maintain conversation context:

```python
# Thread-based session (when thread_ts exists)
session_id = f"{user_id}:{channel_id}:{thread_ts}"

# Channel-based session (for new threads)
session_id = f"{user_id}:{channel_id}"
```

### Message Routing

All bot responses are sent to the appropriate thread:

```python
# Slack API payload includes thread_ts
payload = {
    'channel': channel_id,
    'text': formatted_response,
    'thread_ts': thread_ts,  # Routes to correct thread
    'mrkdwn': True
}
```

## User Experience Examples

### Example 1: Creating a New Thread

```
Channel: #revenue-analysis
User: @RevBot What were our Q4 2023 revenue numbers?
├─ RevBot: *RevOps Analysis:* ✅
   Based on our Firebolt data warehouse, Q4 2023 revenue was $2.3M...
```

### Example 2: Continuing a Thread

```
Channel: #revenue-analysis
User: @RevBot What were our Q4 2023 revenue numbers?
├─ RevBot: *RevOps Analysis:* ✅
   Based on our Firebolt data warehouse, Q4 2023 revenue was $2.3M...
├─ User: @RevBot How does that compare to Q3?
├─ RevBot: *RevOps Analysis:* ✅
   Q3 2023 revenue was $2.1M, so Q4 showed a 9.5% increase...
```

### Example 3: Multiple Users in Same Thread

```
Channel: #revenue-analysis
User1: @RevBot What were our Q4 2023 revenue numbers?
├─ RevBot: *RevOps Analysis:* ✅
   Based on our Firebolt data warehouse, Q4 2023 revenue was $2.3M...
├─ User2: @RevBot Can you break that down by product line?
├─ RevBot: *RevOps Analysis:* ✅
   Q4 2023 revenue breakdown by product line:
   - Product A: $1.2M (52%)
   - Product B: $0.8M (35%)...
├─ User1: @RevBot What about geographical distribution?
├─ RevBot: *RevOps Analysis:* ✅
   Q4 2023 geographical revenue distribution:
   - North America: $1.4M (61%)...
```

## Technical Benefits

### 1. Conversation Context
- Each thread maintains its own conversation history
- Users can reference previous messages within the thread
- Bedrock Agent maintains session continuity per thread

### 2. Channel Organization
- Reduces main channel clutter
- Related questions stay grouped together
- Easy to follow conversation flow

### 3. Collaborative Analysis
- Multiple users can participate in the same analysis
- Shared context across team members
- Builds on previous questions and responses

### 4. Session Isolation
- Thread conversations are isolated from channel conversations
- Different threads have independent conversation contexts
- User-specific session tracking within threads

## Configuration

### Handler Configuration

The handler captures thread information from Slack events:

```python
# Extract thread context
thread_ts = event_data.get('thread_ts')
ts = event_data.get('ts')

# Determine reply context
reply_thread_ts = thread_ts if thread_ts else ts

# Include in processing data
processing_data = {
    'type': 'app_mention',
    'user_id': user_id,
    'channel_id': channel_id,
    'message_text': user_message,
    'thread_ts': reply_thread_ts,
    'original_event': event_data,
    'response_message_ts': message_ts,
    'timestamp': int(time.time())
}
```

### Processor Configuration

The processor handles thread-aware message sending:

```python
# Thread-specific session ID
if thread_ts:
    session_id = f"{user_id}:{channel_id}:{thread_ts}"
else:
    session_id = f"{user_id}:{channel_id}"

# Send messages to correct thread
success = send_slack_message(channel_id, agent_response, thread_ts)
```

## Testing

Run the comprehensive test suite to verify thread behavior:

```bash
cd /path/to/slack-bedrock-gateway
python test_thread_behavior.py
```

### Test Coverage

1. **Thread Detection**: Verifies handler extracts thread_ts correctly
2. **New Thread Creation**: Tests behavior when no thread_ts exists
3. **Session Management**: Confirms thread-specific session IDs
4. **Message Routing**: Validates messages sent to correct threads
5. **Multi-User Support**: Tests multiple users in same thread
6. **Session Isolation**: Confirms thread vs channel session separation

## Monitoring

### CloudWatch Metrics

Monitor thread-based conversations through:

- `revops-thread-conversations`: Number of thread-based conversations
- `revops-channel-conversations`: Number of channel-based conversations
- `revops-multi-user-threads`: Threads with multiple participants

### Logs

Thread information is logged throughout the process:

```
INFO Processing mention from U123456789 in C123456789
INFO Thread TS: 1234567890.000000
INFO Thread-based session ID: U123456789:C123456789:1234567890.000000
INFO Sending fallback message in thread
```

## Troubleshooting

### Common Issues

1. **Messages Not in Thread**: Check that thread_ts is being passed correctly
2. **Lost Context**: Verify session_id includes thread_ts
3. **Multiple Threads**: Ensure different thread_ts values create separate sessions

### Debug Commands

```bash
# Check for thread-related logs
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'Thread' \
  --start-time $(date -u -d '1 hour ago' +%s)000

# Monitor thread session creation
aws logs filter-log-events \
  --log-group-name '/aws/lambda/revops-slack-bedrock-processor' \
  --filter-pattern 'session_id' \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

## Migration Notes

### Backward Compatibility

The thread behavior is fully backward compatible:
- Existing channel-based conversations continue to work
- No changes needed to existing deployment
- Thread support is automatically enabled

### Deployment

No additional configuration required:
- Thread support is enabled by default
- Existing infrastructure handles thread messages
- All environment variables remain the same

This implementation provides a more organized and collaborative experience while maintaining full backward compatibility with existing functionality.