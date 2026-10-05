"""Shared helpers for the Streamlit pages."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from jobmatch import db
from jobmatch.matcher import MatchingService
from jobmatch.models import ModelsNotTrainedError, get_classifier
from jobmatch.resume_parser import ResumeParseError, extract_resume_text

BLUE = "#2a78d6"


@st.cache_resource(show_spinner="Loading AI models...")
def load_models():
    clf = get_classifier()
    return clf, MatchingService(clf)


def models_or_stop():
    try:
        return load_models()
    except ModelsNotTrainedError:
        st.error("The AI models have not been trained yet. Run `python train.py` in a terminal, then reload.")
        st.stop()


def current_user() -> dict | None:
    return st.session_state.get("user")


def pretty(category: str) -> str:
    """"BUSINESS-DEVELOPMENT" -> "Business Development", keeping HR and BPO upper-case."""
    return " ".join(w if w in ("HR", "BPO") else w.title() for w in category.split("-"))


def read_resume_input(key: str) -> tuple[str, str] | None:
    """Upload or paste a resume. Returns (text, filename) or None."""
    tab_upload, tab_paste = st.tabs(["Upload file", "Paste text"])
    with tab_upload:
        file = st.file_uploader("Resume (PDF, DOCX or TXT, max 5 MB)", type=["pdf", "docx", "txt"], key=f"{key}_file")
    with tab_paste:
        pasted = st.text_area("Resume text", height=200, key=f"{key}_text",
                              placeholder="Paste the full text of a resume here...")
    if file is not None:
        try:
            return extract_resume_text(file.getvalue(), file.name), file.name
        except ResumeParseError as exc:
            st.error(str(exc))
            return None
    if pasted and pasted.strip():
        if len(pasted.split()) < 30:
            st.warning("That looks very short. Predictions are more reliable on a full resume (100+ words).")
        return pasted, "pasted.txt"
    return None


def probability_chart(top: list[tuple[str, float]]):
    data = pd.DataFrame({"Category": [pretty(c) for c, _ in top], "Probability": [p for _, p in top]})
    chart = (
        alt.Chart(data)
        .mark_bar(color=BLUE, cornerRadiusEnd=4, height=18)
        .encode(
            x=alt.X("Probability:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%", grid=True)),
            y=alt.Y("Category:N", sort="-x", title=None, axis=alt.Axis(labelOverlap=False, labelLimit=200)),
            tooltip=["Category", alt.Tooltip("Probability:Q", format=".1%")],
        )
        .properties(height=44 * len(top))
    )
    st.altair_chart(chart, use_container_width=True)


def score_badge(score: int) -> str:
    if score >= 70:
        return f":green-badge[{score}% match]"
    if score >= 45:
        return f":orange-badge[{score}% match]"
    return f":red-badge[{score}% match]"


def match_details(match: dict):
    """Explain a match score: the four signals plus matched and missing skills."""
    cols = st.columns(4)
    cols[0].metric("Category fit", f"{match['category_fit']}%", help="Classifier probability that this resume belongs to the job's category (40% weight)")
    cols[1].metric("Skill match", f"{match['skill_match']}%", help="Share of the job's required skills found in the resume (30% weight)")
    sem = match.get("semantic_similarity")
    cols[2].metric("Semantic similarity", "n/a" if sem is None else f"{sem}%", help="Similarity of deep-learning (CNN) embeddings of resume and job (20% weight)")
    exp = match.get("experience_fit")
    years = match.get("years_detected")
    cols[3].metric("Experience fit", "unknown" if exp is None else f"{exp}%",
                   help="Detected years of experience vs. the job minimum (10% weight; ignored when unknown)",
                   delta=None if years is None else f"{years:g} yrs detected", delta_color="off")
    st.markdown(f"**Matched skills:** {', '.join(match['matched_skills']) or 'none'}  \n"
                f"**Missing skills:** {', '.join(match['missing_skills']) or 'none'}")


def job_card_header(job: dict):
    st.markdown(f"#### {job['title']}")
    st.caption(f"{job['company']} · {job.get('location') or 'Location not specified'} · {job.get('job_type') or ''}"
               f" · {pretty(job['category'])} · min {job.get('min_experience') or 0:g} yrs"
               + (f" · {job['salary']}" if job.get("salary") else ""))


def require_role(role: str) -> dict:
    user = current_user()
    if not user or user["role"] != role:
        st.warning("Please log in with the right account to view this page.")
        st.stop()
    return user


def refresh_user():
    user = current_user()
    if user:
        st.session_state["user"] = {**user, **(db.get_user(user["id"]) or {})}
