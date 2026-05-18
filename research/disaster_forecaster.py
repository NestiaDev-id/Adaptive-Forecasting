import os
import json
import numpy as np
from datetime import datetime

# Path to the scraped BMKG data
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw", "bmkg_quakes_realtime.json")

class ChronosDisasterForecaster:
    def __init__(self):
        self.model_loaded = False
        self.pipeline = None
        self._try_load_chronos()

    def _try_load_chronos(self):
        """Attempts to load the Hugging Face chronos-forecasting pipeline."""
        try:
            import torch
            from chronos import ChronosPipeline
            print("[Chronos] Loading pre-trained Chronos-2 foundation model...")
            # We use the small/tiny variant for optimal CPU/Space loading
            self.pipeline = ChronosPipeline.from_pretrained(
                "amazon/chronos-t5-tiny",
                device_map="auto",
                torch_dtype=torch.float32
            )
            self.model_loaded = True
            print("[Chronos] Model loaded successfully.")
        except ImportError:
            print("[Chronos] chronos-forecasting or torch not installed. Running in local simulation mode.")
        except Exception as e:
            print(f"[Chronos] Failed to load model: {e}. Falling back to simulation.")

    def forecast_earthquakes(self, limit: int = 50, horizon: int = 10) -> dict:
        """
        Loads the BMKG earthquake magnitudes and forecasts future trends.
        """
        # 1. Load data
        if not os.path.exists(DATA_PATH):
            return {"status": "error", "message": f"Data file not found at {DATA_PATH}"}

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        quakes = data.get("earthquakes", [])
        if not quakes:
            return {"status": "error", "message": "No earthquakes found in the dataset."}

        # Sort by datetime (oldest to newest for time-series)
        # BMKG usually returns newest first, so we reverse it
        sorted_quakes = sorted(quakes, key=lambda x: x.get("datetime", ""))
        
        # Extract magnitudes
        magnitudes = [q["magnitude"] for q in sorted_quakes if q.get("magnitude") is not None]
        
        if len(magnitudes) < 10:
            return {"status": "error", "message": "Not enough data points for time-series analysis."}

        # Keep the latest N points for forecasting context
        context = magnitudes[-limit:]
        
        print(f"[Forecaster] Running predictions on latest {len(context)} earthquake magnitudes...")

        # 2. Perform forecasting
        if self.model_loaded and self.pipeline:
            import torch
            # Chronos expects a 2D tensor of shape [num_series, series_length]
            context_tensor = torch.tensor(context, dtype=torch.float32).unsqueeze(0)
            
            # Predict
            with torch.no_grad():
                forecast = self.pipeline.predict(context_tensor, horizon)
                # forecast shape: [num_series, num_samples, horizon]
                # We calculate mean and 95% confidence intervals (low/high)
                samples = forecast[0].numpy()
                mean = np.mean(samples, axis=0).tolist()
                low = np.percentile(samples, 2.5, axis=0).tolist()
                high = np.percentile(samples, 97.5, axis=0).tolist()
        else:
            # High-fidelity statistical fallback simulation for local development
            mean_val = np.mean(context)
            std_val = np.std(context)
            
            # Generate drift-aware walk forecast
            mean = []
            low = []
            high = []
            
            last_val = context[-1]
            for i in range(1, horizon + 1):
                # Regression to mean + minor volatility
                step_mean = last_val * 0.8 + mean_val * 0.2 + np.random.normal(0, 0.1)
                mean.append(float(np.clip(step_mean, 1.0, 9.5)))
                
                # Confidence intervals widen over time
                uncertainty = std_val * 0.5 * np.sqrt(i)
                low.append(float(np.clip(step_mean - uncertainty, 1.0, 9.5)))
                high.append(float(np.clip(step_mean + uncertainty, 1.0, 9.5)))
                last_val = step_mean

        return {
            "status": "success",
            "model_type": "Chronos-T5-Tiny" if self.model_loaded else "Simulation Mode",
            "context": context,
            "forecast": {
                "mean": mean,
                "low": low,
                "high": high
            },
            "recent_areas": [q.get("area", "Unknown") for q in sorted_quakes[-5:]]
        }

if __name__ == "__main__":
    forecaster = ChronosDisasterForecaster()
    res = forecaster.forecast_earthquakes(limit=30, horizon=10)
    print("\n--- Forecaster Output ---")
    print(json.dumps(res, indent=2))
