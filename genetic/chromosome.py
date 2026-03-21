import numpy as np
from config.settings import (
    HW_ALPHA_BOUNDS, HW_BETA_BOUNDS, HW_GAMMA_BOUNDS, HW_SEASON_BOUNDS,
    ARIMA_P_BOUNDS, ARIMA_D_BOUNDS, ARIMA_Q_BOUNDS,
    LSTM_HIDDEN_BOUNDS, LSTM_LR_BOUNDS, LSTM_EPOCH_BOUNDS,
)


# ── Gene definitions ────────────────────────────────────────────────────

GENE_DEFS = {
    # Solution DNA — Holt-Winters
    "hw_alpha":         {"min": HW_ALPHA_BOUNDS[0],  "max": HW_ALPHA_BOUNDS[1],  "type": "float"},
    "hw_beta":          {"min": HW_BETA_BOUNDS[0],   "max": HW_BETA_BOUNDS[1],   "type": "float"},
    "hw_gamma":         {"min": HW_GAMMA_BOUNDS[0],  "max": HW_GAMMA_BOUNDS[1],  "type": "float"},
    "hw_season_length": {"min": HW_SEASON_BOUNDS[0], "max": HW_SEASON_BOUNDS[1], "type": "int"},
    "hw_mode":          {"options": ["additive", "multiplicative"],               "type": "categorical"},

    # Solution DNA — ARIMA
    "arima_p": {"min": ARIMA_P_BOUNDS[0], "max": ARIMA_P_BOUNDS[1], "type": "int"},
    "arima_d": {"min": ARIMA_D_BOUNDS[0], "max": ARIMA_D_BOUNDS[1], "type": "int"},
    "arima_q": {"min": ARIMA_Q_BOUNDS[0], "max": ARIMA_Q_BOUNDS[1], "type": "int"},

    # Solution DNA — LSTM
    "lstm_hidden":  {"min": LSTM_HIDDEN_BOUNDS[0], "max": LSTM_HIDDEN_BOUNDS[1], "type": "int"},
    "lstm_lr":      {"min": LSTM_LR_BOUNDS[0],     "max": LSTM_LR_BOUNDS[1],     "type": "float"},
    "lstm_epochs":  {"min": LSTM_EPOCH_BOUNDS[0],  "max": LSTM_EPOCH_BOUNDS[1],  "type": "int"},
}


def random_gene(gene_name: str) -> float:
    """Generate a random value for a named gene."""
    gdef = GENE_DEFS[gene_name]
    if gdef["type"] == "float":
        return np.random.uniform(gdef["min"], gdef["max"])
    elif gdef["type"] == "int":
        return float(np.random.randint(gdef["min"], gdef["max"] + 1))
    elif gdef["type"] == "categorical":
        return float(np.random.randint(0, len(gdef["options"])))
    return 0.0


def decode_gene(gene_name: str, value: float):
    """Convert a raw gene float to its proper typed value."""
    gdef = GENE_DEFS[gene_name]
    if gdef["type"] == "int":
        return int(np.clip(round(value), gdef["min"], gdef["max"]))
    elif gdef["type"] == "float":
        return float(np.clip(value, gdef["min"], gdef["max"]))
    elif gdef["type"] == "categorical":
        idx = int(np.clip(round(value), 0, len(gdef["options"]) - 1))
        return gdef["options"][idx]
    return value


def clamp_gene(gene_name: str, value: float) -> float:
    """Clamp a gene value to its valid range."""
    gdef = GENE_DEFS[gene_name]
    if gdef["type"] in ("float", "int"):
        return float(np.clip(value, gdef["min"], gdef["max"]))
    elif gdef["type"] == "categorical":
        return float(np.clip(round(value), 0, len(gdef["options"]) - 1))
    return value


def encode_params(model_name: str, params: dict) -> dict[str, float]:
    """Convert model params dict → gene dict (float-encoded)."""
    genes = {}
    if model_name == "holt_winters":
        genes["hw_alpha"] = params.get("alpha", 0.3)
        genes["hw_beta"] = params.get("beta", 0.1)
        genes["hw_gamma"] = params.get("gamma", 0.1)
        genes["hw_season_length"] = float(params.get("season_length", 12))
        mode = params.get("mode", "additive")
        genes["hw_mode"] = 0.0 if mode == "additive" else 1.0
    elif model_name == "arima":
        genes["arima_p"] = float(params.get("p", 2))
        genes["arima_d"] = float(params.get("d", 1))
        genes["arima_q"] = float(params.get("q", 1))
    elif model_name == "lstm":
        genes["lstm_hidden"] = float(params.get("hidden_size", 16))
        genes["lstm_lr"] = params.get("learning_rate", 0.01)
        genes["lstm_epochs"] = float(params.get("epochs", 50))
    return genes


def decode_params(model_name: str, genes: dict[str, float]) -> dict:
    """Convert gene dict → model params dict (typed)."""
    params = {}
    if model_name == "holt_winters":
        params["alpha"] = decode_gene("hw_alpha", genes.get("hw_alpha", 0.3))
        params["beta"] = decode_gene("hw_beta", genes.get("hw_beta", 0.1))
        params["gamma"] = decode_gene("hw_gamma", genes.get("hw_gamma", 0.1))
        params["season_length"] = decode_gene("hw_season_length", genes.get("hw_season_length", 12))
        params["mode"] = decode_gene("hw_mode", genes.get("hw_mode", 0.0))
    elif model_name == "arima":
        params["p"] = decode_gene("arima_p", genes.get("arima_p", 2))
        params["d"] = decode_gene("arima_d", genes.get("arima_d", 1))
        params["q"] = decode_gene("arima_q", genes.get("arima_q", 1))
    elif model_name == "lstm":
        params["hidden_size"] = decode_gene("lstm_hidden", genes.get("lstm_hidden", 16))
        params["learning_rate"] = decode_gene("lstm_lr", genes.get("lstm_lr", 0.01))
        params["epochs"] = decode_gene("lstm_epochs", genes.get("lstm_epochs", 50))
    return params
