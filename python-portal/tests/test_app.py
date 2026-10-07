import io

from models import Application, Job, User, db

RESUME = b"Python developer with 5 years of experience in Flask, SQL and Docker. B.Tech in CS."


def register(client, name, email, role):
    return client.post("/register", data=dict(name=name, email=email, password="secret1",
                                              role=role), follow_redirects=True)


def post_job(client, **overrides):
    data = dict(title="Python Developer", company="Acme", location="Pune",
                job_type="full-time", experience_level="mid",
                skills_required="Python, Flask, SQL, Docker",
                description="Build web services with Python and Flask backed by SQL.")
    data.update(overrides)
    return client.post("/jobs/new", data=data, follow_redirects=True)


def test_full_flow_apply_and_rank(app, client):
    register(client, "Emp", "emp@x.com", "employer")
    assert b"Job posted" in post_job(client).data
    client.get("/logout")

    register(client, "Cand", "cand@x.com", "candidate")
    with app.app_context():
        job_id = Job.query.first().id
    resp = client.post(f"/jobs/{job_id}/apply",
                       data={"resume": (io.BytesIO(RESUME), "resume.txt"),
                             "cover_letter": "Hi"},
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"AI match score" in resp.data

    # Duplicate applications are rejected.
    resp = client.post(f"/jobs/{job_id}/apply", data={}, follow_redirects=True)
    assert b"already applied" in resp.data

    with app.app_context():
        application = Application.query.one()
        assert application.match_score >= 80
        assert application.details["missing_skills"] == []
        assert User.query.filter_by(email="cand@x.com").one().resume_text

    assert b"Python Developer" in client.get("/recommendations").data
    client.get("/logout")

    client.post("/login", data=dict(email="emp@x.com", password="secret1"))
    page = client.get(f"/jobs/{job_id}/applicants")
    assert b"Cand" in page.data
    assert b"Cand" in client.get(f"/jobs/{job_id}/matches").data
    client.post(f"/applications/{application.id}/status", data={"status": "shortlisted"})
    with app.app_context():
        assert db.session.get(Application, application.id).status == "shortlisted"


def test_role_guards(client):
    register(client, "Cand", "c@x.com", "candidate")
    assert client.get("/jobs/new").status_code == 403
    client.get("/logout")
    assert client.get("/jobs/new").status_code == 302  # redirected to login


def test_employer_cannot_touch_other_employers_job(app, client):
    register(client, "A", "a@x.com", "employer")
    post_job(client)
    client.get("/logout")
    register(client, "B", "b@x.com", "employer")
    with app.app_context():
        job_id = Job.query.first().id
    assert client.get(f"/jobs/{job_id}/applicants").status_code == 403
    assert client.post(f"/jobs/{job_id}/delete").status_code == 403


def test_rejects_bad_resume_type(app, client):
    register(client, "E", "e@x.com", "employer")
    post_job(client)
    client.get("/logout")
    register(client, "C", "c@x.com", "candidate")
    with app.app_context():
        job_id = Job.query.first().id
    resp = client.post(f"/jobs/{job_id}/apply",
                       data={"resume": (io.BytesIO(b"x"), "resume.exe")},
                       content_type="multipart/form-data", follow_redirects=True)
    assert b"PDF, DOCX, or TXT" in resp.data


def test_job_search_filters(client):
    register(client, "E", "e@x.com", "employer")
    post_job(client)
    post_job(client, title="Data Scientist", skills_required="python, machine learning",
             experience_level="senior", location="Remote")
    assert b"Data Scientist" not in client.get("/jobs?skill=flask").data
    assert b"Data Scientist" in client.get("/jobs?level=senior").data
    assert b"Python Developer" not in client.get("/jobs?location=remote").data


def test_api_match(client):
    resp = client.post("/api/match", json={
        "resume_text": RESUME.decode(), "title": "Backend", "description": "Python Flask APIs",
        "skills_required": "python, flask", "experience_level": "mid"})
    assert resp.status_code == 200
    assert resp.get_json()["skill_match_percent"] == 100
    assert client.post("/api/match", json={}).status_code == 400
