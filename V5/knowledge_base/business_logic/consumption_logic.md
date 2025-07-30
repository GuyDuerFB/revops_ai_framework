# Consumption Logic and Usage Patterns

## Consumption Patterns by Customer Type

### Commit Customer Consumption
- **Pattern**: Steady, predictable production workloads
- **Characteristics**: High FBU efficiency, consistent daily usage, optimized queries
- **Typical Range**: $10K-$100K+ monthly consumption
- **Usage Behavior**: 
  - Business hours heavy (9 AM - 6 PM weekdays)
  - Month-end spikes for reporting workloads
  - Optimized query patterns and caching usage
  - Multi-engine deployments for workload separation

### PLG Customer Consumption
- **Pattern**: Growing, experimental, implementation-focused
- **Characteristics**: Variable efficiency, learning curve, scaling usage
- **Typical Range**: $200-$5K monthly consumption  
- **Usage Behavior**:
  - Irregular patterns during implementation
  - Testing and proof-of-concept workloads
  - Single engine deployments initially
  - Query optimization learning curve

### Prospect Consumption
- **Pattern**: Trial evaluation, proof-of-concept focused
- **Characteristics**: Low volume, exploratory queries, sample datasets
- **Typical Range**: $0-$200 (free credits)
- **Usage Behavior**:
  - Burst usage during active evaluation
  - Small dataset testing
  - Feature exploration and demos
  - Time-boxed evaluation periods

## Consumption Health Indicators

### Healthy Consumption Patterns
- **Growth Trajectory**: Steady month-over-month increase (20-50% for PLG, 10-30% for Commit)
- **Efficiency Improvement**: Decreasing FBU per query over time as optimization improves
- **Consistency**: Regular daily usage without extended gaps
- **Feature Adoption**: Usage of advanced features (indexes, aggregating indexes, etc.)

### Warning Signs
- **Declining Usage**: 30%+ drop in monthly consumption without explanation
- **Efficiency Degradation**: Increasing FBU per query indicating optimization issues
- **Irregular Patterns**: Long gaps in usage or inconsistent weekly patterns
- **Limited Features**: Only using basic features after 60+ days

### Critical Issues
- **Usage Cliff**: 70%+ drop in consumption indicating potential churn
- **Zero Usage**: No queries for 14+ days for paying customers
- **Error Spikes**: High query failure rates indicating technical issues
- **Cost Shock**: Sudden 3x+ increase in costs without usage growth

## Consumption Benchmarks and Thresholds

### PLG→Commit Conversion Indicators
- **Spending Velocity**: Reaching $2K+ monthly spend consistently
- **Usage Consistency**: 90+ consecutive days with query activity
- **Team Adoption**: 3+ users actively querying in the organization
- **Workload Maturity**: Production-like query patterns and optimization

### Expansion Opportunity Indicators
- **High Utilization**: Approaching or exceeding contracted consumption levels
- **Consistent Growth**: 3+ months of increasing usage trends
- **Advanced Features**: Adoption of premium capabilities and enterprise features
- **Multi-Engine Usage**: Scaling to multiple engines for workload separation

### Churn Risk Indicators
- **Usage Decline**: 50%+ decrease in consumption over 30 days
- **Support Escalation**: Multiple performance or cost-related support tickets
- **Feature Abandonment**: Stopping use of previously adopted advanced features
- **Team Contraction**: Reduction in active users or query frequency

## Consumption Optimization Strategies

### For Commit Customers
- **Efficiency Programs**: Query optimization consultations, index recommendations
- **Capacity Planning**: Right-sizing engines and storage for optimal cost/performance
- **Feature Adoption**: Introduce advanced capabilities to improve efficiency
- **Usage Analytics**: Regular consumption reviews and optimization opportunities

### For PLG Customers
- **Implementation Support**: Guidance on best practices and optimization techniques
- **Success Milestones**: Structured onboarding with consumption growth targets
- **Feature Education**: Training on efficiency features and cost optimization
- **Conversion Preparation**: Proactive outreach as usage approaches enterprise levels

### For Prospects
- **Trial Optimization**: Ensure meaningful evaluation within credit limits
- **Quick Wins**: Help achieve early success and value demonstration
- **Use Case Expansion**: Guide exploration of additional relevant use cases
- **Success Metrics**: Track engagement and progress toward conversion

## Temporal Consumption Analysis

### Day-of-Week Patterns
- **Business Days**: 80% of usage typically occurs Monday-Friday
- **Weekend Usage**: Production workloads may run scheduled jobs
- **Time Zone Distribution**: Global customers create 24/7 usage patterns
- **Holiday Impact**: Reduced usage during major holidays and company shutdowns

### Usage Forecasting
- **Growth Projections**: Based on historical patterns and customer lifecycle stage
- **Capacity Planning**: Predict infrastructure needs based on consumption trends
- **Budget Planning**: Help customers forecast costs based on usage trajectory
- **Resource Allocation**: Optimize engine sizing and storage allocation