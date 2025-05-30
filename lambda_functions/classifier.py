import json, os, logging, boto3, requests

log = logging.getLogger(); log.setLevel(logging.INFO)
ses = boto3.client("sesv2")
OPENAI_KEY = os.environ["OPENAI_SECRET_NAME"]

def classify(text):
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENAI_KEY}"},
        json={
          "model": "gpt-4o-mini",
          "response_format": {"type":"json_object"},
          "messages":[
            {"role":"system",
             "content":"Return JSON {\"label\":\"SAFE|SCAM\",\"reason\":\"...\"} (≤120 chars)."},
            {"role":"user","content":text[:4000]}
          ]
        }, timeout=20).json()
    return json.loads(r["choices"][0]["message"]["content"])

def lambda_handler(event, _):
    for rec in event["Records"]:
        msg = json.loads(rec["body"])
        result = classify(msg["text"])
        log.info("GPT result %s", result)

        ses.send_email(
            FromEmailAddress=f"noreply@{os.environ['DOMAIN_NAME']}",
            Destination={"ToAddresses":[msg["sender"]]},
            Content={
              "Simple":{
                "Subject":{"Data":f"[ScamVanguard] {result['label']}"},
                "Body":{"Text":{"Data":f"{result['reason']}\n\n💙 scamvanguard.com/donate"}}
              }
            }
        )
    return {"statusCode": 200}
