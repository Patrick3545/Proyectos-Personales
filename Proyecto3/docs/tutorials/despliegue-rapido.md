# Tutorial: Despliegue Rápido del Pipeline F1 🏎️

> [!NOTE]
> Este tutorial te guiará paso a paso para instalar y ejecutar el F1 Telemetry Pipeline en tu máquina local, conectarlo con el juego F1 25 y visualizar los datos en Grafana en menos de 10 minutos.

## 1. Requisitos Previos

Antes de comenzar, asegúrate de tener instalados:
- **Docker**: Necesario para correr los contenedores. [Instalar Docker Desktop](https://docs.docker.com/get-docker/).
- **F1 25**: El videojuego oficial instalado en la misma red local o máquina.

## 2. Iniciar la Infraestructura

Abre una terminal, navega a la raíz del repositorio y ejecuta:

```bash
docker compose up -d --build
```

Este comando levantará 5 contenedores interconectados mediante una red dedicada (`f1-mesh`):
1. **Redpanda** (Broker de mensajes)
2. **Redpanda Console** (Interfaz web para ver los tópicos)
3. **InfluxDB** (Base de datos Time-Series)
4. **Grafana** (Visualizador de Dashboards)
5. **Parser y Consumer** (Los scripts Python que procesan los datos)

## 3. Verificar los Servicios

Una vez que los contenedores estén corriendo, verifica que puedas acceder a los servicios clave:

- **Grafana**: [http://localhost:3000](http://localhost:3000) (Usuario/Clave: `admin` / `admin`).
- **Redpanda Console**: [http://localhost:8080](http://localhost:8080) (Aquí verás los tópicos de Kafka).
- **InfluxDB**: [http://localhost:8086](http://localhost:8086)

## 4. Configurar F1 25

Para que el juego empiece a enviar datos a nuestro `Parser`:

1. Abre F1 25 y ve a **Opciones** > **Ajustes de Telemetría**.
2. **Activar Telemetría UDP**: Ponlo en `Sí`.
3. **Dirección IP UDP**: Si Docker y el juego están en la misma PC, usa `127.0.0.1`. Si están en máquinas distintas, usa la IP local del equipo con Docker (ej. `192.168.1.50`).
4. **Puerto UDP**: Configúralo en `20777` (es el puerto expuesto por nuestro contenedor `f1-parser`).
5. **Formato de Telemetría UDP**: Asegúrate de que está seleccionado **F1 25**.
6. **Velocidad de Envío**: Recomendamos 60Hz o 120Hz para máxima fidelidad, aunque requerirá más ancho de banda.

## 5. Visualizar la Telemetría

1. Inicia una sesión de Contra Reloj (Time Trial) o una carrera en F1 25.
2. Abre **Grafana** en tu navegador.
3. El proyecto incluye auto-provisioning. En la sección "Dashboards" a la izquierda, busca **"Muro del Ingeniero"**.
4. ¡Acelera en el juego! Deberías ver los medidores de RPM, Velocidad y Temperaturas cobrando vida en tiempo real.

> [!TIP]
> Si los datos no aparecen, revisa los logs del parser con:
> `docker logs f1-parser -f`
> Deberías ver mensajes diciendo "Parsed and sent packet..." si los paquetes UDP están llegando correctamente.

---
**Siguiente paso:** ¿Quieres modificar qué datos se guardan? Revisa la guía en [Cómo agregar nueva telemetría](../how-to/agregar-telemetria.md).
