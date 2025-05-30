import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
sqs = boto3.client('sqs')

def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    # Get bucket and key from SES notification
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    logger.info(f"Email stored at: s3://{bucket}/{key}")

    # Optionally fetch the email file
    response = s3.get_object(Bucket=bucket, Key=key)
    raw_email = response['Body'].read().decode('utf-8', errors='ignore')

    logger.info("Email content (first 500 chars):\n%s", raw_email[:500])

    # Send message to SQS
    queue_url = os.environ['PROCESSING_QUEUE_URL']
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps({
            's3_bucket': bucket,
            's3_key': key
        })
    )

    return {"statusCode": 200}
