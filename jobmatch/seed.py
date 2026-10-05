"""Create demo accounts, jobs and AI-scored applications.

    python -m jobmatch.seed --reset

Demo candidates use resumes from the held-out test set, so the demo
screens resumes the models never saw during training. For a clear demo, each
candidate gets the first test resume of their category that the model
classifies correctly; about 14% of test resumes are misclassified (see the
Model Performance page). All demo accounts use the password `demo1234`.
"""

from __future__ import annotations

import argparse
import json

import pandas as pd

from . import config, db
from .experience import extract_experience_years
from .matcher import MatchingService
from .models import get_classifier
from .skills import extract_skills

PASSWORD = "demo1234"

EMPLOYERS = [
    ("Priya Sharma", "talent@nimbus.example.com", "Nimbus Technologies"),
    ("Arjun Mehta", "hiring@crestview.example.com", "Crestview Capital"),
    ("Kavya Nair", "careers@brightminds.example.com", "Bright Minds Group"),
]

# (name, email, category of the test-set resume to use, which jobs to apply to by category)
CANDIDATES = [
    ("Ananya Iyer", "ananya@example.com", "INFORMATION-TECHNOLOGY", ["INFORMATION-TECHNOLOGY", "CONSULTANT"]),
    ("Rahul Verma", "rahul@example.com", "FINANCE", ["FINANCE", "BANKING", "ACCOUNTANT"]),
    ("Sneha Reddy", "sneha@example.com", "HR", ["HR"]),
    ("Karthik Raman", "karthik@example.com", "ACCOUNTANT", ["ACCOUNTANT", "FINANCE"]),
    ("Meera Pillai", "meera@example.com", "TEACHER", ["TEACHER"]),
    ("Vikram Singh", "vikram@example.com", "SALES", ["SALES", "BUSINESS-DEVELOPMENT"]),
    ("Fatima Khan", "fatima@example.com", "DESIGNER", ["DESIGNER", "DIGITAL-MEDIA"]),
    ("Rohan Das", "rohan@example.com", "CHEF", ["CHEF"]),
    ("Divya Menon", "divya@example.com", "HEALTHCARE", ["HEALTHCARE", "FITNESS"]),
    ("Aditya Kulkarni", "aditya@example.com", "ENGINEERING", ["ENGINEERING", "CONSTRUCTION"]),
    ("Nisha Agarwal", "nisha@example.com", "BANKING", ["BANKING", "FINANCE"]),
    ("Sanjay Gupta", "sanjay@example.com", "BUSINESS-DEVELOPMENT", ["BUSINESS-DEVELOPMENT", "SALES"]),
    ("Lakshmi Krishnan", "lakshmi@example.com", "ADVOCATE", ["ADVOCATE"]),
    ("Imran Sheikh", "imran@example.com", "AVIATION", ["AVIATION"]),
    ("Pooja Bhatt", "pooja@example.com", "PUBLIC-RELATIONS", ["PUBLIC-RELATIONS", "DIGITAL-MEDIA"]),
    ("Arun Joseph", "arun@example.com", "CONSTRUCTION", ["CONSTRUCTION"]),
]



def seed(reset: bool = False, path=None) -> dict:
    db_path = path or config.DB_PATH
    if reset and db_path.exists():
        db_path.unlink()
    db.init_db(db_path)
    if db.list_users(path=db_path):
        return {"skipped": True}

    clf = get_classifier()
    service = MatchingService(clf)
    metrics = json.loads(config.METRICS_PATH.read_text())
    df = pd.read_csv(config.RESUME_DATASET).drop_duplicates("Resume_str").reset_index(drop=True)
    test = df.loc[metrics["test_rows"]]

    db.create_user("Platform Admin", "admin@example.com", PASSWORD, "admin", path=db_path)
    employer_ids = [db.create_user(n, e, PASSWORD, "employer", company=c, path=db_path) for n, e, c in EMPLOYERS]

    jobs = json.loads(config.JOBS_SEED_FILE.read_text())
    job_ids = {}
    for i, job in enumerate(jobs):
        job_ids[job["category"]] = db.create_job(
            employer_ids[i % len(employer_ids)], job["title"], job["company"], job["category"], job["description"],
            job["skills"], job["location"], job["job_type"], job["min_experience"], job["salary"], path=db_path)

    candidate_resumes = []
    for name, email, category, _ in CANDIDATES:
        uid = db.create_user(name, email, PASSWORD, "candidate", path=db_path)
        pool = test[test.Category == category].Resume_str
        text = next((t for t in pool if clf.predict(t)["category"] == category), pool.iloc[0])
        pred = clf.predict(text)
        years = extract_experience_years(text)
        db.save_resume(uid, text, f"{name.split()[0].lower()}_resume.txt", pred["category"],
                       pred["probabilities"], extract_skills(text), years, path=db_path)
        candidate_resumes.append((uid, text, pred["probabilities"], years))

    applications = 0
    by_job: dict[int, list[tuple[int, int]]] = {}
    for (uid, text, probs, years), (_n, _e, _c, targets) in zip(candidate_resumes, CANDIDATES):
        for cat in targets:
            job = db.get_job(job_ids[cat], path=db_path)
            ranked = service.rank_candidates(job, [{"text": text, "category_probs": probs, "experience_years": years}])
            match = ranked[0][1]
            app_id = db.create_application(job["id"], uid, match["score"], match, path=db_path)
            by_job.setdefault(job["id"], []).append((match["score"], app_id))
            applications += 1
    for apps in by_job.values():
        best_score, best_app = max(apps)
        if best_score >= 60:
            db.set_application_status(best_app, "shortlisted", path=db_path)

    return {"employers": len(EMPLOYERS), "candidates": len(CANDIDATES), "jobs": len(jobs), "applications": applications}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create demo data")
    parser.add_argument("--reset", action="store_true", help="delete the existing database first")
    result = seed(reset=parser.parse_args().reset)
    print("Database already has data (use --reset to recreate)." if result.get("skipped") else
          f"Demo data created: {result}. Password for every account: {PASSWORD}")
