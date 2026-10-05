from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from . import db
from .ai.matcher import recommend_jobs
from .ai.skills import extract_education, extract_skills, extract_years_experience
from .models import Application, Job
from .utils import role_required, save_resume

bp = Blueprint("candidate", __name__)


@bp.route("/dashboard")
@role_required("candidate")
def dashboard():
    apps = (
        Application.query.filter_by(candidate_id=current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    applied_ids = {a.job_id for a in apps}
    recommendations = []
    if current_user.resume_text or current_user.skill_list:
        open_jobs = [j for j in Job.query.filter_by(is_open=True).all() if j.id not in applied_ids]
        recommendations = recommend_jobs(current_user, open_jobs, limit=5)
    return render_template("candidate/dashboard.html", applications=apps, recommendations=recommendations)


@bp.route("/profile", methods=["GET", "POST"])
@role_required("candidate")
def profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip() or current_user.name
        current_user.headline = request.form.get("headline", "").strip()
        current_user.location = request.form.get("location", "").strip()
        current_user.skills = ", ".join(
            s.strip() for s in request.form.get("skills", "").split(",") if s.strip()
        )
        upload = request.files.get("resume")
        if upload and upload.filename:
            try:
                current_user.resume_filename, current_user.resume_text = save_resume(upload)
            except ValueError as exc:
                flash(str(exc), "danger")
                return redirect(url_for("candidate.profile"))
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("candidate.profile"))

    analysis = None
    if current_user.resume_text:
        text = current_user.resume_text
        analysis = {
            "skills": extract_skills(text),
            "years": extract_years_experience(text),
            "education": extract_education(text),
            "words": len(text.split()),
        }
    return render_template("candidate/profile.html", analysis=analysis)


@bp.route("/applications/<int:app_id>")
@role_required("candidate")
def application_detail(app_id):
    application = db.get_or_404(Application, app_id)
    if application.candidate_id != current_user.id:
        abort(403)
    return render_template("candidate/application.html", a=application)


@bp.route("/applications/<int:app_id>/withdraw", methods=["POST"])
@role_required("candidate")
def withdraw(app_id):
    application = db.get_or_404(Application, app_id)
    if application.candidate_id != current_user.id:
        abort(403)
    db.session.delete(application)
    db.session.commit()
    flash("Application withdrawn.", "info")
    return redirect(url_for("candidate.dashboard"))
