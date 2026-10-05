from flask import (
    Blueprint, abort, current_app, flash, redirect, render_template, request,
    send_from_directory, url_for,
)
from flask_login import current_user

from . import db
from .ai.matcher import rank_candidates, score_resume
from .models import APPLICATION_STATUSES, JOB_TYPES, Application, Job, User
from .utils import role_required

bp = Blueprint("employer", __name__)


def _own_job_or_404(job_id):
    job = db.get_or_404(Job, job_id)
    if job.employer_id != current_user.id and current_user.role != "admin":
        abort(403)
    return job


def _job_from_form(job):
    form = request.form
    job.title = form.get("title", "").strip()
    job.company = form.get("company", "").strip() or current_user.company or ""
    job.location = form.get("location", "").strip()
    job.job_type = form.get("job_type") if form.get("job_type") in JOB_TYPES else "Full-time"
    job.salary = form.get("salary", "").strip()
    try:
        job.min_experience = max(0, int(form.get("min_experience") or 0))
    except ValueError:
        job.min_experience = 0
    job.required_skills = ", ".join(s.strip() for s in form.get("required_skills", "").split(",") if s.strip())
    job.description = form.get("description", "").strip()
    if not all([job.title, job.company, job.location, job.required_skills, job.description]):
        return "Title, company, location, required skills and description are required."
    return None


@bp.route("/dashboard")
@role_required("employer")
def dashboard():
    jobs = Job.query.filter_by(employer_id=current_user.id).order_by(Job.created_at.desc()).all()
    total_apps = sum(len(j.applications) for j in jobs)
    shortlisted = sum(1 for j in jobs for a in j.applications if a.status == "shortlisted")
    return render_template("employer/dashboard.html", jobs=jobs, total_apps=total_apps, shortlisted=shortlisted)


@bp.route("/jobs/new", methods=["GET", "POST"])
@role_required("employer")
def new_job():
    job = Job(company=current_user.company, min_experience=0)
    if request.method == "POST":
        error = _job_from_form(job)
        if error:
            flash(error, "danger")
        else:
            job.employer_id = current_user.id
            db.session.add(job)
            db.session.commit()
            flash("Job posted successfully.", "success")
            return redirect(url_for("employer.dashboard"))
    return render_template("employer/job_form.html", job=job, job_types=JOB_TYPES, editing=False)


@bp.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@role_required("employer", "admin")
def edit_job(job_id):
    job = _own_job_or_404(job_id)
    if request.method == "POST":
        error = _job_from_form(job)
        if error:
            flash(error, "danger")
        else:
            # Requirements may have changed, so re-screen every applicant.
            for application in job.applications:
                candidate = application.candidate
                application.apply_screening(score_resume(application.resume_text, job, candidate.skill_list))
            db.session.commit()
            flash("Job updated and applicants re-screened.", "success")
            return redirect(url_for("employer.applicants", job_id=job.id))
    return render_template("employer/job_form.html", job=job, job_types=JOB_TYPES, editing=True)


@bp.route("/jobs/<int:job_id>/toggle", methods=["POST"])
@role_required("employer", "admin")
def toggle_job(job_id):
    job = _own_job_or_404(job_id)
    job.is_open = not job.is_open
    db.session.commit()
    flash(f"Job {'reopened' if job.is_open else 'closed'}.", "info")
    return redirect(request.referrer or url_for("employer.dashboard"))


@bp.route("/jobs/<int:job_id>/delete", methods=["POST"])
@role_required("employer", "admin")
def delete_job(job_id):
    job = _own_job_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.", "info")
    if current_user.role == "admin":
        return redirect(url_for("admin.jobs"))
    return redirect(url_for("employer.dashboard"))


@bp.route("/jobs/<int:job_id>/applicants")
@role_required("employer", "admin")
def applicants(job_id):
    job = _own_job_or_404(job_id)
    status = request.args.get("status", "")
    min_score = request.args.get("min_score", type=float) or 0
    apps = [a for a in job.applications if a.match_score >= min_score and (not status or a.status == status)]
    apps.sort(key=lambda a: a.match_score, reverse=True)
    return render_template(
        "employer/applicants.html", job=job, applications=apps,
        statuses=APPLICATION_STATUSES, status=status, min_score=min_score,
    )


@bp.route("/jobs/<int:job_id>/talent")
@role_required("employer", "admin")
def talent_search(job_id):
    """AI candidate matching: rank every candidate on the platform for this job."""
    job = _own_job_or_404(job_id)
    applied_ids = {a.candidate_id for a in job.applications}
    candidates = User.query.filter_by(role="candidate", is_active_account=True).all()
    ranked = rank_candidates(job, candidates)
    return render_template("employer/talent.html", job=job, ranked=ranked[:25], applied_ids=applied_ids)


@bp.route("/applications/<int:app_id>")
@role_required("employer", "admin")
def application_detail(app_id):
    application = db.get_or_404(Application, app_id)
    _own_job_or_404(application.job_id)
    return render_template("employer/application.html", a=application, statuses=APPLICATION_STATUSES)


@bp.route("/applications/<int:app_id>/status", methods=["POST"])
@role_required("employer", "admin")
def update_status(app_id):
    application = db.get_or_404(Application, app_id)
    _own_job_or_404(application.job_id)
    status = request.form.get("status")
    if status not in APPLICATION_STATUSES:
        flash("Invalid status.", "danger")
    else:
        application.status = status
        db.session.commit()
        flash(f"{application.candidate.name} marked as {status}.", "success")
    return redirect(request.referrer or url_for("employer.applicants", job_id=application.job_id))


@bp.route("/jobs/<int:job_id>/auto-shortlist", methods=["POST"])
@role_required("employer", "admin")
def auto_shortlist(job_id):
    """Shortlist every 'applied' candidate at or above a score threshold."""
    job = _own_job_or_404(job_id)
    threshold = request.form.get("threshold", type=float) or 70
    count = 0
    for application in job.applications:
        if application.status == "applied" and application.match_score >= threshold:
            application.status = "shortlisted"
            count += 1
    db.session.commit()
    flash(f"AI auto-shortlisted {count} candidate(s) scoring {threshold:.0f}% or higher.", "success")
    return redirect(url_for("employer.applicants", job_id=job.id))


@bp.route("/resume/<int:app_id>")
@role_required("employer", "admin", "candidate")
def download_resume(app_id):
    application = db.get_or_404(Application, app_id)
    if current_user.role == "candidate":
        if application.candidate_id != current_user.id:
            abort(403)
    else:
        _own_job_or_404(application.job_id)
    if not application.resume_filename:
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], application.resume_filename, as_attachment=True)
