FROM python:3.11-slim

# Evita que Python escriba archivos .pyc en el disco
ENV PYTHONDONTWRITEBYTECODE=1
# Evita que Python almacene en búfer los logs (útil para ver los prints en tiempo real con docker logs)
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copiamos primero solo las dependencias para aprovechar la caché de capas de Docker
COPY requirements.txt /app/

# Instalamos las librerías sin almacenar caché de pip para reducir el tamaño de la imagen
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código fuente
COPY src/ /app/src/

# Exponemos el puerto UDP donde el F1 25 enviará los datos
EXPOSE 20777/udp

CMD ["python", "src/main.py"]