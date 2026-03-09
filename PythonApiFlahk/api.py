
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import paho.mqtt.publish as publish
from pathlib import Path

FILE = Path(__file__).resolve().parent / "data.json"
BROKER = "192.168.0.28"
BROKER_PORT = 1883

app = Flask(__name__)
CORS(app)

def load_data():
    try:
        with open(FILE, encoding="utf-8") as f:
            return json.load(f)
    except: 
        return []

@app.route("/api/latest")
def latest():
    data = load_data()
    latest_by_node = {}

    # Recorre de mas reciente a mas antiguo y toma solo el primero por nodo.
    for item in reversed(data):
        nodo = item.get("data", {}).get("nodo")
        if nodo and nodo not in latest_by_node:
            latest_by_node[nodo] = item

    # Orden estable por nombre de nodo para una UI predecible (nodo1, nodo2, ...)
    latest_list = [latest_by_node[n] for n in sorted(latest_by_node.keys())]
    return jsonify(latest_list)

@app.route("/api/history")
def history():
    limit = int(request.args.get("limit", 10))
    data = load_data()
    return jsonify(data[-limit:])

@app.route("/api/stats")
def stats():
    data = load_data()

    by_node = {}
    global_temps = []

    for d in data:
        payload = d.get("data", {})
        nodo = payload.get("nodo")
        if not nodo:
            continue

        if nodo not in by_node:
            by_node[nodo] = {
                "temperatura": [],
                "humedad": [],
                "luz": []
            }

        temp = payload.get("temperatura")
        hum = payload.get("humedad")
        luz = payload.get("luz")

        if isinstance(temp, (int, float)):
            t = float(temp)
            by_node[nodo]["temperatura"].append(t)
            global_temps.append(t)
        if isinstance(hum, (int, float)):
            by_node[nodo]["humedad"].append(float(hum))
        if isinstance(luz, (int, float)):
            by_node[nodo]["luz"].append(float(luz))

    if not by_node:
        return jsonify({"error": "no data"})

    node_stats = {}
    for nodo, values in by_node.items():
        node_stats[nodo] = {
            "count": len(values["temperatura"]),
            "temperatura": {
                "min": min(values["temperatura"]) if values["temperatura"] else None,
                "max": max(values["temperatura"]) if values["temperatura"] else None,
                "avg": (sum(values["temperatura"]) / len(values["temperatura"])) if values["temperatura"] else None,
            },
            "humedad": {
                "min": min(values["humedad"]) if values["humedad"] else None,
                "max": max(values["humedad"]) if values["humedad"] else None,
                "avg": (sum(values["humedad"]) / len(values["humedad"])) if values["humedad"] else None,
            },
            "luz": {
                "min": min(values["luz"]) if values["luz"] else None,
                "max": max(values["luz"]) if values["luz"] else None,
                "avg": (sum(values["luz"]) / len(values["luz"])) if values["luz"] else None,
            },
        }

    global_stats = {
        "temperatura": {
            "min": min(global_temps) if global_temps else None,
            "max": max(global_temps) if global_temps else None,
            "avg": (sum(global_temps) / len(global_temps)) if global_temps else None,
        }
    }

    return jsonify({"global": global_stats, "nodes": node_stats})

@app.route("/api/control", methods=["POST"])
def control():
    payload = request.get_json(silent=True) or {}
    nodo = payload.get("nodo")
    estado = str(payload.get("estado", "")).strip()

    if not nodo:
        return jsonify({"error": "nodo es requerido"}), 400

    if estado not in {"0", "1"}:
        return jsonify({"error": "estado debe ser '0' o '1'"}), 400

    topic = f"iot/control/{nodo}"

    try:
        publish.single(topic, estado, hostname=BROKER, port=BROKER_PORT, qos=1)
    except Exception as e:
        return jsonify({"error": "no se pudo publicar al broker", "detail": str(e)}), 503

    return jsonify({"status":"ok","topic":topic,"estado":estado})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
