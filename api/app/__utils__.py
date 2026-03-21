import sys
import os
import json
import logging

# Ensure the project root is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from pipeline.online_loop import OnlineLoop
from config import settings

logger = logging.getLogger("afe.utils")

# ============================================================================
# REDIS MANAGER — Serverless State Persistence
# ============================================================================

class RedisManager:
    """
    Manages state persistence via Upstash Redis (REST API).
    Falls back to in-memory dict when Redis is not configured (local dev).
    """

    def __init__(self):
        self._redis = None
        self._fallback: dict[str, str] = {}  # local-dev fallback (in-memory)

        url = settings.UPSTASH_REDIS_REST_URL
        token = settings.UPSTASH_REDIS_REST_TOKEN

        if url and token:
            try:
                from upstash_redis import Redis
                self._redis = Redis(url=url, token=token)
                logger.info("✅ Upstash Redis connected: %s", url[:40] + "...")
            except Exception as e:
                logger.warning("❌ Upstash Redis connection failed: %s. Using in-memory fallback.", e)
        else:
            logger.info("⚠️  No UPSTASH_REDIS_REST_URL configured. Using in-memory fallback.")

    @property
    def is_connected(self) -> bool:
        return self._redis is not None

    def get(self, key: str) -> dict | None:
        """Retrieve JSON object by key."""
        try:
            if self._redis:
                raw = self._redis.get(key)
                if raw is None:
                    return None
                # Upstash REST client auto-parses JSON strings,
                # but if it returns a string, parse it ourselves
                if isinstance(raw, str):
                    return json.loads(raw)
                if isinstance(raw, dict):
                    return raw
                return None
            else:
                raw = self._fallback.get(key)
                return json.loads(raw) if raw else None
        except Exception as e:
            logger.error("Redis GET error for key '%s': %s", key, e)
            return None

    def set(self, key: str, value: dict, ttl_seconds: int | None = None) -> bool:
        """Store JSON object by key. Optional TTL in seconds."""
        try:
            payload = json.dumps(value)
            if self._redis:
                if ttl_seconds:
                    self._redis.set(key, payload, ex=ttl_seconds)
                else:
                    self._redis.set(key, payload)
            else:
                self._fallback[key] = payload
            return True
        except Exception as e:
            logger.error("Redis SET error for key '%s': %s", key, e)
            return False

    def delete(self, key: str) -> bool:
        """Delete a key."""
        try:
            if self._redis:
                self._redis.delete(key)
            else:
                self._fallback.pop(key, None)
            return True
        except Exception as e:
            logger.error("Redis DELETE error for key '%s': %s", key, e)
            return False

    def append_to_list(self, key: str, value: dict, max_length: int = 100) -> bool:
        """Append an item to a JSON list stored at key, trimming to max_length."""
        try:
            existing = self.get(key) or []
            if not isinstance(existing, list):
                existing = []
            existing.append(value)
            # Trim to max_length (keep most recent)
            if len(existing) > max_length:
                existing = existing[-max_length:]
            return self.set(key, existing)
        except Exception as e:
            logger.error("Redis APPEND error for key '%s': %s", key, e)
            return False


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

# Global RedisManager (lazy-loaded, shared across requests)
_redis_manager: RedisManager | None = None

def get_redis() -> RedisManager:
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


# In-memory OnlineLoop (kept for local dev / single-server use)
_online_loop: OnlineLoop | None = None
_engine_state: dict = {
    "status": "idle",
    "last_profile": None,
    "last_best_individual": None,
    "total_forecasts": 0,
    "total_trainings": 0,
}


def get_online_loop() -> OnlineLoop:
    global _online_loop
    if _online_loop is None:
        _online_loop = OnlineLoop()
    return _online_loop


def reset_online_loop():
    global _online_loop
    if _online_loop is not None:
        _online_loop.reset()
    _online_loop = None


def get_engine_state() -> dict:
    return _engine_state


def update_engine_state(**kwargs):
    _engine_state.update(kwargs)
