"""JobMatch AI: Streamlit web app.

    streamlit run app.py
"""

import streamlit as st

from jobmatch import config, db

st.set_page_config(page_title="JobMatch AI", page_icon="💼", layout="wide")


@st.cache_resource
def prepare_database():
    """Create the database on first run and fill it with demo data."""
    db.init_db()
    if not db.list_users() and config.ML_MODEL_PATH.exists():
        from jobmatch.seed import seed
        seed()
    return True


prepare_database()

from ui import admin, candidate, employer, public  # noqa: E402
from ui.common import refresh_user  # noqa: E402

refresh_user()
user = st.session_state.get("user")

pages = {"Explore": [
    st.Page(public.resume_analyzer, title="Resume Analyzer", icon="🔎", url_path="analyzer", default=True),
    st.Page(public.browse_jobs, title="Browse Jobs", icon="📋", url_path="jobs"),
    st.Page(public.model_performance, title="Model Performance", icon="📈", url_path="performance"),
]}
if user is None:
    pages["Account"] = [st.Page(public.login, title="Log in", icon="🔑", url_path="login"),
                        st.Page(public.register, title="Register", icon="📝", url_path="register")]
elif user["role"] == "candidate":
    pages["Candidate"] = [
        st.Page(candidate.my_resume, title="My Resume", icon="📄", url_path="my-resume"),
        st.Page(candidate.recommended_jobs, title="Recommended Jobs", icon="⭐", url_path="recommended"),
        st.Page(candidate.my_applications, title="My Applications", icon="📬", url_path="applications"),
    ]
elif user["role"] == "employer":
    pages["Employer"] = [
        st.Page(employer.applicants, title="Ranked Applicants", icon="🏆", url_path="applicants"),
        st.Page(employer.find_candidates, title="Find Candidates", icon="🧭", url_path="find-candidates"),
        st.Page(employer.post_job, title="Post a Job", icon="➕", url_path="post-job"),
    ]
elif user["role"] == "admin":
    pages["Admin"] = [st.Page(admin.dashboard, title="Dashboard", icon="🛠️", url_path="admin")]

with st.sidebar:
    st.markdown("### 💼 JobMatch AI")
    st.caption("Resume screening and candidate matching with machine learning and deep learning")
    if user:
        st.write(f"Logged in as **{user['name']}** ({user['role']})")
        if st.button("Log out"):
            st.session_state.pop("user", None)
            st.rerun()

st.navigation(pages).run()
