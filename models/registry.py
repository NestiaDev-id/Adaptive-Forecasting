from models.base_model import BaseModel


class ModelRegistry:
    """
    Central registry for all available forecasting models.
    Makes the system scalable — add new models without touching the GA.
    """

    def __init__(self):
        self._registry: dict[str, type] = {}

    def register(self, name: str, model_class: type) -> None:
        if not issubclass(model_class, BaseModel):
            raise TypeError(f"{model_class} must be a subclass of BaseModel")
        self._registry[name] = model_class

    def get(self, name: str, **kwargs) -> BaseModel:
        if name not in self._registry:
            raise KeyError(
                f"Model '{name}' not registered. "
                f"Available: {list(self._registry.keys())}"
            )
        return self._registry[name](**kwargs)

    def list_models(self) -> list[str]:
        return list(self._registry.keys())

    def create_all(self) -> dict[str, BaseModel]:
        return {name: cls() for name, cls in self._registry.items()}

    def __contains__(self, name: str) -> bool:
        return name in self._registry

    def __len__(self) -> int:
        return len(self._registry)


# ── Default registry with built-in models ────────────────────────────────

def build_default_registry() -> ModelRegistry:
    """Default registry: HW + ARIMA (fast enough for GA evaluation)."""
    from models.holt_winters import HoltWinters
    from models.arima import ARIMA

    registry = ModelRegistry()
    registry.register("holt_winters", HoltWinters)
    registry.register("arima", ARIMA)
    return registry


def build_full_registry() -> ModelRegistry:
    """Full registry including LSTM (slower, use for final training only)."""
    from models.holt_winters import HoltWinters
    from models.arima import ARIMA
    from models.lstm import SimpleLSTM

    registry = ModelRegistry()
    registry.register("holt_winters", HoltWinters)
    registry.register("arima", ARIMA)
    registry.register("lstm", SimpleLSTM)
    return registry
