# Proyecto IoT - Monitoreo Ambiental

Sistema de monitoreo ambiental para ESP32 usando MQTT, almacenamiento JSON local, API REST con Flask y dashboard web.

Arquitectura:

ESP32 -> MQTT Broker (Mosquitto) -> Python Subscriber -> `data.json` -> API Flask -> Dashboard Web

## 1. Estructura del proyecto

```text
proyecto-iot/
|-- venv/
|-- gateway/
|   |-- subscriber.py
|   |-- api.py
|   |-- data.json
|-- dashboard/
|   |-- index.html
|   |-- script.js
|   |-- style.css
|-- requirements.txt
|-- .gitignore
|-- README.md
```

## 2. Crear y activar entorno virtual

### Windows (PowerShell)

```powershell
cd proyecto-iot
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Linux/macOS (bash)

```bash
cd proyecto-iot
python -m venv venv
source venv/bin/activate
```

Si deseas salir del entorno virtual:

```bash
deactivate
```

## 3. Instalar dependencias

Con el entorno virtual activo:

```bash
pip install -r requirements.txt
```

## 4. Ejecutar el subscriber MQTT

Desde la carpeta `proyecto-iot`:

```bash
python gateway/subscriber.py
```

Este proceso:

- Se conecta a `localhost:1883`
- Se suscribe a `iot/ambiente/#`
- Recibe y valida JSON
- Agrega `timestamp`
- Guarda cada lectura en `gateway/data.json`

## 5. Ejecutar la API Flask

En otra terminal (con el mismo entorno virtual activo):

```bash
python gateway/api.py
```

La API quedara disponible en:

- `http://localhost:5000/api/latest`
- `http://localhost:5000/api/history?limit=10`
- `http://localhost:5000/api/stats`
- `http://localhost:5000/api/control`

## 6. Probar endpoints con curl

### Obtener ultima lectura por nodo

```bash
curl http://localhost:5000/api/latest
```

### Obtener ultimas 5 lecturas

```bash
curl "http://localhost:5000/api/history?limit=5"
```

### Obtener estadisticas por nodo

```bash
curl http://localhost:5000/api/stats
```

### Encender relevador de nodo1

```bash
curl -X POST http://localhost:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"nodo":"nodo1","estado":"1"}'
```

### Apagar relevador de nodo1

```bash
curl -X POST http://localhost:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"nodo":"nodo1","estado":"0"}'
```

## 7. Dashboard web

Abre `dashboard/index.html` en el navegador.

El dashboard:

- Consulta la API cada 5 segundos
- Muestra tarjetas por nodo con temperatura, humedad y luz
- Grafica temperatura historica y luminosidad actual usando Chart.js
- Permite enviar comandos de encendido/apagado a cada nodo

## 8. Topics MQTT usados

Lectura de sensores (entrada):

- `iot/ambiente/nodo1`
- `iot/ambiente/nodo2`
- `iot/ambiente/nodo3`

Control de relevador (salida):

- `iot/control/<nodo>`

Valores de control:

- `1`: encender relevador
- `0`: apagar relevador
