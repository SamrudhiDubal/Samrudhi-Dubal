import io

from app import db
from app.models import Application, Job, User

from .conftest import login, make_user

RESUME = b"Python developer with 3 years of experience in Flask, MySQL and Docker. B.Tech CSE."


def upload(data=RESUME, name="resume.txt"):
    return (io.BytesIO(data), name)


def test_register_and_login(client):
    resp = client.post("/auth/register", data={
        "name": "Asha", "email": "asha@x.com", "password": "secret123", "role": "candidate",
    }, follow_redirects=True)
    assert b"Welcome, Asha" in resp.data
    client.get("/auth/logout")
    resp = login(client, "asha@x.com")
    assert b"My applications" in resp.data


def test_cannot_self_register_as_admin(client):
    client.post("/auth/register", data={"name": "X", "email": "x@x.com", "password": "secret123", "role": "admin"})
    assert User.query.filter_by(email="x@x.com").first() is None


def test_employer_posts_job(client, employer):
    login(client, employer.email)
    resp = client.post("/employer/jobs/new", data={
        "title": "ML Engineer", "company": "Co", "location": "Remote", "job_type": "Remote",
        "min_experience": "1", "required_skills": "python, nlp", "description": "Build NLP models.",
    }, follow_redirects=True)
    assert b"Job posted successfully" in resp.data
    assert Job.query.filter_by(title="ML Engineer").count() == 1


def test_candidate_cannot_post_job(client):
    make_user("c@x.com")
    login(client, "c@x.com")
    assert client.get("/employer/jobs/new").status_code == 403


def test_apply_runs_ai_screening(client, job):
    make_user("c@x.com")
    login(client, "c@x.com")
    resp = client.post(f"/jobs/{job.id}/apply", data={"resume": upload()},
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"AI match score" in resp.data
    application = Application.query.one()
    assert application.match_score > 60
    assert application.matched_skill_list == ["python", "flask", "sql", "docker"]
    assert application.years_experience == 3
    assert application.education == "Bachelor's"
    # duplicate applications are rejected
    resp = client.post(f"/jobs/{job.id}/apply", data={"resume": upload()},
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"already applied" in resp.data
    assert Application.query.count() == 1


def test_apply_rejects_bad_file_type(client, job):
    make_user("c@x.com")
    login(client, "c@x.com")
    resp = client.post(f"/jobs/{job.id}/apply", data={"resume": upload(b"MZ", "virus.exe")},
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"must be a PDF, DOCX or TXT" in resp.data
    assert Application.query.count() == 0


def test_employer_sees_ranked_applicants_and_updates_status(client, job, employer):
    for email, text in [("weak@x.com", b"Chef who loves cooking."), ("strong@x.com", RESUME)]:
        make_user(email, name=email.split("@")[0])
        login(client, email)
        client.post(f"/jobs/{job.id}/apply", data={"resume": upload(text)}, content_type="multipart/form-data")
        client.get("/auth/logout")

    login(client, employer.email)
    page = client.get(f"/employer/jobs/{job.id}/applicants").data.decode()
    assert page.index("strong@x.com") < page.index("weak@x.com")

    strong = Application.query.join(User).filter(User.email == "strong@x.com").one()
    client.post(f"/employer/applications/{strong.id}/status", data={"status": "shortlisted"})
    assert db.session.get(Application, strong.id).status == "shortlisted"


def test_auto_shortlist(client, job, employer):
    make_user("strong@x.com")
    login(client, "strong@x.com")
    client.post(f"/jobs/{job.id}/apply", data={"resume": upload()}, content_type="multipart/form-data")
    client.get("/auth/logout")
    login(client, employer.email)
    client.post(f"/employer/jobs/{job.id}/auto-shortlist", data={"threshold": "50"})
    assert Application.query.one().status == "shortlisted"


def test_other_employer_cannot_view_applicants(client, job):
    make_user("other@co.com", role="employer", company="Other")
    login(client, "other@co.com")
    assert client.get(f"/employer/jobs/{job.id}/applicants").status_code == 403


def test_talent_search_and_recommendations(client, job, employer):
    make_user("c@x.com", name="Tara Talent", resume_text=RESUME.decode(), skills="python")
    make_user("empty@x.com", name="No Resume")
    login(client, "c@x.com")
    dash = client.get("/candidate/dashboard").data
    assert b"Recommended for you" in dash and b"Python Developer" in dash
    client.get("/auth/logout")
    login(client, employer.email)
    talent = client.get(f"/employer/jobs/{job.id}/talent").data
    assert b"Tara Talent" in talent  # candidate who never applied is still found
    assert b"No Resume" not in talent  # profiles without resume/skills are skipped


def test_profile_resume_upload_shows_analysis(client):
    make_user("c@x.com")
    login(client, "c@x.com")
    resp = client.post("/candidate/profile", data={"name": "C", "skills": "python", "resume": upload()},
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"Skills found in your resume" in resp.data
    assert b"3 years" in resp.data


def test_admin_dashboard_and_deactivate(client, job):
    make_user("admin@x.com", role="admin")
    cand = make_user("c@x.com")
    login(client, "admin@x.com")
    assert client.get("/admin/").status_code == 200
    client.post(f"/admin/users/{cand.id}/toggle")
    client.get("/auth/logout")
    resp = login(client, "c@x.com")
    assert b"deactivated" in resp.data


def test_job_search(client, job):
    assert b"Python Developer" in client.get("/jobs?q=flask").data
    assert b"Python Developer" not in client.get("/jobs?q=nursing").data
