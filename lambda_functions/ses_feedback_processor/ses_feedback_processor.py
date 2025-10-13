import json
import boto3
import os
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['SUPPRESSION_TABLE'])

def handler(event, context):
    """
    Process SES bounce and complaint notifications from SNS
    """
    for record in event['Records']:
        if record['EventSource'] != 'aws:sns':
            continue
            
        message = json.loads(record['Sns']['Message'])
        notification_type = message.get('notificationType')
        
        if notification_type == 'Bounce':
            process_bounce(message)
        elif notification_type == 'Complaint':
            process_complaint(message)
    
    return {'statusCode': 200}

def process_bounce(message):
    """
    Handle bounce notifications
    """
    bounce = message['bounce']
    bounce_type = bounce['bounceType']
    
    # Only suppress hard bounces and complaints
    if bounce_type == 'Permanent':
        for recipient in bounce['bouncedRecipients']:
            email = recipient['emailAddress']
            suppress_email(email, 'bounce', bounce_type)
            
            # Log for monitoring
            print(f"Suppressed email due to permanent bounce: {email}")

def process_complaint(message):
    """
    Handle complaint notifications
    """
    complaint = message['complaint']
    
    for recipient in complaint['complainedRecipients']:
        email = recipient['emailAddress']
        suppress_email(email, 'complaint', 'user_complaint')
        
        # Log for monitoring
        print(f"Suppressed email due to complaint: {email}")

def suppress_email(email, reason, detail):
    """
    Add email to suppression list with TTL
    """
    # Keep suppressed for 6 months
    ttl = int((datetime.now() + timedelta(days=180)).timestamp())
    
    try:
        table.put_item(
            Item={
                'email': email.lower(),
                'reason': reason,
                'detail': detail,
                'suppressed_at': datetime.now().isoformat(),
                'ttl': ttl
            }
        )
    except Exception as e:
        print(f"Error suppressing email {email}: {str(e)}")

def is_suppressed(email):
    """
    Check if an email is in the suppression list
    """
    try:
        response = table.get_item(
            Key={'email': email.lower()}
        )
        return 'Item' in response
    except Exception:
        return False