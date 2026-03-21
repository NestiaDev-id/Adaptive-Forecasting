export interface DriftEvent {
  method: string;
  magnitude: number;
  location: number;
}

export interface AdaptationEvent {
  action: string;
  confidence: number;
  reason: string;
}

export interface FitnessRecord {
  gen: number;
  best: number;
  avg: number;
  diversity: number;
  metric: string;
  avg_mutation: number;
}

export interface DataProfile {
  trend_strength: number;
  seasonal_strength: number;
  noise_level: number;
  seasonal_period: number;
  stationarity: number;
  data_length: number;
}

export interface BestIndividual {
  fitness: number;
  mutation_rate: number;
  crossover_rate: number;
  mutation_step: number;
  model_weights: Record<string, number>;
  holt_winters_params: Record<string, unknown>;
  arima_params: Record<string, unknown>;
}

export interface ForecastResponse {
  forecast: number[];
  forecast_lower: number[];
  forecast_upper: number[];
  confidence: number;
  val_predictions: number[];
  val_actual: number[];
  val_mse: number;
  profile: DataProfile;
  best_individual: BestIndividual;
  final_weights: Record<string, number>;
  drift_events: DriftEvent[];
  adaptation_history: AdaptationEvent[];
  fitness_history: FitnessRecord[];
}

interface ForecastRequest {
  data: number[];
  horizon: number;
  generations: number;
  population: number;
  val_ratio: number;
}

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "";

export const api = {
  forecast: async (req: ForecastRequest): Promise<ForecastResponse> => {
    const res = await fetch(`${BASE_URL}/api/forecast`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });

    if (!res.ok) {
      const err = (await res
        .json()
        .catch(() => ({ detail: res.statusText }))) as { detail?: string };
      throw new Error(err.detail ?? `HTTP ${res.status}`);
    }

    return res.json() as Promise<ForecastResponse>;
  },
};
