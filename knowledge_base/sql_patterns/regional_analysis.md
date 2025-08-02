# Regional Analysis SQL Patterns

## Regional Field Priority Strategy

**CRITICAL: For any regional analysis, use this field priority order:**

### Primary Regional Classification Fields
1. **salesforce_account_d.account_region** - Direct regional assignment
2. **salesforce_account_d.billing_country** - Country-based region mapping  
3. **amberflo_customer_d.customer_country** - Customer location fallback

### Regional Field Availability
- ✅ **account_region** in salesforce_account_d (PRIMARY)
- ✅ **billing_country** in salesforce_account_d (SECONDARY)  
- ✅ **customer_country** in amberflo_customer_d (TERTIARY)
- ✅ **employee-based region** via opportunity owner relationship (ALTERNATIVE)
- ❌ **sales_territory** in employee_d (NOT AVAILABLE directly)

### Regional Analysis via Employee-Opportunity-Account Chain
**Key Relationship**: `employee_d.sf_user_id = opportunity_d.owner_id → opportunity_d.sf_account_id = salesforce_account_d.sf_account_id`

This allows analysis by:
- Opportunity owner name + account region
- Regional performance by sales team member
- Territory analysis through opportunity ownership patterns

### Standard Regional Query Pattern

```sql
-- Standard regional breakdown with fallback logic
SELECT
    COALESCE(
        sa.account_region,
        CASE 
            WHEN sa.billing_country = 'US' THEN 'North America'
            WHEN sa.billing_country IN ('CA', 'MX') THEN 'North America'
            WHEN sa.billing_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL') THEN 'Europe'
            WHEN sa.billing_country IN ('JP', 'KR', 'SG', 'AU') THEN 'APAC'
            WHEN ac.customer_country = 'US' THEN 'North America'
            WHEN ac.customer_country IN ('CA', 'MX') THEN 'North America'
            WHEN ac.customer_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL') THEN 'Europe'
            WHEN ac.customer_country IN ('JP', 'KR', 'SG', 'AU') THEN 'APAC'
            ELSE 'Unknown'
        END
    ) as region,
    -- your metrics here
FROM your_main_table
LEFT JOIN salesforce_account_d sa ON your_main_table.sf_account_id = sa.sf_account_id
LEFT JOIN amberflo_customer_d ac ON sa.organization_id = ac.organization_id
GROUP BY region;
```

## Opportunity Regional Analysis

### New Opportunities by Region (Last Week)

```sql
-- Find new opportunities created last week by region
SELECT
    COALESCE(
        sa.account_region,
        CASE 
            WHEN sa.billing_country = 'US' THEN 'North America'
            WHEN sa.billing_country IN ('CA', 'MX') THEN 'North America'
            WHEN sa.billing_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN sa.billing_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            WHEN ac.customer_country = 'US' THEN 'North America'
            WHEN ac.customer_country IN ('CA', 'MX') THEN 'North America'
            WHEN ac.customer_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN ac.customer_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            ELSE 'Unknown'
        END
    ) as region,
    COUNT(*) as new_opportunities,
    SUM(o.amount) as total_tcv,
    AVG(o.amount) as avg_tcv,
    -- Show data quality
    COUNT(CASE WHEN sa.account_region IS NOT NULL THEN 1 END) as with_account_region,
    COUNT(CASE WHEN sa.billing_country IS NOT NULL THEN 1 END) as with_billing_country,
    COUNT(CASE WHEN ac.customer_country IS NOT NULL THEN 1 END) as with_customer_country
FROM opportunity_d o
LEFT JOIN salesforce_account_d sa ON o.sf_account_id = sa.sf_account_id
LEFT JOIN amberflo_customer_d ac ON sa.organization_id = ac.organization_id
WHERE o.created_at_ts >= CURRENT_DATE - INTERVAL '7 days'
    AND o.created_at_ts < CURRENT_DATE
GROUP BY region
ORDER BY new_opportunities DESC;
```

### New Opportunities by Region with Owner Details

```sql
-- Find new opportunities with owner and account region information
SELECT
    COALESCE(
        sa.account_region,
        CASE 
            WHEN sa.billing_country = 'US' THEN 'North America'
            WHEN sa.billing_country IN ('CA', 'MX') THEN 'North America'
            WHEN sa.billing_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN sa.billing_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            WHEN ac.customer_country = 'US' THEN 'North America'
            WHEN ac.customer_country IN ('CA', 'MX') THEN 'North America'
            WHEN ac.customer_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN ac.customer_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            ELSE 'Unknown'
        END
    ) as region,
    CONCAT(e.first_name, ' ', e.last_name) as opportunity_owner,
    COUNT(*) as new_opportunities,
    SUM(o.amount) as total_tcv,
    AVG(o.amount) as avg_tcv,
    -- Show example opportunities
    STRING_AGG(o.opportunity_name, ', ' ORDER BY o.amount DESC LIMIT 3) as top_opportunities
FROM opportunity_d o
LEFT JOIN employee_d e ON o.owner_id = e.sf_user_id
LEFT JOIN salesforce_account_d sa ON o.sf_account_id = sa.sf_account_id
LEFT JOIN amberflo_customer_d ac ON sa.organization_id = ac.organization_id
WHERE o.created_at_ts >= CURRENT_DATE - INTERVAL '7 days'
    AND o.created_at_ts < CURRENT_DATE
GROUP BY region, opportunity_owner
ORDER BY region, total_tcv DESC;
```

### Opportunity Pipeline by Region

```sql
-- Current opportunity pipeline by region and stage
SELECT
    COALESCE(
        sa.account_region,
        CASE 
            WHEN sa.billing_country = 'US' THEN 'North America'
            WHEN sa.billing_country IN ('CA', 'MX') THEN 'North America'
            WHEN sa.billing_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN sa.billing_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            WHEN ac.customer_country = 'US' THEN 'North America'
            WHEN ac.customer_country IN ('CA', 'MX') THEN 'North America' 
            WHEN ac.customer_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN ac.customer_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            ELSE 'Unknown'
        END
    ) as region,
    o.stage_name,
    COUNT(*) as opportunity_count,
    SUM(o.amount) as total_tcv,
    SUM(o.amount * o.probability / 100) as weighted_tcv
FROM opportunity_d o
LEFT JOIN salesforce_account_d sa ON o.sf_account_id = sa.sf_account_id
LEFT JOIN amberflo_customer_d ac ON sa.organization_id = ac.organization_id
WHERE o.stage_name NOT IN ('Closed Won', 'Closed Lost')
GROUP BY region, o.stage_name
ORDER BY region, total_tcv DESC;
```

## Revenue Regional Analysis

### Monthly Revenue by Region

```sql
-- Monthly recurring revenue by region
SELECT
    date_trunc('month', be.mrr_report_date_ts) as month,
    COALESCE(
        sa.account_region,
        CASE 
            WHEN sa.billing_country = 'US' THEN 'North America'
            WHEN sa.billing_country IN ('CA', 'MX') THEN 'North America'
            WHEN sa.billing_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN sa.billing_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            WHEN ac.customer_country = 'US' THEN 'North America'
            WHEN ac.customer_country IN ('CA', 'MX') THEN 'North America'
            WHEN ac.customer_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN ac.customer_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            ELSE 'Unknown'
        END
    ) as region,
    SUM(be.amount) as total_revenue,
    COUNT(DISTINCT be.organization_id) as customer_count,
    SUM(be.amount) / COUNT(DISTINCT be.organization_id) as avg_revenue_per_customer
FROM billing_event_f be
LEFT JOIN salesforce_account_d sa ON be.organization_id = sa.organization_id
LEFT JOIN amberflo_customer_d ac ON be.organization_id = ac.organization_id
WHERE be.mrr_report_date_ts >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY month, region
ORDER BY month DESC, total_revenue DESC;
```

## Data Quality Validation

### Regional Data Completeness Check

```sql
-- Check data quality for regional classification
SELECT
    'account_region' as field_name,
    COUNT(*) as total_accounts,
    COUNT(CASE WHEN account_region IS NOT NULL AND account_region != '' THEN 1 END) as populated_count,
    ROUND(100.0 * COUNT(CASE WHEN account_region IS NOT NULL AND account_region != '' THEN 1 END) / COUNT(*), 2) as completion_percentage
FROM salesforce_account_d
WHERE sf_account_id IS NOT NULL

UNION ALL

SELECT
    'billing_country' as field_name,
    COUNT(*) as total_accounts,
    COUNT(CASE WHEN billing_country IS NOT NULL AND billing_country != '' THEN 1 END) as populated_count,
    ROUND(100.0 * COUNT(CASE WHEN billing_country IS NOT NULL AND billing_country != '' THEN 1 END) / COUNT(*), 2) as completion_percentage
FROM salesforce_account_d
WHERE sf_account_id IS NOT NULL

UNION ALL

SELECT
    'customer_country' as field_name,
    COUNT(*) as total_customers,
    COUNT(CASE WHEN customer_country IS NOT NULL AND customer_country != '' THEN 1 END) as populated_count,
    ROUND(100.0 * COUNT(CASE WHEN customer_country IS NOT NULL AND customer_country != '' THEN 1 END) / COUNT(*), 2) as completion_percentage
FROM amberflo_customer_d
WHERE aflo_customer_id IS NOT NULL;
```

### Regional Classification Examples

```sql
-- Show examples of how accounts are being classified
SELECT
    sa.sf_account_name,
    sa.account_region as primary_region,
    sa.billing_country as billing_country,
    ac.customer_country as customer_country,
    COALESCE(
        sa.account_region,
        CASE 
            WHEN sa.billing_country = 'US' THEN 'North America'
            WHEN sa.billing_country IN ('CA', 'MX') THEN 'North America'
            WHEN sa.billing_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN sa.billing_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            WHEN ac.customer_country = 'US' THEN 'North America'
            WHEN ac.customer_country IN ('CA', 'MX') THEN 'North America'
            WHEN ac.customer_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN ac.customer_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            ELSE 'Unknown'
        END
    ) as final_region,
    CASE 
        WHEN sa.account_region IS NOT NULL THEN 'account_region'
        WHEN sa.billing_country IS NOT NULL THEN 'billing_country'
        WHEN ac.customer_country IS NOT NULL THEN 'customer_country'
        ELSE 'no_data'
    END as data_source
FROM salesforce_account_d sa
LEFT JOIN amberflo_customer_d ac ON sa.organization_id = ac.organization_id
WHERE sa.sf_account_id IS NOT NULL
ORDER BY final_region, sa.sf_account_name
LIMIT 20;
```

## Common Regional Analysis Issues

### Issue: All Regions Show as "Unknown"
**Cause**: Query not using proper fallback logic or joining wrong tables
**Solution**: Use the standard regional query pattern above with COALESCE

### Issue: Employee Territory Not Available  
**Cause**: Schema doesn't include sales territory in employee_d table
**Solution**: Use account-based regional classification instead

### Issue: Inconsistent Regional Classifications
**Cause**: Different analyses using different regional logic
**Solution**: Always use the standard COALESCE pattern for consistency

## Territory Analysis via Employee-Opportunity Relationships

### Sales Performance by Employee and Region

```sql
-- Analyze sales performance by employee with regional context
SELECT
    CONCAT(e.first_name, ' ', e.last_name) as sales_rep,
    COALESCE(
        sa.account_region,
        CASE 
            WHEN sa.billing_country = 'US' THEN 'North America'
            WHEN sa.billing_country IN ('CA', 'MX') THEN 'North America'
            WHEN sa.billing_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN sa.billing_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            ELSE 'Unknown'
        END
    ) as region,
    COUNT(*) as total_opportunities,
    COUNT(CASE WHEN o.stage_name = 'Closed Won' THEN 1 END) as won_opportunities,
    SUM(o.amount) as total_pipeline_value,
    SUM(CASE WHEN o.stage_name = 'Closed Won' THEN o.amount ELSE 0 END) as won_value,
    ROUND(100.0 * COUNT(CASE WHEN o.stage_name = 'Closed Won' THEN 1 END) / COUNT(*), 2) as win_rate_percent
FROM opportunity_d o
LEFT JOIN employee_d e ON o.owner_id = e.sf_user_id
LEFT JOIN salesforce_account_d sa ON o.sf_account_id = sa.sf_account_id
WHERE o.created_at_ts >= CURRENT_DATE - INTERVAL '365 days'
    AND e.first_name IS NOT NULL -- Filter out opportunities without owner info
GROUP BY sales_rep, region
HAVING COUNT(*) >= 3 -- Only show reps with meaningful activity
ORDER BY region, won_value DESC;
```

### Regional Coverage by Sales Team

```sql
-- Show which regions each sales rep covers
SELECT
    CONCAT(e.first_name, ' ', e.last_name) as sales_rep,
    COUNT(DISTINCT COALESCE(
        sa.account_region,
        CASE 
            WHEN sa.billing_country = 'US' THEN 'North America'
            WHEN sa.billing_country IN ('CA', 'MX') THEN 'North America'
            WHEN sa.billing_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN sa.billing_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            ELSE 'Unknown'
        END
    )) as regions_covered,
    STRING_AGG(DISTINCT COALESCE(
        sa.account_region,
        CASE 
            WHEN sa.billing_country = 'US' THEN 'North America'
            WHEN sa.billing_country IN ('CA', 'MX') THEN 'North America'
            WHEN sa.billing_country IN ('GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'CH', 'SE', 'NO', 'DK') THEN 'Europe'
            WHEN sa.billing_country IN ('JP', 'KR', 'SG', 'AU', 'NZ', 'IN') THEN 'APAC'
            ELSE 'Unknown'
        END
    ), ', ') as region_list,
    COUNT(*) as total_opportunities
FROM opportunity_d o
LEFT JOIN employee_d e ON o.owner_id = e.sf_user_id
LEFT JOIN salesforce_account_d sa ON o.sf_account_id = sa.sf_account_id
WHERE o.created_at_ts >= CURRENT_DATE - INTERVAL '365 days'
    AND e.first_name IS NOT NULL
GROUP BY sales_rep
ORDER BY regions_covered DESC, total_opportunities DESC;
```

## Best Practices

1. **Always use fallback logic**: Don't rely on single regional field
2. **Show data source**: Include which field provided the regional classification
3. **Validate data quality**: Include completion percentages in analysis
4. **Consistent mapping**: Use the same country-to-region mapping across all queries
5. **Handle nulls explicitly**: Use COALESCE with 'Unknown' as final fallback
6. **Use employee-opportunity-account chain**: For territory analysis, join through opportunity ownership
7. **Filter meaningful data**: Exclude opportunities without owner information when analyzing by sales rep