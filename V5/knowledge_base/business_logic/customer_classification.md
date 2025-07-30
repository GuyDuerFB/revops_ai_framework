# Customer Classification System

## Customer Types

### Commit Customers
- **Definition**: Signed formal contracts, paying from own resources
- **Salesforce Indicator**: `sf_account_type_custom = 'Commit Customer'`
- **Revenue Impact**: Primary revenue source (typically 70-80% of total)
- **Usage Patterns**: Production workloads, established consumption
- **Analysis Focus**: Retention, expansion, contract renewals, efficiency

### PLG Customers  
- **Definition**: Exhausted $200 credits, usage-based billing, no formal contract
- **Salesforce Indicator**: `sf_account_type_custom = 'PLG Customer'`
- **Revenue Impact**: Growth revenue (15-25% of total)
- **Usage Patterns**: Implementation, scaling, experimentation
- **Analysis Focus**: Conversion readiness, growth velocity, feature adoption

### Prospects
- **Definition**: Free credits remaining, no payment method, or early sales process
- **Salesforce Indicator**: `sf_account_type_custom IS NULL OR != 'Commit Customer' AND != 'PLG Customer'`
- **Revenue Impact**: Pipeline potential (0% current revenue)
- **Usage Patterns**: Trial usage, evaluation workloads
- **Analysis Focus**: Activation rates, conversion funnel, trial effectiveness

## Conversion Thresholds
- **PLG→Commit Triggers**: $2K+ monthly spend, 90+ day usage, multi-user adoption
- **Prospect→PLG Triggers**: $200 credit exhaustion + payment method connection
- **Typical Progression**: 45 days prospect→PLG, 127 days PLG→commit