"""Employer pages: post jobs, ranked applicants, candidate search."""

from __future__ import annotations

import streamlit as st

from jobmatch import db
from jobmatch.db import APPLICATION_STATUSES
from ui.common import job_card_header, match_details, models_or_stop, pretty, require_role, score_badge


def _job_picker(user, label="Job"):
    jobs = db.list_jobs(status=None, employer_id=user["id"])
    if not jobs:
        st.info("You have not posted any jobs yet. Use **Post a Job**.")
        return None
    return st.selectbox(label, jobs, format_func=lambda j: f"{j['title']} ({j['status']})")


def post_job():
    user = require_role("employer")
    st.title("Post a Job")
    clf, _ = models_or_stop()
    with st.form("post_job", clear_on_submit=True):
        title = st.text_input("Job title")
        c1, c2 = st.columns(2)
        category = c1.selectbox("Category", clf.labels, format_func=pretty)
        job_type = c2.selectbox("Job type", ["Full-time", "Part-time", "Contract", "Internship"])
        c1, c2, c3 = st.columns(3)
        location = c1.text_input("Location")
        min_exp = c2.number_input("Minimum years of experience", 0, 40, 0)
        salary = c3.text_input("Salary (optional)", placeholder="e.g. ₹6–9 LPA")
        description = st.text_area("Job description", height=150)
        skills = st.text_input("Required skills (comma separated)", placeholder="e.g. recruiting, payroll, hris")
        submitted = st.form_submit_button("Post job", type="primary")
    if submitted:
        skill_list = [s for s in skills.split(",") if s.strip()]
        if not title.strip() or not description.strip() or not skill_list:
            st.error("Title, description and at least one skill are required.")
            return
        db.create_job(user["id"], title, user.get("company") or "", category, description, skill_list,
                      location, job_type, min_exp, salary)
        st.success("Job posted. Applicants will be screened and ranked automatically.")


def applicants():
    user = require_role("employer")
    st.title("Ranked Applicants")
    job = _job_picker(user)
    if not job:
        return
    c1, c2 = st.columns([3, 1])
    with c1:
        job_card_header(job)
    new_status = "closed" if job["status"] == "open" else "open"
    if c2.button(f"{'Close' if new_status == 'closed' else 'Reopen'} job"):
        db.set_job_status(job["id"], new_status)
        st.rerun()

    apps = db.list_applications_for_job(job["id"])
    st.caption(f"{len(apps)} applicants, ranked by AI match score")
    for app in apps:
        with st.container(border=True):
            left, mid, right = st.columns([3, 1, 1.3])
            left.markdown(f"**{app['candidate_name']}**  \n{app['candidate_email']}")
            mid.markdown(score_badge(app["score"]))
            status = right.selectbox("Status", APPLICATION_STATUSES, index=APPLICATION_STATUSES.index(app["status"]),
                                     key=f"status_{app['id']}", label_visibility="collapsed", format_func=str.title)
            if status != app["status"]:
                db.set_application_status(app["id"], status)
                st.rerun()
            with st.expander("Why this score?"):
                match_details(app["breakdown"])
                if app.get("cover_letter"):
                    st.markdown(f"**Cover letter:** {app['cover_letter']}")


def find_candidates():
    user = require_role("employer")
    st.title("Find Matching Candidates")
    st.write("Rank every candidate on the platform for one of your jobs, including people who have not applied.")
    _, service = models_or_stop()
    job = _job_picker(user)
    if not job:
        return
    candidates = db.list_candidates_with_resumes()
    applied = {a["candidate_id"] for a in db.list_applications_for_job(job["id"])}
    min_score = st.slider("Minimum match score", 0, 100, 40)
    ranked = [(c, m) for c, m in service.rank_candidates(job, candidates) if m["score"] >= min_score]
    st.caption(f"{len(ranked)} of {len(candidates)} candidates at or above {min_score}%")
    for cand, match in ranked:
        with st.container(border=True):
            left, mid, right = st.columns([3, 1, 1])
            left.markdown(f"**{cand['name']}**  \n{cand['email']} · resume classified as {pretty(cand['predicted_category'])}")
            mid.markdown(score_badge(match["score"]))
            right.markdown(":blue-badge[Applied]" if cand["user_id"] in applied else ":gray-badge[Not applied]")
            with st.expander("Why this score?"):
                match_details(match)
