import os
import json
import uuid
import boto3
import re

def get_localstack_endpoint():
    host = os.environ.get("LOCALSTACK_HOSTNAME", "localhost")
    return f"http://{host}:4566"

def dns_to_plain_queue_url(queue_url):
    new_endpoint = get_localstack_endpoint()
    return re.sub(r'http://sqs\.(.*?)\.localhost\.localstack\.cloud:4566', new_endpoint, queue_url)

def handler(event, context):
    endpoint = get_localstack_endpoint()
    sqs = boto3.client("sqs", endpoint_url=endpoint,
                       aws_access_key_id="test", aws_secret_access_key="test", region_name="us-east-1")
    raw_queue_url = os.environ['SQS_QUEUE_URL']
    queue_url = dns_to_plain_queue_url(raw_queue_url)
    
    try:
        body = json.loads(event.get("body", "{}"))
        order_id = str(uuid.uuid4())
        body["order_id"] = order_id
        body["status"] = "EN_COLA"
        
        print("ENDPOINT:", endpoint, flush=True)
        print("QUEUE_URL:", queue_url, flush=True)
        resp = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(body)
        )
        print("MESSAGE_ID:", resp["MessageId"], flush=True)
        
        return {
            "statusCode": 202,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"message": "Pedido recibido y encolado con éxito", "order_id": order_id})
        }
    except Exception as e:
        print("ERROR:", e, flush=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }