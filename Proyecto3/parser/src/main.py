import socket
import struct
import sys
import json
import time
import logging
from typing import Dict, List, Any

# pyrefly: ignore [missing-import]
from kafka import KafkaProducer

# --- CONFIGURACIÓN ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

UDP_IP = "0.0.0.0"
UDP_PORT = 20777
KAFKA_BROKER = "redpanda:9092"

# --- CONSTANTES DE PAQUETES ---
PACKET_MOTION = 0
PACKET_LAP_DATA = 2
PACKET_PARTICIPANTS = 4
PACKET_TELEMETRY = 6
PACKET_STATUS = 7
PACKET_SESSION_HISTORY = 11

TOPIC_MAPPING = {
    PACKET_PARTICIPANTS: "f1-session-metadata",
    PACKET_LAP_DATA: "f1-lap-data",
    PACKET_TELEMETRY: "f1-telemetry-fast",
    PACKET_STATUS: "f1-race-status",
    PACKET_SESSION_HISTORY: "f1-session-history",
    PACKET_MOTION: "f1-motion"
}

# --- FORMATOS MAESTROS DE ALINEACIÓN ---
HEADER_FORMAT = "<HBBBBBQfIIBB"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

PARTICIPANT_FORMAT = "<BBBBBBB32sBBHBB12s"
PARTICIPANT_SIZE = struct.calcsize(PARTICIPANT_FORMAT)

TELEMETRY_CAR_FORMAT = "<HfffbbHBBH4H4B4BH4f4B"
TELEMETRY_CAR_SIZE = struct.calcsize(TELEMETRY_CAR_FORMAT)

STATUS_CAR_FORMAT = "<BBBBBfffHHBBHBBBbfffBfffB"
STATUS_CAR_SIZE = struct.calcsize(STATUS_CAR_FORMAT)

LAP_DATA_FORMAT = "<IIHBHBHBHBfff15BHHBfB"
LAP_DATA_SIZE = struct.calcsize(LAP_DATA_FORMAT)

LAP_HISTORY_FORMAT = "<IHBHBHBB"
LAP_HISTORY_SIZE = struct.calcsize(LAP_HISTORY_FORMAT)

MOTION_CAR_FORMAT = "<ffffffhhhhhhffffff"
MOTION_CAR_SIZE = struct.calcsize(MOTION_CAR_FORMAT)

# --- ESTADO GLOBAL ---
DRIVER_MAP: Dict[int, str] = {}
PARTICIPANTS_RECEIVED: bool = False

def init_kafka_producer() -> KafkaProducer:
    """
    Inicializa y devuelve el cliente productor de Kafka/Redpanda.

    El productor está configurado para serializar los mensajes a JSON codificado en UTF-8.
    Utiliza acks=1 para equilibrar latencia y durabilidad en la ingesta.

    Returns:
        KafkaProducer: Instancia activa del productor.
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks=1
        )
        logger.info("Conectado a Kafka exitosamente.")
        return producer
    except Exception as e:
        logger.error(f"Error inicializando Kafka: {e}")
        sys.exit(1)

def parse_participants_packet(data: bytes) -> None:
    """
    Desempaqueta el paquete binario de participantes (Packet ID 4) y actualiza el DRIVER_MAP global.

    Este paquete contiene los nombres, nacionalidades y telemetría pública de los 22 pilotos.
    La función decodifica las cadenas nulas terminadas en C a strings en Python.

    Args:
        data (bytes): Payload binario UDP crudo.
    """
    global DRIVER_MAP, PARTICIPANTS_RECEIVED
    offset = HEADER_SIZE + 1 
    for i in range(22):
        try:
            unpacked = struct.unpack_from(PARTICIPANT_FORMAT, data, offset)
            name = unpacked[7].decode('utf-8', errors='ignore').split('\x00')[0].strip()
            if name and not name.startswith("Piloto"):
                DRIVER_MAP[i] = name
                PARTICIPANTS_RECEIVED = True
            offset += PARTICIPANT_SIZE
        except struct.error:
            break

def parse_telemetry_packet(data: bytes) -> List[Dict[str, Any]]:
    """
    Desempaqueta el paquete de telemetría dinámica (Packet ID 6).

    Extrae métricas como velocidad, freno, acelerador, marchas y temperaturas del motor.

    Args:
        data (bytes): Payload binario UDP crudo.

    Returns:
        List[Dict[str, Any]]: Lista de diccionarios, uno por cada coche activo, con su telemetría decodificada.
    """
    cars = []
    offset = HEADER_SIZE
    for i in range(22):
        try:
            unpacked = struct.unpack_from(TELEMETRY_CAR_FORMAT, data, offset)
            if i in DRIVER_MAP:
                cars.append({
                    "car_idx": i, "driver_name": DRIVER_MAP[i],
                    "speed": unpacked[0], "throttle": unpacked[1], "brake": unpacked[3],
                    "gear": unpacked[5], "engine_rpm": unpacked[6], "engine_temperature": unpacked[22],
                    "brakes_temp": {"rl": unpacked[10], "rr": unpacked[11], "fl": unpacked[12], "fr": unpacked[13]},
                    "tyres_surf_temp": {"rl": unpacked[14], "rr": unpacked[15], "fl": unpacked[16], "fr": unpacked[17]}
                })
            offset += TELEMETRY_CAR_SIZE
        except struct.error:
            break
    return cars

def parse_status_packet(data: bytes) -> List[Dict[str, Any]]:
    cars = []
    offset = HEADER_SIZE
    for i in range(22):
        try:
            unpacked = struct.unpack_from(STATUS_CAR_FORMAT, data, offset)
            raw_ers = unpacked[19]
            ers_percentage = max(0.0, min(100.0, round((raw_ers / 4000000.0) * 100.0, 1)))

            if i in DRIVER_MAP:
                cars.append({
                    "car_idx": i,
                    "driver_name": DRIVER_MAP[i],
                    "fuel_in_tank": round(unpacked[5], 2),
                    "fuel_remaining_laps": round(unpacked[7], 2),
                    "ers_store_energy_pct": ers_percentage,
                    "ers_deploy_mode": unpacked[20],
                    "visual_tyre_compound": unpacked[14],
                    "tyres_age_laps": unpacked[15],
                    "fia_flags": unpacked[16]
                })
            offset += STATUS_CAR_SIZE
        except struct.error:
            break
    return cars

def parse_lap_packet(data: bytes) -> List[Dict[str, Any]]:
    cars = []
    offset = HEADER_SIZE
    for i in range(22):
        try:
            unpacked = struct.unpack_from(LAP_DATA_FORMAT, data, offset)
            last_lap_ms = unpacked[0]
            current_lap_ms = unpacked[1]
            
            s1_ms = (unpacked[3] * 60 * 1000) + unpacked[2] if unpacked[2] > 0 or unpacked[3] > 0 else 0
            s2_ms = (unpacked[5] * 60 * 1000) + unpacked[4] if unpacked[4] > 0 or unpacked[5] > 0 else 0
            
            s3_ms = last_lap_ms - s1_ms - s2_ms if (last_lap_ms > 0 and s1_ms > 0 and s2_ms > 0) else 0
            if s3_ms < 0: s3_ms = 0

            delta_front_ms = (unpacked[7] * 60 * 1000) + unpacked[6] if unpacked[6] > 0 or unpacked[7] > 0 else 0
            delta_leader_ms = (unpacked[9] * 60 * 1000) + unpacked[8] if unpacked[8] > 0 or unpacked[9] > 0 else 0

            if i in DRIVER_MAP:
                cars.append({
                    "car_idx": i, "driver_name": DRIVER_MAP[i],
                    "last_lap_time_ms": last_lap_ms,
                    "current_lap_time_ms": current_lap_ms,
                    "sector1_time_ms": s1_ms,
                    "sector2_time_ms": s2_ms,
                    "sector3_time_ms": s3_ms,
                    "car_position": unpacked[13],
                    "current_lap_num": unpacked[14],
                    "delta_front_ms": delta_front_ms,
                    "delta_leader_ms": delta_leader_ms
                })
            offset += LAP_DATA_SIZE
        except struct.error:
            break
    return cars

def parse_session_history_packet(data: bytes) -> List[Dict[str, Any]]:
    offset = HEADER_SIZE
    try:
        unpacked_meta = struct.unpack_from("<BBBBBBB", data, offset)
    except struct.error:
        return []
        
    car_idx = unpacked_meta[0]
    num_laps = unpacked_meta[1]
    
    laps = []
    offset += 7
    
    for i in range(num_laps):
        lap_data_offset = offset + (i * LAP_HISTORY_SIZE)
        try:
            unpacked_lap = struct.unpack_from(LAP_HISTORY_FORMAT, data, lap_data_offset)
        except struct.error:
            break
            
        lap_time_ms = unpacked_lap[0]
        s1_ms = (unpacked_lap[2] * 60 * 1000) + unpacked_lap[1] if unpacked_lap[1] > 0 or unpacked_lap[2] > 0 else 0
        s2_ms = (unpacked_lap[4] * 60 * 1000) + unpacked_lap[3] if unpacked_lap[3] > 0 or unpacked_lap[4] > 0 else 0
        s3_ms = (unpacked_lap[6] * 60 * 1000) + unpacked_lap[5] if unpacked_lap[5] > 0 or unpacked_lap[6] > 0 else 0
        valid_flags = unpacked_lap[7]
        
        if lap_time_ms > 0:
            laps.append({
                "lap_num": i + 1,
                "lap_time_ms": lap_time_ms,
                "sector1_time_ms": s1_ms,
                "sector2_time_ms": s2_ms,
                "sector3_time_ms": s3_ms,
                "is_valid": valid_flags & 0x01
            })
            
    if car_idx not in DRIVER_MAP:
        return []
    return [{
        "car_idx": car_idx,
        "driver_name": DRIVER_MAP[car_idx],
        "laps": laps
    }]

def parse_motion_packet(data: bytes) -> List[Dict[str, Any]]:
    cars = []
    offset = HEADER_SIZE
    for i in range(22):
        try:
            unpacked = struct.unpack_from(MOTION_CAR_FORMAT, data, offset)
            if i in DRIVER_MAP:
                cars.append({
                    "car_idx": i,
                    "driver_name": DRIVER_MAP[i],
                    "world_x": unpacked[0],
                    "world_z": unpacked[2]
                })
            offset += MOTION_CAR_SIZE
        except struct.error:
            break
    return cars

def main() -> None:
    """
    Bucle principal de ingesta de red UDP.

    Abre un socket C nativo de bajo nivel para capturar paquetes UDP de F1 25 a máxima velocidad.
    El bucle extrae la cabecera (Packet ID), enruta el desempaquetado binario (`struct`) 
    según el ID y envía un diccionario JSON resultante al clúster de Kafka (Redpanda).
    """
    logger.info("--- Ingestor UDP F1 25 v7.1 (Optimized & Clean) ---")
    producer = init_kafka_producer()
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        logger.info(f"Escuchando paquetes UDP en {UDP_IP}:{UDP_PORT}")
    except OSError as e:
        logger.error(f"Error al enlazar el socket UDP: {e}")
        sys.exit(1)

    last_motion_time = 0.0

    while True:
        try:
            data, addr = sock.recvfrom(2048)
            if len(data) < HEADER_SIZE:
                continue
                
            header = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
            packet_id, session_uid, player_car_idx = header[5], str(header[6]), header[10]

            if packet_id == PACKET_MOTION:
                current_time = time.time()
                if current_time - last_motion_time < 0.2:
                    continue
                last_motion_time = current_time

            if packet_id == PACKET_PARTICIPANTS:
                parse_participants_packet(data)
            
            if not PARTICIPANTS_RECEIVED:
                continue
                
            if packet_id not in TOPIC_MAPPING:
                continue

            payload = {
                "session_uid": session_uid, 
                "player_car_index": player_car_idx, 
                "packet_id": packet_id
            }
            
            if packet_id == PACKET_TELEMETRY:
                payload["cars"] = parse_telemetry_packet(data)
            elif packet_id == PACKET_STATUS:
                payload["cars"] = parse_status_packet(data)
            elif packet_id == PACKET_LAP_DATA:
                payload["cars"] = parse_lap_packet(data)
            elif packet_id == PACKET_SESSION_HISTORY:
                payload["cars"] = parse_session_history_packet(data)
            elif packet_id == PACKET_MOTION:
                payload["cars"] = parse_motion_packet(data)

            producer.send(TOPIC_MAPPING[packet_id], value=payload)
            # logger.debug(f"Parsed and sent packet {packet_id} for session {session_uid}")
        except Exception as e:
            logger.error(f"Error processing packet: {e}", exc_info=True)
            continue

if __name__ == "__main__":
    main()