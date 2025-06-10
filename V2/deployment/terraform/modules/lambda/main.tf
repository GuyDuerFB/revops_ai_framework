variable "lambda_functions" {
  description = "Map of lambda functions configurations"
  type        = map(object({
    name              = string
    handler           = string
    runtime           = string
    source_path       = string
    environment_vars  = map(string)
    timeout           = number
    memory_size       = number
    policy_statements = list(object({
      actions   = list(string)
      resources = list(string)
      effect    = string
    }))
  }))
}

resource "aws_iam_role" "lambda_role" {
  for_each = var.lambda_functions

  name = "${each.value.name}-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  for_each = var.lambda_functions
  
  name        = "${each.value.name}-policy"
  description = "Policy for ${each.value.name} Lambda function"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Effect   = "Allow"
        Action   = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = ["arn:aws:logs:*:*:*"]
      },
      {
        Effect   = "Allow"
        Action   = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = ["*"]
      }
    ], [
      for statement in each.value.policy_statements : {
        Effect   = statement.effect
        Action   = statement.actions
        Resource = statement.resources
      }
    ])
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  for_each = var.lambda_functions
  
  role       = aws_iam_role.lambda_role[each.key].name
  policy_arn = aws_iam_policy.lambda_policy[each.key].arn
}

data "archive_file" "lambda_package" {
  for_each = var.lambda_functions
  
  type        = "zip"
  source_dir  = each.value.source_path
  output_path = "${path.module}/dist/${each.value.name}.zip"
}

resource "aws_lambda_function" "lambda" {
  for_each = var.lambda_functions
  
  function_name    = each.value.name
  role             = aws_iam_role.lambda_role[each.key].arn
  handler          = each.value.handler
  runtime          = each.value.runtime
  filename         = data.archive_file.lambda_package[each.key].output_path
  source_code_hash = data.archive_file.lambda_package[each.key].output_base64sha256
  
  timeout      = each.value.timeout
  memory_size  = each.value.memory_size
  
  environment {
    variables = each.value.environment_vars
  }
  
  tracing_config {
    mode = "Active"
  }
}

output "lambda_functions" {
  description = "Map of deployed Lambda functions"
  value = {
    for key, lambda in aws_lambda_function.lambda : key => {
      arn           = lambda.arn
      function_name = lambda.function_name
      role_arn      = lambda.role
    }
  }
}
