
import json
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883
TOPIC = "iot/ambiente/#"
FILE = "data.json"

def on_connect(client, userdata, flags, rc):
    print("Conectado al broker MQTT")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        data = {
            "timestamp": datetime.now().isoformat(),
            "topic": msg.topic,
            "data": payload
        }

        try:
            with open(FILE, "r") as f:
                historial = json.load(f)
        except:
            historial = []

        historial.append(data)

        with open(FILE, "w") as f:
            json.dump(historial, f, indent=4)

        print("Dato guardado:", data)

    except Exception as e:
        print("Error procesando mensaje:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)

client.loop_forever()
