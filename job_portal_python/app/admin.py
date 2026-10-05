from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func

from . import db
from .models import Application, Job, User
from .utils import role_required

bp = Blueprint("admin", __name__)


@bp.route("/")
@role_required("admin")
def dashboard():
    stats = {
        "candidates": User.query.filter_by(role="candidate").count(),
        "employers": User.query.filter_by(role="employer").count(),
        "jobs": Job.query.count(),
        "open_jobs": Job.query.filter_by(is_open=True).count(),
        "applications": Application.query.count(),
        "avg_score": db.session.query(func.avg(Application.match_score)).scalar() or 0,
    }
    by_status = dict(
        db.session.query(Application.status, func.count(Application.id)).group_by(Application.status).all()
    )
    buckets = {"75-100": 0, "50-74": 0, "30-49": 0, "0-29": 0}
    for (score,) in db.session.query(Application.match_score).all():
        if score >= 75:
            buckets["75-100"] += 1
        elif score >= 50:
            buckets["50-74"] += 1
        elif score >= 30:
            buckets["30-49"] += 1
        else:
            buckets["0-29"] += 1
    recent = Application.query.order_by(Application.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, by_status=by_status, buckets=buckets, recent=recent)


@bp.route("/users")
@role_required("admin")
def users():
    role = request.args.get("role", "")
    q = request.args.get("q", "").strip()
    query = User.query
    if role:
        query = query.filter_by(role=role)
    if q:
        query = query.filter(User.name.ilike(f"%{q}%") | User.email.ilike(f"%{q}%"))
    return render_template("admin/users.html", users=query.order_by(User.created_at.desc()).all(), role=role, q=q)


@bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You can't deactivate your own account.", "warning")
    else:
        user.is_active_account = not user.is_active_account
        db.session.commit()
        flash(f"{user.name} {'activated' if user.is_active_account else 'deactivated'}.", "info")
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@role_required("admin")
def delete_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You can't delete your own account.", "warning")
    else:
        db.session.delete(user)  # cascades to their jobs and applications
        db.session.commit()
        flash("User deleted.", "info")
    return redirect(url_for("admin.users"))


@bp.route("/jobs")
@role_required("admin")
def jobs():
    return render_template("admin/jobs.html", jobs=Job.query.order_by(Job.created_at.desc()).all())
