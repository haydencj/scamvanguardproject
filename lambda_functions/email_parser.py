import os
import json
import logging
import boto3
import urllib.request
import urllib.error
import re
from urllib.parse import urlparse
from botocore.exceptions import ClientError

# Set up logging
log = logging.getLogger()
log.setLevel(logging.INFO)

# Initialize AWS clients
ses = boto3.client("ses")
secrets = boto3.client("secretsmanager")
sqs = boto3.client("sqs")

# Cache for secrets to avoid repeated API calls
_openai_key_cache = None

# Public email domains that companies should NEVER use
PUBLIC_EMAIL_DOMAINS = {
    'gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'icloud.com',
    'aol.com', 'protonmail.com', 'gmx.com', 'mail.com', 'usa.com',
    'yandex.com', 'mail.ru', 'qq.com', '163.com', '126.com', 'sina.com',
    'yahoo.co.uk', 'yahoo.ca', 'yahoo.de', 'yahoo.fr', 'yahoo.es',
    'outlook.de', 'outlook.fr', 'outlook.es', 'live.com', 'msn.com',
    'me.com', 'mac.com', 'googlemail.com', 'pm.me', 'proton.me',
    'tutanota.com', 'fastmail.com', 'hushmail.com', 'gmx.de', 'web.de'
}

# Known legitimate company domains (expandable)
LEGITIMATE_COMPANY_DOMAINS = {
    # Banks
    'bankofamerica.com', 'chase.com', 'wellsfargo.com', 'citibank.com',
    'usbank.com', 'pnc.com', 'capitalone.com', 'tdbank.com', 'keybank.com',
    'regions.com', 'fifththird.com', 'huntington.com', 'suntrust.com',
    # Major tech companies
    'amazon.com', 'apple.com', 'microsoft.com', 'google.com', 'meta.com',
    'netflix.com', 'adobe.com', 'salesforce.com', 'oracle.com', 'ibm.com',
    # Payment services
    'paypal.com', 'venmo.com', 'cashapp.com', 'zelle.com', 'stripe.com',
    # E-commerce
    'ebay.com', 'etsy.com', 'shopify.com', 'walmart.com', 'target.com',
    'bestbuy.com', 'homedepot.com', 'lowes.com', 'costco.com',
    # Services
    'uber.com', 'lyft.com', 'doordash.com', 'grubhub.com', 'airbnb.com',
    'spotify.com', 'dropbox.com', 'slack.com', 'zoom.us', 'linkedin.com',
    'twitter.com', 'instagram.com', 'facebook.com', 'tiktok.com',
    # Utilities & Telecom
    'att.com', 'verizon.com', 'tmobile.com', 'comcast.com', 'spectrum.com',
    # Airlines
    'aa.com', 'delta.com', 'united.com', 'southwest.com', 'jetblue.com',
    # Automotive
    'grammarly.com', 'cars.com', 'carvana.com', 'carmax.com', 'email-carmax.com',
    'autotrader.com', 'carvana.com', 'vroom.com', 'shift.com', 'accu-trade.com'
    # Other services
    'indeed.com', 'glassdoor.com', 'zillow.com', 'redfin.com', 'apartments.com'
}

# Common email marketing domain patterns used by legitimate companies
LEGITIMATE_EMAIL_PATTERNS = [
    r'email[.-].*\.com$',  # email-company.com, email.company.com
    r'mail[.-].*\.com$',   # mail-company.com, mail.company.com
    r'.*\.mailer\..*',     # company.mailer.com
    r'.*\.mailgun\..*',    # via mailgun
    r'.*\.sendgrid\..*',   # via sendgrid
    r'.*\.amazonses\.com$', # Amazon SES
    r'.*\.messagebus\.com$' # MessageBus
]

def extract_sender_domain(sender_email):
    """Extract domain from email address."""
    match = re.search(r'@([^\s>]+)', sender_email)
    if match:
        return match.group(1).lower().strip()
    return None

def is_public_email_domain(domain):
    """Check if the domain is a public email provider."""
    if not domain:
        return False
    return domain in PUBLIC_EMAIL_DOMAINS or any(domain.endswith('.' + public) for public in PUBLIC_EMAIL_DOMAINS)

def check_domain_legitimacy(domain):
    """Check if a domain appears to be from a legitimate company."""
    if not domain:
        return False
    
    # Direct match against known legitimate domains
    for legit_domain in LEGITIMATE_COMPANY_DOMAINS:
        if domain == legit_domain or domain.endswith('.' + legit_domain):
            return True
    
    # Check if it's a subdomain of a legitimate company
    # e.g., ealerts.bankofamerica.com, email-carmax.com
    parts = domain.split('.')
    if len(parts) >= 2:
        # Check the last two parts (e.g., bankofamerica.com from ealerts.bankofamerica.com)
        base_domain = '.'.join(parts[-2:])
        if base_domain in LEGITIMATE_COMPANY_DOMAINS:
            return True
        
        # Check the last three parts for domains like co.uk
        if len(parts) >= 3:
            base_domain_extended = '.'.join(parts[-3:])
            if base_domain_extended in LEGITIMATE_COMPANY_DOMAINS:
                return True
    
    # Check common email marketing patterns
    for pattern in LEGITIMATE_EMAIL_PATTERNS:
        if re.match(pattern, domain):
            # Additional check: ensure the base company name is recognizable
            for company in ['carmax', 'uber', 'amazon', 'apple', 'paypal', 'ebay', 
                          'netflix', 'spotify', 'target', 'walmart', 'bestbuy',
                          'bankofamerica', 'chase', 'wellsfargo', 'citibank']:
                if company in domain.lower().replace('-', '').replace('_', ''):
                    return True
    
    return False

def extract_urls_from_text(text):
    """Extract all URLs from the text."""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return urls

def analyze_email_content(message):
    """Analyze email content for suspicious patterns."""
    text = message.get("text", "").lower()
    subject = message.get("subject", "").lower()
    
    # Combine subject and text for analysis
    full_content = f"{subject} {text}"
    
    # Check for legitimate indicators first
    has_specific_account_info = bool(re.search(r'\b\d{4}\b|\$\d+\.\d{2}|account ending in', full_content))
    has_person_name = bool(re.search(r'(hayden|dear [a-z]+ [a-z]+)', full_content))
    
    suspicious_indicators = {
        'urgency': bool(re.search(r'\b(urgent|immediate|act now|expire|limited time|hurry|asap|deadline|final notice|last chance)\b', full_content)) and not has_specific_account_info,
        'account_threats': bool(re.search(r'\b(suspend|suspended|lock|locked|close|closed|deactivate|terminate|restriction|limited access)\b', full_content)) and not has_specific_account_info,
        'verify_account': bool(re.search(r'\b(verify your account|confirm your identity|update your information|validate your account|re-verify)\b', full_content)),
        'money_request': bool(re.search(r'\b(wire transfer|western union|moneygram|bitcoin|cryptocurrency|payment required|send money|pay now)\b', full_content)),
        'prizes': bool(re.search(r'\b(congratulations|won|winner|prize|lottery|sweepstakes|million dollars|inheritance|beneficiary)\b', full_content)),
        'tax_refund': bool(re.search(r'\b(tax refund|irs refund|government refund|stimulus payment)\b', full_content)),
        'click_link': bool(re.search(r'\b(click here|click this link|click below|click now)\b', full_content)) and not has_specific_account_info,
        'personal_info_request': bool(re.search(r'\b(social security|ssn|password|pin|account number|routing number|credit card)\b', full_content)) and 'enter' in full_content,
        'poor_grammar': len(re.findall(r'[.!?]{2,}|[A-Z]{5,}', text)) > 3,
        'suspicious_attachment': bool(re.search(r'attachment.*(\.exe|\.scr|\.vbs|\.pif|\.cmd|\.bat|\.jar|\.zip|\.rar)', full_content))
    }
    
    return suspicious_indicators

def get_openai_key():
    """Get OpenAI API key from Secrets Manager with caching."""
    global _openai_key_cache
    
    if _openai_key_cache:
        log.info("Cache HIT - returning cached OpenAI key")
        return _openai_key_cache
    
    log.info("Cache MISS - fetching OpenAI key from Secrets Manager")
    try:
        secret_name = os.environ["OPENAI_SECRET_NAME"]
        response = secrets.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response["SecretString"])
        _openai_key_cache = secret_data["api_key"]
        return _openai_key_cache
    except Exception as e:
        log.error(f"Failed to retrieve OpenAI API key: {str(e)}")
        raise

def classify(message):
    """Classify text as SAFE, SCAM, or UNSURE using OpenAI GPT-4."""
    try:
        # Extract sender information
        sender = message.get("sender", "")
        sender_domain = extract_sender_domain(sender)
        is_public_domain = is_public_email_domain(sender_domain)
        is_known_company = check_domain_legitimacy(sender_domain)
        
        # Extract URLs and analyze content
        text = message.get("text", "")
        urls = extract_urls_from_text(text)
        suspicious_indicators = analyze_email_content(message)
        
        # Claims to be from a company but uses public email = INSTANT SCAM
        company_claim_pattern = r'\b(bank|paypal|amazon|apple|microsoft|google|netflix|ebay|fedex|ups|irs|government|support team|customer service|security team|account team)\b'
        claims_to_be_company = bool(re.search(company_claim_pattern, text.lower()))
        
        if is_public_domain and claims_to_be_company:
            log.info(f"Instant scam detection: Public domain {sender_domain} claiming to be a company")
            return {
                "label": "SCAM",
                "reason": "Fraudulent sender using public email",
                "detailed_reason": f"This email claims to be from a legitimate company but is sent from {sender_domain}, a public email domain. Real companies NEVER use Gmail, Yahoo, Outlook, etc."
            }
        
        # Prepare enhanced prompt for AI
        api_key = get_openai_key()
        
        system_prompt = """You are an expert email security analyst specializing in scam detection. Analyze emails with these critical rules:

FUNDAMENTAL RULE: Real companies NEVER send official communications from public email domains (@gmail.com, @yahoo.com, @outlook.com, @hotmail.com, etc.). Any email claiming to be from a bank, PayPal, Amazon, or any company but sent from a public email domain is 100% a SCAM.

IMPORTANT: Many legitimate companies use specialized subdomains and email marketing domains:
- Subdomains: ealerts.bankofamerica.com, alerts.chase.com, email.netflix.com
- Marketing domains: email-carmax.com, mail.company.com
- These are LEGITIMATE if they are subdomains of the actual company domain

Classification Guidelines:

SCAM indicators:
- Sender uses public email domain (Gmail, Yahoo, etc.) while claiming to be a company
- Domain that looks similar but isn't the real company (bankofamerica-alerts.com vs ealerts.bankofamerica.com)
- Requests sensitive information (passwords, SSN, credit card details)
- Contains urgent threats (account suspension, immediate action required) WITHOUT specific details
- Promises unexpected money (lottery, inheritance, tax refund)
- Has suspicious links to non-company domains
- Poor grammar/spelling from supposed professional entity
- Generic greetings without your name or account details

SAFE indicators:
- From legitimate company subdomain (e.g., ealerts.bankofamerica.com)
- Contains specific account details (last 4 digits, specific amounts, dates)
- Routine account notifications (low balance alerts, transaction confirmations)
- Professional formatting matching company's usual style
- Links go to the official company domain
- No requests for you to provide sensitive information
- Personalized with your name or partial account number

UNSURE when:
- Domain seems legitimate but content is suspicious
- Cannot definitively determine if safe or scam

Return JSON: {"label":"SAFE|SCAM|UNSURE","reason":"brief explanation under 120 chars","detailed_reason":"1-2 sentences explaining the specific factors"}"""

        # Build context for the AI
        suspicious_count = sum(suspicious_indicators.values())
        suspicious_items = [k.replace('_', ' ') for k, v in suspicious_indicators.items() if v]
        
        email_context = f"""
Email Analysis:
- Sender email: {sender}
- Sender domain: {sender_domain}
- Is public email domain: {is_public_domain}
- Claims to be from company: {claims_to_be_company}
- Domain appears legitimate: {is_known_company}
- Number of URLs in email: {len(urls)}
- Suspicious indicators found: {suspicious_count} ({', '.join(suspicious_items) if suspicious_items else 'none'})

Email subject: {message.get('subject', 'No subject')}

Email content:
{text[:4000]}
"""
        
        # Make API request
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": email_context}
            ],
            "temperature": 0.1,  # Very low for consistency
            "max_tokens": 300
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode('utf-8'))
        
        # Extract and validate classification
        content = result["choices"][0]["message"]["content"]
        classification = json.loads(content)
        
        if "label" not in classification or classification["label"] not in ["SAFE", "SCAM", "UNSURE"]:
            classification = {
                "label": "UNSURE",
                "reason": "Unable to determine classification",
                "detailed_reason": "The analysis could not definitively determine if this is safe or a scam. Exercise caution."
            }
        
        log.info(f"AI Classification: {classification['label']} for {sender_domain}")
        return classification
        
    except urllib.error.URLError as e:
        log.error(f"OpenAI API error: {str(e)}")
        return {
            "label": "UNSURE",
            "reason": "Analysis service temporarily unavailable",
            "detailed_reason": "Could not complete analysis. When in doubt, don't click links or share personal information."
        }
    except Exception as e:
        log.error(f"Classification error: {str(e)}")
        return {
            "label": "UNSURE",
            "reason": "Service error - treat with caution",
            "detailed_reason": "Analysis service encountered an error. Please exercise caution with this message."
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
            
            # Get the user who forwarded the email (to send response back to them)
            response_email = message.get('forwarding_user', message.get('sender', 'unknown'))
            original_sender = message.get('sender', 'unknown')
            
            log.info(f"Processing email originally from: {original_sender}")
            log.info(f"Will send response to: {response_email}")
            
            # Classify the content with full message context
            result = classify(message)
            
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
                        'ToAddresses': [response_email]
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
                
                log.info(f"Email sent to {response_email}, MessageId: {response['MessageId']}")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                
                if error_code == 'MessageRejected':
                    log.error(f"SES MessageRejected: {error_message}")
                    log.error(f"Make sure {response_email} is verified in SES (sandbox mode) or move SES out of sandbox mode")
                    # Don't re-raise for email sending errors in sandbox mode
                    # Just log and continue
                else:
                    raise
            
        except Exception as e:
            log.error(f"Error processing record: {str(e)}")
            # Re-raise to let Lambda retry (respecting the DLQ settings)
            raise
    
    return {"statusCode": 200, "body": json.dumps("Messages processed successfully")}