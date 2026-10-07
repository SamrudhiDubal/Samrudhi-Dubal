"""Job Portal with AI-Based Resume Screening and Candidate Matching (single file).

Usage:
    pip install scikit-learn pypdf python-docx
    python job_portal.py          # interactive menu
    python job_portal.py --demo   # load sample data and show AI rankings
"""

import hashlib
import json
import os
import re
import sqlite3
import sys

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "job_portal.db")

# ============================================================== AI MATCHING ENGINE

SKILL_WEIGHT, TEXT_WEIGHT, EXPERIENCE_WEIGHT = 0.5, 0.25, 0.25
LEVEL_MIN_YEARS = {"entry": 0, "mid": 2, "senior": 5, "lead": 8}

SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "php", "ruby",
    "kotlin", "swift", "sql", "html", "css", "react.js", "angular", "vue.js", "node.js",
    "express.js", "django", "flask", "fastapi", "spring boot", ".net", "rest", "graphql",
    "microservices", "mongodb", "mysql", "postgresql", "redis", "amazon web services", "azure",
    "google cloud", "docker", "kubernetes", "terraform", "jenkins", "linux", "git", "devops",
    "machine learning", "deep learning", "natural language processing", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "data analysis",
    "data science", "spark", "tableau", "power bi", "artificial intelligence", "android",
    "ios", "flutter", "selenium", "pytest", "agile", "scrum", "figma", "communication",
    "leadership", "project management", "cybersecurity",
]

ALIASES = {
    "js": "javascript", "ts": "typescript", "react": "react.js", "reactjs": "react.js",
    "node": "node.js", "nodejs": "node.js", "vue": "vue.js", "express": "express.js",
    "postgres": "postgresql", "mongo": "mongodb", "k8s": "kubernetes", "aws": "amazon web services",
    "gcp": "google cloud", "ml": "machine learning", "dl": "deep learning",
    "nlp": "natural language processing", "ai": "artificial intelligence", "golang": "go",
    "cpp": "c++", "csharp": "c#", "restful": "rest", "rest api": "rest", "sklearn": "scikit-learn",
}

YEARS_PATTERNS = [
    re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:professional\s*)?experience", re.I),
    re.compile(r"experience\s*(?:of)?\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I),
    re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s*(?:in|as|working)", re.I),
]

EDUCATION = [
    ("PhD", ["ph.d", "phd", "doctorate"]),
    ("Master", ["master of", "master's", "msc", "m.sc", "mba", "m.tech", "mtech"]),
    ("Bachelor", ["bachelor", "bsc", "b.sc", "b.tech", "btech", "b.e."]),
    ("Diploma", ["diploma", "associate degree"]),
]


def canonical(skill):
    s = skill.lower().strip()
    return ALIASES.get(s, s)


def has_term(text, term):
    return re.search(r"(?:^|[^a-z0-9])" + re.escape(term) + r"(?:$|[^a-z0-9+#])", text) is not None


def extract_skills(text):
    text = (text or "").lower()
    found = {s for s in SKILLS if has_term(text, s)}
    found |= {c for alias, c in ALIASES.items() if has_term(text, alias)}
    return sorted(found)


def extract_years(text):
    years = [int(m.group(1)) for p in YEARS_PATTERNS for m in p.finditer(text or "")]
    years = [y for y in years if y <= 50]
    return max(years) if years else None


def extract_education(text):
    text = (text or "").lower()
    for level, keywords in EDUCATION:
        if any(k in text for k in keywords):
            return level
    return None


def text_similarity(a, b):
    if not (a or "").strip() or not (b or "").strip():
        return 0.0
    try:
        tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        m = tfidf.fit_transform([a, b])
    except ValueError:
        return 0.0
    return float(cosine_similarity(m[0], m[1])[0][0])


def experience_fit(years, level):
    if years is None:
        return None
    need = LEVEL_MIN_YEARS.get(level, 0)
    return 100 if need == 0 or years >= need else round(years / need * 100)


def screen_resume(resume_text, job, declared_skills=()):
    """Score a resume against a job dict. Returns a dict with score 0-100 and details."""
    job_skills = sorted({canonical(s) for s in job["skills"] if s.strip()})
    cand_skills = set(extract_skills(resume_text)) | {canonical(s) for s in declared_skills if s.strip()}

    matched = [s for s in job_skills if s in cand_skills]
    missing = [s for s in job_skills if s not in cand_skills]
    skill_pct = 100 if not job_skills else round(len(matched) / len(job_skills) * 100)

    job_text = f"{job['title']} {job['description']} {' '.join(job_skills)}"
    text_pct = round(text_similarity(resume_text, job_text) * 100)

    years = extract_years(resume_text)
    exp_pct = experience_fit(years, job["level"])

    if exp_pct is None:  # unknown experience: spread its weight over the other signals
        total = SKILL_WEIGHT + TEXT_WEIGHT
        score = (SKILL_WEIGHT * skill_pct + TEXT_WEIGHT * text_pct) / total
    else:
        score = SKILL_WEIGHT * skill_pct + TEXT_WEIGHT * text_pct + EXPERIENCE_WEIGHT * exp_pct

    return {
        "score": max(0, min(100, round(score))),
        "skill_match": skill_pct,
        "text_similarity": text_pct,
        "experience_fit": exp_pct,
        "years": years,
        "education": extract_education(resume_text),
        "matched_skills": matched,
        "missing_skills": missing,
    }


# ============================================================== RESUME READING

def read_resume(path):
    path = path.strip().strip('"')
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
    if ext == ".docx":
        import docx
        return "\n".join(p.text for p in docx.Document(path).paragraphs)
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


# ============================================================== DATABASE

def connect(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, password TEXT,
            role TEXT, skills TEXT DEFAULT '', resume TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY, employer_id INTEGER, title TEXT, company TEXT,
            location TEXT, level TEXT, skills TEXT, description TEXT, status TEXT DEFAULT 'open');
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY, job_id INTEGER, candidate_id INTEGER, score INTEGER,
            details TEXT, status TEXT DEFAULT 'applied', UNIQUE(job_id, candidate_id));
    """)
    return conn


def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


def split(csv):
    return [s.strip().lower() for s in (csv or "").split(",") if s.strip()]


def job_dict(row):
    return {"title": row["title"], "description": row["description"],
            "skills": split(row["skills"]), "level": row["level"]}


def register(conn, name, email, password, role, skills="", resume=""):
    cur = conn.execute(
        "INSERT INTO users (name, email, password, role, skills, resume) VALUES (?,?,?,?,?,?)",
        (name, email.lower(), hash_pw(password), role, skills, resume))
    conn.commit()
    return cur.lastrowid


def login(conn, email, password):
    return conn.execute("SELECT * FROM users WHERE email=? AND password=?",
                        (email.lower(), hash_pw(password))).fetchone()


def post_job(conn, employer_id, title, company, location, level, skills, description):
    cur = conn.execute(
        "INSERT INTO jobs (employer_id, title, company, location, level, skills, description) "
        "VALUES (?,?,?,?,?,?,?)", (employer_id, title, company, location, level, skills, description))
    conn.commit()
    return cur.lastrowid


def search_jobs(conn, keyword="", skill=""):
    rows = conn.execute(
        "SELECT * FROM jobs WHERE status='open' AND (title LIKE ? OR description LIKE ? OR company LIKE ?)",
        (f"%{keyword}%",) * 3).fetchall()
    return [r for r in rows if not skill or canonical(skill) in map(canonical, split(r["skills"]))]


def apply(conn, job_id, candidate):
    job = conn.execute("SELECT * FROM jobs WHERE id=? AND status='open'", (job_id,)).fetchone()
    if not job:
        raise ValueError("Job not found or closed.")
    if not candidate["resume"]:
        raise ValueError("Upload a resume first.")
    result = screen_resume(candidate["resume"], job_dict(job), split(candidate["skills"]))
    try:
        conn.execute("INSERT INTO applications (job_id, candidate_id, score, details) VALUES (?,?,?,?)",
                     (job_id, candidate["id"], result["score"], json.dumps(result)))
    except sqlite3.IntegrityError:
        raise ValueError("You already applied to this job.")
    conn.commit()
    return result


def ranked_applicants(conn, job_id):
    """AI resume screening: applicants for a job, best match first."""
    return conn.execute(
        "SELECT a.*, u.name, u.email FROM applications a JOIN users u ON u.id=a.candidate_id "
        "WHERE a.job_id=? ORDER BY a.score DESC", (job_id,)).fetchall()


def match_candidates(conn, job_id):
    """AI candidate matching: rank every candidate with a resume, applied or not."""
    job = job_dict(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())
    cands = conn.execute("SELECT * FROM users WHERE role='candidate' AND resume != ''").fetchall()
    results = [(c, screen_resume(c["resume"], job, split(c["skills"]))) for c in cands]
    return sorted(results, key=lambda x: x[1]["score"], reverse=True)


def recommend_jobs(conn, candidate):
    """Open jobs ranked by fit for a candidate."""
    jobs = conn.execute("SELECT * FROM jobs WHERE status='open'").fetchall()
    results = [(j, screen_resume(candidate["resume"], job_dict(j), split(candidate["skills"])))
               for j in jobs]
    return sorted(results, key=lambda x: x[1]["score"], reverse=True)


# ============================================================== CONSOLE UI

def show_result(r):
    exp = f"{r['experience_fit']}%" if r["experience_fit"] is not None else "n/a"
    print(f"    Score {r['score']}/100 | skills {r['skill_match']}% | text {r['text_similarity']}% "
          f"| experience {exp} ({r['years'] or '?'} yrs) | education {r['education'] or '?'}")
    print(f"    matched: {', '.join(r['matched_skills']) or '-'}")
    print(f"    missing: {', '.join(r['missing_skills']) or '-'}")


def list_jobs(rows):
    if not rows:
        print("  No jobs found.")
    for j in rows:
        print(f"  [{j['id']}] {j['title']} @ {j['company']} ({j['location']}, {j['level']}) "
              f"- skills: {j['skills']} [{j['status']}]")


def candidate_menu(conn, user):
    while True:
        user = conn.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
        print(f"\n--- Candidate: {user['name']} ---")
        print("1. Upload resume  2. Update skills  3. Search jobs  4. AI job recommendations")
        print("5. Apply to job   6. My applications  0. Logout")
        c = input("> ").strip()
        try:
            if c == "1":
                text = read_resume(input("Resume file path (.pdf/.docx/.txt): "))
                conn.execute("UPDATE users SET resume=? WHERE id=?", (text, user["id"]))
                conn.commit()
                print("Resume saved. Detected skills:", ", ".join(extract_skills(text)) or "none")
            elif c == "2":
                conn.execute("UPDATE users SET skills=? WHERE id=?",
                             (input("Skills (comma-separated): "), user["id"]))
                conn.commit()
            elif c == "3":
                list_jobs(search_jobs(conn, input("Keyword: "), input("Skill (optional): ")))
            elif c == "4":
                if not user["resume"]:
                    print("Upload a resume first.")
                    continue
                for job, r in recommend_jobs(conn, user):
                    print(f"  [{job['id']}] {job['title']} @ {job['company']}")
                    show_result(r)
            elif c == "5":
                r = apply(conn, int(input("Job id: ")), user)
                print("Applied! AI screening result:")
                show_result(r)
            elif c == "6":
                for a in conn.execute(
                        "SELECT a.*, j.title FROM applications a JOIN jobs j ON j.id=a.job_id "
                        "WHERE candidate_id=?", (user["id"],)):
                    print(f"  {a['title']}: score {a['score']}/100, status {a['status']}")
            elif c == "0":
                return
        except (ValueError, OSError) as e:
            print("Error:", e)


def employer_menu(conn, user):
    while True:
        print(f"\n--- Employer: {user['name']} ---")
        print("1. Post job  2. My jobs  3. Ranked applicants  4. AI candidate matches")
        print("5. Update application status  6. Close/reopen job  0. Logout")
        c = input("> ").strip()
        try:
            if c == "1":
                level = input("Level (entry/mid/senior/lead): ").strip().lower()
                post_job(conn, user["id"], input("Title: "), input("Company: "),
                         input("Location: ") or "Remote",
                         level if level in LEVEL_MIN_YEARS else "entry",
                         input("Required skills (comma-separated): "), input("Description: "))
                print("Job posted.")
            elif c == "2":
                list_jobs(conn.execute("SELECT * FROM jobs WHERE employer_id=?", (user["id"],)).fetchall())
            elif c == "3":
                for i, a in enumerate(ranked_applicants(conn, int(input("Job id: "))), 1):
                    print(f"  #{i} [app {a['id']}] {a['name']} <{a['email']}> - {a['status']}")
                    show_result(json.loads(a["details"]))
            elif c == "4":
                for cand, r in match_candidates(conn, int(input("Job id: "))):
                    print(f"  {cand['name']} <{cand['email']}>")
                    show_result(r)
            elif c == "5":
                status = input("New status (shortlisted/rejected/hired): ").strip()
                conn.execute("UPDATE applications SET status=? WHERE id=?",
                             (status, int(input("Application id: "))))
                conn.commit()
            elif c == "6":
                conn.execute("UPDATE jobs SET status=CASE status WHEN 'open' THEN 'closed' ELSE 'open' END "
                             "WHERE id=? AND employer_id=?", (int(input("Job id: ")), user["id"]))
                conn.commit()
            elif c == "0":
                return
        except ValueError as e:
            print("Error:", e)


def main_menu(conn):
    while True:
        print("\n===== AI JOB PORTAL =====")
        print("1. Register  2. Login  3. Browse jobs  0. Exit")
        c = input("> ").strip()
        if c == "1":
            role = input("Role (candidate/employer): ").strip().lower()
            if role not in ("candidate", "employer"):
                print("Invalid role.")
                continue
            try:
                register(conn, input("Name: "), input("Email: "), input("Password: "), role)
                print("Registered. Please log in.")
            except sqlite3.IntegrityError:
                print("Email already registered.")
        elif c == "2":
            user = login(conn, input("Email: "), input("Password: "))
            if not user:
                print("Invalid credentials.")
            elif user["role"] == "candidate":
                candidate_menu(conn, user)
            else:
                employer_menu(conn, user)
        elif c == "3":
            list_jobs(search_jobs(conn))
        elif c == "0":
            break


# ============================================================== DEMO

def demo():
    conn = connect(":memory:")
    emp = register(conn, "Acme HR", "hr@acme.com", "pass", "employer")
    jobs = [
        post_job(conn, emp, "Python Backend Developer", "Acme", "Pune", "mid",
                 "python, flask, sql, docker, rest",
                 "Build REST APIs in Python and Flask with PostgreSQL, deployed using Docker."),
        post_job(conn, emp, "Machine Learning Engineer", "Acme", "Remote", "senior",
                 "python, machine learning, pytorch, nlp, aws",
                 "Train and deploy deep learning and NLP models on AWS."),
        post_job(conn, emp, "Frontend Developer", "Acme", "Bengaluru", "entry",
                 "javascript, react, html, css", "Build responsive UIs with React."),
    ]
    people = [
        ("Asha", "python, flask", "Backend developer with 4 years of experience in Python, Flask, "
         "Django, PostgreSQL, Docker and REST APIs. B.Tech in Computer Science."),
        ("Rahul", "python, ml", "Data scientist with 6 years of experience in machine learning, "
         "PyTorch, NLP and AWS. M.Tech in AI."),
        ("Neha", "js, react", "Fresher frontend developer skilled in JavaScript, React, HTML, CSS."),
    ]
    for name, skills, resume in people:
        cid = register(conn, name, f"{name.lower()}@mail.com", "pass", "candidate", skills, resume)
        cand = conn.execute("SELECT * FROM users WHERE id=?", (cid,)).fetchone()
        for jid in jobs:
            apply(conn, jid, cand)

    for jid in jobs:
        title = conn.execute("SELECT title FROM jobs WHERE id=?", (jid,)).fetchone()["title"]
        print(f"\n=== Ranked applicants: {title} ===")
        for i, a in enumerate(ranked_applicants(conn, jid), 1):
            print(f"  #{i} {a['name']}")
            show_result(json.loads(a["details"]))


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        main_menu(connect())
