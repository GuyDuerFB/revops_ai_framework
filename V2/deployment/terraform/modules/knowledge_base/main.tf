variable "knowledge_bases" {
  description = "Map of knowledge base configurations"
  type        = map(object({
    name           = string
    description    = string
    s3_source_path = string
    bedrock_model  = string
  }))
}

resource "aws_s3_bucket" "knowledge_base_bucket" {
  bucket_prefix = "revops-ai-kb-"
}

resource "aws_s3_object" "knowledge_base_files" {
  for_each = var.knowledge_bases
  
  bucket = aws_s3_bucket.knowledge_base_bucket.id
  key    = "${each.key}/source/"
  source = each.value.s3_source_path
}

resource "aws_bedrock_knowledge_base" "knowledge_base" {
  for_each = var.knowledge_bases
  
  name        = each.value.name
  description = each.value.description
  
  knowledge_base_configuration {
    type = "VECTOR"
    
    storage_configuration {
      type = "S3"
      s3_configuration {
        bucket_name = aws_s3_bucket.knowledge_base_bucket.id
        s3_prefix   = "${each.key}/source/"
      }
    }
    
    vector_ingestion_configuration {
      model_id = each.value.bedrock_model
    }
  }
}

output "knowledge_bases" {
  description = "Created knowledge bases"
  value = {
    for key, kb in aws_bedrock_knowledge_base.knowledge_base : key => {
      id   = kb.id
      name = kb.name
      arn  = kb.arn
    }
  }
}
