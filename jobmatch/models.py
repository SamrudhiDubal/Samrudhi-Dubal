"""Load the trained classifiers and use them for prediction.

`ResumeClassifier` wraps the two trained models written by `train.py`:

- the machine-learning model: TF-IDF + calibrated Linear SVM (scikit-learn)
- the deep-learning model: word embeddings + 1D convolutional network (Keras)

The deployed strategy ("ml", "dl" or "ensemble") is read from
reports/metrics.json, where train.py records the option with the best
validation score. If TensorFlow is not installed, the classifier falls back
to the machine-learning model alone.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache

import numpy as np

from . import config
from .text import prepare

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")


class ModelsNotTrainedError(FileNotFoundError):
    pass


class ResumeClassifier:
    def __init__(self):
        if not config.ML_MODEL_PATH.exists() or not config.LABELS_PATH.exists():
            raise ModelsNotTrainedError("Trained models not found. Run `python train.py` first.")
        import joblib

        self.labels: list[str] = json.loads(config.LABELS_PATH.read_text())
        self.ml_model = joblib.load(config.ML_MODEL_PATH)
        metrics = json.loads(config.METRICS_PATH.read_text()) if config.METRICS_PATH.exists() else {}
        self.metrics = metrics
        self.strategy = metrics.get("deployment", {}).get("strategy", "ml")

        self.dl_model = self.vectorizer = self.embedder = None
        self.dl_available = False
        # Loaded even for the "ml" strategy: its embeddings power semantic matching.
        self._load_deep_model()
        if not self.dl_available:
            self.strategy = "ml"

    def _load_deep_model(self):
        try:
            import keras
            from keras import layers
        except ImportError:
            return
        if not config.DL_MODEL_PATH.exists():
            return
        self.dl_model = keras.models.load_model(config.DL_MODEL_PATH, compile=False)
        vocab = json.loads(config.DL_VOCAB_PATH.read_text())
        # Index 0 (padding) and 1 ([UNK]) are re-added by TextVectorization.
        self.vectorizer = layers.TextVectorization(
            max_tokens=config.DL_MAX_TOKENS, output_sequence_length=config.DL_SEQUENCE_LENGTH,
            vocabulary=vocab[2:])
        self.embedder = keras.Model(self.dl_model.inputs, self.dl_model.get_layer("resume_vector").output)
        self.dl_available = True

    # ---------------------------------------------------------------- prediction

    def _sequences(self, prepared: list[str]):
        return self.vectorizer(np.array(prepared, dtype=object)).numpy()

    def ml_proba(self, texts: list[str]) -> np.ndarray:
        return self.ml_model.predict_proba([prepare(t) for t in texts])

    def dl_proba(self, texts: list[str]) -> np.ndarray:
        if not self.dl_available:
            raise RuntimeError("Deep-learning model is not available (TensorFlow not installed)")
        return self.dl_model.predict(self._sequences([prepare(t) for t in texts]), verbose=0)

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        """Category probabilities using the deployed strategy, shape (n, n_labels)."""
        if self.strategy == "ml":
            return self.ml_proba(texts)
        if self.strategy == "dl":
            return self.dl_proba(texts)
        return (self.ml_proba(texts) + self.dl_proba(texts)) / 2

    def predict(self, text: str, top: int = 3) -> dict:
        """Prediction for one resume, with each model's view for transparency."""
        ml = self.ml_proba([text])[0]
        dl = self.dl_proba([text])[0] if self.dl_available else None
        final = {"ml": ml, "dl": dl, "ensemble": (ml + dl) / 2 if dl is not None else ml}[self.strategy]
        order = np.argsort(final)[::-1]
        return {
            "category": self.labels[order[0]],
            "confidence": float(final[order[0]]),
            "top": [(self.labels[i], float(final[i])) for i in order[:top]],
            "probabilities": {self.labels[i]: float(final[i]) for i in range(len(self.labels))},
            "ml_category": self.labels[int(ml.argmax())],
            "dl_category": self.labels[int(dl.argmax())] if dl is not None else None,
            "strategy": self.strategy,
        }

    def embed(self, texts: list[str]) -> np.ndarray:
        """Dense resume vectors from the CNN's penultimate layer (L2-normalised)."""
        if not self.dl_available:
            raise RuntimeError("Deep-learning model is not available (TensorFlow not installed)")
        vectors = self.embedder.predict(self._sequences([prepare(t) for t in texts]), verbose=0)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.where(norms == 0, 1, norms)

    def tfidf(self, texts: list[str]):
        """TF-IDF vectors from the trained ML pipeline (already L2-normalised)."""
        return self.ml_model.named_steps["tfidf"].transform([prepare(t) for t in texts])


@lru_cache(maxsize=1)
def get_classifier() -> ResumeClassifier:
    return ResumeClassifier()
