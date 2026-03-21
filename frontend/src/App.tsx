import { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import {
  Activity, Play, DatabaseZap, BarChart3,
  TrendingUp, Settings2, Sparkles, Radio,
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { toast } from "sonner";

import { api, type ForecastResponse } from "@/lib/api";
import { ForecastChart } from "@/components/ForecastChart";
import { FitnessChart } from "@/components/FitnessChart";
import { WeightsChart } from "@/components/WeightsChart";
import { MetricCards } from "@/components/MetricCards";
import { ProfilePanel } from "@/components/ProfilePanel";
import { ThemeToggle } from "@/components/ThemeToggle";
import { FileUpload } from "@/components/FileUpload";
import { ExportButton } from "@/components/ExportButton";
import { StreamPanel } from "@/components/StreamPanel";
import { NumberInput } from "@/components/NumberInput";

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
  const [dataInput, setDataInput] = useState(SAMPLE_DATA.join(", "));
  const [parsedData, setParsedData] = useState<number[]>(SAMPLE_DATA);
  const [horizon, setHorizon] = useState(12);
  const [generations, setGenerations] = useState(30);
  const [population, setPopulation] = useState(20);

  const parseData = useCallback((): number[] => {
    return dataInput
      .split(/[,\s\n]+/)
      .map(Number)
      .filter((n) => !isNaN(n));
  }, [dataInput]);

  const handleForecast = async () => {
    setLoading(true);
    try {
      const data = parseData();
      if (data.length < 10) {
        toast.error("Minimum 10 data point diperlukan.");
        return;
      }
      setParsedData(data);
      toast.info("Menjalankan Self-Adaptive GA...", { duration: 2000, icon: "🧬" });

      const res = await api.forecast({
        data, horizon, generations, population,
        val_ratio: 0.2,
      });
      setResult(res);
      toast.success("Forecast berhasil!", {
        description: `RMSE: ${Math.sqrt(res.val_mse).toFixed(2)} · Confidence: ${(res.confidence * 100).toFixed(0)}%`,
      });

      if (res.drift_events.length > 0) {
        for (const de of res.drift_events) {
          toast.warning(`⚠️ Drift terdeteksi: ${de.method}`, {
            description: `Magnitude: ${de.magnitude.toFixed(3)} pada langkah ${de.location}`,
            duration: 8000,
          });
        }
      }

      if (res.adaptation_history.length > 0) {
        toast.info(`${res.adaptation_history.length} aksi adaptasi dilakukan`, {
          description: res.adaptation_history.map((a) => a.action).join(", "),
          duration: 5000,
        });
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Terjadi kesalahan.");
    } finally {
      setLoading(false);
    }
  };

  const loadSample = () => {
    setDataInput(SAMPLE_DATA.join(", "));
    setParsedData(SAMPLE_DATA);
    toast.info("Sample data dimuat (120 data point seasonal)");
  };

  const handleFileLoaded = (data: number[], _fileName: string) => {
    setDataInput(data.join(", "));
    setParsedData(data);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <motion.header
        className="border-b border-border/50 bg-card/30 backdrop-blur-md sticky top-0 z-50"
        initial={{ y: -60, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
      >
        <div className="max-w-[1400px] mx-auto px-6 h-14 flex items-center justify-between">
          <motion.div
            className="flex items-center gap-3"
            whileHover={{ scale: 1.01 }}
          >
            <motion.div
              className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center"
              whileHover={{ rotate: 15, scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              transition={{ type: "spring", stiffness: 400 }}
            >
              <Sparkles className="h-4 w-4 text-white" />
            </motion.div>
            <h1 className="font-semibold text-foreground tracking-tight">
              Adaptive Forecasting Engine
            </h1>
          </motion.div>
          <div className="flex items-center gap-2">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Badge variant="outline" className="text-xs gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Self-Adaptive GA
              </Badge>
            </motion.div>
            <ThemeToggle />
          </div>
        </div>
      </motion.header>

      {/* Main */}
      <main className="max-w-[1400px] mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left: Input panel */}
          <motion.div
            className="lg:col-span-1 space-y-4"
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.15, ease: "easeOut" }}
          >
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold flex items-center gap-2">
                    <DatabaseZap className="h-4 w-4 text-blue-400" />
                    Input Data
                  </h2>
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Button variant="ghost" size="sm" onClick={loadSample} className="text-xs h-7">
                      Sample
                    </Button>
                  </motion.div>
                </div>

                <FileUpload onDataLoaded={handleFileLoaded} />

                <Textarea
                  value={dataInput}
                  onChange={(e) => setDataInput(e.target.value)}
                  placeholder="Masukkan data time series... (pisahkan dengan koma)"
                  className="h-28 text-xs font-mono resize-none bg-secondary/30"
                />

                <Separator />

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-xs text-muted-foreground flex items-center gap-1">
                      <Settings2 className="h-3 w-3" /> Parameter
                    </label>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <NumberInput label="Horizon" value={horizon} onChange={setHorizon} min={1} max={100} />
                    <NumberInput label="Generasi" value={generations} onChange={setGenerations} min={5} max={500} />
                    <NumberInput label="Populasi" value={population} onChange={setPopulation} min={10} max={200} />
                  </div>
                </div>

                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>
                  <Button
                    className="w-full gap-2"
                    onClick={handleForecast}
                    disabled={loading}
                  >
                    {loading ? (
                      <>
                        <Spinner className="h-4 w-4" />
                        Memproses...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4" />
                        Jalankan Forecast
                      </>
                    )}
                  </Button>
                </motion.div>
              </CardContent>
            </Card>

            <AnimatePresence>
              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 20, height: 0 }}
                  animate={{ opacity: 1, y: 0, height: "auto" }}
                  exit={{ opacity: 0, y: 20, height: 0 }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                >
                  <ProfilePanel result={result} />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Right: Results area */}
          <div className="lg:col-span-3 space-y-6">
            <AnimatePresence mode="wait">
              {!result && !loading && (
                <motion.div
                  key="empty"
                  className="flex flex-col items-center justify-center py-32 text-center"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95, y: -20 }}
                  transition={{ duration: 0.4 }}
                >
                  <motion.div
                    className="h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 flex items-center justify-center mb-4"
                    animate={{ y: [0, -6, 0] }}
                    transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                  >
                    <TrendingUp className="h-8 w-8 text-blue-400" />
                  </motion.div>
                  <h2 className="text-lg font-semibold text-foreground mb-2">
                    Siap untuk Forecast
                  </h2>
                  <p className="text-sm text-muted-foreground max-w-md">
                    Masukkan data time series, upload CSV, atau gunakan Sample Data.
                    Sistem akan mendeteksi pola, menjalankan Self-Adaptive GA, dan menghasilkan prediksi
                    dengan confidence interval.
                  </p>
                </motion.div>
              )}

              {loading && (
                <motion.div
                  key="loading"
                  className="flex flex-col items-center justify-center py-32"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.3 }}
                >
                  <Spinner className="h-10 w-10 text-blue-400 mb-4" />
                  <motion.p
                    className="text-sm text-muted-foreground"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  >
                    Menjalankan Self-Adaptive GA...
                  </motion.p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Mendeteksi pola → Evolusi populasi → Adaptasi strategi
                  </p>
                </motion.div>
              )}

              {result && !loading && (
                <motion.div
                  key="results"
                  className="space-y-6"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  {/* Header with export */}
                  <motion.div
                    className="flex items-center justify-between"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <h2 className="text-sm font-medium text-muted-foreground">
                      Hasil Forecast ({result.forecast.length} langkah · {result.fitness_history.length} generasi)
                    </h2>
                    <ExportButton result={result} chartContainerId="chart-container" />
                  </motion.div>

                  {/* Metric cards */}
                  <MetricCards result={result} />

                  {/* Charts tabs */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3, duration: 0.4 }}
                  >
                    <Tabs defaultValue="forecast" className="w-full">
                      <TabsList className="grid grid-cols-4 w-full max-w-lg">
                        <TabsTrigger value="forecast" className="gap-1 text-xs">
                          <BarChart3 className="h-3 w-3" /> Forecast
                        </TabsTrigger>
                        <TabsTrigger value="fitness" className="gap-1 text-xs">
                          <Activity className="h-3 w-3" /> Fitness
                        </TabsTrigger>
                        <TabsTrigger value="weights" className="gap-1 text-xs">
                          <TrendingUp className="h-3 w-3" /> Bobot
                        </TabsTrigger>
                        <TabsTrigger value="live" className="gap-1 text-xs">
                          <Radio className="h-3 w-3" /> Live
                        </TabsTrigger>
                      </TabsList>

                      <TabsContent value="forecast">
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3 }}
                        >
                          <Card className="bg-card/50 border-border/50" id="chart-container">
                            <CardContent className="p-5">
                              <ForecastChart result={result} />
                            </CardContent>
                          </Card>
                        </motion.div>
                      </TabsContent>

                      <TabsContent value="fitness">
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3 }}
                        >
                          <Card className="bg-card/50 border-border/50">
                            <CardContent className="p-5">
                              <FitnessChart history={result.fitness_history} />
                            </CardContent>
                          </Card>
                        </motion.div>
                      </TabsContent>

                      <TabsContent value="weights">
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3 }}
                        >
                          <Card className="bg-card/50 border-border/50">
                            <CardContent className="p-5">
                              <WeightsChart weights={result.final_weights} />
                            </CardContent>
                          </Card>
                        </motion.div>
                      </TabsContent>

                      <TabsContent value="live">
                        <motion.div
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3 }}
                        >
                          <StreamPanel sampleData={parsedData} />
                        </motion.div>
                      </TabsContent>
                    </Tabs>
                  </motion.div>

                  {/* Forecast table */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5, duration: 0.4 }}
                  >
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
                                <motion.tr
                                  key={i}
                                  className="border-b border-border/30 hover:bg-secondary/20 transition-colors"
                                  initial={{ opacity: 0, x: -8 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: 0.5 + i * 0.03, duration: 0.2 }}
                                >
                                  <td className="py-2 text-foreground font-mono">t+{i + 1}</td>
                                  <td className="py-2 text-right text-orange-400 font-mono">{f.toFixed(2)}</td>
                                  <td className="py-2 text-right text-muted-foreground font-mono">{result.forecast_lower[i].toFixed(2)}</td>
                                  <td className="py-2 text-right text-muted-foreground font-mono">{result.forecast_upper[i].toFixed(2)}</td>
                                </motion.tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
