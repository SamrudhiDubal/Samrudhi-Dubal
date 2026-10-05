"""Train and evaluate every resume-classification model, then save the best.

    python train.py            # full run (about 10-15 minutes on a laptop CPU)
    python train.py --quick    # 1 seed per deep model, skips BiLSTM (about 3 minutes)

Evaluation protocol (no information from the test set is used to choose models):

    all resumes (deduplicated)
    ├── test  20%  -> touched once, at the end, for the reported numbers
    └── train 80%
        ├── 5-fold stratified cross-validation   -> compares the ML models
        └── fit 85% / validation 15%             -> early stopping for deep models,
                                                    and the choice of deployed model

Outputs: models/ (trained artifacts), reports/metrics.json, reports/figures/*.png
"""

from __future__ import annotations

import argparse
import json
import os
import time

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support, top_k_accuracy_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from jobmatch import config
from jobmatch.text import prepare

# Chart colours (validated categorical slots 1 and 2): ML = blue, DL = orange.
ML_COLOR, DL_COLOR, ENS_COLOR = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


# ---------------------------------------------------------------- data

def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(config.RESUME_DATASET)
    before = len(df)
    df = df.drop_duplicates("Resume_str").reset_index(drop=True)
    print(f"Loaded {before} resumes, {before - len(df)} duplicates removed, {df.Category.nunique()} categories")
    df["text"] = df["Resume_str"].map(prepare)
    return df


# ---------------------------------------------------------------- models

def tfidf(max_features=50000):
    return TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.9, sublinear_tf=True,
                           stop_words="english", max_features=max_features)


def ml_models() -> dict[str, Pipeline]:
    return {
        "Logistic Regression": Pipeline([("tfidf", tfidf()), ("clf", LogisticRegression(C=10, max_iter=3000))]),
        "Linear SVM": Pipeline([("tfidf", tfidf()), ("clf", CalibratedClassifierCV(LinearSVC(C=0.5), cv=3))]),
        "Naive Bayes": Pipeline([("tfidf", tfidf()), ("clf", ComplementNB(alpha=0.3))]),
        "Random Forest": Pipeline([("tfidf", tfidf()), ("clf", RandomForestClassifier(
            n_estimators=400, n_jobs=-1, random_state=config.RANDOM_SEED))]),
    }


def build_dl_model(arch: str, n_classes: int, input_dim: int | None = None):
    import keras
    from keras import layers

    if arch == "MLP":
        model = keras.Sequential([
            layers.Input((input_dim,)),
            layers.Dropout(0.3),
            layers.Dense(256, activation="relu"),
            layers.Dropout(0.5),
            layers.Dense(128, activation="relu", name="resume_vector"),
            layers.Dropout(0.3),
            layers.Dense(n_classes, activation="softmax"),
        ], name="mlp")
    else:
        inp = layers.Input((config.DL_SEQUENCE_LENGTH,), dtype="int32")
        x = layers.Embedding(config.DL_MAX_TOKENS, 128, mask_zero=(arch == "BiLSTM"))(inp)
        if arch == "1D-CNN":
            x = layers.Conv1D(128, 5, activation="relu")(x)
            x = layers.GlobalMaxPooling1D()(x)
        else:
            x = layers.Bidirectional(layers.LSTM(64))(x)
        x = layers.Dropout(0.5)(x)
        x = layers.Dense(64, activation="relu", name="resume_vector")(x)
        out = layers.Dense(n_classes, activation="softmax")(x)
        model = keras.Model(inp, out, name=arch.lower().replace("-", ""))
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


# ---------------------------------------------------------------- metrics

def scores(y_true, proba, labels) -> dict:
    pred = proba.argmax(1)
    return {
        "accuracy": round(float(accuracy_score(y_true, pred)), 4),
        "macro_f1": round(float(f1_score(y_true, pred, average="macro")), 4),
        "weighted_f1": round(float(f1_score(y_true, pred, average="weighted")), 4),
        "top3_accuracy": round(float(top_k_accuracy_score(y_true, proba, k=3, labels=range(len(labels)))), 4),
    }


def mean_std(runs: list[dict]) -> dict:
    return {k: {"mean": round(float(np.mean([r[k] for r in runs])), 4),
                "std": round(float(np.std([r[k] for r in runs])), 4)} for k in runs[0]}


# ---------------------------------------------------------------- figures

def pretty_label(label: str) -> str:
    """"BUSINESS-DEVELOPMENT" -> "Business Development", keeping HR and BPO upper-case."""
    return " ".join(w if w in ("HR", "BPO") else w.title() for w in label.split("-"))


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def plot_class_distribution(df):
    counts = df.Category.value_counts().sort_values()
    counts.index = [pretty_label(c) for c in counts.index]
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(counts.index, counts.values, color=ML_COLOR, height=0.7)
    for y, v in enumerate(counts.values):
        ax.text(v + 1, y, str(v), va="center", fontsize=8, color=MUTED)
    ax.set_title("Resumes per category", loc="left", color=INK, fontsize=12)
    ax.set_xlabel("Number of resumes", color=MUTED)
    _style(ax)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "class_distribution.png", dpi=150)
    plt.close(fig)


def plot_length_distribution(df):
    words = df.Resume_str.str.split().str.len()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(words, bins=50, color=ML_COLOR, edgecolor="white", linewidth=0.5)
    ax.axvline(words.median(), color=INK, linewidth=1, linestyle="--")
    ax.text(words.median() * 1.03, ax.get_ylim()[1] * 0.9, f"median {int(words.median())} words", color=INK, fontsize=9)
    ax.set_title("Resume length", loc="left", color=INK, fontsize=12)
    ax.set_xlabel("Words per resume", color=MUTED)
    ax.set_ylabel("Resumes", color=MUTED)
    _style(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "resume_length.png", dpi=150)
    plt.close(fig)


def plot_model_comparison(results: dict):
    names = list(results)
    # Deep models report mean +/- std over seeds; ML models a single number.
    value = lambda v: v["mean"] if isinstance(v, dict) else v  # noqa: E731
    acc = [value(results[n]["test"]["accuracy"]) for n in names]
    f1 = [value(results[n]["test"]["macro_f1"]) for n in names]
    colors = [{"ML": ML_COLOR, "DL": DL_COLOR, "Ensemble": ENS_COLOR}[results[n]["family"]] for n in names]
    order = np.argsort(acc)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    for ax, values, title in [(axes[0], acc, "Test accuracy"), (axes[1], f1, "Test macro-F1")]:
        ax.barh([names[i] for i in order], [values[i] for i in order], color=[colors[i] for i in order], height=0.65)
        for y, i in enumerate(order):
            ax.text(values[i] + 0.008, y, f"{values[i]:.1%}", va="center", fontsize=8, color=INK)
        ax.set_xlim(0, 1)
        ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.set_title(title, loc="left", color=INK, fontsize=11)
        _style(ax)
    handles = [matplotlib.patches.Patch(color=c, label=l) for l, c in
               [("Machine learning", ML_COLOR), ("Deep learning", DL_COLOR), ("Ensemble", ENS_COLOR)]]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(config.FIGURES_DIR / "model_comparison.png", dpi=150)
    plt.close(fig)


def plot_confusion(y_true, y_pred, labels, title):
    cm = confusion_matrix(y_true, y_pred, labels=range(len(labels)), normalize="true")
    fig, ax = plt.subplots(figsize=(10, 9))
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
    short = [pretty_label(l) for l in labels]
    ax.set_xticks(range(len(labels)), short, rotation=90, fontsize=8)
    ax.set_yticks(range(len(labels)), short, fontsize=8)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if cm[i, j] >= 0.1:
                ax.text(j, i, f"{cm[i, j]:.0%}"[:-1], ha="center", va="center", fontsize=6,
                        color="white" if cm[i, j] > 0.55 else INK)
    ax.set_xlabel("Predicted category", color=MUTED)
    ax.set_ylabel("True category", color=MUTED)
    ax.set_title(title + " (row-normalised, % of true category)", loc="left", color=INK, fontsize=11)
    fig.colorbar(im, ax=ax, fraction=0.04, format=matplotlib.ticker.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "confusion_matrix.png", dpi=150)
    plt.close(fig)


def plot_per_class_f1(y_true, y_pred, labels):
    _p, _r, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=range(len(labels)), zero_division=0)
    order = np.argsort(f1)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh([pretty_label(labels[i]) for i in order], f1[order], color=DL_COLOR, height=0.7)
    for y, i in enumerate(order):
        ax.text(f1[i] + 0.01, y, f"{f1[i]:.2f} (n={support[i]})", va="center", fontsize=7, color=MUTED)
    ax.set_xlim(0, 1.15)
    ax.set_title("F1 score per category, deployed model, test set", loc="left", color=INK, fontsize=11)
    _style(ax)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "per_class_f1.png", dpi=150)
    plt.close(fig)


def plot_training_curves(history: dict, arch: str):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    epochs = range(1, len(history["loss"]) + 1)
    for ax, key, title in [(axes[0], "loss", "Loss"), (axes[1], "accuracy", "Accuracy")]:
        ax.plot(epochs, history[key], color=ML_COLOR, linewidth=2, label="Training")
        ax.plot(epochs, history["val_" + key], color=DL_COLOR, linewidth=2, label="Validation")
        ax.set_title(f"{arch}: {title}", loc="left", color=INK, fontsize=11)
        ax.set_xlabel("Epoch", color=MUTED)
        _style(ax)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
    axes[1].legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "training_curves.png", dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------- main

def main(quick: bool = False):
    import keras
    from keras import layers

    t0 = time.time()
    for d in (config.MODELS_DIR, config.FIGURES_DIR):
        d.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    labels = sorted(df.Category.unique())
    y = df.Category.map({l: i for i, l in enumerate(labels)}).to_numpy()
    idx_train, idx_test = train_test_split(np.arange(len(df)), test_size=config.TEST_SIZE, stratify=y,
                                           random_state=config.RANDOM_SEED)
    idx_fit, idx_val = train_test_split(idx_train, test_size=0.15, stratify=y[idx_train],
                                        random_state=config.RANDOM_SEED)
    X = df.text.to_numpy()
    print(f"Split: train {len(idx_train)} (fit {len(idx_fit)} / validation {len(idx_val)}), test {len(idx_test)}")

    plot_class_distribution(df)
    plot_length_distribution(df)

    results, val_proba, test_proba, fitted_ml = {}, {}, {}, {}

    # ---- classical machine learning
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=config.RANDOM_SEED)
    for name, pipe in ml_models().items():
        t = time.time()
        cvres = cross_validate(pipe, X[idx_train], y[idx_train], cv=cv, scoring=["accuracy", "f1_macro"], n_jobs=1)
        val_model = clone(pipe).fit(X[idx_fit], y[idx_fit])
        val_proba[name] = val_model.predict_proba(X[idx_val])
        final = clone(pipe).fit(X[idx_train], y[idx_train])
        fitted_ml[name] = final
        test_proba[name] = final.predict_proba(X[idx_test])
        results[name] = {
            "family": "ML",
            "cv": {"accuracy": round(float(cvres["test_accuracy"].mean()), 4),
                   "accuracy_std": round(float(cvres["test_accuracy"].std()), 4),
                   "macro_f1": round(float(cvres["test_f1_macro"].mean()), 4)},
            "validation": scores(y[idx_val], val_proba[name], labels),
            "test": scores(y[idx_test], test_proba[name], labels),
        }
        print(f"[ML] {name:20s} CV acc {results[name]['cv']['accuracy']:.3f}  "
              f"test acc {results[name]['test']['accuracy']:.3f}  ({time.time() - t:.0f}s)", flush=True)

    best_ml = max((n for n in results), key=lambda n: results[n]["cv"]["macro_f1"])
    print(f"Best ML model by cross-validated macro-F1: {best_ml}")

    # ---- deep learning
    vectorizer = layers.TextVectorization(max_tokens=config.DL_MAX_TOKENS,
                                          output_sequence_length=config.DL_SEQUENCE_LENGTH)
    vectorizer.adapt(X[idx_fit])
    seq = {k: vectorizer(X[v]).numpy() for k, v in [("fit", idx_fit), ("val", idx_val), ("test", idx_test)]}
    mlp_tfidf = tfidf(max_features=20000).fit(X[idx_fit])
    dense = {k: mlp_tfidf.transform(X[v]).toarray().astype("float32")
             for k, v in [("fit", idx_fit), ("val", idx_val), ("test", idx_test)]}

    archs = ["MLP", "1D-CNN"] + ([] if quick else ["BiLSTM"])
    seeds = [42] if quick else [42, 7, 2024]
    best_dl = {"val_f1": -1}
    for arch in archs:
        inputs = dense if arch == "MLP" else seq
        runs_val, runs_test, probs_val, probs_test = [], [], [], []
        for seed in seeds:
            keras.utils.set_random_seed(seed)
            model = build_dl_model(arch, len(labels), input_dim=dense["fit"].shape[1])
            t = time.time()
            hist = model.fit(inputs["fit"], y[idx_fit], validation_data=(inputs["val"], y[idx_val]),
                             epochs=40, batch_size=32, verbose=0,
                             callbacks=[keras.callbacks.EarlyStopping(patience=4, restore_best_weights=True)])
            pv = model.predict(inputs["val"], verbose=0)
            pt = model.predict(inputs["test"], verbose=0)
            sv, st = scores(y[idx_val], pv, labels), scores(y[idx_test], pt, labels)
            runs_val.append(sv)
            runs_test.append(st)
            probs_val.append(pv)
            probs_test.append(pt)
            print(f"[DL] {arch:8s} seed {seed:5d}  epochs {len(hist.history['loss']):2d}  val acc {sv['accuracy']:.3f}  "
                  f"test acc {st['accuracy']:.3f}  ({time.time() - t:.0f}s)", flush=True)
            if arch != "MLP" and sv["macro_f1"] > best_dl["val_f1"]:
                best_dl = {"arch": arch, "seed": seed, "val_f1": sv["macro_f1"], "model": model,
                           "history": hist.history, "val_proba": pv, "test_proba": pt}
        results[arch] = {"family": "DL", "seeds": seeds,
                         "validation": mean_std(runs_val), "test": mean_std(runs_test)}
        val_proba[arch] = np.mean(probs_val, axis=0)
        test_proba[arch] = np.mean(probs_test, axis=0)

    # ---- ensemble: average the best ML model and the selected deep model
    ens_val = (val_proba[best_ml] + best_dl["val_proba"]) / 2
    ens_test = (test_proba[best_ml] + best_dl["test_proba"]) / 2
    ens_name = f"Ensemble ({best_ml} + {best_dl['arch']})"
    results[ens_name] = {"family": "Ensemble", "validation": scores(y[idx_val], ens_val, labels),
                         "test": scores(y[idx_test], ens_test, labels)}

    # ---- choose what the app deploys, using validation macro-F1 only
    candidates = {
        "ml": results[best_ml]["validation"]["macro_f1"],
        "dl": best_dl["val_f1"],
        "ensemble": results[ens_name]["validation"]["macro_f1"],
    }
    strategy = max(candidates, key=candidates.get)
    deployed_test = {"ml": test_proba[best_ml], "dl": best_dl["test_proba"], "ensemble": ens_test}[strategy]
    print(f"Validation macro-F1: {candidates} -> deploying '{strategy}'")

    # ---- save artifacts
    joblib.dump(fitted_ml[best_ml], config.ML_MODEL_PATH, compress=3)
    best_dl["model"].save(config.DL_MODEL_PATH)
    # Re-save without the optimizer state (only needed to keep training): 32 MB -> 11 MB.
    keras.models.load_model(config.DL_MODEL_PATH, compile=False).save(config.DL_MODEL_PATH)
    config.DL_VOCAB_PATH.write_text(json.dumps(vectorizer.get_vocabulary()))
    config.LABELS_PATH.write_text(json.dumps(labels, indent=1))

    deployed_name = {"ml": best_ml, "dl": best_dl["arch"], "ensemble": ens_name}[strategy]
    metrics = {
        "dataset": {"resumes": int(len(df)), "categories": len(labels), "train": int(len(idx_train)),
                    "test": int(len(idx_test)), "duplicates_removed": int(pd.read_csv(config.RESUME_DATASET).duplicated("Resume_str").sum())},
        "labels": labels,
        "results": results,
        "best_ml": best_ml,
        "best_dl": {"arch": best_dl["arch"], "seed": best_dl["seed"]},
        "deployment": {"strategy": strategy, "model": deployed_name, "test": scores(y[idx_test], deployed_test, labels),
                       "validation_macro_f1": candidates},
        "test_rows": [int(i) for i in idx_test],
        "validation_rows": [int(i) for i in idx_val],
        "training_seconds": round(time.time() - t0),
    }
    config.METRICS_PATH.write_text(json.dumps(metrics, indent=1))

    plot_model_comparison({n: r for n, r in results.items()})
    plot_confusion(y[idx_test], deployed_test.argmax(1), labels, f"Confusion matrix: {deployed_name}")
    plot_per_class_f1(y[idx_test], deployed_test.argmax(1), labels)
    plot_training_curves(best_dl["history"], best_dl["arch"])
    print(f"\nDeployed: {deployed_name}  test {metrics['deployment']['test']}")
    print(f"Saved models to {config.MODELS_DIR} and figures to {config.FIGURES_DIR} in {metrics['training_seconds']}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quick", action="store_true", help="1 seed per deep model and no BiLSTM")
    main(quick=parser.parse_args().quick)
