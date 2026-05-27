import json
import os
import boto3
from decimal import Decimal

def get_localstack_endpoint():
    host = os.environ.get("LOCALSTACK_HOSTNAME", "localhost")
    return f"http://{host}:4566"

# SIEMPRE usa la misma variable que en Terraform (ORDERS_TABLE_NAME)
TABLE_NAME = os.environ.get("ORDERS_TABLE_NAME")

dynamodb = boto3.resource("dynamodb", endpoint_url=get_localstack_endpoint(),
                          aws_access_key_id="test", aws_secret_access_key="test", region_name="us-east-1")

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def handler(event, context):
    try:
        table = dynamodb.Table(TABLE_NAME)
        response = table.scan()
        items = response.get('Items', [])
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(items, cls=DecimalEncoder)
        }
    except Exception as e:
        print("ERROR READER:", e, flush=True)
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }