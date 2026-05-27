import json
import os
import boto3

# Conexión local a S3
s3 = boto3.client(
    "s3",
    endpoint_url=f"http://{os.environ.get('LOCALSTACK_HOSTNAME', 'localhost')}:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

def handler(event, context):
    for record in event.get("Records", []):
        try:
            sns_message = json.loads(record["Sns"]["Message"])
            order_id = sns_message["order_id"]
            invoice_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Factura PATRICKGEAR</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 40px; margin: 0; }}
    .card {{ background-color: #1e293b; border-radius: 12px; padding: 30px; max-width: 500px; margin: 0 auto; border: 1px solid #334155; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); }}
    h1 {{ color: #6366f1; margin-top: 0; border-bottom: 2px solid #334155; padding-bottom: 12px; font-size: 22px; text-transform: uppercase; letter-spacing: 1px; font-weight: 800; }}
    .row {{ display: flex; justify-content: space-between; margin: 16px 0; font-size: 14px; }}
    .label {{ color: #94a3b8; }}
    .value {{ font-weight: 600; color: #f8fafc; }}
    .value.id {{ font-family: monospace; color: #6366f1; }}
    .value.success {{ color: #10b981; }}
    .footer {{ text-align: center; margin-top: 35px; font-size: 13px; color: #94a3b8; border-top: 1px solid #334155; padding-top: 20px; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>PATRICKGEAR - Comprobante</h1>
    <div class="row">
      <span class="label">ID del Pedido:</span>
      <span class="value id">{order_id}</span>
    </div>
    <div class="row">
      <span class="label">Estado del Envío:</span>
      <span class="value success">PROCESADO Y ENVIADO</span>
    </div>
    <div class="row">
      <span class="label">Notificación:</span>
      <span class="value">{sns_message.get('customer_email', 'unknown@email.com')}</span>
    </div>
    <div class="footer">
      <p>¡Gracias por armar tu setup con nosotros!</p>
      <p>Tu periférico ya está saliendo de nuestros almacenes locales.</p>
    </div>
  </div>
</body>
</html>"""
          
            s3.put_object(
                Bucket="patrick-facturas", 
                Key=f"invoice_{order_id}.html",
                Body=invoice_html.encode('utf-8'), 
                ContentType="text/html; charset=utf-8", 
                ContentDisposition=f"attachment; filename=factura_{order_id}.html" 
            )
            print(f"Factura HTML para PATRICKGEAR generada con éxito: {order_id}", flush=True)
            
        except Exception as e:
            print(f"Error al generar factura: {str(e)}", flush=True)
            raise e
    return {"statusCode": 200}
