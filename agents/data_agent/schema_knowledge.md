# Firebolt Data Warehouse Schema Knowledge

This document contains detailed schema information for the Firebolt data warehouse. It describes tables, their relationships, and common query patterns to help the Data Agent generate accurate and efficient SQL queries.

## Core Revenue and Customer Tables

### billing_event_f
Billing events fact table with all revenue data:
- **organization_id**: Foreign key to organization_d.organization_id
- **mrr_report_date_ts**: Date when MRR was reported
- **amount**: Revenue amount in USD
- **is_fb2_usage**: Boolean indicating if this is Firebolt 2.0 usage (true) or FB 1.0 (false)
- **aflo_customer_name**: Customer name in Amberflo system
- **aws_account_id**: AWS account ID if applicable

### organization_d
Organization dimension table with all customer organizations:
- **organization_id**: Primary key - unique organization identifier
- **organization_name**: Name of the organization
- **company_name**: Legal company name
- **is_internal**: Boolean indicating if this is an internal Firebolt organization
- **is_verified**: Boolean indicating if the organization is verified
- **verified_at**: Timestamp when the organization was verified

### salesforce_account_d
Account dimension table with all Salesforce account data:
- **sf_account_id**: Primary key - Salesforce account ID
- **sf_x18_digit_id**: 18-digit Salesforce ID
- **sf_account_name**: Name of the account
- **organization_id**: Foreign key to organization_d.organization_id
- **sf_account_type_custom**: Custom account type (e.g., 'PLG Customer', 'Commit Customer')
- **account_region**: Geographic region of the account
- **sf_industry**: Industry of the account
- **sf_sub_industry**: Sub-industry categorization
- **sf_owner_id**: Foreign key to employee_d.sf_user_id
- **sf_open_opportunities**: Count of open opportunities
- **billing_country**: Country for billing
- **potential_account_spend_usd**: Potential spending in USD
- **sf_company_domain**: Company's domain name
- **created_at_ts**: Timestamp when account was created

### firebolt_account_d
Firebolt account dimension table:
- **account_id**: Primary key - unique account identifier
- **account_name**: Name of the Firebolt account
- **is_deleted**: Boolean indicating if the account is deleted

### firebolt_fb1_account_d
Firebolt 1.0 account dimension table:
- **account_name**: Name of the Firebolt 1.0 account
- **sf_account_id**: Foreign key to salesforce_account_d.sf_account_id

## Opportunities and Agreements

### opportunity_d
Opportunity dimension table with all Salesforce opportunity data:
- **opportunity_id**: Primary key - Salesforce opportunity ID
- **opportunity_name**: Name of the opportunity
- **opportunity_type**: Type of opportunity (e.g., 'New Business', 'Upsell')
- **sf_account_id**: Foreign key to salesforce_account_d.sf_account_id
- **stage_name**: Current stage of opportunity (e.g., 'Closed Won', 'Closed Lost')
- **amount**: Opportunity amount in USD
- **contract_duration_months**: Duration of contract in months
- **probability**: Probability of closing (percentage)
- **close_date**: Expected or actual close date
- **created_at_ts**: Timestamp when opportunity was created
- **closed_at_date**: Date when opportunity was closed
- **closed_won_lost_reason**: Reason for winning or losing the opportunity
- **owner_id**: Foreign key to employee_d.sf_user_id
- **campaign_id**: Foreign key to campaign_d.campaign_id
- **contact_id**: Foreign key to contact_d.contact_id

### agreement_f
Agreements fact table with contract details:
- **sf_account_id**: Foreign key to salesforce_account_d.sf_account_id
- **amount**: Total contract value in USD
- **contract_term_months**: Duration of contract in months
- **is_active**: Boolean indicating if the agreement is active
- **agreement_status**: Status of the agreement (e.g., 'Active', 'Expired')
- **description**: Description of the agreement

## Consumption and Usage Metrics

### consumption_daily_d
Daily consumption metrics for accounts:
- **consumption_date**: Date of consumption
- **sf_account_id**: Foreign key to salesforce_account_d.sf_account_id
- **engine_hours**: Hours of engine usage
- **query_count**: Number of queries executed
- **data_scanned_bytes**: Amount of data scanned in bytes

### consumption_event_f
Detailed consumption events fact table:
- **activity_date**: Date of the activity
- **engine_id**: Foreign key to engine_d.engine_id
- **account_id**: Foreign key to firebolt_account_d.account_id
- **organization_id**: Foreign key to organization_d.organization_id
- **organization_name**: Name of the organization
- **account_name**: Name of the account
- **fbu_per_hour**: Firebolt Units per hour used
- **instance_count**: Number of instances
- **price_per_fbu_usd**: Price per Firebolt Unit in USD
- **total_cost_post_discount_usd**: Total cost after discount in USD
- **start_event_id**: ID of the start event
- **end_event_id**: ID of the end event

### engine_d
Engine dimension table:
- **engine_id**: Primary key - unique engine identifier
- **engine_name**: Name of the engine
- **engine_region**: Region where the engine is deployed
- **date_effective_ts**: Timestamp when the engine became effective
- **cluster_count**: Number of clusters in the engine
- **is_current**: Boolean indicating if this is the current engine version

### engine_event_f
Engine events fact table:
- **start_event_id**: ID of the start event
- **end_event_id**: ID of the end event
- **triggered_by_user_id**: Foreign key to user_d.user_id
- **account_id**: Foreign key to firebolt_account_d.account_id

## Billing and Pricing

### customer_invoice_line_f
Customer invoice line items fact table:
- **organization_id**: Foreign key to organization_d.organization_id
- **invoice_started_at**: Start date of the invoice period
- **product_item_name**: Name of the product item (e.g., 'Storage', 'Compute')
- **account_name**: Name of the account
- **engine_name**: Name of the engine if applicable
- **total_amount**: Total amount in USD
- **aflo_customer_name**: Customer name in Amberflo system

### customer_discount_f
Customer discounts fact table:
- **organization_id**: Foreign key to organization_d.organization_id
- **valid_from**: Start date of discount validity
- **valid_to**: End date of discount validity
- **discount_amount**: Discount amount as a decimal (e.g., 0.2 for 20%)

## Marketing and Users

### campaign_d
Marketing campaign dimension table:
- **campaign_id**: Primary key - unique campaign identifier
- **campaign_name**: Name of the campaign

### contact_d
Contact dimension table:
- **contact_id**: Primary key - unique contact identifier
- **contact_name**: Name of the contact
- **contact_email**: Email of the contact
- **job_title**: Job title of the contact

### employee_d
Employee dimension table:
- **sf_user_id**: Primary key - Salesforce user ID
- **first_name**: First name of the employee
- **last_name**: Last name of the employee
- **user_email**: Email of the employee

### user_d
User dimension table:
- **user_id**: Primary key - unique user identifier
- **account_id**: Foreign key to firebolt_account_d.account_id
- **login_id**: Foreign key to login_d.login_id

### login_d
Login dimension table:
- **login_id**: Primary key - unique login identifier
- **login_name**: Login name/username

## Geographic and Miscellaneous

### countries_by_region
Countries and regions mapping table:
- **country_code**: Country code (e.g., 'US')
- **country_name**: Full country name

### aws_account_d
AWS account dimension table:
- **aws_account_id**: Primary key - AWS account ID
- **country**: Country associated with the AWS account

### salesforce_account_forecast_pivot_d
Account forecast dimension table:
- **account_id**: Foreign key to salesforce_account_d.sf_account_id
- **forecast_date**: Date of the forecast
- **forecast_id**: Unique forecast identifier
- **forecast_name**: Name of the forecast
- **amount**: Forecasted amount in USD

## Common Joins and Query Patterns

### Core Entity Relationships
- Join opportunities to Salesforce accounts: `opportunity_d.sf_account_id = salesforce_account_d.sf_account_id`
- Join consumption metrics to Salesforce accounts: `consumption_daily_d.sf_account_id = salesforce_account_d.sf_account_id`
- Join organizations to Salesforce accounts: `organization_d.organization_id = salesforce_account_d.organization_id`
- Join Firebolt accounts to consumption events: `firebolt_account_d.account_id = consumption_event_f.account_id`
- Join billing events to organizations: `billing_event_f.organization_id = organization_d.organization_id`
- Join agreements to Salesforce accounts: `agreement_f.sf_account_id = salesforce_account_d.sf_account_id`

### User and Employee Relationships
- Join account owners to Salesforce accounts: `employee_d.sf_user_id = salesforce_account_d.sf_owner_id`
- Join opportunity owners to opportunities: `employee_d.sf_user_id = opportunity_d.owner_id`
- Join users to engines: `user_d.user_id = engine_event_f.triggered_by_user_id`
- Join login information to users: `login_d.login_id = user_d.login_id`

### Revenue and Billing Relationships
- Join discounts to invoices: `customer_discount_f.organization_id = customer_invoice_line_f.organization_id AND invoice_started_at BETWEEN valid_from AND valid_to`
- Join invoices to Salesforce accounts: `customer_invoice_line_f.organization_id = salesforce_account_d.organization_id`

### Special Joins for FB 1.0 and FB 2.0
- Join FB 1.0 accounts to Salesforce accounts: `firebolt_fb1_account_d.sf_account_id = salesforce_account_d.sf_account_id`
- Bridge FB 1.0 and FB 2.0 data: `billing_event_f.aflo_customer_name = firebolt_fb1_account_d.account_name`

## Common Query Patterns

### Monthly Revenue Analysis
```sql
SELECT 
    date_trunc('month', CAST(mrr_report_date_ts AS TIMESTAMP)) AS month,
    CASE WHEN is_fb2_usage = true THEN 'FB 2.0' ELSE 'FB 1.0' END AS source,
    SUM(amount) AS mrr
FROM billing_event_f
WHERE mrr_report_date_ts BETWEEN [start_date] AND [end_date]
GROUP BY 1, 2
ORDER BY 1, 2
```

### Engine Cost Analysis
```sql
SELECT
    date_trunc('day', CAST(activity_date AS TIMESTAMP)) AS day,
    engine_name,
    SUM(total_cost_post_discount_usd) AS cost_after_discount
FROM consumption_event_f
JOIN engine_d ON engine_d.engine_id = consumption_event_f.engine_id
WHERE activity_date BETWEEN [start_date] AND [end_date]
GROUP BY 1, 2
ORDER BY 3 DESC
```

### Storage vs Compute Cost Breakdown
```sql
SELECT
    date_trunc('month', CAST(invoice_started_at AS TIMESTAMP)) AS month,
    CASE
        WHEN product_item_name ILIKE 'storage%' THEN 'Storage'
        ELSE 'Compute'
    END AS component,
    SUM(total_amount::float * (1 - COALESCE(discount_amount, 0))) AS net_total
FROM customer_invoice_line_f
LEFT JOIN customer_discount_f ON customer_invoice_line_f.organization_id = customer_discount_f.organization_id
    AND invoice_started_at BETWEEN valid_from AND valid_to
WHERE invoice_started_at BETWEEN [start_date] AND [end_date]
GROUP BY 1, 2
```

### Opportunity Analysis
```sql
SELECT
    salesforce_account_d.sf_account_name,
    opportunity_d.opportunity_name,
    opportunity_d.stage_name,
    opportunity_d.amount AS tcv,
    opportunity_d.amount/opportunity_d.contract_duration_months*12 AS acv
FROM opportunity_d
JOIN salesforce_account_d ON opportunity_d.sf_account_id = salesforce_account_d.sf_account_id
WHERE opportunity_d.stage_name NOT IN ('Closed Lost')
    AND [additional_filters]
ORDER BY opportunity_d.amount DESC
```

## Business Metrics

### Revenue Metrics

#### Monthly Recurring Revenue (MRR)
- **Definition**: Monthly revenue recognized from customers
- **Primary Table**: `billing_event_f`
- **Key Columns**: `mrr_report_date_ts`, `amount`, `is_fb2_usage`
- **Common Segmentation**: FB 1.0 vs FB 2.0, account type, region
- **Example Query Pattern**: Group by month, source (FB 1.0/2.0), sum amount

#### Annual Contract Value (ACV)
- **Definition**: Annualized value of a contract (amount / contract_duration_months * 12)
- **Primary Table**: `opportunity_d` or `agreement_f`
- **Key Columns**: `amount`, `contract_duration_months` or `contract_term_months`
- **Example Query Pattern**: Calculate ACV from TCV and contract duration

#### Total Contract Value (TCV)
- **Definition**: Total value of a contract over its full duration
- **Primary Table**: `opportunity_d` or `agreement_f`
- **Key Columns**: `amount`
- **Example Query Pattern**: Sum amount by account, opportunity type, etc.

### Usage and Consumption Metrics

#### Engine Usage Cost
- **Definition**: Cost of compute engine usage after discounts
- **Primary Table**: `consumption_event_f`
- **Key Columns**: `activity_date`, `engine_name`, `total_cost_post_discount_usd`
- **Common Segmentation**: By engine, by day/month, by account
- **Example Query Pattern**: Sum cost by day and engine

#### Storage vs. Compute Split
- **Definition**: Breakdown of costs between storage and compute resources
- **Primary Table**: `customer_invoice_line_f`
- **Key Columns**: `invoice_started_at`, `product_item_name`, `total_amount`
- **Common Segmentation**: Month, product type
- **Example Query Pattern**: Classify items as storage/compute, then sum costs

### Sales and Opportunity Metrics

#### Pipeline Analysis
- **Definition**: Analysis of sales opportunities by stage
- **Primary Table**: `opportunity_d`
- **Key Columns**: `stage_name`, `amount`, `probability`, `close_date`
- **Common Segmentation**: Stage, account type, region
- **Example Query Pattern**: Group opportunities by stage, sum amounts

#### Closed Won/Lost Analysis
- **Definition**: Analysis of opportunities that have closed
- **Primary Table**: `opportunity_d`
- **Key Columns**: `stage_name`, `closed_at_date`, `closed_won_lost_reason`
- **Common Segmentation**: Won/lost reason, account tier, industry
- **Example Query Pattern**: Filter on "Closed Won" or "Closed Lost", group by reason

## Analysis Types

### A1: At-risk Account Identification
- **Description**: Identify accounts showing signs of churn risk
- **Key Tables**: `consumption_daily_d`, `opportunity_d`
- **Risk Indicators**: >20% decline in usage over 3 consecutive months, delayed renewals
- **Example Query**: Find accounts with declining usage trends or stalled opportunities

### A2: Closed-lost Opportunity Pattern Analysis
- **Description**: Identify patterns in lost opportunities
- **Key Tables**: `opportunity_d`
- **Pattern Indicators**: Common closed-lost reasons, competitive losses
- **Example Query**: Group closed-lost by reason and identify top reasons by account type

### A3: Upsell Opportunity Detection
- **Description**: Identify accounts ready for upsell
- **Key Tables**: `consumption_daily_d`, `salesforce_account_d`
- **Upsell Indicators**: High utilization of current resources, consistent growth
- **Example Query**: Find accounts using >80% of current resources consistently

### A4: Customer Health Monitoring
- **Description**: Monitor overall customer health
- **Key Tables**: All usage and opportunity tables
- **Health Indicators**: Usage trends, open opportunities, engagement
- **Example Query**: Create a health score based on multiple usage and sales metrics

### A5: Usage Pattern Anomaly Detection
- **Description**: Detect unusual patterns in product usage
- **Key Tables**: `consumption_event_f`, `consumption_daily_d`
- **Anomaly Indicators**: Sudden spikes or drops in usage
- **Example Query**: Detect deviations from historical usage patterns

### A6: Competitive Intelligence Gathering
- **Description**: Gather intelligence on competitors
- **Key Tables**: `opportunity_d`
- **Intelligence Sources**: Competitor mentions in closed-lost reasons
- **Example Query**: Extract and analyze competitor mentions in opportunity data
