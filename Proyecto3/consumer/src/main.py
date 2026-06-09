import json
import sys
import time
import logging
from typing import Dict, Any

# pyrefly: ignore [missing-import]
from kafka import KafkaConsumer
# pyrefly: ignore [missing-import]
from influxdb_client import InfluxDBClient, Point
# pyrefly: ignore [missing-import]
from influxdb_client.client.write_api import SYNCHRONOUS

# --- CONFIGURACIÓN ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

KAFKA_BROKER = "redpanda:9092"
TOPICS = ["f1-telemetry-fast", "f1-race-status", "f1-lap-data", "f1-session-history", "f1-motion"]

INFLUX_URL = "http://influxdb:8086"
INFLUX_TOKEN = "token1234567890"
INFLUX_ORG = "red-bull-racing"
INFLUX_BUCKET = "f1_telemetry_raw"

# --- CONSTANTES DE PAQUETES ---
PACKET_MOTION = 0
PACKET_LAP_DATA = 2
PACKET_TELEMETRY = 6
PACKET_STATUS = 7
PACKET_SESSION_HISTORY = 11

TYRE_COMPOUNDS = {
    16: "SOFT",
    17: "MEDIUM",
    18: "HARD",
    7: "INTER",
    8: "WET"
}

def create_telemetry_point(session_uid: str, driver_name: str, is_player: str, car_idx: int) -> Point:
    """
    Crea un punto base de InfluxDB para la medición de telemetría rápida (telemetry_fast).

    Args:
        session_uid (str): Identificador único de la sesión (ej. '123456789' o '123456789-A2').
        driver_name (str): Nombre del piloto.
        is_player (str): 'true' si es el jugador local, 'false' en caso contrario.
        car_idx (int): Índice del coche (0-21).

    Returns:
        Point: Instancia configurada con tags estructurales lista para recibir campos dinámicos.
    """
    return Point("telemetry_fast")\
        .tag("session_uid", session_uid)\
        .tag("driver_name", driver_name)\
        .tag("is_player", is_player)\
        .tag("car_idx", str(car_idx))

def create_lap_history_point(session_uid: str, driver_name: str, is_player: str, lap_num: int) -> Point:
    """
    Crea un punto base de InfluxDB para el registro histórico de vueltas (lap_history).

    Args:
        session_uid (str): Identificador único de la sesión.
        driver_name (str): Nombre del piloto.
        is_player (str): 'true' si es el jugador local, 'false' en caso contrario.
        lap_num (int): Número de vuelta registrada.

    Returns:
        Point: Instancia de punto de datos para InfluxDB.
    """
    return Point("lap_history")\
        .tag("session_uid", session_uid)\
        .tag("driver_name", driver_name)\
        .tag("is_player", is_player)\
        .tag("lap_num", str(lap_num))

session_attempts: Dict[str, int] = {}
session_max_lap: Dict[str, int] = {}

def get_effective_session_uid(base_uid: str) -> str:
    """
    Determina el identificador efectivo de la sesión considerando los posibles reinicios de carrera.

    Si se detecta un reinicio (recesión en el contador de vueltas), se anexa un sufijo
    al identificador original (ej. '-A2', '-A3') para aislar la telemetría histórica.

    Args:
        base_uid (str): Identificador crudo proveniente del paquete UDP.

    Returns:
        str: Identificador efectivo con sufijo de intento si aplica.
    """
    if not base_uid or base_uid == "0": return base_uid
    attempt = session_attempts.get(base_uid, 1)
    if attempt > 1:
        return f"{base_uid}-A{attempt}"
    return base_uid

def main() -> None:
    """
    Bucle principal de ejecución del consumidor asíncrono.

    Responsabilidades:
    1. Inicializar las conexiones a InfluxDB (escritura) y Redpanda/Kafka (lectura).
    2. Consumir de manera ininterrumpida los mensajes JSON estructurados procedentes del `parser`.
    3. Detectar reinicios de sesión (restarts) vigilando anómalas bajadas de vuelta.
    4. Traducir el payload JSON a Line Protocol Point y escribirlo por lotes (Batch) en InfluxDB.
    """
    logger.info("--- Consumidor de Telemetría v7.2 (Optimized & Clean) ---")
    
    try:
        db_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        write_api = db_client.write_api(write_options=SYNCHRONOUS)
        logger.info("Conectado a InfluxDB correctamente.")
    except Exception as e:
        logger.error(f"Error inicializando InfluxDB: {e}")
        sys.exit(1)

    consumer = None
    while consumer is None:
        try:
            consumer = KafkaConsumer(
                *TOPICS, 
                bootstrap_servers=[KAFKA_BROKER],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest'
            )
            logger.info("¡Suscrito a Kafka! Ingestando...")
        except Exception as e:
            logger.warning("Esperando a que Kafka (Redpanda) esté disponible...")
            time.sleep(2)

    for message in consumer:
        try:
            payload: Dict[str, Any] = message.value
            session_uid: str = str(payload.get("session_uid", ""))
            player_car_idx: int = payload.get("player_car_index", -1)
            packet_id: int = payload.get("packet_id", -1)
            cars_list: list = payload.get("cars", [])
            
            # Detect Restarts (drop to lap 1)
            if packet_id == PACKET_LAP_DATA and session_uid != "0" and session_uid != "":
                for car in cars_list:
                    if car.get("car_idx") == player_car_idx:
                        curr_lap = int(car.get("current_lap_num", 1))
                        max_lap = session_max_lap.get(session_uid, 0)
                        if curr_lap < max_lap and curr_lap <= 1 and max_lap > 1:
                            session_attempts[session_uid] = session_attempts.get(session_uid, 1) + 1
                            session_max_lap[session_uid] = curr_lap
                            logger.info(f"Restart detected for session {session_uid}. New attempt: {session_attempts[session_uid]}")
                        elif curr_lap > max_lap:
                            session_max_lap[session_uid] = curr_lap
                        break
            
            effective_session_uid = get_effective_session_uid(session_uid)
            points_batch = []
            
            for car in cars_list:
                car_idx = car.get("car_idx")
                driver_name = car.get("driver_name", "Unknown")
                is_player = "true" if car_idx == player_car_idx else "false"

                point = create_telemetry_point(effective_session_uid, driver_name, is_player, car_idx)

                if packet_id == PACKET_TELEMETRY:
                    point.field("speed", int(car.get("speed", 0)))\
                         .field("throttle", float(car.get("throttle", 0)))\
                         .field("brake", float(car.get("brake", 0)))\
                         .field("gear", int(car.get("gear", 0)))\
                         .field("engine_rpm", int(car.get("engine_rpm", 0)))\
                         .field("engine_temperature", int(car.get("engine_temperature", 0)))
                    
                    tyres = car.get("tyres_surf_temp", {})
                    point.field("tyre_temp_surf_rl", int(tyres.get("rl", 0)))\
                         .field("tyre_temp_surf_rr", int(tyres.get("rr", 0)))\
                         .field("tyre_temp_surf_fl", int(tyres.get("fl", 0)))\
                         .field("tyre_temp_surf_fr", int(tyres.get("fr", 0)))
                    
                    brakes = car.get("brakes_temp", {})
                    point.field("brake_temp_rl", int(brakes.get("rl", 0)))\
                         .field("brake_temp_rr", int(brakes.get("rr", 0)))\
                         .field("brake_temp_fl", int(brakes.get("fl", 0)))\
                         .field("brake_temp_fr", int(brakes.get("fr", 0)))
                
                elif packet_id == PACKET_STATUS:
                    tyre_id = car.get("visual_tyre_compound", 0)
                    tyre_str = TYRE_COMPOUNDS.get(tyre_id, "UNKNOWN")
                    point.field("fuel_in_tank", float(car.get("fuel_in_tank", 0)))\
                         .field("fuel_remaining_laps", float(car.get("fuel_remaining_laps", 0)))\
                         .field("ers_store_energy_pct", float(car.get("ers_store_energy_pct", 0)))\
                         .field("ers_deploy_mode", int(car.get("ers_deploy_mode", 0)))\
                         .field("tyre_compound", tyre_str)\
                         .field("tyre_age", int(car.get("tyres_age_laps", 0)))\
                         .field("fia_flags", int(car.get("fia_flags", 0)))
                         
                elif packet_id == PACKET_LAP_DATA:
                    point.field("last_lap_time", float(car.get("last_lap_time_ms", 0)))\
                         .field("current_lap_time", float(car.get("current_lap_time_ms", 0)))\
                         .field("sector1_time", float(car.get("sector1_time_ms", 0)) / 1000.0)\
                         .field("sector2_time", float(car.get("sector2_time_ms", 0)) / 1000.0)\
                         .field("sector3_time", float(car.get("sector3_time_ms", 0)) / 1000.0)\
                         .field("car_position", int(car.get("car_position", 0)))\
                         .field("current_lap_num", int(car.get("current_lap_num", 0)))\
                         .field("delta_front", float(car.get("delta_front_ms", 0)) / 1000.0)\
                         .field("delta_leader", float(car.get("delta_leader_ms", 0)) / 1000.0)

                elif packet_id == PACKET_SESSION_HISTORY:
                    for lap in car.get("laps", []):
                        lap_num = lap.get("lap_num", 0)
                        hist_point = create_lap_history_point(effective_session_uid, driver_name, is_player, lap_num)\
                            .field("lap_time", float(lap.get("lap_time_ms", 0)))\
                            .field("sector1_time", float(lap.get("sector1_time_ms", 0)) / 1000.0)\
                            .field("sector2_time", float(lap.get("sector2_time_ms", 0)) / 1000.0)\
                            .field("sector3_time", float(lap.get("sector3_time_ms", 0)) / 1000.0)\
                            .field("is_valid", int(lap.get("is_valid", 0)))
                        points_batch.append(hist_point)

                elif packet_id == PACKET_MOTION:
                    point.field("world_x", float(car.get("world_x", 0)))\
                         .field("world_z", float(car.get("world_z", 0)))

                if packet_id in [PACKET_MOTION, PACKET_LAP_DATA, PACKET_TELEMETRY, PACKET_STATUS]:
                    points_batch.append(point)

            if points_batch:
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points_batch)
                # logger.debug(f"Successfully wrote {len(points_batch)} points to InfluxDB (packet_id={packet_id})")

        except Exception as e:
            logger.error(f"Error in consumer loop: {e}", exc_info=True)
            continue

if __name__ == "__main__":
    main()