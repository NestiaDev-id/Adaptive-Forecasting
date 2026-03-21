import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { motion } from "motion/react";
import type { ForecastResponse } from "@/lib/api";

interface Props {
  result: ForecastResponse;
}

export function ProfilePanel({ result }: Props) {
  const p = result.profile;
  const best = result.best_individual;

  const profileBars = [
    { label: "Trend", value: p.trend_strength, color: "bg-blue-500" },
    { label: "Seasonal", value: p.seasonal_strength, color: "bg-orange-500" },
    { label: "Noise", value: p.noise_level, color: "bg-red-500" },
    { label: "Stationarity", value: p.stationarity, color: "bg-emerald-500" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      <Card className="bg-card/50 border-border/50">
        <CardContent className="p-5 space-y-5">
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-3">
              Profil Data
            </h3>
            <div className="space-y-3">
              {profileBars.map((bar, i) => (
                <motion.div
                  key={bar.label}
                  initial={{ opacity: 0, x: -15 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 + 0.2, duration: 0.4 }}
                >
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">{bar.label}</span>
                    <span className="font-mono text-foreground">
                      {(bar.value * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full ${bar.color} rounded-full`}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(bar.value * 100, 100)}%` }}
                      transition={{
                        delay: i * 0.1 + 0.4,
                        duration: 0.8,
                        ease: [0.34, 1.56, 0.64, 1],
                      }}
                    />
                  </div>
                </motion.div>
              ))}
            </div>
            {p.seasonal_period > 0 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.8, type: "spring", stiffness: 400 }}
              >
                <Badge variant="outline" className="mt-3">
                  Period: T={p.seasonal_period}
                </Badge>
              </motion.div>
            )}
          </div>

          <motion.div
            className="border-t border-border/50 pt-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <h3 className="text-sm font-semibold text-foreground mb-3">
              Strategy DNA
            </h3>
            <div className="space-y-2 text-xs">
              {[
                { label: "Mutation Rate", value: best.mutation_rate, color: "text-purple-400" },
                { label: "Crossover Rate", value: best.crossover_rate, color: "text-blue-400" },
                { label: "Mutation Step", value: best.mutation_step, color: "text-emerald-400" },
              ].map((item, i) => (
                <motion.div
                  key={item.label}
                  className="flex justify-between"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + i * 0.08 }}
                  whileHover={{ x: 3 }}
                >
                  <span className="text-muted-foreground">{item.label}</span>
                  <span className={`font-mono ${item.color}`}>
                    {item.value.toFixed(4)}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {result.drift_events.length > 0 && (
            <motion.div
              className="border-t border-border/50 pt-4"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9 }}
            >
              <h3 className="text-sm font-semibold text-foreground mb-2">
                Drift Events
              </h3>
              <div className="space-y-2">
                {result.drift_events.map((de, i) => (
                  <motion.div
                    key={i}
                    className="text-xs p-2 bg-secondary/50 rounded-md"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1.0 + i * 0.08, type: "spring" }}
                    whileHover={{ scale: 1.02 }}
                  >
                    <span className="text-amber-400">{de.method}</span>
                    {" · "}
                    <span className="text-muted-foreground">
                      mag={de.magnitude.toFixed(2)} @ step {de.location}
                    </span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {result.adaptation_history.length > 0 && (
            <motion.div
              className="border-t border-border/50 pt-4"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.1 }}
            >
              <h3 className="text-sm font-semibold text-foreground mb-2">
                Aksi Adaptasi
              </h3>
              <div className="space-y-2">
                {result.adaptation_history.map((aa, i) => (
                  <motion.div
                    key={i}
                    className="text-xs p-2 bg-secondary/50 rounded-md"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 1.2 + i * 0.06 }}
                    whileHover={{ scale: 1.02 }}
                  >
                    <Badge variant="secondary" className="text-[10px] mb-1">
                      {aa.action}
                    </Badge>
                    <p className="text-muted-foreground">{aa.reason}</p>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
