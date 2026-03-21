"""
Experiment: Baseline GA vs Adaptive Mahoraga GA
Tests on regime_change synthetic data to demonstrate adaptation.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from data.loaders import generate_synthetic
from pipeline.orchestrator import Orchestrator
from evaluation.metrics import mse, rmse, mae
from utils.logger import get_logger


def run_experiment():
    log = get_logger("experiment")

    # Generate regime change data (the hardest test)
    log.info("Generating regime_change data (n=200)")
    data = generate_synthetic("regime_change", length=200, seed=42)

    # Run adaptive engine
    log.info("Running Adaptive Forecasting Engine...")
    engine = Orchestrator(
        ga_generations=50,
        ga_population=30,
        forecast_horizon=12,
    )
    result = engine.run(data)

    # Report
    print("\n" + "=" * 50)
    print("  EXPERIMENT: Regime Change Adaptation")
    print("=" * 50)
    print(f"Profile: {result['profile'].summary()}")
    print(f"Val MSE:  {result['val_mse']:.6f}")
    print(f"Val RMSE: {np.sqrt(result['val_mse']):.6f}")
    print(f"Drift events: {len(result['drift_events'])}")
    print(f"Adaptations:  {len(result['adaptation_history'])}")
    print(f"Confidence:   {result['confidence']:.2%}")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    run_experiment()
