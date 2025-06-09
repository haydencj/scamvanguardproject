import json
import boto3
import time
from datetime import datetime
from test_config import *

def test_sns_topics_exist():
    """Verify SNS topic for bounces and complaints - SINGLE TOPIC in your setup"""
    response = sns_client.list_topics()
    topic_arns = [t['TopicArn'] for t in response['Topics']]
    
    # Your setup uses ONE topic for both bounces and complaints
    ses_notification_topic = None
    
    for arn in topic_arns:
        if 'scamvanguard-ses-notifications' in arn:
            ses_notification_topic = arn
            break
    
    assert ses_notification_topic is not None, "SES notification topic not found"
    
    print(f"✅ Found SES notification topic: {ses_notification_topic}")
    
    # Verify Lambda subscription
    subs = sns_client.list_subscriptions_by_topic(TopicArn=ses_notification_topic)
    lambda_sub = any(s['Protocol'] == 'lambda' for s in subs['Subscriptions'])
    email_sub = any(s['Protocol'] == 'email' for s in subs['Subscriptions'])
    
    assert lambda_sub, "No Lambda subscription found"
    print("✅ Lambda subscription found")
    
    if email_sub:
        print("✅ Email subscription found")
    
    return ses_notification_topic

def test_bounce_handler_lambda():
    """Test the SES feedback processor Lambda function"""
    
    # Create test bounce notification matching SES format
    test_bounce_event = {
        "Records": [{
            "EventSource": "aws:sns",
            "Sns": {
                "Message": json.dumps({
                    "notificationType": "Bounce",
                    "bounce": {
                        "bounceType": "Permanent",
                        "bounceSubType": "General",
                        "bouncedRecipients": [{
                            "emailAddress": "test-bounce@example.com",
                            "action": "failed",
                            "status": "5.1.1",
                            "diagnosticCode": "smtp; 550 5.1.1 user unknown"
                        }],
                        "timestamp": datetime.now().isoformat(),
                        "feedbackId": "test-bounce-001"
                    },
                    "mail": {
                        "timestamp": datetime.now().isoformat(),
                        "source": NOREPLY_EMAIL,
                        "messageId": "test-message-001",
                        "destination": ["test-bounce@example.com"]
                    }
                })
            }
        }]
    }
    
    # Invoke the CORRECT Lambda function name
    response = lambda_client.invoke(
        FunctionName=RESOURCES.get('feedback_processor_lambda', 'ScamVanguardSESFeedbackProcessor'),
        InvocationType='RequestResponse',
        Payload=json.dumps(test_bounce_event)
    )
    
    assert response['StatusCode'] == 200, "Feedback processor failed"
    print("✅ Feedback processor handled bounce successfully")
    
    # Check if email was added to suppression list
    time.sleep(2)
    check_suppression_list("test-bounce@example.com", "bounce")

def test_complaint_handling():
    """Test complaint handling"""
    test_complaint_event = {
        "Records": [{
            "EventSource": "aws:sns",
            "Sns": {
                "Message": json.dumps({
                    "notificationType": "Complaint",
                    "complaint": {
                        "complainedRecipients": [{
                            "emailAddress": "test-complaint@example.com"
                        }],
                        "timestamp": datetime.now().isoformat(),
                        "feedbackId": "test-complaint-001",
                        "complaintFeedbackType": "abuse"
                    },
                    "mail": {
                        "timestamp": datetime.now().isoformat(),
                        "source": NOREPLY_EMAIL,
                        "messageId": "test-message-002",
                        "destination": ["test-complaint@example.com"]
                    }
                })
            }
        }]
    }
    
    # Invoke the feedback processor Lambda
    response = lambda_client.invoke(
        FunctionName=RESOURCES.get('feedback_processor_lambda', 'ScamVanguardSESFeedbackProcessor'),
        InvocationType='RequestResponse',
        Payload=json.dumps(test_complaint_event)
    )
    
    assert response['StatusCode'] == 200, "Complaint handler failed"
    print("✅ Feedback processor handled complaint successfully")
    
    # Check suppression list
    time.sleep(2)
    check_suppression_list("test-complaint@example.com", "complaint")

def check_suppression_list(email, expected_reason):
    """Verify email is in suppression list"""
    table = dynamodb.Table(SUPPRESSION_TABLE)
    
    try:
        response = table.get_item(
            Key={'email': email.lower()}
        )
        
        assert 'Item' in response, f"Email {email} not found in suppression list"
        
        item = response['Item']
        assert item['reason'] == expected_reason, f"Expected reason '{expected_reason}', got '{item['reason']}'"
        assert 'ttl' in item, "TTL not set on suppression entry"
        
        print(f"✅ {email} correctly suppressed for reason: {expected_reason}")
        
        # Clean up test data
        table.delete_item(Key={'email': email.lower()})
        
    except Exception as e:
        print(f"❌ Error checking suppression list: {e}")
        raise