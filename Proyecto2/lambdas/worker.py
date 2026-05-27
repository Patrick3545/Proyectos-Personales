import json
import os
import boto3
from decimal import Decimal
import re

def get_localstack_endpoint():
    # Devuelve el endpoint correcto dentro de LocalStack o fallback a localhost
    host = os.environ.get("LOCALSTACK_HOSTNAME", "localhost")
    return f"http://{host}:4566"

def dns_to_plain_topic_arn(topic_arn):
    # Si en algún momento usas SNS con formato DNS, ajusta aquí si hace falta
    return topic_arn  # En general, el ARN es aceptado tal cual por localstack

# Conexiones boto3 a recursos LocalStack
dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=get_localstack_endpoint(),
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

sns = boto3.client(
    "sns",
    endpoint_url=get_localstack_endpoint(),
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

# Variables de entorno pasadas por Terraform
TABLE_NAME = os.environ.get("ORDERS_TABLE_NAME")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

def handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    for record in event.get("Records", []):
        try:
            # Convierte los floats de JSON a Decimal para que DynamoDB no falle
            order_data = json.loads(record["body"], parse_float=Decimal)
            order_id = order_data["order_id"]
            
            print(f"Procesando pedido: {order_id}", flush=True)
            
            order_data["status"] = "PROCESADO"
            
            # Guarda en DynamoDB
            table.put_item(Item=order_data)
            print(f"Pedido {order_id} guardado en DynamoDB.", flush=True)
            
            # Publica en SNS
            sns.publish(
                TopicArn=DNS_TO_PLAIN_TOPIC_ARN(SNS_TOPIC_ARN) if 'DNS_TO_PLAIN_TOPIC_ARN' in globals() else SNS_TOPIC_ARN,
                Message=json.dumps({
                    "event": "ORDER_PROCESSED",
                    "order_id": order_id,
                    "customer_email": order_data.get("email", "unknown@email.com")
                }),
                Subject="Tu pedido ha sido procesado"
            )
            print(f"Pedido {order_id} notificado por SNS.", flush=True)
            
        except Exception as e:
            print(f"Error procesando registro: {str(e)}", flush=True)
            raise e