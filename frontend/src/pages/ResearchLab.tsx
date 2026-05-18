import { useState, useEffect } from "react";
import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, ComposedChart
} from "recharts";
import {
  Activity, AlertTriangle, Cpu, HelpCircle, MapPin,
  RefreshCw, TrendingUp, ShieldAlert, ChevronDown
} from "lucide-react";
import { toast } from "sonner";

// ── Types ──────────────────────────────────────────────────────────────
interface AftershockInfo {
  risk: string;
  probability: number;
  latest_magnitude?: number;
  zone_average?: number;
  zone_max?: number;
  message: string;
}
interface LocationInfo {
  zone: string;
  latest_event: {
    area: string; datetime: string; magnitude: number | null;
    depth_km: number | null; latitude: number | null; longitude: number | null;
  };
  total_events_in_zone: number;
}
interface RecentArea {
  area: string; magnitude: number | null; depth_km: number | null;
  latitude: number | null; longitude: number | null;
}
interface ZoneInfo {
  area: string; event_count: number; max_magnitude: number;
  avg_magnitude: number; latitude: number | null; longitude: number | null;
}
interface ForecastData {
  status: string; model_type: string; context: number[];
  forecast: { mean: number[]; low: number[]; high: number[] };
  location?: LocationInfo; aftershock?: AftershockInfo; recent_areas?: RecentArea[];
}
interface ChartPoint {
  index: number; value?: number; forecast?: number;
  type: string; low: number; high: number;
}

// ── Component ──────────────────────────────────────────────────────────
export default function ResearchLab() {
  const [loading, setLoading] = useState(false);
  const [limit, setLimit] = useState(30);
  const [horizon, setHorizon] = useState(10);
  const [apiUrl] = useState("http://localhost:7860");
  const [apiStatus, setApiStatus] = useState<"online" | "offline" | "checking">("checking");
  const [data, setData] = useState<ForecastData | null>(null);
  const [zones, setZones] = useState<ZoneInfo[]>([]);
  const [selectedZone, setSelectedZone] = useState<string>("all");

  // ── API health check ────────────────────────────────────────────────
  const checkApiStatus = async (silent = false) => {
    if (!silent) setApiStatus("checking");
    try {
      const res = await fetch(apiUrl);
      if (res.ok) { await res.json(); setApiStatus("online"); if (!silent) toast.success("Connected!"); }
      else setApiStatus("offline");
    } catch { setApiStatus("offline"); }
  };

  // ── Fetch zones ─────────────────────────────────────────────────────
  const fetchZones = async () => {
    try {
      const res = await fetch(`${apiUrl}/zones`);
      if (res.ok) { const r = await res.json(); setZones(r.zones ?? []); }
    } catch {
      // Offline fallback zones
      setZones([
        { area: "Java, Indonesia", event_count: 22, max_magnitude: 5.1, avg_magnitude: 3.2, latitude: -7.5, longitude: 110.0 },
        { area: "Banda Sea", event_count: 8, max_magnitude: 4.8, avg_magnitude: 3.5, latitude: -5.5, longitude: 130.0 },
        { area: "Halmahera, Indonesia", event_count: 8, max_magnitude: 4.3, avg_magnitude: 2.9, latitude: 1.0, longitude: 128.0 },
        { area: "Sulawesi, Indonesia", event_count: 7, max_magnitude: 4.6, avg_magnitude: 3.1, latitude: -1.5, longitude: 121.0 },
        { area: "Sumatra, Indonesia", event_count: 6, max_magnitude: 5.3, avg_magnitude: 3.4, latitude: 0.5, longitude: 101.0 },
      ]);
    }
  };

  // ── Forecast ────────────────────────────────────────────────────────
  const handleForecast = async (initial = false) => {
    setLoading(true);
    try {
      const body: Record<string, unknown> = { limit, horizon };
      if (selectedZone !== "all") body.zone = selectedZone;
      const response = await fetch(`${apiUrl}/analyze/earthquake`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (response.ok) {
        const result = await response.json();
        setData(result);
        if (!initial) toast.success("Prediksi berhasil!");
      } else throw new Error("API error");
    } catch {
      // ── offline simulation ────────────────────────────────────────
      const mockCtx = Array.from({ length: limit }, () => Number((2.0 + Math.random() * 3.5).toFixed(1)));
      const mockMean: number[] = []; const mockLow: number[] = []; const mockHigh: number[] = [];
      let last = mockCtx[mockCtx.length - 1];
      const avg = mockCtx.reduce((a, b) => a + b, 0) / limit;
      for (let i = 1; i <= horizon; i++) {
        const s = last * 0.75 + avg * 0.25 + (Math.random() - 0.5) * 0.4;
        const u = 1.2 * 0.4 * Math.sqrt(i);
        mockMean.push(Number(s.toFixed(2)));
        mockLow.push(Number(Math.max(1.0, s - u).toFixed(2)));
        mockHigh.push(Number(Math.min(9.5, s + u).toFixed(2)));
        last = s;
      }
      const zoneName = selectedZone === "all" ? "Seluruh Indonesia" : selectedZone;
      setData({
        status: "success", model_type: "Simulation Mode (Offline)",
        context: mockCtx, forecast: { mean: mockMean, low: mockLow, high: mockHigh },
        location: {
          zone: zoneName,
          latest_event: { area: zoneName, datetime: new Date().toISOString(), magnitude: mockCtx[mockCtx.length - 1], depth_km: 10, latitude: -6.2, longitude: 106.8 },
          total_events_in_zone: limit,
        },
        aftershock: {
          risk: Math.max(...mockCtx) >= 5.0 ? "high" : "low",
          probability: Math.max(...mockCtx) >= 5.0 ? 65 : 12,
          latest_magnitude: mockCtx[mockCtx.length - 1],
          zone_average: Number(avg.toFixed(2)),
          zone_max: Math.max(...mockCtx),
          message: `Simulasi aktivitas seismik di zona ${zoneName}.`,
        },
        recent_areas: [
          { area: "Sunda Strait", magnitude: 3.4, depth_km: 15, latitude: -6.1, longitude: 105.4 },
          { area: "Java Sea", magnitude: 2.8, depth_km: 22, latitude: -5.8, longitude: 112.0 },
          { area: "Northern Sumatra", magnitude: 4.1, depth_km: 30, latitude: 3.5, longitude: 98.5 },
        ],
      });
      if (!initial) toast.info("Simulasi lokal (Research Space offline).");
    } finally { setLoading(false); }
  };

  useEffect(() => { checkApiStatus(true); fetchZones(); handleForecast(true); }, []);

  // ── Chart data ──────────────────────────────────────────────────────
  const getChartData = (): ChartPoint[] => {
    if (!data) return [];
    const cd: ChartPoint[] = [];
    data.context.forEach((v, i) => cd.push({ index: i - data.context.length, value: v, type: "Historical", low: v, high: v }));
    data.forecast.mean.forEach((v, i) => cd.push({ index: i + 1, value: v, forecast: v, type: "Forecast", low: data.forecast.low[i], high: data.forecast.high[i] }));
    return cd;
  };
  const chartData = getChartData();
  const maxMag = data ? Math.max(...data.context) : 0;
  const predictedPeak = data ? Math.max(...data.forecast.mean) : 0;
  const aftershock = data?.aftershock;

  // ── Risk color helpers ──────────────────────────────────────────────
  const riskColor = (r?: string) => r === "very_high" || r === "high" ? "text-red-400 border-red-500/30 bg-red-500/5" : r === "moderate" ? "text-amber-400 border-amber-500/30 bg-amber-500/5" : "text-emerald-400 border-emerald-500/30 bg-emerald-500/5";
  const riskBarColor = (r?: string) => r === "very_high" || r === "high" ? "bg-red-500" : r === "moderate" ? "bg-amber-500" : "bg-emerald-500";

  return (
    <div className="p-8 space-y-8 min-h-screen bg-slate-950 text-slate-100">
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="flex items-center gap-3">
          <span className="p-2 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20">
            <ShieldAlert className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Disaster AI Research Lab</h1>
            <p className="text-sm text-slate-400">
              Peramalan tren seismik per zona menggunakan Amazon Chronos-2 + deteksi gempa susulan (Omori/Bath Law).
            </p>
          </div>
        </div>
        {/* Connection badge */}
        <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 p-3 rounded-xl shadow-lg">
          <div className="text-right">
            <div className="text-[10px] uppercase text-slate-500 font-semibold">AI Space</div>
            <div className="text-xs font-medium text-slate-300">{apiUrl}</div>
          </div>
          <span className={`h-2.5 w-2.5 rounded-full ${apiStatus === "online" ? "bg-emerald-500 animate-pulse" : apiStatus === "offline" ? "bg-rose-500" : "bg-amber-500"}`} />
          <button onClick={() => checkApiStatus()} className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"><RefreshCw className="h-3.5 w-3.5" /></button>
        </div>
      </div>

      {/* ── Grid ───────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">

        {/* ── LEFT: Controls ─────────────────────────────────────── */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900/60 backdrop-blur-xl border border-slate-800 p-6 rounded-2xl space-y-6 shadow-xl">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Cpu className="h-4 w-4 text-blue-400" /> Parameter Kontrol
            </h2>

            {/* Zone Selector */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-red-400" /> Zona Seismik
              </label>
              <div className="relative">
                <select
                  value={selectedZone}
                  onChange={(e) => setSelectedZone(e.target.value)}
                  className="w-full appearance-none bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-xl px-4 py-2.5 pr-10 focus:border-blue-500 focus:outline-none transition-colors cursor-pointer"
                >
                  <option value="all">🌏 Seluruh Indonesia ({zones.reduce((a, z) => a + z.event_count, 0)} events)</option>
                  {zones.map(z => (
                    <option key={z.area} value={z.area}>
                      📍 {z.area} — {z.event_count} events (max M{z.max_magnitude})
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 pointer-events-none" />
              </div>
            </div>

            {/* Context Limit */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-slate-400">Context Length</span>
                <span className="text-blue-400 font-bold">{limit} events</span>
              </div>
              <input type="range" min="10" max="100" value={limit} onChange={e => setLimit(Number(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500" />
            </div>

            {/* Horizon */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-medium">
                <span className="text-slate-400">Forecast Horizon</span>
                <span className="text-purple-400 font-bold">{horizon} steps</span>
              </div>
              <input type="range" min="5" max="30" value={horizon} onChange={e => setHorizon(Number(e.target.value))} className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500" />
            </div>

            {/* Run button */}
            <button onClick={() => handleForecast()} disabled={loading} className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all shadow-lg shadow-purple-500/15 disabled:opacity-50">
              {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <TrendingUp className="h-4 w-4" />}
              {loading ? "Menghitung..." : "Jalankan Chronos"}
            </button>
          </div>

          {/* ── Aftershock Risk Panel ───────────────────────────── */}
          {aftershock && (
            <div className={`border p-5 rounded-2xl space-y-4 ${riskColor(aftershock.risk)}`}>
              <h3 className="text-sm font-bold uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" /> Risiko Gempa Susulan
              </h3>
              <div className="flex items-center gap-3">
                <div className="text-3xl font-black">{aftershock.probability}%</div>
                <div className="flex-1">
                  <div className="h-2.5 bg-slate-800 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-700 ${riskBarColor(aftershock.risk)}`} style={{ width: `${aftershock.probability}%` }} />
                  </div>
                </div>
              </div>
              <p className="text-xs leading-relaxed opacity-80">{aftershock.message}</p>
              {aftershock.latest_magnitude && (
                <div className="grid grid-cols-3 gap-2 text-xs pt-2 border-t border-current/10">
                  <div><span className="block text-[10px] opacity-50">Terakhir</span><span className="font-bold">M{aftershock.latest_magnitude}</span></div>
                  <div><span className="block text-[10px] opacity-50">Rata-rata</span><span className="font-bold">M{aftershock.zone_average}</span></div>
                  <div><span className="block text-[10px] opacity-50">Maks</span><span className="font-bold">M{aftershock.zone_max}</span></div>
                </div>
              )}
            </div>
          )}

          {/* Model Meta */}
          <div className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl text-xs space-y-3">
            <h3 className="font-semibold text-slate-300">Model Info</h3>
            <div className="flex justify-between"><span className="text-slate-500">Framework</span><span className="text-slate-300 font-mono">amazon/chronos-t5-tiny</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Pipeline</span><span className="text-purple-400 font-medium">{data?.model_type || "None"}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Zona</span><span className="text-blue-400 font-medium">{data?.location?.zone || "—"}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Events</span><span className="text-slate-300">{data?.location?.total_events_in_zone ?? "—"}</span></div>
          </div>
        </div>

        {/* ── RIGHT: Charts & Results ────────────────────────────── */}
        <div className="lg:col-span-3 space-y-8">

          {/* Location Banner */}
          {data?.location && (
            <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 p-4 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-blue-400" />
                <div>
                  <div className="text-sm font-bold text-white">Prediksi untuk: {data.location.zone}</div>
                  <div className="text-xs text-slate-400">
                    Gempa terakhir: M{data.location.latest_event.magnitude} · Kedalaman {data.location.latest_event.depth_km} km · {data.location.latest_event.area}
                  </div>
                </div>
              </div>
              {data.location.latest_event.latitude && (
                <div className="text-xs text-slate-500 font-mono">
                  📍 {data.location.latest_event.latitude?.toFixed(2)}°, {data.location.latest_event.longitude?.toFixed(2)}°
                </div>
              )}
            </div>
          )}

          {/* Metric Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl relative overflow-hidden shadow-md">
              <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Magnitudo Maks Historis</div>
              <div className="text-2xl font-bold mt-2 text-red-400">{maxMag.toFixed(1)} <span className="text-xs font-normal text-slate-500">Mw</span></div>
              <div className="absolute right-4 bottom-4 text-red-500/10"><Activity className="h-12 w-12" /></div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl relative overflow-hidden shadow-md">
              <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Prediksi Puncak Tren</div>
              <div className="text-2xl font-bold mt-2 text-purple-400">{predictedPeak.toFixed(2)} <span className="text-xs font-normal text-slate-500">Mw</span></div>
              <div className="absolute right-4 bottom-4 text-purple-500/10"><TrendingUp className="h-12 w-12" /></div>
            </div>
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl relative overflow-hidden shadow-md">
              <div className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Tingkat Risiko</div>
              <div className="text-2xl font-bold mt-2 flex items-center gap-2">
                {predictedPeak >= 5.0
                  ? <span className="text-red-400 flex items-center gap-1.5 text-xl"><AlertTriangle className="h-5 w-5" /> HIGH</span>
                  : predictedPeak >= 3.5
                  ? <span className="text-amber-400 flex items-center gap-1.5 text-xl"><AlertTriangle className="h-5 w-5" /> MEDIUM</span>
                  : <span className="text-emerald-400 flex items-center gap-1.5 text-xl"><HelpCircle className="h-5 w-5" /> LOW</span>}
              </div>
              <div className="absolute right-4 bottom-4 text-slate-500/10"><ShieldAlert className="h-12 w-12" /></div>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-purple-400" /> Tren Prediksi Chronos-2
                {data?.location && <span className="text-xs font-normal text-slate-500 ml-2">— {data.location.zone}</span>}
              </h3>
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-slate-400"><span className="h-2 w-2 rounded-full bg-red-400" /> Histori</span>
                <span className="flex items-center gap-1.5 text-purple-400"><span className="h-2 w-2 rounded-full bg-purple-500 animate-pulse" /> Prediksi</span>
                <span className="flex items-center gap-1.5 text-purple-500/40"><span className="h-2 w-4 rounded-sm bg-purple-500/30" /> 95% CI</span>
              </div>
            </div>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="purpleGlow" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#a855f7" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="index" stroke="#64748b" tickLine={false} />
                  <YAxis stroke="#64748b" tickLine={false} domain={[1.0, "auto"]} />
                  <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "12px" }} labelStyle={{ color: "#94a3b8", fontWeight: "bold" }} />
                  <Area type="monotone" dataKey="high" stroke="none" fill="url(#purpleGlow)" fillOpacity={0.4} />
                  <Area type="monotone" dataKey="low" stroke="none" fill="#0f172a" fillOpacity={0.8} />
                  <Line type="monotone" dataKey="value" stroke="#f87171" strokeWidth={2} dot={false} name="Histori" />
                  <Line type="monotone" dataKey="forecast" stroke="#a855f7" strokeWidth={3} strokeDasharray="5 5" dot={{ stroke: "#c084fc", strokeWidth: 2, r: 4 }} name="Prediksi Chronos" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Areas with Location */}
          {data?.recent_areas && data.recent_areas.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl">
              <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">🌍 Lokasi Aktivitas Seismik Terbaru</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 text-xs">
                {data.recent_areas.map((loc, idx) => (
                  <div key={idx} className="bg-slate-950 border border-slate-800 p-4 rounded-xl hover:border-red-500/30 transition-colors space-y-2">
                    <span className="text-red-400 font-semibold block">{loc.area}</span>
                    <div className="space-y-1 text-slate-400">
                      {loc.magnitude != null && <div>Magnitudo: <span className="text-white font-bold">M{loc.magnitude}</span></div>}
                      {loc.depth_km != null && <div>Kedalaman: <span className="text-slate-300">{loc.depth_km} km</span></div>}
                      {loc.latitude != null && <div className="font-mono text-[10px] text-slate-600">{loc.latitude.toFixed(2)}°, {loc.longitude?.toFixed(2)}°</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
