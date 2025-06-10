variable "aws_region" {
  description = "AWS region for infrastructure deployment"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "environment" {
  description = "Deployment environment (development, staging, production)"
  type        = string
  default     = "development"
}

variable "firebolt_credentials_secret" {
  description = "Name of the AWS Secrets Manager secret containing Firebolt credentials"
  type        = string
  default     = "firebolt-credentials"
}

variable "webhook_url_secret" {
  description = "Name of the AWS Secrets Manager secret containing webhook URLs"
  type        = string
  default     = "webhook-urls"
}
