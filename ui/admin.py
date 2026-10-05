"""Admin dashboard."""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from jobmatch import db
from ui.common import BLUE, pretty, require_role


def dashboard():
    require_role("admin")
    st.title("Admin Dashboard")
    s = db.stats()
    cols = st.columns(6)
    for col, (label, value) in zip(cols, [("Candidates", s["candidates"]), ("Employers", s["employers"]),
                                          ("Open jobs", s["open_jobs"]), ("Applications", s["applications"]),
                                          ("Avg. match", f"{s['avg_score']}%"), ("Shortlisted", s["shortlisted"])]):
        col.metric(label, value)

    status_counts = pd.DataFrame(db.application_status_counts())
    if not status_counts.empty:
        st.subheader("Applications by status")
        st.altair_chart(alt.Chart(status_counts).mark_bar(color=BLUE, cornerRadiusEnd=4).encode(
            x=alt.X("n:Q", title="Applications", axis=alt.Axis(tickMinStep=1, format="d")),
            y=alt.Y("status:N", sort=list(db.APPLICATION_STATUSES), title=None),
            tooltip=[alt.Tooltip("status:N", title="Status"), alt.Tooltip("n:Q", title="Applications")]),
            use_container_width=True)

    st.subheader("Users")
    users = db.list_users()
    st.dataframe(pd.DataFrame(users)[["id", "name", "email", "role", "company", "is_active", "created_at"]],
                 hide_index=True, use_container_width=True)
    others = [u for u in users if u["role"] != "admin"]
    c1, c2 = st.columns([3, 1])
    target = c1.selectbox("Activate or deactivate a user", others, format_func=lambda u: f"{u['name']} ({u['email']})")
    if target and c2.button("Deactivate" if target["is_active"] else "Activate"):
        db.set_user_active(target["id"], not target["is_active"])
        st.rerun()

    st.subheader("Jobs")
    jobs = db.list_jobs(status=None)
    st.dataframe(pd.DataFrame([{"id": j["id"], "title": j["title"], "company": j["company"],
                                "category": pretty(j["category"]), "status": j["status"]} for j in jobs]),
                 hide_index=True, use_container_width=True)
