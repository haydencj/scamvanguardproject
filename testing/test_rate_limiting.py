import json
import time
from datetime import datetime, timedelta
from test_config import *

def test_dynamodb_table_exists():
    """Verify DynamoDB table exists and is configured correctly"""
    try:
        # Check suppression table
        table = dynamodb.Table(SUPPRESSION_TABLE)
        assert table.table_status == 'ACTIVE', f"Table {SUPPRESSION_TABLE} not active"

        # Check TTL configuration
        ttl_description = boto3.client('dynamodb').describe_time_to_live(
            TableName=SUPPRESSION_TABLE
        )
        assert ttl_description['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED', "TTL not enabled"
        assert ttl_description['TimeToLiveDescription']['AttributeName'] == 'ttl', "TTL attribute name incorrect"

        print(f"✅ DynamoDB table {SUPPRESSION_TABLE} configured correctly with TTL")
        return table

    except Exception as e:
        print(f"❌ DynamoDB table error: {e}")
        raise

def test_rate_limit_enforcement():
    """Test that rate limiting actually works per your implementation"""
    table = test_dynamodb_table_exists()

    test_email = "rate-limit-test@example.com"

    # Clean up any existing test data
    try:
        table.delete_item(Key={'email': f'rate_limit#{test_email.lower()}'})
        table.delete_item(Key={'email': test_email.lower()})
    except:
        pass

    print(f"\nTesting rate limit: {RATE_LIMIT_MAX_EMAILS} emails per {RATE_LIMIT_WINDOW_MINUTES} minutes")

    # Simulate emails up to and beyond the limit
    for i in range(RATE_LIMIT_MAX_EMAILS + 2):
        try:
            # Create SES event matching your email_parser expectations
            test_event = {
                "Records": [{
                    "ses": {
                        "mail": {
                            "source": test_email,
                            "messageId": f"test-rate-{i}-{datetime.now().timestamp()}",
                            "destination": [SCAN_EMAIL],
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                }]
            }

            # Create a minimal S3 object for the test
            s3_key = f"emails/{test_event['Records'][0]['ses']['mail']['messageId']}"
            s3_client.put_object(
                Bucket=RESOURCES['email_bucket'],
                Key=s3_key,
                Body=create_test_email_content(test_email, f"Test email {i+1}")
            )

            # Invoke email parser Lambda
            response = lambda_client.invoke(
                FunctionName=RESOURCES['email_parser_lambda'],
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )

            response_payload = json.loads(response['Payload'].read())
            status_code = response_payload.get('statusCode', 500)

            if i < RATE_LIMIT_MAX_EMAILS:
                assert status_code == 200, f"Request {i+1} should succeed, got {status_code}"
                print(f"✅ Request {i+1}/{RATE_LIMIT_MAX_EMAILS} succeeded")
            else:
                assert status_code == 429, f"Request {i+1} should be rate limited, got {status_code}"
                print(f"✅ Request {i+1} correctly rate limited")

                # Verify user is in suppression list
                check_rate_limit_suppression(test_email)

            # Clean up S3 object
            s3_client.delete_object(Bucket=RESOURCES['email_bucket'], Key=s3_key)

            time.sleep(0.5)  # Small delay between requests

        except Exception as e:
            print(f"❌ Error on request {i+1}: {e}")
            raise

    # Clean up test data
    cleanup_test_data(table, test_email)

def check_rate_limit_suppression(email):
    """Verify email was added to suppression list for rate limit"""
    table = dynamodb.Table(SUPPRESSION_TABLE)

    response = table.get_item(Key={'email': email.lower()})
    assert 'Item' in response, "Email not in suppression list after rate limit"

    item = response['Item']
    assert item['reason'] == 'rate_limit_exceeded', f"Wrong suppression reason: {item['reason']}"
    print(f"✅ Email correctly suppressed for rate limit violation")

def create_test_email_content(sender, subject):
    """Create a minimal test email for S3"""
    email_content = f"""From: {sender}
To: {SCAN_EMAIL}
Subject: {subject}
Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}

This is a test email for rate limiting.
"""
    return email_content.encode('utf-8')

def cleanup_test_data(table, test_email):
    """Clean up test entries from DynamoDB"""
    try:
        table.delete_item(Key={'email': f'rate_limit#{test_email.lower()}'})
        table.delete_item(Key={'email': test_email.lower()})
        print("✅ Test data cleaned up")
    except:
        pass
