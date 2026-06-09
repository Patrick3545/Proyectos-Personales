# Hola, soy Patrick Hurtado 👋

👨‍💻 **SysAdmin & MultiCloud Engineer / DevOps**

A punto de finalizar mi Máster en Ingeniería MultiCloud, Seguridad y DevOps en Madrid, España 🇪🇸.
Me apasiona todo el ecosistema cloud, la automatización y la cultura DevOps. He creado este repositorio con un fin muy claro: **aprender haciendo**.

Aquí iré publicando las diferentes pruebas, laboratorios y "trasteos" que vaya realizando para descubrir cómo funcionan realmente los servicios que nubes como Azure, AWS y GCP nos ofrecen. Mi objetivo es crear infraestructuras desde cero, romperlas y volverlas a levantar para entender la tecnología desde dentro.

## 🔭 ¿En qué he estado trabajando?

✅ **Proyecto 1 — Entorno híbrido con Azure Arc + Kubernetes + GitOps + Sentinel**
La idea fue coger una máquina local (VMware) y simular un entorno híbrido en el que:
- Automatizo la instalación/configuración base con Ansible.
- Administro un clúster de Kubernetes (K3s) con Azure Arc.
- Despliego una app con GitOps.
- Monto una alerta de accesos con Microsoft Sentinel para probar detección/monitorización.

✅ **Proyecto 2 — PATRICKGEAR | Event-Driven Cloud E-Commerce**
Ecosistema de comercio electrónico serverless de nivel empresarial, guiado por eventos (Event-Driven) y desplegado de forma 100% local.
- **Arquitectura Cloud a Coste Cero**: Emulación completa de servicios AWS (S3, SQS, SNS, DynamoDB, API Gateway, Lambda) utilizando LocalStack.
- **Totalmente Desacoplado**: Ingesta de pedidos separada del procesamiento en base de datos mediante colas de mensajería asíncronas para asegurar la tolerancia a fallos.
- **CI/CD Inteligente**: Pipeline construida con GitHub Actions que utiliza filtros de rutas para desplegar únicamente las capas modificadas en segundos.
- **Infraestructura como Código (IaC)**: Entorno aprovisionado de forma declarativa con Terraform.

✅ **Proyecto 3 — Pipeline de Telemetría UDP en Tiempo Real (F1)**  
Un proyecto On-Premise de ingesta masiva de datos estructurados para visualizar la telemetría del videojuego F1 25:
- **Ingesta de alta frecuencia** (60Hz UDP) con un **Parser Python** ultra-optimizado.
- Uso de **Redpanda (Kafka)** como búfer de mensajería para desacoplamiento y absorción de picos.
- Procesamiento asíncrono y *Batching* hacia **InfluxDB** (Base de datos Time-Series).
- Visualización analítica en vivo e histórica usando **Grafana** y lenguaje **Flux**.

## 🚀 Stack Tecnológico y Herramientas

He consolidado una base sólida en administración de sistemas y soporte de redes, orientando mi perfil hacia la automatización y la Infraestructura como Código (IaC). Mis herramientas y tecnologías clave incluyen:

- **Cloud:** Microsoft Azure, AWS y Google Cloud Platform (GCP).
- **Automatización (IaC y CI/CD):** Terraform, Ansible y CloudFormation.
- **Contenedores y Orquestación:** Docker y Kubernetes.
- **Monitorización:** Grafana con Prometheus.
- **Bases de Datos:** SQL.

## 🏆 Certificaciones Oficiales

Durante mi camino de aprendizaje, he ido validando mis conocimientos técnicos con las siguientes certificaciones oficiales:

☁️ **Microsoft Azure:**
- ✅ AZ-305: Solutions Architect Expert
- ✅ AZ-500: Security Engineer Associate
- ✅ AZ-104: Administrator Associate
- ✅ AZ-900: Azure Fundamentals

☁️ **Amazon Web Services (AWS):**
- ✅ SAA-C03: Solutions Architect – Associate

☁️ **Google Cloud Platform (GCP):**
- ✅ Google Associate Cloud Engineer

🐙 **GitHub:**
- ✅ GitHub Actions: GH-200

## 📫 Contacto

Si quieres charlar sobre cloud, DevOps, estudios o proyectos:
- **LinkedIn:** [www.linkedin.com/in/patrick-adonis-hurtado-contreras](https://www.linkedin.com/in/patrick-adonis-hurtado-contreras)
- **Email:** [hurtadocontreraspatrick@gmail.com](mailto:hurtadocontreraspatrick@gmail.com)
