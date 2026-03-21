import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Activity, Play, Loader2, DatabaseZap, BarChart3,
  TrendingUp, Settings2, Sparkles,
} from "lucide-react";

import { api, type ForecastResponse } from "@/lib/api";
import { ForecastChart } from "@/components/ForecastChart";
import { FitnessChart } from "@/components/FitnessChart";
import { WeightsChart } from "@/components/WeightsChart";
import { MetricCards } from "@/components/MetricCards";
import { ProfilePanel } from "@/components/ProfilePanel";

// sample seasonal data
const SAMPLE_DATA = Array.from({ length: 120 }, (_, i) => {
  const trend = 50 + i * 0.3;
  const seasonal = 20 * Math.sin((2 * Math.PI * i) / 12);
  const noise = (Math.random() - 0.5) * 5;
  return parseFloat((trend + seasonal + noise).toFixed(2));
});

function App() {
  const [result, setResult] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataInput, setDataInput] = useState(SAMPLE_DATA.join(", "));
  const [horizon, setHorizon] = useState(12);
  const [generations, setGenerations] = useState(30);
  const [population, setPopulation] = useState(20);

  const handleForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = dataInput
        .split(/[,\s\n]+/)
        .map(Number)
        .filter((n) => !isNaN(n));

      if (data.length < 10) {
        throw new Error("Minimum 10 data point diperlukan.");
      }

      const res = await api.forecast({
        data, horizon, generations, population,
        val_ratio: 0.2,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Terjadi kesalahan.");
    } finally {
      setLoading(false);
    }
  };

  const loadSample = () => {
    setDataInput(SAMPLE_DATA.join(", "));
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/30 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <h1 className="font-semibold text-foreground tracking-tight">
              Adaptive Forecasting Engine
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Self-Adaptive GA
            </Badge>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-[1400px] mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left: Input panel */}
          <div className="lg:col-span-1 space-y-4">
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold flex items-center gap-2">
                    <DatabaseZap className="h-4 w-4 text-blue-400" />
                    Input Data
                  </h2>
                  <Button variant="ghost" size="sm" onClick={loadSample} className="text-xs h-7">
                    Sample
                  </Button>
                </div>

                <Textarea
                  value={dataInput}
                  onChange={(e) => setDataInput(e.target.value)}
                  placeholder="Masukkan data time series... (pisahkan dengan koma)"
                  className="h-32 text-xs font-mono resize-none bg-secondary/30"
                />

                <Separator />

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-xs text-muted-foreground flex items-center gap-1">
                      <Settings2 className="h-3 w-3" /> Parameter
                    </label>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="text-[10px] text-muted-foreground block mb-1">Horizon</label>
                      <input
                        type="number" value={horizon}
                        onChange={(e) => setHorizon(+e.target.value)}
                        className="w-full text-xs px-2 py-1.5 rounded-md bg-secondary/50 border border-border/50 text-foreground"
                        min={1} max={100}
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground block mb-1">Generasi</label>
                      <input
                        type="number" value={generations}
                        onChange={(e) => setGenerations(+e.target.value)}
                        className="w-full text-xs px-2 py-1.5 rounded-md bg-secondary/50 border border-border/50 text-foreground"
                        min={5} max={500}
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground block mb-1">Populasi</label>
                      <input
                        type="number" value={population}
                        onChange={(e) => setPopulation(+e.target.value)}
                        className="w-full text-xs px-2 py-1.5 rounded-md bg-secondary/50 border border-border/50 text-foreground"
                        min={10} max={200}
                      />
                    </div>
                  </div>
                </div>

                <Button
                  className="w-full gap-2"
                  onClick={handleForecast}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Memproses...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Jalankan Forecast
                    </>
                  )}
                </Button>

                {error && (
                  <p className="text-xs text-red-400 text-center">{error}</p>
                )}
              </CardContent>
            </Card>

            {/* Profile panel (only when results exist) */}
            {result && <ProfilePanel result={result} />}
          </div>

          {/* Right: Results area */}
          <div className="lg:col-span-3 space-y-6">
            {!result && !loading && (
              <div className="flex flex-col items-center justify-center py-32 text-center">
                <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 flex items-center justify-center mb-4">
                  <TrendingUp className="h-8 w-8 text-blue-400" />
                </div>
                <h2 className="text-lg font-semibold text-foreground mb-2">
                  Siap untuk Forecast
                </h2>
                <p className="text-sm text-muted-foreground max-w-md">
                  Masukkan data time series dan klik "Jalankan Forecast" untuk memulai.
                  Sistem akan mendeteksi pola, menjalankan Self-Adaptive GA, dan menghasilkan prediksi
                  dengan confidence interval.
                </p>
              </div>
            )}

            {loading && (
              <div className="flex flex-col items-center justify-center py-32">
                <Loader2 className="h-10 w-10 animate-spin text-blue-400 mb-4" />
                <p className="text-sm text-muted-foreground">
                  Menjalankan Self-Adaptive GA...
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Mendeteksi pola → Evolusi populasi → Adaptasi strategi
                </p>
              </div>
            )}

            {result && !loading && (
              <>
                {/* Metric cards */}
                <MetricCards result={result} />

                {/* Charts tabs */}
                <Tabs defaultValue="forecast" className="w-full">
                  <TabsList className="grid grid-cols-3 w-full max-w-md">
                    <TabsTrigger value="forecast" className="gap-1 text-xs">
                      <BarChart3 className="h-3 w-3" /> Forecast
                    </TabsTrigger>
                    <TabsTrigger value="fitness" className="gap-1 text-xs">
                      <Activity className="h-3 w-3" /> Fitness
                    </TabsTrigger>
                    <TabsTrigger value="weights" className="gap-1 text-xs">
                      <TrendingUp className="h-3 w-3" /> Bobot
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="forecast">
                    <Card className="bg-card/50 border-border/50">
                      <CardContent className="p-5">
                        <ForecastChart result={result} />
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="fitness">
                    <Card className="bg-card/50 border-border/50">
                      <CardContent className="p-5">
                        <FitnessChart history={result.fitness_history} />
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="weights">
                    <Card className="bg-card/50 border-border/50">
                      <CardContent className="p-5">
                        <WeightsChart weights={result.final_weights} />
                      </CardContent>
                    </Card>
                  </TabsContent>
                </Tabs>

                {/* Forecast table */}
                <Card className="bg-card/50 border-border/50">
                  <CardContent className="p-5">
                    <h3 className="text-sm font-medium text-muted-foreground mb-3">
                      Tabel Forecast
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-border/50">
                            <th className="text-left py-2 text-muted-foreground font-medium">Langkah</th>
                            <th className="text-right py-2 text-muted-foreground font-medium">Prediksi</th>
                            <th className="text-right py-2 text-muted-foreground font-medium">Batas Bawah</th>
                            <th className="text-right py-2 text-muted-foreground font-medium">Batas Atas</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.forecast.map((f, i) => (
                            <tr key={i} className="border-b border-border/30">
                              <td className="py-2 text-foreground font-mono">t+{i + 1}</td>
                              <td className="py-2 text-right text-orange-400 font-mono">{f.toFixed(2)}</td>
                              <td className="py-2 text-right text-muted-foreground font-mono">{result.forecast_lower[i].toFixed(2)}</td>
                              <td className="py-2 text-right text-muted-foreground font-mono">{result.forecast_upper[i].toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
