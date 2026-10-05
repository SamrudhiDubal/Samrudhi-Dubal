"""Pages available without logging in."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from jobmatch import config, db
from jobmatch.experience import extract_experience_years
from jobmatch.skills import extract_skills
from ui.common import (job_card_header, match_details, models_or_stop, pretty, probability_chart,
                       read_resume_input, score_badge)


def resume_analyzer():
    st.title("AI Resume Analyzer")
    st.write("Upload or paste any resume. The deep-learning and machine-learning models predict its job "
             "category, detect skills and experience, and rank open jobs by fit.")
    clf, service = models_or_stop()

    resume = read_resume_input("analyzer")
    if not resume or not st.button("Analyze resume", type="primary"):
        return
    text, _ = resume
    with st.spinner("Analyzing..."):
        pred = clf.predict(text, top=5)
        skills = extract_skills(text)
        years = extract_experience_years(text)
        recs = service.recommend_jobs(text, db.list_jobs("open"), limit=5)

    st.subheader("Predicted job category")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Category", pretty(pred["category"]), f"{pred['confidence']:.0%} confidence", delta_color="off")
        names = {"ensemble": "Ensemble of SVM + CNN", "dl": "1D-CNN (deep learning)", "ml": "Linear SVM (machine learning)"}
        st.caption(f"Model: {names[pred['strategy']]}")
        if pred["dl_category"]:
            st.caption(f"Machine-learning model alone: **{pretty(pred['ml_category'])}**  \n"
                       f"Deep-learning model alone: **{pretty(pred['dl_category'])}**")
    with c2:
        probability_chart(pred["top"])

    st.subheader("Profile extracted from the resume")
    c1, c2 = st.columns([1, 2])
    c1.metric("Years of experience", "not found" if years is None else f"{years:g}")
    c2.markdown("**Skills detected:** " + (", ".join(skills) if skills else "none from the skills dictionary"))

    st.subheader("Best-matching open jobs")
    if not recs:
        st.info("No open jobs yet.")
    for job, match in recs:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                job_card_header(job)
            right.markdown(score_badge(match["score"]))
            with st.expander("Why this score?"):
                match_details(match)


def browse_jobs():
    st.title("Browse Jobs")
    jobs = db.list_jobs("open")
    c1, c2 = st.columns(2)
    query = c1.text_input("Search title, company or skill")
    cats = sorted({j["category"] for j in jobs})
    category = c2.selectbox("Category", ["All"] + cats, format_func=lambda c: c if c == "All" else pretty(c))
    q = query.lower().strip()
    shown = [j for j in jobs if (category == "All" or j["category"] == category) and
             (not q or q in j["title"].lower() or q in j["company"].lower() or any(q in s for s in j["skills"]))]
    st.caption(f"{len(shown)} open jobs")
    for job in shown:
        with st.container(border=True):
            job_card_header(job)
            st.write(job["description"])
            st.markdown("**Required skills:** " + ", ".join(job["skills"]))
    if not st.session_state.get("user"):
        st.info("Log in as a candidate to see your personal match score and apply.")


def model_performance():
    st.title("Model Performance")
    if not config.METRICS_PATH.exists():
        st.error("No metrics yet. Run `python train.py`.")
        return
    m = json.loads(config.METRICS_PATH.read_text())
    d, dep = m["dataset"], m["deployment"]
    st.write(f"Trained on **{d['resumes']:,} real resumes** in **{d['categories']} job categories** "
             f"(LiveCareer resume dataset, CC0 licence). {d['test']} resumes were held out as an unseen test set.")

    cols = st.columns(4)
    t = dep["test"]
    cols[0].metric("Test accuracy", f"{t['accuracy']:.1%}")
    cols[1].metric("Macro-F1", f"{t['macro_f1']:.1%}")
    cols[2].metric("Top-3 accuracy", f"{t['top3_accuracy']:.1%}")
    short = {"ensemble": "Ensemble", "dl": "1D-CNN", "ml": m.get("best_ml", "ML model")}
    cols[3].metric("Deployed model", short[dep["strategy"]], help=dep["model"])

    rows = []
    for name, r in m["results"].items():
        def v(x):
            return f"{x['mean']:.1%} ± {x['std']:.1%}" if isinstance(x, dict) else f"{x:.1%}"
        rows.append({"Model": name, "Type": {"ML": "Machine learning", "DL": "Deep learning"}.get(r["family"], r["family"]),
                     "Test accuracy": v(r["test"]["accuracy"]), "Macro-F1": v(r["test"]["macro_f1"]),
                     "Top-3 accuracy": v(r["test"]["top3_accuracy"]),
                     "5-fold CV accuracy": f"{r['cv']['accuracy']:.1%}" if "cv" in r else "—"})
    st.subheader("All models compared")
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                 column_config={"Model": st.column_config.TextColumn(width="large")})
    st.caption("Deep-learning results are the mean ± standard deviation over 3 random seeds. "
               "The deployed model was chosen on validation data, not the test set.")

    figures = [
        ("model_comparison.png", "Accuracy and macro-F1 of every model"),
        ("matching_precision.png", "Matching quality on unseen resumes"),
        ("confusion_matrix.png", "Where the deployed model gets confused"),
        ("per_class_f1.png", "Performance per category"),
        ("training_curves.png", "Deep-learning training curves"),
        ("class_distribution.png", "Dataset: resumes per category"),
    ]
    for file, caption in figures:
        path = config.FIGURES_DIR / file
        if path.exists():
            st.subheader(caption)
            st.image(str(path), use_container_width=True)

    matching = config.REPORTS_DIR / "matching_metrics.json"
    if matching.exists():
        mm = json.loads(matching.read_text())
        st.subheader("Matching engine evaluation")
        st.dataframe(pd.DataFrame([{"Ranking signal": k, "Precision@10": f"{v['precision_at_10']:.1%}",
                                    "Precision@20": f"{v['precision_at_20']:.1%}", "MAP": f"{v['map']:.3f}"}
                                   for k, v in mm["signals"].items()]), hide_index=True, use_container_width=True)
        st.caption(f"{mm['test_resumes']} unseen resumes ranked for each of {mm['jobs']} jobs. A resume counts as "
                   "relevant when it is from the job's category.")


def login():
    st.title("Log in")
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary")
    if submitted:
        user = db.authenticate(email, password)
        if user:
            st.session_state["user"] = user
            st.rerun()
        else:
            st.error("Invalid email or password, or the account has been deactivated.")
    with st.expander("Demo accounts (password: demo1234)"):
        st.markdown("- Candidate: `ananya@example.com`, `rahul@example.com`, `sneha@example.com`\n"
                    "- Employer: `talent@nimbus.example.com`, `hiring@crestview.example.com`\n"
                    "- Admin: `admin@example.com`")


def register():
    st.title("Create an account")
    with st.form("register"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Password (at least 6 characters)", type="password")
        role = st.radio("I am a", ["candidate", "employer"], horizontal=True, format_func=str.title)
        company = st.text_input("Company (employers only)")
        submitted = st.form_submit_button("Create account", type="primary")
    if submitted:
        if not name.strip() or "@" not in email:
            st.error("Please enter your name and a valid email.")
            return
        if role == "employer" and not company.strip():
            st.error("Employers need a company name.")
            return
        try:
            db.create_user(name, email, password, role, company=company.strip() or None)
        except (ValueError, db.DuplicateError) as exc:
            st.error(str(exc))
            return
        st.session_state["user"] = db.authenticate(email, password)
        st.rerun()
