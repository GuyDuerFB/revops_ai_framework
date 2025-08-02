# Comprehensive Deal Assessment Workflow

## Overview
Unified methodology for analyzing opportunities combining discovery assessment, deal health analysis, and strategic positioning to provide comprehensive deal evaluation and advancement strategies. This workflow integrates discovery questions, ICP scoring, health assessment, and risk mitigation.

## Trigger Conditions
- New opportunity discovery and qualification
- Deal stage progression reviews
- Weekly deal health checks for key opportunities
- Manual assessment requests for specific deals
- Executive/forecast review preparation
- Risk threshold alerts
- **Deal review queries**: "What is the status of [Company] deal?", "Assess probability of [Deal]"
- **Interaction analysis**: "Summarize our interactions with [Company]"

## Core Discovery Framework

### Discovery Questions Matrix
The following questions guide the discovery process and inform our assessment:

#### **What Should We Keep?**
- What's working well in their current data infrastructure?
- Which existing tools and processes are delivering value?
- What team capabilities and relationships should we leverage?
- Which stakeholders are engaged and supportive?
- What successful use cases can we build upon?

#### **What Should We Stop?**
- What processes are creating bottlenecks or inefficiencies?
- Which tools are not delivering expected value?
- What approaches are causing cost or performance issues?
- Which stakeholders are blocking progress?
- What activities are not aligned with business objectives?

#### **What Should Change?**
- What performance improvements are needed?
- Which capabilities need to be enhanced or added?
- What processes require optimization?
- Which stakeholders need different engagement approaches?
- What new opportunities should be pursued?

#### **ICP Positioning Assessment**
- Where is the pipeline positioned within our ICP?
- Where is their data currently located?
- What's the major use case driving this evaluation?
- Which opportunities have blockers vs. clear paths forward?

## Step 1: Account Intelligence & Data Discovery (DataAgent)

### 1.1 Account Foundation Analysis
```sql
-- Comprehensive account and opportunity context
SELECT 
    sa.sf_account_name,
    sa.sf_account_type_custom,
    sa.sf_industry,
    sa.sf_sub_industry,
    sa.account_region,
    sa.sf_open_opportunities,
    sa.organization_id,
    CASE 
        WHEN sa.sf_account_type_custom = 'Commit Customer' THEN 'Existing Commit Customer'
        WHEN sa.sf_account_type_custom = 'PLG Customer' THEN 'Existing PLG Customer'
        ELSE 'New Prospect'
    END as relationship_status,
    od.opportunity_id,
    od.opportunity_name,
    od.opportunity_type,
    od.stage_name,
    od.amount,
    od.contract_duration_months,
    od.amount / od.contract_duration_months * 12 as annual_contract_value,
    od.probability,
    od.close_date,
    od.created_at_ts,
    DATEDIFF('day', od.created_at_ts, CURRENT_DATE) as days_in_cycle,
    DATEDIFF('day', CURRENT_DATE, od.close_date) as days_to_close,
    emp.first_name || ' ' || emp.last_name as opportunity_owner
FROM salesforce_account_d sa
LEFT JOIN opportunity_d od ON sa.sf_account_id = od.sf_account_id
LEFT JOIN employee_d emp ON od.owner_id = emp.sf_user_id
WHERE sa.sf_account_id = '[ACCOUNT_ID]'
   OR od.opportunity_id = '[OPPORTUNITY_ID]'
   OR LOWER(sa.sf_account_name) LIKE LOWER('%[COMPANY_NAME]%');
```

### 1.2 Current Data Infrastructure Assessment
```sql
-- Understanding existing data footprint and usage patterns
SELECT 
    COALESCE(usage.total_fbu_90d, 0) as current_usage_fbu,
    COALESCE(usage.total_cost_90d, 0) as current_monthly_spend,
    COALESCE(usage.active_days_90d, 0) as active_days_last_90,
    COALESCE(usage.avg_daily_fbu, 0) as avg_daily_usage,
    COALESCE(billing.total_revenue_12m, 0) as revenue_last_12m,
    COALESCE(billing.avg_monthly_revenue, 0) as avg_monthly_revenue,
    CASE 
        WHEN usage.total_fbu_90d > 0 THEN 'Active User'
        WHEN billing.total_revenue_12m > 0 THEN 'Previous User'
        ELSE 'Net New'
    END as usage_status,
    CASE
        WHEN usage.total_fbu_90d > 10000 THEN 'High Usage'
        WHEN usage.total_fbu_90d > 1000 THEN 'Medium Usage'
        WHEN usage.total_fbu_90d > 0 THEN 'Low Usage'
        ELSE 'No Usage'
    END as usage_tier
FROM salesforce_account_d sa
LEFT JOIN (
    SELECT 
        ce.organization_id,
        SUM(ce.consumed_fbu) as total_fbu_90d,
        SUM(ce.total_cost_post_discount_usd) as total_cost_90d,
        COUNT(DISTINCT ce.activity_date) as active_days_90d,
        AVG(ce.consumed_fbu) as avg_daily_fbu
    FROM consumption_event_f ce
    WHERE ce.activity_date >= CURRENT_DATE - INTERVAL 90 DAY
    GROUP BY ce.organization_id
) usage ON sa.organization_id = usage.organization_id
LEFT JOIN (
    SELECT 
        be.organization_id,
        SUM(be.amount) as total_revenue_12m,
        AVG(be.amount) as avg_monthly_revenue
    FROM billing_event_f be
    WHERE be.mrr_report_date_ts >= CURRENT_DATE - INTERVAL 12 MONTH
    GROUP BY be.organization_id
) billing ON sa.organization_id = billing.organization_id
WHERE sa.sf_account_id = '[ACCOUNT_ID]';
```

### 1.3 Historical Deal Progression Analysis
```sql
-- Track deal progression velocity and changes
SELECT 
    od.opportunity_id,
    od.stage_name,
    od.amount,
    od.probability,
    od.close_date,
    LAG(od.stage_name) OVER (ORDER BY od.last_modified_date_ts) as previous_stage,
    LAG(od.amount) OVER (ORDER BY od.last_modified_date_ts) as previous_amount,
    LAG(od.close_date) OVER (ORDER BY od.last_modified_date_ts) as previous_close_date,
    od.last_modified_date_ts
FROM opportunity_d od
WHERE od.opportunity_id = '[OPPORTUNITY_ID]'
ORDER BY od.last_modified_date_ts DESC;
```

### 1.4 Conversation Intelligence & Stakeholder Mapping
```sql
-- Comprehensive Gong analysis including sentiment and engagement
SELECT 
    gc.gong_call_name,
    gc.gong_call_start_ts,
    gc.gong_call_duration,
    gc.gong_direction,
    gc.gong_participants_emails,
    gc.gong_call_brief,
    gc.gong_call_key_points,
    gc.gong_opportunity_stage_now,
    gc.gong_opp_amount_time_of_call,
    gc.gong_opp_close_date_time_of_call,
    gc.gong_opp_probability_time_of_call,
    DATEDIFF('day', gc.gong_call_start_ts, CURRENT_DATE) as days_since_call,
    CASE 
        WHEN gc.gong_call_duration > 60 THEN 'Deep Engagement'
        WHEN gc.gong_call_duration > 30 THEN 'Standard Engagement'
        ELSE 'Brief Engagement'
    END as engagement_level
FROM gong_call_f gc
WHERE gc.gong_related_opportunity = '[OPPORTUNITY_ID]'
   OR gc.gong_primary_opportunity = '[OPPORTUNITY_ID]'
ORDER BY gc.gong_call_start_ts DESC
LIMIT 20;
```

## Step 2: Market Context & Competitive Analysis (WebSearchAgent)

### 2.1 Company Intelligence Research
**Request Format:**
```
Research [COMPANY] for comprehensive deal assessment:
- Recent business developments affecting data infrastructure decisions
- Technology initiatives and digital transformation projects
- Leadership changes in data/technology roles affecting decision-making
- Market pressures requiring analytical capabilities or AI initiatives
- Competitive threats demanding real-time insights
- Regulatory or compliance drivers affecting data strategy
- Budget allocation and procurement timeline considerations
- Growth trajectory and expansion plans impacting data needs
```

### 2.2 Competitive Landscape Analysis
**Request Format:**
```
Analyze competitive context for [COMPANY] data infrastructure evaluation:
- Known vendors in active evaluation (Snowflake, Redshift, BigQuery, etc.)
- Previous vendor relationships and migration history
- Competitive strengths and weaknesses for this specific use case
- Differentiation opportunities for Firebolt positioning
- Competitive threats and response strategies needed
- Price/performance positioning advantages available
- Technical differentiation opportunities for this use case
```

### 2.3 Industry and Market Trends Analysis
**Request Format:**
```
Research industry trends affecting [COMPANY] in [INDUSTRY]:
- Data infrastructure modernization trends affecting buying patterns
- Real-time analytics adoption patterns in their industry
- AI/ML initiative acceleration trends and budget allocation
- Customer experience technology investments and priorities
- Regulatory compliance requirements driving analytics needs
- Seasonal buying behaviors and budget cycle considerations
```

## Step 3: Opportunity Classification & Use Case Analysis

### 3.1 Opportunity Type Identification
Based on discovery, classify the opportunity into one of these categories:

#### **Migration Opportunities**
- **Redshift Takeout**: Customer looking to replace Amazon Redshift
  - *Triggers*: Performance bottlenecks, scaling limitations, cost concerns
  - *Timeline*: 3-6 months evaluation, 2-4 months migration
  - *Decision Factors*: Performance benchmarks, TCO analysis, migration complexity

- **Snowflake Takeout**: Customer experiencing Snowflake limitations
  - *Triggers*: Credit fever, concurrency issues, performance at scale
  - *Timeline*: 2-4 months evaluation, 1-3 months migration
  - *Decision Factors*: Concurrency performance, cost predictability, query speed

- **BigQuery Takeout**: Customer facing BigQuery constraints
  - *Triggers*: Unpredictable costs, concurrent user limits, performance issues
  - *Timeline*: 2-3 months evaluation, 1-2 months migration
  - *Decision Factors*: Cost control, concurrency scaling, performance consistency

#### **Expansion Opportunities**
- **PLG Expansion**: Existing self-service customer growing usage
  - *Triggers*: Usage growth, team expansion, need for enterprise features
  - *Timeline*: 1-2 months evaluation, immediate implementation
  - *Decision Factors*: Feature needs, support requirements, pricing optimization

- **Commit Customer Growth**: Enterprise customer expanding use cases
  - *Triggers*: New projects, additional teams, increased data volumes
  - *Timeline*: 1-3 months evaluation, phased rollout
  - *Decision Factors*: Additional capacity, new features, strategic alignment

#### **Greenfield Opportunities**
- **New Analytics Platform**: Building new analytical capabilities
  - *Triggers*: Digital transformation, new data initiatives, competitive pressure
  - *Timeline*: 3-6 months evaluation, 2-6 months implementation
  - *Decision Factors*: Technology fit, team capabilities, strategic vision

- **AI/GenAI Initiative**: Implementing AI-powered applications
  - *Triggers*: AI strategy, competitive differentiation, customer experience
  - *Timeline*: 2-4 months evaluation, 3-6 months implementation
  - *Decision Factors*: Vector capabilities, hybrid retrieval, performance scale

### 3.2 Use Case Mapping
Map the customer's primary use case to Firebolt strengths:

#### **Customer-Facing Analytics**
- Real-time dashboards with sub-second performance requirements
- Embedded analytics in customer applications
- Multi-tenant SaaS platforms requiring workload isolation
- High-concurrency user-facing applications (100+ concurrent users)

#### **Operational Analytics**
- Real-time business intelligence and reporting
- Operational dashboards for internal teams
- Performance monitoring and alerting systems
- Supply chain and inventory optimization

#### **AI/ML Applications**
- RAG (Retrieval-Augmented Generation) systems
- Semantic search and recommendation engines
- Real-time feature serving for ML models
- Conversational analytics and chatbots

#### **Data Infrastructure Modernization**
- Cloud-native data architecture migration
- Real-time data processing and streaming capabilities
- Multi-workload consolidation and optimization
- Cost optimization and performance improvement

## Step 4: ICP Alignment Assessment

### 4.1 ICP Scoring Framework (0-100 scale)

#### **Company Characteristics (25% weight)**
- **Size & Scale** (6 points): Revenue >$50M, data volume >10TB, significant user base
- **Industry Vertical** (6 points): High-priority verticals (SaaS, AdTech, Financial Services, E-commerce)
- **Technology Maturity** (6 points): Cloud-native adoption, modern data stack implementation
- **Growth Trajectory** (7 points): Rapid data/user growth, expansion plans, scaling needs

#### **Technical Requirements (30% weight)**
- **Performance Needs** (8 points): Sub-second latency requirements, high concurrency needs
- **Scale Requirements** (8 points): TB+ data volumes, 100+ concurrent users, high QPS
- **Current Pain Points** (7 points): Clear performance bottlenecks, cost concerns, scalability issues
- **Integration Complexity** (7 points): API-driven applications, embedded analytics needs

#### **Business Fit (25% weight)**
- **Budget Authority** (6 points): Clear budget allocation, decision-making power identified
- **Decision Timeline** (6 points): Defined evaluation timeline, urgency factors present
- **Business Impact** (6 points): Revenue-generating or cost-saving use cases
- **Executive Sponsorship** (7 points): C-level or VP champion identified and engaged

#### **Relationship Factors (20% weight)**
- **Stakeholder Engagement** (5 points): Multiple champions, technical team buy-in
- **Competitive Position** (5 points): Preferred vendor status, differentiation opportunities
- **Implementation Readiness** (5 points): Team capabilities, change management readiness
- **Strategic Alignment** (5 points): Long-term partnership potential, expansion opportunities

### 4.2 ICP Score Interpretation
```
Total ICP Score Calculation:
Score = (Company × 0.25) + (Technical × 0.30) + (Business × 0.25) + (Relationship × 0.20)

Score Categories:
- 80-100: Prime ICP - Ideal fit, fast-track engagement
- 65-79: Strong ICP - Good fit, standard qualification process
- 50-64: Moderate ICP - Requires development, extended nurturing
- 35-49: Weak ICP - Significant gaps, long-term nurture only
- 0-34: Poor ICP - Disqualify or minimal engagement
```

## Step 5: Deal Health Assessment Framework

### 5.1 Overall Deal Health Score (0-100)

#### **Buyer Engagement Score (25 points)**
- **Call Frequency** (5 pts): Regular scheduled meetings maintained
- **Meeting Attendance** (5 pts): Key stakeholders consistently attending
- **Response Time** (5 pts): Timely responses to emails and requests
- **Stakeholder Expansion** (5 pts): Growing circle of engaged contacts
- **Internal Advocacy** (5 pts): Evidence of internal championing

#### **Technical Validation Score (25 points)**
- **POC Success** (10 pts): Successful proof of concept execution
- **Performance Validation** (8 pts): Query performance meeting requirements
- **Integration Success** (4 pts): API/tool integration demonstrated
- **Technical Team Buy-in** (3 pts): Engineering team enthusiasm

#### **Business Case Score (25 points)**
- **ROI Quantification** (8 pts): Clear business case and financial justification
- **Budget Confirmation** (7 pts): Budget authority identified and engaged
- **Use Case Alignment** (5 pts): Primary use case matches Firebolt strengths
- **Success Metrics** (5 pts): Defined KPIs and measurement framework

#### **Process & Timeline Score (25 points)**
- **Decision Process** (8 pts): Clear evaluation and approval process
- **Timeline Realism** (7 pts): Achievable close date based on complexity
- **Procurement Clarity** (5 pts): Budget approval and contracting process defined
- **Competitive Position** (5 pts): Preferred vendor status or differentiation

### 5.2 Deal Health Classification
- **Excellent (90-100)**: Deal on track with strong buying signals
- **Good (75-89)**: Healthy deal with minor areas for attention
- **At Risk (50-74)**: Concerning signals requiring immediate action
- **Critical (25-49)**: Deal in serious jeopardy
- **Lost (0-24)**: Deal likely to be lost without major intervention

### 5.3 Health Assessment by Category

#### **Technical Validation Status**
- **Good (75-100%)**: Successful POC, performance validated, technical team excited
- **Needs Work (40-74%)**: Some technical validation, pending tests, mixed feedback
- **Bad (0-39%)**: No technical validation, failed tests, technical concerns

#### **Business Case Strength**
- **Good (75-100%)**: Clear ROI, budget approved, defined success metrics
- **Needs Work (40-74%)**: Developing business case, budget discussions ongoing
- **Bad (0-39%)**: Unclear ROI, no budget allocation, competing priorities

#### **Stakeholder Engagement**
- **Good (75-100%)**: Multiple champions, executive sponsor, engaged technical team
- **Needs Work (40-74%)**: Single champion, some stakeholder engagement
- **Bad (0-39%)**: Weak champion, limited stakeholder engagement, resistance

#### **Process & Timeline**
- **Good (75-100%)**: Clear decision process, realistic timeline, procurement aligned
- **Needs Work (40-74%)**: Defined process, some timeline challenges
- **Bad (0-39%)**: Unclear process, unrealistic timeline, procurement barriers

## Step 6: Blocker Identification & Risk Assessment

### 6.1 Blocker Identification Matrix

#### **Technical Blockers**
- **High Priority**:
  - Performance requirements not met in testing
  - Integration challenges with existing systems
  - Security/compliance concerns unresolved
  - Technical team resistance or skepticism
  - Missing critical features or functionality

- **Medium Priority**:
  - Incomplete technical evaluation
  - Minor integration adjustments needed
  - Operational complexity concerns
  - Migration complexity and timeline risks

- **Low Priority**:
  - Documentation or training requirements
  - Minor feature gaps with workarounds
  - Timeline coordination challenges
  - Resource allocation questions

#### **Business Blockers**
- **High Priority**:
  - Budget constraints or allocation issues
  - Competing priorities or initiatives
  - ROI concerns or unclear business case
  - Executive sponsor lack of engagement
  - Procurement process barriers

- **Medium Priority**:
  - Legal or contract negotiation delays
  - Success metrics definition needed
  - Change management resistance
  - Timeline misalignment with budget cycles

- **Low Priority**:
  - Team training requirements
  - Implementation coordination
  - Reference customer requests
  - Pricing structure optimization

#### **Relationship Blockers**
- **High Priority**:
  - Weak or missing champion
  - Negative past experiences with vendor
  - Strong competitive vendor preference
  - Organizational politics or conflicts
  - Decision-making authority unclear

- **Medium Priority**:
  - Limited stakeholder access
  - Communication challenges
  - Internal alignment issues
  - Geographic or timezone barriers

- **Low Priority**:
  - Scheduling coordination difficulties
  - Cultural fit considerations
  - Team dynamics optimization
  - Personal relationship factors

### 6.2 Data Location & Architecture Assessment

#### **Current Data Environment**
- **Cloud Platform**: AWS, Azure, GCP, multi-cloud, hybrid infrastructure
- **Data Storage**: S3, Azure Data Lake, BigQuery, Snowflake, Redshift
- **Data Volume**: Current size, growth rate, ingestion patterns, retention needs
- **Data Types**: Structured, semi-structured, streaming, batch processing
- **Access Patterns**: Query frequency, concurrency requirements, latency needs

#### **Integration Requirements**
- **ETL/ELT Tools**: Fivetran, Stitch, Airbyte, custom pipelines, real-time streaming
- **BI Tools**: Tableau, Looker, Power BI, Grafana, custom dashboards
- **APIs**: REST APIs, GraphQL, custom integrations, webhook requirements
- **Programming Languages**: Python, Java, Node.js, Go, .NET support needs
- **Workflow Orchestration**: Airflow, Prefect, Dagster, custom schedulers

## Step 7: Strategic Recommendations & Action Planning

### 7.1 Engagement Strategy by ICP Score

#### **Prime ICP (80-100) - Fast-Track Strategy**
- **Immediate Actions**:
  - Executive-level engagement within 24 hours
  - Technical proof of concept scheduled within 1 week
  - Solutions engineering resources allocated
  - Custom demo with customer data prepared
  - Senior leadership introduction scheduled

- **Success Metrics**:
  - Meeting attendance and engagement quality
  - Technical validation milestones achieved
  - Business case development progress
  - Stakeholder expansion and buy-in
  - Executive sponsor engagement level

#### **Strong ICP (65-79) - Standard Qualification**
- **Immediate Actions**:
  - Technical evaluation within 1 week
  - Business case development support
  - Stakeholder mapping and expansion
  - Competitive differentiation emphasis
  - Standard POC process initiation

- **Success Metrics**:
  - Technical requirements validation
  - Budget and timeline confirmation
  - Champion strengthening and expansion
  - Procurement process engagement
  - Competitive positioning strength

#### **Moderate ICP (50-64) - Development Required**
- **Immediate Actions**:
  - Education and awareness building
  - Use case development and validation
  - Stakeholder identification and engagement
  - Long-term relationship building focus
  - Value demonstration through content

- **Success Metrics**:
  - Problem awareness and education progress
  - Stakeholder engagement improvement
  - Use case clarity and validation
  - Timeline and budget development
  - Competitive awareness and positioning

#### **Weak/Poor ICP (<50) - Minimal Engagement**
- **Immediate Actions**:
  - Polite qualification and expectation setting
  - Minimal resource allocation
  - Periodic check-ins for status changes
  - Focus resources on higher-priority opportunities
  - Maintain relationship for future opportunities

- **Success Metrics**:
  - Efficient resource utilization
  - Future opportunity monitoring
  - Relationship maintenance quality
  - Requalification triggers identified
  - Referral potential assessment

### 7.2 Deal Health-Based Action Plans

#### **Excellent Health (90-100) - Acceleration Focus**
- **Actions**: Accelerate close timeline, expand deal size, secure executive references
- **Resources**: Maintain current team, add implementation planning support
- **Timeline**: Maintain or accelerate current close date
- **Success Metrics**: On-time close, reference agreement, expansion discussions

#### **Good Health (75-89) - Standard Progression**
- **Actions**: Continue standard sales process, monitor for acceleration opportunities
- **Resources**: Current team allocation, periodic management check-ins
- **Timeline**: Maintain current timeline with optimization opportunities
- **Success Metrics**: Progression through stages, stakeholder engagement, technical validation

#### **At Risk (50-74) - Intervention Required**
- **Actions**: Address specific risks, strengthen relationships, clarify value proposition
- **Resources**: Additional SE support, management engagement, competitive analysis
- **Timeline**: Realistic timeline adjustment, milestone-based progression
- **Success Metrics**: Risk mitigation progress, relationship strengthening, clarity improvement

#### **Critical (25-49) - Recovery Mode**
- **Actions**: Executive intervention, deal restructuring, pilot programs
- **Resources**: Senior leadership engagement, custom solutions, flexible terms
- **Timeline**: Extended timeline, phased approach, proof-of-value focus
- **Success Metrics**: Relationship recovery, renewed engagement, pilot success

#### **Lost (<25) - Salvage Operations**
- **Actions**: Graceful disqualification, relationship preservation, competitive intelligence
- **Resources**: Minimal continued investment, relationship maintenance only
- **Timeline**: Deal disqualification or major timeline reset
- **Success Metrics**: Future opportunity preservation, referral potential, lessons learned

### 7.3 Blocker Mitigation Strategies

#### **Technical Blocker Resolution**
- **Performance Concerns**: Extended POC, comprehensive benchmarking, reference customers
- **Integration Challenges**: Technical workshops, proof of concept, partner ecosystem support
- **Security/Compliance**: Documentation review, certification sharing, security deep dive
- **Feature Gaps**: Roadmap alignment, workaround solutions, timeline commitments

#### **Business Blocker Resolution**
- **Budget Constraints**: ROI analysis, phased implementation approach, flexible pricing models
- **Competing Priorities**: Executive alignment sessions, business case strengthening
- **ROI Concerns**: Customer success stories, detailed benchmarking, pilot programs
- **Procurement Delays**: Process acceleration support, relationship leverage

#### **Relationship Blocker Resolution**
- **Weak Champion**: Stakeholder expansion strategy, success story sharing, value demonstration
- **Competitive Preference**: Differentiation emphasis, unique value proposition, third-party validation
- **Organizational Politics**: Executive engagement, neutral facilitation, consensus building
- **Access Limitations**: Multiple touchpoint strategy, relationship building, referral requests

## Step 8: Execution & Monitoring (ExecutionAgent)

### 8.1 Assessment Documentation
- **ICP Score**: Detailed scoring with category breakdown and justification
- **Opportunity Classification**: Type, use case, competitive context, timeline
- **Deal Health Status**: Overall assessment with specific area ratings and trends
- **Blocker Analysis**: Prioritized list with specific mitigation strategies and owners
- **Recommended Actions**: Specific next steps with owners, timelines, and success metrics

### 8.2 Stakeholder Communication
- **Internal Updates**: Sales team briefings, management reporting, technical team coordination
- **Customer Follow-up**: Next steps confirmation, resource allocation, timeline agreement
- **Cross-functional Alignment**: Marketing support, customer success preparation, product coordination
- **Escalation Protocols**: Management involvement triggers, expert resource requests

### 8.3 4-Part Deal Review Analysis Framework

**For deal status and probability assessment queries, structure response with:**

#### **1. True Deal Probability Assessment**
- Cross-reference AE-stated probability with actual engagement evidence from calls
- Validate MEDDPICC completion against real stakeholder involvement patterns
- Assess decision timeline realism based on process insights from conversations
- **Output**: Realistic probability percentage with specific justification

#### **2. Risk Analysis** (Technical, Engagement, Competition, Process)
- **Technical Risks**: Unresolved objections, integration concerns, performance questions from calls
- **Engagement Risks**: Stakeholder accessibility, champion strength, decision maker involvement
- **Competitive Risks**: Threats mentioned in calls, pricing pressure, alternative evaluations
- **Process Risks**: Unclear criteria, extended timelines, procurement challenges
- **Output**: Prioritized risk list with specific evidence from SFDC and call data

#### **3. Opportunity Analysis**
- Expansion potential beyond initial use case (from calls and SFDC notes)
- Strong technical alignment and demonstrated value recognition
- Champion advocacy and internal selling capability evidence
- Favorable competitive positioning demonstrated in conversations
- **Output**: Specific opportunities with supporting evidence

#### **4. Bottom Line & Next Steps**
- **Clear Probability**: Final assessment with confidence level
- **Priority Actions**: Specific next steps to advance the deal
- **Risk Mitigation**: Immediate actions to address top risks
- **Timeline**: Realistic expectations with key milestones
- **Output**: Actionable recommendations with ownership and timing

### 8.4 Data Conflict Resolution Guidelines

**When SFDC data conflicts with call insights:**
- **Prioritize**: Recent call data and actual stakeholder behavior
- **Flag**: Discrepancies for sales team attention and follow-up
- **Weight**: Technical conversations and decision maker engagement heavily
- **Document**: Specific examples of conflicts for coaching opportunities

### 8.5 Success Metrics & KPIs

#### **Assessment Quality Metrics**
- **Completeness**: Percentage of discovery framework coverage achieved
- **Accuracy**: Validation of assumptions and data quality scores
- **Stakeholder Coverage**: Number and quality of stakeholder interactions
- **Competitive Intelligence**: Depth and accuracy of competitive analysis

#### **Process Efficiency Metrics**
- **Time to Complete**: Assessment cycle time from initiation to completion
- **Resource Utilization**: Effort required versus opportunity value potential
- **Conversion Rates**: Assessment to qualified opportunity progression rates
- **Predictive Accuracy**: Correlation between assessment scores and actual outcomes

#### **Business Impact Metrics**
- **Pipeline Quality**: Conversion rates by ICP score and health assessment
- **Sales Velocity**: Time from discovery to close by assessment category
- **Win Rates**: Success rates by opportunity type, ICP score, and health rating
- **Revenue Attribution**: Pipeline and closed-won revenue from assessed opportunities

## Assessment Summary Template

### **Company**: [COMPANY_NAME]
### **Opportunity**: [OPPORTUNITY_NAME]
### **Assessment Date**: [DATE]
### **Assessment Owner**: [OWNER]

#### **ICP Alignment Score**: [X/100]
- Company Characteristics: [X/25]
- Technical Requirements: [X/30]
- Business Fit: [X/25]
- Relationship Factors: [X/20]

#### **Deal Health Score**: [X/100]
- Buyer Engagement: [X/25]
- Technical Validation: [X/25]
- Business Case: [X/25]
- Process & Timeline: [X/25]

#### **Opportunity Classification**: [TYPE]
- **Primary Use Case**: [USE_CASE]
- **Migration/Expansion/Greenfield**: [CATEGORY]
- **Competitive Context**: [COMPETITIVE_SITUATION]
- **Data Location**: [CURRENT_ENVIRONMENT]

#### **Discovery Assessment Results**:
- **What to Keep**: [KEY_STRENGTHS]
- **What to Stop**: [INEFFICIENCIES_TO_ADDRESS]
- **What to Change**: [IMPROVEMENT_OPPORTUNITIES]
- **ICP Positioning**: [STRATEGIC_ALIGNMENT]

#### **Key Blockers Identified**:
1. [HIGH_PRIORITY_BLOCKER] - [MITIGATION_STRATEGY] - [OWNER] - [TIMELINE]
2. [MEDIUM_PRIORITY_BLOCKER] - [MITIGATION_STRATEGY] - [OWNER] - [TIMELINE]
3. [LOW_PRIORITY_BLOCKER] - [MITIGATION_STRATEGY] - [OWNER] - [TIMELINE]

#### **Recommended Strategy**: [STRATEGY_CATEGORY]
#### **Next Steps**:
1. [ACTION_ITEM] - [OWNER] - [TIMELINE] - [SUCCESS_METRIC]
2. [ACTION_ITEM] - [OWNER] - [TIMELINE] - [SUCCESS_METRIC]
3. [ACTION_ITEM] - [OWNER] - [TIMELINE] - [SUCCESS_METRIC]

#### **Success Metrics**:
- [METRIC_1]: [TARGET] - [MEASUREMENT_METHOD]
- [METRIC_2]: [TARGET] - [MEASUREMENT_METHOD]
- [METRIC_3]: [TARGET] - [MEASUREMENT_METHOD]

This comprehensive deal assessment workflow integrates discovery, health analysis, and strategic planning into a unified framework for evaluating and advancing opportunities effectively.