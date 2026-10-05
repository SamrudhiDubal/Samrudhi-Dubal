"""Fill docs/report_template.md with the numbers from the latest training run.

    python docs/build_report.py      (after train.py and evaluate_matching.py)

Writes docs/PROJECT_REPORT.md, so the report always matches the saved models.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from jobmatch import config  # noqa: E402


def pct(x):
    return f"{x:.1%}"


def val(x):
    return f"{x['mean']:.1%} ± {x['std']:.1%}" if isinstance(x, dict) else pct(x)


def main():
    m = json.loads(config.METRICS_PATH.read_text())
    mm = json.loads((config.REPORTS_DIR / "matching_metrics.json").read_text())
    d, dep, res = m["dataset"], m["deployment"], m["results"]

    rows = ["| Model | Type | 5-fold CV accuracy | Test accuracy | Test macro-F1 | Test top-3 accuracy |",
            "| --- | --- | --- | --- | --- | --- |"]
    for name, r in res.items():
        kind = {"ML": "Machine learning", "DL": "Deep learning (3 seeds)"}.get(r["family"], r["family"])
        bold = "**" if name == dep["model"] else ""
        cv = pct(r["cv"]["accuracy"]) if "cv" in r else "—"
        rows.append(f"| {bold}{name}{bold} | {kind} | {cv} | {bold}{val(r['test']['accuracy'])}{bold} | "
                    f"{val(r['test']['macro_f1'])} | {val(r['test']['top3_accuracy'])} |")

    match_rows = ["| Ranking signal | Precision@10 | Precision@20 | MAP |", "| --- | --- | --- | --- |"]
    for name, r in mm["signals"].items():
        match_rows.append(f"| {name} | {pct(r['precision_at_10'])} | {pct(r['precision_at_20'])} | {r['map']:.3f} |")

    sens = ["| Category / Skills / Semantic / Experience | Precision@10 | MAP |", "| --- | --- | --- |"]
    for s in mm["validation_weight_sensitivity"]:
        w = s["weights"]
        sens.append(f"| {w['category']:.0%} / {w['skills']:.0%} / {w['semantic']:.0%} / {w['experience']:.0%} | "
                    f"{pct(s['precision_at_10'])} | {s['map']:.3f} |")

    vc = dep["validation_macro_f1"]
    raw = pd.read_csv(config.RESUME_DATASET)
    values = {
        "N_RAW": f"{len(raw):,}",
        "N_DUPES": str(d["duplicates_removed"]),
        "N_RESUMES": f"{d['resumes']:,}",
        "N_CATEGORIES": str(d["categories"]),
        "N_TRAIN": f"{d['train']:,}",
        "N_TEST": str(d["test"]),
        "CNN_ACC": pct(res["1D-CNN"]["test"]["accuracy"]["mean"]),
        "DEP_ACC": pct(dep["test"]["accuracy"]),
        "DEP_F1": pct(dep["test"]["macro_f1"]),
        "DEP_TOP3": pct(dep["test"]["top3_accuracy"]),
        "DEP_STRATEGY": {"ensemble": "the ensemble", "dl": "the CNN alone", "ml": "the ML model alone"}[dep["strategy"]],
        "VAL_CHOICE": f"ML {vc['ml']:.3f}, DL {vc['dl']:.3f}, ensemble {vc['ensemble']:.3f}",
        "FINAL_P10": pct(mm["signals"]["Final blend (40/30/20/10)"]["precision_at_10"]),
        "SAME_SCORE": f"{mm['mean_score_same_category']:.0f}",
        "OTHER_SCORE": f"{mm['mean_score_other_category']:.0f}",
        "MODEL_TABLE": "\n".join(rows),
        "MATCHING_TABLE": "\n".join(match_rows),
        "SENSITIVITY_TABLE": "\n".join(sens),
    }
    text = (ROOT / "docs" / "report_template.md").read_text()
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    missing = [part.split("}}")[0] for part in text.split("{{")[1:]]
    if missing:
        raise SystemExit(f"Unfilled placeholders: {missing}")
    (ROOT / "docs" / "PROJECT_REPORT.md").write_text(text)
    print("Wrote docs/PROJECT_REPORT.md")


if __name__ == "__main__":
    main()
