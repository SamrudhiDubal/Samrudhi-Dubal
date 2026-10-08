"""AI Job Portal - Flask web application (Section 3.5 of the report).

Run:  python app.py        then open http://127.0.0.1:5000
"""

import json
import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   send_from_directory, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from screening import (EDUCATION_NAMES, SHORTLIST_THRESHOLD, extract_text,
                       parse_resume, rank_candidates)

BASE = Path(__file__).resolve().parent
ALLOWED = {".pdf", ".docx", ".txt"}
STATUSES = ["Applied", "Shortlisted", "Interview", "Rejected", "Hired"]

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
    DATABASE=os.environ.get("DATABASE", str(BASE / "portal.db")),
    UPLOAD_FOLDER=os.environ.get("UPLOAD_FOLDER", str(BASE / "uploads")),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5 MB resume limit
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('seeker', 'recruiter')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recruiter_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    location TEXT,
    description TEXT NOT NULL,
    min_experience REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    seeker_id INTEGER NOT NULL REFERENCES users(id),
    resume_path TEXT NOT NULL,
    score REAL,
    breakdown TEXT,
    status TEXT DEFAULT 'Applied',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (job_id, seeker_id)
);
"""


# ---------------------------------------------------------------- database

def db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    with app.app_context():
        db().executescript(SCHEMA)
        db().commit()


# ---------------------------------------------------------------- auth helpers

def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.")
                return redirect(url_for("login", next=request.path))
            if role and session.get("role") != role:
                flash("Access denied for your account type.")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.context_processor
def inject_user():
    return {"current_role": session.get("role"), "current_name": session.get("name"),
            "threshold": SHORTLIST_THRESHOLD}


@app.template_filter("fromjson")
def fromjson(value):
    return json.loads(value) if value else {}


# ---------------------------------------------------------------- public pages

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    sql = "SELECT j.*, u.name AS company FROM jobs j JOIN users u ON u.id = j.recruiter_id"
    params = ()
    if q:
        sql += " WHERE j.title LIKE ? OR j.description LIKE ? OR j.location LIKE ?"
        params = (f"%{q}%",) * 3
    jobs = db().execute(sql + " ORDER BY j.created_at DESC, j.id DESC", params).fetchall()
    return render_template("index.html", jobs=jobs, q=q)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "seeker")
        if not name or not email or len(password) < 6 or role not in ("seeker", "recruiter"):
            flash("Please fill all fields. Password must be at least 6 characters.")
            return render_template("register.html"), 400
        try:
            db().execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                         (name, email, generate_password_hash(password), role))
            db().commit()
        except sqlite3.IntegrityError:
            flash("Email already registered")
            return render_template("register.html"), 400
        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not check_password_hash(user["password"], request.form.get("password", "")):
            flash("Invalid credentials")
            return render_template("login.html"), 401
        session.clear()
        session.update(user_id=user["id"], role=user["role"], name=user["name"])
        nxt = request.args.get("next", "")
        return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = get_job_or_404(job_id)
    applied = None
    if session.get("role") == "seeker":
        applied = db().execute("SELECT * FROM applications WHERE job_id = ? AND seeker_id = ?",
                               (job_id, session["user_id"])).fetchone()
    return render_template("job_detail.html", job=job, applied=applied)


def get_job_or_404(job_id):
    job = db().execute("SELECT j.*, u.name AS company FROM jobs j JOIN users u "
                       "ON u.id = j.recruiter_id WHERE j.id = ?", (job_id,)).fetchone()
    if job is None:
        abort(404)
    return job


# ---------------------------------------------------------------- dashboards

@app.route("/dashboard")
@login_required()
def dashboard():
    if session["role"] == "recruiter":
        jobs = db().execute(
            "SELECT j.*, COUNT(a.id) AS applicants, "
            "SUM(CASE WHEN a.score >= ? THEN 1 ELSE 0 END) AS above_threshold "
            "FROM jobs j LEFT JOIN applications a ON a.job_id = j.id "
            "WHERE j.recruiter_id = ? GROUP BY j.id ORDER BY j.created_at DESC, j.id DESC",
            (SHORTLIST_THRESHOLD, session["user_id"])).fetchall()
        return render_template("recruiter_dashboard.html", jobs=jobs)
    apps = db().execute(
        "SELECT a.*, j.title, j.location FROM applications a JOIN jobs j ON j.id = a.job_id "
        "WHERE a.seeker_id = ? ORDER BY a.created_at DESC", (session["user_id"],)).fetchall()
    return render_template("seeker_dashboard.html", apps=apps)


# ---------------------------------------------------------------- recruiter

@app.route("/jobs/new", methods=["GET", "POST"])
@login_required("recruiter")
def new_job():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        try:
            min_exp = float(request.form.get("min_experience") or 0)
        except ValueError:
            min_exp = -1
        if not title or not description or min_exp < 0:
            flash("Title, description and a valid minimum experience are required.")
            return render_template("job_form.html"), 400
        db().execute("INSERT INTO jobs (recruiter_id, title, location, description, min_experience) "
                     "VALUES (?, ?, ?, ?, ?)",
                     (session["user_id"], title, location, description, min_exp))
        db().commit()
        flash("Job posted.")
        return redirect(url_for("dashboard"))
    return render_template("job_form.html")


@app.route("/jobs/<int:job_id>/candidates")
@login_required("recruiter")
def candidates(job_id):
    job = get_job_or_404(job_id)
    if job["recruiter_id"] != session["user_id"]:
        abort(403)
    rows = db().execute(
        "SELECT a.*, u.name, u.email FROM applications a JOIN users u ON u.id = a.seeker_id "
        "WHERE a.job_id = ? ORDER BY a.score DESC", (job_id,)).fetchall()
    only_shortlist = request.args.get("filter") == "shortlist"
    if only_shortlist:
        rows = [r for r in rows if r["score"] >= SHORTLIST_THRESHOLD]
    return render_template("candidates.html", job=job, rows=rows, statuses=STATUSES,
                           only_shortlist=only_shortlist, education_names=EDUCATION_NAMES)


@app.route("/applications/<int:app_id>/status", methods=["POST"])
@login_required("recruiter")
def update_status(app_id):
    row = db().execute("SELECT a.job_id, j.recruiter_id FROM applications a JOIN jobs j "
                       "ON j.id = a.job_id WHERE a.id = ?", (app_id,)).fetchone()
    if row is None:
        abort(404)
    if row["recruiter_id"] != session["user_id"]:
        abort(403)
    status = request.form.get("status")
    if status not in STATUSES:
        abort(400)
    db().execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
    db().commit()
    flash("Status updated.")
    return redirect(url_for("candidates", job_id=row["job_id"]))


@app.route("/applications/<int:app_id>/resume")
@login_required()
def view_resume(app_id):
    row = db().execute("SELECT a.*, j.recruiter_id FROM applications a JOIN jobs j "
                       "ON j.id = a.job_id WHERE a.id = ?", (app_id,)).fetchone()
    if row is None:
        abort(404)
    if session["user_id"] not in (row["recruiter_id"], row["seeker_id"]):
        abort(403)
    return send_from_directory(app.config["UPLOAD_FOLDER"], row["resume_path"], as_attachment=True)


# ---------------------------------------------------------------- job seeker

@app.route("/jobs/<int:job_id>/apply", methods=["GET", "POST"])
@login_required("seeker")
def apply(job_id):
    job = get_job_or_404(job_id)
    if request.method == "POST":
        file = request.files.get("resume")
        ext = Path(file.filename).suffix.lower() if file and file.filename else ""
        if ext not in ALLOWED:
            flash("Upload a PDF, DOCX or TXT resume.")
            return redirect(request.url)
        filename = secure_filename(f"{session['user_id']}_{job_id}{ext}")
        path = Path(app.config["UPLOAD_FOLDER"]) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        file.save(path)
        try:
            text = extract_text(path)
        except Exception:
            path.unlink(missing_ok=True)
            flash("Could not read that file. Please upload a text-based PDF, DOCX or TXT resume.")
            return redirect(request.url)
        if not text.strip():
            path.unlink(missing_ok=True)
            flash("No text found in the resume (scanned images are not supported).")
            return redirect(request.url)

        result = rank_candidates(job["description"], {"self": text},
                                 min_experience=job["min_experience"])[0]
        parsed = parse_resume(text)
        breakdown = result.breakdown()
        breakdown.update(experience_years=parsed["experience_years"],
                         education_level=parsed["education_level"],
                         phone=parsed["phone"], parsed_email=parsed["email"])
        db().execute(
            "INSERT INTO applications (job_id, seeker_id, resume_path, score, breakdown) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(job_id, seeker_id) DO UPDATE SET "
            "resume_path = excluded.resume_path, score = excluded.score, "
            "breakdown = excluded.breakdown, status = 'Applied', created_at = CURRENT_TIMESTAMP",
            (job_id, session["user_id"], filename, result.score, json.dumps(breakdown)))
        db().commit()
        flash(f"Application submitted. Your match score is {result.score:.0f}/100.")
        return redirect(url_for("dashboard"))
    return render_template("apply.html", job=job)


@app.errorhandler(413)
def too_large(_e):
    flash("File is larger than 5 MB.")
    return redirect(request.url)


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
