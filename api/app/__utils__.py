import sys
import os

# Ensure the project root is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from pipeline.online_loop import OnlineLoop

# Shared singleton instances across requests
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
