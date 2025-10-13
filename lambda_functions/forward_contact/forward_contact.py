import os
import boto3
import logging
from io import BytesIO
from email import policy
from email.parser import BytesParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
ses = boto3.client("ses", region_name=os.environ.get("AWS_REGION", "us-east-1"))

BUCKET = os.environ["ATTACHMENT_BUCKET"]
KEY_PREFIX = os.environ.get("KEY_PREFIX", "contact/")
FORWARD_TO = os.environ.get("FORWARD_EMAIL")
FROM_ADDRESS = "noreply@scamvanguard.com"

def handler(event, context):
    try:
        logger.info("Processing SES event")
        
        # Extract message details from SES event
        ses_record = event["Records"][0]["ses"]
        message_id = ses_record["mail"]["messageId"]
        
        # Get original sender info
        original_from = ses_record["mail"]["commonHeaders"]["from"][0]
        original_subject = ses_record["mail"]["commonHeaders"].get("subject", "No Subject")
        
        # Construct S3 key
        s3_key = f"{KEY_PREFIX}{message_id}"
        logger.info(f"Fetching email from S3: {BUCKET}/{s3_key}")
        
        # Fetch email from S3
        try:
            obj = s3.get_object(Bucket=BUCKET, Key=s3_key)
            raw_email = obj["Body"].read()
        except Exception as e:
            logger.error(f"Failed to fetch from S3: {str(e)}")
            raise
        
        # Parse the original email
        msg = BytesParser(policy=policy.default).parsebytes(raw_email)
        
        # Create a new forward message
        forward_msg = MIMEMultipart('mixed')
        
        # Set headers for the forwarded message
        forward_msg['Subject'] = f"Fwd: {original_subject}"
        forward_msg['From'] = FROM_ADDRESS
        forward_msg['To'] = FORWARD_TO
        forward_msg['Reply-To'] = original_from
        
        # Create forward information header
        forward_info = f"""
---------- Forwarded message ----------
From: {original_from}
Date: {ses_record['mail']['commonHeaders'].get('date', 'Unknown')}
Subject: {original_subject}
To: contact@scamvanguard.com

"""
        
        # Extract original message body
        body_text = ""
        body_html = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain" and not body_text:
                    body_text = part.get_content()
                elif content_type == "text/html" and not body_html:
                    body_html = part.get_content()
        else:
            content_type = msg.get_content_type()
            if content_type == "text/plain":
                body_text = msg.get_content()
            elif content_type == "text/html":
                body_html = msg.get_content()
        
        # Add text part
        if body_text:
            text_content = forward_info + body_text
            text_part = MIMEText(text_content, 'plain')
            forward_msg.attach(text_part)
        
        # Add HTML part if exists
        if body_html:
            # Prepend forward info to HTML
            html_info = forward_info.replace('\n', '<br>')
            html_content = f"<div style='color: #666;'>{html_info}</div><hr>{body_html}"
            html_part = MIMEText(html_content, 'html')
            forward_msg.attach(html_part)
        
        # If no text or HTML found, create a simple text message
        if not body_text and not body_html:
            text_part = MIMEText(forward_info + "Original message had no readable content.", 'plain')
            forward_msg.attach(text_part)
        
        # Handle attachments
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = part.get("Content-Disposition", "")
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        # Add original attachment
                        attachment = MIMEApplication(part.get_payload(decode=True))
                        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                        forward_msg.attach(attachment)
        
        # Convert message to string
        forward_raw = forward_msg.as_string()
        
        # Send the email
        logger.info(f"Sending forwarded email to {FORWARD_TO}")
        
        response = ses.send_raw_email(
            Source=FROM_ADDRESS,
            Destinations=[FORWARD_TO],
            RawMessage={'Data': forward_raw}
        )
        
        logger.info(f"Email forwarded successfully. MessageId: {response['MessageId']}")
        
        return {
            'statusCode': 200,
            'body': f"Email forwarded to {FORWARD_TO}"
        }
        
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}")
        logger.error(f"Event: {event}")
        raise