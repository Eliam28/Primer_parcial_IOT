"""Subscriber MQTT para capturar lecturas ambientales de nodos ESP32."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List

import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
MQTT_TOPIC = "iot/ambiente/#"
DATA_FILE = Path(__file__).resolve().parent / "data.json"
FILE_LOCK = Lock()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("mqtt-subscriber")


def ensure_data_file() -> None:
    """Crea el archivo de datos si no existe y valida su formato."""
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")
        logger.info("Archivo de datos creado en %s", DATA_FILE)
        return

    try:
        content = json.loads(DATA_FILE.read_text(encoding="utf-8") or "[]")
        if not isinstance(content, list):
            raise ValueError("El archivo data.json no contiene una lista JSON")
    except (json.JSONDecodeError, ValueError):
        logger.warning("data.json estaba invalido. Se reinicia con una lista vacia.")
        DATA_FILE.write_text("[]", encoding="utf-8")


def read_data() -> List[Dict[str, Any]]:
    """Lee el historico completo del archivo JSON."""
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8") or "[]")
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        logger.error("No se pudo parsear data.json. Se devolvera una lista vacia.")
    return []


def write_data(data: List[Dict[str, Any]]) -> None:
    """Guarda el historico completo en el archivo JSON."""
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def append_reading(reading: Dict[str, Any]) -> None:
    """Agrega una lectura al historico con exclusión mutua."""
    with FILE_LOCK:
        data = read_data()
        data.append(reading)
        write_data(data)


def parse_payload(payload: bytes) -> Dict[str, Any]:
    """Parsea y valida el payload JSON recibido por MQTT."""
    message = json.loads(payload.decode("utf-8"))

    required_keys = {"nodo", "temperatura", "humedad", "luz"}
    missing = required_keys.difference(message.keys())
    if missing:
        raise ValueError(f"Faltan campos requeridos: {sorted(missing)}")

    reading = {
        "nodo": str(message["nodo"]),
        "temperatura": float(message["temperatura"]),
        "humedad": float(message["humedad"]),
        "luz": float(message["luz"]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return reading


def on_connect(client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int, properties: Any = None) -> None:
    """Callback al conectar con el broker."""
    if rc == 0:
        logger.info("Conectado a MQTT en %s:%s", BROKER_HOST, BROKER_PORT)
        client.subscribe(MQTT_TOPIC)
        logger.info("Suscrito al topic %s", MQTT_TOPIC)
    else:
        logger.error("Error al conectar con MQTT. Codigo de retorno: %s", rc)


def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    """Callback para procesar mensajes entrantes."""
    try:
        reading = parse_payload(msg.payload)
        append_reading(reading)
        logger.info("Lectura guardada: %s", reading)
    except json.JSONDecodeError:
        logger.error("Mensaje JSON invalido en topic %s: %s", msg.topic, msg.payload)
    except (ValueError, TypeError) as exc:
        logger.error("Mensaje descartado en topic %s: %s", msg.topic, exc)


def main() -> None:
    """Inicializa cliente MQTT y mantiene la escucha activa."""
    ensure_data_file()

    client = mqtt.Client(client_id="iot_gateway_subscriber")
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    logger.info("Iniciando loop MQTT...")
    client.loop_forever()


if __name__ == "__main__":
    main()
