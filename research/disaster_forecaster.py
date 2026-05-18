import os
import json
import numpy as np
from datetime import datetime
from collections import Counter

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

    def _load_quakes(self) -> list[dict]:
        """Load and sort earthquake data from the BMKG JSON file."""
        if not os.path.exists(DATA_PATH):
            return []
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        quakes = data.get("earthquakes", [])
        # Sort oldest → newest
        return sorted(quakes, key=lambda x: x.get("datetime", ""))

    def get_available_zones(self) -> dict:
        """
        Returns all unique seismic zones with event counts.
        Useful for the frontend zone selector dropdown.
        """
        quakes = self._load_quakes()
        if not quakes:
            return {"status": "error", "message": "No data available."}

        area_counts = Counter(q.get("area", "Unknown") for q in quakes)
        # Sort by frequency (most active zones first)
        sorted_zones = sorted(area_counts.items(), key=lambda x: -x[1])

        zones = []
        for area, count in sorted_zones:
            area_quakes = [q for q in quakes if q.get("area") == area]
            max_mag = max((q["magnitude"] for q in area_quakes if q.get("magnitude")), default=0)
            avg_mag = np.mean([q["magnitude"] for q in area_quakes if q.get("magnitude")]) if area_quakes else 0
            # Get representative coordinates (from the latest event in the zone)
            latest = area_quakes[-1] if area_quakes else {}
            zones.append({
                "area": area,
                "event_count": count,
                "max_magnitude": float(max_mag),
                "avg_magnitude": round(float(avg_mag), 2),
                "latitude": latest.get("latitude"),
                "longitude": latest.get("longitude"),
            })

        return {
            "status": "success",
            "total_events": len(quakes),
            "total_zones": len(zones),
            "zones": zones,
        }

    def _predict_series(self, context: list[float], horizon: int) -> dict:
        """
        Core prediction logic — uses Chronos if available, otherwise statistical fallback.
        Returns dict with mean, low, high arrays.
        """
        if self.model_loaded and self.pipeline:
            import torch
            context_tensor = torch.tensor(context, dtype=torch.float32).unsqueeze(0)
            with torch.no_grad():
                forecast = self.pipeline.predict(context_tensor, horizon)
                samples = forecast[0].numpy()
                mean = np.mean(samples, axis=0).tolist()
                low = np.percentile(samples, 2.5, axis=0).tolist()
                high = np.percentile(samples, 97.5, axis=0).tolist()
        else:
            # High-fidelity statistical fallback simulation
            mean_val = np.mean(context)
            std_val = np.std(context)
            mean, low, high = [], [], []
            last_val = context[-1]
            for i in range(1, horizon + 1):
                step_mean = last_val * 0.8 + mean_val * 0.2 + np.random.normal(0, 0.1)
                mean.append(float(np.clip(step_mean, 1.0, 9.5)))
                uncertainty = std_val * 0.5 * np.sqrt(i)
                low.append(float(np.clip(step_mean - uncertainty, 1.0, 9.5)))
                high.append(float(np.clip(step_mean + uncertainty, 1.0, 9.5)))
                last_val = step_mean

        return {"mean": mean, "low": low, "high": high}

    def _assess_aftershock_risk(self, quakes: list[dict]) -> dict:
        """
        Assess aftershock probability using a simplified Omori's Law.

        Omori's Law: n(t) = K / (c + t)^p
        Where:
          - n(t) = rate of aftershocks at time t after mainshock
          - K, c, p = empirical constants (p ≈ 1.0 for most sequences)

        We simplify by checking: was the latest event significantly larger than
        the running average? If so, aftershocks are likely.
        """
        if len(quakes) < 3:
            return {"risk": "unknown", "probability": 0, "message": "Not enough data."}

        magnitudes = [q["magnitude"] for q in quakes if q.get("magnitude") is not None]
        if not magnitudes:
            return {"risk": "unknown", "probability": 0, "message": "No magnitude data."}

        latest_mag = magnitudes[-1]
        avg_mag = np.mean(magnitudes[:-1]) if len(magnitudes) > 1 else magnitudes[0]
        max_mag = max(magnitudes)
        std_mag = np.std(magnitudes) if len(magnitudes) > 1 else 0.5

        # How many standard deviations is the latest event above average?
        z_score = (latest_mag - avg_mag) / std_mag if std_mag > 0 else 0

        # Aftershock probability heuristic
        # Based on Bath's Law: largest aftershock ≈ mainshock - 1.2 Mw
        if latest_mag == max_mag and latest_mag >= 5.0:
            probability = min(95, int(60 + z_score * 15))
            risk = "very_high"
            expected_aftershock_mag = round(latest_mag - 1.2, 1)
            message = (
                f"Gempa M{latest_mag} adalah yang terbesar di zona ini. "
                f"Berdasarkan Hukum Bath, gempa susulan diperkirakan hingga M{expected_aftershock_mag}."
            )
        elif latest_mag >= 4.0 and z_score > 1.0:
            probability = min(80, int(40 + z_score * 12))
            risk = "high"
            expected_aftershock_mag = round(latest_mag - 1.2, 1)
            message = (
                f"Gempa M{latest_mag} secara signifikan di atas rata-rata zona (M{avg_mag:.1f}). "
                f"Potensi gempa susulan hingga M{expected_aftershock_mag}."
            )
        elif z_score > 0.5:
            probability = min(50, int(20 + z_score * 10))
            risk = "moderate"
            message = f"Aktivitas seismik sedikit meningkat dari rata-rata M{avg_mag:.1f}."
        else:
            probability = max(5, int(10 - abs(z_score) * 3))
            risk = "low"
            message = f"Aktivitas seismik normal di sekitar rata-rata M{avg_mag:.1f}."

        return {
            "risk": risk,
            "probability": probability,
            "latest_magnitude": float(latest_mag),
            "zone_average": round(float(avg_mag), 2),
            "zone_max": float(max_mag),
            "message": message,
        }

    def forecast_earthquakes(self, limit: int = 50, horizon: int = 10, zone: str | None = None) -> dict:
        """
        Loads the BMKG earthquake data, optionally filters by zone,
        and forecasts future magnitude trends with aftershock assessment.
        """
        all_quakes = self._load_quakes()
        if not all_quakes:
            return {"status": "error", "message": "No earthquake data available."}

        # Filter by zone if specified
        if zone and zone != "all":
            filtered = [q for q in all_quakes if q.get("area", "").lower() == zone.lower()]
            if len(filtered) < 5:
                return {
                    "status": "error",
                    "message": f"Zona '{zone}' hanya memiliki {len(filtered)} data — minimum 5 diperlukan untuk prediksi."
                }
            working_quakes = filtered
        else:
            working_quakes = all_quakes

        # Extract magnitudes
        magnitudes = [q["magnitude"] for q in working_quakes if q.get("magnitude") is not None]
        if len(magnitudes) < 10:
            return {"status": "error", "message": "Not enough data points for time-series analysis."}

        context = magnitudes[-limit:]
        print(f"[Forecaster] Zone='{zone or 'ALL'}' | {len(context)} events | Horizon={horizon}")

        # Perform forecast
        forecast = self._predict_series(context, horizon)

        # Aftershock assessment
        aftershock = self._assess_aftershock_risk(working_quakes)

        # Location metadata from the working set
        latest_quake = working_quakes[-1]
        location_info = {
            "zone": zone or "Seluruh Indonesia",
            "latest_event": {
                "area": latest_quake.get("area", "Unknown"),
                "datetime": latest_quake.get("datetime", ""),
                "magnitude": latest_quake.get("magnitude"),
                "depth_km": latest_quake.get("depth_km"),
                "latitude": latest_quake.get("latitude"),
                "longitude": latest_quake.get("longitude"),
            },
            "total_events_in_zone": len(working_quakes),
        }

        # Top 5 most recent areas for the selected scope
        recent_areas = []
        seen = set()
        for q in reversed(working_quakes):
            area = q.get("area", "Unknown")
            if area not in seen:
                recent_areas.append({
                    "area": area,
                    "magnitude": q.get("magnitude"),
                    "depth_km": q.get("depth_km"),
                    "latitude": q.get("latitude"),
                    "longitude": q.get("longitude"),
                })
                seen.add(area)
            if len(recent_areas) >= 5:
                break

        return {
            "status": "success",
            "model_type": "Chronos-T5-Tiny" if self.model_loaded else "Simulation Mode",
            "location": location_info,
            "context": context,
            "forecast": forecast,
            "aftershock": aftershock,
            "recent_areas": recent_areas,
        }


if __name__ == "__main__":
    forecaster = ChronosDisasterForecaster()

    # 1. List available zones
    zones = forecaster.get_available_zones()
    print("--- Available Seismic Zones ---")
    for z in zones.get("zones", [])[:10]:
        print(f"  {z['area']}: {z['event_count']} events (max M{z['max_magnitude']})")

    # 2. Forecast for a specific zone
    print("\n--- Zone-Specific Forecast: Java, Indonesia ---")
    res = forecaster.forecast_earthquakes(limit=20, horizon=10, zone="Java, Indonesia")
    print(json.dumps(res, indent=2, ensure_ascii=False))
