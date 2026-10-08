"""Functional test cases from Table 4.1 of the report."""

import io
import sqlite3

import docx

import app as portal

PY_JOB = ("We are hiring a Python Backend Developer. Minimum 2 years of experience. Required skills: "
          "python, django, flask, rest api, sql, git, docker, aws. Qualification: B.Tech or equivalent.")
DA_JOB = ("We are hiring a Data Analyst. Minimum 1 years of experience. Required skills: sql, excel, "
          "python, pandas, power bi, statistics, data visualization, tableau. Qualification: B.Sc or equivalent.")
STRONG = ("Sneha Patil\nsneha@example.com | +91 98765 43210\nPython developer with 4 years of experience.\n"
          "Skills: Python3, Django REST Framework, Flask, RESTful services, PostgreSQL, GitHub, Docker, AWS\n"
          "Education: B.Tech in Computer Science")
WEAK = "Rohan Sharma\nrohan@example.com\nSales executive with 1 year of experience.\nSkills: MS Excel\nEducation: Diploma"


def register(c, name, email, role, password="secret123"):
    return c.post("/register", data=dict(name=name, email=email, password=password, role=role))


def login(c, email, password="secret123"):
    return c.post("/login", data=dict(email=email, password=password))


def post_job(c, title, desc, min_exp):
    return c.post("/jobs/new", data=dict(title=title, location="Pune", description=desc, min_experience=min_exp))


def apply(c, job_id, content, name="resume.txt"):
    return c.post(f"/jobs/{job_id}/apply", data={"resume": (io.BytesIO(content), name)},
                  content_type="multipart/form-data")


def setup_recruiter(c):
    register(c, "Recruiter", "hr@acme.com", "recruiter")
    login(c, "hr@acme.com")
    post_job(c, "Python Backend Developer", PY_JOB, 2)
    post_job(c, "Data Analyst", DA_JOB, 1)
    c.get("/logout")


def test_1_register_hashes_password(client):
    assert register(client, "R", "r@x.com", "recruiter").status_code == 302
    assert register(client, "S", "s@x.com", "seeker").status_code == 302
    conn = sqlite3.connect(portal.app.config["DATABASE"])
    pw = conn.execute("SELECT password FROM users WHERE email='r@x.com'").fetchone()[0]
    assert pw != "secret123" and pw.startswith(("scrypt:", "pbkdf2:"))


def test_2_duplicate_email_refused(client):
    register(client, "R", "r@x.com", "recruiter")
    resp = register(client, "R2", "r@x.com", "seeker")
    assert b"Email already registered" in resp.data


def test_3_wrong_password(client):
    register(client, "R", "r@x.com", "recruiter")
    resp = login(client, "r@x.com", "wrong-password")
    assert resp.status_code == 401 and b"Invalid credentials" in resp.data


def test_4_jobs_on_home_and_dashboard(client):
    setup_recruiter(client)
    home = client.get("/").data
    assert b"Python Backend Developer" in home and b"Data Analyst" in home
    login(client, "hr@acme.com")
    dash = client.get("/dashboard").data
    assert b"Python Backend Developer" in dash and b"Data Analyst" in dash


def test_5_search(client):
    setup_recruiter(client)
    page = client.get("/?q=Analyst").data
    assert b"Data Analyst" in page and b"Python Backend Developer" not in page


def test_6_txt_applications_scored(client):
    setup_recruiter(client)
    for i in range(8):
        register(client, f"Seeker {i}", f"c{i}@demo.com", "seeker")
        login(client, f"c{i}@demo.com")
        apply(client, 1, (STRONG if i % 2 else WEAK).encode())
        client.get("/logout")
    conn = sqlite3.connect(portal.app.config["DATABASE"])
    scores = [r[0] for r in conn.execute("SELECT score FROM applications")]
    assert len(scores) == 8 and all(s is not None for s in scores)


def test_7_docx_resume(client):
    setup_recruiter(client)
    register(client, "S", "s@x.com", "seeker")
    login(client, "s@x.com")
    d = docx.Document()
    for line in STRONG.split("\n"):
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    resp = apply(client, 1, buf.getvalue(), "resume.docx")
    assert resp.status_code == 302
    page = client.get("/dashboard", follow_redirects=True).data
    assert b"match score" in page.lower()


def test_8_exe_refused(client):
    setup_recruiter(client)
    register(client, "S", "s@x.com", "seeker")
    login(client, "s@x.com")
    resp = apply(client, 1, b"MZ...", "virus.exe")
    page = client.get(resp.headers["Location"]).data
    assert b"Upload a PDF, DOCX or TXT resume." in page


def test_9_seeker_cannot_view_candidates(client):
    setup_recruiter(client)
    register(client, "S", "s@x.com", "seeker")
    login(client, "s@x.com")
    resp = client.get("/jobs/1/candidates")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


def test_10_candidates_ranked_with_skills(client):
    setup_recruiter(client)
    for i, text in enumerate([WEAK, STRONG]):
        register(client, f"S{i}", f"s{i}@x.com", "seeker")
        login(client, f"s{i}@x.com")
        apply(client, 1, text.encode())
        client.get("/logout")
    login(client, "hr@acme.com")
    page = client.get("/jobs/1/candidates").data.decode()
    assert page.index("S1") < page.index("S0")   # strong candidate ranked first
    assert "django" in page and "Missing skills" in page


def test_11_status_change_visible_to_seeker(client):
    setup_recruiter(client)
    register(client, "S", "s@x.com", "seeker")
    login(client, "s@x.com")
    apply(client, 1, STRONG.encode())
    client.get("/logout")
    login(client, "hr@acme.com")
    client.post("/applications/1/status", data={"status": "Shortlisted"})
    client.get("/logout")
    login(client, "s@x.com")
    assert b"Shortlisted" in client.get("/dashboard").data


def test_recruiter_cannot_see_other_recruiters_candidates(client):
    setup_recruiter(client)
    register(client, "Other", "other@x.com", "recruiter")
    login(client, "other@x.com")
    assert client.get("/jobs/1/candidates").status_code == 403
