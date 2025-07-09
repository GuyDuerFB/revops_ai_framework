# Comprehensive Customer Risk Assessment Workflow

## Overview
Unified customer health and churn risk assessment workflow combining usage analytics, engagement patterns, business intelligence, external factors, and renewal prediction to identify intervention opportunities and execute retention strategies.

## Trigger Conditions
- **Automated Schedule**: Daily monitoring, weekly health checks, 90/60/30 days before renewal
- **Usage Thresholds**: Significant consumption changes (>30% variance), inactivity alerts
- **Engagement Alerts**: Decreased customer engagement, support activity changes
- **Real-time Anomalies**: Immediate triggers for significant usage anomalies (>50% change)
- **Business Events**: Contract renewals, expansion discussions, competitive threats
- **Manual Assessment**: CSM, Account Executive, or management requests

## Step 1: Usage and Consumption Analysis (DataAgent)

### 1.1 Current Usage Health Assessment
```sql
-- Comprehensive usage health over multiple timeframes
WITH usage_metrics AS (
    SELECT 
        ce.organization_id,
        -- 30-day metrics
        SUM(CASE WHEN ce.activity_date >= CURRENT_DATE - 30 THEN ce.consumed_fbu ELSE 0 END) as fbu_30d,
        SUM(CASE WHEN ce.activity_date >= CURRENT_DATE - 30 THEN ce.total_cost_post_discount_usd ELSE 0 END) as cost_30d,
        COUNT(DISTINCT CASE WHEN ce.activity_date >= CURRENT_DATE - 30 THEN ce.activity_date END) as active_days_30d,
        -- 90-day metrics
        SUM(CASE WHEN ce.activity_date >= CURRENT_DATE - 90 THEN ce.consumed_fbu ELSE 0 END) as fbu_90d,
        SUM(CASE WHEN ce.activity_date >= CURRENT_DATE - 90 THEN ce.total_cost_post_discount_usd ELSE 0 END) as cost_90d,
        COUNT(DISTINCT CASE WHEN ce.activity_date >= CURRENT_DATE - 90 THEN ce.activity_date END) as active_days_90d,
        -- Efficiency and trend metrics
        AVG(ce.consumed_fbu) as avg_fbu_per_event,
        MAX(ce.activity_date) as last_activity_date,
        MIN(ce.activity_date) as first_activity_date
    FROM consumption_event_f ce
    WHERE ce.activity_date >= CURRENT_DATE - 90
    GROUP BY ce.organization_id
)
SELECT 
    sa.sf_account_name,
    sa.sf_account_type_custom,
    sa.account_region,
    um.*,
    -- Trend calculations
    CASE 
        WHEN um.fbu_90d > 0 THEN (um.fbu_30d * 3.0 - um.fbu_90d) / um.fbu_90d * 100
        ELSE 0 
    END as fbu_trend_pct,
    -- Health indicators
    CASE 
        WHEN um.last_activity_date < CURRENT_DATE - 14 THEN 'Inactive'
        WHEN um.fbu_30d * 3 < um.fbu_90d * 0.7 THEN 'Declining'
        WHEN um.fbu_30d * 3 > um.fbu_90d * 1.3 THEN 'Growing'
        ELSE 'Stable'
    END as usage_trend,
    DATEDIFF('day', um.last_activity_date, CURRENT_DATE) as days_since_activity,
    -- Anomaly detection
    CASE
        WHEN um.fbu_30d = 0 AND um.fbu_90d > 0 THEN 'Complete Stop'
        WHEN um.fbu_30d * 3 < um.fbu_90d * 0.3 THEN 'Major Decline'
        WHEN um.fbu_30d * 3 > um.fbu_90d * 3 THEN 'Major Spike'
        ELSE 'Normal'
    END as anomaly_flag
FROM usage_metrics um
JOIN salesforce_account_d sa ON um.organization_id = sa.organization_id
WHERE sa.sf_account_id = '[ACCOUNT_ID]'
   OR LOWER(sa.sf_account_name) LIKE LOWER('%[COMPANY_NAME]%');
```

### 1.2 Historical Usage Pattern Analysis
```sql
-- Comprehensive historical analysis for trend detection
WITH monthly_usage AS (
    SELECT 
        ce.organization_id,
        DATE_TRUNC('month', ce.activity_date) as usage_month,
        SUM(ce.consumed_fbu) as monthly_fbu,
        SUM(ce.total_cost_post_discount_usd) as monthly_cost,
        COUNT(DISTINCT ce.activity_date) as active_days,
        COUNT(*) as total_events,
        AVG(ce.consumed_fbu) as avg_fbu_per_event
    FROM consumption_event_f ce
    WHERE ce.activity_date >= CURRENT_DATE - INTERVAL 12 MONTH
    GROUP BY ce.organization_id, DATE_TRUNC('month', ce.activity_date)
)
SELECT 
    sa.sf_account_name,
    mu.usage_month,
    mu.monthly_fbu,
    mu.monthly_cost,
    mu.active_days,
    LAG(mu.monthly_fbu, 1) OVER (ORDER BY mu.usage_month) as prev_month_fbu,
    LAG(mu.monthly_fbu, 3) OVER (ORDER BY mu.usage_month) as prev_quarter_fbu,
    LAG(mu.monthly_fbu, 12) OVER (ORDER BY mu.usage_month) as prev_year_fbu,
    -- Growth calculations
    CASE 
        WHEN LAG(mu.monthly_fbu, 1) OVER (ORDER BY mu.usage_month) > 0 
        THEN (mu.monthly_fbu - LAG(mu.monthly_fbu, 1) OVER (ORDER BY mu.usage_month)) / LAG(mu.monthly_fbu, 1) OVER (ORDER BY mu.usage_month) * 100
        ELSE 0 
    END as month_over_month_growth,
    -- Volatility indicators
    STDDEV(mu.monthly_fbu) OVER (ORDER BY mu.usage_month ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) as usage_volatility
FROM monthly_usage mu
JOIN salesforce_account_d sa ON mu.organization_id = sa.organization_id
WHERE sa.sf_account_id = '[ACCOUNT_ID]'
ORDER BY mu.usage_month DESC;
```

### 1.3 Billing and Revenue Health Analysis
```sql
-- Revenue trends and billing health assessment
SELECT 
    sa.sf_account_name,
    be.mrr_report_date_ts,
    be.amount as monthly_revenue,
    be.invoice_month,
    SUM(be.amount) OVER (ORDER BY be.mrr_report_date_ts ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as quarterly_revenue,
    LAG(be.amount, 1) OVER (ORDER BY be.mrr_report_date_ts) as prev_month_revenue,
    LAG(be.amount, 12) OVER (ORDER BY be.mrr_report_date_ts) as prev_year_revenue,
    -- Growth calculations
    CASE 
        WHEN LAG(be.amount, 1) OVER (ORDER BY be.mrr_report_date_ts) > 0 
        THEN (be.amount - LAG(be.amount, 1) OVER (ORDER BY be.mrr_report_date_ts)) / LAG(be.amount, 1) OVER (ORDER BY be.mrr_report_date_ts) * 100
        ELSE 0 
    END as revenue_growth_pct
FROM billing_event_f be
JOIN salesforce_account_d sa ON be.organization_id = sa.organization_id
WHERE sa.sf_account_id = '[ACCOUNT_ID]'
  AND be.mrr_report_date_ts >= CURRENT_DATE - INTERVAL 24 MONTH
ORDER BY be.mrr_report_date_ts DESC;
```

### 1.4 Anomaly Detection and Pattern Analysis
```sql
-- Advanced anomaly detection using statistical baselines
WITH usage_baselines AS (
    SELECT 
        ce.organization_id,
        ce.activity_date,
        ce.consumed_fbu,
        -- Statistical baselines
        AVG(ce.consumed_fbu) OVER (
            ORDER BY ce.activity_date 
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        ) as rolling_30d_avg,
        STDDEV(ce.consumed_fbu) OVER (
            ORDER BY ce.activity_date 
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        ) as rolling_30d_stddev,
        -- Weekly patterns
        AVG(ce.consumed_fbu) OVER (
            PARTITION BY EXTRACT('dow' FROM ce.activity_date)
            ORDER BY ce.activity_date 
            ROWS BETWEEN 8 PRECEDING AND 1 PRECEDING
        ) as same_weekday_avg
    FROM consumption_event_f ce
    WHERE ce.activity_date >= CURRENT_DATE - INTERVAL 90 DAY
)
SELECT 
    sa.sf_account_name,
    ub.activity_date,
    ub.consumed_fbu,
    ub.rolling_30d_avg,
    ub.same_weekday_avg,
    -- Anomaly calculations
    CASE 
        WHEN ub.rolling_30d_stddev > 0 
        THEN ABS(ub.consumed_fbu - ub.rolling_30d_avg) / ub.rolling_30d_stddev
        ELSE 0 
    END as z_score,
    -- Anomaly classification
    CASE 
        WHEN ub.consumed_fbu = 0 AND ub.rolling_30d_avg > 0 THEN 'Complete Stop'
        WHEN ub.consumed_fbu > ub.rolling_30d_avg * 3 THEN 'Major Spike'
        WHEN ub.consumed_fbu < ub.rolling_30d_avg * 0.3 AND ub.rolling_30d_avg > 0 THEN 'Major Drop'
        WHEN ABS(ub.consumed_fbu - ub.rolling_30d_avg) / ub.rolling_30d_avg > 0.5 THEN 'Moderate Anomaly'
        ELSE 'Normal'
    END as anomaly_type,
    -- Severity scoring
    CASE 
        WHEN ub.consumed_fbu = 0 AND ub.rolling_30d_avg > 0 THEN 100
        WHEN ub.consumed_fbu > ub.rolling_30d_avg * 3 THEN 80
        WHEN ub.consumed_fbu < ub.rolling_30d_avg * 0.3 THEN 90
        WHEN ABS(ub.consumed_fbu - ub.rolling_30d_avg) / ub.rolling_30d_avg > 0.5 THEN 60
        ELSE 0
    END as anomaly_severity
FROM usage_baselines ub
JOIN salesforce_account_d sa ON ub.organization_id = sa.organization_id
WHERE sa.sf_account_id = '[ACCOUNT_ID]'
  AND ub.activity_date >= CURRENT_DATE - 30
ORDER BY ub.activity_date DESC;
```

## Step 2: Engagement and Relationship Analysis (DataAgent)

### 2.1 Support and Engagement Patterns
```sql
-- Customer support interaction and engagement analysis
SELECT 
    sa.sf_account_name,
    COUNT(*) as support_tickets_90d,
    AVG(DATEDIFF('day', ticket_created_date, ticket_resolved_date)) as avg_resolution_days,
    SUM(CASE WHEN ticket_priority = 'High' THEN 1 ELSE 0 END) as high_priority_tickets,
    SUM(CASE WHEN ticket_status = 'Open' THEN 1 ELSE 0 END) as open_tickets,
    MAX(ticket_created_date) as last_ticket_date,
    DATEDIFF('day', MAX(ticket_created_date), CURRENT_DATE) as days_since_last_ticket
FROM support_tickets st
JOIN salesforce_account_d sa ON st.account_id = sa.sf_account_id
WHERE st.ticket_created_date >= CURRENT_DATE - 90
  AND sa.sf_account_id = '[ACCOUNT_ID]'
GROUP BY sa.sf_account_name;
```

### 2.2 Gong Conversation Analysis
```sql
-- Recent conversation patterns and sentiment
SELECT 
    sa.sf_account_name,
    COUNT(*) as calls_90d,
    AVG(gc.gong_call_duration) as avg_call_duration,
    COUNT(DISTINCT gc.gong_participants_emails) as unique_participants,
    MAX(gc.gong_call_start_ts) as last_call_date,
    DATEDIFF('day', MAX(gc.gong_call_start_ts), CURRENT_DATE) as days_since_last_call,
    STRING_AGG(DISTINCT gc.gong_call_brief, ' | ') as recent_topics
FROM gong_call_f gc
JOIN salesforce_account_d sa ON gc.gong_primary_account = sa.sf_account_id
WHERE gc.gong_call_start_ts >= CURRENT_DATE - 90
  AND sa.sf_account_id = '[ACCOUNT_ID]'
GROUP BY sa.sf_account_name;
```

### 2.3 Contract and Renewal Context
```sql
-- Contract status and renewal timeline analysis
SELECT 
    sa.sf_account_name,
    sa.sf_account_type_custom,
    contract_start_date,
    contract_end_date,
    DATEDIFF('day', CURRENT_DATE, contract_end_date) as days_to_renewal,
    contract_value,
    auto_renewal_clause,
    cancellation_notice_period,
    CASE 
        WHEN DATEDIFF('day', CURRENT_DATE, contract_end_date) <= 30 THEN 'Immediate Renewal Risk'
        WHEN DATEDIFF('day', CURRENT_DATE, contract_end_date) <= 90 THEN 'Near-term Renewal'
        WHEN DATEDIFF('day', CURRENT_DATE, contract_end_date) <= 180 THEN 'Planning Period'
        ELSE 'Long-term'
    END as renewal_phase
FROM customer_contracts cc
JOIN salesforce_account_d sa ON cc.account_id = sa.sf_account_id
WHERE sa.sf_account_id = '[ACCOUNT_ID]'
  AND contract_status = 'Active';
```

## Step 3: External Factors Analysis (WebSearchAgent)

### 3.1 Company Health and Market Context
**Request Format:**
```
Research [CUSTOMER] external factors affecting retention and growth:
- Company financial health, funding status, and stability indicators
- Market challenges or growth opportunities affecting data strategy
- Leadership changes in technology or data roles
- Competitive landscape changes affecting their business model
- Technology strategy shifts or platform consolidation initiatives
- Budget allocation patterns and cost optimization pressures
- Regulatory or compliance changes affecting data requirements
- Industry trends impacting their data infrastructure needs
```

### 3.2 Competitive Intelligence and Threats
**Request Format:**
```
Analyze competitive threats for [CUSTOMER] retention:
- Known competitor evaluations or RFP processes underway
- Competitive vendor relationships and partnerships
- Technology stack changes or migrations planned
- Vendor consolidation initiatives affecting data infrastructure
- Cost optimization pressures driving vendor reassessment
- Performance or scalability issues driving solution evaluation
- New use cases requiring different technology capabilities
```

## Step 4: Comprehensive Risk Scoring Framework

### 4.1 Primary Risk Indicators (Weighted Scoring)

#### **Usage and Adoption Metrics (30% weight)**
**Consumption Trends:**
- Increasing usage trends: +20 points
- Stable usage patterns: 0 points  
- Declining usage (1-25%): -10 points
- Declining usage (26-50%): -20 points
- Declining usage (>50%): -30 points

**Activity Patterns:**
- Daily active usage: +10 points
- Weekly active usage: +5 points
- Monthly active usage: 0 points
- Sporadic usage: -10 points
- No recent activity (>14 days): -20 points

**Feature Adoption:**
- Expanding feature usage: +10 points
- Stable feature usage: 0 points
- Limited feature adoption: -5 points
- Decreasing feature usage: -10 points

#### **Relationship Health (25% weight)**
**Engagement Metrics:**
- Strong champion advocacy: +15 points
- Regular executive engagement: +10 points
- Responsive to CSM outreach: +5 points
- Standard engagement level: 0 points
- Delayed responses or missed meetings: -10 points
- Loss of key champion or contact: -20 points

**Support Interaction Quality:**
- Proactive optimization discussions: +10 points
- Standard support interactions: 0 points
- Frequent high-priority tickets: -10 points
- Escalations or complaints: -15 points

#### **Financial and Business Context (20% weight)**
**Revenue Trends:**
- Growing revenue/usage: +15 points
- Stable revenue: 0 points
- Declining revenue (1-25%): -10 points
- Declining revenue (>25%): -20 points

**Business Health Indicators:**
- Strong company growth: +10 points
- Stable business conditions: 0 points
- Known budget constraints: -10 points
- Financial stress indicators: -20 points

#### **Technical and Operational Factors (15% weight)**
**Performance Satisfaction:**
- Excellent performance feedback: +10 points
- Satisfactory performance: 0 points
- Performance concerns raised: -10 points
- Significant performance issues: -20 points

**Integration Health:**
- Expanding integration usage: +5 points
- Stable integrations: 0 points
- Integration challenges: -10 points

#### **Competitive and Strategic Factors (10% weight)**
**Competitive Threats:**
- Strong Firebolt advocacy: +10 points
- Neutral vendor stance: 0 points
- Known competitor evaluation: -15 points
- Strong competitor relationship: -25 points

### 4.2 Risk Score Calculation and Classification
```
Total Risk Score = (Usage × 0.30) + (Relationship × 0.25) + (Financial × 0.20) + (Technical × 0.15) + (Competitive × 0.10)

Risk Categories:
- 60-100: Low Risk - Healthy, growing relationship
- 20-59: Moderate Risk - Some concerns, monitoring needed
- -20-19: High Risk - Significant issues, intervention required
- -50 to -21: Critical Risk - Immediate escalation needed
- Below -50: Extreme Risk - Executive intervention required
```

### 4.3 Renewal Risk Specific Assessment

#### **Renewal Timeline Risk Factors**
**90 Days Before Renewal:**
- Contract negotiation preparation
- Budget planning and approval processes
- Performance review and satisfaction assessment
- Competitive evaluation window
- Success metrics and ROI review

**60 Days Before Renewal:**
- Formal renewal discussions initiation
- Stakeholder alignment and decision making
- Terms and pricing negotiations
- Implementation and migration planning if switching

**30 Days Before Renewal:**
- Final decision making and approvals
- Contract execution and legal reviews
- Transition planning if not renewing
- Last-chance intervention opportunities

## Step 5: Anomaly Analysis and Pattern Recognition

### 5.1 Usage Anomaly Classification

#### **Positive Anomalies (Usage Increases)**
**Sudden Spikes (>50% increase)**
- Data backfill or catch-up processing
- New project or team onboarding
- Business event (marketing campaign, product launch)
- Seasonal business patterns
- Successful feature adoption

**Gradual Growth (Sustained increases)**
- Business expansion and scaling
- Successful user adoption programs
- New use case development
- Market growth driving data needs

#### **Negative Anomalies (Usage Decreases)**
**Sudden Drops (>50% decrease)**
- Technical issues or service problems
- Data pipeline failures or integration issues
- Team changes or personnel loss
- Budget constraints or cost optimization
- Competitive solution evaluation

**Gradual Decline (Trending decreases)**
- Changing business priorities
- Seasonal business reduction
- Process optimization reducing data needs
- Migration to alternative solutions
- Business contraction or downsizing

#### **Critical Anomalies**
**Complete Usage Stop**
- Immediate investigation required
- Technical troubleshooting needed
- Relationship health check mandatory
- Competitive threat assessment
- Contract status verification

## Step 6: Intervention Strategy and Action Planning

### 6.1 Risk-Based Intervention Strategies

#### **Low Risk (60-100) - Growth and Expansion Focus**
**Actions:**
- Expansion opportunity identification
- Success story documentation
- Reference customer development
- Strategic partnership discussions
- Optimization and best practices sharing

**Resources:**
- Customer Success Manager regular check-ins
- Product updates and roadmap sharing
- Training and enablement opportunities
- Executive relationship building

**Success Metrics:**
- Usage growth trends
- Expansion revenue opportunities
- Satisfaction scores and feedback
- Reference and advocacy participation

#### **Moderate Risk (20-59) - Proactive Health Management**
**Actions:**
- Performance optimization review
- Stakeholder engagement expansion
- Training and adoption programs
- Technical health assessment
- Business case reinforcement

**Resources:**
- Enhanced CSM engagement
- Technical support and optimization
- Product specialist consultation
- Executive check-in scheduling

**Success Metrics:**
- Usage stabilization and growth
- Engagement quality improvement
- Technical performance optimization
- Stakeholder satisfaction recovery

#### **High Risk (-20-19) - Active Intervention Required**
**Actions:**
- Immediate stakeholder outreach
- Technical troubleshooting and optimization
- Competitive differentiation reinforcement
- Business case redevelopment
- Executive escalation and engagement

**Resources:**
- Senior CSM or account management
- Technical architecture review
- Executive sponsor engagement
- Custom solutions and support

**Success Metrics:**
- Issue resolution and satisfaction
- Usage recovery and stabilization
- Stakeholder re-engagement
- Competitive position strengthening

#### **Critical Risk (-50 to -21) - Executive Intervention**
**Actions:**
- Executive escalation and direct engagement
- Comprehensive account review and planning
- Technical and business case reconstruction
- Competitive response strategy
- Risk mitigation and relationship recovery

**Resources:**
- Executive sponsor direct involvement
- Cross-functional team support
- Custom solutions and flexible terms
- Senior technical resources

**Success Metrics:**
- Relationship recovery indicators
- Technical issue resolution
- Business case acceptance
- Renewal probability improvement

#### **Extreme Risk (Below -50) - Salvage Operations**
**Actions:**
- C-level executive engagement
- Comprehensive win-back strategy
- Technical and commercial concessions
- Relationship repair and trust building
- Graceful transition planning if necessary

**Resources:**
- Senior executive time investment
- Custom engineering and support
- Commercial flexibility and incentives
- Dedicated project management

**Success Metrics:**
- Relationship stabilization
- Trust and confidence rebuilding
- Technical satisfaction improvement
- Retention probability assessment

### 6.2 Specific Intervention Tactics by Risk Factor

#### **Usage Decline Interventions**
- Technical optimization workshops
- Best practices training and implementation
- Use case expansion and development
- Performance tuning and enhancement
- Integration optimization and support

#### **Relationship Issues Interventions**
- Stakeholder mapping and expansion
- Executive relationship building
- Success story sharing and validation
- Regular business review establishment
- Communication frequency optimization

#### **Competitive Threat Responses**
- Differentiation and positioning reinforcement
- TCO and ROI analysis updates
- Performance benchmarking and comparison
- Feature gap assessment and roadmap alignment
- Reference customer and proof point sharing

#### **Financial Pressure Responses**
- Cost optimization and efficiency analysis
- Usage-based pricing model optimization
- Phased implementation or payment terms
- ROI demonstration and business case strengthening
- Budget planning and approval support

## Step 7: Execution and Monitoring (ExecutionAgent)

### 7.1 Immediate Response Actions
- **High/Critical Risk Alerts**: Immediate stakeholder notification and escalation
- **Anomaly Investigations**: Technical troubleshooting and root cause analysis
- **Relationship Outreach**: CSM and account management engagement
- **Competitive Responses**: Positioning and differentiation activation

### 7.2 Ongoing Monitoring and Tracking
- **Daily Usage Monitoring**: Automated anomaly detection and alerting
- **Weekly Risk Scoring**: Updated risk assessments and trend analysis
- **Monthly Business Reviews**: Comprehensive health and strategy assessment
- **Quarterly Executive Reviews**: Strategic relationship and growth planning

### 7.3 Success Metrics and KPIs

#### **Leading Indicators**
- Usage trend direction and velocity
- Engagement frequency and quality
- Support ticket volume and severity
- Stakeholder accessibility and responsiveness

#### **Lagging Indicators**
- Renewal rates and expansion revenue
- Customer lifetime value growth
- Reference and advocacy participation
- Net Promoter Score improvements

#### **Process Metrics**
- Risk assessment accuracy and predictive value
- Intervention effectiveness and success rates
- Time to resolution for risk factors
- Resource utilization and efficiency

## Risk Assessment Summary Template

### **Customer**: [CUSTOMER_NAME]
### **Assessment Date**: [DATE]
### **Assessment Owner**: [CSM/OWNER]

#### **Overall Risk Score**: [X/100] - [RISK_CATEGORY]

#### **Risk Component Scores**:
- Usage and Adoption: [X/30]
- Relationship Health: [X/25]
- Financial Context: [X/20]
- Technical Factors: [X/15]
- Competitive Factors: [X/10]

#### **Key Risk Factors Identified**:
1. [PRIMARY_RISK] - Severity: [HIGH/MEDIUM/LOW] - Impact: [DESCRIPTION]
2. [SECONDARY_RISK] - Severity: [HIGH/MEDIUM/LOW] - Impact: [DESCRIPTION]
3. [TERTIARY_RISK] - Severity: [HIGH/MEDIUM/LOW] - Impact: [DESCRIPTION]

#### **Usage Pattern Analysis**:
- **Current Trend**: [GROWING/STABLE/DECLINING/INACTIVE]
- **Anomalies Detected**: [ANOMALY_TYPE] - Severity: [X/100]
- **Days Since Last Activity**: [X]
- **Usage Compared to Baseline**: [+/-X%]

#### **Renewal Context**:
- **Days to Renewal**: [X]
- **Renewal Phase**: [IMMEDIATE/NEAR-TERM/PLANNING/LONG-TERM]
- **Contract Value**: [$X]
- **Renewal Probability**: [X%]

#### **Recommended Actions**:
1. [ACTION_ITEM] - [PRIORITY] - [OWNER] - [TIMELINE] - [SUCCESS_METRIC]
2. [ACTION_ITEM] - [PRIORITY] - [OWNER] - [TIMELINE] - [SUCCESS_METRIC]
3. [ACTION_ITEM] - [PRIORITY] - [OWNER] - [TIMELINE] - [SUCCESS_METRIC]

#### **Next Review Date**: [DATE]
#### **Escalation Status**: [NONE/CSM/MANAGEMENT/EXECUTIVE]

This comprehensive customer risk assessment workflow provides early warning systems, detailed intervention strategies, and ongoing monitoring to maximize customer retention and growth.