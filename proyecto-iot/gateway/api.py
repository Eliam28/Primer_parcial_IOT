"""API REST para consultar lecturas y enviar comandos MQTT de control."""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS
import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883
DATA_FILE = Path(__file__).resolve().parent / "data.json"

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("iot-api")

mqtt_client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="iot_api_publisher",
)
mqtt_connected = False


def on_connect(
    client: mqtt.Client,
    userdata: Any,
    flags: Dict[str, Any],
    reason_code: mqtt.ReasonCode,
    properties: Any,
) -> None:
    """Marca el estado de conexion del cliente MQTT publicador."""
    global mqtt_connected
    mqtt_connected = reason_code == 0
    if mqtt_connected:
        logger.info("API conectada a broker MQTT en %s:%s", BROKER_HOST, BROKER_PORT)
    else:
        logger.error("No se pudo conectar a MQTT. Codigo de retorno: %s", reason_code)


def start_mqtt() -> None:
    """Inicia el cliente MQTT de publicacion para endpoint de control."""
    mqtt_client.on_connect = on_connect
    try:
        mqtt_client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        mqtt_client.loop_start()
    except Exception as exc:
        logger.error("Error al iniciar cliente MQTT: %s", exc)


def ensure_data_file() -> None:
    """Crea data.json si no existe para evitar errores de lectura."""
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def read_data() -> List[Dict[str, Any]]:
    """Lee y valida el historico almacenado."""
    ensure_data_file()
    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8") or "[]")
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        logger.error("data.json invalido. Se retorna lista vacia.")
    return []


@app.get("/api/latest")
def get_latest() -> Any:
    """Retorna la ultima lectura disponible por nodo."""
    data = read_data()
    latest_by_node: Dict[str, Dict[str, Any]] = {}

    for item in reversed(data):
        node = item.get("nodo")
        if node and node not in latest_by_node:
            latest_by_node[node] = item

    return jsonify({"latest": latest_by_node, "nodos": len(latest_by_node)})


@app.get("/api/history")
def get_history() -> Any:
    """Retorna las ultimas N lecturas del historico."""
    data = read_data()

    limit_param = request.args.get("limit", default="50")
    try:
        limit = int(limit_param)
        if limit <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "El parametro limit debe ser un entero positivo"}), 400

    return jsonify({"history": data[-limit:], "count": min(limit, len(data))})


@app.get("/api/stats")
def get_stats() -> Any:
    """Calcula estadisticas agregadas de temperatura y humedad por nodo."""
    data = read_data()

    grouped: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: {"temperatura": [], "humedad": []})

    for item in data:
        node = item.get("nodo")
        if not node:
            continue
        try:
            grouped[node]["temperatura"].append(float(item["temperatura"]))
            grouped[node]["humedad"].append(float(item["humedad"]))
        except (KeyError, TypeError, ValueError):
            continue

    stats: Dict[str, Dict[str, float]] = {}
    for node, values in grouped.items():
        temps = values["temperatura"]
        hums = values["humedad"]
        if not temps or not hums:
            continue
        stats[node] = {
            "temperatura_min": min(temps),
            "temperatura_max": max(temps),
            "temperatura_promedio": sum(temps) / len(temps),
            "humedad_promedio": sum(hums) / len(hums),
        }

    return jsonify({"stats": stats})


@app.post("/api/control")
def post_control() -> Any:
    """Publica comandos de encendido/apagado a un topic de control por nodo."""
    payload = request.get_json(silent=True) or {}
    node = payload.get("nodo")
    state = payload.get("estado")

    if not node or state not in {"0", "1"}:
        return jsonify({"error": "Se requiere nodo y estado ('0' o '1')"}), 400

    if not mqtt_connected:
        return jsonify({"error": "No hay conexion disponible con MQTT"}), 503

    topic = f"iot/control/{node}"
    result = mqtt_client.publish(topic, str(state), qos=0, retain=False)

    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        return jsonify({"error": "No se pudo publicar el comando MQTT"}), 500

    return jsonify({
        "message": "Comando enviado",
        "topic": topic,
        "payload": str(state),
    })


if __name__ == "__main__":
    start_mqtt()
    app.run(host="0.0.0.0", port=5000, debug=True)
