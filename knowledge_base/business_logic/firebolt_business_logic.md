# Firebolt Business Logic and Customer Lifecycle

## Customer Classification System

Understanding customer types is critical for accurate RevOps analysis, forecasting, and strategic decision-making. Each customer type represents a different stage in the Firebolt journey with distinct characteristics, behaviors, and business implications.

## Customer Types

### 1. Commit Customers

**Definition**: Customers who have signed a formal commitment deal with Firebolt and are paying from their own financial resources.

**Characteristics**:
- Signed a formal contract with Firebolt (typically 6-12+ month commitments)
- Have moved beyond trial/proof-of-concept phase
- Paying with established payment methods (credit card, wire transfer, purchase orders)
- Usually have dedicated Firebolt account teams (AE, CSM, Solutions Engineer)
- Have completed technical implementation and onboarding
- Consuming Firebolt services at production or near-production levels

**Business Indicators**:
- `sf_account_type_custom` = 'Commit Customer' in Salesforce
- Active agreements in `agreement_f` table with `is_active` = true
- Regular consumption patterns in `consumption_event_f` and `billing_event_f`
- Contract values typically $50K+ annually
- Closed-Won opportunities in Salesforce

**Revenue Recognition**:
- Primary revenue source for Firebolt
- Predictable, recurring revenue streams
- Usually subject to committed spend minimums
- May have volume discounts or custom pricing

**Analysis Considerations**:
- These customers drive core business metrics (ARR, retention, expansion)
- Consumption patterns indicate product-market fit and customer health
- Churn risk analysis is critical given revenue impact
- Expansion opportunities should be actively monitored
- Success metrics: net retention, consumption growth, contract renewals

### 2. PLG (Product-Led Growth) Customers

**Definition**: Customers who have exhausted their $200 free credits and are paying from their own pocket but have not yet signed a formal commitment deal.

**Characteristics**:
- Started with Firebolt's self-service/trial offering
- Consumed initial $200 in free credits
- Connected payment method and are being charged for usage
- Usually in implementation, testing, or early production phases
- Consumption levels typically lower than Commit Customers
- May not have dedicated account team coverage initially
- Represent potential pipeline for future Commit deals

**Business Indicators**:
- `sf_account_type_custom` = 'PLG Customer' in Salesforce
- Billing records in `billing_event_f` showing post-credit usage
- No active formal agreements (or smaller MSA-type agreements)
- Consumption patterns showing experimentation or gradual ramp
- Payment methods connected in `amberflo_customer_d`

**Revenue Recognition**:
- Pay-as-you-go consumption billing
- Variable monthly revenue based on usage
- Important leading indicator of potential larger deals
- Revenue typically smaller but growing

**Analysis Considerations**:
- Key conversion metric: PLG → Commit Customer progression
- Time-to-value and adoption velocity are critical metrics
- Consumption growth patterns predict likelihood of conversion
- Support and success metrics indicate implementation progress
- Risk: Can churn more easily due to lower commitment
- Success metrics: usage growth, feature adoption, time to first value

**Conversion Triggers**:
- Monthly consumption exceeding certain thresholds ($2K-5K+)
- Sustained usage over 2-3+ months
- Multi-user adoption within the organization
- Production workload deployment
- Request for enterprise features (SSO, advanced security, etc.)

### 3. Prospects

**Definition**: Potential customers who have not yet become paying customers and are in various stages of the early sales/evaluation process.

**Characteristics**:
- Have not exhausted their $200 free credits, OR
- Have not connected a payment method, OR  
- Have not yet registered for Firebolt, OR
- Are in early stages of a sales process

**Sub-Categories**:

#### 3a. Active Trial Prospects
- Registered for Firebolt with $200 free credits
- Actively using/testing the platform
- Credits not yet exhausted
- May be in active sales conversations
- Technical evaluation in progress

#### 3b. Sales-Led Prospects  
- Engaged through traditional sales channels
- May have signed evaluation agreements
- Often larger enterprise deals in progress
- May be testing on dedicated resources/environments
- Usually have dedicated sales team engagement

#### 3c. Early-Stage Prospects
- Marketing qualified leads (MQLs)
- Sales qualified leads (SQLs) in early stages
- Demo requests, whitepaper downloads, event connections
- No active Firebolt usage yet
- Competitive evaluations, budget confirmation phases

**Business Indicators**:
- Salesforce opportunities in early stages (Discovery, Technical Evaluation, etc.)
- `amberflo_customer_d.is_test` = true for trial users
- Low or no consumption in `consumption_event_f`
- Remaining credits in `customer_credit_f`
- Recent registration dates in `organization_d`

**Revenue Recognition**:
- No current revenue contribution
- Represent future pipeline and potential ARR
- Investment stage requiring sales and marketing resources

**Analysis Considerations**:
- Conversion rates from prospect → PLG → Commit Customer
- Time in trial and usage velocity during trial period
- Lead scoring and qualification metrics
- Sales pipeline health and progression rates
- Marketing attribution and channel effectiveness
- Success metrics: trial activation, time to first query, feature usage

## Business Logic Rules

### Customer Lifecycle Progression

The typical customer journey follows this progression:
```
Prospect → PLG Customer → Commit Customer
    ↓           ↓            ↓
Trial     → Pay-as-go   → Contract
$200 free → Usage billing → Committed spend
```

### Revenue Classification

**For Revenue Analysis**:
- **Primary Revenue**: Commit Customer consumption and contract values
- **Growth Revenue**: PLG Customer pay-as-you-go billing  
- **Pipeline Revenue**: Prospect opportunity values (potential/forecasted)

**For Consumption Analysis**:
- **Production Consumption**: Commit Customers (established workloads)
- **Ramping Consumption**: PLG Customers (growing usage patterns)
- **Trial Consumption**: Active Prospects (evaluation usage)

### Customer Health Scoring

**Commit Customers**:
- Usage vs. committed spend ratios
- Monthly consumption trends (growth/decline)
- Support ticket volume and resolution
- Contract renewal proximity and likelihood
- Expansion opportunity indicators

**PLG Customers**:
- Monthly spending velocity ($0-500, $500-2K, $2K+)
- Usage consistency and growth trends
- Feature adoption breadth and depth
- Time since first production workload
- Sales engagement receptivity

**Prospects**:
- Credit consumption rate and pattern
- Time to first value/first query
- Technical evaluation progress
- Sales stage progression velocity
- Competitive displacement likelihood

### Analysis Context Guidelines

**When analyzing revenue**:
- Separate Commit vs PLG revenue for different business insights
- PLG revenue growth indicates pipeline health
- Commit revenue stability indicates customer retention

**When analyzing consumption**:
- Commit Customer patterns indicate product stickiness
- PLG Customer patterns indicate conversion potential
- Prospect patterns indicate product-market fit for trial experience

**When analyzing customer counts**:
- Always specify customer type to avoid misleading aggregations
- "Total customers" should clarify if including prospects/trials
- Growth metrics should separate new vs. expansion within each type

**When analyzing churn**:
- Commit Customer churn has immediate revenue impact
- PLG Customer churn indicates conversion funnel issues
- Prospect churn indicates trial experience or market fit problems

### Sales and Marketing Attribution

**Lead Sources by Customer Type**:
- **Commit Customers**: Often sales-led, enterprise deals, strategic partnerships
- **PLG Customers**: Self-service, content marketing, community, referrals
- **Prospects**: Mixed - both inbound marketing and outbound sales

**Conversion Metrics**:
- Prospect → PLG conversion rate (trial activation)
- PLG → Commit conversion rate (deal signing)
- Time between stages (sales velocity)
- Revenue expansion within each customer type

### Forecasting Considerations

**For Commit Customers**:
- Renewal likelihood and timing
- Expansion potential based on consumption trends
- Churn risk assessment
- Contract value growth patterns

**For PLG Customers**:
- Conversion probability to Commit deals
- Monthly spending progression rates
- Seasonal usage patterns
- Support and success resource requirements

**For Prospects**:
- Trial-to-paid conversion rates
- Pipeline progression probabilities
- Sales cycle length by deal size/type
- Resource requirements for successful conversion

## Integration with Data Analysis

### Required Context for Queries

When DataAgent performs analysis, always consider:

1. **Customer Type Segmentation**: Break down metrics by Commit/PLG/Prospect
2. **Lifecycle Stage**: Where customers are in their journey
3. **Business Impact**: Revenue contribution and strategic importance
4. **Temporal Context**: Seasonal patterns, billing cycles, contract dates
5. **Conversion Funnels**: Movement between customer types

### Key Business Questions by Customer Type

**Commit Customers**:
- Are consumption patterns healthy and growing?
- What's the renewal likelihood based on usage trends?
- Which customers show expansion or churn risk?
- How does actual consumption compare to committed spend?

**PLG Customers**:
- Which PLG customers are ready for Commit deal conversations?
- What usage patterns indicate successful implementation?
- How long does PLG→Commit conversion typically take?
- What consumption thresholds predict conversion success?

**Prospects**:
- How effective is our trial experience at driving activation?
- Which prospect segments convert best to paying customers?
- What early usage patterns predict long-term success?
- How can we improve trial-to-paid conversion rates?

### Data Quality and Mapping

**Salesforce Account Type Mapping**:
- `sf_account_type_custom` = 'Commit Customer': Full contract customers
- `sf_account_type_custom` = 'PLG Customer': Self-service paying customers  
- Other values or NULL: Likely prospects or unclassified

**Billing and Usage Correlation**:
- Commit Customers: Regular billing aligned with contract terms
- PLG Customers: Variable billing based on consumption patterns
- Prospects: Minimal/no billing, credit consumption tracking

**Customer Journey Tracking**:
- Monitor progression: registration → trial usage → payment → contract
- Track conversion timeframes and success/drop-off points
- Measure customer lifetime value by acquisition type

This business logic should inform all RevOps analysis to ensure accurate customer classification, appropriate benchmarking, and relevant business insights for each customer type.