# Tutorial: Cómo crear paneles Flux personalizados en Grafana

Este tutorial te guiará paso a paso para crear tu propio panel de análisis en Grafana utilizando el lenguaje de consultas Flux, respetando las variables de sesión que hemos configurado en este proyecto.

## Requisitos previos

- Tener la infraestructura de contenedores iniciada (`docker-compose up -d`).
- Haber registrado al menos una sesión de juego (la variable `$session` debe tener datos).
- Conocimientos básicos de cómo navegar por la interfaz de Grafana.

## Paso 1: Crear un Panel Vacío

1. Abre Grafana en [http://localhost:3000](http://localhost:3000) (admin/admin).
2. Ve al dashboard **Análisis Histórico Post-Carrera**.
3. Haz clic en el botón superior derecho **Add panel** > **Add a new panel**.

## Paso 2: Configurar el Origen de Datos

En la sección inferior del panel (pestaña "Query"):
1. Asegúrate de que el **Data source** seleccionado es `InfluxDB` (o el nombre que le hayas dado a tu conexión con Influx).
2. Verifica que el editor esté en modo **Flux**. Si ves un constructor visual anticuado, pulsa el botón que permite escribir código crudo.

## Paso 3: Escribir la Consulta Flux (Ignorando el Time Picker)

El secreto para que el panel histórico funcione sin que importe qué rango de tiempo haya seleccionado el usuario en la esquina superior derecha (Time Picker) es forzar la consulta a un tiempo absoluto (ej. los últimos 30 días).

Copia y pega este bloque de código base:

```flux
from(bucket: "f1_telemetry_raw")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "lap_history")
  |> filter(fn: (r) => r["session_uid"] =~ /^${session:regex}$/)
  |> filter(fn: (r) => r["driver_name"] == "${driver}")
  |> filter(fn: (r) => r["_field"] == "lap_time")
```

### Entendiendo la consulta:
- `range(start: -30d)`: Ignora el `$__timeFilter` de Grafana. Busca en toda la base de datos de los últimos 30 días.
- `r["session_uid"] =~ /^${session:regex}$/`: **¡Crítico!** Dado que el desplegable "Sesión" formatea las fechas visualmente, necesitamos usar `:regex` para que Grafana inyecte el identificador crudo (ej. `123456789-A2`) correctamente en la consulta.
- `r["driver_name"] == "${driver}"`: Filtra la telemetría usando la variable del piloto seleccionado.

## Paso 4: Dar Formato y Guardar

1. En el panel lateral derecho, busca la sección **Standard options**.
2. Cambia la unidad (`Unit`) según lo que estés midiendo (por ejemplo, `Time > milliseconds` si estás midiendo tiempos de vuelta).
3. Ponle un título descriptivo a tu panel.
4. Pulsa **Apply** (esquina superior derecha) y luego **Save dashboard**.

¡Enhorabuena! Has creado un panel resistente a fallos de tiempo, totalmente integrado con nuestro sistema de "Intentos" (`-A2`) y variables dinámicas.
