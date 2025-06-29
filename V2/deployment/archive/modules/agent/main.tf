variable "agents" {
  description = "Map of Bedrock agent configurations"
  type        = map(object({
    name          = string
    description   = string
    foundation_model = string
    instruction   = string
    knowledge_bases = list(string)
    lambda_functions = list(string)
    tags          = map(string)
  }))
}

variable "knowledge_base_map" {
  description = "Map of knowledge base outputs from the knowledge_base module"
  type = map(object({
    id  = string
    arn = string
  }))
}

variable "lambda_function_map" {
  description = "Map of Lambda functions from the lambda module"
  type = map(object({
    arn = string
  }))
}

resource "aws_bedrock_agent" "agent" {
  for_each = var.agents
  
  agent_name        = each.value.name
  agent_resource_role_arn = aws_iam_role.agent_role[each.key].arn
  foundation_model  = each.value.foundation_model
  description       = each.value.description
  instruction       = each.value.instruction
  
  dynamic "knowledge_base_associations" {
    for_each = each.value.knowledge_bases
    
    content {
      knowledge_base_id = var.knowledge_base_map[knowledge_base_associations.value].id
    }
  }
  
  dynamic "action_group" {
    for_each = each.value.lambda_functions
    iterator = lambda_function
    
    content {
      action_group_name = "lambda_${lambda_function.value}"
      action_group_executor {
        lambda {
          lambda_arn = var.lambda_function_map[lambda_function.value].arn
        }
      }
    }
  }
  
  tags = each.value.tags
}

resource "aws_iam_role" "agent_role" {
  for_each = var.agents
  
  name = "${each.value.name}-agent-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "bedrock.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "agent_policy" {
  for_each = var.agents
  
  name        = "${each.value.name}-agent-policy"
  description = "Policy for ${each.value.name} Bedrock Agent"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "bedrock:*",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = ["*"]
      },
      {
        Effect   = "Allow"
        Action   = [
          "lambda:InvokeFunction"
        ]
        Resource = [for lambda_name in each.value.lambda_functions : 
          var.lambda_function_map[lambda_name].arn
        ]
      },
      {
        Effect   = "Allow"
        Action   = [
          "bedrock:AssociateAgentKnowledgeBase"
        ]
        Resource = [for kb_name in each.value.knowledge_bases :
          var.knowledge_base_map[kb_name].arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "agent_policy_attachment" {
  for_each = var.agents
  
  role       = aws_iam_role.agent_role[each.key].name
  policy_arn = aws_iam_policy.agent_policy[each.key].arn
}

output "agents" {
  description = "Created Bedrock agents"
  value = {
    for key, agent in aws_bedrock_agent.agent : key => {
      id   = agent.id
      name = agent.agent_name
      arn  = agent.arn
    }
  }
}
