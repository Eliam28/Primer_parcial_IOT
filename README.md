# Sistema de Monitoreo Ambiental IoT

# Instalación del Proyecto

## 1. Clonar el repositorio

```bash
git clone https://github.com/Eliam28/Primer_parcial_IOT
cd Primer_parcial_IOT
```

# Configuración del Gateway (Raspberry Pi)

Actualizar sistema:

```bash
sudo apt update
sudo apt upgrade
```

Instalar Mosquitto:

```bash
sudo apt install mosquitto mosquitto-clients -y
```

Activar servicio:

```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Verificar estado:

```bash
sudo systemctl status mosquitto
```

El broker MQTT se ejecutará en el **puerto 1883**.

---

# Configuración del Hardware

Cada nodo ESP32 tiene conectados los siguientes sensores.

## Sensor DHT22

| DHT22 | ESP32 |
| ----- | ----- |
| VCC   | 3V3   |
| OUT   | P4    |
| GND   | GND   |

---

## Sensor LDR

| LDR | ESP32 |
| --- | ----- |
| VCC | 3V3   |
| GND | GND   |
| OUT | P34   |

---

## Módulo Relevador

| Relay | ESP32 |
| ----- | ----- |
| VCC   | 3V3   |
| GND   | GND   |
| IN    | P5    |

---

# Programación de los ESP32

Abrir **Arduino IDE** e instalar las siguientes librerías:

- PubSubClient
- DHT Sensor Library
- WiFi

Configurar en el código:

```cpp
const char* ssid = "TuWiFi";
const char* password = "TuPassword";
const char* mqtt_server = "192.168.1.10";
```

Subir el código al ESP32.

Cada nodo debe tener un identificador diferente:

```
nodo1
nodo2
nodo3
```

---

# Configuración del Backend (Python API)

Entrar a la carpeta del backend:

```bash
cd PythonApiFlahk
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

---

# Ejecutar Subscriber MQTT

El subscriber recibe los datos de los nodos ESP32 y los almacena en un archivo JSON.

```bash
python subscriber.py
```

Los datos se guardan en:

```
data.json
```

---

# Ejecutar API REST

```bash
python api.py
```

La API se ejecutará en:

```
http://localhost:5000
```

---

# Endpoints de la API

### Obtener últimas lecturas

```
GET /api/latest
```

---

### Obtener historial

```
GET /api/history?limit=50
```

---

### Estadísticas de sensores

```
GET /api/stats
```

---

### Controlar relevador

```
POST /api/control
```

Body:

```json
{
  "nodo": "nodo1",
  "estado": 1
}
```

Estados:

```
1 = Encender
0 = Apagar
```

---

# Ejecutar Dashboard Web

Entrar a la carpeta:

```bash
cd dashboard
```

Instalar dependencias:

```bash
npm install
```

Ejecutar servidor de desarrollo:

```bash
npm run dev
```

El dashboard se abrirá normalmente en:

```
http://localhost:5173
```

---

# Funcionamiento del Sistema

1. Encender Raspberry Pi (broker MQTT)
2. Ejecutar `subscriber.py`
3. Ejecutar `api.py`
4. Encender los nodos ESP32
5. Ejecutar el dashboard web
6. Visualizar datos en tiempo real
7. Controlar relevadores desde el dashboard

---
