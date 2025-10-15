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

# Bucket encryption at rest
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

# ==================== ECR REPOSITORIES ====================

# Single ECR repository for all Lambda functions
resource "aws_ecr_repository" "lambda_functions" {
  name                 = "scamvanguard/lambda-functions"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

# Lifecycle policy to keep only recent images
resource "aws_ecr_lifecycle_policy" "lambda_functions" {
  repository = aws_ecr_repository.lambda_functions.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 4 versioned images per function"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["classifier-", "email-parser-", "ses-feedback-processor-", "forward-contact-"]
          countType     = "imageCountMoreThan"
          countNumber   = 4
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep -latest tags forever"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["classifier-latest", "email-parser-latest", "ses-feedback-processor-latest", "forward-contact-latest"]
          countType     = "imageCountMoreThan"
          countNumber   = 999  # Effectively keep forever
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Remove untagged images after 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
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
        # Note: Removed the condition here to allow both noreply@ and contact@ to send
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
      {
        Sid      = "SecretsManagerRead",
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue"],
        Resource = aws_secretsmanager_secret.openai_api_key.arn
      },
      {
        Sid    = "DynamoDBSuppression",
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ],
        Resource = aws_dynamodb_table.email_suppression.arn
      }
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

# contact@scamvanguard.com forwarder
resource "aws_lambda_function" "contact_forwarder" {
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_functions.repository_url}:forward-contact-latest"
  function_name = "ScamVanguardContactForwarder"
  role          = aws_iam_role.lambda_execution.arn
  timeout       = 30
  memory_size   = 128
  
  environment {
    variables = {
      ATTACHMENT_BUCKET = aws_s3_bucket.email_attachments.id
      KEY_PREFIX        = "contact/"
      FORWARD_EMAIL     = var.forward_email
    }
  }
}

# Email Parser Lambda
resource "aws_lambda_function" "email_parser" {
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_functions.repository_url}:email-parser-latest"
  function_name = "ScamVanguardEmailParser"
  role          = aws_iam_role.lambda_execution.arn
  timeout       = 60
  memory_size   = 512
  
  environment {
    variables = {
      ATTACHMENT_BUCKET    = aws_s3_bucket.email_attachments.id
      PROCESSING_QUEUE_URL = aws_sqs_queue.processing_queue.url
      SUPPRESSION_TABLE    = aws_dynamodb_table.email_suppression.name
    }
  }
  
  tracing_config {
    mode = "Active"
  }
}

# Classifier Lambda
resource "aws_lambda_function" "classifier" {
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_functions.repository_url}:classifier-latest"
  function_name = "ScamVanguardClassifier"
  role          = aws_iam_role.lambda_execution.arn
  timeout       = 300 # 5 minutes
  memory_size   = 1024
  
  environment {
    variables = {
      ATTACHMENT_BUCKET  = aws_s3_bucket.email_attachments.id
      OPENAI_SECRET_NAME = aws_secretsmanager_secret.openai_api_key.name
      MODEL_THRESHOLD    = var.model_threshold
    }
  }
}

# Suspression List stuff
resource "aws_lambda_function" "ses_feedback_processor" {
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_functions.repository_url}:ses-feedback-processor-latest"
  function_name = "ScamVanguardSESFeedbackProcessor"
  role          = aws_iam_role.lambda_execution.arn
  timeout       = 60
  memory_size   = 256 # Smaller than classifier - simpler task
  
  environment {
    variables = {
      SUPPRESSION_TABLE = aws_dynamodb_table.email_suppression.name
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

# ==================== SNS CONFIGURATION ====================

# Create the topic
resource "aws_sns_topic" "ses_notifications" {
  name = "scamvanguard-ses-notifications"
  #kms_master_key_id = "alias/aws/sns" # Encryption
}

resource "aws_sns_topic_policy" "allow_ses_publish" {
  arn = aws_sns_topic.ses_notifications.arn
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowSESPublish"
        Effect    = "Allow"
        Principal = { Service = "ses.amazonaws.com" }
        Action    = "SNS:Publish"
        Resource  = "arn:aws:sns:${var.aws_region}:${data.aws_caller_identity.current.account_id}:scamvanguard-ses-notifications"
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "AWS:SourceArn" = "arn:aws:ses:${var.aws_region}:${data.aws_caller_identity.current.account_id}:identity/${var.domain_name}"
          }
        }
      }
    ]
  })
}

# Subscribe your email
resource "aws_sns_topic_subscription" "ses_notifications_email" {
  topic_arn = aws_sns_topic.ses_notifications.arn
  protocol  = "email"
  endpoint  = "contact@scamvanguard.com" # You'll get notifications here
}

# Connect SES to SNS for bounces
resource "aws_ses_identity_notification_topic" "bounce" {
  topic_arn                = aws_sns_topic.ses_notifications.arn
  notification_type        = "Bounce"
  identity                 = aws_ses_domain_identity.main.domain
  include_original_headers = true # Helps debugging
  depends_on = [
    aws_sns_topic_policy.allow_ses_publish,
    aws_ses_domain_identity.main,
  ]
}

# Connect SES to SNS for complaints
resource "aws_ses_identity_notification_topic" "complaint" {
  topic_arn                = aws_sns_topic.ses_notifications.arn
  notification_type        = "Complaint"
  identity                 = aws_ses_domain_identity.main.domain
  include_original_headers = true # Helps debugging
  depends_on = [
    aws_sns_topic_policy.allow_ses_publish,
    aws_ses_domain_identity.main,
  ]
}

# OPTIONAL BUT RECOMMENDED: Subscribe Lambda to process notifications automatically
resource "aws_sns_topic_subscription" "ses_notifications_lambda" {
  topic_arn = aws_sns_topic.ses_notifications.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.ses_feedback_processor.arn
}

# Permission for SNS to invoke the Lambda
resource "aws_lambda_permission" "allow_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ses_feedback_processor.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.ses_notifications.arn
}

# ==================== SES CONFIGURATION ====================

# Configuration Set
resource "aws_ses_configuration_set" "main" {
  name = "scamvanguard-config-set"
}

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

resource "aws_ses_receipt_rule" "forward_contact" {
  name          = "ForwardContactRule"
  rule_set_name = aws_ses_receipt_rule_set.main.rule_set_name
  enabled       = true
  scan_enabled  = true

  recipients = ["contact@${var.domain_name}"]

  depends_on = [
    aws_lambda_permission.allow_ses_forward,
    aws_ses_active_receipt_rule_set.main,
  ]

  s3_action {
    bucket_name       = aws_s3_bucket.email_attachments.id
    object_key_prefix = "contact/"
    position          = 1
  }

  lambda_action {
    function_arn    = aws_lambda_function.contact_forwarder.arn
    invocation_type = "Event"
    position        = 2
  }
}

resource "aws_lambda_permission" "allow_ses_forward" {
  statement_id   = "AllowSESInvokeContactForwarder"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.contact_forwarder.function_name
  principal      = "ses.amazonaws.com"
  source_account = data.aws_caller_identity.current.account_id
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

resource "aws_dynamodb_table" "email_suppression" {
  name         = "ScamVanguardEmailSuppression"
  billing_mode = "PAY_PER_REQUEST" # No pre-provisioning needed
  hash_key     = "email"           # Primary key

  attribute {
    name = "email"
    type = "S" # String
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true # Auto-delete old records
  }
}

# ==================== CLOUDWATCH ====================

resource "aws_cloudwatch_metric_alarm" "high_bounce_rate" {
  alarm_name          = "ScamVanguard-HighBounceRate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2" # Must fail 2 checks
  metric_name         = "Reputation.BounceRate"
  namespace           = "AWS/SES"
  period              = "300" # 5-minute periods
  statistic           = "Average"
  threshold           = "0.05" # 0.001% bounce rate, if above AWS may suspend sending
  alarm_actions       = [aws_sns_topic.ses_notifications.arn]
}

resource "aws_cloudwatch_metric_alarm" "high_complaint_rate" {
  alarm_name          = "ScamVanguard-HighComplaintRate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Reputation.ComplaintRate"
  namespace           = "AWS/SES"
  period              = "300"
  statistic           = "Average"
  threshold           = "0.001" # 0.1% complaint rate
  alarm_description   = "This metric monitors SES complaint rate"
  alarm_actions       = [aws_sns_topic.ses_notifications.arn]
}

resource "aws_cloudwatch_log_metric_filter" "emails_analyzed" {
  name           = "EmailsAnalyzed"
  log_group_name = aws_cloudwatch_log_group.email_parser.name
  pattern        = "[timestamp, request_id, level=INFO, msg=\"Email analyzed\", ...]"

  metric_transformation {
    name      = "EmailsAnalyzed"
    namespace = "ScamVanguard"
    value     = "1"
  }
}
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

# output "dns_records_instructions" {
#   value       = <<-EOT
    
#     ========== REQUIRED DNS RECORDS ==========
    
#     Add these DNS records to ${var.domain_name}:
    
#     1. Domain Verification (TXT Record):
#        Name: _amazonses.${var.domain_name}
#        Type: TXT
#        Value: ${aws_ses_domain_identity.main.verification_token}
    
#     2. DKIM Records (CNAME Records):
#        ${join("\n       ", [for token in aws_ses_domain_dkim.main.dkim_tokens : "Name: ${token}._domainkey.${var.domain_name}\n       Type: CNAME\n       Value: ${token}.dkim.amazonses.com\n"])}
    
#     3. MX Record (for receiving email):
#        Name: ${var.domain_name}
#        Type: MX
#        Priority: 10
#        Value: inbound-smtp.${var.aws_region}.amazonaws.com
    
#     ==========================================
#   EOT
#   description = "Instructions for DNS configuration"
# }
