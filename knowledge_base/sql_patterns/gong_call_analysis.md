# Gong Call Analysis SQL Patterns

## Basic Call Information Query

```sql
-- Get comprehensive call information with related entities
SELECT
    gong_call_name, -- name of the call
    gong_call_start_ts, -- when the call started - timestamp
    gong_call_end_ts, -- when the call ended - timestamp
    gong_call_duration, -- length of the call
    gong_opportunity_stage_now, -- current opportunity stage, if opportunity was linked
    gong_opp_stage_time_of_call, -- opportunity stage at time of call
    gong_opp_amount_time_of_call, -- TCV of the deal at time of call
    gong_opp_close_date_time_of_call, -- close date at time of call
    gong_opp_probability_time_of_call, -- probability at time of call
    gong_call_brief, -- brief of the call - overall summary
    gong_call_key_points, -- key points during the call - main issues and topics
    gong__call_highlights_next_steps, -- next steps agreed during the call
    sf_account_name, -- name of the account, if available
    contact_name, -- name of the main contact, if available
    opportunity_name, -- name of the opportunity, if available
    lead_name, -- name of the lead, if available
    gong_call_id -- gong call id for API use
FROM gong_call_f
LEFT JOIN salesforce_account_d
    ON salesforce_account_d.sf_account_id = gong_call_f.gong_related_account 
LEFT JOIN contact_d
    ON contact_d.contact_id = gong_call_f.gong_related_contact
LEFT JOIN opportunity_d
    ON opportunity_d.opportunity_id = gong_call_f.gong_related_opportunity
LEFT JOIN lead_d
    ON lead_d.lead_id = gong_call_f.gong_related_lead
WHERE gong_call_f.is_deleted = FALSE
ORDER BY gong_call_start_ts DESC;
```

## Search Calls by Account/Company

```sql
-- Find calls for a specific account (e.g., "IXIS")
SELECT
    gong_call_name,
    gong_call_start_ts,
    gong_call_brief,
    gong_call_key_points,
    gong__call_highlights_next_steps,
    sf_account_name,
    contact_name,
    gong_call_id
FROM gong_call_f
LEFT JOIN salesforce_account_d
    ON salesforce_account_d.sf_account_id = gong_call_f.gong_related_account 
LEFT JOIN contact_d
    ON contact_d.contact_id = gong_call_f.gong_related_contact
WHERE gong_call_f.is_deleted = FALSE
    AND (
        LOWER(sf_account_name) LIKE '%ixis%' 
        OR LOWER(gong_call_name) LIKE '%ixis%'
    )
ORDER BY gong_call_start_ts DESC;
```

## Recent Calls for Account

```sql
-- Get recent calls for an account within date range
SELECT
    gong_call_name,
    gong_call_start_ts,
    gong_call_duration,
    gong_call_brief,
    gong_call_key_points,
    gong__call_highlights_next_steps,
    sf_account_name,
    contact_name,
    gong_call_id
FROM gong_call_f
LEFT JOIN salesforce_account_d
    ON salesforce_account_d.sf_account_id = gong_call_f.gong_related_account 
LEFT JOIN contact_d
    ON contact_d.contact_id = gong_call_f.gong_related_contact
WHERE gong_call_f.is_deleted = FALSE
    AND LOWER(sf_account_name) = 'ixis'
    AND gong_call_start_ts >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY gong_call_start_ts DESC
LIMIT 10;
```

## Last Call with Account

```sql
-- Get the most recent call with a specific account
SELECT
    gong_call_name,
    gong_call_start_ts,
    gong_call_brief,
    gong_call_key_points,
    gong__call_highlights_next_steps,
    sf_account_name,
    contact_name,
    gong_call_id -- Use this ID for Gong API transcript retrieval
FROM gong_call_f
LEFT JOIN salesforce_account_d
    ON salesforce_account_d.sf_account_id = gong_call_f.gong_related_account 
LEFT JOIN contact_d
    ON contact_d.contact_id = gong_call_f.gong_related_contact
WHERE gong_call_f.is_deleted = FALSE
    AND LOWER(sf_account_name) = 'ixis'
ORDER BY gong_call_start_ts DESC
LIMIT 1;
```

## Calls by Opportunity Stage

```sql
-- Analyze calls by opportunity stage
SELECT
    gong_opp_stage_time_of_call,
    COUNT(*) as call_count,
    AVG(gong_opp_probability_time_of_call) as avg_probability,
    SUM(gong_opp_amount_time_of_call) as total_tcv
FROM gong_call_f
WHERE gong_call_f.is_deleted = FALSE
    AND gong_opp_stage_time_of_call IS NOT NULL
    AND gong_call_start_ts >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY gong_opp_stage_time_of_call
ORDER BY call_count DESC;
```

## Calls with Key Topics

```sql
-- Search calls by key topics or keywords
SELECT
    gong_call_name,
    gong_call_start_ts,
    gong_call_brief,
    gong_call_key_points,
    sf_account_name,
    gong_call_id
FROM gong_call_f
LEFT JOIN salesforce_account_d
    ON salesforce_account_d.sf_account_id = gong_call_f.gong_related_account 
WHERE gong_call_f.is_deleted = FALSE
    AND (
        LOWER(gong_call_key_points) LIKE '%pricing%'
        OR LOWER(gong_call_key_points) LIKE '%contract%'
        OR LOWER(gong_call_key_points) LIKE '%technical%'
    )
    AND gong_call_start_ts >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY gong_call_start_ts DESC;
```

## Latest Customer Call Strategy

### CRITICAL: When asked for "latest customer call" or "most recent call"

**Problem**: Simple ORDER BY queries often return internal meetings or calls without content.

**Solution**: Use this specific query pattern to find calls with actual customer content:

```sql
-- Find latest calls with substantial customer content (external, not internal)
SELECT
    gong_call_name,
    gong_call_start_ts,
    gong_call_brief,
    gong_call_key_points,
    gong__call_highlights_next_steps,
    sf_account_name,
    contact_name,
    gong_call_id,
    gong_call_system -- helps identify call type
FROM gong_call_f
LEFT JOIN salesforce_account_d ON salesforce_account_d.sf_account_id = gong_call_f.gong_related_account 
LEFT JOIN contact_d ON contact_d.contact_id = gong_call_f.gong_related_contact
WHERE gong_call_f.is_deleted = FALSE
    AND (
        -- Filter for calls with substantial content
        (gong_call_brief IS NOT NULL AND LENGTH(gong_call_brief) > 50)
        OR (gong_call_key_points IS NOT NULL AND LENGTH(gong_call_key_points) > 50)
        OR (gong__call_highlights_next_steps IS NOT NULL AND LENGTH(gong__call_highlights_next_steps) > 20)
    )
    -- Exclude internal meetings
    AND gong_call_name NOT LIKE '%Weekly Sales Cadence%'
    AND gong_call_name NOT LIKE '%Internal%'
    AND gong_call_name NOT LIKE '%Team Meeting%'
    AND gong_call_name NOT LIKE '%Standup%'
    AND gong_call_name NOT LIKE '%All Hands%'
    AND gong_call_name NOT LIKE '%Daily%'
    -- Must have associated account for customer calls
    AND sf_account_name IS NOT NULL
ORDER BY gong_call_start_ts DESC
LIMIT 10;
```

### Content Validation Steps:
1. **Check content availability**: Verify if call has brief, key points, or next steps
2. **Identify call type**: Distinguish between customer calls, internal meetings, voicemails
3. **Report accurately**: Specify what information is available vs. missing
4. **Offer transcript retrieval**: If user wants full transcript, use gong_call_id with Gong API

### Common Issues to Avoid:
- ❌ Returning internal meetings as "customer calls"
- ❌ Reporting calls without content as "latest with transcript"
- ❌ Not checking if calls are just voicemails or brief touchpoints
- ❌ Using simple ORDER BY without content filtering

## Usage Guidelines

### Priority Order for Call Information:
1. **gong_call_brief** - Quick summary, fastest to process
2. **gong_call_key_points** - Main topics and issues discussed
3. **gong__call_highlights_next_steps** - Action items and follow-up tasks
4. **gong_call_id** - Only use for Gong API transcript when detailed accuracy is needed

### When to Use Gong API:
- When you need verbatim quotes from the call
- When the brief/key points don't contain sufficient detail
- When specifically asked for "transcript" or "exact words"
- When high accuracy is critical for sensitive topics

### Search Patterns:
- Use LOWER() for case-insensitive searches
- Search both account name and call name fields
- Use LIKE '%keyword%' for partial matching
- Consider date ranges for performance

### Performance Tips:
- Always include `is_deleted = FALSE` filter
- Use date ranges to limit results
- Limit results with LIMIT clause when appropriate
- Index on gong_call_start_ts for better performance