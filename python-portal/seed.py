"""Populate the database with demo employers, jobs and candidates.

Usage:  python seed.py   (all demo accounts use the password "password123")
"""

from app import create_app
from models import Job, User, db

JOBS = [
    dict(title="Python Backend Developer", company="Acme Corp", location="Pune",
         experience_level="mid", skills_required="python, flask, sql, docker, rest",
         description="Design and build REST APIs in Python/Flask, backed by PostgreSQL, "
                     "deployed with Docker."),
    dict(title="Machine Learning Engineer", company="DataWorks", location="Remote",
         experience_level="senior", skills_required="python, machine learning, pytorch, nlp, aws",
         description="Train and deploy deep learning and NLP models on AWS. "
                     "Own the ML pipeline end to end."),
    dict(title="Frontend Developer (React)", company="Pixel Labs", location="Bengaluru",
         experience_level="entry", skills_required="javascript, react, html, css",
         description="Build responsive UIs with React and modern JavaScript."),
]

CANDIDATES = [
    ("Asha Patil", "asha@example.com", "python, flask, sql",
     "Backend developer with 4 years of experience in Python, Flask, Django, PostgreSQL, "
     "Docker and REST APIs. B.Tech in Computer Science."),
    ("Rahul Mehta", "rahul@example.com", "python, ml",
     "Data scientist with 6 years of experience in machine learning, PyTorch, NLP and AWS. "
     "M.Tech in Artificial Intelligence."),
    ("Neha Joshi", "neha@example.com", "js, react",
     "Fresher frontend developer skilled in JavaScript, React, HTML, CSS and Figma. "
     "Bachelor of Engineering."),
]


def make_user(name, email, role, **extra):
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(name=name, email=email, role=role, **extra)
        user.set_password("password123")
        db.session.add(user)
    return user


def main():
    app = create_app()
    with app.app_context():
        employer = make_user("Demo Employer", "employer@example.com", "employer")
        db.session.flush()
        for job in JOBS:
            if not Job.query.filter_by(title=job["title"]).first():
                db.session.add(Job(employer_id=employer.id, **job))
        for name, email, skills, resume in CANDIDATES:
            make_user(name, email, "candidate", skills=skills, resume_text=resume)
        db.session.commit()
        print("Seeded. Log in as employer@example.com / password123 "
              "or asha@example.com / password123")


if __name__ == "__main__":
    main()
