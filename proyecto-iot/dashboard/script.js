const API_BASE = "http://localhost:5000";
const cardsContainer = document.getElementById("cards");
const lastUpdateLabel = document.getElementById("last-update");

let tempChart;
let lightChart;

async function fetchJSON(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Error HTTP ${response.status}`);
  }
  return response.json();
}

function buildNodeCard(node, data) {
  return `
    <article class="card">
      <h3>${node}</h3>
      <div class="metrics">
        <p><strong>Temp:</strong> ${Number(data.temperatura).toFixed(1)} C</p>
        <p><strong>Humedad:</strong> ${Number(data.humedad).toFixed(1)} %</p>
        <p><strong>Luz:</strong> ${Number(data.luz).toFixed(1)} %</p>
        <p><strong>Hora:</strong> ${new Date(data.timestamp).toLocaleTimeString()}</p>
      </div>
      <div class="controls">
        <button onclick="sendControl('${node}','1')">Encender</button>
        <button class="off" onclick="sendControl('${node}','0')">Apagar</button>
      </div>
    </article>
  `;
}

function updateCards(latest) {
  const nodes = Object.keys(latest);
  if (nodes.length === 0) {
    cardsContainer.innerHTML = "<p>No hay datos todavia.</p>";
    return;
  }

  cardsContainer.innerHTML = nodes
    .sort()
    .map((node) => buildNodeCard(node, latest[node]))
    .join("");
}

function updateTempChart(history) {
  const labels = history.map((entry) =>
    new Date(entry.timestamp).toLocaleTimeString(),
  );
  const nodes = [...new Set(history.map((entry) => entry.nodo))].sort();

  const datasets = nodes.map((node, idx) => {
    const color = ["#0f766e", "#0369a1", "#b45309", "#9d174d"][idx % 4];
    return {
      label: `${node} temperatura`,
      data: history.map((entry) =>
        entry.nodo === node ? entry.temperatura : null,
      ),
      borderColor: color,
      backgroundColor: `${color}33`,
      spanGaps: true,
      tension: 0.35,
    };
  });

  if (!tempChart) {
    tempChart = new Chart(document.getElementById("tempChart"), {
      type: "line",
      data: { labels, datasets },
      options: { responsive: true, maintainAspectRatio: false },
    });
    return;
  }

  tempChart.data.labels = labels;
  tempChart.data.datasets = datasets;
  tempChart.update();
}

function updateLightChart(latest) {
  const nodes = Object.keys(latest).sort();
  const values = nodes.map((node) => latest[node].luz);

  if (!lightChart) {
    lightChart = new Chart(document.getElementById("lightChart"), {
      type: "bar",
      data: {
        labels: nodes,
        datasets: [
          {
            label: "Luminosidad",
            data: values,
            backgroundColor: ["#0f766e", "#0369a1", "#b45309"],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true, max: 100 } },
      },
    });
    return;
  }

  lightChart.data.labels = nodes;
  lightChart.data.datasets[0].data = values;
  lightChart.update();
}

async function refreshDashboard() {
  try {
    const [latestResp, historyResp] = await Promise.all([
      fetchJSON("/api/latest"),
      fetchJSON("/api/history?limit=30"),
    ]);

    const latest = latestResp.latest || {};
    const history = historyResp.history || [];

    updateCards(latest);
    updateTempChart(history);
    updateLightChart(latest);
    lastUpdateLabel.textContent = `Ultima actualizacion: ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    console.error("No se pudo actualizar dashboard:", error);
    lastUpdateLabel.textContent =
      "Ultima actualizacion: error de conexion con API";
  }
}

async function sendControl(node, state) {
  try {
    const response = await fetch(`${API_BASE}/api/control`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nodo: node, estado: state }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "No se pudo enviar comando");
    }

    alert(
      `Comando enviado a ${node}: ${state === "1" ? "ENCENDER" : "APAGAR"}`,
    );
  } catch (error) {
    alert(`Error enviando comando: ${error.message}`);
  }
}

window.sendControl = sendControl;

refreshDashboard();
setInterval(refreshDashboard, 5000);
