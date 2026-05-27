# SQS - Cola de pedidos
resource "aws_sqs_queue" "orders_queue" {
  name = "orders-queue-dev"
}

# IAM Role para Lambda Ingestor (solo permite enviar mensajes a SQS y logs)
resource "aws_iam_role" "ingestor_role" {
  name = "lambda-ingestor-role-dev"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "ingestor_sqs_policy" {
  name = "lambda-ingestor-sqs-policy-dev"
  description = "Permite escribir en SQS y logs"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.orders_queue.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ingestor_policy_attachment" {
  role       = aws_iam_role.ingestor_role.name
  policy_arn = aws_iam_policy.ingestor_sqs_policy.arn
}


# DynamoDB - Tabla de pedidos
resource "aws_dynamodb_table" "orders_table" {
  name           = "OrdersTable-dev"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }
}

# IAM Role para Lambda Worker (permite acceder a DynamoDB, SQS y Logs)
resource "aws_iam_role" "worker_role" {
  name = "lambda-worker-role-dev"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "worker_policy" {
  name        = "lambda-worker-dynamo-sqs-policy-dev"
  description = "Permite dinamodb:PutItem/GetItem, sqs Receive/Delete, logs"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem"
        ]
        Resource = aws_dynamodb_table.orders_table.arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.orders_queue.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "worker_policy_attachment" {
  role       = aws_iam_role.worker_role.name
  policy_arn = aws_iam_policy.worker_policy.arn
}


# SNS Topic - Notificación pedido procesado
resource "aws_sns_topic" "order_processed_topic" {
  name = "order-processed-topic-dev"
}

# IAM Policy: publicará al topic SNS y logs (Attach a Worker Lambda role luego)
resource "aws_iam_policy" "worker_sns_policy" {
  name = "lambda-worker-sns-policy-dev"
  description = "Permite publicar en SNS topic de pedidos procesados y logs"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "sns:Publish"
        ],
        Resource = aws_sns_topic.order_processed_topic.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Adjunta esta nueva policy de SNS al worker (además de la de Dynamo/SQS)
resource "aws_iam_role_policy_attachment" "worker_sns_policy_attachment" {
  role       = aws_iam_role.worker_role.name
  policy_arn = aws_iam_policy.worker_sns_policy.arn
}


# Archivo ZIP para Lambda Ingestor
data "archive_file" "ingestor_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/ingestor.py"
  output_path = "${path.module}/../lambdas/ingestor.zip"
}

# Lambda Ingestor
resource "aws_lambda_function" "ingestor" {
  function_name = "ingestor-lambda-dev"
  handler       = "ingestor.handler"
  runtime       = "python3.10" # LocalStack soporta hasta Python 3.10 ya cada quien usa la que vea conveniente
  filename      = data.archive_file.ingestor_zip.output_path
  role          = aws_iam_role.ingestor_role.arn
  source_code_hash = data.archive_file.ingestor_zip.output_base64sha256
  timeout       = 10

  environment {
    variables = {
      SQS_QUEUE_URL = aws_sqs_queue.orders_queue.url
    }
  }
}

# Archivo ZIP para Lambda Worker
data "archive_file" "worker_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/worker.py"
  output_path = "${path.module}/../lambdas/worker.zip"
}

# Lambda Worker
resource "aws_lambda_function" "worker" {
  function_name = "worker-lambda-dev"
  handler       = "worker.handler"
  runtime       = "python3.10"
  filename      = data.archive_file.worker_zip.output_path
  role          = aws_iam_role.worker_role.arn
  source_code_hash = data.archive_file.worker_zip.output_base64sha256

  environment {
    variables = {
      ORDERS_TABLE_NAME = aws_dynamodb_table.orders_table.name
      SNS_TOPIC_ARN     = aws_sns_topic.order_processed_topic.arn
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_to_worker" {
  event_source_arn = aws_sqs_queue.orders_queue.arn
  function_name    = aws_lambda_function.worker.arn
  batch_size       = 10
  enabled          = true
}

# Archivo ZIP para Lambda Reader
data "archive_file" "reader_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/reader.py"
  output_path = "${path.module}/../lambdas/reader.zip"
}

# IAM Role para Reader Lambda (solo lectura DynamoDB + logs)
resource "aws_iam_role" "reader_role" {
  name = "lambda-reader-role-dev"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "reader_policy" {
  name        = "lambda-reader-policy-dev"
  description = "Permite leer (scan) de la tabla DynamoDB"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.orders_table.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "reader_policy_attachment" {
  role       = aws_iam_role.reader_role.name
  policy_arn = aws_iam_policy.reader_policy.arn
}

# Lambda Reader
resource "aws_lambda_function" "reader" {
  function_name = "reader-lambda-dev"
  handler       = "reader.handler"
  runtime       = "python3.10"
  filename      = data.archive_file.reader_zip.output_path
  role          = aws_iam_role.reader_role.arn
  source_code_hash = data.archive_file.reader_zip.output_base64sha256

  environment {
    variables = {
      ORDERS_TABLE_NAME = aws_dynamodb_table.orders_table.name
    }
  }
}

# 1. API REST Gateway
resource "aws_api_gateway_rest_api" "orders_api" {
  name        = "orders-api-dev"
  description = "API para procesamiento de pedidos (LocalStack demo)"
}

# 2. /orders resource
resource "aws_api_gateway_resource" "orders_resource" {
  rest_api_id = aws_api_gateway_rest_api.orders_api.id
  parent_id   = aws_api_gateway_rest_api.orders_api.root_resource_id
  path_part   = "orders"
}

# 3. POST /orders (crear pedido)
resource "aws_api_gateway_method" "orders_post" {
  rest_api_id   = aws_api_gateway_rest_api.orders_api.id
  resource_id   = aws_api_gateway_resource.orders_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "orders_post_integration" {
  rest_api_id             = aws_api_gateway_rest_api.orders_api.id
  resource_id             = aws_api_gateway_resource.orders_resource.id
  http_method             = aws_api_gateway_method.orders_post.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.ingestor.invoke_arn
}

resource "aws_lambda_permission" "apigw_post" {
  statement_id  = "AllowAPIGatewayInvokePOST"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.orders_api.execution_arn}/*/*"
}

# 4. GET /orders (leer pedidos)
resource "aws_api_gateway_method" "orders_get" {
  rest_api_id   = aws_api_gateway_rest_api.orders_api.id
  resource_id   = aws_api_gateway_resource.orders_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "orders_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.orders_api.id
  resource_id             = aws_api_gateway_resource.orders_resource.id
  http_method             = aws_api_gateway_method.orders_get.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.reader.invoke_arn
}

resource "aws_lambda_permission" "apigw_get" {
  statement_id  = "AllowAPIGatewayInvokeGET"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.reader.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.orders_api.execution_arn}/*/*"
}

# 5. Despliegue de la API
resource "aws_api_gateway_deployment" "orders_api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.orders_api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.orders_resource.id,
      aws_api_gateway_method.orders_post.id,
      aws_api_gateway_integration.orders_post_integration.id,
      aws_api_gateway_method.orders_get.id,
      aws_api_gateway_integration.orders_get_integration.id,
    ]))
  }
}

resource "aws_api_gateway_stage" "orders_api_stage" {
  rest_api_id   = aws_api_gateway_rest_api.orders_api.id
  deployment_id = aws_api_gateway_deployment.orders_api_deployment.id
  stage_name    = "dev"
}

resource "aws_s3_bucket" "static_site" {
  bucket = "patrick-static-site"
  force_destroy = true
}

resource "aws_s3_bucket_website_configuration" "site_config" {
  bucket = aws_s3_bucket.static_site.id
  index_document {
    suffix = "dashboard.html"
  }
}


#SISTEMA DE FACTURACIÓN

# 1. Nuevo Bucket de S3 exclusivo para almacenar las facturas HTML
resource "aws_s3_bucket" "invoices_bucket" {
  bucket        = "patrick-facturas"
  force_destroy = true
}

# 2. Empaquetado en .zip de la nueva Lambda de facturas
data "archive_file" "invoice_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/invoice.py"
  output_path = "${path.module}/../lambdas/invoice.zip"
}

# 3. Rol e IAM Policy para dar permiso a la Lambda a escribir en el Bucket
resource "aws_iam_role" "invoice_role" {
  name = "lambda-invoice-role-dev"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_policy" "invoice_policy" {
  name = "lambda-invoice-policy-dev"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["s3:PutObject"], Resource = "${aws_s3_bucket.invoices_bucket.arn}/*" }]
  })
}

resource "aws_iam_role_policy_attachment" "invoice_attach" {
  role       = aws_iam_role.invoice_role.name
  policy_arn = aws_iam_policy.invoice_policy.arn
}

# 4. Creación de la Función Lambda
resource "aws_lambda_function" "invoice_lambda" {
  function_name    = "invoice-lambda-dev"
  handler          = "invoice.handler"
  runtime          = "python3.10"
  filename         = data.archive_file.invoice_zip.output_path
  role             = aws_iam_role.invoice_role.arn
  source_code_hash = data.archive_file.invoice_zip.output_base64sha256
}

# 5. Suscripción: Conectar la Lambda al Topic SNS de pedidos procesados
resource "aws_sns_topic_subscription" "sns_to_lambda_invoice" {
  topic_arn = aws_sns_topic.order_processed_topic.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.invoice_lambda.arn
}

# 6. Permiso para que SNS pueda "despertar" a la Lambda
resource "aws_lambda_permission" "sns_allow_invoice" {
  statement_id  = "AllowSNSInvokeInvoice"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.invoice_lambda.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.order_processed_topic.arn
}