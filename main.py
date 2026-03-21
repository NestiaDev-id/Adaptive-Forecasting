import argparse
import sys
import os
import numpy as np

# ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.loaders import generate_synthetic, load_csv
from pipeline.orchestrator import Orchestrator
from utils.logger import get_logger
from evaluation.metrics import mse, mae, rmse


def main():
    parser = argparse.ArgumentParser(
        description="Adaptive Forecasting Engine — Self-Adaptive GA System",
    )
    parser.add_argument("--data", type=str, default=None,
                        help="Path to CSV file (will use first numeric column)")
    parser.add_argument("--demo", type=str, default="seasonal",
                        choices=["stable", "trending", "seasonal",
                                 "chaotic", "regime_change"],
                        help="Run demo with synthetic data")
    parser.add_argument("--horizon", type=int, default=12,
                        help="Forecast horizon (steps ahead)")
    parser.add_argument("--generations", type=int, default=80,
                        help="GA max generations")
    parser.add_argument("--population", type=int, default=40,
                        help="GA population size")
    parser.add_argument("--length", type=int, default=200,
                        help="Synthetic data length (demo mode)")
    parser.add_argument("--noise", type=float, default=0.1,
                        help="Noise level (demo mode)")
    parser.add_argument("--plot", action="store_true",
                        help="Show matplotlib plots")
    args = parser.parse_args()

    log = get_logger("main")

    # ── Load data ────────────────────────────────────────────────────
    if args.data:
        log.info(f"Loading data from {args.data}")
        data = load_csv(args.data)
    else:
        log.info(f"Generating synthetic data: {args.demo} (n={args.length})")
        data = generate_synthetic(
            args.demo, length=args.length,
            noise_level=args.noise, seed=42)

    log.info(f"Data shape: {data.shape}, range: [{data.min():.2f}, {data.max():.2f}]")

    # ── Run engine ───────────────────────────────────────────────────
    engine = Orchestrator(
        ga_generations=args.generations,
        ga_population=args.population,
        forecast_horizon=args.horizon,
    )

    result = engine.run(data)

    # ── Report ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ADAPTIVE FORECASTING ENGINE — RESULTS")
    print("=" * 60)

    print(f"\n📊 Data Profile:")
    print(f"   {result['profile'].summary()}")
    print(f"   Length: {result['profile'].data_length}")

    print(f"\n🧬 Best Individual:")
    best = result["best_individual"]
    print(f"   {best}")
    print(f"   Strategy DNA: mut={best.mutation_rate:.4f}, "
          f"cx={best.crossover_rate:.4f}, step={best.mutation_step:.4f}")
    weights = best.get_normalised_weights()
    print(f"   Model weights: " + ", ".join(
        f"{k}={v:.1%}" for k, v in sorted(weights.items(), key=lambda x: -x[1])))

    print(f"\n📈 Validation Performance:")
    print(f"   MSE:  {result['val_mse']:.6f}")
    print(f"   RMSE: {np.sqrt(result['val_mse']):.6f}")

    print(f"\n🔮 Forecast ({args.horizon} steps ahead):")
    for i, (f, lo, hi) in enumerate(zip(
            result["forecast"], result["forecast_lower"], result["forecast_upper"])):
        print(f"   t+{i + 1:2d}: {f:10.4f}  [{lo:.4f}, {hi:.4f}]")
    print(f"   Confidence: {result['confidence']:.2%}")

    print(f"\n🚨 Drift Events: {len(result['drift_events'])}")
    for de in result["drift_events"]:
        print(f"   [{de.method}] magnitude={de.magnitude:.2f} at step {de.location}")

    print(f"\n🔧 Adaptation Actions: {len(result['adaptation_history'])}")
    for aa in result["adaptation_history"]:
        print(f"   {aa.action} (conf={aa.confidence:.2f}) — {aa.reason}")

    print(f"\n⚖️ Final Weights:")
    for name, w in sorted(result["final_weights"].items(), key=lambda x: -x[1]):
        print(f"   {name:15s}: {w:.4f}")

    print(f"\n{'=' * 60}\n")

    # ── Optional plots ───────────────────────────────────────────────
    if args.plot:
        _plot_results(data, result, args.horizon)


def _plot_results(data, result, horizon):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed — skipping plots")
        return

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Actual vs Predicted (validation)
    ax = axes[0, 0]
    val = result["val_actual"]
    pred = result["val_predictions"]
    ax.plot(val, label="Actual", color="#2196F3", linewidth=2)
    ax.plot(pred, label="Predicted", color="#FF5722", linewidth=2, linestyle="--")
    ax.set_title("Validation: Actual vs Predicted")
    ax.legend()
    ax.grid(alpha=0.3)

    # 2. Forecast with confidence interval
    ax = axes[0, 1]
    n_hist = min(50, len(data))
    ax.plot(range(n_hist), data[-n_hist:], label="Historical",
            color="#2196F3", linewidth=2)
    fc_x = range(n_hist, n_hist + horizon)
    ax.plot(fc_x, result["forecast"], label="Forecast",
            color="#FF5722", linewidth=2)
    ax.fill_between(fc_x, result["forecast_lower"], result["forecast_upper"],
                     alpha=0.2, color="#FF5722", label="95% CI")
    ax.set_title("Forecast with Confidence Interval")
    ax.legend()
    ax.grid(alpha=0.3)

    # 3. Fitness evolution
    ax = axes[1, 0]
    history = result["fitness_history"]
    if history:
        gens = [h["gen"] for h in history]
        bests = [h["best"] for h in history]
        avgs = [h["avg"] for h in history]
        ax.plot(gens, bests, label="Best", color="#4CAF50", linewidth=2)
        ax.plot(gens, avgs, label="Average", color="#9E9E9E", linewidth=1)
        ax.set_title("Fitness Evolution")
        ax.set_xlabel("Generation")
        ax.legend()
        ax.grid(alpha=0.3)

    # 4. Mutation rate evolution
    ax = axes[1, 1]
    if history:
        muts = [h["avg_mutation"] for h in history]
        ax.plot(gens, muts, color="#9C27B0", linewidth=2)
        ax.set_title("Average Mutation Rate (Meta-Evolution)")
        ax.set_xlabel("Generation")
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig("forecast_results.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Plot saved → forecast_results.png")


if __name__ == "__main__":
    main()
