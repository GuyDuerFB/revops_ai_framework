-- IXIS Data Check Queries for Firebolt Data Warehouse
-- Use these queries with the query_fire Lambda function

-- 1. Check for IXIS opportunities in opportunity_d table
SELECT 
    account_name,
    opportunity_name,
    opportunity_id,
    stage_name,
    close_date,
    amount,
    probability,
    created_date,
    owner_name
FROM opportunity_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(opportunity_name) LIKE '%IXIS%'
ORDER BY created_date DESC
LIMIT 20;

-- 2. Check for IXIS calls in gong_call_f table
SELECT 
    account_name,
    call_title,
    call_date,
    call_duration_minutes,
    host_name,
    attendees,
    opportunity_name,
    call_type,
    created_date
FROM gong_call_f 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(call_title) LIKE '%IXIS%'
   OR UPPER(attendees) LIKE '%IXIS%'
ORDER BY call_date DESC
LIMIT 20;

-- 3. Check for IXIS accounts in salesforce_account_d table
SELECT 
    account_name,
    account_id,
    account_type,
    industry,
    account_owner,
    created_date,
    last_modified_date,
    parent_account_name,
    account_status
FROM salesforce_account_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(parent_account_name) LIKE '%IXIS%'
ORDER BY last_modified_date DESC
LIMIT 20;

-- 4. Get count summary of IXIS records in each table
SELECT 
    'opportunity_d' as table_name,
    COUNT(*) as ixis_record_count
FROM opportunity_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(opportunity_name) LIKE '%IXIS%'

UNION ALL

SELECT 
    'gong_call_f' as table_name,
    COUNT(*) as ixis_record_count
FROM gong_call_f 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(call_title) LIKE '%IXIS%'
   OR UPPER(attendees) LIKE '%IXIS%'

UNION ALL

SELECT 
    'salesforce_account_d' as table_name,
    COUNT(*) as ixis_record_count
FROM salesforce_account_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(parent_account_name) LIKE '%IXIS%'

ORDER BY ixis_record_count DESC;

-- 5. Advanced search for IXIS with broader criteria
SELECT 
    'opportunity_d' as source_table,
    account_name,
    opportunity_name as name,
    stage_name as status,
    close_date as date_field,
    amount::VARCHAR as amount_or_info,
    owner_name as owner_or_host
FROM opportunity_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(opportunity_name) LIKE '%IXIS%'
   OR UPPER(owner_name) LIKE '%IXIS%'

UNION ALL

SELECT 
    'gong_call_f' as source_table,
    account_name,
    call_title as name,
    call_type as status,
    call_date as date_field,
    call_duration_minutes::VARCHAR as amount_or_info,
    host_name as owner_or_host
FROM gong_call_f 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(call_title) LIKE '%IXIS%'
   OR UPPER(host_name) LIKE '%IXIS%'
   OR UPPER(attendees) LIKE '%IXIS%'

UNION ALL

SELECT 
    'salesforce_account_d' as source_table,
    account_name,
    parent_account_name as name,
    account_type as status,
    last_modified_date as date_field,
    industry as amount_or_info,
    account_owner as owner_or_host
FROM salesforce_account_d 
WHERE UPPER(account_name) LIKE '%IXIS%' 
   OR UPPER(parent_account_name) LIKE '%IXIS%'
   OR UPPER(account_owner) LIKE '%IXIS%'

ORDER BY source_table, date_field DESC
LIMIT 50;