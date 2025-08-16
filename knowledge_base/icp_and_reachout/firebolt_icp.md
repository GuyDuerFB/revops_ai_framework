# Firebolt Ideal Customer Profile (ICP)

## Executive Summary

Firebolt targets **digital native companies, startups, and high-growth companies** that need high-performance, low-latency analytics for customer-facing applications and AI workloads. These organizations require sub-second query performance with extreme concurrency while maintaining cost efficiency.

*Last updated: August 2025 - IAM permissions fixed*

## Company Profile

### Company Characteristics
- **Type**: Digital native companies, startups, and high-growth companies
- **Size**: 50 to 5,000 employees (sweet spot: 200-1,000 employees)
- **Regions**: Americas, EMEA, JAPAC
  - **Primary Focus**: United States, United Kingdom, India, Israel
  - **Cloud Focus**: AWS (primary), Azure, GCP

### Industries (In Scope)
- **Software** - SaaS platforms, developer tools, cloud services
- **Business Products and Services** - B2B software, professional services
- **IT Services** - System integrators, managed services, consulting
- **Advertising and Marketing** - AdTech, MarTech, digital agencies
- **Financial Services** - Fintech, digital banking, trading platforms
- **Retail** - E-commerce, digital marketplaces, omnichannel retail
- **Artificial Intelligence** - AI/ML platforms, GenAI applications
- **E-Commerce** - Online retail, marketplace platforms, digital commerce

### Industries (Excluded)
- Traditional Manufacturing
- Consumer Goods
- Government and Public Services
- Energy and Utilities
- Traditional Transportation and Logistics
- Legacy Media and Entertainment

**Exception**: Digital or AI-native companies in excluded industries may qualify

### High-Value Cohorts
- **Cloud 100** - Top 100 private cloud companies (Forbes ranking)
- **AI 100** - Leading private AI companies (CB Insights)
- **Unicorns** - Private companies valued at $1B+
- **VC-Funded** - Companies backed by VCs that have also funded Firebolt
- **Inc. 5000** - Fastest growing private US companies (Inc. magazine)

### Qualifying Technical Criteria
- **Performance Pain**: Need sub-second query performance
- **Concurrency**: 50+ concurrent users or 100+ QPS requirements
- **Data Scale**: 1TB+ datasets or daily ingestion >500GB
- **Growth**: Data/user growth >100% annually
- **Use Cases**: Customer-facing analytics, embedded dashboards, AI applications

### Primary Use Cases

#### Customer-Facing Analytics
- **Embedded Dashboards:** SaaS platforms with analytics for 1,000+ end users
- **Real-time Personalization:** E-commerce recommendation engines updating with user behavior
- **API-driven Analytics:** Serving thousands of API requests/second with sub-150ms response
- **Multi-tenant Analytics:** Performance isolation across customer base
- **Live Leaderboards:** Gaming platforms with millions of concurrent players

#### AI/GenAI Applications
- **RAG Systems:** Document retrieval, customer support chatbots, knowledge bases
- **Semantic Search:** Content discovery, product recommendations, research platforms
- **AI Copilots:** Code assistance, business intelligence, data exploration
- **Real-time AI:** Fraud detection, recommendation engines, dynamic pricing
- **Conversational Analytics:** Natural language to SQL, chat-based BI
- **Hybrid Retrieval:** Vector similarity combined with structured metadata queries

#### High-Concurrency Operational Analytics
- **Real-time Dashboards:** Business operations with 100+ concurrent users
- **Peak Traffic Management:** Black Friday, viral events, traffic spikes
- **Performance Monitoring:** System alerts and real-time SLA tracking
- **Executive Dashboards:** C-level insights with instant refresh capabilities
- **Financial Analytics:** Real-time reconciliation and fraud detection

#### Industry-Specific Use Cases

##### AdTech & Marketing Technology
- **Real-time Bidding:** Sub-millisecond bid optimization for programmatic advertising
- **Campaign Analytics:** Instant performance insights for marketing optimization
- **Audience Segmentation:** Dynamic audience analysis with real-time behavioral data
- **Attribution Analysis:** Multi-touch attribution with sub-second query performance

##### E-commerce & Retail
- **Dynamic Pricing:** Price optimization based on real-time market conditions
- **Inventory Analytics:** Cross-channel inventory optimization with instant updates
- **Customer Journey Analysis:** Sub-second tracking across all touchpoints
- **Product Recommendations:** Real-time recommendations based on user behavior

##### Gaming Industry
- **Player Analytics:** Real-time behavior and engagement metrics
- **Content Creator Analytics:** Performance metrics for streamers and influencers
- **Monetization Optimization:** Real-time analysis of in-game purchases
- **Live Tournament Data:** Real-time statistics during competitive events

##### Financial Services
- **Fraud Detection:** Millisecond fraud scoring for transaction processing
- **Risk Analytics:** Real-time risk assessment for trading and lending
- **Regulatory Reporting:** Automated compliance with real-time data accuracy
- **Algorithmic Trading:** High-frequency market analysis and optimization

## Target Personas

### Technical Decision Makers

#### Data Engineers & Platform Teams
**Responsibilities:**
- Managing and optimizing large-scale data infrastructures and pipelines
- Building and maintaining analytical pipelines and ELT processes
- Ensuring performance SLAs with cost-efficiency for growing data volumes
- Implementing and maintaining data tooling and integration ecosystem

**Pain Points to Address:**
- "Spending too much time tuning queries and fighting performance issues"
- "Manual partitioning and indexing to get acceptable performance"
- "Limited visibility into query execution and bottlenecks"
- "Complex orchestration across multiple specialized tools"
- "Performance degradation as data volumes and users grow"

**Success Criteria:**
- Maintain sub-second SLA for 100s to 1000s of concurrent users
- Reduce time spent on manual tuning, optimization, and firefighting
- Scale QPS and data volume linearly without architectural rewrites
- Build using familiar SQL tools and standard ecosystem integrations

**Key Performance Indicators:**
- Query latency (target: <150ms median, <500ms P95)
- System uptime and reliability (>99.9%)
- Cost per query or cost per TB processed
- Time to implement new analytical features
- Developer productivity and team velocity

**Approach Strategy:**
- **Operational Efficiency Focus:** "Sub-second queries at scale without manual tuning"
- **Familiar Tools Emphasis:** "PostgreSQL-compatible SQL with DBT, Airflow integration"
- **Performance Predictability:** "Consistent sub-150ms latency at 2,500+ QPS"
- **Proof Points:** SimilarWeb (300 QPS, <100ms latency, 100+ TB), IQVIA (1B records in milliseconds)

#### Data Architects & Senior Data Engineers
**Responsibilities:**
- Designing scalable data architectures for enterprise analytics
- Evaluating and selecting data infrastructure technologies
- Ensuring data governance, security, and compliance requirements
- Architecting multi-workload platforms supporting diverse use cases

**Pain Points to Address:**
- "Current architecture can't handle both batch and real-time workloads efficiently"
- "Need separate systems for different use cases increasing complexity"
- "Performance unpredictability affecting SLA commitments"
- "Difficulty scaling without major architectural changes"

**Success Criteria:**
- Design unified platform supporting diverse analytical workloads
- Achieve predictable performance scaling with data and user growth
- Reduce architectural complexity through platform consolidation
- Enable self-service analytics without performance degradation

**Approach Strategy:**
- **Architectural Simplification:** "Unified platform replacing 3-5 specialized tools"
- **Workload Isolation:** "Multi-engine architecture for ingestion, transformation, serving"
- **Proof Points:** IQVIA (diverse workloads from ELT to customer-facing apps)

#### AI Engineers & Data Scientists
**Responsibilities:**
- Implementing LLM-based applications and RAG pipelines
- Building semantic retrieval and AI-serving infrastructure
- Developing GenAI applications requiring real-time context access
- Managing model training data and feature engineering pipelines

**Pain Points to Address:**
- "Fragmented infrastructure with separate vector databases and data warehouses"
- "RAG pipelines requiring complex orchestration and custom caching"
- "Inconsistent retrieval latency affecting AI application performance"
- "Data freshness lags due to synchronization between systems"
- "Difficulty scaling AI applications under variable load"

**Success Criteria:**
- Faster, more relevant AI responses with grounded context from enterprise data
- Simplified, more reliable hybrid retrieval pipelines
- Scalable infrastructure for AI-serving workloads with predictable performance
- Consistent low-latency experience for users interacting with AI systems

**Technical Requirements:**
- Vector similarity search with sub-second performance
- Hybrid queries combining vector and structured data
- High-throughput inference serving (1000s QPS)
- Integration with ML/AI toolchain and frameworks

**Approach Strategy:**
- **Unified AI Infrastructure:** "SQL-driven hybrid retrieval combining vector similarity with structured metadata"
- **Simplified Pipelines:** "Single platform for vector search, structured analytics, real-time ingestion"
- **Consistent Performance:** "Sub-150ms context retrieval for LLMs at 3,000+ QPS"
- **Proof Points:** Firebolt Support Chatbot (thousands of RAG queries with millisecond responses)

#### VP Data & Head of Data
**Responsibilities:**
- Leading data strategy and team building for growing organizations
- Ensuring data infrastructure supports business growth and innovation
- Managing data team productivity and deliverables
- Balancing technical debt with feature velocity

**Pain Points to Address:**
- "Team spending too much time on infrastructure maintenance vs. business value"
- "Difficulty delivering real-time analytics features customers demand"
- "Infrastructure costs growing faster than team output"
- "Performance issues blocking product roadmap execution"

**Success Criteria:**
- Enable data team to focus on business value vs. infrastructure firefighting
- Deliver customer-facing analytics features that drive product adoption
- Scale team output without proportional infrastructure cost increases
- Provide predictable performance enabling product commitments

**Approach Strategy:**
- **Team Productivity:** "Reduce infrastructure overhead, increase feature velocity"
- **Business Impact:** "Enable real-time analytics features driving customer value"
- **Proof Points:** Ezora (40% faster time-to-market for new features)

#### VP Data Products & Chief Data Officer
**Responsibilities:**
- Monetizing data through customer-facing products and features
- Enabling data-driven decision making across the organization
- Managing data as a strategic business asset
- Driving competitive advantage through analytics and AI capabilities

**Pain Points to Address:**
- "Analytics features limited by infrastructure performance constraints"
- "Customer experience suffering from slow dashboards and reports"
- "Cannot deliver real-time insights competitors are providing"
- "Data infrastructure limiting innovation and new product development"

**Success Criteria:**
- Launch data products that create competitive advantage
- Improve customer experience through instant analytics
- Generate revenue from data-driven features and insights
- Enable real-time decision making across the organization

**Approach Strategy:**
- **Product Differentiation:** "Sub-second analytics enabling unique customer experiences"
- **Revenue Generation:** "Data products that customers love and pay for"
- "Proof Points:" AppsFlyer (unlimited users analyzing unlimited data), SimilarWeb (millions of users with instant insights)

#### CTOs & VP Engineering
**Responsibilities:**
- Enabling scalable infrastructure for analytics and AI workloads
- Managing TCO for data and AI infrastructure across the organization
- Ensuring technical teams can move fast without infrastructure bottlenecks
- Making build vs. buy decisions for data infrastructure components

**Pain Points to Address:**
- "Managing multiple specialized tools increases complexity and cost"
- "Performance bottlenecks blocking new feature development"
- "Unpredictable scaling costs affecting budget planning"
- "Technical debt from fragmented data infrastructure"
- "Team productivity limited by tooling complexity"

**Success Criteria:**
- Maintain performance SLAs while reducing total infrastructure cost
- Accelerate developer productivity through familiar tools and simplified architecture
- Scale QPS and data volume linearly without rewrites or migrations
- Consolidate systems to reduce operational overhead and technical debt

**Strategic Considerations:**
- Infrastructure consolidation and vendor reduction
- Risk mitigation and technology future-proofing
- Team productivity and developer experience
- Compliance and security requirements

**Approach Strategy:**
- **Infrastructure Consolidation:** "Replace 3-5 specialized tools with unified SQL-native platform"
- **Predictable Scaling:** "Linear performance and cost scaling without architectural rewrites"
- **Developer Productivity:** "Familiar SQL interface reducing ramp-up time and training needs"
- **Proof Points:** FireScale Benchmark (8x-90x better price-performance), Lurkit (40% cost reduction)

#### Founders & Technical Co-Founders
**Responsibilities:**
- Building scalable technical foundation for rapid business growth
- Making strategic technology choices that enable competitive advantage
- Ensuring technical decisions support product-market fit and growth
- Balancing technical debt with speed to market

**Pain Points to Address:**
- "Current infrastructure limiting product capabilities and customer experience"
- "Technical complexity slowing down feature development"
- "Infrastructure costs consuming too much of funding runway"
- "Performance issues affecting customer satisfaction and retention"

**Success Criteria:**
- Enable rapid product development without infrastructure constraints
- Deliver customer experiences that drive growth and retention
- Build technical foundation that scales with business growth
- Optimize infrastructure costs to extend runway and improve unit economics

**Approach Strategy:**
- **Growth Enablement:** "Infrastructure that scales with your success"
- **Customer Experience:** "Sub-second analytics that delight users"
- **Cost Efficiency:** "30-40% infrastructure cost reduction"
- **Proof Points:** Startup success stories like Lurkit, Ezora

### Business Decision Makers

#### C-Level Executives (CEO, COO, CPO)
**Responsibilities:**
- Driving data and AI transformation across the organization
- Ensuring competitive advantage through data-driven insights and AI capabilities
- Managing overall business performance, growth, and customer experience
- Making strategic technology investments and vendor partnerships

**Pain Points to Address:**
- "Data infrastructure limiting business agility and time-to-market"
- "Infrastructure costs growing faster than business value"
- "Customer experience affected by slow analytical applications"
- "Competitive disadvantage due to inability to deliver real-time insights"
- "Technical complexity preventing rapid innovation"

**Success Criteria:**
- Increase customer satisfaction (NPS) and product engagement through instant insights
- Drive revenue growth through AI-powered user experiences and data products
- Launch new data/AI features faster with existing engineering teams
- Reduce infrastructure costs and operational complexity while scaling

**Business Impact Metrics:**
- Time-to-market for new data-driven features
- Customer retention and engagement metrics
- Revenue per user and monetization of data
- Infrastructure cost as percentage of revenue

**Approach Strategy:**
- **Business Acceleration:** "Enable instant analytics and AI experiences driving customer engagement"
- **Competitive Advantage:** "Deliver sub-second insights while competitors struggle with slow queries"
- **Cost Efficiency:** "30-40% infrastructure cost reduction while improving capabilities"
- **Proof Points:** AppsFlyer (1,000 users analyzing unlimited data), Bigabid (400x performance improvement)

### Competitive Displacement Opportunities

#### Snowflake Displacement Signals
- "Credit fever" or unexpected cost spikes from auto-scaling
- Performance degradation with 100+ concurrent users
- Need for sub-second query performance for customer-facing applications

#### Redshift Displacement Signals
- Minutes-long query compilation times
- Performance bottlenecks with 50+ concurrent users
- Cluster resize operations requiring downtime

#### BigQuery Displacement Signals
- Unpredictable monthly costs due to per-byte scanning
- Performance issues with 100+ concurrent users
- Need for reserved slots to ensure predictable performance

#### ClickHouse Displacement Signals
- Query failures on complex analytical workloads
- Operational complexity requiring specialized expertise
- Need for enterprise features like ACID compliance

## Customer Success Stories & Examples

### Detailed Success Case Studies

#### **SimilarWeb - Internet-Scale Analytics Platform**
**Company Profile:** Web analytics platform serving global marketers and brands
**Technical Challenge:** 1 petabyte of data, 5TB daily ingestion, sub-second user experience requirements for millions of users
**Requirements:** 100+ QPS on 100+ TB with <100ms latency
**Results:**
- Serves millions of users with instant insights on trillion+ rows of data
- Analyzes up to 2 years of data with millisecond response times
- Dynamic querying without additional pre-processing requirements
- Eliminated need for complex caching and aggregation layers
**Business Impact:** Enabled unlimited concurrent users vs. previous 20-query limit
**Quote:** "Firebolt had the best performance but also didn't require any additional pre-processing"

#### **Bigabid - AdTech Performance Revolution**
**Company Profile:** AI-driven mobile advertising optimization platform processing 1M ad auctions/second
**Technical Challenge:** MySQL databases taking minutes for queries, inadequate BI performance for real-time optimization
**Requirements:** Real-time analysis of 1M+ auctions per second
**Results:**
- **400x performance improvement** (minutes to seconds on same datasets)
- **77% storage cost reduction** while improving performance
- Consolidated BI and analytics platforms into single solution
- Real-time ad optimization capabilities enabling competitive advantage
**Business Impact:** Enabled real-time optimization of millions of daily auctions
**Quote:** "Using the same test dataset of 100 million records, other databases took minutes, Firebolt analyzed in seconds"

#### **IQVIA - Healthcare Analytics at Scale**
**Company Profile:** Healthcare data analytics serving life sciences industry
**Technical Challenge:** Diverse workloads from ELT to customer-facing applications, 1B+ patient records requiring millisecond queries
**Requirements:** Consistent sub-second performance for 100-250 concurrent BI users
**Results:**
- **1 billion patient records queried in milliseconds**
- Seamless scaling across ELT, batch analytics, and live applications
- Cost-optimized storage at $23/TB/month on S3
- Unified platform supporting diverse analytical workloads
**Business Impact:** Consistent performance for hundreds of concurrent healthcare researchers
**Quote:** "Whether we have 100, 200, or 250 users accessing a BI tool, we need consistent sub-second query performance"

#### **Ezora - F&B Financial Analytics Transformation**
**Company Profile:** Financial reconciliation and analytics platform for food & beverage franchisees
**Technical Challenge:** Aurora Postgres limitations preventing granular drill-downs, complex financial data analysis
**Requirements:** Sub-second analytics on granular transactional data without aggregations
**Results:**
- **30x performance acceleration** compared to Aurora Postgres
- **Eliminated need for aggregations** - queries run directly on transactional data
- **40% faster time-to-market** for new analytical features
- Enabled expansion to enterprise clients with 10K+ SKUs
**Business Impact:** Expanded enterprise client base through improved performance
**Quote:** "From speed of ingestion to speed of performance, Firebolt has blown expectations out of the water"

#### **AppsFlyer - Enterprise Analytics Transformation**
**Company Profile:** Leading mobile attribution platform serving 12,000+ companies
**Technical Challenge:** 1,000 Looker users, 35 petabytes of data, Athena couldn't handle scale
**Requirements:** Support unlimited concurrent users analyzing massive datasets
**Results:**
- Unlimited concurrent users vs. previous 20-query limit
- 5x cost savings while dramatically improving performance
- 12-month analysis capabilities on petabyte-scale data
- Instant insights instead of slow dashboards
**Business Impact:** Transformed customer experience from limited to unlimited analytics access
**Quote:** "AppsFlyer transformed from being limited to 20 concurrent queries to supporting 1,000 Looker users analyzing unlimited data volumes in seconds"

#### **Lurkit - Gaming Platform Optimization**
**Company Profile:** Swedish gaming tech platform connecting developers, publishers, and content creators
**Technical Challenge:** 50,000 users, 80,000 complex queries daily, MongoDB costs becoming prohibitive
**Requirements:** Near real-time insights for 50,000 creators across millions of gaming channels
**Results:**
- 16.5x-32.1x query performance improvement
- 40% cost reduction in analytics infrastructure
- Near real-time insights every 10 minutes vs. 24-hour delays
- Support for 10x larger historical queries
**Business Impact:** Content creators can report performance to publishers instantly
**Quote:** "Lurkit achieved 32x faster gaming analytics while reducing costs by 40%, enabling real-time insights for 50,000 creators"

#### **WingX - Aviation Intelligence Processing**
**Company Profile:** Aviation intelligence company processing flight and market data
**Technical Challenge:** Processing 400M rows daily, 168B rows scanned, SQL Server performance degradation during pandemic surge
**Requirements:** Daily processing of massive aviation datasets with millisecond query response
**Results:**
- 70-77% reduction in processing time
- Daily processing reduced from 16 hours to 4 hours
- Millisecond queries on 400M daily rows
- Ability to analyze 15 years of historical data efficiently
**Business Impact:** Real-time aviation intelligence instead of day-old insights
**Quote:** "WingX boosted data processing efficiency by 70%, reducing daily processing time from 16 hours to 4 hours"

#### **Dealer Trade Network - Automotive Analytics Acceleration**
**Company Profile:** Largest new car dealer-to-dealer trading network in the United States
**Technical Challenge:** 4,000+ dealerships, slow dealer-specific reports, limited to 30-day data retention
**Requirements:** Instant market intelligence for thousands of dealerships
**Results:**
- 60x faster analytics performance
- Report generation reduced from 1+ hour to 2 minutes
- 12-month data retention enabling historical market analysis
- 2x revenue increase through automated lead identification
**Business Impact:** Real-time market intelligence enabling new revenue opportunities
**Quote:** "Dealer Trade Network achieved 60x faster analytics, reducing dealer report generation from over an hour to 2 minutes"

### Company Type Examples

#### Digital Native Companies (50-200 employees)
- **Lurkit:** Gaming platform optimizing creator analytics with 40% cost reduction
- **Bigabid:** AdTech startup processing millions of auctions with 400x performance improvement
- **Ezora:** Financial analytics platform achieving 30x acceleration for F&B franchises

#### Scale-ups (200-1,000 employees)
- **AppsFlyer:** Mobile attribution scaling to 1,000+ concurrent users with 5x cost savings
- **SimilarWeb:** Web analytics serving millions of users with <100ms latency
- **WingX:** Aviation intelligence reducing processing time from 16 hours to 4 hours

#### High-Growth Companies (1,000-5,000 employees)
- **IQVIA:** Healthcare analytics querying 1B patient records in milliseconds
- **Dealer Trade Network:** Automotive trading network serving 4,000+ dealers with 60x faster analytics
- **Enterprise FinTech:** Trading platforms requiring millisecond fraud detection and risk analytics

### Persona Success Examples

#### Data Engineers & Platform Teams Success Stories
- **SimilarWeb Data Team:** Eliminated complex pre-processing, achieved 300+ QPS on 100+ TB
- **IQVIA Platform Team:** Unified platform supporting diverse workloads from ELT to customer-facing apps
- **Lurkit Engineers:** 40% cost reduction while enabling 10x larger historical queries

#### AI Engineers & Data Scientists Success Stories
- **Firebolt Support Chatbot:** Production RAG system with millisecond responses at scale
- **Financial Services AI:** Real-time fraud detection with hybrid vector + structured queries
- **E-commerce ML Teams:** Real-time personalization engines updating with user behavior

#### VP Data & Head of Data Success Stories
- **Ezora Leadership:** 40% faster time-to-market for new analytical features
- **AppsFlyer Data Strategy:** Transformed from infrastructure limitations to unlimited user analytics
- **Gaming Platform Data Head:** Near real-time creator insights enabling instant sponsor reporting

#### Data Architects Success Stories
- **IQVIA Architecture:** Single platform replacing multiple specialized systems
- **Enterprise Healthcare:** Unified workload isolation for regulatory compliance and performance
- **Scale-up Architecture:** Simplified infrastructure reducing operational overhead by 50%

#### CTO & VP Engineering Success Stories
- **Lurkit CTO:** 40% infrastructure cost reduction with 32x performance improvement
- **Bigabid Engineering:** 400x performance gain while cutting storage costs 77%
- **Healthcare Technology:** Unified platform reducing operational complexity across teams

#### Founders & Technical Co-Founders Success Stories
- **Gaming Startup Founder:** Enabled new revenue streams through real-time creator analytics
- **AdTech Founder:** Competitive advantage through real-time optimization of millions of auctions
- **FinTech CEO:** Customer experience transformation through instant financial insights

#### VP Data Products & CDO Success Stories
- **SimilarWeb Product:** Millions of users receiving instant insights on trillion+ rows
- **AppsFlyer Products:** Unlimited analytics access creating competitive differentiation
- **Enterprise Data Products:** Real-time customer-facing dashboards driving user engagement
