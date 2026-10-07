"""JobMatch AI (Python) - job portal with AI-based resume screening and candidate matching.

Run:  python app.py   ->  http://127.0.0.1:5000
"""

import json
import os
import uuid
from functools import wraps

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import (
    LoginManager, current_user, login_required, login_user, logout_user,
)
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from matcher import compute_match
from models import Application, Job, User, db
from resume_parser import allowed_file, extract_text

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

JOB_TYPES = ["full-time", "part-time", "contract", "internship"]
EXPERIENCE_LEVELS = ["entry", "mid", "senior", "lead"]
APPLICATION_STATUSES = ["applied", "shortlisted", "rejected", "hired"]


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "jobportal.db")
        ),
        UPLOAD_FOLDER=os.path.join(BASE_DIR, "uploads"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # 5 MB resumes
    )
    if config:
        app.config.update(config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager = LoginManager(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def save_resume(file_storage, upload_folder):
    """Save an uploaded resume and return (stored_filename, extracted_text)."""
    if not file_storage or not file_storage.filename:
        return None, None
    if not allowed_file(file_storage.filename):
        raise ValueError("Resume must be a PDF, DOCX, or TXT file.")
    filename = f"{uuid.uuid4().hex}_{secure_filename(file_storage.filename)}"
    path = os.path.join(upload_folder, filename)
    file_storage.save(path)
    text = extract_text(path)
    if not text.strip():
        raise ValueError("Could not read any text from that resume.")
    return filename, text


def match_job(job, resume_text, declared_skills=None):
    return compute_match(
        resume_text, job.title, job.description, job.skill_list,
        job.experience_level, declared_skills,
    )


def get_owned_job(job_id):
    job = db.get_or_404(Job, job_id)
    if job.employer_id != current_user.id:
        abort(403)
    return job


def register_routes(app):
    # ---------------------------------------------------------------- auth
    @app.route("/")
    def index():
        latest = Job.query.filter_by(status="open").order_by(Job.created_at.desc()).limit(6).all()
        return render_template("index.html", jobs=latest)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            role = request.form.get("role", "candidate")
            if not name or not email or len(password) < 6 or role not in ("candidate", "employer"):
                flash("Please fill all fields (password at least 6 characters).", "danger")
            elif User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "danger")
            else:
                user = User(name=name, email=email, role=role)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash(f"Welcome, {user.name}!", "success")
                return redirect(url_for("profile" if role == "candidate" else "employer_jobs"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(request.form.get("password", "")):
                login_user(user)
                return redirect(request.args.get("next") or url_for("jobs"))
            flash("Invalid email or password.", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("index"))

    # ---------------------------------------------------------------- profile
    @app.route("/profile", methods=["GET", "POST"])
    @role_required("candidate")
    def profile():
        if request.method == "POST":
            current_user.name = request.form.get("name", current_user.name).strip()
            current_user.skills = request.form.get("skills", "")
            try:
                _, text = save_resume(request.files.get("resume"), app.config["UPLOAD_FOLDER"])
                if text:
                    current_user.resume_text = text
            except ValueError as exc:
                flash(str(exc), "danger")
                return redirect(url_for("profile"))
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("recommendations"))
        return render_template("profile.html")

    # ---------------------------------------------------------------- jobs
    @app.route("/jobs")
    def jobs():
        query = Job.query.filter_by(status="open")
        q = request.args.get("q", "").strip()
        location = request.args.get("location", "").strip()
        job_type = request.args.get("job_type", "")
        level = request.args.get("level", "")
        skill = request.args.get("skill", "").strip().lower()
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Job.title.ilike(like), Job.description.ilike(like),
                                     Job.company.ilike(like)))
        if location:
            query = query.filter(Job.location.ilike(f"%{location}%"))
        if job_type:
            query = query.filter_by(job_type=job_type)
        if level:
            query = query.filter_by(experience_level=level)
        results = query.order_by(Job.created_at.desc()).all()
        if skill:
            results = [j for j in results if skill in j.skill_list]
        return render_template("jobs.html", jobs=results, job_types=JOB_TYPES,
                               levels=EXPERIENCE_LEVELS, args=request.args)

    @app.route("/jobs/<int:job_id>")
    def job_detail(job_id):
        job = db.get_or_404(Job, job_id)
        preview, existing = None, None
        if current_user.is_authenticated and current_user.role == "candidate":
            existing = Application.query.filter_by(job_id=job.id,
                                                   candidate_id=current_user.id).first()
            if current_user.resume_text:
                preview = match_job(job, current_user.resume_text, current_user.skill_list)
        return render_template("job_detail.html", job=job, preview=preview, existing=existing)

    @app.route("/jobs/new", methods=["GET", "POST"])
    @role_required("employer")
    def job_new():
        if request.method == "POST":
            job = Job(employer_id=current_user.id)
            if fill_job_from_form(job):
                db.session.add(job)
                db.session.commit()
                flash("Job posted.", "success")
                return redirect(url_for("employer_jobs"))
        return render_template("job_form.html", job=None, job_types=JOB_TYPES,
                               levels=EXPERIENCE_LEVELS)

    @app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
    @role_required("employer")
    def job_edit(job_id):
        job = get_owned_job(job_id)
        if request.method == "POST" and fill_job_from_form(job):
            db.session.commit()
            flash("Job updated.", "success")
            return redirect(url_for("employer_jobs"))
        return render_template("job_form.html", job=job, job_types=JOB_TYPES,
                               levels=EXPERIENCE_LEVELS)

    @app.route("/jobs/<int:job_id>/toggle", methods=["POST"])
    @role_required("employer")
    def job_toggle(job_id):
        job = get_owned_job(job_id)
        job.status = "closed" if job.status == "open" else "open"
        db.session.commit()
        return redirect(url_for("employer_jobs"))

    @app.route("/jobs/<int:job_id>/delete", methods=["POST"])
    @role_required("employer")
    def job_delete(job_id):
        db.session.delete(get_owned_job(job_id))
        db.session.commit()
        flash("Job deleted.", "info")
        return redirect(url_for("employer_jobs"))

    @app.route("/employer/jobs")
    @role_required("employer")
    def employer_jobs():
        my_jobs = Job.query.filter_by(employer_id=current_user.id) \
            .order_by(Job.created_at.desc()).all()
        return render_template("employer_jobs.html", jobs=my_jobs)

    # ---------------------------------------------------------------- applications
    @app.route("/jobs/<int:job_id>/apply", methods=["POST"])
    @role_required("candidate")
    def apply(job_id):
        job = db.get_or_404(Job, job_id)
        if job.status != "open":
            flash("This job is no longer accepting applications.", "warning")
            return redirect(url_for("job_detail", job_id=job.id))
        if Application.query.filter_by(job_id=job.id, candidate_id=current_user.id).first():
            flash("You have already applied to this job.", "warning")
            return redirect(url_for("job_detail", job_id=job.id))
        try:
            filename, text = save_resume(request.files.get("resume"), app.config["UPLOAD_FOLDER"])
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("job_detail", job_id=job.id))
        if text:
            current_user.resume_text = text  # keep profile resume up to date
        else:
            text = current_user.resume_text
        if not text:
            flash("Please upload a resume to apply.", "danger")
            return redirect(url_for("job_detail", job_id=job.id))

        result = match_job(job, text, current_user.skill_list)
        application = Application(
            job_id=job.id, candidate_id=current_user.id, resume_filename=filename,
            resume_text=text, cover_letter=request.form.get("cover_letter", ""),
            match_score=result.score, match_details=json.dumps(result.to_dict()),
        )
        db.session.add(application)
        db.session.commit()
        flash(f"Application submitted! Your AI match score: {result.score}/100", "success")
        return redirect(url_for("my_applications"))

    @app.route("/my/applications")
    @role_required("candidate")
    def my_applications():
        apps = Application.query.filter_by(candidate_id=current_user.id) \
            .order_by(Application.created_at.desc()).all()
        return render_template("my_applications.html", applications=apps)

    @app.route("/jobs/<int:job_id>/applicants")
    @role_required("employer")
    def applicants(job_id):
        job = get_owned_job(job_id)
        min_score = request.args.get("min_score", type=int, default=0)
        ranked = Application.query.filter_by(job_id=job.id) \
            .filter(Application.match_score >= min_score) \
            .order_by(Application.match_score.desc()).all()
        return render_template("applicants.html", job=job, applications=ranked,
                               statuses=APPLICATION_STATUSES, min_score=min_score)

    @app.route("/applications/<int:app_id>/status", methods=["POST"])
    @role_required("employer")
    def update_status(app_id):
        application = db.get_or_404(Application, app_id)
        if application.job.employer_id != current_user.id:
            abort(403)
        status = request.form.get("status")
        if status in APPLICATION_STATUSES:
            application.status = status
            db.session.commit()
        return redirect(url_for("applicants", job_id=application.job_id))

    # ---------------------------------------------------------------- AI matching
    @app.route("/jobs/<int:job_id>/matches")
    @role_required("employer")
    def candidate_matches(job_id):
        """Proactive candidate matching: rank every candidate with a profile
        resume against this job, whether or not they have applied."""
        job = get_owned_job(job_id)
        applied_ids = {a.candidate_id for a in job.applications}
        candidates = User.query.filter(User.role == "candidate", User.resume_text != "").all()
        ranked = sorted(
            ((c, match_job(job, c.resume_text, c.skill_list)) for c in candidates),
            key=lambda pair: pair[1].score, reverse=True,
        )
        return render_template("matches.html", job=job, ranked=ranked, applied_ids=applied_ids)

    @app.route("/recommendations")
    @role_required("candidate")
    def recommendations():
        if not current_user.resume_text:
            flash("Upload a resume on your profile to get AI job recommendations.", "info")
            return redirect(url_for("profile"))
        open_jobs = Job.query.filter_by(status="open").all()
        ranked = sorted(
            ((j, match_job(j, current_user.resume_text, current_user.skill_list))
             for j in open_jobs),
            key=lambda pair: pair[1].score, reverse=True,
        )
        return render_template("recommendations.html", ranked=ranked)

    @app.route("/api/match", methods=["POST"])
    def api_match():
        """Stateless JSON endpoint: score raw resume text against a job spec."""
        data = request.get_json(silent=True) or {}
        if not data.get("resume_text") or not data.get("description"):
            return jsonify(error="resume_text and description are required"), 400
        skills = data.get("skills_required", [])
        if isinstance(skills, str):
            skills = skills.split(",")
        result = compute_match(
            data["resume_text"], data.get("title", ""), data["description"], skills,
            data.get("experience_level", "entry"), data.get("declared_skills"),
        )
        return jsonify(result.to_dict())

    @app.errorhandler(403)
    def forbidden(_):
        return render_template("error.html", code=403, message="You don't have access to that."), 403

    @app.errorhandler(404)
    def not_found(_):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(413)
    def too_large(_):
        return render_template("error.html", code=413, message="File too large (max 5 MB)."), 413


def fill_job_from_form(job):
    form = request.form
    title, company, description = (form.get(k, "").strip() for k in ("title", "company", "description"))
    if not title or not company or not description:
        flash("Title, company and description are required.", "danger")
        return False
    job.title, job.company, job.description = title, company, description
    job.location = form.get("location", "").strip() or "Remote"
    job.job_type = form.get("job_type") if form.get("job_type") in JOB_TYPES else "full-time"
    job.experience_level = form.get("experience_level") \
        if form.get("experience_level") in EXPERIENCE_LEVELS else "entry"
    job.skills_required = ", ".join(s.strip().lower() for s in form.get("skills_required", "").split(",") if s.strip())
    return True


if __name__ == "__main__":
    create_app().run(debug=True)
