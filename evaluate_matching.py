"""Evaluate the job <-> candidate matching engine on unseen resumes.

    python evaluate_matching.py      (run after train.py)

There are no human relevance labels for (job, resume) pairs, so a resume is
treated as relevant to a job when it belongs to the job's category. For each
of the 24 jobs in data/jobs.json, every held-out resume is ranked and we
measure:

- Precision@10: share of the top 10 that are from the job's category
- MAP: mean average precision over the full ranking

Each signal is evaluated on its own and in the final blend. The weight
sensitivity table is computed on the validation resumes, never the test set.
"""

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from jobmatch import config
from jobmatch.experience import experience_fit, extract_experience_years
from jobmatch.matcher import WEIGHTS, job_text, scale_semantic
from jobmatch.models import get_classifier
from jobmatch.skills import match_skills
from jobmatch.text import clean_text

ML_COLOR, DL_COLOR, ENS_COLOR, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#0b0b0b", "#52514e", "#e4e3df"


def signals(clf, resumes, jobs):
    """Each signal as a (jobs x resumes) matrix in 0-1, experience may be NaN."""
    probs = clf.predict_proba(resumes)
    idx = {l: i for i, l in enumerate(clf.labels)}
    cleaned = [clean_text(r) for r in resumes]
    jt = [job_text(j) for j in jobs]
    years = [extract_experience_years(r) for r in resumes]

    def exp(y, j):
        fit = experience_fit(y, j["min_experience"])
        return np.nan if fit is None else fit / 100

    return {
        "category": np.array([probs[:, idx[j["category"]]] for j in jobs]),
        "skills": np.array([[len(match_skills(t, j["skills"])[0]) / len(j["skills"]) for t in cleaned] for j in jobs]),
        "semantic": np.vectorize(scale_semantic)(clf.embed(jt) @ clf.embed(resumes).T),
        "tfidf": (clf.tfidf(jt) @ clf.tfidf(resumes).T).toarray(),
        "experience": np.array([[exp(y, j) for y in years] for j in jobs]),
    }


def blend(sig, weights):
    known = ~np.isnan(sig["experience"])
    base = sum(weights[k] * sig[k] for k in ("category", "skills", "semantic"))
    with_exp = base + weights["experience"] * np.nan_to_num(sig["experience"])
    return np.where(known, with_exp, base / (1 - weights["experience"]))


def precision_at(scores, y, jobs, k=10):
    return float(np.mean([np.mean(y[np.argsort(-scores[i])[:k]] == j["category"]) for i, j in enumerate(jobs)]))


def mean_ap(scores, y, jobs):
    aps = []
    for i, j in enumerate(jobs):
        rel = y[np.argsort(-scores[i])] == j["category"]
        hits = np.cumsum(rel)
        aps.append(float((hits[rel] / (np.where(rel)[0] + 1)).mean()))
    return float(np.mean(aps))


def main():
    clf = get_classifier()
    metrics = json.loads(config.METRICS_PATH.read_text())
    df = pd.read_csv(config.RESUME_DATASET).drop_duplicates("Resume_str").reset_index(drop=True)
    jobs = json.loads(config.JOBS_SEED_FILE.read_text())

    def subset(rows):
        return df.Resume_str[rows].tolist(), df.Category[rows].to_numpy()

    test_r, test_y = subset(metrics["test_rows"])
    sig = signals(clf, test_r, jobs)
    rows = {
        "Skill keywords only": sig["skills"],
        "TF-IDF similarity only (ML)": sig["tfidf"],
        "CNN embedding similarity only (DL)": sig["semantic"],
        "Category probability only (ensemble classifier)": sig["category"],
        "Final blend (40/30/20/10)": blend(sig, WEIGHTS),
    }
    results = {name: {"precision_at_10": round(precision_at(s, test_y, jobs), 4),
                      "precision_at_20": round(precision_at(s, test_y, jobs, 20), 4),
                      "map": round(mean_ap(s, test_y, jobs), 4)} for name, s in rows.items()}
    final = blend(sig, WEIGHTS) * 100
    same = np.mean([final[i][test_y == j["category"]].mean() for i, j in enumerate(jobs)])
    other = np.mean([final[i][test_y != j["category"]].mean() for i, j in enumerate(jobs)])

    val_r, val_y = subset(metrics["validation_rows"])
    vsig = signals(clf, val_r, jobs)
    sensitivity = []
    for w in [(0.4, 0.3, 0.2, 0.1), (0.5, 0.2, 0.2, 0.1), (0.3, 0.4, 0.2, 0.1), (0.3, 0.3, 0.3, 0.1), (0.25, 0.25, 0.25, 0.25)]:
        weights = dict(zip(("category", "skills", "semantic", "experience"), w))
        s = blend(vsig, weights)
        sensitivity.append({"weights": weights, "precision_at_10": round(precision_at(s, val_y, jobs), 4),
                            "map": round(mean_ap(s, val_y, jobs), 4)})

    out = {"test_resumes": len(test_r), "jobs": len(jobs), "signals": results,
           "mean_score_same_category": round(float(same), 1), "mean_score_other_category": round(float(other), 1),
           "validation_weight_sensitivity": sensitivity}
    (config.REPORTS_DIR / "matching_metrics.json").write_text(json.dumps(out, indent=1))

    for name, r in results.items():
        print(f"{name:50s} P@10 {r['precision_at_10']:.3f}  P@20 {r['precision_at_20']:.3f}  MAP {r['map']:.3f}")
    print(f"Average final score: same-category resumes {same:.0f}, other resumes {other:.0f}")
    print("Validation weight sensitivity:")
    for s in sensitivity:
        print(f"  {s['weights']}  P@10 {s['precision_at_10']:.3f}  MAP {s['map']:.3f}")

    names = list(results)
    vals = [results[n]["precision_at_10"] for n in names]
    colors = [MUTED, ML_COLOR, DL_COLOR, ENS_COLOR, INK]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.barh(names[::-1], vals[::-1], color=colors[::-1], height=0.6)
    for y, v in enumerate(vals[::-1]):
        ax.text(v + 0.01, y, f"{v:.0%}", va="center", fontsize=9, color=INK)
    ax.set_xlim(0, 1.08)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_title("Matching quality: share of top-10 candidates from the job's category (test set)",
                 loc="left", color=INK, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / "matching_precision.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
