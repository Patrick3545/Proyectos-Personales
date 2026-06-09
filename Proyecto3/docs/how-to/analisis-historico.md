# Cómo Realizar un Análisis Histórico Post-Carrera

Este proyecto separa la telemetría en tiempo real de los datos históricos. Para analizar los tiempos por vuelta, estrategias de neumáticos y diferencias después de una carrera, debes utilizar el dashboard dedicado de **Análisis Histórico**.

## 1. Acceder al Dashboard

1. Abre tu instancia de Grafana (típicamente `http://localhost:3000`).
2. Ve a **Dashboards** > **Formula 1**.
3. Selecciona el dashboard **Análisis Histórico Post-Carrera (F1 25)**.

## 2. Filtrar por Sesión y Piloto

Dado que InfluxDB guarda de forma persistente todas las sesiones que juegas, es vital filtrar la vista para no solapar datos históricos:

- **Variable `Sesión`**: En la esquina superior izquierda encontrarás un desplegable. Este menú formatea automáticamente el identificador interno del juego en fechas legibles (ej: `YYYY-MM-DDTHH:MM:SSZ - Carrera (...)`). Selecciona la fecha de la sesión que desees analizar.
- **Variable `Piloto`**: Selecciona a tu piloto de la parrilla para aislar su telemetría del resto de competidores.

> [!NOTE]
> **Sobre el selector de tiempo (Time Picker):** El dashboard histórico está programado internamente para ignorar el rango de tiempo global de Grafana (ej. *Last 24 hours*). Al seleccionar una `Sesión`, los paneles automáticamente cargarán toda la telemetría correspondiente a esa carrera buscando en un rango histórico de los últimos 30 días, sin que tengas que ajustar el reloj de la esquina superior derecha.

### Sistema de Intentos (Restarts)

Si durante una sesión reinicias la carrera (por ejemplo, desde el menú de pausa tras un accidente), el sistema de ingesta (`consumer`) detectará automáticamente la regresión en el número de vuelta. 

Para evitar que las vueltas del primer intento se mezclen con el segundo en los gráficos históricos, el sistema separa las telemetrías añadiendo un sufijo automático al final del identificador de sesión. Por tanto, en el desplegable de `Sesión` podrás ver:
- `... - Carrera (ID_Original)`: Tu primer intento.
- `... - Carrera (ID_Original-A2)`: Tu segundo intento (Attempt 2).
- `... - Carrera (ID_Original-A3)`: Tu tercer intento.

## 3. Paneles Clave

- **Tabla de Vueltas**: Un desglose completo vuelta a vuelta, mostrando tus sectores en milisegundos.
- **Evolución del Tiempo de Vuelta**: Un gráfico lineal para ver si fuiste constante o si tuviste caída de rendimiento (drop-off).
- **Degradación Térmica**: Visualiza cómo la temperatura superficial de los 4 neumáticos evolucionó a lo largo del stint.

## Diferencia con el Muro de Ingeniero

El dashboard principal (**Muro de Ingeniería de Pista**) está diseñado exclusivamente para el uso en tiempo real (segundo monitor o tablet). Dicho dashboard también cuenta con la variable de `Sesión` para garantizar que la pantalla en vivo siempre apunte a los datos correctos sin mezclarse con la telemetría de carreras anteriores.
