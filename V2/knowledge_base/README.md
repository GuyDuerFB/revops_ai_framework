# RevOps AI Framework V2 - Knowledge Base

This directory contains the knowledge base resources that power the AI agents in the RevOps AI Framework.

## Overview

The knowledge base currently contains the Firebolt data warehouse schema information needed by the Data Agent. It includes JSON schema definitions and Markdown documentation of tables, relationships, and common queries. Additional knowledge types will be added in the future (see ROADMAP.md).

## Directory Structure

```
knowledge_base/
├── README.md                   # This file
├── firebolt_schema/            # Firebolt database schema information
│   ├── firebolt_schema.json    # JSON schema of Firebolt tables and relationships
│   └── firebolt_schema.md      # Markdown documentation of Firebolt schema
└── schema_knowledge_base.py    # Module for loading schema data
```

## Current Implementation

The `schema_knowledge_base.py` module provides functionality to load and use Firebolt schema information. It is used by the Data Agent to understand the database structure and generate appropriate queries.

The schema files in the `firebolt_schema/` directory are deployed to S3 via Terraform and made accessible to Bedrock knowledge bases for use by the agents.
The knowledge base can be updated using the management utilities:

```python
from knowledge_base.manager import KnowledgeManager

# Initialize the manager
manager = KnowledgeManager()

# Add a new document
manager.add_document(
    collection="best_practices",
    document_id="upsell_strategies",
    content="Document content...",
    metadata={
        "author": "RevOps Team",
        "created_at": "2023-06-15"
    }
)

# Update embeddings for the document
manager.update_embeddings("best_practices/upsell_strategies")
```

## Embedding Models

The knowledge base uses vector embeddings for semantic search and similarity matching. The default embedding model is stored in the `embeddings/` directory.

Available embedding models:

- `general-purpose`: General text embedding model
- `revops-specific`: Domain-adapted model for revenue operations
- `customer-interaction`: Specialized model for customer interaction analysis

## Integration with Agents

The knowledge base is integrated with the framework's agents:

- **Data Agent**: Uses the knowledge base for query enhancement and context enrichment
- **Decision Agent**: References best practices and heuristics for decision-making
- **Execution Agent**: Uses templates and examples for action implementation

## Maintenance

### Updating the Knowledge Base

```bash
# Update document embeddings
python scripts/update_embeddings.py --collection=best_practices

# Import new documents
python scripts/import_documents.py --source=s3://bucket/path --collection=product_knowledge

# Verify knowledge base integrity
python scripts/verify_kb.py
```

### Backup and Restore

```bash
# Create a backup
python scripts/backup_kb.py --target=s3://backup-bucket/kb-backup-$(date +%Y%m%d)

# Restore from backup
python scripts/restore_kb.py --source=s3://backup-bucket/kb-backup-20230615
```

## Development

### Adding New Knowledge Sources

1. Create a new directory in the appropriate collection
2. Add content in Markdown, JSON, or other supported formats
3. Run the indexing script to incorporate the new content
4. Update embeddings for the new content

### Creating Custom Taxonomies

Custom taxonomies can be defined in YAML format:

```yaml
# taxonomies/customer_segment_taxonomy.yaml
name: customer_segment_taxonomy
description: "Taxonomy of customer segments for RevOps"
version: "1.0"
categories:
  - id: enterprise
    name: "Enterprise"
    attributes:
      - annual_revenue: "> $100M"
      - employee_count: "> 1000"
    subcategories:
      - id: global_enterprise
        name: "Global Enterprise"
        attributes:
          - regions: "> 3"
  - id: mid_market
    name: "Mid-Market"
    attributes:
      - annual_revenue: "$10M - $100M"
      - employee_count: "100 - 1000"
  - id: smb
    name: "Small Business"
    attributes:
      - annual_revenue: "< $10M"
      - employee_count: "< 100"
```

## Security and Access Control

- Access to the knowledge base is controlled through IAM policies
- Sensitive information is encrypted at rest
- Usage and access are logged for audit purposes
