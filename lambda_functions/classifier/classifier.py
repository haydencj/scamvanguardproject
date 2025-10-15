import os
import json
import logging
import boto3
from openai import OpenAI
from pydantic import BaseModel
import re
import tldextract
from botocore.exceptions import ClientError
from email.utils import parseaddr
from typing import Literal

# Set up logging
log = logging.getLogger()
log.setLevel(logging.INFO)

# Initialize AWS clients
ses = boto3.client("ses")
secrets = boto3.client("secretsmanager")
sqs = boto3.client("sqs")
dynamodb = boto3.resource('dynamodb')
suppression_table = dynamodb.Table('ScamVanguardEmailSuppression')

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

LEGITIMATE_ESP_DOMAINS = {
    'convertkit.com', 'sendgrid.net', 'mailgun.org', 'rsgsv.net',
    'mailchimp.com', 'constantcontact.com', 'klaviyo.com', 
    'braze.com', 'salesforce.com', 'exacttarget.com',
    'mailjet.com', 'sendinblue.com', 'getresponse.com'
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

no_cache_extract = tldextract.TLDExtract(cache_dir='/tmp')

# Structured output schema
class EmailClassification(BaseModel):
    label: Literal["SAFE", "SCAM", "UNSURE"]  # Enum constraint
    reason: str  # Brief explanation
    detailed_reason: str  # Detailed analysis

def is_email_suppressed(email):
    """
    Check if email is in our suppression list
    """
    try:
        response = suppression_table.get_item(
            Key={'email': email.lower()}
        )
        return 'Item' in response
    except Exception:
        # If we can't check, err on the side of caution and don't send
        return True

def extract_sender_domain(raw_from):
    """
    Extract the registrable domain from a From: header.
    Handles names like 'Chipotle <chipotle@email.chipotle.com>'.
    """
    addr = parseaddr(raw_from)[1]              # chipotle@email.chipotle.com
    if not addr or '@' not in addr:
        return None
    full_domain = addr.split('@')[1].lower()   # email.chipotle.com
    # Use the configured extractor instead of the default
    ext = no_cache_extract(full_domain)    
    if not ext.domain or not ext.suffix:
        return full_domain                     # fallback
    return f"{ext.domain}.{ext.suffix}"        # chipotle.com

def is_public_email_domain(domain):
    """True only for *exact* public providers like gmail.com, yahoo.com, etc."""
    if not domain:
        return False
    return domain in PUBLIC_EMAIL_DOMAINS   # no sub-domain match

def check_domain_legitimacy(domain):
    """Check if a domain appears to be from a legitimate company."""
    if not domain:
        return False
    
        # Exact match for known ESPs (they send on behalf of many companies)
    if domain in LEGITIMATE_ESP_DOMAINS:
        return True
    
    # Check against known legitimate domains first
    if domain in LEGITIMATE_COMPANY_DOMAINS:
        return True
    
    # Check if it's a subdomain of a legitimate company
    parts = domain.split('.')
    if len(parts) >= 2:
        base_domain = '.'.join(parts[-2:])
        if base_domain in LEGITIMATE_COMPANY_DOMAINS:
            return True
        
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
        'personal_info_request': bool(
            re.search(r'\b(social security|ssn|account password|online banking pass|full credit card|routing number)\b',
                    full_content)
        ),
        'poor_grammar': len(re.findall(r'[A-Z]{8,}', text)) > 5,
        'suspicious_attachment': bool(re.search(r'attachment.*(\.exe|\.scr|\.vbs|\.pif|\.cmd|\.bat|\.jar|\.zip|\.rar)', full_content))
    }
    
    return suspicious_indicators

def get_openai_key():
    """Get OpenAI API key from Secrets Manager with caching."""
    global _openai_key_cache
    
    if _openai_key_cache:
        return _openai_key_cache
    
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
    """Classify text as SAFE, SCAM, or UNSURE using OpenAI GPT-5."""
    try:
        # Extract sender information
        sender = message.get("sender", "")
        sender_domain = extract_sender_domain(sender)
        is_public_domain = is_public_email_domain(sender_domain)
        is_known_company = check_domain_legitimacy(sender_domain)
        
        # ---------- EARLY EXIT ----------
        # Legit-looking company domain → SAFE,
        # unless an executable attachment is present.
        if is_known_company and not is_public_domain:
            if not re.search(r'\.(exe|scr|vbs|pif|cmd|bat|jar|zip|rar)$',
                             message.get("attachments", "")):  # adapt if you store attachment names differently
                return {
                    "label": "SAFE",
                    "reason": "Legitimate company domain",
                    "detailed_reason": f"{sender_domain} is a recognised company domain; no red-flag attachments detected."
                }

        if sender_domain in LEGITIMATE_ESP_DOMAINS:
            return {
                "label": "SAFE",
                "reason": "Recognised ESP domain",
                "detailed_reason": f"{sender_domain} is a verified email-service provider domain used for newsletters/receipts."
            }

        # Extract URLs and analyze content
        text = message.get("text", "")
        urls = extract_urls_from_text(text)
        suspicious_indicators = analyze_email_content(message)
        
        # Claims to be from a company but uses public email = INSTANT SCAM
        company_claim_pattern = r'\b(bank|paypal|amazon|apple|microsoft|google|netflix|ebay|fedex|ups|irs|government|support team|customer service|security team|account team)\b'
        claims_to_be_company = bool(re.search(company_claim_pattern, text.lower()))
        
        #if is_public_domain and claims_to_be_company:
        if is_public_domain and not is_known_company and claims_to_be_company:
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

            LEGITIMATE COMPANY DOMAIN RULE:
            - If an email is sent from a verified company's actual domain (e.g., @paypal.com, @amazon.com, @chase.com, @bankofamerica.com), it should be considered LEGITIMATE by default
            - This includes any subdomain or email address from that domain (service@company.com, noreply@company.com, alerts@company.com, etc.)
            - Legitimate companies regularly send: card expiration notices, account updates, security alerts, transaction confirmations, and promotional offers
            - These are NORMAL business communications when from the actual company domain

            LEGITIMATE EMAIL SERVICE PATTERNS:
            Many companies use email services with subdomains - these are SAFE:
            - anything@email.company.com → SAFE (email subdomain of company)
            - anything@mail.company.com → SAFE (mail subdomain of company)
            - anything@notifications.company.com → SAFE (notification subdomain)

            Sub-domains such as email.company.com, mail.company.com and notifications.company.com are **normal** and should be treated exactly like company.com.
            
            CRITICAL: email.chipotle.com is NOT a public email domain! It's a subdomain of chipotle.com:
            - chipotle@email.chipotle.com → SAFE (subdomain of legitimate company)
            - discover@email.discover.com → SAFE (subdomain of legitimate company)
            - target@email.target.com → SAFE (subdomain of legitimate company)

            Public email domains are ONLY services like:
            - @gmail.com, @yahoo.com, @outlook.com, @aol.com, @hotmail.com, etc

            Subdomains of company domains (*.company.com) are PRIVATE company domains, NOT public!

            Classification Guidelines:

            SCAM indicators (ONLY apply these if sender is NOT from a legitimate company domain):
            - Sender uses public email domain while claiming to be a company
            Example: "PayPal Security" <paypalsecurity2024@gmail.com>
            - Sender uses a fake lookalike domain
            Example: @paypaI.com (capital I), @arnazon.com, @bankofamerica-security.net
            - Asks you to reply with sensitive information directly via email
            Example: "Please reply with your password and SSN to verify your account"
            - Links that go to suspicious non-company domains
            Example: PayPal email with links to www.paypal-verification.random-site.com
            - Extremely poor grammar/spelling throughout
            Example: "You're account has been suspend. Click here immediate to restore"
            - Generic threatening language with no personalization
            Example: "Dear Customer, your account will be deleted in 24 hours"

            SAFE indicators:
            - Sender domain matches the company being claimed
            Example: service@paypal.com, noreply@amazon.com, alerts@chase.com
            - Professional formatting and branding consistent with the company
            - Contains any personalization
            Example: "Hello Hayden Johnson", "card ending in 3054", "your order #123-4567890" (but still verify the domain first - scammers often include fake order numbers to create panic)
            - Directs you to log into your account through official channels
            Example: "Log into your PayPal account to update your information"
            - Has specific transaction or account details
            Example: "$49.99 purchase at Target on June 10", "Your Prime membership renews on July 1"

            TRICKY EXAMPLES TO REMEMBER:

            SAFE but looks suspicious:
            - From: service@paypal.com
            Subject: "Update your card information for PayPal"
            Content: "Your card ending in 3054 is expiring. Click here to update."
            WHY SAFE: From actual PayPal domain, personalized (card ending), asks to update through their portal

            - From: noreply@bankofamerica.com
            Subject: "Unusual activity on your account"
            Content: "We noticed a login from a new device. If this wasn't you, please log into your account."
            WHY SAFE: From actual bank domain, common security alert, directs to official login

            SCAM but looks legitimate:
            - From: "Amazon Support" <amazon.support@gmail.com>
            Subject: "Your Amazon order #123-4567890"
            Content: Professional looking, mentions specific order number
            WHY SCAM: Using Gmail instead of @amazon.com - dead giveaway

            - From: security@paypal-notifications.com
            Subject: "PayPal: Verify your account"
            Content: Perfect PayPal branding, professional design
            WHY SCAM: Domain is paypal-notifications.com, NOT paypal.com

            OVERRIDE RULE: To determine if an email is from a legitimate company:
            1. Check if the sender domain matches the company name being claimed
            2. Look for standard corporate email patterns: @companyname.com, noreply@companyname.com, etc.
            3. Consider common legitimate business email services that companies use

            DOMAIN VERIFICATION PROCESS:
            - If email claims to be from "Chipotle" and is from @chipotle.com → LIKELY LEGITIMATE
            - If email claims to be from "Discover" and is from @discover.com → LIKELY LEGITIMATE
            - If email claims to be from "Target" and is from @target.com → LIKELY LEGITIMATE

            The company doesn't need to be on a specific list - the pattern is what matters:
            - Company name matches domain name
            - Professional email structure
            - Not using public email domains

            LEGITIMATE EMAIL SERVICE PATTERNS:
            Many companies use email services that append their domain:
            - chipotle@email.chipotle.com (subdomain pattern)
            - discover@mail.discover.com (mail subdomain)
            - noreply@notifications.company.com (notification subdomain)

            RED FLAGS remain the same:
            - Company name does NOT match domain (PayPal from @security-alert.com)
            - Using public email providers (Bank of America from @gmail.com)
            - Suspicious variations (Discover from @disc0ver.com with zero instead of 'o')

            CLASSIFICATION APPROACH:
            1. First, check if domain reasonably matches the claimed company
            2. If yes, look at the content - is it a normal business communication?
            3. Personalization (your name, partial account numbers) makes it MORE likely to be safe
            4. Requests to click links to verify/update are NORMAL for legitimate companies
            5. Only flag as SCAM if domain is clearly fraudulent OR content asks for extremely sensitive info via email

            Examples of SAFE emails from legitimate but unlisted companies:
            - chipotle@email.chipotle.com: "Your order is ready" → SAFE (legitimate domain pattern)
            - noreply@discover.com: "Payment received for $XXX.XX" → SAFE (legitimate domain + transaction detail)
            - alerts@homedepot.com: "Your order #12345 has shipped" → SAFE (legitimate domain + order detail)

            When unsure about a company's official domains, classify as UNSURE rather than SAFE and advise the user to search for official domain.
            
            NORMAL ORDER EMAIL RULE:
            - If the domain is verified legitimate, links that point to the same domain
            (or its sub-domains) for viewing receipts, rewards, or tracking orders are
            STANDARD practice and **do not** count as requests for sensitive info.

            Return JSON: {"label":"SAFE|SCAM|UNSURE", "reason":"brief explanation under 120 chars","detailed_reason":"1-2 sentences explaining the specific factors"}"""
            
        # Build context for the AI
        suspicious_count = sum(suspicious_indicators.values())
        #suspicious_items = [k.replace('_', ' ') for k, v in suspicious_indicators.items() if v]
        suspicious_items = [k.replace('_', ' ') for k, v in suspicious_indicators.items() if v][:5]  # cap at 5

        email_context = f"""
        Email Analysis:
        - Sender email: {sender}
        - Sender domain: {sender_domain}
        - Is public email domain: {is_public_domain}
        - Claims to be from company: {claims_to_be_company}
        - Number of URLs in email: {len(urls)}
        - Suspicious indicators found: {suspicious_count} ({', '.join(suspicious_items) if suspicious_items else 'none'})

        Email subject: {message.get('subject', 'No subject')}

        Email content:
        {text[:4000]}
        """
        
        # Make API request using OpenAI Responses API
        client = OpenAI(api_key=api_key)
        
        try:
            response = client.responses.parse(
                model="gpt-5-mini",  # or gpt-5-nano for lower cost
                modalities=["text"],
                instructions=system_prompt,
                input=[
                    {"type": "message", "role": "user", "content": email_context}
                ],
                text_format=EmailClassification,
                temperature=0.2, # Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
                #max_output_tokens=300
            )

            # Extract the parsed structured output
            classification = response.output_parsed
            
            # Convert to dict format expected by rest of code
            result = {
                "label": classification.label,
                "reason": classification.reason,
                "detailed_reason": classification.detailed_reason
            }
            
            log.info(f"AI Classification: {result['label']} for {sender_domain}")
            return result
            
        except Exception as e:
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

def generate_html_email(result, sender_email=None):
    """Generate HTML email content based on classification result."""
    emoji = get_emoji(result["label"])
    css_class = get_result_class(result["label"])
    
    # Add sender info if available
    sender_info = ""
    if sender_email:
        sender_info = f"""
        <div style="background-color: #f8f9fa; padding: 10px; margin: 15px 0; border-radius: 4px;">
            <strong>Analyzed Email From:</strong> {sender_email}
        </div>
        """

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

        {sender_info}

        {tips_section}

        <div class="warning">
            <strong>⚠️ When in doubt, don't click links or share personal information.</strong> Contact the company directly using official phone numbers or websites.
        </div>

        <div class="footer">
            <p>This is an automated analysis. Always verify suspicious messages independently.</p>
            <p>💙 Created by: <a href="https://haydencj" class="support-link">haydenjohnson.co</a></p>
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

def generate_text_email(result, sender_email=None):
    """Generate plain text fallback for email clients that don't support HTML."""
    emoji = get_emoji(result["label"])

    sender_info = f"Analyzed Email From: {sender_email}\n\n" if sender_email else ""

    text_content = f"""{emoji} {result['label']}: {result['reason']}

Analysis Details: {result.get('detailed_reason', result['reason'])}

{sender_info}

⚠️ When in doubt, don't click links or share personal information.

Safety Tips:
• Verify sender addresses
• Be wary of urgent requests
• Never share sensitive information via email
• If it seems too good to be true, it probably is

---
This is an automated analysis from ScamVanguard.
Created by: haydencj.com
Support our mission: scamvanguard.com/donate

To stop receiving these emails, simply stop forwarding messages to scan@scamvanguard.com"""
    
    return text_content

def handler(event, context):
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
            
            # Check suppression list first
            if is_email_suppressed(response_email):
                print(f"Email {response_email} is suppressed, not sending response")
                return {
                    'statusCode': 200,
                    'body': json.dumps('Email suppressed, no response sent')
                }

            log.info(f"Processing email originally from: {original_sender}")
            log.info(f"Will send response to: {response_email}")
            
            
            # Classify the content with full message context
            result = classify(message)
            
            log.info(f"Classification result: {result}")
            
            # Get the appropriate emoji
            emoji = get_emoji(result["label"])
            
            # Generate email content
            html_body = generate_html_email(result, original_sender)
            text_body = generate_text_email(result, original_sender)
            
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