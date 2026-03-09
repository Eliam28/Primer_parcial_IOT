# Sistema de Monitoreo Ambiental IoT

Este proyecto implementa un **sistema IoT de monitoreo ambiental** utilizando **ESP32**, comunicación **MQTT**, una **API REST con Flask** y un **dashboard web** para visualizar datos en tiempo real.

El sistema permite medir:

- Temperatura
- Humedad
- Luminosidad

Además, permite **controlar un relevador remotamente** desde el dashboard web.

---

# 1. Clonar el repositorio

```bash
git clone https://github.com/Eliam28/Primer_parcial_IOT
cd Primer_parcial_IOT
```

---

# 2. Configuración del Gateway (Raspberry Pi)

Actualizar el sistema:

```bash
sudo apt update
sudo apt upgrade
```

Instalar Mosquitto MQTT:

```bash
sudo apt install mosquitto mosquitto-clients -y
```

Habilitar el servicio:

```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Verificar que el servicio esté activo:

```bash
sudo systemctl status mosquitto
```

El broker MQTT se ejecutará en el **puerto 1883**.

---

# 3. Configuración del Hardware

Cada nodo ESP32 tiene conectados los siguientes módulos.

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

# 4. Programación de los ESP32

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

# 5. Instalación de dependencias Python

Entrar a la carpeta del backend:

```bash
cd PythonApiFlahk
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

---

# 6. Ejecución del Subscriber MQTT

El subscriber recibe los datos enviados por los nodos ESP32 y los guarda en un archivo JSON.

Ejecutar:

```bash
python subscriber.py
```

Los datos recibidos se almacenan en:

```
data.json
```

---

# 7. Ejecución de la API REST

Ejecutar:

```bash
python api.py
```

La API se ejecutará en:

```
http://localhost:5000
```

---

# 8. Ejecución del Dashboard

Entrar a la carpeta del dashboard:

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

El dashboard normalmente se abrirá en:

```
http://localhost:5173
```

---

# 9. Uso del Sistema

Para utilizar el sistema completo seguir los siguientes pasos:

1. Encender la Raspberry Pi con el broker MQTT activo.
2. Ejecutar el subscriber:

```bash
python subscriber.py
```

3. Ejecutar la API REST:

```bash
python api.py
```

4. Encender los nodos ESP32 conectados a los sensores.
5. Ejecutar el dashboard web.
6. Abrir el navegador en:

```
http://localhost:5173
```

Desde el dashboard se pueden:

- Visualizar datos de **temperatura**
- Visualizar datos de **humedad**
- Visualizar datos de **luminosidad**
- Controlar el **relevador de cada nodo**
- Monitorear datos en **tiempo real**
