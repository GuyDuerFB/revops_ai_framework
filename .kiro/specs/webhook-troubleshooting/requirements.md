# Requirements Document

## Introduction

The webhook processing system is currently broken. POST requests with tracking ID `3fb00afe-b9cf-4891-91b6-b7935e843cc6` and others are being received but are not successfully processed through to agent invocation and response delivery. Messages are coming in but not coming out, and agents are not working properly. This is a root cause analysis and troubleshooting effort to identify and fix the specific failures preventing end-to-end webhook processing.

**Current Problem Statement:**
- Webhook POST requests are received successfully
- Messages appear to be queued but are not processed by agents
- No responses are being delivered to configured webhook endpoints
- Unclear how webhook routing determines which destination URL to use
- System appears to fail silently without clear error reporting

## Requirements

### Requirement 1

**User Story:** As a system administrator, I need to perform a root cause analysis on the broken webhook processing system, so that I can identify exactly where and why the processing pipeline is failing.

#### Acceptance Criteria

1. WHEN investigating the webhook failure THEN I SHALL trace the specific request `3fb00afe-b9cf-4891-91b6-b7935e843cc6` through all system components
2. WHEN examining CloudWatch logs THEN I SHALL find all log entries related to this tracking ID across all Lambda functions
3. WHEN analyzing the processing flow THEN I SHALL identify the exact point where processing stops or fails
4. WHEN reviewing SQS queues THEN I SHALL verify messages are being queued and consumed properly
5. WHEN checking agent invocation THEN I SHALL determine if the manager agent wrapper is being called and responding

### Requirement 2

**User Story:** As a system administrator, I need to verify that the manager agent (Bedrock Agent) is accessible and functional, so that I can rule out or confirm agent-related failures.

#### Acceptance Criteria

1. WHEN testing agent connectivity THEN I SHALL directly invoke the manager agent wrapper Lambda function with a test payload
2. WHEN calling the Bedrock Agent THEN I SHALL verify the agent ID `PVWGKOWSOT` and alias `TSTALIASID` are correctly configured
3. WHEN the agent processes a request THEN I SHALL confirm it returns a properly formatted response
4. WHEN agent invocation fails THEN I SHALL capture the specific error messages and AWS service responses
5. WHEN testing agent timeout THEN I SHALL verify the Lambda timeout settings allow sufficient processing time

### Requirement 3

**User Story:** As a system administrator, I need to validate that SQS message processing is working correctly, so that I can ensure messages flow from webhook receipt to agent processing.

#### Acceptance Criteria

1. WHEN a webhook request is received THEN I SHALL verify the message is properly formatted and queued to `OUTBOUND_WEBHOOK_QUEUE_URL`
2. WHEN the queue processor runs THEN I SHALL confirm it successfully retrieves and processes messages from the queue
3. WHEN processing SQS messages THEN I SHALL verify the message format matches what the queue processor expects
4. WHEN queue processing fails THEN I SHALL identify if it's due to message format, Lambda errors, or queue configuration issues
5. WHEN messages are processed THEN I SHALL confirm they are properly removed from the queue or moved to dead letter queues

### Requirement 4

**User Story:** As a system administrator, I need to fix the webhook routing logic so responses are delivered to the correct destination endpoints.

#### Acceptance Criteria

1. WHEN examining the current routing logic THEN I SHALL document how responses are classified (deal_analysis, data_analysis, lead_analysis, general)
2. WHEN reviewing webhook configuration THEN I SHALL verify all webhook URLs in `deployment-config.json` are accessible and functional
3. WHEN a response is classified THEN I SHALL ensure the system selects the correct webhook URL based on the classification
4. WHEN no specific webhook is configured THEN I SHALL verify the system falls back to the `GENERAL_WEBHOOK_URL` environment variable
5. WHEN webhook delivery fails THEN I SHALL implement proper error handling and retry logic

### Requirement 5

**User Story:** As a system administrator, I need to create diagnostic tools to test and monitor the webhook system, so that I can quickly identify future failures.

#### Acceptance Criteria

1. WHEN troubleshooting THEN I SHALL create a diagnostic script that can trace any tracking ID through the complete system
2. WHEN testing the system THEN I SHALL create a test harness that can send synthetic webhook requests and verify end-to-end processing
3. WHEN monitoring system health THEN I SHALL implement health checks for all critical components (SQS, Lambda, Bedrock, webhook endpoints)
4. WHEN failures occur THEN I SHALL ensure comprehensive error logging with sufficient context for debugging
5. WHEN the system is working THEN I SHALL create monitoring dashboards to track processing success rates and performance

### Requirement 6

**User Story:** As a system administrator, I need to document the fixed system architecture and create operational procedures, so that future issues can be quickly resolved.

#### Acceptance Criteria

1. WHEN the system is fixed THEN I SHALL document the complete request flow with all components and their interactions
2. WHEN creating operational procedures THEN I SHALL provide step-by-step troubleshooting guides for common failure scenarios
3. WHEN documenting configuration THEN I SHALL clearly explain how webhook routing works and how to add new destinations
4. WHEN system changes are made THEN I SHALL update environment variable documentation and deployment procedures
5. WHEN training team members THEN I SHALL provide clear examples of how to trace requests and diagnose issues