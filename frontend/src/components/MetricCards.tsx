import { Card, CardContent } from "@/components/ui/card";
import {
  TrendingUp, Shield, AlertTriangle, Cpu,
  Activity, BarChart3, Zap, Target,
} from "lucide-react";
import { motion } from "motion/react";
import type { ForecastResponse } from "@/lib/api";

interface Props {
  result: ForecastResponse;
}

export function MetricCards({ result }: Props) {
  const rmse = Math.sqrt(result.val_mse);
  const confidence = result.confidence * 100;
  const drifts = result.drift_events.length;
  const adaptations = result.adaptation_history.length;

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
      {cards.map((card, index) => (
        <motion.div
          key={card.label}
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{
            duration: 0.4,
            delay: index * 0.06,
            ease: [0.25, 0.46, 0.45, 0.94],
          }}
          whileHover={{ y: -2, scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <Card className="bg-card/50 border-border/50 backdrop-blur-sm cursor-default">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground font-medium">
                  {card.label}
                </span>
                <motion.div
                  initial={{ rotate: -90, opacity: 0 }}
                  animate={{ rotate: 0, opacity: 1 }}
                  transition={{ delay: index * 0.06 + 0.2, type: "spring", stiffness: 300 }}
                >
                  <card.icon className={`h-4 w-4 ${card.color}`} />
                </motion.div>
              </div>
              <motion.p
                className={`text-xl font-bold ${card.color}`}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.06 + 0.15, duration: 0.3 }}
              >
                {card.value}
              </motion.p>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
