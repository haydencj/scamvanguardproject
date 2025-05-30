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
ses = boto3.client("sesv2")
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
                    "content": "You are a scam detection assistant. Analyze the text and return JSON: {\"label\":\"SAFE|SCAM|UNSURE\",\"reason\":\"brief explanation\"} (reason <= 120 chars)."
                },
                {
                    "role": "user",
                    "content": text[:4000]  # Limit text to 4000 chars
                }
            ],
            "temperature": 0.3,  # Lower temperature for more consistent results
            "max_tokens": 150
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
        
        return classification
        
    except urllib.error.URLError as e:
        log.error(f"OpenAI API error: {str(e)}")
        if hasattr(e, 'code') and e.code == 401:
            return {"label": "UNSURE", "reason": "Authentication error - check API key"}
        return {"label": "UNSURE", "reason": "Service timeout - treat as potential scam"}
    except Exception as e:
        log.error(f"Classification error: {str(e)}")
        return {"label": "UNSURE", "reason": "Service unavailable - treat as potential scam"}

def get_emoji(label):
    """Return appropriate emoji for the label."""
    emoji_map = {
        "SAFE": "✅",
        "SCAM": "🚨",
        "UNSURE": "⚠️"
    }
    return emoji_map.get(label, "❓")

def lambda_handler(event, context):
    """Process messages from SQS queue and send classification results via SES."""
    
    # Get domain name from environment or use default
    domain_name = os.environ.get("DOMAIN_NAME", "scamvanguard.com")
    
    for record in event["Records"]:
        try:
            # Parse the SQS message
            message = json.loads(record["body"])
            
            log.info(f"Processing message from {message.get('sender', 'unknown')}")
            
            # Classify the content
            result = classify(message.get("text", ""))
            
            log.info(f"Classification result: {result}")
            
            # Get the appropriate emoji
            emoji = get_emoji(result["label"])
            
            # Prepare email content
            email_body = f"""{emoji} {result['label']}: {result['reason']}

This is an automated analysis. When in doubt, don't click links or share personal information.

💙 Created by: haydenjohnson.co"""
            
            # Send email response
            ses.send_email(
                FromEmailAddress=f"noreply@{domain_name}",
                Destination={
                    "ToAddresses": [message["sender"]]
                },
                Content={
                    "Simple": {
                        "Subject": {
                            "Data": f"[ScamVanguard] {emoji} {result['label']}"
                        },
                        "Body": {
                            "Text": {
                                "Data": email_body
                            }
                        }
                    }
                }
            )
            
            log.info(f"Email sent to {message['sender']}")
            
        except Exception as e:
            log.error(f"Error processing record: {str(e)}")
            # Re-raise to let Lambda retry (respecting the DLQ settings)
            raise
    
    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}