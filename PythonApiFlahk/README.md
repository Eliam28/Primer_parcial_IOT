Proyecto IoT - Gateway Python

Archivos incluidos:
- subscriber.py -> Escucha datos MQTT y los guarda en JSON
- api.py -> API REST con Flask para consultar datos y controlar relevadores

Instalación:

pip install -r requirements.txt

Ejecutar subscriber:

python subscriber.py

Ejecutar API:

python api.py

Endpoints:

GET /api/latest
GET /api/history?limit=10
GET /api/stats
POST /api/control

Ejemplo POST:

{
 "nodo":"nodo1",
 "estado":"1"
}