output "lambda_functions" {
  description = "Map of deployed Lambda functions"
  value       = module.lambda_functions.lambda_functions
}

output "knowledge_bases" {
  description = "Map of deployed knowledge bases"
  value       = module.knowledge_bases.knowledge_bases
}

output "agents" {
  description = "Map of deployed Bedrock agents"
  value       = module.agents.agents
}

output "flows" {
  description = "Map of deployed Bedrock flows"
  value       = module.flows.flows
}

output "webhook_queue_url" {
  description = "URL of the webhook dispatch queue"
  value       = aws_sqs_queue.webhook_queue.url
}

output "webhook_dlq_url" {
  description = "URL of the webhook dead letter queue"
  value       = aws_sqs_queue.webhook_dlq.url
}

output "dashboard_url" {
  description = "URL for the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}
