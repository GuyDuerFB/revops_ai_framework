This file contains the Firebolt schema for the data agent to understand tables/queries.

# Firebolt Data Warehouse Schema Knowledge

This document contains detailed schema information for the Firebolt data warehouse. It describes tables, their relationships, and common query patterns to help the Data Agent generate accurate and efficient SQL queries.

## Core Revenue and Customer Tables

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

### billing_event_f
Billing events fact table with all revenue data:
- **organization_id**: Foreign key to organization_d.organization_id
- **mrr_report_date_ts**: Date when MRR was reported
- **amount**: Revenue amount in USD
- **is_fb2_usage**: Boolean indicating if this is Firebolt 2.0 usage (true) or FB 1.0 (false)
- **aflo_customer_name**: Customer name in Amberflo system
- **aws_account_id**: AWS account ID if applicable

### amberflo_customer_d
Customer details from Amberflo:
- **aflo_customer_id**: Unique identifier for the Amberflo customer
- **aflo_customer_name**: Name of the Amberflo customer
- **organization_id**: Unique identifier for the organization
- **payment_method_id**: Identifier for the customer's payment method
- **life_cycle_stage**: The lifecycle stage of the customer
- **payment_provider_name**: Name of the payment provider
- **is_private_offer**: Boolean indicating if customer is on a private offer
- **is_test**: Boolean indicating if this is a test customer
- **is_enabled**: Boolean indicating if the customer is currently enabled
- **aws_customer_id**: AWS customer identifier
- **customer_country**: Customer's country
- **customer_city**: Customer's city
- **customer_state**: Customer's state

### organization_d
Organization dimension table with all customer organizations:
- **organization_id**: Primary key - unique organization identifier
- **organization_name**: Name of the organization
- **company_name**: Legal company name
- **is_internal**: Boolean indicating if this is an internal Firebolt organization
- **is_verified**: Boolean indicating if the organization is verified
- **verified_at**: Timestamp when the organization was verified

### firebolt_account_d
Firebolt account dimension table:
- **account_id**: Primary key - unique account identifier
- **account_name**: Name of the Firebolt account
- **is_deleted**: Boolean indicating if the account is deleted

### firebolt_fb1_account_d
Firebolt 1.0 account dimension table:
- **account_name**: Name of the Firebolt 1.0 account
- **sf_account_id**: Foreign key to salesforce_account_d.sf_account_id

## Sales Calls and Engagement

### gong_call_f
Gong sales calls fact table with comprehensive call data and AI-generated summaries:
- **sf_gong_call_id**: Primary key - Salesforce Gong call ID
- **gong_call_id**: Gong's internal call ID - use for Gong API transcript when detailed accuracy is needed
- **gong_call_name**: Name/title of the call
- **gong_title**: Call title from Gong
- **sf_owner_id**: Foreign key to employee_d.sf_user_id (call owner)
- **is_deleted**: Boolean indicating if the call record is deleted
- **created_by_id**: Salesforce user ID who created the record
- **created_date_ts**: Timestamp when the call record was created
- **last_modified_date_ts**: Timestamp when the call record was last modified
- **gong_call_start_ts**: Timestamp when the call started
- **gong_call_end_ts**: Timestamp when the call ended
- **gong_scheduled_ts**: Timestamp when the call was scheduled
- **gong_call_duration**: Duration of the call (string format)
- **gong_direction**: Direction of the call (Conference, Outbound, Inbound, Unknown)
- **gong_media**: Media type of the call (Video, Audio)
- **gong_system**: System used for the call (Google Meet, Zoom, Microsoft Teams, Outreach, etc.)
- **gong_language**: Language of the call
- **gong_quality_score**: Quality score assigned by Gong
- **gong_recorded_from**: Source of the recording
- **gong_scope**: Scope/context of the call
- **gong_primary_user**: Primary user from Gong's perspective
- **gong_talk_time_them**: Talk time of external participants
- **gong_playbook_match**: Playbook matches identified by Gong
- **gong_participants_emails**: Comma-separated list of participant email addresses
- **gong_primary_account**: Foreign key to salesforce_account_d.sf_account_id (primary account)
- **gong_related_account**: Related Salesforce account ID
- **gong_related_lead**: Related Salesforce lead ID
- **gong_related_contact**: Related Salesforce contact ID
- **gong_related_opportunity**: Foreign key to opportunity_d.opportunity_id
- **gong_primary_opportunity**: Primary opportunity ID associated with the call
- **gong_opportunity_stage_now**: Current stage of the related opportunity
- **gong_opp_stage_time_of_call**: Opportunity stage at the time of the call
- **gong_opp_amount_time_of_call**: Opportunity amount at the time of the call (USD)
- **gong_opp_close_date_time_of_call**: Opportunity close date at the time of the call
- **gong_opp_probability_time_of_call**: Opportunity probability at the time of the call (percentage)
- **gong_call_brief**: AI-generated brief summary of the call content - overall summary - fastest to process
- **gong_call_key_points**: AI-generated key points and takeaways from the call - main issues and topics discussed
- **gong__call_highlights_next_steps**: Next steps agreed during the call - action items and follow-up tasks
- **gong_related_participants_json**: JSON structure containing detailed participant information
- **source_file_name**: Source file name for data lineage
- **source_file_timestamp**: Timestamp of the source file
- **dbt_last_updated_ts**: Timestamp when the record was last updated by dbt

### gong_call_f Usage Priority
**For efficiency and speed, prioritize these fields in order:**
1. **gong_call_brief** - Use for quick call summaries
2. **gong_call_key_points** - Use for main topics and issues
3. **gong__call_highlights_next_steps** - Use for action items
4. **gong_call_id** - Use only when detailed transcript is needed from Gong API

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

## Contacts, Leads, and People

### contact_d
Contact dimension table with customer contact information:
- **contact_id**: Primary key - unique contact identifier
- **contact_name**: Full name of the contact
- **contact_email**: Email address of the contact
- **contact_phone**: Phone number of the contact
- **contact_title**: Job title of the contact
- **sf_account_id**: Foreign key to salesforce_account_d.sf_account_id
- **is_deleted**: Boolean indicating if the contact is deleted
- **created_date_ts**: Timestamp when the contact was created
- **last_modified_date_ts**: Timestamp when the contact was last modified

### lead_d
Lead dimension table with prospect lead information:
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

## Opportunities and Agreements

### opportunity_d
Opportunity dimension table with all Salesforce opportunity data:
- **opportunity_id**: Primary key - Salesforce opportunity ID
- **opportunity_name**: Name of the opportunity
- **opportunity_type**: Type of opportunity (e.g., 'New Business', 'Upsell')
- **sf_account_id**: Foreign key to salesforce_account_d.sf_account_id
- **stage_name**: Current stage of opportunity (e.g., 'Closed Won', 'Closed Lost')
- **amount**: TCV amount in USD
- **contract_duration_months**: Duration of contract in months
- **probability**: Probability of closing (percentage)
- **close_date**: Expected or actual close date
- **created_at_ts**: Timestamp when opportunity was created
- **closed_at_date**: Date when opportunity was closed
- **closed_won_lost_reason**: Reason for winning or losing the opportunity
- **owner_id**: Foreign key to employee_d.sf_user_id
- **campaign_id**: Foreign key to campaign_d.campaign_id
- **contact_id**: Foreign key to contact_d.contact_id
##### MEDDPICC Fields in opportunity_d
- **metrics**: Quantifiable business metrics/outcomes the prospect wants to achieve
- **metrics_status**: Status of metrics qualification (e.g., 'Identified', 'Validated', 'Not Defined')
- **economic_buyer**: The person with budget authority and final decision-making power
- **economic_buyer_status**: Status of economic buyer identification (e.g., 'Identified', 'Engaged', 'Unknown')
- **identify_pain**: The specific business pain or problem the solution addresses
- **identify_pain_status**: Status of pain identification (e.g., 'Identified', 'Validated', 'Unclear')
- **champion**: Internal advocate who supports the solution and influences the buying process
- **champion_status**: Status of champion relationship (e.g., 'Identified', 'Engaged', 'Strong', 'Weak')
- **decision_criteria**: The specific criteria the prospect will use to make their decision
- **decision_criteria_status**: Status of decision criteria understanding (e.g., 'Known', 'Partial', 'Unknown')
- **competition**: Information about competing solutions or vendors
- **competition_status**: Status of competitive landscape understanding (e.g., 'Known', 'Researched', 'Unknown')
- **competitors**: Specific competing vendors or solutions identified
- **decision_making_process**: The formal process the prospect follows to make purchasing decisions
- **decision_making_process_status**: Status of process understanding (e.g., 'Mapped', 'Partial', 'Unknown')
- **decision_timeline_date**: Expected date for final decision
- **paper_process**: The legal, procurement, and contracting process required
- **paper_process_status**: Status of paper process understanding (e.g., 'Mapped', 'In Progress', 'Unknown')

### opportunity_stage_f

Fact table capturing each transition of a Salesforce opportunity from one stage to the next. One record represents the time the opportunity **left** the `from_stage` and entered the `to_stage`.

- **opportunity_stage_id**: Surrogate primary key for this fact record.
- **opportunity_id**: Foreign key to `opportunity_d.opportunity_id`.
- **owner_id**: Foreign key to `employee_d.sf_user_id` of the opportunity owner at the time of the transition.
- **created_by_id**: Foreign key to `employee_d.sf_user_id` of the user who created the stage change record.
- **from_stage**: Stage that the opportunity was *in* before the transition.
- **to_stage**: Stage that the opportunity was moved *to*.
- **days_in_stage**: Number of days the opportunity spent in `from_stage` (inclusive).
- **started_at_ts**: Timestamp when the opportunity **entered** `from_stage`.
- **ended_at_ts**: Timestamp when the opportunity **left** `from_stage` and entered `to_stage`.
- **is_first_stage**: `TRUE` if `from_stage` is the first lifecycle stage (initial creation of the opportunity).
- **is_last_stage**: `TRUE` if `to_stage` is a terminal stage (e.g., *Closed Won* or *Closed Lost*).
- **is_active_stage**: `TRUE` if this row represents the **current** stage of the opportunity (i.e., it has not yet moved to a later stage).
- **is_deleted**: Flag indicating that the record was deleted in the source system.
- **system_modified_at_ts**: Timestamp captured from Salesforce *SystemModstamp* (last system modification).
- **dbt_last_updated_ts**: Timestamp when dbt last updated this record.

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

### daily_customer_cost_f
Daily cost details per customer:
- **customer_id**: Unique identifier for the customer
- **organization_id**: Unique identifier for the organization
- **aflo_customer_name**: Name of the Amberflo customer
- **aws_customer_id**: AWS customer identifier
- **start_time**: Start timestamp for the usage period
- **end_time**: End timestamp for the usage period
- **cost_before_discount**: Total cost before any discounts ($)
- **cost_after_discount**: Total cost after discounts ($)
- **prepaid_used**: Portion of cost covered by prepaid credits
- **consumed_fbu**: FBU consumption for FB2 customers
- **consumed_gib**: Storage consumption for FB2 customers
- **consumed_engine_hours**: Engine hours consumption for FB1 customers
- **consumed_bytes**: Storage consumption for FB1 customers
- **engine_v2_cost_before_discount**: Engine costs before discount for FB2 ($)
- **engine_v2_cost_after_discount**: Engine costs after discount for FB2 ($)
- **storage_v2_cost**: Storage costs for FB2 customers ($)
- **engine_v1_cost_before_discount**: Engine costs before discount for FB1 ($)
- **engine_v1_cost_after_discount**: Engine costs after discount for FB1 ($)
- **storage_v1_cost**: Storage costs for FB1 customers ($)

### customer_billing_f
Engine and storage billing details:
- **organization_id**: Unique identifier for the organization
- **account_id**: Unique identifier for the account
- **usage_date**: Date for which the billing data is recorded
- **consumed_fbu**: Total consumed Firebolt Usage Units (FBU)
- **credit_consumed_fbu**: Consumed FBU covered by credits
- **billed_engine_cost**: Total billed cost for engine usage
- **credit_billed_engine_cost**: Billed engine cost covered by credits
- **consumed_gib_per_month**: Total consumed storage in GiB per month
- **credit_consumed_gib_per_month**: Storage consumption covered by credits
- **billed_storage_cost**: Total billed cost for storage usage
- **credit_billed_storage_cost**: Billed storage cost covered by credits

### engine_billing_f
Engine billing details:
- **billing_id**: Unique identifier for the billing record
- **organization_id**: Unique identifier for the organization
- **account_id**: Unique identifier for the Firebolt account
- **engine_id**: Unique identifier for the Firebolt engine
- **account_name**: Name of the Firebolt account
- **organization_name**: Name of the organization
- **engine_name**: Name of the Firebolt engine
- **usage_date**: Date when the billing usage was recorded
- **consumed_fbu**: Total Firebolt Units (FBU) consumed
- **credit_consumed_fbu**: FBU consumed using credits
- **billed_engine_cost**: Total cost billed for engine usage
- **credit_billed_engine_cost**: Cost covered by credits for engine usage

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
- **customer_id**: Unique identifier for the customer
- **invoice_uri**: URI reference for the invoice
- **invoice_id**: Unique identifier for the invoice
- **account_id**: Identifier for the account associated with the invoice line
- **region_name**: Region associated with the invoice line item
- **product_plan_id**: Identifier for the product plan
- **plan_name**: Name of the product plan
- **product_item_id**: Identifier for the product item
- **meter_api_name**: API name of the meter
- **quantity**: Quantity of units billed for this invoice line

### customer_invoice_f
High-level invoice data per customer:
- **invoice_uri**: URI reference for the invoice
- **invoice_id**: Unique identifier for the invoice
- **customer_id**: Unique identifier for the customer
- **aflo_customer_name**: Name of the Amberflo customer
- **organization_id**: Unique identifier for the organization
- **product_plan_id**: Identifier for the product plan
- **plan_name**: Name of the product plan
- **invoice_started_at**: Timestamp when the invoice period started
- **invoice_ended_at**: Timestamp when the invoice period ended
- **total_prepaid**: Total amount covered by prepaid credits
- **total_discount**: Total discount amount applied
- **total_amount_before_discount**: Invoice amount before applying discounts
- **total_amount_before_prepaid**: Invoice amount before applying prepaid credits
- **total_amount**: Final invoice amount after all discounts and prepaid credits

### customer_discount_f
Customer discounts fact table:
- **organization_id**: Foreign key to organization_d.organization_id
- **valid_from**: Start date of discount validity (as valid_from)
- **valid_to**: End date of discount validity
- **discount_amount**: Discount amount as a decimal (e.g., 0.2 for 20%)
- **aflo_promotion_id**: Unique identifier for the Amberflo promotion
- **promotion_id**: Identifier for the promotion applied
- **product_id**: Identifier for the product associated with the promotion
- **customer_id**: Unique identifier for the customer receiving the discount
- **payment_method_id**: Identifier for the payment method used
- **aflo_customer_name**: Name of the customer
- **promotion_name**: Name of the promotion
- **promotion_type**: Type of promotion applied

### pricing_plan_d
Dimension table containing pricing plan details:
- **product_plan_id**: Unique identifier for the product plan
- **product_plan_name**: Name of the product plan
- **product_item_id**: Identifier for the product item associated with the plan
- **product_item_price_id**: Identifier for the product item price
- **is_default**: Boolean indicating if this is the default pricing plan
- **product_plan_type**: Type of the product plan
- **customer_region**: Extracted customer region from the pricing data
- **price_per_fbu_usd**: Price per functional billing unit (FBU) in USD

### customer_pricing_plan_f
Customer pricing plan details:
- **organization_id**: Unique identifier for the organization
- **customer_id**: Unique identifier for the customer
- **product_plan_id**: Identifier for the product plan
- **product_plan_name**: Name of the product plan
- **started_at**: Timestamp when the customer pricing plan started
- **ended_at**: Timestamp when the customer pricing plan ended

### account_pricing_history_f
Historical pricing details per account and region:
- **organization_id**: Unique identifier for the organization
- **organization_name**: Name of the organization
- **account_id**: Unique identifier for the account
- **account_name**: Name of the account
- **customer_id**: Unique identifier for the customer
- **product_plan_id**: Identifier for the product plan
- **product_plan_name**: Name of the product plan
- **started_at**: Timestamp when the pricing plan started
- **ended_at**: Timestamp when the pricing plan ended
- **price_per_fbu_usd**: Price per FBU in USD
- **account_region**: Region associated with the account
- **sf_account_id**: Salesforce account ID linked to the account
- **is_internal**: Boolean indicating if the account is internal

### customer_credit_f
Prepaid information extracted from Amberflo:
- **customer_id**: Unique identifier for the customer
- **prepaid_id**: Extracted prepaid ID from prepaid_uri
- **label**: Label describing the prepaid transaction
- **prepaid_amount**: Total amount allocated for the prepaid card
- **used_amount**: Amount already utilized from the prepaid card
- **amount_left**: Remaining balance in the prepaid card
- **started_at**: Start timestamp of the prepaid transaction
- **expired_at**: Expiration timestamp of the prepaid transaction
- **payment_status**: Status of the payment for the prepaid transaction

### prepaid_credit_f
Detailed prepaid credit information:
- **customer_id**: Unique identifier for the customer
- **prepaid_id**: Extracted prepaid ID from prepaid_uri
- **label**: Label describing the prepaid transaction
- **prepaid_price**: Total amount of prepaid
- **organization_id**: Unique identifier for the organization
- **customer_priority**: Customer prepaid priority
- **prepaid_priority**: Prepaid priority description
- **started_at**: Start timestamp of the prepaid transaction
- **ended_at**: End timestamp of the prepaid transaction
- **payment_status**: Status of the payment for the prepaid transaction

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
- **NOTE**: No sales territory or regional assignment fields available

### user_d
User dimension table:
- **user_id**: Primary key - unique user identifier
- **account_id**: Foreign key to firebolt_account_d.account_id
- **login_id**: Foreign key to login_d.login_id

### login_d
Login dimension table:
- **login_id**: Primary key - unique login identifier
- **login_name**: Login name/username

## AWS Billing

### daily_aws_billing_event_f
Daily AWS billing event data:
- **aflo_customer_id**: Unique identifier for the Aflo customer
- **aflo_customer_name**: Name of the Aflo customer
- **organization_id**: Identifier for the organization
- **customer_aws_account_id**: AWS account ID for the customer
- **payer_aws_account_id**: AWS account ID for the payer
- **mrr_report_date**: The reporting date used for MRR calculation
- **amount**: Billed amount for the usage
- **is_fb2_usage**: Indicates whether the usage is related to FB2
- **aws_product_code**: Code representing the AWS product used
- **usage_hours**: Number of hours the resource was used
- **usage_unit_type**: Unit type for the usage (e.g., Hours, GB)
- **currency**: Currency of the billed amount
- **aws_instance_type**: AWS instance type used (e.g., t3.medium)
- **usage_period_start_date**: Start date of the usage period
- **usage_period_end_date**: End date of the usage period

### monthly_aws_billing_event_f
Aggregated monthly AWS billing event data:
- **billing_event_id**: Unique identifier for the billing event
- **invoice_id**: Identifier of the AWS invoice
- **action**: Action type for the billing event (e.g., usage, refund)
- **transaction_type**: Type of transaction recorded
- **product_id**: Internal product ID
- **product_code**: Code representing the product
- **is_private_offer**: Boolean flag indicating if the charge is part of a private offer
- **billing_amount**: Total billing amount for the event
- **mrr_report_date_ts**: Timestamp representing the reporting date for MRR
- **aws_account_id**: AWS account ID associated with the billing
- **aws_customer_id**: Customer ID provided by AWS
- **aflo_customer_id**: Unique identifier for the Aflo customer
- **aflo_customer_name**: Name of the Aflo customer
- **organization_id**: Identifier for the organization

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
- Join Gong calls to accounts: `gong_call_f.gong_primary_account = salesforce_account_d.sf_account_id`
- Join Gong calls to opportunities: `gong_call_f.gong_related_opportunity = opportunity_d.opportunity_id`
- Join Opportunity stages to Opportunity to get Opportunity information: `opportunity_stage_f.opportunity_id = opportunity_d.opportunity_id`

### FB1/FB2 Bridge Relationships
- FB1 to Salesforce bridge: `firebolt_fb1_account_d.sf_account_id = salesforce_account_d.sf_account_id`
- Billing events to FB1 accounts: `billing_event_f.aflo_customer_name = firebolt_fb1_account_d.account_name`
- Billing events to FB2 accounts: `billing_event_f.organization_id = salesforce_account_d.organization_id`
- Amberflo customer connection: `billing_event_f.aflo_customer_id = amberflo_customer_d.aflo_customer_id`
- FB2 consumption to accounts: `firebolt_account_d.account_id = consumption_event_f.account_id`
- Join FB 1.0 accounts to Salesforce accounts: `firebolt_fb1_account_d.sf_account_id = salesforce_account_d.sf_account_id`

### User and Employee Relationships
- Join account owners to Salesforce accounts: `employee_d.sf_user_id = salesforce_account_d.sf_owner_id`
- Join opportunity owners to opportunities: `employee_d.sf_user_id = opportunity_d.owner_id`
- Join users to engines: `user_d.user_id = engine_event_f.triggered_by_user_id`
- Join login information to users: `login_d.login_id = user_d.login_id`
- Join Gong call owners to employees: `employee_d.sf_user_id = gong_call_f.sf_owner_id`

### Revenue and Billing Relationships
- Join discounts to invoices: `customer_discount_f.organization_id = customer_invoice_line_f.organization_id AND invoice_started_at BETWEEN valid_from AND valid_to`
- Join invoices to Salesforce accounts: `customer_invoice_line_f.organization_id = salesforce_account_d.organization_id`

### Call and Opportunity Analysis Relationship

### gong_call_f Table Joins
**IMPORTANT**: Use these joins to get comprehensive call information:

- Join call with account information: `salesforce_account_d.sf_account_id = gong_call_f.gong_related_account`
- Join call with contact information: `contact_d.contact_id = gong_call_f.gong_related_contact`
- Join call with opportunity information:
`opportunity_d.opportunity_id = gong_call_f.gong_related_opportunity`
--Join call with lead information:
    `lead_d.lead_id = gong_call_f.gong_related_lead`

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

### Monthly Revenue by Account, Region and Owner
```sql
SELECT
    COALESCE(salesforce_account_d.sf_account_id,sf_acc.sf_account_id) as "salesforce_account_d.sf_account_id",
    COALESCE(salesforce_account_d.sf_account_type_custom,sf_acc.sf_account_type_custom) AS "salesforce_account_d.sf_account_type_custom",
    COALESCE(salesforce_account_d.sf_account_type_custom,sf_acc.sf_account_type_custom) AS sf_account_type_custom,
    COALESCE(salesforce_account_d.sf_account_name, sf_acc.sf_account_name) AS sf_account_name,
    COALESCE(salesforce_account_d.sf_open_opportunities, sf_acc.sf_open_opportunities) AS sf_open_opportunities,
    COALESCE(salesforce_account_d.sf_account_name, sf_acc.sf_account_name) AS "salesforce_account_d.sf_account_name",
    COALESCE(salesforce_account_d.account_region, sf_acc.account_region) AS "salesforce_account_d.account_region",
    COALESCE(sf_owner_1.first_name  || ' ' || sf_owner_1.last_name, sf_owner_2.first_name  || ' ' || sf_owner_2.last_name) AS sf_account_owner_name,
  	date_trunc('month', mrr_report_date_ts) as month,
  	case when organization_d.organization_name is null then 'Firebolt 1' else 'Firebolt 2' end as platform,
  	sum(amount) as consumption
FROM billing_event_f
LEFT JOIN organization_d AS organization_d ON organization_d.organization_id = billing_event_f.organization_id
LEFT JOIN salesforce_account_d AS salesforce_account_d ON billing_event_f.organization_id = salesforce_account_d.organization_id 
LEFT JOIN 
    employee_d AS sf_owner_1
    ON sf_owner_1.sf_user_id = salesforce_account_d.sf_owner_id
LEFT JOIN 
 firebolt_fb1_account_d fb1 ON billing_event_f.aflo_customer_name = fb1.account_name
LEFT JOIN salesforce_account_d sf_acc ON fb1.sf_account_id = sf_acc.sf_account_id
LEFT JOIN amberflo_customer_d  ON billing_event_f.aflo_customer_id = amberflo_customer_d.aflo_customer_id
LEFT JOIN countries_by_region ON amberflo_customer_d.customer_country = countries_by_region.country_code
LEFT JOIN aws_account_d ON billing_event_f.aws_account_id = aws_account_d.aws_account_id
LEFT JOIN 
    employee_d AS sf_owner_2
    ON sf_owner_2.sf_user_id = sf_acc.sf_owner_id
group by all
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
    salesforce_account_d.account_region,
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
### Opportunity Stages 

```sql
SELECT 
    sf_account_id,
    sf_account_name,
    account_region,
    opportunity_id,
    opportunity_name,
    opportunity_d.created_at,
    from_stage,
    to_stage,
    days_in_stage,
    started_at_ts,
    ended_at_ts,
    is_first_stage,
    is_last_stage,
    is_active_stage
FROM opportunity_stage_f
JOIN opportunity_d ON opportunity_d.opportunity_id = opportunity_stage_f.opportunity_id
JOIN salesforce_account_d ON salesforce_account_d.sf_account_id = opportunity_d.sf_account_id;
```

### Gong Calls Analysis

#### Sales Call Activity by Account
```sql
SELECT 
    sa.sf_account_name,
    COUNT(*) AS total_calls,
    COUNT(CASE WHEN gc.gong_direction = 'Outbound' THEN 1 END) AS outbound_calls,
    COUNT(CASE WHEN gc.gong_direction = 'Conference' THEN 1 END) AS conference_calls,
    COUNT(CASE WHEN gc.gong_related_opportunity IS NOT NULL THEN 1 END) AS calls_with_opportunities,
    AVG(gc.gong_opp_amount_time_of_call) AS avg_opp_value
FROM gong_call_f gc
JOIN salesforce_account_d sa ON gc.gong_primary_account = sa.sf_account_id
WHERE gc.gong_call_start_ts >= CURRENT_DATE - INTERVAL 90 DAY
GROUP BY sa.sf_account_name, sa.sf_account_id
ORDER BY total_calls DESC
```

#### Call Frequency and Opportunity Progression
```sql
SELECT 
    gc.gong_opportunity_stage_now,
    COUNT(*) AS call_count,
    COUNT(DISTINCT gc.gong_related_opportunity) AS unique_opportunities,
    AVG(gc.gong_opp_amount_time_of_call) AS avg_opportunity_value,
    COUNT(CASE WHEN gc.gong_direction = 'Outbound' THEN 1 END) AS outbound_calls
FROM gong_call_f gc
WHERE gc.gong_call_start_ts >= CURRENT_DATE - INTERVAL 90 DAY
GROUP BY gc.gong_opportunity_stage_now
ORDER BY call_count DESC
```

#### Basic Call Information Query

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
#### Search Calls by Account/Company

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

#### Recent Calls for Account

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

#### Last Call with Account

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

#### Calls by Opportunity Stage

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

#### Calls with Key Topics

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
