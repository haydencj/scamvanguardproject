# main.tf - ScamVanguard Infrastructure as Code

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ScamVanguard"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "Hayden Johnson"
    }
  }
}

# ==================== S3 BUCKETS ====================

# Generate unique suffix for bucket names
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Main bucket for email storage
resource "aws_s3_bucket" "email_attachments" {
  bucket = "scamvanguard-email-attachments-${random_id.bucket_suffix.hex}"
}

# # Bucket version control
# resource "aws_s3_bucket_versioning" "email_attachments" {
#   bucket = aws_s3_bucket.email_attachments.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# Bucket encryption 
resource "aws_s3_bucket_server_side_encryption_configuration" "email_attachments" {
  bucket = aws_s3_bucket.email_attachments.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle policy for automatic deletion
resource "aws_s3_bucket_lifecycle_configuration" "email_attachments" {
  bucket = aws_s3_bucket.email_attachments.id

  rule {
    id     = "delete-old-attachments"
    status = "Enabled"

    filter {
      prefix = "" # Applies to all objects
    }

    expiration {
      days = 1
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "email_attachments" {
  bucket = aws_s3_bucket.email_attachments.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket policy for SES and Lambda access
resource "aws_s3_bucket_policy" "email_attachments" {
  bucket = aws_s3_bucket.email_attachments.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowSESPuts"
        Effect = "Allow"
        Principal = {
          Service = "ses.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.email_attachments.arn}/*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# ==================== IAM ROLES & POLICIES ====================

# Lambda execution role
resource "aws_iam_role" "lambda_execution" {
  name = "ScamVanguardLambdaRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole" # aws security token service
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda policy
resource "aws_iam_role_policy" "lambda_policy" {
  name = "ScamVanguardLambdaPolicy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Sid    = "SESAccess"
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "ses:FromAddress" = "noreply@${var.domain_name}"
          }
        }
      },
      {
        Sid    = "SQSAccess"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.processing_queue.arn
      },
      {
        Sid      = "S3ReadEmail"
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.email_attachments.arn}/*"
      },
      # Classifier can fetch secret
      {
        Sid      = "SecretsManagerRead",
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = aws_secretsmanager_secret.openai_api_key.arn
      },
      # ... other statements
    ]
  })
}

# ==================== SQS QUEUES ====================

# Dead Letter Queue - catches messages that fail processing
resource "aws_sqs_queue" "dlq" {
  name                      = "ScamVanguardDLQ"
  message_retention_seconds = 1209600 # 14 days
  kms_master_key_id         = "alias/aws/sqs"
}

# Main processing queue
resource "aws_sqs_queue" "processing_queue" {
  name                       = "ScamVanguardProcessingQueue"
  message_retention_seconds  = 86400 # 24 hours
  visibility_timeout_seconds = 900   # 15 minutes
  receive_wait_time_seconds  = 20    # Long polling
  delay_seconds              = 0
  max_message_size           = 262144 # 256 KB
  kms_master_key_id          = "alias/aws/sqs"

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

# ==================== LAMBDA FUNCTIONS ====================

# Email Parser Lambda
resource "aws_lambda_function" "email_parser" {
  filename         = "lambda_functions/email_parser.zip"
  function_name    = "ScamVanguardEmailParser"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "email_parser.lambda_handler"
  source_code_hash = filebase64sha256("lambda_functions/email_parser.zip")
  runtime          = "python3.9"
  timeout          = 60
  memory_size      = 512

  environment {
    variables = {
      ATTACHMENT_BUCKET    = aws_s3_bucket.email_attachments.id
      PROCESSING_QUEUE_URL = aws_sqs_queue.processing_queue.url
    }
  }

  tracing_config {
    mode = "Active"
  }
}

# Classifier Lambda
resource "aws_lambda_function" "classifier" {
  filename         = "lambda_functions/classifier.zip"
  function_name    = "ScamVanguardClassifier"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "classifier.lambda_handler"
  source_code_hash = filebase64sha256("lambda_functions/classifier.zip")
  runtime          = "python3.9"
  timeout          = 300 # 5 minutes
  memory_size      = 1024

  environment {
    variables = {
      ATTACHMENT_BUCKET  = aws_s3_bucket.email_attachments.id
      OPENAI_SECRET_NAME = aws_secretsmanager_secret.openai_api_key.name
      MODEL_THRESHOLD    = var.model_threshold
    }
  }
}

# SQS trigger for classifier Lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.processing_queue.arn
  function_name    = aws_lambda_function.classifier.arn
  batch_size       = 1
}

# ==================== SECRETS MANAGER ====================

# OpenAI API Key secret
resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "ScamVanguard/OpenAI/APIKey"
  description             = "OpenAI API key for GPT-4 Vision"
  recovery_window_in_days = 7
}

# Secret version (must set the actual value manually or via variable)
resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id = aws_secretsmanager_secret.openai_api_key.id
  secret_string = jsonencode({
    api_key = var.openai_api_key
  })
}

# ==================== SES CONFIGURATION ====================

# Verify domain
resource "aws_ses_domain_identity" "main" {
  domain = var.domain_name
}

# Domain verification records (output these to add to DNS)
resource "aws_ses_domain_dkim" "main" {
  domain = aws_ses_domain_identity.main.domain
}

# SES Receipt Rule Set
resource "aws_ses_receipt_rule_set" "main" {
  rule_set_name = "ScamVanguardRuleSet"
}

# Activate the rule set
resource "aws_ses_active_receipt_rule_set" "main" {
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
}

# SES Receipt Rule
resource "aws_ses_receipt_rule" "scan_email" {
  name          = "ScamVanguardScanRule"
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
  enabled       = true
  scan_enabled  = true # Enable spam/virus scanning

  recipients = ["scan@${var.domain_name}"]

  depends_on = [
    aws_s3_bucket.email_attachments,
    aws_lambda_function.email_parser,
    aws_ses_receipt_rule_set.main
  ]

  # Store email in S3
  s3_action {
    bucket_name       = aws_s3_bucket.email_attachments.id
    object_key_prefix = "emails/"
    position          = 1
  }

  # Trigger Lambda
  lambda_action {
    function_arn    = aws_lambda_function.email_parser.arn
    invocation_type = "Event"
    position        = 2
  }
}

# Permission for SES to invoke Lambda
resource "aws_lambda_permission" "allow_ses" {
  statement_id   = "AllowExecutionFromSES"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.email_parser.function_name
  principal      = "ses.amazonaws.com"
  source_account = data.aws_caller_identity.current.account_id
}

# ==================== DYNAMODB (Optional Rate Limiting) ==================== Later

# ==================== CLOUDWATCH ====================

# Log Groups
resource "aws_cloudwatch_log_group" "email_parser" {
  name              = "/aws/lambda/${aws_lambda_function.email_parser.function_name}"
  retention_in_days = 7
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "ScamVanguard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["ScamVanguard", "EmailsReceived", { stat = "Sum" }],
            [".", "EmailsClassified", { stat = "Sum" }],
            [".", "ClassificationErrors", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Email Processing Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["ScamVanguard", "Classification_SAFE", { stat = "Sum" }],
            [".", "Classification_SCAM", { stat = "Sum" }],
            [".", "Classification_UNSURE", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Classification Results"
        }
      }
    ]
  })
}

# ==================== DATA SOURCES ====================

data "aws_caller_identity" "current" {}

# ==================== OUTPUTS ====================

output "email_bucket_name" {
  value       = aws_s3_bucket.email_attachments.id
  description = "Name of the S3 bucket for email attachments"
}

output "processing_queue_url" {
  value       = aws_sqs_queue.processing_queue.url
  description = "URL of the SQS processing queue"
}

output "scan_email_address" {
  value       = "scan@${var.domain_name}"
  description = "Email address users should forward suspicious emails to"
}

output "ses_verification_token" {
  value       = aws_ses_domain_identity.main.verification_token
  description = "Add this as a TXT record to verify your SES domain"
}

output "ses_dkim_tokens" {
  value       = aws_ses_domain_dkim.main.dkim_tokens
  description = "DKIM tokens to add to DNS as CNAME records"
}

output "dns_records_instructions" {
  value       = <<-EOT
    
    ========== REQUIRED DNS RECORDS ==========
    
    Add these DNS records to ${var.domain_name}:
    
    1. Domain Verification (TXT Record):
       Name: _amazonses.${var.domain_name}
       Type: TXT
       Value: ${aws_ses_domain_identity.main.verification_token}
    
    2. DKIM Records (CNAME Records):
       ${join("\n       ", [for token in aws_ses_domain_dkim.main.dkim_tokens : "Name: ${token}._domainkey.${var.domain_name}\n       Type: CNAME\n       Value: ${token}.dkim.amazonses.com\n"])}
    
    3. MX Record (for receiving email):
       Name: ${var.domain_name}
       Type: MX
       Priority: 10
       Value: inbound-smtp.${var.aws_region}.amazonaws.com
    
    ==========================================
  EOT
  description = "Instructions for DNS configuration"
}
