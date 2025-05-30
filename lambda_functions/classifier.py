import os
import json
import logging
import boto3
import urllib.request
import urllib.error
from botocore.exceptions import ClientError

# Set up logging
log = logging.getLogger()
log.setLevel(logging.INFO)

# Initialize AWS clients
ses = boto3.client("ses")  # Using SES v1 for HTML support
secrets = boto3.client("secretsmanager")
sqs = boto3.client("sqs")

# Cache for secrets to avoid repeated API calls
_openai_key_cache = None

def get_openai_key():
    """Get OpenAI API key from Secrets Manager with caching."""
    global _openai_key_cache
    
    if _openai_key_cache:
        return _openai_key_cache
    
    try:
        secret_name = os.environ["OPENAI_SECRET_NAME"]
        response = secrets.get_secret_value(SecretId=secret_name)
        
        # Parse the secret value (it's stored as JSON)
        secret_data = json.loads(response["SecretString"])
        _openai_key_cache = secret_data["api_key"]
        
        return _openai_key_cache
    except Exception as e:
        log.error(f"Failed to retrieve OpenAI API key: {str(e)}")
        raise

def classify(text):
    """Classify text as SAFE, SCAM, or UNSURE using OpenAI GPT-4."""
    try:
        api_key = get_openai_key()
        
        # Prepare the request
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "You are a scam detection assistant. Analyze the text and return JSON: {\"label\":\"SAFE|SCAM|UNSURE\",\"reason\":\"brief explanation\",\"detailed_reason\":\"A more detailed explanation of why this was flagged (1-2 sentences)\"} (reason <= 120 chars)."
                },
                {
                    "role": "user",
                    "content": text[:4000]  # Limit text to 4000 chars
                }
            ],
            "temperature": 0.3,  # Lower temperature for more consistent results
            "max_tokens": 200
        }
        
        # Make the request using urllib
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        
        # Set timeout
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        # Extract the classification result
        content = result["choices"][0]["message"]["content"]
        classification = json.loads(content)
        
        # Validate the response format
        if "label" not in classification or "reason" not in classification:
            raise ValueError("Invalid response format from GPT")
        
        # Ensure label is one of the expected values
        if classification["label"] not in ["SAFE", "SCAM", "UNSURE"]:
            classification["label"] = "UNSURE"
            classification["reason"] = "Unable to determine classification"
            classification["detailed_reason"] = "The analysis could not definitively determine if this is safe or a scam."
        
        return classification
        
    except urllib.error.URLError as e:
        log.error(f"OpenAI API error: {str(e)}")
        if hasattr(e, 'code') and e.code == 401:
            return {
                "label": "UNSURE", 
                "reason": "Authentication error - check API key",
                "detailed_reason": "Service temporarily unavailable. Please exercise caution with suspicious messages."
            }
        return {
            "label": "UNSURE", 
            "reason": "Service timeout - treat as potential scam",
            "detailed_reason": "Analysis service timed out. When in doubt, don't click links or share personal information."
        }
    except Exception as e:
        log.error(f"Classification error: {str(e)}")
        return {
            "label": "UNSURE", 
            "reason": "Service unavailable - treat as potential scam",
            "detailed_reason": "Analysis service is temporarily unavailable. Please exercise caution."
        }

def get_emoji(label):
    """Return appropriate emoji for the label."""
    emoji_map = {
        "SAFE": "✅",
        "SCAM": "🚨",
        "UNSURE": "⚠️"
    }
    return emoji_map.get(label, "❓")

def get_result_class(label):
    """Return CSS class for the label."""
    class_map = {
        "SAFE": "safe",
        "SCAM": "scam",
        "UNSURE": "unsure"
    }
    return class_map.get(label, "unsure")

def generate_html_email(result):
    """Generate HTML email content based on classification result."""
    emoji = get_emoji(result["label"])
    css_class = get_result_class(result["label"])
    
    # Different tips based on result
    if result["label"] == "SAFE":
        tips_section = """
        <div class="tips">
            <h3>✅ This appears to be legitimate, but always stay vigilant:</h3>
            <ul>
                <li>Verify the sender's email address matches official domains</li>
                <li>Check that any links go to the correct website</li>
                <li>Be cautious of any unexpected requests, even from known contacts</li>
                <li>Keep your security software up to date</li>
            </ul>
        </div>
        """
    else:
        tips_section = """
        <div class="tips">
            <h3>🔍 How to Spot Scams - Key Warning Signs:</h3>
            <ul>
                <li><strong>Check the sender's address:</strong> Is it from an official domain? Scammers often use fake or suspicious email addresses</li>
                <li><strong>Urgency and pressure:</strong> Legitimate companies rarely demand immediate action or threaten consequences</li>
                <li><strong>Requests for sensitive info:</strong> Never share passwords, Social Security numbers, or banking details via email or text</li>
                <li><strong>Too good to be true:</strong> Unexpected winnings, inheritance, or get-rich-quick schemes are almost always scams</li>
                <li><strong>Poor spelling/grammar:</strong> Many scams contain obvious errors or awkward language</li>
                <li><strong>Suspicious links:</strong> Hover over links to see where they really go before clicking</li>
                <li><strong>Unexpected attachments:</strong> Don't open attachments from unknown senders</li>
            </ul>
        </div>
        """
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScamVanguard Analysis Result</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        .container {{
            background-color: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #2c5aa0;
        }}
        .result {{
            font-size: 20px;
            font-weight: bold;
            text-align: center;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .safe {{ background-color: #d4edda; color: #155724; }}
        .scam {{ background-color: #f8d7da; color: #721c24; }}
        .unsure {{ background-color: #fff3cd; color: #856404; }}
        .explanation {{
            background-color: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #2c5aa0;
            margin: 15px 0;
        }}
        .tips {{
            margin-top: 25px;
            padding: 20px;
            background-color: #f0f8ff;
            border-radius: 5px;
            border: 1px solid #b3d9ff;
        }}
        .tips h3 {{
            color: #2c5aa0;
            margin-top: 0;
            font-size: 18px;
        }}
        .tips ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .tips li {{
            margin-bottom: 8px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 14px;
            color: #666;
            text-align: center;
        }}
        .support-link {{
            color: #2c5aa0;
            text-decoration: none;
            font-weight: bold;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            padding: 10px;
            margin: 15px 0;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🛡️ ScamVanguard</div>
            <p>Automated Scam Analysis</p>
        </div>

        <div class="result {css_class}">
            {emoji} {result['label']}: {result['reason']}
        </div>

        <div class="explanation">
            <strong>Why this was flagged:</strong> {result.get('detailed_reason', result['reason'])}
        </div>

        {tips_section}

        <div class="warning">
            <strong>⚠️ When in doubt, don't click links or share personal information.</strong> Contact the company directly using official phone numbers or websites.
        </div>

        <div class="footer">
            <p>This is an automated analysis. Always verify suspicious messages independently.</p>
            <p>💙 Created by: <a href="https://haydenjohnson.co" class="support-link">haydenjohnson.co</a></p>
            <p style="font-size: 12px; color: #888; margin-top: 15px;">
                This service is provided free of charge. To support our mission of protecting people from scams, 
                consider visiting <a href="https://scamvanguard.com/donate" class="support-link">scamvanguard.com</a>
            </p>
            <p style="font-size: 11px; color: #999; margin-top: 10px;">
                ScamVanguard | Automated Scam Detection | To stop receiving these emails, simply stop forwarding messages to scan@scamvanguard.com
            </p>
        </div>
    </div>
</body>
</html>"""
    
    return html_content

def generate_text_email(result):
    """Generate plain text fallback for email clients that don't support HTML."""
    emoji = get_emoji(result["label"])
    
    text_content = f"""{emoji} {result['label']}: {result['reason']}

Analysis Details: {result.get('detailed_reason', result['reason'])}

⚠️ When in doubt, don't click links or share personal information.

Safety Tips:
• Verify sender addresses
• Be wary of urgent requests
• Never share sensitive information via email
• If it seems too good to be true, it probably is

---
This is an automated analysis from ScamVanguard.
Created by: haydenjohnson.co
Support our mission: scamvanguard.com/donate

To stop receiving these emails, simply stop forwarding messages to scan@scamvanguard.com"""
    
    return text_content

def lambda_handler(event, context):
    """Process messages from SQS queue and send classification results via SES."""
    
    # Get domain name from environment
    domain_name = os.environ.get("DOMAIN_NAME", "scamvanguard.com")
    
    for record in event["Records"]:
        try:
            # Parse the SQS message
            message = json.loads(record["body"])
            
            sender_email = message.get('sender', 'unknown')
            log.info(f"Processing message from {sender_email}")
            
            # Classify the content
            result = classify(message.get("text", ""))
            
            log.info(f"Classification result: {result}")
            
            # Get the appropriate emoji
            emoji = get_emoji(result["label"])
            
            # Generate email content
            html_body = generate_html_email(result)
            text_body = generate_text_email(result)
            
            # Try to send email response
            try:
                response = ses.send_email(
                    Source=f"ScamVanguard <noreply@{domain_name}>",
                    Destination={
                        'ToAddresses': [sender_email]
                    },
                    Message={
                        'Subject': {
                            'Data': f"ScamVanguard Analysis: {emoji} {result['label']}",
                            'Charset': 'UTF-8'
                        },
                        'Body': {
                            'Text': {
                                'Data': text_body,
                                'Charset': 'UTF-8'
                            },
                            'Html': {
                                'Data': html_body,
                                'Charset': 'UTF-8'
                            }
                        }
                    }
                )
                
                log.info(f"Email sent to {sender_email}, MessageId: {response['MessageId']}")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                
                if error_code == 'MessageRejected':
                    log.error(f"SES MessageRejected: {error_message}")
                    log.error(f"Make sure {sender_email} is verified in SES (sandbox mode) or move SES out of sandbox mode")
                    # Don't re-raise for email sending errors in sandbox mode
                    # Just log and continue
                else:
                    raise
            
        except Exception as e:
            log.error(f"Error processing record: {str(e)}")
            # Re-raise to let Lambda retry (respecting the DLQ settings)
            raise
    
    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}