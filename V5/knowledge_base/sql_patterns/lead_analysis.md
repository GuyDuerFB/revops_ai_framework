# Lead Analysis SQL Patterns

## Lead Data Overview

The `lead_d` table contains prospect lead information and is fully available for analysis.

### Key Lead Fields
- **lead_id**: Primary key - unique lead identifier
- **lead_name**: Full name of the lead
- **lead_email**: Email address of the lead
- **lead_phone**: Phone number of the lead
- **lead_title**: Job title of the lead
- **lead_company**: Company name of the lead
- **lead_status**: Current status of the lead
- **lead_source**: Source of the lead
- **is_deleted**: Boolean indicating if the lead is deleted
- **created_date_ts**: Timestamp when the lead was created
- **last_modified_date_ts**: Timestamp when the lead was last modified

## Basic Lead Count Queries

### New Leads Created (Last Week)

```sql
-- Count new leads created in the last 7 days
SELECT COUNT(*) as new_leads_count
FROM lead_d 
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '7 days'
    AND created_date_ts < CURRENT_DATE
    AND is_deleted = FALSE;
```

### New Leads by Day (Last Week)

```sql
-- Break down new leads by day for the last week
SELECT 
    DATE(created_date_ts) as lead_date,
    COUNT(*) as new_leads_count
FROM lead_d
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '7 days'
    AND created_date_ts < CURRENT_DATE
    AND is_deleted = FALSE
GROUP BY DATE(created_date_ts)
ORDER BY lead_date;
```

### New Leads This Month vs Last Month

```sql
-- Compare current month vs previous month lead creation
WITH current_month AS (
    SELECT COUNT(*) as current_count
    FROM lead_d
    WHERE created_date_ts >= date_trunc('month', CURRENT_DATE)
        AND created_date_ts < CURRENT_DATE
        AND is_deleted = FALSE
),
previous_month AS (
    SELECT COUNT(*) as previous_count
    FROM lead_d
    WHERE created_date_ts >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')
        AND created_date_ts < date_trunc('month', CURRENT_DATE)
        AND is_deleted = FALSE
)
SELECT 
    current_count,
    previous_count,
    (current_count - previous_count) as difference,
    ROUND(100.0 * (current_count - previous_count) / NULLIF(previous_count, 0), 2) as growth_rate_percent
FROM current_month, previous_month;
```

## Lead Source Analysis

### Leads by Source (Last Week)

```sql
-- Analyze lead sources for new leads in the last week
SELECT 
    COALESCE(lead_source, 'Unknown') as source,
    COUNT(*) as new_leads_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM lead_d
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '7 days'
    AND created_date_ts < CURRENT_DATE
    AND is_deleted = FALSE
GROUP BY lead_source
ORDER BY new_leads_count DESC;
```

### Top Lead Sources (Last 30 Days)

```sql
-- Show top performing lead sources over the last 30 days
SELECT 
    COALESCE(lead_source, 'Unknown') as source,
    COUNT(*) as total_leads,
    COUNT(DISTINCT DATE(created_date_ts)) as active_days,
    ROUND(COUNT(*) / COUNT(DISTINCT DATE(created_date_ts)), 2) as avg_leads_per_day
FROM lead_d
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '30 days'
    AND created_date_ts < CURRENT_DATE
    AND is_deleted = FALSE
GROUP BY lead_source
HAVING COUNT(*) >= 5 -- Filter for meaningful volume
ORDER BY total_leads DESC;
```

## Lead Status Analysis

### Lead Status Distribution (New Leads)

```sql
-- Analyze status distribution of recently created leads
SELECT 
    COALESCE(lead_status, 'Unknown') as status,
    COUNT(*) as lead_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage,
    AVG(DATEDIFF('day', created_date_ts, CURRENT_DATE)) as avg_days_since_creation
FROM lead_d
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '30 days'
    AND created_date_ts < CURRENT_DATE
    AND is_deleted = FALSE
GROUP BY lead_status
ORDER BY lead_count DESC;
```

### Lead Conversion Tracking

```sql
-- Track lead progression and conversion patterns
SELECT 
    lead_status,
    COUNT(*) as total_leads,
    COUNT(CASE WHEN created_date_ts >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as created_last_week,
    COUNT(CASE WHEN last_modified_date_ts >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as modified_last_week,
    ROUND(100.0 * COUNT(CASE WHEN last_modified_date_ts >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) / COUNT(*), 2) as activity_rate_percent
FROM lead_d
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '90 days'
    AND is_deleted = FALSE
GROUP BY lead_status
ORDER BY total_leads DESC;
```

## Lead Quality Analysis

### Lead Company Analysis

```sql
-- Analyze lead distribution by company information
SELECT 
    CASE 
        WHEN lead_company IS NULL OR lead_company = '' THEN 'No Company'
        ELSE 'Has Company'
    END as company_status,
    COUNT(*) as lead_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM lead_d
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '30 days'
    AND created_date_ts < CURRENT_DATE
    AND is_deleted = FALSE
GROUP BY company_status;
```

### Lead Contact Information Completeness

```sql
-- Assess data quality of lead contact information
SELECT 
    COUNT(*) as total_leads,
    COUNT(CASE WHEN lead_email IS NOT NULL AND lead_email != '' THEN 1 END) as with_email,
    COUNT(CASE WHEN lead_phone IS NOT NULL AND lead_phone != '' THEN 1 END) as with_phone,
    COUNT(CASE WHEN lead_company IS NOT NULL AND lead_company != '' THEN 1 END) as with_company,
    COUNT(CASE WHEN lead_title IS NOT NULL AND lead_title != '' THEN 1 END) as with_title,
    ROUND(100.0 * COUNT(CASE WHEN lead_email IS NOT NULL AND lead_email != '' THEN 1 END) / COUNT(*), 2) as email_completion_rate,
    ROUND(100.0 * COUNT(CASE WHEN lead_phone IS NOT NULL AND lead_phone != '' THEN 1 END) / COUNT(*), 2) as phone_completion_rate
FROM lead_d
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '30 days'
    AND created_date_ts < CURRENT_DATE
    AND is_deleted = FALSE;
```

## Time-Based Lead Analysis

### Lead Creation Trends (Last 90 Days)

```sql
-- Show lead creation trends over the last 90 days
SELECT 
    date_trunc('week', created_date_ts) as week_start,
    COUNT(*) as leads_created,
    COUNT(DISTINCT lead_source) as unique_sources,
    COUNT(DISTINCT DATE(created_date_ts)) as active_days_in_week
FROM lead_d
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '90 days'
    AND created_date_ts < CURRENT_DATE
    AND is_deleted = FALSE
GROUP BY date_trunc('week', created_date_ts)
ORDER BY week_start DESC;
```

### Daily Lead Volume Pattern

```sql
-- Analyze which days of the week generate most leads
SELECT 
    DAYNAME(created_date_ts) as day_of_week,
    COUNT(*) as total_leads,
    ROUND(AVG(COUNT(*)) OVER(), 2) as avg_leads_per_day,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage_of_total
FROM lead_d
WHERE created_date_ts >= CURRENT_DATE - INTERVAL '90 days'
    AND created_date_ts < CURRENT_DATE
    AND is_deleted = FALSE
GROUP BY DAYNAME(created_date_ts), DAYOFWEEK(created_date_ts)
ORDER BY DAYOFWEEK(created_date_ts);
```

## Lead-to-Opportunity Conversion

### Leads Connected to Gong Calls

```sql
-- Find leads that have associated Gong calls (engagement indicator)
SELECT 
    COUNT(DISTINCT l.lead_id) as total_leads,
    COUNT(DISTINCT CASE WHEN gc.gong_related_lead IS NOT NULL THEN l.lead_id END) as leads_with_calls,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN gc.gong_related_lead IS NOT NULL THEN l.lead_id END) / COUNT(DISTINCT l.lead_id), 2) as call_engagement_rate
FROM lead_d l
LEFT JOIN gong_call_f gc ON l.lead_id = gc.gong_related_lead AND gc.is_deleted = FALSE
WHERE l.created_date_ts >= CURRENT_DATE - INTERVAL '30 days'
    AND l.created_date_ts < CURRENT_DATE
    AND l.is_deleted = FALSE;
```

## Best Practices for Lead Analysis

1. **Always filter deleted leads**: Use `is_deleted = FALSE`
2. **Use appropriate date ranges**: Consider business context for time periods
3. **Handle null values**: Use COALESCE for lead_source and other nullable fields
4. **Include data quality metrics**: Show completion rates for key fields
5. **Compare time periods**: Show trends and growth rates
6. **Segment by source**: Lead sources often have different conversion characteristics
7. **Consider business days**: Some lead patterns vary by day of week

## Common Lead Analysis Questions

### "How many new leads last week?"
Use the basic new leads count query with 7-day filter.

### "What's our best lead source?"
Use lead source analysis with conversion tracking.

### "Are our leads getting better quality?"
Use lead quality analysis with data completeness metrics.

### "How many leads turn into calls?"
Use the lead-to-opportunity conversion with Gong calls analysis.