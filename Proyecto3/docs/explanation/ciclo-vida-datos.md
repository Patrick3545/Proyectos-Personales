# Explicación: El Ciclo de Vida de los Datos (Time-Series)

Este documento explora las razones arquitectónicas detrás de cómo viaja la telemetría en nuestro proyecto, desde el videojuego hasta el renderizado final en Grafana.

## El problema de la Ingesta Directa

En un inicio, podríamos pensar en escribir un único script en Python que lea el socket UDP del juego F1 y ejecute comandos `INSERT` directamente sobre una base de datos. Sin embargo, el juego F1 envía paquetes a una tasa abrumadora (60Hz para 22 coches, resultando en decenas de miles de métricas por minuto).

Si conectáramos el socket de red directamente con una base de datos Time-Series como InfluxDB usando peticiones HTTP síncronas por cada paquete:
1. El cuello de botella de latencia de red ahogaría el socket UDP, provocando pérdida masiva de paquetes (Packet Loss).
2. La base de datos sufriría de sobrecarga de I/O al intentar realizar miles de pequeñas escrituras por segundo en el disco.

## La Solución: Desacoplamiento y Búferes

Para solucionar esto, implementamos una arquitectura en tres etapas:

### 1. El Parser (Productor Inmediato)
El `parser` en Python tiene una única misión crítica: vaciar el socket UDP lo más rápido posible. Escrito sin bucles asíncronos complejos, simplemente lee bytes C, los decodifica y escupe JSONs crudos hacia **Redpanda** (Kafka).
Kafka es un sistema de mensajería distribuida optimizado para latencia sub-milisegundo. Actúa como un *búfer elástico*: si la base de datos se ralentiza, Kafka retiene los mensajes en memoria/disco sin que el juego de F1 note ninguna latencia.

### 2. El Consumer (Lógica Lenta)
El `consumer` extrae los mensajes de Redpanda a su propio ritmo. Aquí es donde ocurre la magia costosa computacionalmente:
- Detecta caídas de vueltas para inferir reinicios de carrera (creando los sufijos `-A2`, `-A3`).
- Transforma los diccionarios JSON en objetos `Point` (Line Protocol) nativos de InfluxDB.

### 3. Asynchronous Batching en InfluxDB
En lugar de hacer un HTTP POST por cada paquete, el `consumer` aprovecha el *Batching*. Acumula miles de puntos en memoria RAM y realiza una inserción masiva a InfluxDB cada cierto tiempo o cuando alcanza un tamaño crítico de array.
Las bases de datos columnares y de series temporales (Time-Series) están matemáticamente optimizadas para inserciones masivas de datos continuos, lo que reduce el consumo de CPU y disco a niveles mínimos.

## Conclusión

El viaje de un dato desde el freno de tu volante hasta Grafana recorre un puente cuidadosamente diseñado:
`UDP -> C Struct -> JSON -> Kafka/Redpanda -> Python Polling -> Line Protocol Batching -> InfluxDB -> Flux Query -> Grafana.`

Gracias a este pipeline, la visualización en el **Muro del Ingeniero** fluye en tiempo real sin importar si tu disco duro o CPU tienen picos de uso repentinos.
