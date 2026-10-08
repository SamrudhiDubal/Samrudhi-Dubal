"""Evaluate the screening engine on the labelled test dataset (Chapter IV of the report).

Usage (from the job_portal folder):
    python -m eval.generate_dataset
    python -m eval.evaluate            # prints the tables, writes eval/results.json
    python -m eval.evaluate --charts   # also saves PNG charts to eval/charts (needs matplotlib)
"""

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from screening.matcher import (DEFAULT_WEIGHTS, keyword_scores, rank_candidates,
                               skill_scores, tfidf_scores)
from screening.parser import parse_resume

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


# ---------------------------------------------------------------- metrics

def ranking(scores):
    return sorted(scores, key=lambda cid: scores[cid], reverse=True)


def precision_at(order, labels, k=10):
    return sum(labels[c] == 2 for c in order[:k]) / k


def recall_at(order, labels, k=20):
    strong = sum(v == 2 for v in labels.values())
    return sum(labels[c] == 2 for c in order[:k]) / strong if strong else 0.0


def ndcg_at(order, labels, k=10):
    dcg = sum((2 ** labels[c] - 1) / math.log2(i + 2) for i, c in enumerate(order[:k]))
    ideal = sorted(labels.values(), reverse=True)[:k]
    idcg = sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def table(headers, rows):
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows)]
    line = lambda r: "| " + " | ".join(str(x).ljust(w) for x, w in zip(r, widths)) + " |"
    return "\n".join([line(headers), "|" + "|".join("-" * (w + 2) for w in widths) + "|"]
                     + [line(r) for r in rows])


# ---------------------------------------------------------------- evaluation

def hybrid_scores(job, texts, weights=None):
    res = rank_candidates(job["description"], texts, weights=weights,
                          min_experience=job["min_experience"], min_education=job["min_education"])
    return {r.candidate_id: r.score for r in res}, res


def main(charts=False):
    jobs = json.loads((DATA / "jobs.json").read_text())
    resumes = json.loads((DATA / "resumes.json").read_text())
    texts = {r["id"]: r["text"] for r in resumes}
    stuffed_for = {j["title"]: {r["id"] for r in resumes if r.get("target") == j["title"]} for j in jobs}
    out = {}

    # 4.2 Parser accuracy
    ok = {"email": 0, "phone": 0, "experience": 0, "education": 0}
    recall, precision = [], []
    for r in resumes:
        p, t = parse_resume(r["text"]), r["truth"]
        ok["email"] += p["email"] == t["email"]
        ok["phone"] += p["phone"] == t["phone"]
        ok["experience"] += abs(p["experience_years"] - t["experience_years"]) < 1e-6
        ok["education"] += p["education_level"] == t["education_level"]
        truth = set(t["skills"])
        found = set(p["skills"])
        # stuffed resumes contain extra keywords by design, so judge skills on the genuine part only
        if r["kind"] == "stuffed":
            found = set(parse_resume(r["text"].split("\n\nKeywords:")[0])["skills"])
        recall.append(len(truth & found) / len(truth))
        precision.append(len(truth & found) / len(found) if found else 0)
    n = len(resumes)
    parser_rows = [[k.capitalize(), v, n, f"{100 * v / n:.1f}"] for k, v in ok.items()]
    parser_rows += [["Skills (recall)", "-", n, f"{100 * np.mean(recall):.1f}"],
                    ["Skills (precision)", "-", n, f"{100 * np.mean(precision):.1f}"]]
    print("\nTable 4.2 Resume parser field extraction accuracy\n")
    print(table(["Field", "Correct", "Total", "Accuracy (%)"], parser_rows))
    out["parser"] = parser_rows

    # 4.3 / 4.4 Method comparison
    methods = {"A. Boolean keyword": lambda j: keyword_scores(j["skills"], texts),
               "B. TF-IDF only": lambda j: tfidf_scores(j["description"], texts),
               "C. Skill match only": lambda j: skill_scores(j["skills"], texts),
               "D. Hybrid (proposed)": lambda j: hybrid_scores(j, texts)[0]}
    summary, per_job = [], {m: {} for m in methods}
    for name, fn in methods.items():
        p10, r20, nd, rho, stuffed = [], [], [], [], []
        for j in jobs:
            labels = {r["id"]: r["labels"][j["id"]] for r in resumes}
            s = fn(j)
            order = ranking(s)
            p10.append(precision_at(order, labels))
            r20.append(recall_at(order, labels))
            nd.append(ndcg_at(order, labels))
            ids = list(labels)
            rho.append(spearmanr([s[c] for c in ids], [labels[c] for c in ids]).statistic)
            stuffed.append(len(set(order[:10]) & stuffed_for[j["title"]]))
            per_job[name][j["title"]] = p10[-1]
        summary.append([name, f"{np.mean(p10):.3f}", f"{np.mean(r20):.3f}", f"{np.mean(nd):.3f}",
                        f"{np.mean(rho):.3f}", f"{np.mean(stuffed):.2f}"])
    print("\nTable 4.3 Comparison of screening methods (average of six job descriptions)\n")
    print(table(["Method", "P@10", "R@20", "NDCG@10", "Spearman", "Stuffed in top 10"], summary))
    rows = [[j["title"]] + [f"{per_job[m][j['title']]:.2f}" for m in methods] for j in jobs]
    rows.append(["Average"] + [f"{np.mean(list(per_job[m].values())):.2f}" for m in methods])
    print("\nTable 4.4 Precision at 10 by job description\n")
    print(table(["Job"] + [m.split()[1] if m[1] == "." else m for m in methods], rows))
    out["methods"], out["per_job_p10"] = summary, per_job

    # 4.5 Score distribution by relevance, 4.6 thresholds
    groups = {"Strong fit (label 2)": [], "Partial fit (label 1)": [],
              "Not relevant (label 0)": [], "Keyword-stuffed (label 0)": []}
    pairs = []  # (score, label)
    for j in jobs:
        s, _ = hybrid_scores(j, texts)
        for r in resumes:
            lab = r["labels"][j["id"]]
            pairs.append((s[r["id"]], lab))
            if r["id"] in stuffed_for[j["title"]]:
                groups["Keyword-stuffed (label 0)"].append(s[r["id"]])
            else:
                groups[{2: "Strong fit (label 2)", 1: "Partial fit (label 1)", 0: "Not relevant (label 0)"}[lab]].append(s[r["id"]])
    dist = [[g, len(v), f"{np.mean(v):.2f}", f"{np.std(v, ddof=1):.2f}", f"{min(v):.2f}", f"{max(v):.2f}"]
            for g, v in groups.items() if v]
    print("\nTable 4.5 Hybrid match score by ground-truth relevance\n")
    print(table(["Group", "Count", "Mean", "Std", "Min", "Max"], dist))
    out["distribution"] = dist

    thr_rows = []
    total_strong = sum(l == 2 for _, l in pairs)
    for cut in (40, 50, 60, 70, 80):
        listed = [(s, l) for s, l in pairs if s >= cut]
        tp = sum(l == 2 for _, l in listed)
        fp, fn = len(listed) - tp, total_strong - tp
        prec = tp / len(listed) if listed else 0
        rec = tp / total_strong if total_strong else 0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
        thr_rows.append([cut, len(listed), tp, fp, fn, f"{prec:.3f}", f"{rec:.3f}", f"{f1:.3f}",
                         f"{100 * (1 - len(listed) / len(pairs)):.1f}"])
    print("\nTable 4.6 Effect of shortlisting threshold\n")
    print(table(["Cut-off", "Listed", "TP", "FP", "FN", "Precision", "Recall", "F1", "Saving %"], thr_rows))
    out["thresholds"] = thr_rows

    # 4.7 Weight sensitivity
    settings = {"Proposed (35, 40, 15, 10)": DEFAULT_WEIGHTS,
                "Text-heavy (70, 20, 5, 5)": dict(text=.70, skills=.20, experience=.05, education=.05),
                "Skill-heavy (15, 70, 10, 5)": dict(text=.15, skills=.70, experience=.10, education=.05),
                "Equal (25, 25, 25, 25)": dict(text=.25, skills=.25, experience=.25, education=.25)}
    sens = []
    for name, w in settings.items():
        p10, nd, rho = [], [], []
        for j in jobs:
            labels = {r["id"]: r["labels"][j["id"]] for r in resumes}
            s, _ = hybrid_scores(j, texts, w)
            order = ranking(s)
            p10.append(precision_at(order, labels))
            nd.append(ndcg_at(order, labels))
            ids = list(labels)
            rho.append(spearmanr([s[c] for c in ids], [labels[c] for c in ids]).statistic)
        sens.append([name, f"{np.mean(p10):.3f}", f"{np.mean(nd):.3f}", f"{np.mean(rho):.3f}"])
    print("\nTable 4.7 Sensitivity to component weights (Text, Skills, Experience, Education)\n")
    print(table(["Weights", "P@10", "NDCG@10", "Spearman"], sens))
    out["weights"] = sens

    # 4.8 Top ten for the first job
    job = jobs[0]
    _, res = hybrid_scores(job, texts)
    by_id = {r["id"]: r for r in resumes}
    top = [[i + 1, m.candidate_id, f"{by_id[m.candidate_id]['family']}, {by_id[m.candidate_id]['kind']}",
            f"{m.score:.2f}", len(m.matched_skills), ", ".join(m.missing_skills) or "None"]
           for i, m in enumerate(res[:10])]
    print(f"\nTable 4.8 Top ten candidates for the {job['title']} job\n")
    print(table(["Rank", "Candidate", "Actual profile", "Score", "Matched", "Missing"], top))
    out["top10"] = top

    # 4.9 Processing time
    times = []
    for j in jobs:
        start = time.perf_counter()
        hybrid_scores(j, texts)
        ms = (time.perf_counter() - start) * 1000 / len(texts)
        times.append([j["title"], f"{ms:.2f}"])
    times.append(["Average", f"{np.mean([float(t[1]) for t in times]):.2f}"])
    print("\nTable 4.9 Processing time per resume (ms)\n")
    print(table(["Job", "ms / resume"], times))
    out["timing"] = times

    (HERE / "results.json").write_text(json.dumps(out, indent=2, default=float))
    print(f"\nSaved results to {HERE / 'results.json'}")
    if charts:
        save_charts(out, groups)


def save_charts(out, groups):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    folder = HERE / "charts"
    folder.mkdir(exist_ok=True)

    names = [r[0] for r in out["methods"]]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for k, (col, label) in enumerate([(1, "Precision@10"), (3, "NDCG@10"), (4, "Spearman")]):
        ax.bar(x + (k - 1) * 0.25, [float(r[col]) for r in out["methods"]], 0.25, label=label)
    ax.set_xticks(x, names, fontsize=8)
    ax.set_ylim(0, 1.05)
    ax.set_title("Ranking quality by screening method")
    ax.legend()
    fig.tight_layout()
    fig.savefig(folder / "methods.png", dpi=150)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.boxplot(list(groups.values()), tick_labels=[g.replace(" (", "\n(") for g in groups])
    ax.axhline(60, color="red", linestyle="--", linewidth=1)
    ax.set_ylabel("Hybrid match score")
    ax.set_title("Distribution of hybrid scores by ground-truth relevance")
    fig.tight_layout()
    fig.savefig(folder / "distribution.png", dpi=150)

    cuts = [r[0] for r in out["thresholds"]]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for col, label in [(5, "Precision"), (6, "Recall"), (7, "F1")]:
        ax.plot(cuts, [float(r[col]) for r in out["thresholds"]], marker="o", label=label)
    ax.set_xlabel("Shortlist threshold")
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.set_title("Precision, recall and F1 at different thresholds")
    fig.tight_layout()
    fig.savefig(folder / "thresholds.png", dpi=150)
    print(f"Saved charts to {folder}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--charts", action="store_true")
    main(ap.parse_args().charts)
