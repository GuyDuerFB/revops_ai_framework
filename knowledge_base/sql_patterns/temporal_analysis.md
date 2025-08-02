# Temporal Analysis SQL Patterns

## Daily Rate Calculations

```sql
-- Monthly revenue with daily rates
SELECT 
    date_trunc('month', mrr_report_date_ts) as month,
    COUNT(DISTINCT DATE(mrr_report_date_ts)) as days_in_period,
    SUM(amount) as total_revenue,
    SUM(amount) / COUNT(DISTINCT DATE(mrr_report_date_ts)) as daily_revenue_rate
FROM billing_event_f
WHERE mrr_report_date_ts >= [start_date]
GROUP BY month
ORDER BY month;
```

## Same-Period Comparisons

```sql
-- Compare same elapsed days across periods
WITH current_q3 AS (
    SELECT SUM(amount) as q3_revenue
    FROM billing_event_f 
    WHERE mrr_report_date_ts BETWEEN '2025-07-01' AND '2025-07-05'
),
q2_same_period AS (
    SELECT SUM(amount) as q2_revenue
    FROM billing_event_f
    WHERE mrr_report_date_ts BETWEEN '2025-04-01' AND '2025-04-05'
)
SELECT 
    q3_revenue,
    q2_revenue,
    (q3_revenue - q2_revenue) / q2_revenue * 100 as growth_rate_pct
FROM current_q3, q2_same_period;
```

## Projection Templates

```sql
-- Project current period based on elapsed days
WITH current_period AS (
    SELECT 
        SUM(amount) as partial_revenue,
        COUNT(DISTINCT DATE(mrr_report_date_ts)) as elapsed_days
    FROM billing_event_f 
    WHERE mrr_report_date_ts >= [period_start]
    AND mrr_report_date_ts <= CURRENT_DATE
)
SELECT 
    partial_revenue,
    elapsed_days,
    (partial_revenue / elapsed_days) * [total_days_in_period] as projected_revenue,
    'PROJECTION - Based on ' || elapsed_days || ' days only' as caveat
FROM current_period;
```

## Quarter-over-Quarter Growth Analysis

```sql
-- Compare quarterly performance with same-period elapsed days
SELECT 
    EXTRACT(QUARTER FROM mrr_report_date_ts) as quarter,
    EXTRACT(YEAR FROM mrr_report_date_ts) as year,
    COUNT(DISTINCT DATE(mrr_report_date_ts)) as elapsed_days,
    SUM(amount) as total_revenue,
    SUM(amount) / COUNT(DISTINCT DATE(mrr_report_date_ts)) as daily_avg_revenue,
    LAG(SUM(amount)) OVER (ORDER BY EXTRACT(YEAR FROM mrr_report_date_ts), EXTRACT(QUARTER FROM mrr_report_date_ts)) as prev_quarter_revenue,
    (SUM(amount) - LAG(SUM(amount)) OVER (ORDER BY EXTRACT(YEAR FROM mrr_report_date_ts), EXTRACT(QUARTER FROM mrr_report_date_ts))) / 
    LAG(SUM(amount)) OVER (ORDER BY EXTRACT(YEAR FROM mrr_report_date_ts), EXTRACT(QUARTER FROM mrr_report_date_ts)) * 100 as qoq_growth_pct
FROM billing_event_f
WHERE mrr_report_date_ts >= '2024-01-01'
GROUP BY quarter, year
ORDER BY year, quarter;
```

## Monthly Cohort Analysis

```sql
-- Track customer revenue by signup month cohort
WITH customer_cohorts AS (
    SELECT 
        sa.organization_id,
        date_trunc('month', sa.created_at_ts) as signup_month,
        sa.sf_account_type_custom
    FROM salesforce_account_d sa
    WHERE sa.created_at_ts IS NOT NULL
)
SELECT 
    cc.signup_month,
    date_trunc('month', be.mrr_report_date_ts) as revenue_month,
    DATEDIFF('month', cc.signup_month, date_trunc('month', be.mrr_report_date_ts)) as months_since_signup,
    COUNT(DISTINCT be.organization_id) as active_customers,
    SUM(be.amount) as cohort_revenue
FROM customer_cohorts cc
JOIN billing_event_f be ON cc.organization_id = be.organization_id
WHERE be.mrr_report_date_ts >= cc.signup_month
GROUP BY cc.signup_month, revenue_month, months_since_signup
ORDER BY cc.signup_month, months_since_signup;
```