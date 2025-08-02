# Sales Process and Opportunity Management Logic

## Opportunity Types and Definitions

### New Business Opportunities
**Purpose**: Securing commit deals for new workloads or use cases where Firebolt services have not been previously utilized.

**Sub-Types**:
- **New Business**: First-time customer acquisition with new workloads
- **Upsell**: Increasing contract TCV by adding new features, services, or enhancements beyond original scope

### Renewal Opportunities  
**Purpose**: Extending or expanding existing customer relationships.

**Sub-Types**:
- **Renewal**: Extending existing contract with same terms or minor TCV uplift
- **Expansion**: Increasing contract TCV significantly within the same use case

## New Business Opportunity Stages

### Stage 1: Opportunity Created (0% probability)
**MEDDPICC Requirements**: E (Economic Buyer), I (Identify Pain), C (Champion Identified), C (Competition Identified)

**Description**: New opportunity identified with initial conversation indicating potential business challenge and interest in Firebolt within 12 months.

**Entrance Criteria**:
- Lead or inquiry captured in CRM
- At least one meaningful discussion or inquiry completed
- Clear business pain or reason to explore solution identified
- Account is ICP fit and contact is right persona

**Exit Criteria**:
- Initial MEDDPICC populated (required insights)
- Call notes in Salesforce
- Follow-up call completed (if SDR sourced)

### Stage 2: Discover (10% probability)
**MEDDPICC Requirements**: M (Metrics), I (Identify Pain), D (Decision Process - preliminary), C (Champion), C (Competition)

**Description**: Opportunity validated for seriousness and fit. Business need confirmed, key stakeholders identified, buying process mapping begun.

**Entrance Criteria**:
- Prospect acknowledges pressing need and actively considers solutions
- Preliminary budget, authority, timeline seem viable
- At least one potential champion emerging internally

**Exit Criteria**:
- Agreed Mutual Proof of Concept Success Plan signed off by Champion
- InfoSec requirements understood and path identified
- Discovery and business case development complete

### Stage 3: Proof of Concept (40% probability)
**MEDDPICC Requirements**: E (Economic Buyer), D (Decision Criteria), D (Decision Process)

**Description**: Path to POC established and agreed upon by both sides. Aligning Firebolt capabilities with prospect success criteria.

**Entrance Criteria**:
- Customer agrees to proceed with POC or pilot
- Key stakeholders (including Champion) committed to evaluating results
- Initial success metrics, timelines, decision criteria defined

**Exit Criteria**:
- Technical requirements validated; POC results meet/exceed criteria
- Champion reinforcing Firebolt internally
- Clear understanding of competitive positioning
- POC results ready and readout completed

**Key Milestones**: Tech Win

### Stage 4: Propose (50% probability)
**MEDDPICC Requirements**: All components (M, E, D, D, I, C, C)

**Description**: Customer success criteria validated, technical fit confirmed. Focus on finalizing buying process, involving economic decision-makers, clarifying commercial terms.

**Entrance Criteria**:
- POC successfully concluded with favorable results
- Technical team confirms solution meets requirements
- Internal support established (Champion, Economic Buyer engagement)
- Decision process fully mapped

**Exit Criteria**:
- Draft proposal accepted
- Any remaining technical/functional questions resolved

**Key Milestones**: Business Win, Financial Win

### Stage 5: Negotiate (75% probability)
**MEDDPICC Requirements**: All components plus P (Paper Process fully mapped)

**Description**: Firebolt vendor selected for identified workload with commitment to move into production. Working on path to production.

**Entrance Criteria**:
- Prospect explicitly identifies Firebolt as frontrunner/selected vendor
- Technical, functional, business requirements fully aligned
- Negotiations on pricing and terms in progress

**Exit Criteria**:
- All commercial and legal terms agreed upon in principle
- Economic Buyer and other sign-offs secured or imminent
- Champion driving final internal endorsements

### Stage 6: Signature (90% probability)
**MEDDPICC Requirements**: All components maintained

**Description**: Contractual documents in progress, with some pieces signed or under review. Deal nearly closed pending final approvals.

**Entrance Criteria**:
- Contract, SOW, or legal documents drafted and partially executed or under final review
- Procurement/legal processes nearly complete with minor outstanding items

**Exit Criteria**:
- All agreements and legal requirements fully signed off and logged
- Opportunity moves to "Closed Won"

**Key Milestones**: Legal Win

### Stage 7: Closed Won (100% probability)
**Description**: Commit deal finalized, all required documents and agreements signed.

### Stage 8: Closed Lost (0% probability)
**Description**: Sales process ended without purchase decision in favor of Firebolt.

## Renewal Opportunity Stages

### Stage 1: Open (0% probability)
**Description**: Initial stage for all renewal opportunities. Renewal identified but no significant action taken.

**Entrance Criteria**:
- Renewal date or window identified
- Account flagged for upcoming renewal
- Minimal or no action taken yet

**Exit Criteria**:
- CSM made contact or at least one outreach attempt
- Enough interest/information to proceed to Qualification

### Stage 2: Qualification (10% probability)
**Description**: Gathering information to assess renewal feasibility including customer needs, budget, timeline, decision-making process.

**Entrance Criteria**:
- Initial discussion started
- No formal agreement in progress

**Exit Criteria**:
- CSM confirmed renewal viability (budget, timeline, interest)
- Necessary internal approvals secured or in motion

### Stage 3: Propose (50% probability)
**Description**: Discuss and refine renewal terms including pricing, contract duration, conditions for mutually acceptable agreement.

**Entrance Criteria**:
- Renewal plan shared
- Terms under negotiation

**Exit Criteria**:
- Commercial and legal terms agreed upon in principle
- Economic Buyer and sign-offs secured or imminent

### Stage 4: Negotiate (75% probability)
**Description**: Customer verbally confirmed intention to renew under discussed terms. Strong likelihood of final agreement.

**Entrance Criteria**:
- Verbal confirmation received
- Both parties agree on general structure and content

**Exit Criteria**:
- Agreement sent to contact
- All terms finalized

### Stage 5: Signature (90% probability)
**Description**: Finalized renewal contract delivered to customer for review and signature.

**Entrance Criteria**:
- Contract/legal documents drafted and partially executed or under final review
- Procurement/legal processes nearly complete

**Exit Criteria**:
- All agreements and legal requirements fully signed off
- Opportunity moves to "Closed Won"

### Stage 6: Closed Won (100% probability)
**Description**: Renewal deal finalized, all required documents and agreements signed.

### Stage 7: Closed Lost (0% probability)
**Description**: Renewal process ended without renewal decision in favor of Firebolt.

## POC (Proof of Concept) Process

### POC Structure and Flow
**Purpose**: Win POCs through structured process proving superior performance, demonstrating cost benefits, building customer confidence to commit.

### POC Session Framework

#### Session 1: Getting Started
**Purpose**: Establish initial engagement and set POC foundations
**Duration**: 40 minutes
**Key Activities**:
- Introduction and expectation setting (5 min)
- Discovery questions and use case understanding (5 min)
- Firebolt high-level review (5 min)
- Interactive demo and account setup (20 min)
- Next steps and communication channel setup (5 min)

#### Session 2: Discovery
**Purpose**: Deep technical understanding of prospect's use case
**Duration**: 60 minutes
**Key Activities**:
- End-to-end data flow understanding (35 min)
- Success criteria definition (10 min)
- Next steps and data activation (10 min)
- Pre-call preparation and scoping questions

#### Session 3: Hands-On Working Sessions
**Purpose**: Validate Firebolt capabilities with prospect's actual data
**Duration**: 45 minutes
**Key Activities**:
- Data loading and validation (10 min)
- Query optimization hands-on (25 min)
- Benchmark planning (10 min)
- Multiple sessions possible as evaluation progresses

#### Session 4: POC Validation
**Purpose**: Present POC outcomes including performance and cost analysis
**Key Activities**:
- Benchmark results presentation
- Cost analysis and TCO comparison
- Performance validation against success criteria
- Business case development

#### Session 5: Migration Planning
**Purpose**: Create clear path to production implementation
**Duration**: 60 minutes
**Key Activities**:
- Migration overview and key steps (5 min)
- Technical deep dive (40 min)
- Next steps and action plan (10 min)

### POC Success Criteria
**Technical Validation**:
- Performance improvements demonstrated through benchmarks
- Query optimization with customer data
- Integration capabilities validated

**Business Validation**:
- Clear cost analysis and projections
- ROI quantification and business case
- Migration timeline and resource requirements

**Relationship Building**:
- Champion identification and strengthening
- Stakeholder engagement and buy-in
- Decision process mapping and validation

## MEDDPICC Qualification Framework

### M - Metrics
**Definition**: Quantified business impact and success criteria
**Key Questions**: What metrics define success? How do you measure ROI?

### E - Economic Buyer
**Definition**: Person with budget authority and financial approval power
**Key Questions**: Who controls the budget? Who can say yes to this investment?

### D - Decision Criteria  
**Definition**: Technical and business evaluation criteria for vendor selection
**Key Questions**: How will you evaluate solutions? What are must-have vs. nice-to-have features?

### D - Decision Process
**Definition**: Procurement, legal, and approval workflow
**Key Questions**: What's your evaluation timeline? Who needs to approve this decision?

### P - Paper Process (Later Stages)
**Definition**: Legal, procurement, and contracting requirements
**Key Questions**: What's your procurement process? Who handles contract negotiations?

### I - Identify Pain
**Definition**: Current problems and business drivers requiring solution
**Key Questions**: What's broken today? What happens if you don't solve this?

### C - Champion
**Definition**: Internal advocate with influence and commitment to solution
**Key Questions**: Who will champion this internally? Who benefits most from success?

### C - Competition
**Definition**: Alternative solutions and vendors under consideration
**Key Questions**: What other solutions are you evaluating? What's your status quo?

## Territory and Coverage Model

### Geographic Coverage
**Americas**: United States (state-level assignments), Canada, LATAM
**EMEA**: UK/Ireland, DACH, Nordics, Benelux, Middle East, Africa
**JAPAC**: India (Enterprise and Mid-Market), Rest of APAC

### Account Executive Assignments
**Defined by**: Geographic region with specific state/country assignments
**Overrides**: Special rules for major metros (Bay Area, Texas regions)
**Coverage Principle**: Every region covered by exactly one AE to prevent overlap

## Deal Closing Process

### High-Level Closing Flow
1. **Prepare & Approve Offer**: AE drafts pricing options, secures internal approval
2. **Present & Confirm**: Customer selects pricing tier
3. **Generate Quote & Collect Signature**: Finance issues quote, DocuSign process
4. **Create AWS Offer**: Finance sets up Private Offer in AWS Marketplace
5. **Customer Accepts**: Customer accepts AWS offer
6. **Close Deal**: Automatic invoicing triggered, CRM updated

### Key Stakeholders in Closing
- **AE**: Owns customer communication, offering, DocuSign coordination
- **Regional VP Sales**: Approves initial offer before Finance/Legal review
- **VP Finance**: Approves offers, creates formal quote, creates AWS private offer
- **Customer Procurement/Legal**: Reviews and signs DocuSign agreement
- **Customer Technical/AWS Admin**: Approves AWS Private Offer

### Critical Success Factors
- **Internal Approval**: VP and Finance approval before customer presentation
- **Clear Signer Identification**: Distinguish between DocuSign signer and AWS admin
- **AWS Marketplace Process**: Private offer acceptance triggers invoicing
- **Documentation**: Signed quote and offer acceptance email required for Closed Won

## Opportunity Health Indicators

### Positive Indicators
- **MEDDPICC Complete**: All components identified and validated
- **POC Success**: Technical validation with customer data
- **Champion Strength**: Active internal advocacy and relationship building
- **Decision Process Clarity**: Well-defined evaluation and approval timeline
- **Competitive Position**: Preferred vendor status or clear differentiation

### Risk Indicators
- **Incomplete MEDDPICC**: Missing economic buyer, champion, or decision criteria
- **POC Challenges**: Technical issues, performance gaps, integration problems
- **Stakeholder Changes**: Champion departure, decision maker changes
- **Timeline Pressure**: Unrealistic close dates, rushed evaluation
- **Competitive Threats**: Strong incumbent vendor, compelling alternatives

### Stage Progression Velocity
- **Fast Track**: Accelerated progression through stages (high intent, clear need)
- **Standard**: Normal progression timeline with steady advancement
- **At Risk**: Slow progression, stalled stages, declining engagement
- **Recovery**: Re-engagement after setbacks, relationship rebuilding

## Integration with Customer Classification

### Opportunity Context by Customer Type
- **New Prospects**: Focus on ICP alignment, pain identification, use case validation
- **PLG Customers**: Conversion readiness, usage growth validation, expansion planning
- **Commit Customers**: Renewal preparation, expansion opportunities, relationship deepening

### Revenue Implications
- **New Business**: Customer acquisition, market expansion, competitive wins
- **Upsell**: Customer growth, additional use cases, platform expansion
- **Renewal**: Revenue retention, relationship continuation, churn prevention
- **Expansion**: Revenue growth, deeper platform adoption, strategic partnership