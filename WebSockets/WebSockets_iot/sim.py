"""
=============================================================
SIMULADOR — Genera datos de sensores y los manda al servidor
=============================================================
Este script simula 3 servidores mandando telemetría.
Envía datos via HTTP POST al endpoint /api/sensor del servidor.

En un proyecto real, esto sería reemplazado por:
  - Un ESP32 mandando datos por MQTT
  - Un subscriber MQTT que reenvia al API

Ejecutar (en otra terminal, después de server.py):
    python simulator.py
=============================================================
"""

import requests
import random
import math
import time
from datetime import datetime

# URL del servidor
SERVER_URL = "http://localhost:5000/api/sensor"

# Configuración de servidores simulados
servers = {
    "SRV-01": {"base_temp": 22.0, "base_power": 180},
    "SRV-02": {"base_temp": 23.5, "base_power": 220},
    "SRV-03": {"base_temp": 21.0, "base_power": 160},
}

reading_count = 0


def generate_reading(srv_id, params):
    """Genera una lectura simulada con patrones realistas"""
    global reading_count
    reading_count += 1
    
    now = datetime.now()
    hour = now.hour + now.minute / 60.0
    
    # Patrón diurno: más carga durante el día
    work_factor = 0.3 * math.exp(-0.5 * ((hour - 14) / 4) ** 2)
    
    # Temperatura
    temp = params["base_temp"] + work_factor * 5 + random.gauss(0, 0.3)
    
    # Anomalía en SRV-01 cada ~30 lecturas (~1 min)
    if srv_id == "SRV-01" and reading_count % 30 == 0:
        temp += random.uniform(10, 15)
        print(f"  💥 ¡Anomalía inyectada en {srv_id}! temp={temp:.1f}°C")
    
    power = params["base_power"] + work_factor * 80 + random.gauss(0, 3)
    cpu = max(5, min(100, 25 + work_factor * 60 + random.gauss(0, 5)))
    fan = max(800, 1000 + (temp - 22) * 200 + random.gauss(0, 20))
    
    return {
        "device_id": srv_id,
        "timestamp": now.strftime("%H:%M:%S"),
        "temperature_c": round(temp, 1),
        "power_w": round(power, 1),
        "cpu_percent": round(cpu, 1),
        "fan_rpm": round(fan, 0),
    }


def send_reading(data):
    """Envía una lectura al servidor via HTTP POST"""
    try:
        response = requests.post(SERVER_URL, json=data, timeout=2)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


# ============================================================
# LOOP PRINCIPAL
# ============================================================
if __name__ == '__main__':
    print("=" * 55)
    print("  📡 SIMULADOR DE SENSORES")
    print("=" * 55)
    print()
    print(f"  Enviando datos a: {SERVER_URL}")
    print(f"  Servidores: {', '.join(servers.keys())}")
    print(f"  Intervalo: 2 segundos")
    print(f"  Anomalías: cada ~30 lecturas en SRV-01")
    print()
    print("  Asegúrate de que server.py esté corriendo")
    print()
    print("=" * 55)
    print()
    
    # Esperar a que el servidor esté listo
    print("  Conectando al servidor...", end="", flush=True)
    while True:
        try:
            requests.get("http://localhost:5000", timeout=1)
            print(" ✅ Conectado!")
            break
        except:
            print(".", end="", flush=True)
            time.sleep(1)
    
    print()
    print("  Enviando datos (Ctrl+C para detener):")
    print("  " + "-" * 50)
    
    while True:
        for srv_id, params in servers.items():
            reading = generate_reading(srv_id, params)
            
            success = send_reading(reading)
            
            # Mostrar en terminal
            icon = "📤" if success else "❌"
            temp_color = "🔴" if reading["temperature_c"] > 30 else "🟢"
            print(f"  {icon} {reading['device_id']}  "
                  f"{temp_color} {reading['temperature_c']:>5}°C  "
                  f"⚡{reading['power_w']:>6}W  "
                  f"🖥️{reading['cpu_percent']:>5}%  "
                  f"🌀{reading['fan_rpm']:>6} RPM")
        
        print()  # Línea en blanco entre rondas
        time.sleep(2)