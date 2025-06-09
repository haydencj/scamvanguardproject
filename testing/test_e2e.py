import time
import uuid
import json  # Add this import!
from datetime import datetime, timedelta
from test_config import *

def test_complete_email_flow():
    """Test the entire email processing pipeline"""
    
    print("\n=== Starting End-to-End Test ===")
    
    # Generate unique test ID
    test_id = str(uuid.uuid4())[:8]
    test_subject = f"Test Scam Check {test_id}"
    
    # Create a forwarded email that looks like what users would send
    forwarded_content = """
---------- Forwarded message ---------
From: scammer@definitely-not-paypal.com
Date: Mon, Jan 15, 2025 at 10:30 AM
Subject: Urgent: Your account will be suspended!
To: victim@example.com

Dear Customer,

Your PayPal account will be suspended unless you verify your information immediately.
Click here to verify: http://bit.ly/totallylegitpaypal

PayPal Security Team
"""
    
    # Create email content
    email_body = f"""From: test-user@example.com
To: {SCAN_EMAIL}
Subject: Fwd: {test_subject}
Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}
Message-ID: <{test_id}@example.com>

Can you check if this is a scam?

{forwarded_content}
"""
    
    # 1. Upload to S3 (simulating SES delivery)
    message_id = f"test-{test_id}"
    s3_key = f"emails/{message_id}"
    
    try:
        s3_client.put_object(
            Bucket=RESOURCES['email_bucket'],
            Key=s3_key,
            Body=email_body.encode('utf-8')
        )
        print(f"✅ Test email uploaded to S3: {s3_key}")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")
        raise
    
    # 2. Invoke email parser Lambda
    ses_event = {
        "Records": [{
            "ses": {
                "mail": {
                    "source": "test-user@example.com",
                    "messageId": message_id,
                    "destination": [SCAN_EMAIL],
                    "timestamp": datetime.now().isoformat()
                }
            }
        }]
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=RESOURCES['email_parser_lambda'],
            InvocationType='RequestResponse',
            Payload=json.dumps(ses_event)
        )
        
        # Get the response payload
        response_payload = json.loads(response['Payload'].read())
        status_code = response_payload.get('statusCode', response['StatusCode'])
        
        assert status_code == 200, f"Email parser failed with status {status_code}"
        print("✅ Email parser processed successfully")
    except Exception as e:
        print(f"❌ Email parser error: {e}")
        raise
    
    # Continue with rest of test...
    # (rest of the function remains the same)

def check_lambda_logs(message_id):
    """Check Lambda logs for our test message"""
    logs_client = boto3.client('logs')

    log_groups = [
        f"/aws/lambda/{RESOURCES['email_parser_lambda']}",
        f"/aws/lambda/{RESOURCES['classifier_lambda']}"
    ]

    for log_group in log_groups:
        try:
            # Get recent log streams
            streams = logs_client.describe_log_streams(
                logGroupName=log_group,
                orderBy='LastEventTime',
                descending=True,
                limit=5
            )

            if not streams['logStreams']:
                print(f"⚠️  No log streams found for {log_group}")
                continue

            # Search recent streams for our message
            found = False
            for stream in streams['logStreams'][:2]:  # Check last 2 streams
                events = logs_client.filter_log_events(
                    logGroupName=log_group,
                    logStreamName=stream['logStreamName'],
                    filterPattern=f'"{message_id}"',
                    startTime=int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000)
                )

                if events['events']:
                    found = True
                    print(f"✅ Found {len(events['events'])} log entries in {log_group.split('/')[-1]}")
                    break

            if not found:
                print(f"⚠️  No logs found for message {message_id} in {log_group.split('/')[-1]}")

        except Exception as e:
            print(f"⚠️  Error checking {log_group}: {str(e)}")
