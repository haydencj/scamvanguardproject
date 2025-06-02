import boto3
import os
import json
import email
import logging
import re
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr

# Set up logging
log = logging.getLogger()
log.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client("s3")
sqs = boto3.client("sqs")

# Environment variables
BUCKET = os.environ["ATTACHMENT_BUCKET"]
QUEUE_URL = os.environ["PROCESSING_QUEUE_URL"]

def extract_original_sender_from_forwarded(email_content):
    """
    Extract the original sender from a forwarded email.
    Looks for common forwarding patterns.
    """
    # Common forwarding patterns
    patterns = [
        # "From: John Doe <john@example.com>"
        r'From:\s*([^<\n]+<[^>\n]+>)',
        r'From:\s*([^\n]+@[^\n]+)',
        # "From: john@example.com"
        r'From:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        # Apple Mail style: "From: John Doe <john@example.com>"
        r'From:\s*"?([^"<\n]+)"?\s*<([^>\n]+)>',
        # Outlook style
        r'From:\s*([^\[]+)\s*\[mailto:([^\]]+)\]',
        # Gmail forward style
        r'---------- Forwarded message ---------\s*From:\s*([^<\n]+<[^>\n]+>)',
        r'---------- Forwarded message ---------\s*From:\s*([^\n]+)',
        # Generic forward indicators
        r'Begin forwarded message:.*?From:\s*([^<\n]+<[^>\n]+>)',
        r'-------- Original Message --------.*?From:\s*([^<\n]+<[^>\n]+>)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, email_content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            # Extract email address from the match
            sender_info = match.group(1)
            # Parse the email address properly
            name, email_addr = parseaddr(sender_info)
            if email_addr and '@' in email_addr:
                log.info(f"Found original sender: {email_addr}")
                return email_addr
    
    return None

def extract_forwarded_content(msg, full_content):
    """
    Extract the actual forwarded content from the email.
    This removes the forwarding headers and gets to the suspicious content.
    """
    # Look for common forwarding delimiters
    forward_patterns = [
        r'---------- Forwarded message ---------',
        r'-------- Original Message --------',
        r'Begin forwarded message:',
        r'-----Original Message-----',
        r'> From:',  # Quoted forward
        r'From:.*?Sent:.*?To:.*?Subject:',  # Outlook pattern
    ]
    
    for pattern in forward_patterns:
        match = re.search(pattern, full_content, re.IGNORECASE)
        if match:
            # Return everything after the forward delimiter
            return full_content[match.start():]
    
    # If no forward pattern found, return the whole content
    return full_content

def extract_original_subject(email_content):
    """
    Extract the original subject from forwarded email.
    """
    # Look for subject patterns in forwarded content
    patterns = [
        r'Subject:\s*(.+?)(?:\n|$)',
        r'Re:\s*(.+?)(?:\n|$)',
        r'Fwd:\s*(.+?)(?:\n|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, email_content, re.IGNORECASE)
        if match:
            subject = match.group(1).strip()
            # Clean up common forward prefixes
            subject = re.sub(r'^(Fwd?:|Re:|FW:)\s*', '', subject, flags=re.IGNORECASE)
            return subject
    
    return "No Subject"

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
        
        # Get the user who forwarded this (for sending response back)
        forwarding_user = ses_mail.get("source", "unknown")
        log.info(f"Email forwarded by: {forwarding_user}")
        
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
        
        # Extract the forwarded content
        forwarded_content = extract_forwarded_content(msg, body)
        
        # Try to extract the original sender from the forwarded email
        original_sender = extract_original_sender_from_forwarded(forwarded_content)
        
        # If we couldn't find the original sender, check email headers
        if not original_sender:
            # Sometimes the original sender is in the email headers as "X-Forwarded-From"
            for header in ["X-Forwarded-From", "X-Original-From", "Reply-To"]:
                if msg.get(header):
                    original_sender = msg.get(header)
                    break
        
        # Extract original subject from forwarded content
        original_subject = extract_original_subject(forwarded_content)
        
        # If still no original sender found, note this in the sender field
        if not original_sender:
            log.warning("Could not extract original sender from forwarded email")
            original_sender = "unknown-sender@unknown.domain"
        
        # Check for attachments in the original email
        has_attachments = any(
            part.get_content_disposition() == "attachment"
            for part in msg.walk()
        )
        
        # Also check for image attachments (screenshots)
        has_images = any(
            part.get_content_type().startswith("image/")
            for part in msg.walk()
        )
        
        # Prepare job for classification queue
        job = {
            "message_id": message_id,
            "sender": original_sender,  # Original sender of suspicious email
            "forwarding_user": forwarding_user,  # User who forwarded to ScamVanguard
            "subject": original_subject,
            "text": forwarded_content[:250_000],  # Stay under SQS 256KB limit
            "has_attachments": has_attachments,
            "has_images": has_images,
            "s3_key": s3_key,
            "timestamp": ses_mail.get("timestamp", "")
        }
        
        # Log what we extracted
        log.info(f"Extracted - Original sender: {original_sender}, Subject: {original_subject[:50]}...")
        
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