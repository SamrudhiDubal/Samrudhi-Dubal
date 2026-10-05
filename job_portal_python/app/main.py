from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from . import db
from .ai.matcher import score_resume
from .models import JOB_TYPES, Application, Job, User
from .utils import role_required, save_resume

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    latest = Job.query.filter_by(is_open=True).order_by(Job.created_at.desc()).limit(6).all()
    stats = {
        "jobs": Job.query.filter_by(is_open=True).count(),
        "companies": db.session.query(Job.company).distinct().count(),
        "candidates": User.query.filter_by(role="candidate").count(),
        "applications": Application.query.count(),
    }
    return render_template("index.html", jobs=latest, stats=stats)


@bp.route("/jobs")
def jobs():
    q = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    job_type = request.args.get("job_type", "")

    query = Job.query.filter_by(is_open=True)
    if q:
        like = f"%{q}%"
        query = query.filter(
            Job.title.ilike(like)
            | Job.description.ilike(like)
            | Job.required_skills.ilike(like)
            | Job.company.ilike(like)
        )
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if job_type in JOB_TYPES:
        query = query.filter_by(job_type=job_type)

    results = query.order_by(Job.created_at.desc()).all()
    return render_template(
        "jobs/list.html", jobs=results, job_types=JOB_TYPES,
        q=q, location=location, job_type=job_type,
    )


@bp.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = db.get_or_404(Job, job_id)
    if not job.is_open and not (
        current_user.is_authenticated
        and (current_user.id == job.employer_id or current_user.role == "admin")
    ):
        abort(404)

    existing = preview = None
    if current_user.is_authenticated and current_user.role == "candidate":
        existing = Application.query.filter_by(job_id=job.id, candidate_id=current_user.id).first()
        if not existing and (current_user.resume_text or current_user.skill_list):
            preview = score_resume(current_user.resume_text, job, current_user.skill_list)
    return render_template("jobs/detail.html", job=job, existing=existing, preview=preview)


@bp.route("/jobs/<int:job_id>/apply", methods=["POST"])
@role_required("candidate")
def apply(job_id):
    job = db.get_or_404(Job, job_id)
    if not job.is_open:
        flash("This job is no longer accepting applications.", "warning")
        return redirect(url_for("main.job_detail", job_id=job.id))
    if Application.query.filter_by(job_id=job.id, candidate_id=current_user.id).first():
        flash("You have already applied to this job.", "info")
        return redirect(url_for("main.job_detail", job_id=job.id))

    upload = request.files.get("resume")
    if upload and upload.filename:
        try:
            stored, text = save_resume(upload)
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("main.job_detail", job_id=job.id))
        # Keep the profile resume up to date for job recommendations.
        current_user.resume_filename, current_user.resume_text = stored, text
    elif current_user.resume_text:
        stored, text = current_user.resume_filename, current_user.resume_text
    else:
        flash("Please upload a resume to apply.", "danger")
        return redirect(url_for("main.job_detail", job_id=job.id))

    application = Application(
        job_id=job.id,
        candidate_id=current_user.id,
        cover_letter=request.form.get("cover_letter", "").strip(),
        resume_filename=stored,
        resume_text=text,
    )
    result = score_resume(text, job, current_user.skill_list)
    application.apply_screening(result)
    db.session.add(application)
    db.session.commit()

    flash(f"Application submitted! AI match score: {result.score:.0f}% ({result.recommendation}).", "success")
    return redirect(url_for("candidate.application_detail", app_id=application.id))
