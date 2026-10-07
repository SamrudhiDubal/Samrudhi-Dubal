import json
from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def _now():
    return datetime.now(timezone.utc)


def _split_skills(raw):
    return [s.strip().lower() for s in (raw or "").split(",") if s.strip()]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "candidate" | "employer"
    skills = db.Column(db.Text, default="")  # comma-separated, candidates only
    resume_text = db.Column(db.Text, default="")  # latest uploaded resume
    created_at = db.Column(db.DateTime, default=_now)

    jobs = db.relationship("Job", backref="employer", lazy=True, cascade="all, delete-orphan")
    applications = db.relationship(
        "Application", backref="candidate", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def skill_list(self):
        return _split_skills(self.skills)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), default="Remote")
    job_type = db.Column(db.String(20), default="full-time")
    experience_level = db.Column(db.String(20), default="entry")
    description = db.Column(db.Text, nullable=False)
    skills_required = db.Column(db.Text, default="")  # comma-separated
    status = db.Column(db.String(10), default="open")
    employer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=_now)

    applications = db.relationship(
        "Application", backref="job", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def skill_list(self):
        return _split_skills(self.skills_required)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    resume_filename = db.Column(db.String(300))
    resume_text = db.Column(db.Text, default="")
    cover_letter = db.Column(db.Text, default="")
    match_score = db.Column(db.Integer, default=0)
    match_details = db.Column(db.Text, default="{}")  # JSON of MatchResult
    status = db.Column(db.String(20), default="applied")
    created_at = db.Column(db.DateTime, default=_now)

    __table_args__ = (db.UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),)

    @property
    def details(self):
        return json.loads(self.match_details or "{}")
