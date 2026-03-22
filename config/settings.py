import os

# ============================================================================
# PROJECT PATHS
# ============================================================================
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "experiments", "results")

# ============================================================================
# GENETIC ALGORITHM  –  Layer 3
# ============================================================================
POPULATION_SIZE = 60          # number of individuals per generation
MAX_GENERATIONS = 200         # hard stop for GA
TOURNAMENT_SIZE = 5           # tournament selection pool
ELITISM_COUNT = 3             # top-N preserved unchanged

# --- Default strategy DNA bounds (meta-evolution) -------------------------
MUTATION_RATE_BOUNDS = (0.01, 0.50)     # per-individual mutation rate
CROSSOVER_RATE_BOUNDS = (0.40, 0.95)    # per-individual crossover rate
MUTATION_STEP_BOUNDS = (0.001, 0.20)    # mutation step size

# --- Self-adaptation constants --------------------------------------------
STRATEGY_MUTATION_RATE = 0.10   # probability of mutating strategy DNA itself
TAU = 0.10                      # learning rate for strategy self-adaptation

# ============================================================================
# ADAPTIVE FITNESS  –  Part of Layer 3
# ============================================================================
STAGNATION_LIMIT = 15          # generations without improvement → react
FITNESS_SWITCH_COOLDOWN = 10   # min gens between fitness switches
DIVERSITY_THRESHOLD = 0.05     # below this → diversity is collapsed
OVERFITTING_RATIO = 1.5        # train_error * ratio < val_error → overfitting

# ============================================================================
# MEMORY SYSTEM  –  Part of Layer 3
# ============================================================================
FAILURE_MEMORY_SIZE = 100      # max entries in failure bank
SUCCESS_MEMORY_SIZE = 50       # max entries in success bank (elites)
PATTERN_MEMORY_SIZE = 30       # max DataProfile → Strategy mappings

# ============================================================================
# DRIFT DETECTION  –  Layer 2
# ============================================================================
DRIFT_CUSUM_THRESHOLD = 5.0    # CUSUM alarm threshold
DRIFT_CUSUM_DRIFT_RATE = 0.5   # allowable drift in CUSUM
DRIFT_MIN_WINDOW = 20          # minimum observations before drift can fire
DRIFT_COOLDOWN = 10            # min steps between consecutive drift alarms

# ============================================================================
# REFLEX SYSTEM  –  Layer 1
# ============================================================================
REFLEX_DECAY = 0.95            # exponential decay for old weights
REFLEX_ERROR_SENSITIVITY = 1.0 # scale factor in exp(-sensitivity * error)
REFLEX_MIN_WEIGHT = 0.01       # floor for any model's weight

# ============================================================================
# MODELS  –  Holt-Winters / ARIMA / LSTM parameter bounds
# ============================================================================
HW_ALPHA_BOUNDS = (0.01, 0.99)
HW_BETA_BOUNDS  = (0.001, 0.50)
HW_GAMMA_BOUNDS = (0.001, 0.99)
HW_SEASON_BOUNDS = (2, 52)     # seasonal period range

ARIMA_P_BOUNDS = (0, 5)
ARIMA_D_BOUNDS = (0, 2)
ARIMA_Q_BOUNDS = (0, 5)

LSTM_HIDDEN_BOUNDS = (4, 64)
LSTM_LR_BOUNDS = (0.0001, 0.1)
LSTM_EPOCH_BOUNDS = (10, 200)

# ============================================================================
# GENERAL
# ============================================================================
RANDOM_SEED = 42
DEFAULT_FORECAST_HORIZON = 12
DEFAULT_VAL_RATIO = 0.2

# ============================================================================
# UPSTASH REDIS  –  Serverless State Management
# ============================================================================
# ============================================================================
UPSTASH_REDIS_REST_URL = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL", "")
UPSTASH_REDIS_REST_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN", "")

# ============================================================================
# WORKER  –  Background Standalone Process
# ============================================================================
WORKER_INTERVAL_SECONDS = int(os.environ.get("WORKER_INTERVAL_SECONDS", "6"))

# ============================================================================
# SECURITY  –  Internal API Key Protection
# ============================================================================
# Shared secret between Frontend and Backend (Vercel)
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY", "")
