import logging
import sys
from datetime import datetime


# ---------------------------------------------------------------------------
# Colour codes for terminal (ANSI)
# ---------------------------------------------------------------------------
_COLORS = {
    "RESET":   "\033[0m",
    "RED":     "\033[91m",
    "GREEN":   "\033[92m",
    "YELLOW":  "\033[93m",
    "BLUE":    "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN":    "\033[96m",
    "BOLD":    "\033[1m",
}


class _ColorFormatter(logging.Formatter):
    """Formatter that adds colour to log-level names in the terminal."""

    LEVEL_COLORS = {
        logging.DEBUG:    _COLORS["CYAN"],
        logging.INFO:     _COLORS["GREEN"],
        logging.WARNING:  _COLORS["YELLOW"],
        logging.ERROR:    _COLORS["RED"],
        logging.CRITICAL: _COLORS["MAGENTA"],
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, _COLORS["RESET"])
        record.levelname = f"{color}{record.levelname:<8}{_COLORS['RESET']}"
        return super().format(record)


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------

_loggers: dict[str, logging.Logger] = {}


def get_logger(name: str = "mahoraga",
               level: int = logging.INFO) -> logging.Logger:
    """
    Return a named logger with coloured console output.
    Re-uses existing loggers to avoid duplicate handlers.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not logger.handlers:
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        fmt = _ColorFormatter(
            fmt="%(asctime)s │ %(levelname)s │ %(name)s │ %(message)s",
            datefmt="%H:%M:%S",
        )
        console.setFormatter(fmt)
        logger.addHandler(console)

    _loggers[name] = logger
    return logger


# ---------------------------------------------------------------------------
# Structured event helpers
# ---------------------------------------------------------------------------

class EvolutionLogger:
    """
    High-level helper to log GA events in a structured way.

    Usage
    -----
        evo_log = EvolutionLogger()
        evo_log.generation(gen=5, best_fit=0.012, avg_fit=0.034, mutation_rate=0.15)
        evo_log.drift_detected(drift_type="sudden", magnitude=2.3)
        evo_log.adaptation("PARTIAL_RESET", reason="sudden drift detected")
    """

    def __init__(self, name: str = "mahoraga.evolution"):
        self._log = get_logger(name)
        self._history: list[dict] = []

    # -- GA events ----------------------------------------------------------

    def generation(self, gen: int, best_fit: float, avg_fit: float,
                   mutation_rate: float = None, **extra):
        """Log a generation summary."""
        msg = (f"Gen {gen:>4d} │ best={best_fit:.6f} │ "
               f"avg={avg_fit:.6f}")
        if mutation_rate is not None:
            msg += f" │ mut_rate={mutation_rate:.4f}"
        self._log.info(msg)
        self._history.append({
            "event": "generation", "gen": gen,
            "best_fit": best_fit, "avg_fit": avg_fit,
            "mutation_rate": mutation_rate,
            "time": datetime.now().isoformat(),
            **extra,
        })

    def stagnation(self, gen: int, stagnant_gens: int):
        """Log stagnation detection."""
        self._log.warning(
            f"Gen {gen:>4d} │ ⚠ STAGNATION detected "
            f"({stagnant_gens} gens without improvement)"
        )
        self._history.append({
            "event": "stagnation", "gen": gen,
            "stagnant_gens": stagnant_gens,
            "time": datetime.now().isoformat(),
        })

    def fitness_switch(self, gen: int, old_metric: str, new_metric: str,
                       reason: str = ""):
        """Log a fitness function switch."""
        self._log.warning(
            f"Gen {gen:>4d} │ 🔄 FITNESS SWITCH: {old_metric} → {new_metric}"
            f"{' (' + reason + ')' if reason else ''}"
        )
        self._history.append({
            "event": "fitness_switch", "gen": gen,
            "old": old_metric, "new": new_metric, "reason": reason,
            "time": datetime.now().isoformat(),
        })

    # -- Drift events -------------------------------------------------------

    def drift_detected(self, drift_type: str, magnitude: float,
                       location: int = None):
        """Log a concept drift detection."""
        self._log.warning(
            f"🚨 DRIFT DETECTED │ type={drift_type} │ "
            f"magnitude={magnitude:.4f}"
            f"{' │ at=' + str(location) if location else ''}"
        )
        self._history.append({
            "event": "drift", "drift_type": drift_type,
            "magnitude": magnitude, "location": location,
            "time": datetime.now().isoformat(),
        })

    # -- Adaptation events --------------------------------------------------

    def adaptation(self, action: str, reason: str = "", **details):
        """Log an adaptation action taken by the policy engine."""
        self._log.info(
            f"🔧 ADAPT │ action={action}"
            f"{' │ reason=' + reason if reason else ''}"
        )
        self._history.append({
            "event": "adaptation", "action": action,
            "reason": reason, **details,
            "time": datetime.now().isoformat(),
        })

    # -- Memory events ------------------------------------------------------

    def memory_store(self, bank: str, description: str):
        """Log a memory bank store event."""
        self._log.debug(f"💾 MEMORY [{bank}] │ {description}")

    def memory_recall(self, bank: str, description: str):
        """Log a memory bank recall event."""
        self._log.debug(f"📖 RECALL [{bank}] │ {description}")

    # -- Access history -----------------------------------------------------

    def get_history(self) -> list[dict]:
        """Return full event history."""
        return list(self._history)

    def clear_history(self):
        """Clear event history."""
        self._history.clear()
