variable "flows" {
  description = "Map of Bedrock flow configurations"
  type        = map(object({
    name        = string
    description = string
    definition  = string
    agents      = list(string)
  }))
}

variable "agent_map" {
  description = "Map of agent outputs from the agent module"
  type = map(object({
    id  = string
    arn = string
  }))
}

resource "aws_bedrock_flow" "flow" {
  for_each = var.flows
  
  name        = each.value.name
  description = each.value.description
  definition  = each.value.definition
  execution_role_arn = aws_iam_role.flow_role[each.key].arn
}

resource "aws_iam_role" "flow_role" {
  for_each = var.flows
  
  name = "${each.value.name}-flow-role"
  
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

resource "aws_iam_policy" "flow_policy" {
  for_each = var.flows
  
  name        = "${each.value.name}-flow-policy"
  description = "Policy for ${each.value.name} Bedrock Flow"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "bedrock:*",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "xray:PutTraceSegments"
        ]
        Resource = ["*"]
      },
      {
        Effect   = "Allow"
        Action   = [
          "bedrock:InvokeAgent"
        ]
        Resource = [for agent_name in each.value.agents :
          var.agent_map[agent_name].arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "flow_policy_attachment" {
  for_each = var.flows
  
  role       = aws_iam_role.flow_role[each.key].name
  policy_arn = aws_iam_policy.flow_policy[each.key].arn
}

output "flows" {
  description = "Created Bedrock flows"
  value = {
    for key, flow in aws_bedrock_flow.flow : key => {
      id   = flow.id
      name = flow.name
      arn  = flow.arn
    }
  }
}
