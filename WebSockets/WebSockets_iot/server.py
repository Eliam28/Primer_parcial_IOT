from flask import Flask, request, jsonify, render_template_string
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/api/sensor', methods=['POST'])
def receive_sensor_data():
    data = request.get_json()
    print(f"[API] Recibido: {data}")
    socketio.emit('sensor_update', data)
    return jsonify({"status": "ok"})

@app.route('/')
def dashboard():
    html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard IoT - Sensores en Tiempo Real</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0e1a;
            color: #e2e8f0;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: #111827;
            border-bottom: 2px solid #0891b2;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 {
            color: #06b6d4;
            font-size: 2.5em;
        }
        .header-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .connection-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 1.1em;
        }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ef4444;
        }
        .status-dot.connected {
            background: #10b981;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .message-count {
            background: #1e293b;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        .servers {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .server-card {
            background: #1e293b;
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #334155;
        }
        .server-card h3 {
            color: #06b6d4;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        .metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .metric {
            background: #0f172a;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .metric h4 {
            color: #94a3b8;
            font-size: 0.9em;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        .metric .value {
            font-size: 1.8em;
            font-weight: bold;
            color: #e2e8f0;
        }
        .metric .unit {
            color: #64748b;
            font-size: 0.8em;
        }
        .metric.temp .value.hot { color: #ef4444; }
        .log-section {
            background: #1e293b;
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #334155;
        }
        .log-section h3 {
            color: #06b6d4;
            margin-bottom: 15px;
        }
        .log-entries {
            max-height: 300px;
            overflow-y: auto;
        }
        .log-entry {
            background: #0f172a;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 8px;
            font-family: 'Consolas', monospace;
            font-size: 0.85em;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .log-entry .data {
            color: #e2e8f0;
        }
        .log-entry .time {
            color: #64748b;
            font-size: 0.8em;
        }
        .last-update {
            text-align: center;
            color: #64748b;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ IoT Server Monitor</h1>
            <div class="header-info">
                <div class="message-count" id="message-count">Mensajes: 0</div>
                <div class="connection-status">
                    <div class="status-dot" id="status-dot"></div>
                    <span id="connection-text">Desconectado</span>
                </div>
            </div>
        </div>
        
        <div class="servers">
            <div class="server-card" id="srv-01">
                <h3>SRV-01</h3>
                <div class="metrics">
                    <div class="metric temp">
                        <h4>🌡️ Temp</h4>
                        <div class="value" id="srv01-temp">--</div>
                        <div class="unit">°C</div>
                    </div>
                    <div class="metric">
                        <h4>⚡ Power</h4>
                        <div class="value" id="srv01-power">--</div>
                        <div class="unit">W</div>
                    </div>
                    <div class="metric">
                        <h4>🖥️ CPU</h4>
                        <div class="value" id="srv01-cpu">--</div>
                        <div class="unit">%</div>
                    </div>
                    <div class="metric">
                        <h4>💨 Fan</h4>
                        <div class="value" id="srv01-fan">--</div>
                        <div class="unit">RPM</div>
                    </div>
                </div>
            </div>
            
            <div class="server-card" id="srv-02">
                <h3>SRV-02</h3>
                <div class="metrics">
                    <div class="metric temp">
                        <h4>🌡️ Temp</h4>
                        <div class="value" id="srv02-temp">--</div>
                        <div class="unit">°C</div>
                    </div>
                    <div class="metric">
                        <h4>⚡ Power</h4>
                        <div class="value" id="srv02-power">--</div>
                        <div class="unit">W</div>
                    </div>
                    <div class="metric">
                        <h4>🖥️ CPU</h4>
                        <div class="value" id="srv02-cpu">--</div>
                        <div class="unit">%</div>
                    </div>
                    <div class="metric">
                        <h4>💨 Fan</h4>
                        <div class="value" id="srv02-fan">--</div>
                        <div class="unit">RPM</div>
                    </div>
                </div>
            </div>
            
            <div class="server-card" id="srv-03">
                <h3>SRV-03</h3>
                <div class="metrics">
                    <div class="metric temp">
                        <h4>🌡️ Temp</h4>
                        <div class="value" id="srv03-temp">--</div>
                        <div class="unit">°C</div>
                    </div>
                    <div class="metric">
                        <h4>⚡ Power</h4>
                        <div class="value" id="srv03-power">--</div>
                        <div class="unit">W</div>
                    </div>
                    <div class="metric">
                        <h4>🖥️ CPU</h4>
                        <div class="value" id="srv03-cpu">--</div>
                        <div class="unit">%</div>
                    </div>
                    <div class="metric">
                        <h4>💨 Fan</h4>
                        <div class="value" id="srv03-fan">--</div>
                        <div class="unit">RPM</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="log-section">
            <h3>📋 Últimas Lecturas</h3>
            <div class="log-entries" id="log-entries">
                <div class="log-entry">
                    <span class="data">Esperando datos del simulador...</span>
                    <span class="time">--:--:--</span>
                </div>
            </div>
        </div>
        
        <div class="last-update" id="last-update">
            Última actualización: Nunca
        </div>
    </div>

    <script>
        const socket = io();
        let messageCount = 0;
        const maxLogEntries = 10;
        
        socket.on('connect', () => {
            document.getElementById('connection-text').textContent = 'Conectado';
            document.getElementById('status-dot').classList.add('connected');
        });
        
        socket.on('disconnect', () => {
            document.getElementById('connection-text').textContent = 'Desconectado';
            document.getElementById('status-dot').classList.remove('connected');
        });
        
        socket.on('sensor_update', (data) => {
            messageCount++;
            document.getElementById('message-count').textContent = 'Mensajes: ' + messageCount;
            
            // Actualizar servidor específico
            const srvId = data.device_id.toLowerCase().replace('-', '');
            const tempEl = document.getElementById(srvId + '-temp');
            const powerEl = document.getElementById(srvId + '-power');
            const cpuEl = document.getElementById(srvId + '-cpu');
            const fanEl = document.getElementById(srvId + '-fan');
            
            if (tempEl) {
                tempEl.textContent = data.temperature_c;
                if (data.temperature_c > 30) {
                    tempEl.classList.add('hot');
                } else {
                    tempEl.classList.remove('hot');
                }
            }
            if (powerEl) powerEl.textContent = data.power_w;
            if (cpuEl) cpuEl.textContent = data.cpu_percent;
            if (fanEl) fanEl.textContent = data.fan_rpm;
            
            // Agregar al log
            addLogEntry(data);
            
            // Última actualización
            const now = new Date();
            document.getElementById('last-update').textContent = 
                'Última actualización: ' + now.toLocaleTimeString();
        });
        
        function addLogEntry(data) {
            const logContainer = document.getElementById('log-entries');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `
                <span class="data">${data.device_id}: ${data.temperature_c}°C, ${data.power_w}W, ${data.cpu_percent}%, ${data.fan_rpm} RPM</span>
                <span class="time">${data.timestamp}</span>
            `;
            logContainer.insertBefore(entry, logContainer.firstChild);
            
            // Mantener solo las últimas 10
            while (logContainer.children.length > maxLogEntries) {
                logContainer.removeChild(logContainer.lastChild);
            }
        }
    </script>
</body>
</html>
"""
    return render_template_string(html)

if __name__ == '__main__':
    socketio.run(app, port=5000)