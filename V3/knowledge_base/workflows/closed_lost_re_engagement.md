# Closed-Lost Re-engagement Workflow

## Overview
This workflow analyzes closed-lost deals to determine why they were lost and generates personalized win-back strategies for re-engagement.

## Trigger Conditions
- Deal status changes to "Closed-Lost" in Salesforce
- Manual analysis request for specific closed-lost opportunities
- Quarterly review of closed-lost deals for re-engagement opportunities

## Data Sources Required
- **Salesforce**: Opportunity details, close reason, competitor information, timeline
- **Gong**: Call recordings and analysis from the sales cycle
- **Firebolt**: Historical usage data if prospect was in trial/POC
- **External Research**: Company updates, funding events, leadership changes

## Analysis Framework

### 1. Loss Reason Analysis
**Primary Loss Categories:**
- **Price/Budget**: Lost due to pricing concerns or budget constraints
- **Feature Gap**: Missing functionality or technical requirements
- **Timing**: Wrong timing for prospect's priorities or budget cycle
- **Competition**: Lost to competitor solution
- **Internal Champion**: Lost internal advocate or decision-maker changes
- **Technical Fit**: Solution didn't meet technical requirements
- **Trust/Relationship**: Relationship or trust issues

**Analysis Process:**
1. Extract close reason from Salesforce opportunity
2. Analyze Gong call sentiment and objection patterns
3. Review timeline for deal velocity issues
4. Identify decision-maker changes or organizational shifts
5. Compare against winning deal patterns for similar prospects

### 2. Re-engagement Timing Strategy
**Immediate Re-engagement (0-3 months):**
- Price/budget objections with new budget cycles
- Feature gaps that have been addressed in product updates
- Decision-maker changes with new stakeholders

**Medium-term Re-engagement (3-6 months):**
- Timing-related losses with changed business priorities
- Competitive losses where competitor may have under-delivered
- Technical fit issues with evolved requirements

**Long-term Re-engagement (6-12 months):**
- Major organizational changes or new leadership
- Significant product enhancements addressing previous gaps
- Market condition changes affecting priorities

### 3. Win-back Message Framework
**Message Components:**
1. **Acknowledgment**: Recognize the previous decision and timeline
2. **What's Changed**: Highlight relevant changes since last conversation
3. **Value Proposition**: Updated value based on current situation
4. **Social Proof**: Similar customer success stories
5. **Low-commitment Next Step**: Easy way to re-engage

## Workflow Steps

### Step 1: Data Collection and Analysis
```
Action: Gather comprehensive deal history
- Salesforce opportunity record and activity history
- Gong call recordings and sentiment analysis
- Email thread analysis for objection patterns
- Competitive intelligence from sales notes
- Current company status and recent developments
```

### Step 2: Loss Categorization
```
Action: Categorize the primary loss reason
- Apply loss reason framework to available data
- Score confidence level in loss reason assessment
- Identify secondary contributing factors
- Document decision-maker timeline and changes
```

### Step 3: Re-engagement Readiness Assessment
```
Action: Evaluate re-engagement potential
Scoring Criteria:
- Company growth/funding events (+2 points)
- Decision-maker changes (+1 point)  
- Product updates addressing gaps (+2 points)
- Competitor issues/dissatisfaction (+1 point)
- Budget cycle alignment (+1 point)
- Relationship warmth maintained (+1 point)

Threshold: 4+ points = High priority, 2-3 = Medium, <2 = Low
```

### Step 4: Win-back Strategy Development
```
Action: Create personalized re-engagement approach
- Select optimal timing based on loss reason
- Craft message addressing specific loss factors
- Identify best messenger (AE, SE, executive)
- Recommend engagement channel (email, LinkedIn, call)
- Suggest value-add content or insights to include
```

### Step 5: Message Generation
```
Action: Draft win-back communication
Template Structure:
1. Personal acknowledgment of previous process
2. Brief update on what's changed (company/product)
3. Specific value proposition for their situation
4. Social proof relevant to their industry/use case
5. Soft ask for brief conversation or coffee chat
6. Easy out if timing still isn't right
```

## Success Metrics
- **Re-engagement Rate**: % of contacted prospects who respond
- **Meeting Conversion**: % of responses that convert to meetings
- **Opportunity Creation**: % of meetings that become new opportunities
- **Win Rate**: % of re-engaged opportunities that close-won
- **Time to Re-engagement**: Average days from loss to first response

## Sample Output

### Analysis Summary
```
Company: DataTech Solutions
Original Loss Date: 2024-03-15
Loss Reason: Feature Gap (Real-time analytics capabilities)
Re-engagement Score: 6/7 (High Priority)

Key Changes Since Loss:
- Firebolt launched real-time streaming analytics (April 2024)
- DataTech raised $50M Series B (June 2024)
- Original champion Sarah Johnson promoted to VP of Data

Recommended Timing: Immediate (within 2 weeks)
Recommended Messenger: Original AE with SE support
```

### Win-back Message Draft
```
Subject: Real-time Analytics Update for DataTech

Hi Sarah,

Congratulations on your recent promotion to VP of Data and DataTech's Series B! 

I wanted to reach out because I know real-time analytics capabilities were a key requirement when we last spoke in March. I'm excited to share that we've since launched our streaming analytics platform that addresses exactly what you were looking for.

I'd love to show you how companies like Acme Corp (similar size, same industry) are now getting sub-second insights from their data streams. Would you be open to a brief 20-minute conversation to see if there's potential value now that your priorities and our capabilities have evolved?

No pressure if the timing still isn't right - I just didn't want you to miss this update given our previous discussions.

Best regards,
[AE Name]
```

## Integration Points
- **Salesforce**: Update opportunity record with re-engagement status and timeline
- **Gong**: Schedule follow-up call recording for analysis
- **Marketing Automation**: Add to targeted nurture campaigns
- **Success Metrics**: Track re-engagement funnel metrics in dashboard

## Escalation Triggers
- High-value prospects (>$500K ARR potential) get executive involvement
- Multiple failed re-engagement attempts require strategy review
- Competitive intelligence suggests dissatisfaction with chosen vendor