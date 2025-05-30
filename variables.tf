# variables.tf - Variable definitions for ScamVanguard

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Domain name for ScamVanguard (e.g., scamvanguard.com)"
  type        = string
  default     = "scamvanguard.com"
}

variable "openai_api_key" {
  description = "OpenAI API key for GPT-4 Vision"
  type        = string
  sensitive   = true
}

variable "enable_rate_limiting" {
  description = "Enable DynamoDB-based rate limiting"
  type        = bool
  default     = false  # Start without it, enable later
}

variable "huggingface_api_url" {
  description = "HuggingFace model API URL (optional)"
  type        = string
  default     = ""
}

variable "model_threshold" {
  description = "Confidence threshold for HuggingFace model"
  type        = number
  default     = 0.95
}

variable "daily_request_limit" {
  description = "Maximum requests per day (global)"
  type        = number
  default     = 500
}

variable "per_sender_daily_limit" {
  description = "Maximum requests per sender per day"
  type        = number
  default     = 10
}