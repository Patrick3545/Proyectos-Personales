output "orders_queue_url" {
  value       = aws_sqs_queue.orders_queue.id
  description = "URL SQS creada, siempre local."
}
output "orders_queue_arn" {
  value       = aws_sqs_queue.orders_queue.arn
  description = "ARN local de la cola de pedidos."
}
output "lambda_ingestor_role_arn" {
  value       = aws_iam_role.ingestor_role.arn
  description = "ARN del role IAM para el Ingestor Lambda."
}

output "orders_table_name" {
  value       = aws_dynamodb_table.orders_table.name
  description = "Nombre de la tabla DynamoDB Orders"
}
output "orders_table_arn" {
  value       = aws_dynamodb_table.orders_table.arn
  description = "ARN local de la tabla de pedidos"
}
output "lambda_worker_role_arn" {
  value       = aws_iam_role.worker_role.arn
  description = "ARN del role IAM para el Worker Lambda"
}

output "order_processed_topic_arn" {
  value       = aws_sns_topic.order_processed_topic.arn
  description = "ARN del topic SNS usado para notificar procesamiento de pedidos"
}

output "ingestor_lambda_arn" {
  value       = aws_lambda_function.ingestor.arn
  description = "ARN de la Lambda Ingestor principal"
}
output "worker_lambda_arn" {
  value       = aws_lambda_function.worker.arn
  description = "ARN de la Lambda Worker"
}

output "reader_lambda_arn" {
  value       = aws_lambda_function.reader.arn
  description = "ARN de la Lambda Reader"
}

output "orders_api_url_localstack" {
  value = "http://localhost:4566/restapis/${aws_api_gateway_rest_api.orders_api.id}/dev/_user_request_/orders"
  description = "Endpoint localstack real de /orders"
}