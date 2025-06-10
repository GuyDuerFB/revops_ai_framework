provider "aws" {
  region = var.aws_region
}

module "lambda_functions" {
  source = "./modules/lambda"
  
  lambda_functions = {
    firebolt_reader = {
      name          = "firebolt-reader-lambda"
      handler       = "lambda_function.handler"
      runtime       = "python3.9"
      source_path   = "${path.module}/../../tools/firebolt/query_lambda"
      timeout       = 60
      memory_size   = 256
      environment_vars = {
        FIREBOLT_CREDENTIALS_SECRET = var.firebolt_credentials_secret
        LOG_LEVEL                   = "INFO"
      }
      policy_statements = [
        {
          actions   = ["secretsmanager:GetSecretValue"]
          resources = ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.firebolt_credentials_secret}-*"]
          effect    = "Allow"
        }
      ]
    },
    firebolt_writer = {
      name          = "firebolt-writer-lambda"
      handler       = "lambda_function.handler"
      runtime       = "python3.9"
      source_path   = "${path.module}/../../tools/firebolt/writer_lambda"
      timeout       = 60
      memory_size   = 256
      environment_vars = {
        FIREBOLT_CREDENTIALS_SECRET = var.firebolt_credentials_secret
        LOG_LEVEL                   = "INFO"
      }
      policy_statements = [
        {
          actions   = ["secretsmanager:GetSecretValue"]
          resources = ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.firebolt_credentials_secret}-*"]
          effect    = "Allow"
        }
      ]
    },
    firebolt_metadata = {
      name          = "firebolt-metadata-lambda"
      handler       = "lambda_function.handler"
      runtime       = "python3.9"
      source_path   = "${path.module}/../../tools/firebolt/metadata_lambda"
      timeout       = 30
      memory_size   = 256
      environment_vars = {
        FIREBOLT_CREDENTIALS_SECRET = var.firebolt_credentials_secret
        LOG_LEVEL                   = "INFO"
      }
      policy_statements = [
        {
          actions   = ["secretsmanager:GetSecretValue"]
          resources = ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.firebolt_credentials_secret}-*"]
          effect    = "Allow"
        }
      ]
    },
    webhook_dispatcher = {
      name          = "webhook-dispatcher-lambda"
      handler       = "lambda_function.handler"
      runtime       = "python3.9"
      source_path   = "${path.module}/../../tools/webhook/dispatcher_lambda"
      timeout       = 30
      memory_size   = 128
      environment_vars = {
        WEBHOOK_URL_SECRET = var.webhook_url_secret
        LOG_LEVEL         = "INFO"
      }
      policy_statements = [
        {
          actions   = ["secretsmanager:GetSecretValue"]
          resources = ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.webhook_url_secret}-*"]
          effect    = "Allow"
        },
        {
          actions   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
          resources = [aws_sqs_queue.webhook_queue.arn]
          effect    = "Allow"
        }
      ]
    }
  }
}

resource "aws_sqs_queue" "webhook_queue" {
  name                      = "webhook-dispatch-queue"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 86400
  receive_wait_time_seconds = 10
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.webhook_dlq.arn
    maxReceiveCount     = 5
  })
}

resource "aws_sqs_queue" "webhook_dlq" {
  name                      = "webhook-dispatch-dlq"
  message_retention_seconds = 1209600 # 14 days
}

module "knowledge_bases" {
  source = "./modules/knowledge_base"
  
  knowledge_bases = {
    deal_quality = {
      name           = "deal-quality-knowledge-base"
      description    = "Knowledge base for deal quality analysis"
      s3_source_path = "${path.module}/../../knowledge_base/deal_quality"
      bedrock_model  = "anthropic.claude-3-sonnet-20240229-v1:0"
    },
    consumption_patterns = {
      name           = "consumption-patterns-knowledge-base"
      description    = "Knowledge base for consumption pattern analysis"
      s3_source_path = "${path.module}/../../knowledge_base/consumption_patterns"
      bedrock_model  = "anthropic.claude-3-sonnet-20240229-v1:0"
    }
  }
}

module "agents" {
  source = "./modules/agent"
  
  agents = {
    data_agent = {
      name          = "firebolt-data-agent"
      description   = "Agent for retrieving and writing Firebolt data"
      foundation_model = "anthropic.claude-3-sonnet-20240229-v1:0"
      instruction   = file("${path.module}/../../agents/data_agent/instructions.txt")
      knowledge_bases = []
      lambda_functions = ["firebolt_reader", "firebolt_writer", "firebolt_metadata"]
      tags = {
        Environment = var.environment
        Project     = "RevOps AI Framework"
      }
    },
    deal_quality_agent = {
      name          = "deal-quality-agent"
      description   = "Agent for analyzing deal quality"
      foundation_model = "anthropic.claude-3-sonnet-20240229-v1:0"
      instruction   = file("${path.module}/../../agents/deal_quality_agent/instructions.txt")
      knowledge_bases = ["deal_quality"]
      lambda_functions = []
      tags = {
        Environment = var.environment
        Project     = "RevOps AI Framework"
      }
    },
    consumption_agent = {
      name          = "consumption-agent"
      description   = "Agent for analyzing consumption patterns"
      foundation_model = "anthropic.claude-3-sonnet-20240229-v1:0"
      instruction   = file("${path.module}/../../agents/consumption_agent/instructions.txt")
      knowledge_bases = ["consumption_patterns"]
      lambda_functions = []
      tags = {
        Environment = var.environment
        Project     = "RevOps AI Framework"
      }
    },
    execution_agent = {
      name          = "execution-agent"
      description   = "Agent for executing actions based on analyses"
      foundation_model = "anthropic.claude-3-sonnet-20240229-v1:0"
      instruction   = file("${path.module}/../../agents/execution_agent/instructions.txt")
      knowledge_bases = []
      lambda_functions = ["webhook_dispatcher"]
      tags = {
        Environment = var.environment
        Project     = "RevOps AI Framework"
      }
    }
  }
  
  knowledge_base_map = module.knowledge_bases.knowledge_bases
  lambda_function_map = module.lambda_functions.lambda_functions
}

module "flows" {
  source = "./modules/flow"
  
  flows = {
    deal_quality_analysis = {
      name        = "deal-quality-analysis-flow"
      description = "Orchestration flow for deal quality analysis"
      definition  = file("${path.module}/../../flows/deal_quality_flow.json")
      agents      = ["data_agent", "deal_quality_agent", "execution_agent"]
    },
    consumption_analysis = {
      name        = "consumption-analysis-flow"
      description = "Orchestration flow for consumption pattern analysis"
      definition  = file("${path.module}/../../flows/consumption_flow.json")
      agents      = ["data_agent", "consumption_agent", "execution_agent"]
    }
  }
  
  agent_map = module.agents.agents
}

# CloudWatch Alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = module.lambda_functions.lambda_functions
  
  alarm_name          = "${each.value.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 2
  alarm_description   = "This metric monitors lambda function errors"
  
  dimensions = {
    FunctionName = each.value.function_name
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_sns_topic" "alerts" {
  name = "revops-ai-alerts"
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "RevOps-AI-Dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            for name, lambda in module.lambda_functions.lambda_functions :
            ["AWS/Lambda", "Invocations", "FunctionName", lambda.function_name]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Lambda Invocations"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            for name, lambda in module.lambda_functions.lambda_functions :
            ["AWS/Lambda", "Errors", "FunctionName", lambda.function_name]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Lambda Errors"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            for name, lambda in module.lambda_functions.lambda_functions :
            ["AWS/Lambda", "Duration", "FunctionName", lambda.function_name]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Lambda Duration"
        }
      },
      {
        type   = "log",
        x      = 12,
        y      = 6,
        width  = 12,
        height = 6,
        properties = {
          query = "SOURCE '/aws/lambda/firebolt-reader-lambda' | SOURCE '/aws/lambda/firebolt-writer-lambda' | SOURCE '/aws/lambda/firebolt-metadata-lambda' | SOURCE '/aws/lambda/webhook-dispatcher-lambda' | filter level = 'ERROR' | stats count() by bin(30s)"
          region = var.aws_region
          title  = "Error Logs"
          view   = "timeSeries"
        }
      }
    ]
  })
}
