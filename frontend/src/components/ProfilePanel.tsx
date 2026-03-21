import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
    <Card className="bg-card/50 border-border/50">
      <CardContent className="p-5 space-y-5">
        <div>
          <h3 className="text-sm font-semibold text-foreground mb-3">
            Profil Data
          </h3>
          <div className="space-y-3">
            {profileBars.map((bar) => (
              <div key={bar.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-muted-foreground">{bar.label}</span>
                  <span className="font-mono text-foreground">
                    {(bar.value * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className={`h-full ${bar.color} rounded-full transition-all duration-700`}
                    style={{ width: `${Math.min(bar.value * 100, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
          {p.seasonal_period > 0 && (
            <Badge variant="outline" className="mt-3">
              Period: T={p.seasonal_period}
            </Badge>
          )}
        </div>

        <div className="border-t border-border/50 pt-4">
          <h3 className="text-sm font-semibold text-foreground mb-3">
            Strategy DNA
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Mutation Rate</span>
              <span className="font-mono text-purple-400">
                {best.mutation_rate.toFixed(4)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Crossover Rate</span>
              <span className="font-mono text-blue-400">
                {best.crossover_rate.toFixed(4)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Mutation Step</span>
              <span className="font-mono text-emerald-400">
                {best.mutation_step.toFixed(4)}
              </span>
            </div>
          </div>
        </div>

        {result.drift_events.length > 0 && (
          <div className="border-t border-border/50 pt-4">
            <h3 className="text-sm font-semibold text-foreground mb-2">
              Drift Events
            </h3>
            <div className="space-y-2">
              {result.drift_events.map((de, i) => (
                <div key={i} className="text-xs p-2 bg-secondary/50 rounded-md">
                  <span className="text-amber-400">{de.method}</span>
                  {" · "}
                  <span className="text-muted-foreground">
                    mag={de.magnitude.toFixed(2)} @ step {de.location}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {result.adaptation_history.length > 0 && (
          <div className="border-t border-border/50 pt-4">
            <h3 className="text-sm font-semibold text-foreground mb-2">
              Aksi Adaptasi
            </h3>
            <div className="space-y-2">
              {result.adaptation_history.map((aa, i) => (
                <div key={i} className="text-xs p-2 bg-secondary/50 rounded-md">
                  <Badge variant="secondary" className="text-[10px] mb-1">
                    {aa.action}
                  </Badge>
                  <p className="text-muted-foreground">{aa.reason}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
