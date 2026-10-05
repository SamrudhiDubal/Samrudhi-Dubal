"""Reset the database and load demo data (admin, employers, candidates, jobs, applications).

Usage:  python seed.py
All demo accounts use the password: password123
"""
import os

from app import create_app, db
from app.ai.matcher import score_resume
from app.models import Application, Job, User

HERE = os.path.dirname(os.path.abspath(__file__))
PASSWORD = "password123"


def resume(filename):
    with open(os.path.join(HERE, "sample_resumes", filename), encoding="utf-8") as fh:
        return fh.read()


def make_user(**fields):
    user = User(**fields)
    user.set_password(PASSWORD)
    db.session.add(user)
    return user


JOBS = [
    dict(title="Machine Learning Engineer", location="Chennai", job_type="Full-time", salary="₹12–18 LPA",
         min_experience=2, required_skills="python, machine learning, deep learning, nlp, tensorflow, scikit-learn, sql, docker",
         description="Design, train and deploy machine learning and NLP models that power our product search and "
                     "recommendation features. Work with large datasets, build data pipelines and serve models via REST APIs."),
    dict(title="Full Stack Developer (React + Node)", location="Bengaluru", job_type="Full-time", salary="₹10–16 LPA",
         min_experience=3, required_skills="javascript, react, node.js, express, mongodb, rest api, git, docker",
         description="Build and maintain modern web applications end-to-end. You will develop responsive React frontends, "
                     "Node.js/Express backends and MongoDB data models, and ship features in an agile team."),
    dict(title="Data Analyst – Graduate Trainee", location="Chennai", job_type="Full-time", salary="₹4–6 LPA",
         min_experience=0, required_skills="sql, excel, power bi, python, data analysis, communication",
         description="Entry-level role for fresh graduates. Analyse business data, build dashboards in Power BI and Excel, "
                     "write SQL queries and present insights to stakeholders."),
    dict(title="DevOps Engineer", location="Hyderabad", job_type="Full-time", salary="₹14–22 LPA",
         min_experience=4, required_skills="aws, docker, kubernetes, terraform, jenkins, ci/cd, linux, python",
         description="Own our cloud infrastructure on AWS. Automate everything with Terraform, maintain Kubernetes clusters "
                     "and build CI/CD pipelines that let developers ship safely many times a day."),
    dict(title="Python Backend Developer Intern", location="Remote", job_type="Internship", salary="₹25,000 / month",
         min_experience=0, required_skills="python, flask, sql, rest api, git",
         description="6-month internship building REST APIs with Python and Flask, writing SQL and unit tests, "
                     "and learning production engineering practices from senior developers."),
]


def run():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        make_user(name="Platform Admin", email="admin@jobmatch.ai", role="admin")
        techsoft = make_user(name="Kavya Reddy", email="hr@techsoft.com", role="employer", company="TechSoft Solutions")
        cloudnine = make_user(name="Vikram Singh", email="talent@cloudnine.io", role="employer", company="CloudNine Systems")

        candidates = [
            make_user(name="Priya Sharma", email="priya@example.com", role="candidate", headline="Data Scientist",
                      location="Chennai", skills="python, machine learning, nlp", resume_filename=None,
                      resume_text=resume("priya_sharma_data_scientist.txt")),
            make_user(name="Rahul Verma", email="rahul@example.com", role="candidate", headline="Full Stack Developer",
                      location="Bengaluru", skills="react, node.js, python",
                      resume_text=resume("rahul_verma_fullstack.txt")),
            make_user(name="Ananya Iyer", email="ananya@example.com", role="candidate", headline="B.Tech CSE final-year student",
                      location="Chennai", skills="python, sql, excel",
                      resume_text=resume("ananya_iyer_fresher.txt")),
            make_user(name="Arjun Nair", email="arjun@example.com", role="candidate", headline="DevOps / Cloud Engineer",
                      location="Hyderabad", skills="aws, kubernetes, terraform",
                      resume_text=resume("arjun_nair_devops.txt")),
        ]

        jobs = []
        for i, spec in enumerate(JOBS):
            employer = techsoft if i % 2 == 0 else cloudnine
            job = Job(company=employer.company, employer=employer, **spec)
            db.session.add(job)
            jobs.append(job)
        db.session.flush()

        # Every candidate applies to a few jobs so the ranked views have data.
        applications = {0: [0, 2, 4], 1: [1, 4, 0], 2: [2, 4, 0, 1], 3: [3, 1]}
        for cand_index, job_indexes in applications.items():
            cand = candidates[cand_index]
            for j in job_indexes:
                job = jobs[j]
                application = Application(job=job, candidate=cand, resume_text=cand.resume_text,
                                          cover_letter=f"I am excited to apply for the {job.title} role.")
                application.apply_screening(score_resume(cand.resume_text, job, cand.skill_list))
                db.session.add(application)

        db.session.commit()
        print(f"Seeded {User.query.count()} users, {Job.query.count()} jobs, {Application.query.count()} applications.")
        print(f"Login with any demo account, password: {PASSWORD}")
        for u in User.query.order_by(User.role).all():
            print(f"  {u.role:<10} {u.email}")


if __name__ == "__main__":
    run()
