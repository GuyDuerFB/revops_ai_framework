# Churn Risk Logic and Customer Health Assessment

## Churn Risk Scoring Framework

### Risk Score Calculation (0-100 scale)
- **0-25: Low Risk** - Healthy, growing customers with strong engagement
- **26-50: Medium Risk** - Stable customers with some warning indicators  
- **51-75: High Risk** - Declining customers requiring intervention
- **76-100: Critical Risk** - Immediate churn risk requiring executive intervention

## Risk Factors by Customer Type

### Commit Customer Risk Factors

#### Usage-Based Indicators (40% weight)
- **Consumption Decline**: >30% decrease in monthly FBU usage
- **Query Frequency**: <50% of historical daily query volume
- **Feature Abandonment**: Stopping use of previously adopted advanced features
- **Efficiency Degradation**: Increasing cost per query without optimization

#### Engagement Indicators (25% weight)  
- **Support Escalation**: 3+ P1/P2 tickets in 30 days
- **Response Delays**: Slow response to support or account team outreach
- **Meeting Avoidance**: Declining QBRs, health checks, or renewal discussions
- **Champion Changes**: Key technical or business sponsor departures

#### Business Indicators (25% weight)
- **Budget Constraints**: Discussions about cost reduction or budget cuts
- **Strategy Shifts**: Technology consolidation or vendor reduction initiatives  
- **Competitive Evaluation**: Active evaluation of alternative solutions
- **Contract Utilization**: <60% of committed spend utilization

#### Contract Indicators (10% weight)
- **Renewal Proximity**: <90 days to renewal with no renewal discussions
- **Payment Issues**: Late payments or billing disputes
- **Legal Issues**: Contract modification requests or termination discussions
- **Procurement Changes**: New procurement requirements or approval processes

### PLG Customer Risk Factors

#### Usage Trajectory (50% weight)
- **Spending Decline**: 50%+ decrease in monthly billing
- **Usage Gaps**: 14+ days without query activity
- **Single User Pattern**: Only 1 active user after 60+ days
- **Basic Usage Only**: No adoption of optimization features

#### Implementation Progress (30% weight)
- **Stalled Onboarding**: No progress in 30+ days
- **Technical Blockers**: Unresolved data loading or integration issues
- **Performance Issues**: Consistent query timeouts or errors
- **Limited Data**: Only using sample/test datasets after 60 days

#### Team Engagement (20% weight)
- **No Team Expansion**: Single user account after 90+ days
- **Support Disengagement**: Not responding to success outreach
- **Feature Rejection**: Declining training or optimization assistance
- **Budget Uncertainty**: No discussions about future spend or scaling

### Prospect Risk Factors

#### Trial Engagement (60% weight)
- **Low Credit Usage**: <30% credit utilization after 30 days
- **Minimal Queries**: <5 queries per week during active trial
- **No Data Loading**: Only using sample datasets provided
- **Single Session**: Long gaps between login sessions

#### Technical Progress (25% weight)
- **Setup Issues**: Unable to connect data sources or load data
- **Query Failures**: High error rates in submitted queries
- **No Optimization**: Not using indexes or performance features
- **Limited Exploration**: Only basic SELECT queries

#### Sales Engagement (15% weight)
- **Meeting Avoidance**: Declining demo requests or technical discussions
- **No Timeline**: Vague or undefined evaluation timeline
- **Budget Unclear**: No discussions about budget or procurement process
- **Competition**: Active evaluation of alternative solutions

## Early Warning System

### Automated Risk Detection
- **Daily Monitoring**: Query volume, error rates, user activity
- **Weekly Analysis**: Spending trends, feature usage, support engagement
- **Monthly Assessment**: Overall health score calculation and trend analysis
- **Quarterly Review**: Comprehensive risk assessment and intervention planning

### Risk Score Changes
- **Rapid Escalation**: 20+ point increase in 30 days triggers immediate review
- **Trending Risk**: Consistent monthly increases require intervention planning
- **Critical Threshold**: Scores >75 trigger executive team notification
- **Improvement Tracking**: Score decreases indicate successful intervention

## Intervention Strategies by Risk Level

### Low Risk (0-25) - Maintenance Mode
- **Cadence**: Quarterly check-ins, success metrics tracking
- **Actions**: Optimization recommendations, feature education, expansion planning
- **Ownership**: Customer Success Manager (CSM) led
- **Success Metrics**: Usage growth, feature adoption, satisfaction scores

### Medium Risk (26-50) - Proactive Management
- **Cadence**: Monthly check-ins, usage review, health score monitoring
- **Actions**: Technical optimization, training sessions, business value reinforcement
- **Ownership**: CSM with Sales Engineering support
- **Success Metrics**: Risk score stabilization, usage trend improvement

### High Risk (51-75) - Active Intervention
- **Cadence**: Bi-weekly check-ins, executive engagement, success planning
- **Actions**: Dedicated technical support, business case refresh, contract optimization
- **Ownership**: CSM + AE + Management escalation
- **Success Metrics**: Risk score reduction, renewed engagement, commitment extension

### Critical Risk (76-100) - Executive Intervention
- **Cadence**: Weekly monitoring, daily communication during intervention
- **Actions**: Executive sponsorship, custom solutions, retention incentives
- **Ownership**: C-level engagement, dedicated war room approach
- **Success Metrics**: Churn prevention, contract retention, relationship recovery

## Customer Health Indicators

### Positive Health Signals
- **Usage Growth**: Consistent month-over-month consumption increases
- **Feature Adoption**: Regular adoption of new capabilities and optimizations
- **Team Expansion**: Additional users and broader organizational adoption
- **Proactive Engagement**: Customers initiating optimization or expansion discussions

### Neutral Health Signals  
- **Stable Usage**: Consistent consumption without significant growth or decline
- **Regular Engagement**: Standard cadence of support and success interactions
- **Predictable Patterns**: Expected seasonal or cyclical usage variations
- **Maintenance Mode**: Established, optimized usage with minimal changes

### Negative Health Signals
- **Usage Decline**: Consistent decreases in consumption or activity
- **Disengagement**: Reduced responsiveness to outreach and support
- **Technical Issues**: Unresolved performance, cost, or functionality problems
- **Business Changes**: Budget cuts, team reductions, or strategic shifts

## Industry-Specific Risk Factors

### Technology/SaaS Customers
- **High Risk**: Funding issues, competitive pressure, rapid scale requirements
- **Medium Risk**: Engineering team changes, technology stack consolidation
- **Monitoring**: Burn rate, headcount changes, competitive moves

### Financial Services
- **High Risk**: Regulatory changes, compliance requirements, cost pressure
- **Medium Risk**: Merger/acquisition activity, system modernization projects
- **Monitoring**: Regulatory announcements, industry consolidation, budget cycles

### Retail/E-commerce
- **High Risk**: Seasonal performance, supply chain issues, consumer demand shifts
- **Medium Risk**: Peak season preparation, inventory management changes
- **Monitoring**: Seasonal patterns, macroeconomic indicators, consumer trends

## Churn Prevention Playbooks

### Technical Intervention Playbook
1. **Performance Optimization**: Query tuning, index recommendations, architecture review
2. **Cost Optimization**: Right-sizing engines, storage optimization, efficiency improvements
3. **Feature Training**: Advanced capabilities education, best practices sharing
4. **Integration Support**: API usage, tool integrations, workflow optimization

### Business Intervention Playbook
1. **Value Demonstration**: ROI quantification, business case refresh, success metrics
2. **Executive Alignment**: C-level meetings, strategic planning sessions, roadmap alignment
3. **Contract Flexibility**: Term adjustments, payment flexibility, pilot expansions
4. **Success Planning**: Milestone definition, success metrics, regular progress reviews

### Relationship Intervention Playbook
1. **Champion Development**: Multi-threading relationships, advocate identification
2. **Executive Sponsorship**: Senior leader engagement, relationship building
3. **Community Engagement**: User groups, advisory boards, beta programs
4. **Recognition Programs**: Customer success stories, speaking opportunities, awards