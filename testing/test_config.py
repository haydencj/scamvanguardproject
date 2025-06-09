import os
import boto3
import json  # Add this import!
from datetime import datetime, timedelta

# Configuration matching your environment
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
DOMAIN_NAME = os.environ.get('DOMAIN_NAME', 'scamvanguard.com')
SCAN_EMAIL = f"scan@{DOMAIN_NAME}"
NOREPLY_EMAIL = f"noreply@{DOMAIN_NAME}"

# Table names from your main.tf
SUPPRESSION_TABLE = "ScamVanguardEmailSuppression"

# Rate limit settings from email_parser
RATE_LIMIT_WINDOW_MINUTES = 60
RATE_LIMIT_MAX_EMAILS = 10
RATE_LIMIT_BLOCK_DAYS = 1

# AWS Clients
ses_client = boto3.client('ses', region_name=AWS_REGION)
sns_client = boto3.client('sns', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name=AWS_REGION)
s3_client = boto3.client('s3', region_name=AWS_REGION)
sqs_client = boto3.client('sqs', region_name=AWS_REGION)

# Get actual resource names from AWS
def get_resource_names():
    """Get actual deployed resource names"""
    resources = {}
    
    # Get S3 bucket name
    buckets = s3_client.list_buckets()
    for bucket in buckets['Buckets']:
        if 'scamvanguard-email-attachments' in bucket['Name']:
            resources['email_bucket'] = bucket['Name']
            break
    
    # Get SQS queue URL
    queues = sqs_client.list_queues(QueueNamePrefix='ScamVanguardProcessingQueue')
    if 'QueueUrls' in queues and queues['QueueUrls']:
        resources['queue_url'] = queues['QueueUrls'][0]
    
    # Lambda function names 
    resources['email_parser_lambda'] = 'ScamVanguardEmailParser'
    resources['classifier_lambda'] = 'ScamVanguardClassifier'
    resources['feedback_processor_lambda'] = 'ScamVanguardSESFeedbackProcessor'  
    resources['contact_forwarder_lambda'] = 'ScamVanguardContactForwarder'
    
    return resources

RESOURCES = get_resource_names()