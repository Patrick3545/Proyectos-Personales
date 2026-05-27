# 🛒 PATRICKGEAR | Event-Driven Cloud E-Commerce

> **Ecosistema de comercio electrónico serverless de nivel empresarial.** > Una arquitectura guiada por eventos (Event-Driven) que emula servicios de AWS de forma 100% local, provisionada como Infraestructura como Código (IaC) y automatizada con integración continua inteligente.

![AWS](https://img.shields.io/badge/AWS-LocalStack-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/Python-Lambdas-3776AB?style=for-the-badge&logo=python&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

---

## Características Principales

* **Arquitectura Cloud a Coste Cero:** Emulación completa de servicios AWS (S3, SQS, SNS, DynamoDB, API Gateway, Lambda) utilizando **LocalStack**.
* **Totalmente Desacoplado:** Sistema asíncrono donde la ingesta de pedidos y su procesamiento en base de datos están separados por colas de mensajería, asegurando tolerancia a fallos y alta disponibilidad.
* **CI/CD Inteligente:** Pipeline construida con **GitHub Actions** (vía Self-Hosted Runner) que utiliza filtros de rutas para desplegar únicamente las capas modificadas (Frontend, Lambdas o Infraestructura), reduciendo el tiempo de despliegue a segundos.
* **Facturación Dinámica:** Generación automática de comprobantes de compra interactivos en HTML, inyectados en un bucket S3 privado con cabeceras de descarga directa.

---

## Topología de la Arquitectura

El flujo de datos transaccional sigue este ciclo de vida:

1. **Ingestión Síncrona:** El usuario compra en el frontend estático (`S3`). La petición entra por `API Gateway` y es recogida por la Lambda `Ingestor`.
2. **Encolamiento:** El Ingestor deposita un evento en una cola `SQS` y libera al usuario inmediatamente (HTTP 202).
3. **Procesamiento Lote:** Un `Worker` Lambda consume los mensajes de SQS, guarda el registro definitivo en `DynamoDB` y notifica el éxito publicando en un Topic `SNS`.
4. **Reacción Fan-out:** La Lambda de Facturación (`Invoice`), suscrita al SNS, genera un HTML y lo sube al bucket seguro `patrick-facturas`.

---

## Stack Tecnológico

| Capa | Tecnología Utilizada |
| :--- | :--- |
| **Infraestructura (IaC)** | Terraform |
| **Emulación Cloud** | LocalStack, Docker |
| **Cómputo** | AWS Lambda (Python 3.10) |
| **Bases de Datos** | Amazon DynamoDB (NoSQL) |
| **Mensajería / Eventos** | Amazon SQS, Amazon SNS |
| **Frontend / Almacenamiento** | Amazon S3, HTML5, CSS3, JS Vanilla |
| **API / Enrutamiento** | Amazon API Gateway |
| **Automatización** | GitHub Actions, Bash Scripts |

---

## 📂 Estructura del Proyecto

```text
📦 patrickgear-aws-localstack
 ┣ 📂 .github/workflows   # Configuración de la Pipeline inteligente (CI/CD)
 ┣ 📂 lambdas             # Código fuente de los microservicios en Python
 ┃ ┣ 📜 ingestor.py       # Recibe la petición web y la encola
 ┃ ┣ 📜 worker.py         # Procesa la cola y guarda en DynamoDB
 ┃ ┣ 📜 reader.py         # Consulta de base de datos para la interfaz web
 ┃ ┗ 📜 invoice.py        # Generador de facturas HTML reaccionando a SNS
 ┣ 📂 terraform           # Definición declarativa de toda la infraestructura
 ┃ ┣ 📜 main.tf           # Recursos core (S3, Dynamo, SQS, SNS, API Gateway, Lambdas)
 ┃ ┗ 📜 outputs.tf        # Exportación de endpoints dinámicos
 ┣ 📂 web                 # Interfaz de usuario E-commerce
 ┃ ┗ 📜 dashboard.html    # Single Page Application
 ┗ 📜 README.md
 ┃
 ┗ docker-compose.yml