# Customer Segmentation SQL Patterns

## Basic Customer Type Segmentation

```sql
-- Standard customer classification
SELECT 
    CASE 
        WHEN sa.sf_account_type_custom = 'Commit Customer' THEN 'Commit Customer'
        WHEN sa.sf_account_type_custom = 'PLG Customer' THEN 'PAYG Customer'
        ELSE 'Prospect'
    END as customer_type,
    COUNT(DISTINCT sa.organization_id) as customer_count
FROM salesforce_account_d sa
GROUP BY customer_type;
```

## Revenue by Customer Type

```sql
-- Revenue analysis with customer segmentation
SELECT 
    CASE 
        WHEN sa.sf_account_type_custom = 'Commit Customer' THEN 'Commit Customer'
        WHEN sa.sf_account_type_custom = 'PLG Customer' THEN 'PAYG Customer'
        ELSE 'Prospect'
    END as customer_type,
    date_trunc('month', be.mrr_report_date_ts) as month,
    SUM(be.amount) as total_revenue,
    COUNT(DISTINCT be.organization_id) as paying_customers,
    SUM(be.amount) / COUNT(DISTINCT be.organization_id) as avg_revenue_per_customer
FROM billing_event_f be
LEFT JOIN salesforce_account_d sa ON be.organization_id = sa.organization_id
WHERE be.mrr_report_date_ts >= [start_date]
GROUP BY customer_type, month
ORDER BY month, customer_type;
```

## Consumption by Customer Type

```sql
-- Consumption patterns with customer segmentation using daily customer cost
SELECT 
    CASE 
        WHEN sa.sf_account_type_custom = 'Commit Customer' THEN 'Commit'
        WHEN sa.sf_account_type_custom = 'PLG Customer' THEN 'PLG'
        ELSE 'Prospect'
    END as customer_type,
    SUM(dcc.consumed_fbu) as total_fbu,
    AVG(dcc.consumed_fbu) as avg_fbu_per_customer,
    SUM(dcc.cost_after_discount) as total_cost,
    COUNT(DISTINCT dcc.organization_id) as customer_count
FROM daily_customer_cost_f dcc
LEFT JOIN salesforce_account_d sa ON dcc.organization_id = sa.organization_id
WHERE dcc.start_time >= [start_date]
GROUP BY customer_type;
```

## Advanced Consumption Patterns by Customer Type

```sql
-- Detailed consumption analysis with FB1 vs FB2 breakdown
SELECT 
    CASE 
        WHEN sa.sf_account_type_custom = 'Commit Customer' THEN 'Commit'
        WHEN sa.sf_account_type_custom = 'PLG Customer' THEN 'PLG'
        ELSE 'Prospect'
    END as customer_type,
    CASE WHEN dcc.consumed_fbu > 0 THEN 'FB 2.0' ELSE 'FB 1.0' END as platform,
    COUNT(DISTINCT dcc.organization_id) as customer_count,
    SUM(dcc.consumed_fbu) as total_fbu,
    SUM(dcc.consumed_engine_hours) as total_engine_hours,
    SUM(dcc.cost_after_discount) as total_cost,
    AVG(dcc.cost_after_discount) as avg_cost_per_customer
FROM daily_customer_cost_f dcc
LEFT JOIN salesforce_account_d sa ON dcc.organization_id = sa.organization_id
WHERE dcc.start_time >= [start_date]
GROUP BY customer_type, platform
ORDER BY customer_type, platform;
```

## Customer Lifecycle Analysis

```sql
-- Track customer progression between types
WITH customer_progression AS (
    SELECT 
        organization_id,
        MIN(created_at_ts) as first_signup,
        MIN(CASE WHEN sf_account_type_custom = 'PLG Customer' THEN created_at_ts END) as plg_date,
        MIN(CASE WHEN sf_account_type_custom = 'Commit Customer' THEN created_at_ts END) as commit_date
    FROM salesforce_account_d
    GROUP BY organization_id
)
SELECT 
    COUNT(DISTINCT CASE WHEN plg_date IS NOT NULL THEN organization_id END) as plg_conversions,
    COUNT(DISTINCT CASE WHEN commit_date IS NOT NULL THEN organization_id END) as commit_conversions,
    AVG(DATEDIFF('day', first_signup, plg_date)) as avg_days_to_plg,
    AVG(DATEDIFF('day', plg_date, commit_date)) as avg_days_plg_to_commit
FROM customer_progression;
```