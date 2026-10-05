"""SQLite persistence for users, resumes, jobs and applications."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from . import config
from .auth import hash_password, verify_password

ROLES = ("candidate", "employer", "admin")
APPLICATION_STATUSES = ("applied", "shortlisted", "rejected", "hired")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('candidate', 'employer', 'admin')),
    company TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS resumes (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT,
    text TEXT NOT NULL,
    predicted_category TEXT,
    category_probs TEXT,
    skills TEXT,
    experience_years REAL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT,
    job_type TEXT,
    min_experience REAL DEFAULT 0,
    salary TEXT,
    description TEXT NOT NULL,
    skills TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    breakdown TEXT NOT NULL,
    cover_letter TEXT,
    status TEXT NOT NULL DEFAULT 'applied',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (job_id, candidate_id)
);
"""


class DuplicateError(ValueError):
    pass


@contextmanager
def connect(path: Path | str | None = None):
    conn = sqlite3.connect(str(path or config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path=None) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)


def _row(row) -> dict | None:
    if row is None:
        return None
    data = dict(row)
    for key in ("skills", "category_probs", "breakdown"):
        if key in data and isinstance(data[key], str):
            data[key] = json.loads(data[key])
    return data


# ---------- users ----------

def create_user(name, email, password, role, company=None, path=None) -> int:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    try:
        with connect(path) as conn:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, role, company) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), email.strip().lower(), hash_password(password), role, company),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError as exc:
        raise DuplicateError("An account with this email already exists") from exc


def authenticate(email, password, path=None) -> dict | None:
    """Return the user if the credentials are valid and the account is active."""
    with connect(path) as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if row and row["is_active"] and verify_password(password, row["password_hash"]):
        user = dict(row)
        user.pop("password_hash")
        return user
    return None


def get_user(user_id, path=None) -> dict | None:
    with connect(path) as conn:
        row = conn.execute(
            "SELECT id, name, email, role, company, is_active, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return _row(row)


def list_users(path=None) -> list[dict]:
    with connect(path) as conn:
        rows = conn.execute(
            "SELECT id, name, email, role, company, is_active, created_at FROM users ORDER BY id"
        ).fetchall()
    return [_row(r) for r in rows]


def set_user_active(user_id, active: bool, path=None) -> None:
    with connect(path) as conn:
        conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (int(active), user_id))


# ---------- resumes ----------

def save_resume(user_id, text, filename, predicted_category, category_probs, skills, experience_years, path=None):
    with connect(path) as conn:
        conn.execute(
            """INSERT INTO resumes (user_id, filename, text, predicted_category, category_probs, skills, experience_years)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET filename=excluded.filename, text=excluded.text,
                 predicted_category=excluded.predicted_category, category_probs=excluded.category_probs,
                 skills=excluded.skills, experience_years=excluded.experience_years,
                 updated_at=CURRENT_TIMESTAMP""",
            (user_id, filename, text, predicted_category, json.dumps(category_probs), json.dumps(skills), experience_years),
        )


def get_resume(user_id, path=None) -> dict | None:
    with connect(path) as conn:
        return _row(conn.execute("SELECT * FROM resumes WHERE user_id = ?", (user_id,)).fetchone())


def list_candidates_with_resumes(path=None) -> list[dict]:
    with connect(path) as conn:
        rows = conn.execute(
            """SELECT u.id AS user_id, u.name, u.email, r.text, r.predicted_category, r.category_probs,
                      r.skills, r.experience_years
               FROM users u JOIN resumes r ON r.user_id = u.id
               WHERE u.role = 'candidate' AND u.is_active = 1"""
        ).fetchall()
    return [_row(r) for r in rows]


# ---------- jobs ----------

def create_job(employer_id, title, company, category, description, skills, location="", job_type="Full-time",
               min_experience=0, salary="", path=None) -> int:
    if not title.strip() or not description.strip():
        raise ValueError("Title and description are required")
    with connect(path) as conn:
        cur = conn.execute(
            """INSERT INTO jobs (employer_id, title, company, category, location, job_type, min_experience,
                                 salary, description, skills)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (employer_id, title.strip(), company, category, location, job_type, min_experience, salary,
             description.strip(), json.dumps([s.strip().lower() for s in skills if s.strip()])),
        )
        return cur.lastrowid


def get_job(job_id, path=None) -> dict | None:
    with connect(path) as conn:
        return _row(conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())


def list_jobs(status="open", employer_id=None, path=None) -> list[dict]:
    sql, args = "SELECT * FROM jobs WHERE 1=1", []
    if status:
        sql += " AND status = ?"
        args.append(status)
    if employer_id:
        sql += " AND employer_id = ?"
        args.append(employer_id)
    with connect(path) as conn:
        rows = conn.execute(sql + " ORDER BY id DESC", args).fetchall()
    return [_row(r) for r in rows]


def set_job_status(job_id, status, path=None) -> None:
    if status not in ("open", "closed"):
        raise ValueError("status must be open or closed")
    with connect(path) as conn:
        conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))


def delete_job(job_id, path=None) -> None:
    with connect(path) as conn:
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))


# ---------- applications ----------

def create_application(job_id, candidate_id, score, breakdown, cover_letter="", path=None) -> int:
    try:
        with connect(path) as conn:
            cur = conn.execute(
                "INSERT INTO applications (job_id, candidate_id, score, breakdown, cover_letter) VALUES (?, ?, ?, ?, ?)",
                (job_id, candidate_id, int(score), json.dumps(breakdown), cover_letter),
            )
            return cur.lastrowid
    except sqlite3.IntegrityError as exc:
        raise DuplicateError("You have already applied to this job") from exc


def list_applications_for_job(job_id, path=None) -> list[dict]:
    with connect(path) as conn:
        rows = conn.execute(
            """SELECT a.*, u.name AS candidate_name, u.email AS candidate_email
               FROM applications a JOIN users u ON u.id = a.candidate_id
               WHERE a.job_id = ? ORDER BY a.score DESC, a.created_at""",
            (job_id,),
        ).fetchall()
    return [_row(r) for r in rows]


def list_applications_for_candidate(candidate_id, path=None) -> list[dict]:
    with connect(path) as conn:
        rows = conn.execute(
            """SELECT a.*, j.title AS job_title, j.company, j.status AS job_status
               FROM applications a JOIN jobs j ON j.id = a.job_id
               WHERE a.candidate_id = ? ORDER BY a.created_at DESC""",
            (candidate_id,),
        ).fetchall()
    return [_row(r) for r in rows]


def set_application_status(application_id, status, path=None) -> None:
    if status not in APPLICATION_STATUSES:
        raise ValueError(f"status must be one of {APPLICATION_STATUSES}")
    with connect(path) as conn:
        conn.execute("UPDATE applications SET status = ? WHERE id = ?", (status, application_id))


def application_status_counts(path=None) -> list[dict]:
    with connect(path) as conn:
        rows = conn.execute("SELECT status, COUNT(*) AS n FROM applications GROUP BY status").fetchall()
    return [dict(r) for r in rows]


def stats(path=None) -> dict:
    with connect(path) as conn:
        one = lambda sql: conn.execute(sql).fetchone()[0]  # noqa: E731
        return {
            "candidates": one("SELECT COUNT(*) FROM users WHERE role = 'candidate'"),
            "employers": one("SELECT COUNT(*) FROM users WHERE role = 'employer'"),
            "open_jobs": one("SELECT COUNT(*) FROM jobs WHERE status = 'open'"),
            "applications": one("SELECT COUNT(*) FROM applications"),
            "avg_score": round(one("SELECT COALESCE(AVG(score), 0) FROM applications")),
            "shortlisted": one("SELECT COUNT(*) FROM applications WHERE status IN ('shortlisted', 'hired')"),
            "by_category": [dict(r) for r in conn.execute(
                "SELECT predicted_category AS category, COUNT(*) AS n FROM resumes GROUP BY 1 ORDER BY 2 DESC")],
        }
