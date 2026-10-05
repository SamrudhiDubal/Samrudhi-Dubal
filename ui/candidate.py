"""Candidate pages: resume profile, recommendations, applications."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from jobmatch import db
from jobmatch.experience import extract_experience_years
from jobmatch.skills import extract_skills
from ui.common import (job_card_header, match_details, models_or_stop, pretty, probability_chart,
                       read_resume_input, require_role, score_badge)


def my_resume():
    user = require_role("candidate")
    st.title("My Resume")
    clf, _ = models_or_stop()
    saved = db.get_resume(user["id"])
    if saved:
        st.success(f"Resume on file: **{saved['filename']}**, classified as **{pretty(saved['predicted_category'])}**.")
        top = sorted(saved["category_probs"].items(), key=lambda kv: kv[1], reverse=True)[:5]
        probability_chart(top)
        years = saved["experience_years"]
        st.markdown("**Skills detected:** " + (", ".join(saved["skills"]) or "none") + "  \n"
                    "**Years of experience detected:** " + ("not found" if years is None else f"{years:g}"))
        with st.expander("View resume text"):
            st.text(saved["text"][:5000])
        st.subheader("Replace resume")
    else:
        st.info("Upload your resume so the AI can recommend jobs and employers can find you.")

    resume = read_resume_input("profile")
    if resume and st.button("Save resume", type="primary"):
        text, filename = resume
        with st.spinner("Analyzing..."):
            pred = clf.predict(text)
            db.save_resume(user["id"], text, filename, pred["category"], pred["probabilities"],
                           extract_skills(text), extract_experience_years(text))
        st.rerun()


def recommended_jobs():
    user = require_role("candidate")
    st.title("Recommended Jobs")
    _, service = models_or_stop()
    saved = db.get_resume(user["id"])
    if not saved:
        st.warning("Upload your resume on the **My Resume** page first.")
        return
    applied = {a["job_id"] for a in db.list_applications_for_candidate(user["id"])}
    jobs = db.list_jobs("open")
    st.caption(f"All {len(jobs)} open jobs ranked against your resume (classified as {pretty(saved['predicted_category'])}).")
    for job, match in service.recommend_jobs(saved["text"], jobs, limit=len(jobs)):
        with st.container(border=True):
            left, right = st.columns([4, 1])
            with left:
                job_card_header(job)
            right.markdown(score_badge(match["score"]))
            with st.expander("Details and apply"):
                st.write(job["description"])
                match_details(match)
                if job["id"] in applied:
                    st.success("You have applied to this job.")
                else:
                    cover = st.text_area("Cover letter (optional)", key=f"cover_{job['id']}")
                    if st.button("Apply", key=f"apply_{job['id']}", type="primary"):
                        try:
                            db.create_application(job["id"], user["id"], match["score"], match, cover)
                            st.success("Application submitted.")
                            st.rerun()
                        except db.DuplicateError as exc:
                            st.error(str(exc))


def my_applications():
    user = require_role("candidate")
    st.title("My Applications")
    apps = db.list_applications_for_candidate(user["id"])
    if not apps:
        st.info("No applications yet. See **Recommended Jobs**.")
        return
    st.dataframe(pd.DataFrame([{"Job": a["job_title"], "Company": a["company"], "AI match": f"{a['score']}%",
                                "Status": a["status"].title(), "Applied": a["created_at"][:10]} for a in apps]),
                 hide_index=True, use_container_width=True)
