import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from "recharts";

interface Props {
  weights: Record<string, number>;
}

const COLORS = ["#3b82f6", "#f97316", "#a855f7", "#10b981", "#ef4444"];

export function WeightsChart({ weights }: Props) {
  const data = Object.entries(weights)
    .sort(([, a], [, b]) => b - a)
    .map(([name, value]) => ({
      name: name.replace(/_/g, " "),
      weight: parseFloat((value * 100).toFixed(1)),
    }));

  return (
    <div className="w-full">
      <h3 className="text-sm font-medium text-muted-foreground mb-3">
        Bobot Model Ensemble
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis
            dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
          />
          <YAxis
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
            domain={[0, 100]} unit="%"
          />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
              color: "hsl(var(--foreground))",
            }}
            formatter={(value: number) => [`${value}%`, "Bobot"]}
          />
          <Bar dataKey="weight" radius={[6, 6, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
