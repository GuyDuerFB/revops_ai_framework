# Firebolt Ideal Customer Profile (ICP)

## Executive Summary

Firebolt targets **digital native companies, startups, and high-growth companies** that need high-performance, low-latency analytics for customer-facing applications and AI workloads. These organizations require sub-second query performance with extreme concurrency while maintaining cost efficiency.

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
- Embedded dashboards in SaaS applications
- Real-time user analytics and personalization
- API-driven analytics serving thousands of requests/second
- Multi-tenant analytics with performance isolation

#### AI/GenAI Applications
- RAG systems requiring hybrid vector + structured data retrieval
- Real-time AI inference serving
- Conversational analytics and natural language interfaces
- AI copilots and intelligent agents

#### High-Concurrency Operational Analytics
- Real-time dashboards for business operations
- Live reporting during peak traffic (Black Friday, viral events)
- Performance monitoring and alerting systems
- Executive dashboards with instant refresh

## Target Personas

### Technical Decision Makers

#### Data Engineers & Platform Teams
**Responsibilities:**
- Managing and optimizing large-scale data infrastructures and pipelines
- Building and maintaining analytical pipelines and ELT processes
- Ensuring performance SLAs with cost-efficiency for growing data volumes
- Implementing and maintaining data tooling and integration ecosystem

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

#### AI Engineers & Data Scientists
**Responsibilities:**
- Implementing LLM-based applications and RAG pipelines
- Building semantic retrieval and AI-serving infrastructure
- Developing GenAI applications requiring real-time context access
- Managing model training data and feature engineering pipelines

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

#### CTOs & VP Engineering
**Responsibilities:**
- Enabling scalable infrastructure for analytics and AI workloads
- Managing TCO for data and AI infrastructure across the organization
- Ensuring technical teams can move fast without infrastructure bottlenecks
- Making build vs. buy decisions for data infrastructure components

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

### Business Decision Makers

#### C-Level Executives (CEO, COO, CPO)
**Responsibilities:**
- Driving data and AI transformation across the organization
- Ensuring competitive advantage through data-driven insights and AI capabilities
- Managing overall business performance, growth, and customer experience
- Making strategic technology investments and vendor partnerships

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
