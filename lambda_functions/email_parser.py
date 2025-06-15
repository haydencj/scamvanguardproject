import boto3
import os
import json
import email
import logging
import re
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from datetime import datetime, timedelta
from decimal import Decimal
from html.parser import HTMLParser

class HTMLStripper(HTMLParser):
    """Helper class to strip HTML tags"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return ''.join(self.text)


def strip_html(html):
    """Remove HTML tags from text"""
    s = HTMLStripper()
    s.feed(html)
    return s.get_text()

# Set up logging
log = logging.getLogger()
log.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client("s3")
sqs = boto3.client("sqs")
dynamodb = boto3.resource('dynamodb')

# Environment variables
BUCKET = os.environ["ATTACHMENT_BUCKET"]
QUEUE_URL = os.environ["PROCESSING_QUEUE_URL"]
SUPPRESSION_TABLE = os.environ.get("SUPPRESSION_TABLE", "ScamVanguardEmailSuppression")

# Rate limiting configuration
RATE_LIMIT_WINDOW_MINUTES = 60  # 1 hour window
RATE_LIMIT_MAX_EMAILS = 10      # Max 10 emails per hour
RATE_LIMIT_BLOCK_DAYS = 1        # Block for 1 day after rate limit exceeded

# Get DynamoDB tables
suppression_table = dynamodb.Table(SUPPRESSION_TABLE)

def check_rate_limit(email_address):
    """
    Check if email has exceeded rate limit.
    Returns tuple (is_allowed, current_count)
    """
    try:
        # Calculate time window
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)
        
        # Query recent emails from this sender
        # We'll store rate limit data in the suppression table with a special prefix
        response = suppression_table.get_item(
            Key={'email': f'rate_limit#{email_address.lower()}'}
        )
        
        if 'Item' in response:
            item = response['Item']
            # Check if we have a valid rate limit entry
            if 'count' in item and 'window_start' in item:
                item_window_start = datetime.fromisoformat(item['window_start'])
                
                # If the window has expired, start a new one
                if item_window_start < window_start:
                    # Reset the counter
                    update_rate_limit_count(email_address, 1)
                    return (True, 1)
                else:
                    # Check if limit exceeded
                    current_count = int(item['count'])
                    if current_count >= RATE_LIMIT_MAX_EMAILS:
                        return (False, current_count)
                    else:
                        # Increment counter
                        update_rate_limit_count(email_address, current_count + 1, item_window_start.isoformat())
                        return (True, current_count + 1)
        
        # No rate limit entry exists, create one
        update_rate_limit_count(email_address, 1)
        return (True, 1)
        
    except Exception as e:
        log.error(f"Error checking rate limit for {email_address}: {str(e)}")
        # On error, allow the email through but log the issue
        return (True, 0)

def update_rate_limit_count(email_address, count, window_start=None):
    """
    Update the rate limit counter for an email address
    """
    try:
        if window_start is None:
            window_start = datetime.utcnow().isoformat()
        
        # TTL for rate limit entries (clean up after 24 hours)
        ttl = int((datetime.utcnow() + timedelta(days=1)).timestamp())
        
        suppression_table.put_item(
            Item={
                'email': f'rate_limit#{email_address.lower()}',
                'count': count,
                'window_start': window_start,
                'ttl': ttl,
                'type': 'rate_limit_counter'
            }
        )
    except Exception as e:
        log.error(f"Error updating rate limit count: {str(e)}")

def add_to_suppression_list(email_address, reason, detail):
    """
    Add email to suppression list
    """
    try:
        # Suppress for specified duration
        if reason == "rate_limit_exceeded":
            suppress_days = RATE_LIMIT_BLOCK_DAYS
        else:
            suppress_days = 180  # Default 6 months for other reasons
            
        ttl = int((datetime.utcnow() + timedelta(days=suppress_days)).timestamp())
        
        suppression_table.put_item(
            Item={
                'email': email_address.lower(),
                'reason': reason,
                'detail': detail,
                'suppressed_at': datetime.utcnow().isoformat(),
                'ttl': ttl
            }
        )
        
        log.info(f"Added {email_address} to suppression list. Reason: {reason}")
        
    except Exception as e:
        log.error(f"Error adding to suppression list: {str(e)}")

def is_email_suppressed(email_address):
    """
    Check if email is in suppression list
    """
    try:
        response = suppression_table.get_item(
            Key={'email': email_address.lower()}
        )
        return 'Item' in response
    except Exception as e:
        log.error(f"Error checking suppression list: {str(e)}")
        return False

def extract_original_sender_from_forwarded(email_content, forwarding_user=None):
    """
    Extract the original sender from a forwarded email.
    Looks for common forwarding patterns.
    """
    # First, try to strip HTML if present
    if '<' in email_content and '>' in email_content:
        # Also search in the HTML-stripped version
        plain_content = strip_html(email_content)
    else:
        plain_content = email_content
    
    # Log a snippet of what we're searching through
    log.info(f"Searching for sender in content (first 500 chars): {plain_content[:500]}")
    
    # Common forwarding patterns - updated to be more flexible
    patterns = [
        # Basic patterns with flexible spacing and quotes
        r'From:\s*["\']?([^<\n"\'>]+@[^<\n"\'>]+)["\']?',
        r'From:\s*<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?',
        # Generic – first address on the From: line (brackets optional)
        r'From:[^\n]*?\s<?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*>?',
        # Gmail forward style
        r'------+\s*Forwarded message\s*------+.*?From:\s*<?([^<\n>]+@[^<\n>]+)>?',
        # Outlook style
        r'From:\s*([^\[]+)\s*\[mailto:([^\]]+)\]',
        # Generic forward indicators
        r'Begin forwarded message:.*?From:\s*<?([^<\n>]+@[^<\n>]+)>?',
        r'----+\s*Original Message\s*----+.*?From:\s*<?([^<\n>]+@[^<\n>]+)>?',
        # Just email address on a line after "From:"
        r'From:\s*\n?\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    ]
    
    # Try patterns on both HTML and plain content
    for content in [email_content, plain_content]:
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            for match in matches:
                # Handle different match group scenarios
                if match.lastindex == 2:
                    # Pattern matched name and email separately
                    email_addr = match.group(2).strip()
                else:
                    # Pattern matched email only
                    email_addr = match.group(1).strip()
                
                # Clean up the email address
                email_addr = email_addr.strip('<>"\' \t\n\r')
                
                # Validate it looks like an email
                if '@' in email_addr and '.' in email_addr.split('@')[1]:
                    # Additional validation
                    if not any(char in email_addr for char in ['<', '>', ' ', '\n', '\r', '\t']):
                        log.info(f"Found original sender: {email_addr}")
                        return email_addr
    
    # Try one more approach - look for standalone email addresses
    email_pattern = r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
    all_emails = re.findall(email_pattern, plain_content)
    
    # Filter out common system emails and the forwarding user's email
    for email_addr in all_emails:
        if forwarding_user and email_addr.lower() == forwarding_user.lower():
            continue          # ← don't treat the forwarder as the sender
        if not any(skip in email_addr.lower() for skip in ['scamvanguard','noreply','do-not-reply','notification']):
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
    # Strip HTML first if present
    if '<' in email_content and '>' in email_content:
        plain_content = strip_html(email_content)
    else:
        plain_content = email_content
    
    # Look for subject patterns in forwarded content
    patterns = [
        r'Subject:\s*(.+?)(?:\n|$)',
        r'Re:\s*(.+?)(?:\n|$)',
        r'Fwd:\s*(.+?)(?:\n|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, plain_content, re.IGNORECASE)
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
        
        # Get the user who forwarded this (for sending response back)
        forwarding_user = ses_mail.get("source", "unknown").lower()
        log.info(f"Email forwarded by: {forwarding_user}")
        
        # Check if user is suppressed
        if is_email_suppressed(forwarding_user):
            log.warning(f"Email from {forwarding_user} is suppressed. Not processing.")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Email from suppressed sender"})
            }
        
        # Check rate limit
        is_allowed, email_count = check_rate_limit(forwarding_user)
        
        if not is_allowed:
            log.warning(f"Rate limit exceeded for {forwarding_user}. Count: {email_count}")
            # Add to suppression list
            add_to_suppression_list(
                forwarding_user,
                "rate_limit_exceeded",
                f"Sent {email_count} emails in {RATE_LIMIT_WINDOW_MINUTES} minutes"
            )
            
            # Optionally, you could still send them ONE final email explaining why they're blocked
            # For now, we'll just not process it
            return {
                "statusCode": 429,
                "body": json.dumps({"message": "Rate limit exceeded"})
            }
        
        log.info(f"Rate limit check passed. Email #{email_count} in current window for {forwarding_user}")
        
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
        
        # Extract the forwarded content
        forwarded_content = extract_forwarded_content(msg, body)
        
        # Try to extract the original sender from the forwarded email
        original_sender = extract_original_sender_from_forwarded(forwarded_content, forwarding_user)
        
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
            "timestamp": ses_mail.get("timestamp", ""),
            "rate_limit_count": email_count  # Include for monitoring
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