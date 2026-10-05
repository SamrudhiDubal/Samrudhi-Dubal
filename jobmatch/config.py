"""Project-wide paths and settings."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

RESUME_DATASET = DATA_DIR / "resumes.csv"
JOBS_SEED_FILE = DATA_DIR / "jobs.json"
DB_PATH = Path(os.environ.get("JOBMATCH_DB", DATA_DIR / "jobmatch.db"))

# Trained artifacts written by train.py and loaded by the app.
ML_MODEL_PATH = MODELS_DIR / "ml_model.joblib"
DL_MODEL_PATH = MODELS_DIR / "dl_model.keras"
DL_VOCAB_PATH = MODELS_DIR / "dl_vocab.json"
LABELS_PATH = MODELS_DIR / "labels.json"
METRICS_PATH = REPORTS_DIR / "metrics.json"

RANDOM_SEED = 42
TEST_SIZE = 0.2

# Deep learning text settings (must match between training and inference).
DL_MAX_TOKENS = 20000
DL_SEQUENCE_LENGTH = 600
