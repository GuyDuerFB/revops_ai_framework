# Lead Assessment Workflow

## Overview
Comprehensive workflow for evaluating leads combining internal data analysis, external intelligence gathering, and ICP scoring to provide actionable lead qualification and engagement recommendations.

## Step 1: Internal Data Discovery (DataAgent)

### 1.1 Contact and Account Search
```sql
-- Search for existing records
SELECT 
    sa.sf_account_name,
    sa.sf_account_type_custom,
    sa.sf_industry,
    sa.sf_sub_industry,
    sa.account_region,
    sa.sf_open_opportunities,
    sa.created_at_ts,
    CASE 
        WHEN sa.sf_account_type_custom = 'Commit Customer' THEN 'Existing Commit'
        WHEN sa.sf_account_type_custom = 'PLG Customer' THEN 'Existing PLG'
        ELSE 'Prospect/New'
    END as relationship_status
FROM salesforce_account_d sa
WHERE LOWER(sa.sf_account_name) LIKE LOWER('%[COMPANY_NAME]%')
   OR LOWER(sa.sf_company_domain) LIKE LOWER('%[COMPANY_DOMAIN]%');
```

### 1.2 Usage History Analysis
```sql
-- Check consumption patterns if existing customer
SELECT 
    ce.organization_id,
    COUNT(DISTINCT ce.activity_date) as active_days_last_90,
    SUM(ce.consumed_fbu) as total_fbu_90d,
    AVG(ce.consumed_fbu) as avg_daily_fbu,
    SUM(ce.total_cost_post_discount_usd) as total_cost_90d,
    MAX(ce.activity_date) as last_activity_date
FROM consumption_event_f ce
JOIN salesforce_account_d sa ON ce.organization_id = sa.organization_id
WHERE sa.sf_account_name ILIKE '%[COMPANY_NAME]%'
  AND ce.activity_date >= CURRENT_DATE - INTERVAL 90 DAY
GROUP BY ce.organization_id;
```

### 1.3 Gong Conversation History
```sql
-- Search for previous sales interactions
SELECT 
    gc.gong_call_name,
    gc.gong_call_start_ts,
    gc.gong_call_brief,
    gc.gong_call_key_points,
    gc.gong_participants_emails,
    gc.gong_opportunity_stage_now,
    gc.gong_opp_amount_time_of_call
FROM gong_call_f gc
JOIN salesforce_account_d sa ON gc.gong_primary_account = sa.sf_account_id
WHERE LOWER(sa.sf_account_name) LIKE LOWER('%[COMPANY_NAME]%')
  AND gc.gong_call_start_ts >= CURRENT_DATE - INTERVAL 180 DAY
ORDER BY gc.gong_call_start_ts DESC
LIMIT 10;
```

## Step 2: External Intelligence Gathering (WebSearchAgent)

### 2.1 Person Intelligence Research
**Request Format:**
```
Research [PERSON_NAME] from [COMPANY] for lead assessment:
- Professional background and current role responsibilities
- Decision-making authority and influence level
- Recent career moves or role changes
- Technical expertise and data infrastructure experience
- Public statements about data strategy or technology priorities
- Professional network and industry connections
```

### 2.2 Company Intelligence Research  
**Request Format:**
```
Research [COMPANY] for comprehensive company assessment:
- Company size, revenue, and funding status
- Technology stack and data infrastructure maturity
- Recent data/analytics initiatives or announcements
- Competitive landscape and market position
- Growth trajectory and expansion plans
- Data strategy and analytics team structure
- Budget and procurement patterns for technology vendors
```

### 2.3 Market Context Analysis
**Request Format:**
```
Analyze market context for [COMPANY] in [INDUSTRY]:
- Industry trends affecting data infrastructure needs
- Regulatory requirements driving analytics adoption
- Competitive pressures requiring real-time insights
- Economic factors impacting technology spending
- Seasonal patterns affecting evaluation timelines
```

## Step 3: ICP Alignment Scoring

### 3.1 Company Fit Assessment (40% weight)
- **Size & Scale**: Revenue >$50M, data volume >10TB
- **Industry Vertical**: High-priority verticals (SaaS, AdTech, Financial Services, E-commerce)
- **Technology Maturity**: Cloud-native, modern data stack adoption
- **Growth Stage**: Scale-up or enterprise with rapid data growth
- **Use Case Alignment**: Customer-facing analytics, real-time applications, AI/ML workloads

### 3.2 Technical Fit Assessment (30% weight)
- **Performance Requirements**: Sub-second latency needs, high concurrency requirements
- **Scale Requirements**: TB+ data volumes, 100+ concurrent users
- **Current Pain Points**: Existing solution limitations, performance bottlenecks
- **Integration Needs**: API-driven applications, embedded analytics
- **Technical Sophistication**: In-house engineering team, SQL proficiency

### 3.3 Business Fit Assessment (30% weight)
- **Budget Authority**: Clear budget allocation for data infrastructure
- **Decision Timeline**: Defined evaluation and procurement timeline
- **Business Impact**: Revenue-generating or cost-saving use cases
- **Executive Sponsorship**: C-level or VP-level champion identified
- **Urgency Factors**: Business drivers requiring immediate solution

### 3.4 ICP Score Calculation
```
Total ICP Score = (Company Fit × 0.4) + (Technical Fit × 0.3) + (Business Fit × 0.3)

Score Interpretation:
- 80-100: Ideal fit - High priority, fast-track engagement
- 60-79: Good fit - Standard qualification and nurturing
- 40-59: Moderate fit - Extended evaluation, education needed
- 20-39: Poor fit - Disqualify or long-term nurture
- 0-19: No fit - Disqualify
```

## Step 4: Lead Qualification Matrix

### 4.1 Relationship Status Assessment
- **New Prospect**: No existing relationship or data
- **Existing Trial**: Active trial user or free credits remaining
- **Former Customer**: Previous relationship requiring reactivation
- **Existing Customer**: Current PLG or Commit customer expansion opportunity

### 4.2 Engagement Readiness Assessment
- **Sales-Ready**: Budget, authority, need, timeline all confirmed
- **Nurture-Ready**: Some qualification criteria met, requires development
- **Education-Needed**: Interest present but missing key qualification elements
- **Disqualified**: Does not meet minimum ICP criteria or fit requirements

### 4.3 Priority Level Assignment
- **P1 - Immediate**: ICP 80+, sales-ready, high revenue potential
- **P2 - Standard**: ICP 60-79, nurture-ready, moderate revenue potential  
- **P3 - Long-term**: ICP 40-59, education-needed, lower priority
- **P4 - Disqualify**: ICP <40, poor fit, minimal potential

## Step 5: Engagement Strategy Development

### 5.1 High Priority (P1) Strategy
- **Immediate Actions**: Schedule demo within 48 hours, assign senior AE
- **Approach**: Executive-level engagement, custom demo with their data
- **Timeline**: Fast-track evaluation, 30-day close timeline
- **Resources**: Solutions Engineer assigned, technical proof of concept
- **Success Metrics**: Meeting attendance, technical validation, procurement engagement

### 5.2 Standard Priority (P2) Strategy
- **Immediate Actions**: Qualify within 1 week, assign AE
- **Approach**: Technical evaluation focus, standard demo flow
- **Timeline**: Standard evaluation, 60-90 day close timeline
- **Resources**: Sales Engineering support as needed
- **Success Metrics**: Trial activation, usage growth, budget confirmation

### 5.3 Nurture Priority (P3) Strategy
- **Immediate Actions**: Add to nurture sequence, content marketing
- **Approach**: Education and awareness building
- **Timeline**: Long-term relationship building, 6+ month timeline
- **Resources**: Marketing automation, periodic check-ins
- **Success Metrics**: Content engagement, trial signup, qualification improvement

### 5.4 Disqualification (P4) Strategy
- **Immediate Actions**: Polite disqualification, future monitoring
- **Approach**: Brief explanation, future consideration invitation
- **Timeline**: Quarterly re-evaluation for status changes
- **Resources**: Minimal, automated monitoring only
- **Success Metrics**: Minimal engagement, focus on higher priorities

## Step 6: Action Implementation (ExecutionAgent)

### 6.1 CRM Updates
- Lead scoring and qualification status update
- Contact and account record creation/enrichment
- Opportunity creation for qualified leads
- Activity logging and next step scheduling

### 6.2 Sales Team Notification
- Immediate notification for P1 leads
- Daily digest for P2 leads  
- Weekly summary for P3 leads
- Quarterly report for P4 status

### 6.3 Marketing Automation
- Sequence enrollment based on priority level
- Content personalization based on ICP scoring
- Lead scoring synchronization with marketing platforms
- Attribution tracking for campaign effectiveness

## Success Metrics and KPIs

### Lead Quality Metrics
- ICP score distribution and accuracy
- Conversion rates by priority level
- Time from lead to qualified opportunity
- Revenue attribution by lead source

### Process Efficiency Metrics
- Time to complete assessment workflow
- Data completeness and accuracy rates
- Internal vs external data contribution
- Agent collaboration effectiveness

### Business Impact Metrics
- Pipeline contribution from assessed leads
- Revenue generated from qualified leads
- Sales team productivity improvement
- Customer acquisition cost optimization