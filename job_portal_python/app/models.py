import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager

ROLES = ("candidate", "employer", "admin")
JOB_TYPES = ("Full-time", "Part-time", "Internship", "Contract", "Remote")
APPLICATION_STATUSES = ("applied", "shortlisted", "interview", "rejected", "hired")


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="candidate")
    is_active_account = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Candidate profile
    headline = db.Column(db.String(200))
    location = db.Column(db.String(120))
    skills = db.Column(db.Text, default="")  # comma-separated, declared by the candidate
    resume_filename = db.Column(db.String(255))
    resume_text = db.Column(db.Text)

    # Employer profile
    company = db.Column(db.String(150))

    jobs = db.relationship("Job", backref="employer", lazy=True, cascade="all, delete-orphan")
    applications = db.relationship(
        "Application", backref="candidate", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return bool(self.is_active_account)

    @property
    def skill_list(self):
        return [s.strip() for s in (self.skills or "").split(",") if s.strip()]


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    company = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    job_type = db.Column(db.String(30), default="Full-time")
    salary = db.Column(db.String(60))
    min_experience = db.Column(db.Integer, default=0)  # years
    required_skills = db.Column(db.Text, nullable=False)  # comma-separated
    description = db.Column(db.Text, nullable=False)
    is_open = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    employer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    applications = db.relationship(
        "Application", backref="job", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def skill_list(self):
        return [s.strip() for s in (self.required_skills or "").split(",") if s.strip()]


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    cover_letter = db.Column(db.Text)
    resume_filename = db.Column(db.String(255))
    resume_text = db.Column(db.Text)
    status = db.Column(db.String(20), default="applied")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # AI screening results
    match_score = db.Column(db.Float, default=0)
    skill_score = db.Column(db.Float)
    text_score = db.Column(db.Float)
    experience_score = db.Column(db.Float)
    years_experience = db.Column(db.Float)
    education = db.Column(db.String(50))
    matched_skills = db.Column(db.Text, default="[]")  # JSON list
    missing_skills = db.Column(db.Text, default="[]")  # JSON list
    recommendation = db.Column(db.String(30))

    __table_args__ = (db.UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),)

    @property
    def matched_skill_list(self):
        return json.loads(self.matched_skills or "[]")

    @property
    def missing_skill_list(self):
        return json.loads(self.missing_skills or "[]")

    def apply_screening(self, result):
        """Copy a MatchResult (from app.ai.matcher) onto this application."""
        self.match_score = result.score
        self.skill_score = result.skill_score
        self.text_score = result.text_score
        self.experience_score = result.experience_score
        self.years_experience = result.years_experience
        self.education = result.education
        self.matched_skills = json.dumps(result.matched_skills)
        self.missing_skills = json.dumps(result.missing_skills)
        self.recommendation = result.recommendation
