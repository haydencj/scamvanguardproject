import boto3
import os
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def lambda_handler(event, context):
    for record in event['Records']:
        logger.info("Received SQS message: %s", record['body'])

        data = json.loads(record['body'])
        bucket = data['s3_bucket']
        key = data['s3_key']

        # Fetch email contents from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        email_data = response['Body'].read().decode('utf-8', errors='ignore')

        # Simulate classification
        logger.info("Classifying email from: s3://%s/%s", bucket, key)
        logger.info("Email (first 500 chars):\n%s", email_data[:500])

        # TODO: Use OpenAI API to classify email and send a reply
        logger.info("Result: SCAM (simulated)")

    return {"statusCode": 200}
