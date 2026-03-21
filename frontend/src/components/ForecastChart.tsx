import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Area, AreaChart, Legend,
} from "recharts";
import type { ForecastResponse } from "@/lib/api";

interface Props {
  result: ForecastResponse;
}

export function ForecastChart({ result }: Props) {
  // build chart data: historical (val_actual) + forecast
  const valLen = result.val_actual.length;

  const historicalData = result.val_actual.map((val, i) => ({
    index: i,
    label: `t-${valLen - i}`,
    actual: parseFloat(val.toFixed(2)),
    predicted: parseFloat(result.val_predictions[i].toFixed(2)),
  }));

  const forecastData = result.forecast.map((val, i) => ({
    index: valLen + i,
    label: `t+${i + 1}`,
    forecast: parseFloat(val.toFixed(2)),
    lower: parseFloat(result.forecast_lower[i].toFixed(2)),
    upper: parseFloat(result.forecast_upper[i].toFixed(2)),
  }));

  return (
    <div className="w-full">
      <h3 className="text-sm font-medium text-muted-foreground mb-3">
        Validasi: Aktual vs Prediksi
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={historicalData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="label" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
          <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              color: "hsl(var(--foreground))",
            }}
          />
          <Legend />
          <Line
            type="monotone" dataKey="actual" stroke="#3b82f6"
            strokeWidth={2} dot={false} name="Aktual"
          />
          <Line
            type="monotone" dataKey="predicted" stroke="#f97316"
            strokeWidth={2} strokeDasharray="6 3" dot={false} name="Prediksi"
          />
        </LineChart>
      </ResponsiveContainer>

      <h3 className="text-sm font-medium text-muted-foreground mb-3 mt-6">
        Forecast {result.forecast.length} Langkah ke Depan
      </h3>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={forecastData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="label" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
          <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              color: "hsl(var(--foreground))",
            }}
          />
          <Area
            type="monotone" dataKey="upper" stroke="none"
            fill="#f9731622" name="Batas Atas"
          />
          <Area
            type="monotone" dataKey="lower" stroke="none"
            fill="#3b82f600" name="Batas Bawah"
          />
          <Line
            type="monotone" dataKey="forecast" stroke="#f97316"
            strokeWidth={2.5} dot={{ r: 4, fill: "#f97316" }} name="Forecast"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
