import { Card, CardContent } from "@/components/ui/card";
import {
  TrendingUp, Shield, AlertTriangle, Cpu,
  Activity, BarChart3, Zap, Target,
} from "lucide-react";
import type { ForecastResponse } from "@/lib/api";

interface Props {
  result: ForecastResponse;
}

export function MetricCards({ result }: Props) {
  const rmse = Math.sqrt(result.val_mse);
  const confidence = result.confidence * 100;
  const drifts = result.drift_events.length;
  const adaptations = result.adaptation_history.length;

  // find best model
  const bestModel = Object.entries(result.final_weights)
    .sort(([, a], [, b]) => b - a)[0];

  const cards = [
    {
      label: "Val RMSE",
      value: rmse.toFixed(2),
      icon: Target,
      color: rmse < 5 ? "text-emerald-400" : rmse < 10 ? "text-amber-400" : "text-red-400",
    },
    {
      label: "Confidence",
      value: `${confidence.toFixed(1)}%`,
      icon: Shield,
      color: confidence > 60 ? "text-emerald-400" : confidence > 40 ? "text-amber-400" : "text-red-400",
    },
    {
      label: "Drift Events",
      value: drifts.toString(),
      icon: AlertTriangle,
      color: drifts === 0 ? "text-emerald-400" : "text-amber-400",
    },
    {
      label: "Adaptasi",
      value: adaptations.toString(),
      icon: Zap,
      color: "text-purple-400",
    },
    {
      label: "Best Model",
      value: bestModel ? bestModel[0].replace(/_/g, " ") : "—",
      icon: Cpu,
      color: "text-blue-400",
    },
    {
      label: "Best Fitness",
      value: result.best_individual.fitness.toFixed(4),
      icon: TrendingUp,
      color: "text-emerald-400",
    },
    {
      label: "Generasi",
      value: result.fitness_history.length.toString(),
      icon: Activity,
      color: "text-indigo-400",
    },
    {
      label: "Season Period",
      value: result.profile.seasonal_period > 0
        ? `T=${result.profile.seasonal_period}` : "—",
      icon: BarChart3,
      color: "text-cyan-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {cards.map((card) => (
        <Card key={card.label} className="bg-card/50 border-border/50 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-muted-foreground font-medium">
                {card.label}
              </span>
              <card.icon className={`h-4 w-4 ${card.color}`} />
            </div>
            <p className={`text-xl font-bold ${card.color}`}>
              {card.value}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
