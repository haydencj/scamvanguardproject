import boto3, os, json, email, logging

log = logging.getLogger()
log.setLevel(logging.INFO)

s3  = boto3.client("s3")
sqs = boto3.client("sqs")

BUCKET     = os.environ["ATTACHMENT_BUCKET"]
QUEUE_URL  = os.environ["PROCESSING_QUEUE_URL"]

def lambda_handler(event, _):
    ses = event["Records"][0]["ses"]
    message_id = ses["mail"]["messageId"]
    key = f"emails/{message_id}"            # matches 'object_key_prefix'

    raw = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    msg = email.message_from_bytes(raw)
    body_part = msg.get_body(preferencelist=("plain","html"))
    text = body_part.get_content() if body_part else ""

    job = {
        "sender": ses["mail"]["source"],
        "subject": ses["mail"]["commonHeaders"].get("subject",""),
        "text": text[:250_000]               # stay under SQS 256-KB limit
    }
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(job))
    return {"statusCode": 200}
