import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import type { FitnessRecord } from "@/lib/api";

interface Props {
  history: FitnessRecord[];
}

export function FitnessChart({ history }: Props) {
  const data = history.map((h) => ({
    gen: h.gen,
    best: parseFloat(h.best.toFixed(4)),
    avg: parseFloat(Math.min(h.avg, h.best * 10).toFixed(4)),
    mutation: parseFloat(h.avg_mutation.toFixed(4)),
    diversity: parseFloat(h.diversity.toFixed(4)),
  }));

  return (
    <div className="w-full">
      <h3 className="text-sm font-medium text-muted-foreground mb-3">
        Evolusi Fitness (per Generasi)
      </h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="gen" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
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
            type="monotone" dataKey="best" stroke="#10b981"
            strokeWidth={2} dot={false} name="Best Fitness"
          />
          <Line
            type="monotone" dataKey="avg" stroke="#6b7280"
            strokeWidth={1} dot={false} name="Avg Fitness"
          />
        </LineChart>
      </ResponsiveContainer>

      <h3 className="text-sm font-medium text-muted-foreground mb-3 mt-4">
        Meta-Evolution (Mutation Rate)
      </h3>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="gen" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} />
          <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} domain={[0, 0.5]} />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              color: "hsl(var(--foreground))",
            }}
          />
          <Line
            type="monotone" dataKey="mutation" stroke="#a855f7"
            strokeWidth={2} dot={false} name="Avg Mutation Rate"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
