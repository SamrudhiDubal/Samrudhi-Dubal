"""Load demo data: one recruiter, the six job descriptions and 8 job seekers with resumes.

Usage:  python seed_demo.py      (run eval/generate_dataset.py first)
Logins: recruiter hr@demo.com / demo123   ·   job seekers c0@demo.com ... c7@demo.com / demo123
"""

import json
import random
from pathlib import Path

from werkzeug.security import generate_password_hash

import app as portal
from screening import parse_resume, rank_candidates

DATA = Path(__file__).resolve().parent / "eval" / "data"


def main():
    if not (DATA / "jobs.json").exists():
        raise SystemExit("Run `python -m eval.generate_dataset` first.")
    jobs = json.loads((DATA / "jobs.json").read_text())
    resumes = json.loads((DATA / "resumes.json").read_text())
    rng = random.Random(7)
    with portal.app.app_context():
        db = portal.db()
        if db.execute("SELECT 1 FROM users WHERE email = 'hr@demo.com'").fetchone():
            raise SystemExit("Demo data already loaded.")
        pw = generate_password_hash("demo123")
        rid = db.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'recruiter')",
                         ("Qollabb Talent Team", "hr@demo.com", pw)).lastrowid
        job_ids = [db.execute("INSERT INTO jobs (recruiter_id, title, location, description, min_experience) "
                              "VALUES (?, ?, ?, ?, ?)",
                              (rid, j["title"], j["location"], j["description"], j["min_experience"])).lastrowid
                   for j in jobs]
        # 8 seekers apply to the first job (Python Backend Developer): a mix of strong, partial and other
        py = [r for r in resumes if r["family"] == jobs[0]["title"]]
        pool = [r for r in py if r["kind"] == "strong"][:3] + [r for r in py if r["kind"] == "partial"][:3] \
            + rng.sample([r for r in resumes if r["family"] != jobs[0]["title"]], 2)
        uploads = Path(portal.app.config["UPLOAD_FOLDER"])
        uploads.mkdir(exist_ok=True)
        for i, r in enumerate(pool):
            name = r["text"].split("\n")[0]
            sid = db.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, 'seeker')",
                             (name, f"c{i}@demo.com", pw)).lastrowid
            fname = f"{sid}_{job_ids[0]}.txt"
            (uploads / fname).write_text(r["text"])
            res = rank_candidates(jobs[0]["description"], {"self": r["text"]},
                                  min_experience=jobs[0]["min_experience"])[0]
            p = parse_resume(r["text"])
            b = res.breakdown()
            b.update(experience_years=p["experience_years"], education_level=p["education_level"],
                     phone=p["phone"], parsed_email=p["email"])
            db.execute("INSERT INTO applications (job_id, seeker_id, resume_path, score, breakdown) "
                       "VALUES (?, ?, ?, ?, ?)", (job_ids[0], sid, fname, res.score, json.dumps(b)))
        db.commit()
    print("Demo data loaded. Recruiter: hr@demo.com / demo123, seekers: c0..c7@demo.com / demo123")


if __name__ == "__main__":
    main()
