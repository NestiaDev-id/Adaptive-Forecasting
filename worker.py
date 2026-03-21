#!/usr/bin/env python3
"""
Standalone Worker — Background Process (6-Second Loop)
======================================================

This script runs independently (outside of Vercel/FastAPI) and performs
the real-time data ingestion + GA prediction cycle every 6 seconds.

It writes the latest prediction state to Upstash Redis, which is then
read by the Vercel Edge-cached endpoint (/api/forecast/latest).

Usage:
    # Set environment variables first (or use .env file)
    export UPSTASH_REDIS_REST_URL="https://..."
    export UPSTASH_REDIS_REST_TOKEN="..."

    python worker.py
"""

import sys
import os
import time
import json
import math
import logging
from datetime import datetime, timezone

# Ensure project root is importable
_project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, _project_root)

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_project_root, ".env"))
except ImportError:
    pass

from config import settings
from api.app.__utils__ import RedisManager

# ============================================================================
# CONFIGURATION
# ============================================================================
INTERVAL = settings.WORKER_INTERVAL_SECONDS  # default: 6 seconds
REDIS_KEY_LATEST = "public:latest_forecast"
REDIS_KEY_HISTORY = "public:forecast_history"
REDIS_KEY_STREAM_BUFFER = "stream:buffer"
HISTORY_MAX_LENGTH = 288  # ~24h of data at 5-min intervals (or 288 * 6s ≈ 28min)

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WORKER] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("worker")

# ============================================================================
# DATA SOURCE (Simulated)
# ============================================================================

class SimulatedSensor:
    """
    Simulates a real-time data source (e.g., BMKG temperature sensor).
    Replace this class with actual API calls for production use.

    Example replacement for BMKG:
        import httpx
        resp = httpx.get("https://api.bmkg.go.id/...")
        return resp.json()["temperature"]
    """

    def __init__(self):
        self._step = 0
        self._base = 50.0  # base temperature

    def read(self) -> float:
        """Return a simulated sensor reading with seasonal + noise pattern."""
        self._step += 1
        seasonal = 20 * math.sin(2 * math.pi * self._step / 144)  # ~24h cycle
        noise = (hash(self._step) % 100 - 50) / 25.0  # deterministic noise
        return round(self._base + seasonal + noise, 2)


# ============================================================================
# PREDICTION ENGINE (Lightweight)
# ============================================================================

class LightweightPredictor:
    """
    A lightweight prediction engine for the worker.
    Uses exponential smoothing for fast, per-tick predictions.

    For heavier GA-based predictions, import and use the full
    OnlineLoop from pipeline.online_loop.
    """

    def __init__(self):
        self._buffer: list[float] = []
        self._alpha = 0.3  # smoothing factor
        self._prediction = None

    def update(self, value: float) -> dict:
        self._buffer.append(value)

        # Keep buffer manageable
        if len(self._buffer) > 500:
            self._buffer = self._buffer[-500:]

        # Simple exponential smoothing prediction
        if self._prediction is None:
            self._prediction = value
        else:
            self._prediction = self._alpha * value + (1 - self._alpha) * self._prediction

        # Confidence based on buffer size & stability
        if len(self._buffer) < 5:
            confidence = 0.0
        else:
            recent = self._buffer[-10:]
            std = (sum((x - sum(recent)/len(recent))**2 for x in recent) / len(recent)) ** 0.5
            confidence = max(0, min(100, 100 - std * 2))

        return {
            "prediction": round(self._prediction, 4),
            "actual": value,
            "confidence": round(confidence, 2),
            "buffer_size": len(self._buffer),
        }


# ============================================================================
# MAIN LOOP
# ============================================================================

def main():
    log.info("=" * 60)
    log.info("🚀 Adaptive Forecasting Engine — Worker Started")
    log.info("   Interval: %d seconds", INTERVAL)
    log.info("   Redis: %s", settings.UPSTASH_REDIS_REST_URL[:40] + "..." if settings.UPSTASH_REDIS_REST_URL else "NOT CONFIGURED")
    log.info("=" * 60)

    redis = RedisManager()

    if not redis.is_connected:
        log.warning("⚠️  Redis not connected. Worker will run but cannot persist data.")
        log.warning("   Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN in .env")

    sensor = SimulatedSensor()
    predictor = LightweightPredictor()
    tick = 0

    try:
        while True:
            tick += 1
            start_time = time.time()

            # 1. Read sensor data
            value = sensor.read()

            # 2. Run prediction
            result = predictor.update(value)

            # 3. Build payload
            payload = {
                "tick": tick,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sensor_value": value,
                "prediction": result["prediction"],
                "confidence": result["confidence"],
                "buffer_size": result["buffer_size"],
            }

            # 4. Write to Redis
            if redis.is_connected:
                # Latest (overwrite)
                redis.set(REDIS_KEY_LATEST, payload)
                # History (append)
                redis.append_to_list(REDIS_KEY_HISTORY, payload, max_length=HISTORY_MAX_LENGTH)

            # 5. Log progress
            elapsed = time.time() - start_time
            log.info(
                "Tick %04d | Value: %7.2f | Pred: %7.2f | Conf: %5.1f%% | Redis: %s | %.0fms",
                tick, value, result["prediction"], result["confidence"],
                "✅" if redis.is_connected else "❌",
                elapsed * 1000,
            )

            # 6. Sleep for remaining interval
            sleep_time = max(0, INTERVAL - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        log.info("\n🛑 Worker stopped by user (Ctrl+C)")
    except Exception as e:
        log.error("💥 Worker crashed: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()
