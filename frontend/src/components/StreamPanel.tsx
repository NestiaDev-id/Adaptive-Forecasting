import { useCallback, useRef, useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Play, Square, RotateCcw, Zap, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

import { BASE_URL } from "@/lib/baseUrl";

interface StreamPoint {
  index: number;
  actual: number;
  prediction?: number;
  drift?: boolean;
}

interface Props {
  sampleData: number[];
}

export function StreamPanel({ sampleData }: Props) {
  const [points, setPoints] = useState<StreamPoint[]>([]);
  const [running, setRunning] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [stats, setStats] = useState({ drifts: 0, confidence: 0, steps: 0 });
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const indexRef = useRef(0);
  const [speed, setSpeed] = useState(1000);

  const init = useCallback(async () => {
    if (sampleData.length < 20) {
      toast.error("Minimum 20 data point untuk streaming");
      return;
    }

    // use first 60% as initial data
    const initSize = Math.floor(sampleData.length * 0.6);
    const initData = sampleData.slice(0, initSize);

    try {
      const res = await fetch(`${BASE_URL}/api/stream/init`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: initData }),
      });
      if (!res.ok) throw new Error("Init failed");

      const initialPoints: StreamPoint[] = initData.map((v, i) => ({
        index: i,
        actual: parseFloat(v.toFixed(2)),
      }));

      setPoints(initialPoints);
      indexRef.current = initSize;
      setInitialized(true);
      setStats({ drifts: 0, confidence: 0, steps: 0 });
      toast.success(`Stream diinisialisasi dengan ${initSize} data point`);
    } catch (e) {
      toast.error(`Gagal inisialisasi: ${e instanceof Error ? e.message : "Error"}`);
    }
  }, [sampleData]);

  const step = useCallback(async () => {
    if (indexRef.current >= sampleData.length) {
      setRunning(false);
      if (intervalRef.current) clearInterval(intervalRef.current);
      toast.info("Data habis. Streaming selesai.", { icon: "✅" });
      return;
    }

    const value = sampleData[indexRef.current];
    try {
      const res = await fetch(`${BASE_URL}/api/stream/step`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value }),
      });
      if (!res.ok) throw new Error("Step failed");

      const data = await res.json();

      const newPoint: StreamPoint = {
        index: indexRef.current,
        actual: parseFloat(value.toFixed(2)),
        prediction: parseFloat(data.prediction.toFixed(2)),
        drift: data.drift_detected,
      };

      setPoints((prev) => [...prev.slice(-100), newPoint]);
      setStats((prev) => ({
        drifts: prev.drifts + (data.drift_detected ? 1 : 0),
        confidence: data.confidence,
        steps: prev.steps + 1,
      }));

      if (data.drift_detected) {
        toast.warning("⚠️ Drift terdeteksi!", {
          description: `Langkah ${indexRef.current}: perubahan pola data mendadak`,
          duration: 5000,
        });
      }

      indexRef.current++;
    } catch (e) {
      toast.error(`Step error: ${e instanceof Error ? e.message : "Error"}`);
    }
  }, [sampleData]);

  const start = useCallback(() => {
    setRunning(true);
    intervalRef.current = setInterval(step, speed);
  }, [step, speed]);

  const stop = useCallback(() => {
    setRunning(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const reset = useCallback(async () => {
    stop();
    setPoints([]);
    setInitialized(false);
    setStats({ drifts: 0, confidence: 0, steps: 0 });
    indexRef.current = 0;
    try {
      await fetch(`${BASE_URL}/api/stream/reset`, { method: "POST" });
    } catch { /* ignore */ }
  }, [stop]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        {!initialized ? (
          <Button size="sm" onClick={init} className="gap-1.5 text-xs">
            <Zap className="h-3.5 w-3.5" /> Inisialisasi Stream
          </Button>
        ) : (
          <>
            {!running ? (
              <Button size="sm" onClick={start} className="gap-1.5 text-xs">
                <Play className="h-3.5 w-3.5" /> Mulai
              </Button>
            ) : (
              <Button size="sm" variant="secondary" onClick={stop} className="gap-1.5 text-xs">
                <Square className="h-3.5 w-3.5" /> Stop
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={reset} className="gap-1.5 text-xs">
              <RotateCcw className="h-3.5 w-3.5" /> Reset
            </Button>
          </>
        )}

        {initialized && (
          <div className="flex items-center gap-2 ml-auto">
            <label className="text-[10px] text-muted-foreground">Kecepatan:</label>
            <select
              value={speed}
              onChange={(e) => {
                const v = +e.target.value;
                setSpeed(v);
                if (running && intervalRef.current) {
                  clearInterval(intervalRef.current);
                  intervalRef.current = setInterval(step, v);
                }
              }}
              className="text-xs px-2 py-1 rounded-md bg-secondary/50 border border-border/50 text-foreground"
            >
              <option value={2000}>0.5x</option>
              <option value={1000}>1x</option>
              <option value={500}>2x</option>
              <option value={200}>5x</option>
            </select>
          </div>
        )}
      </div>

      {/* Stats */}
      {initialized && (
        <div className="flex gap-3">
          <Badge variant="outline" className="text-[10px] gap-1">
            <span className={`h-1.5 w-1.5 rounded-full ${running ? "bg-emerald-500 animate-pulse" : "bg-gray-400"}`} />
            {running ? "LIVE" : "PAUSED"}
          </Badge>
          <Badge variant="secondary" className="text-[10px]">
            Step: {stats.steps}
          </Badge>
          <Badge variant="secondary" className="text-[10px]">
            Confidence: {(stats.confidence * 100).toFixed(0)}%
          </Badge>
          {stats.drifts > 0 && (
            <Badge variant="destructive" className="text-[10px] gap-1">
              <AlertTriangle className="h-2.5 w-2.5" />
              {stats.drifts} drift
            </Badge>
          )}
        </div>
      )}

      {/* Live Chart */}
      {points.length > 0 && (
        <Card className="bg-card/50 border-border/50">
          <CardContent className="p-5">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">
              Live Prediction
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={points} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="index"
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
                />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                    color: "hsl(var(--foreground))",
                  }}
                />
                <Line
                  type="monotone" dataKey="actual" stroke="#3b82f6"
                  strokeWidth={2} dot={false} name="Aktual"
                  isAnimationActive={true} animationDuration={300}
                />
                <Line
                  type="monotone" dataKey="prediction" stroke="#f97316"
                  strokeWidth={2} strokeDasharray="4 2" dot={false} name="Prediksi"
                  isAnimationActive={true} animationDuration={300}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {!initialized && (
        <div className="text-center py-16 text-sm text-muted-foreground">
          <Zap className="h-8 w-8 mx-auto mb-3 text-purple-400/50" />
          <p>Klik "Inisialisasi Stream" untuk memulai mode live prediction.</p>
          <p className="text-xs mt-1">Sistem akan menggunakan 60% data awal untuk training, lalu mulai prediksi real-time.</p>
        </div>
      )}
    </div>
  );
}
