import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type SensorData = {
  nodo: string;
  temperatura: number;
  humedad: number;
  luz: number;
  relay?: number;
  timestamp: string;
};

type RawApiItem = {
  timestamp: string;
  topic?: string;
  data?: {
    nodo?: string;
    temperatura?: number;
    humedad?: number;
    luz?: number;
    relay?: number;
  };
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

const normalizeItem = (item: RawApiItem): SensorData | null => {
  if (!item?.data?.nodo) {
    return null;
  }

  return {
    nodo: item.data.nodo,
    temperatura: Number(item.data.temperatura ?? 0),
    humedad: Number(item.data.humedad ?? 0),
    luz: Number(item.data.luz ?? 0),
    relay: item.data.relay,
    timestamp: item.timestamp,
  };
};

function App() {
  const [latest, setLatest] = useState<SensorData[]>([]);
  const [history, setHistory] = useState<SensorData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  const getData = async (): Promise<void> => {
    try {
      setError("");
      const latestRes = await fetch(`${API_BASE}/latest`);
      const historyRes = await fetch(`${API_BASE}/history?limit=20`);

      if (!latestRes.ok || !historyRes.ok) {
        throw new Error("Error al obtener datos");
      }

      const latestRaw: RawApiItem[] = await latestRes.json();
      const historyRaw: RawApiItem[] = await historyRes.json();

      const latestData = latestRaw
        .map(normalizeItem)
        .filter((item): item is SensorData => item !== null);

      const historyData = historyRaw
        .map(normalizeItem)
        .filter((item): item is SensorData => item !== null);

      setLatest(latestData);
      setHistory(historyData);
    } catch (err) {
      console.error(err);
      setError("No se pudo conectar con la API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getData();

    const interval = setInterval(() => {
      getData();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleRelay = async (nodo: string, estado: number): Promise<void> => {
    try {
      const controlRes = await fetch(`${API_BASE}/control`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ nodo, estado: String(estado) }),
      });

      if (!controlRes.ok) {
        throw new Error("Error en control");
      }

      getData();
    } catch (err) {
      console.error(err);
      alert("Error al enviar control");
    }
  };

  const getNodeHistory = (nodo: string): SensorData[] => {
    return history.filter((item) => item.nodo === nodo);
  };

  if (loading) {
    return <div className="p-6">Cargando dashboard...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-900 p-6">
      <h1 className="mb-2 text-3xl font-bold">Dashboard IoT</h1>
      <p className="mb-6 text-slate-300">Monitoreo ambiental de nodos</p>

      {error && (
        <div className="mb-4 rounded bg-red-500 px-4 py-3 text-white">
          {error}
        </div>
      )}

      <div className="grid gap-6">
        {latest.map((node) => (
          <div
            key={node.nodo}
            className="rounded-xl border border-slate-700 bg-slate-800 p-5"
          >
            <h2 className="mb-4 text-2xl font-semibold">{node.nodo}</h2>

            <div className="mb-4 grid gap-4 md:grid-cols-3">
              <div className="rounded-lg bg-slate-700 p-4">
                <p className="text-sm text-slate-300">Temperatura</p>
                <p className="text-2xl font-bold">{node.temperatura} °C</p>
              </div>

              <div className="rounded-lg bg-slate-700 p-4">
                <p className="text-sm text-slate-300">Humedad</p>
                <p className="text-2xl font-bold">{node.humedad} %</p>
              </div>

              <div className="rounded-lg bg-slate-700 p-4">
                <p className="text-sm text-slate-300">Luz</p>
                <p className="text-2xl font-bold">{node.luz} %</p>
              </div>
            </div>

            <div className="mb-4">
              <p className="text-sm text-slate-300">
                Última actualización: {node.timestamp}
              </p>
              <p className="text-sm text-slate-300">
                Relay: {node.relay === 1 ? "Encendido" : "Apagado"}
              </p>
            </div>

            <div className="mb-6 flex gap-3">
              <button
                onClick={() => handleRelay(node.nodo, 1)}
                className="rounded bg-green-500 px-4 py-2 font-semibold text-black"
              >
                Encender
              </button>

              <button
                onClick={() => handleRelay(node.nodo, 0)}
                className="rounded bg-red-500 px-4 py-2 font-semibold text-white"
              >
                Apagar
              </button>
            </div>

            <div className="h-64 rounded-lg bg-slate-700 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={getNodeHistory(node.nodo)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="temperatura"
                    stroke="#f97316"
                  />
                  <Line type="monotone" dataKey="humedad" stroke="#38bdf8" />
                  <Line type="monotone" dataKey="luz" stroke="#eab308" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
