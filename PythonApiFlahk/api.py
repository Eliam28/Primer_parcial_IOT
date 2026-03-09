
from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import paho.mqtt.publish as publish
from pathlib import Path

FILE = Path(__file__).resolve().parent / "data.json"
BROKER = "192.168.0.28"

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
    return jsonify(data[-3:])

@app.route("/api/history")
def history():
    limit = int(request.args.get("limit", 10))
    data = load_data()
    return jsonify(data[-limit:])

@app.route("/api/stats")
def stats():
    data = load_data()

    temps = [d["data"]["temperatura"] for d in data if "temperatura" in d["data"]]

    if not temps:
        return jsonify({"error":"no data"})

    stats = {
        "min": min(temps),
        "max": max(temps),
        "avg": sum(temps)/len(temps)
    }

    return jsonify(stats)

@app.route("/api/control", methods=["POST"])
def control():
    nodo = request.json["nodo"]
    estado = request.json["estado"]

    topic = f"iot/control/{nodo}"

    publish.single(topic, estado, hostname=BROKER)

    return jsonify({"status":"ok","topic":topic,"estado":estado})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
