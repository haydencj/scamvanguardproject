import boto3
import os
import json
import email
import logging
from email import policy
from email.parser import BytesParser

# Set up logging
log = logging.getLogger()
log.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# Environment variables
BUCKET = os.environ["ATTACHMENT_BUCKET"]
QUEUE_URL = os.environ["PROCESSING_QUEUE_URL"]

def lambda_handler(event, context):
    """
    Process incoming email from SES, extract content, and queue for classification.
    """
    try:
        # Extract SES event data
        ses_mail = event["Records"][0]["ses"]["mail"]
        message_id = ses_mail["messageId"]
        
        # S3 key matches the 'object_key_prefix' in Terraform
        s3_key = f"emails/{message_id}"
        
        log.info(f"Processing email: {message_id}")
        
        # Retrieve email from S3
        response = s3.get_object(Bucket=BUCKET, Key=s3_key)
        raw_email = response["Body"].read()
        
        # Parse email
        msg = BytesParser(policy=policy.default).parsebytes(raw_email)
        
        # Extract text content (prefer plain text over HTML)
        body = ""
        
        # Try to get the best body representation
        body_part = msg.get_body(preferencelist=("plain", "html"))
        if body_part:
            body = body_part.get_content()
        else:
            # Fallback: walk through all parts
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                elif part.get_content_type() == "text/html" and not body:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        # Extract sender and subject
        sender = ses_mail.get("source", "unknown")
        subject = ses_mail.get("commonHeaders", {}).get("subject", "No Subject")
        
        # Check for attachments
        has_attachments = any(
            part.get_content_disposition() == "attachment"
            for part in msg.walk()
        )
        
        # Prepare job for classification queue
        job = {
            "message_id": message_id,
            "sender": sender,
            "subject": subject,
            "text": body[:250_000],  # Stay under SQS 256KB limit
            "has_attachments": has_attachments,
            "s3_key": s3_key,
            "timestamp": ses_mail.get("timestamp", "")
        }
        
        # Send to SQS
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(job)
        )
        
        log.info(f"Successfully queued email {message_id} for classification")
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Email processed successfully"})
        }
        
    except Exception as e:
        log.error(f"Error processing email: {str(e)}")
        # Re-raise to let Lambda retry
        raise