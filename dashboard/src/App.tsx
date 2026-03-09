import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

type SensorData = {
  nodo: string;
  temperatura: number;
  humedad: number;
  luz: number;
  relay?: number;
  relay_on?: boolean;
  relay_ok?: boolean;
  dht_ok?: boolean;
  ldr_ok?: boolean;
  node_ok?: boolean;
  timestamp: string;
};

type RawApiItem = {
  timestamp: string;
  topic?: string;
  data?: {
    nodo?: string;
    temperatura?: number | null;
    humedad?: number | null;
    luz?: number | null;
    relay?: number;
    relay_on?: boolean;
    relay_ok?: boolean;
    dht_ok?: boolean;
    ldr_ok?: boolean;
    node_ok?: boolean;
  };
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

const normalizeItem = (item: RawApiItem): SensorData | null => {
  if (!item?.data?.nodo) return null;

  return {
    nodo: item.data.nodo,
    temperatura: Number(item.data.temperatura ?? 0),
    humedad: Number(item.data.humedad ?? 0),
    luz: Number(item.data.luz ?? 0),
    relay: item.data.relay,
    relay_on: item.data.relay_on ?? false,
    relay_ok: item.data.relay_ok ?? false,
    dht_ok: item.data.dht_ok ?? false,
    ldr_ok: item.data.ldr_ok ?? false,
    node_ok: item.data.node_ok ?? false,
    timestamp: item.timestamp,
  };
};

const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;

  return date.toLocaleString("es-MX", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    day: "2-digit",
    month: "short",
  });
};

const formatChartTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;

  return date.toLocaleTimeString("es-MX", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

const getTemperatureStatus = (value: number): string => {
  if (value >= 32) return "Alta";
  if (value >= 24) return "Normal";
  return "Baja";
};

const getHumidityStatus = (value: number): string => {
  if (value >= 70) return "Alta";
  if (value >= 40) return "Normal";
  return "Baja";
};

const getLightStatus = (value: number): string => {
  if (value >= 70) return "Alta";
  if (value >= 30) return "Media";
  return "Baja";
};

type StatCardProps = {
  label: string;
  value: string;
  status: string;
  glowClass: string;
  disabled?: boolean;
};

function StatCard({
  label,
  value,
  status,
  glowClass,
  disabled = false,
}: StatCardProps) {
  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border p-4 shadow-lg backdrop-blur-md transition duration-300 ${
        disabled
          ? "border-slate-700 bg-slate-800/40 opacity-50"
          : `border-white/10 bg-white/5 hover:-translate-y-1 hover:bg-white/10 ${glowClass}`
      }`}
    >
      {!disabled && (
        <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-60" />
      )}

      <div className="relative z-10">
        <p className="text-sm text-slate-300">{label}</p>
        <p className="mt-2 text-3xl font-bold text-white">
          {disabled ? "Deshabilitado" : value}
        </p>
        <span className="mt-3 inline-flex rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs text-slate-200">
          {disabled ? "No disponible" : status}
        </span>
      </div>
    </div>
  );
}

function App() {
  const [latest, setLatest] = useState<SensorData[]>([]);
  const [history, setHistory] = useState<SensorData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [relayLoading, setRelayLoading] = useState<string>("");

  const getData = async (): Promise<void> => {
    try {
      setError("");

      const [latestRes, historyRes] = await Promise.all([
        fetch(`${API_BASE}/latest`),
        fetch(`${API_BASE}/history?limit=20`),
      ]);

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
    setRelayLoading(nodo);

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

      await getData();
    } catch (err) {
      console.error(err);
      setError("Error al enviar control");
    } finally {
      setRelayLoading("");
    }
  };

  const getNodeHistory = (nodo: string): SensorData[] => {
    return history
      .filter((item) => item.nodo === nodo)
      .map((item) => ({
        ...item,
        timestamp: formatChartTime(item.timestamp),
      }));
  };

  const summary = useMemo(() => {
    const activeNodes = latest.filter((item) => item.node_ok === true);

    if (activeNodes.length === 0) {
      return {
        totalNodos: latest.length,
        nodosDisponibles: 0,
        avgTemp: 0,
        avgHum: 0,
        avgLuz: 0,
      };
    }

    const nodosDisponibles = activeNodes.length;

    const avgTemp =
      activeNodes.reduce((acc, item) => acc + item.temperatura, 0) /
      nodosDisponibles;
    const avgHum =
      activeNodes.reduce((acc, item) => acc + item.humedad, 0) /
      nodosDisponibles;
    const avgLuz =
      activeNodes.reduce((acc, item) => acc + item.luz, 0) / nodosDisponibles;

    return {
      totalNodos: latest.length,
      nodosDisponibles,
      avgTemp,
      avgHum,
      avgLuz,
    };
  }, [latest]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <div className="rounded-2xl border border-white/10 bg-white/5 px-6 py-5 shadow-2xl backdrop-blur-md">
          <p className="text-lg font-semibold">Cargando dashboard...</p>
          <p className="mt-1 text-sm text-slate-300">
            Esperando datos de los nodos IoT
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="relative z-10 mx-auto max-w-7xl px-4 py-8 md:px-8">
        <header className="mb-8 overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl backdrop-blur-xl">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="mb-2 inline-flex rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-300">
                Sistema de monitoreo ambiental
              </p>
              <h1 className="text-3xl font-black tracking-tight md:text-5xl">
                Dashboard IoT
              </h1>
              <p className="mt-2 max-w-2xl text-sm text-slate-300 md:text-base">
                Visualización en tiempo real de temperatura, humedad, luz y
                control de relay por nodo.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 md:w-[360px]">
              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  Nodos disponibles
                </p>
                <p className="mt-2 text-2xl font-bold">
                  {summary.nodosDisponibles}
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  Temp. promedio
                </p>
                <p className="mt-2 text-2xl font-bold">
                  {summary.avgTemp.toFixed(1)} °C
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  Humedad prom.
                </p>
                <p className="mt-2 text-2xl font-bold">
                  {summary.avgHum.toFixed(1)} %
                </p>
              </div>

              <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  Luz promedio
                </p>
                <p className="mt-2 text-2xl font-bold">
                  {summary.avgLuz.toFixed(1)} %
                </p>
              </div>
            </div>
          </div>
        </header>

        {error && (
          <div className="mb-6 rounded-2xl border border-red-400/20 bg-red-500/10 px-4 py-3 text-red-200 shadow-lg">
            {error}
          </div>
        )}

        {latest.length === 0 ? (
          <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-center shadow-xl backdrop-blur-md">
            <h2 className="text-2xl font-bold">No hay datos disponibles</h2>
            <p className="mt-2 text-slate-300">
              Revisa que la API y los nodos estén enviando información.
            </p>
          </div>
        ) : (
          <div className="grid gap-8">
            {latest.map((node) => {
              const relayOn = node.relay_on === true;
              const nodeAvailable = node.node_ok === true;
              const dhtDisabled = node.dht_ok === false;
              const ldrDisabled = node.ldr_ok === false;
              const relayFailed = node.relay_ok === false;
              const chartDisabled =
                !nodeAvailable || (dhtDisabled && ldrDisabled);

              return (
                <section
                  key={node.nodo}
                  className="overflow-hidden rounded-3xl border border-white/10 bg-white/5 shadow-2xl backdrop-blur-xl"
                >
                  <div className="border-b border-white/10 bg-gradient-to-r from-cyan-500/10 via-slate-900/40 to-fuchsia-500/10 p-6">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                      <div>
                        <div className="mb-2 flex flex-wrap items-center gap-3">
                          <h2 className="text-2xl font-bold md:text-3xl">
                            {node.nodo}
                          </h2>

                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              nodeAvailable
                                ? "bg-cyan-400/15 text-cyan-300 ring-1 ring-cyan-400/20"
                                : "bg-amber-400/15 text-amber-300 ring-1 ring-amber-400/20"
                            }`}
                          >
                            {nodeAvailable
                              ? "Nodo disponible"
                              : "Nodo no disponible"}
                          </span>

                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              relayFailed
                                ? "bg-red-400/15 text-red-300 ring-1 ring-red-400/20"
                                : relayOn && nodeAvailable
                                  ? "bg-emerald-400/15 text-emerald-300 ring-1 ring-emerald-400/20"
                                  : "bg-slate-400/15 text-slate-300 ring-1 ring-white/10"
                            }`}
                          >
                            {relayFailed
                              ? "Relay con falla"
                              : `Relay ${relayOn && nodeAvailable ? "encendido" : "apagado"}`}
                          </span>

                          {node.dht_ok === false && (
                            <span className="rounded-full bg-rose-400/15 px-3 py-1 text-xs font-semibold text-rose-300 ring-1 ring-rose-400/20">
                              DHT con falla
                            </span>
                          )}

                          {node.ldr_ok === false && (
                            <span className="rounded-full bg-yellow-400/15 px-3 py-1 text-xs font-semibold text-yellow-300 ring-1 ring-yellow-400/20">
                              LDR con falla
                            </span>
                          )}
                        </div>

                        <p className="text-sm text-slate-300">
                          Última actualización:{" "}
                          {formatTimestamp(node.timestamp)}
                        </p>
                      </div>

                      <div className="flex flex-wrap gap-3">
                        <button
                          onClick={() => handleRelay(node.nodo, 1)}
                          disabled={
                            relayLoading === node.nodo ||
                            relayFailed ||
                            !nodeAvailable
                          }
                          className="rounded-2xl bg-emerald-400 px-5 py-3 font-semibold text-slate-900 shadow-lg transition hover:scale-[1.02] hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {relayLoading === node.nodo
                            ? "Enviando..."
                            : "Encender"}
                        </button>

                        <button
                          onClick={() => handleRelay(node.nodo, 0)}
                          disabled={
                            relayLoading === node.nodo ||
                            relayFailed ||
                            !nodeAvailable
                          }
                          className="rounded-2xl bg-rose-500 px-5 py-3 font-semibold text-white shadow-lg transition hover:scale-[1.02] hover:bg-rose-400 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {relayLoading === node.nodo
                            ? "Enviando..."
                            : "Apagar"}
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="grid gap-6 p-6 xl:grid-cols-[1.1fr_1.6fr]">
                    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
                      <StatCard
                        label="Temperatura"
                        value={`${node.temperatura} °C`}
                        status={getTemperatureStatus(node.temperatura)}
                        glowClass="hover:shadow-orange-500/20"
                        disabled={dhtDisabled || !nodeAvailable}
                      />

                      <StatCard
                        label="Humedad"
                        value={`${node.humedad} %`}
                        status={getHumidityStatus(node.humedad)}
                        glowClass="hover:shadow-sky-500/20"
                        disabled={dhtDisabled || !nodeAvailable}
                      />

                      <StatCard
                        label="Luminosidad"
                        value={`${node.luz} %`}
                        status={getLightStatus(node.luz)}
                        glowClass="hover:shadow-yellow-500/20"
                        disabled={ldrDisabled || !nodeAvailable}
                      />
                    </div>

                    <div
                      className={`rounded-3xl border p-4 shadow-inner ${
                        chartDisabled
                          ? "border-slate-700 bg-slate-900/40 opacity-50"
                          : "border-white/10 bg-slate-900/60"
                      }`}
                    >
                      <div className="mb-4 flex flex-col gap-1">
                        <h3 className="text-lg font-semibold">
                          Historial del nodo
                        </h3>
                        <p className="text-sm text-slate-400">
                          Últimas lecturas de temperatura, humedad y luz
                        </p>
                      </div>

                      <div className="relative h-[320px]">
                        {chartDisabled && (
                          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl bg-slate-950/40">
                            <p className="text-sm font-medium text-slate-300">
                              Gráfica no disponible
                            </p>
                          </div>
                        )}

                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={getNodeHistory(node.nodo)}>
                            <CartesianGrid
                              strokeDasharray="3 3"
                              stroke="rgba(148, 163, 184, 0.15)"
                            />
                            <XAxis
                              dataKey="timestamp"
                              tick={{ fill: "#cbd5e1", fontSize: 12 }}
                              axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
                              tickLine={false}
                            />
                            <YAxis
                              tick={{ fill: "#cbd5e1", fontSize: 12 }}
                              axisLine={{ stroke: "rgba(148, 163, 184, 0.2)" }}
                              tickLine={false}
                            />
                            <Tooltip
                              contentStyle={{
                                backgroundColor: "#0f172a",
                                border: "1px solid rgba(255,255,255,0.1)",
                                borderRadius: "16px",
                                color: "#fff",
                              }}
                            />
                            <Legend />
                            <Line
                              type="monotone"
                              dataKey="temperatura"
                              name="Temperatura"
                              stroke="#fb923c"
                              strokeWidth={3}
                              dot={false}
                            />
                            <Line
                              type="monotone"
                              dataKey="humedad"
                              name="Humedad"
                              stroke="#38bdf8"
                              strokeWidth={3}
                              dot={false}
                            />
                            <Line
                              type="monotone"
                              dataKey="luz"
                              name="Luz"
                              stroke="#facc15"
                              strokeWidth={3}
                              dot={false}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                </section>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
