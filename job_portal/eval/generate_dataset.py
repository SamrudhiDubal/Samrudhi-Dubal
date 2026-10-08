"""Generate the controlled, labelled test dataset (Section 3.4 of the report).

Six job families; for each: 10 strong resumes, 12 partial resumes, plus 18
keyword-stuffed resumes overall (each job description targeted by exactly 3).
A fixed random seed makes the dataset reproducible.

Usage:  python -m eval.generate_dataset      (from the job_portal folder)
Writes: eval/data/jobs.json, eval/data/resumes.json
"""

import json
import random
from pathlib import Path

SEED = 42
OUT = Path(__file__).resolve().parent / "data"

FIRST = ["Aarav", "Diya", "Rohan", "Sneha", "Vivaan", "Ananya", "Kabir", "Isha", "Arjun", "Meera",
         "Siddharth", "Priya", "Aditya", "Neha", "Kunal", "Pooja", "Rahul", "Tanvi", "Yash", "Riya"]
LAST = ["Sharma", "Patil", "Iyer", "Nair", "Deshmukh", "Pawar", "Shinde", "Kulkarni", "Joshi",
        "Mehta", "Reddy", "Gupta", "Kapoor", "Rao", "Jain"]

# Each family: required skills (canonical) with alternative ways of writing them,
# responsibilities, minimum experience and minimum education (1 diploma .. 4 PhD).
FAMILIES = {
    "Python Backend Developer": {
        "skills": {"python": ["Python", "Python3"], "django": ["Django", "Django REST Framework"],
                   "flask": ["Flask"], "rest api": ["REST API", "RESTful services"],
                   "sql": ["SQL", "PostgreSQL", "MySQL"], "git": ["Git", "GitHub"],
                   "docker": ["Docker", "containerization"], "aws": ["AWS", "Amazon Web Services"]},
        "duties": ["built and maintained backend services and APIs", "designed database schemas and wrote optimised queries",
                   "wrote unit tests and reviewed code", "deployed microservices to the cloud",
                   "integrated third-party payment and messaging services"],
        "min_exp": 2, "edu": 2, "qual": "B.Tech or equivalent", "location": "Pune (Hybrid)",
    },
    "Data Analyst": {
        "skills": {"sql": ["SQL", "MySQL", "T-SQL"], "excel": ["Excel", "Advanced Excel"],
                   "python": ["Python"], "pandas": ["pandas"], "power bi": ["Power BI", "PowerBI"],
                   "statistics": ["statistics", "statistical analysis"],
                   "data visualization": ["data visualization", "data visualisation"],
                   "tableau": ["Tableau"]},
        "duties": ["prepared weekly business dashboards", "cleaned and analysed sales data",
                   "presented insights to managers", "automated MIS reports",
                   "performed cohort and trend analysis"],
        "min_exp": 1, "edu": 2, "qual": "B.Sc or equivalent", "location": "Remote",
    },
    "DevOps Engineer": {
        "skills": {"aws": ["AWS", "EC2"], "docker": ["Docker"], "kubernetes": ["Kubernetes", "k8s", "EKS"],
                   "ci/cd": ["CI/CD", "Jenkins", "GitHub Actions"], "terraform": ["Terraform", "infrastructure as code"],
                   "linux": ["Linux", "Ubuntu"], "shell scripting": ["shell scripting", "Bash"],
                   "monitoring": ["monitoring", "Prometheus", "Grafana"]},
        "duties": ["managed cloud infrastructure and deployment pipelines", "reduced release time by automating builds",
                   "maintained production clusters with high availability", "handled incident response and on-call",
                   "hardened servers and managed access policies"],
        "min_exp": 3, "edu": 2, "qual": "B.E. or equivalent", "location": "Bengaluru",
    },
    "QA Engineer": {
        "skills": {"selenium": ["Selenium", "Selenium WebDriver"], "manual testing": ["manual testing", "functional testing"],
                   "automation testing": ["automation testing", "test automation"], "jira": ["JIRA", "defect tracking"],
                   "api testing": ["API testing", "Postman"], "sql": ["SQL", "MySQL"],
                   "pytest": ["pytest", "TestNG"], "agile": ["Agile", "Scrum"]},
        "duties": ["wrote and executed test plans for web releases", "logged and tracked defects to closure",
                   "built regression suites for every sprint", "validated backend data with queries",
                   "worked with developers to reproduce production issues"],
        "min_exp": 2, "edu": 2, "qual": "B.Tech or equivalent", "location": "Hyderabad",
    },
    "HR Executive": {
        "skills": {"recruitment": ["recruitment", "Talent Acquisition"], "onboarding": ["onboarding", "induction"],
                   "payroll": ["payroll", "payroll processing"],
                   "employee engagement": ["employee engagement", "employee relations"],
                   "hrms": ["HRMS", "Workday"], "labour law": ["labour law", "statutory compliance"],
                   "performance management": ["performance management", "appraisals"],
                   "excel": ["MS Excel", "Excel"]},
        "duties": ["managed end-to-end hiring for business teams", "coordinated joining formalities for new employees",
                   "maintained employee records and attendance", "organised engagement and wellness activities",
                   "handled employee queries and exit formalities"],
        "min_exp": 2, "edu": 3, "qual": "MBA in HR or equivalent", "location": "Mumbai",
    },
    "Digital Marketing Executive": {
        "skills": {"seo": ["SEO", "search engine optimization"], "sem": ["SEM", "Google Ads"],
                   "social media marketing": ["social media marketing", "Meta Ads"],
                   "content marketing": ["content marketing", "copywriting"],
                   "google analytics": ["Google Analytics", "GA4"], "email marketing": ["email marketing", "Mailchimp"],
                   "excel": ["Excel"], "communication": ["communication skills", "communication"]},
        "duties": ["planned and ran paid campaigns for product launches", "grew organic website traffic",
                   "managed brand pages and posting calendars", "wrote blogs and landing page copy",
                   "reported campaign performance to stakeholders"],
        "min_exp": 1, "edu": 2, "qual": "BBA or any graduate", "location": "Pune",
    },
}

# Closely related families: a strong resume from one is a partial fit for the other (label 1).
RELATED = {("Python Backend Developer", "DevOps Engineer"), ("DevOps Engineer", "Python Backend Developer"),
           ("QA Engineer", "Python Backend Developer")}

EDU_TEXT = {1: "Diploma in {}", 2: "B.Tech in {}", 3: "MBA in {}", 4: "PhD in {}"}
EDU_FIELD = {"Python Backend Developer": "Computer Science", "Data Analyst": "Statistics",
             "DevOps Engineer": "Information Technology", "QA Engineer": "Computer Engineering",
             "HR Executive": "Human Resources", "Digital Marketing Executive": "Marketing"}


def job_description(title, fam):
    skills = ", ".join(fam["skills"])
    duties = "; ".join(fam["duties"])
    return (f"We are hiring a {title}. Minimum {fam['min_exp']} years of experience. "
            f"Required skills: {skills}. Responsibilities: {duties}. Qualification: {fam['qual']}.")


def write_skill(rng, canon, alts):
    """About half of the skills are written with a synonym or alternative term."""
    return rng.choice(alts[1:]) if len(alts) > 1 and rng.random() < 0.5 else alts[0]


def make_resume(rng, rid, family, kind):
    fam = FAMILIES[family]
    canon = list(fam["skills"])
    if kind in ("strong", "stuffed"):  # a stuffed resume is a genuine strong resume of its own family
        n_skills = rng.randint(6, 8)
        years = round(fam["min_exp"] + rng.uniform(0.5, 4.0), 1)
        edu = fam["edu"] if rng.random() < 0.8 else min(fam["edu"] + 1, 4)
    else:  # partial
        n_skills = rng.randint(2, 4)
        years = round(rng.uniform(0.2, max(fam["min_exp"] * 0.6, 0.4)), 1)
        edu = 1 if rng.random() < 0.4 else max(fam["edu"] - 1, 1)
    chosen = rng.sample(canon, n_skills)
    skill_words = [write_skill(rng, c, fam["skills"][c]) for c in chosen]
    duties = rng.sample(fam["duties"], 3)
    name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
    email = f"{name.split()[0].lower()}.{rid.lower()}@example.com"
    phone = f"9{rng.randint(100000000, 999999999)}"
    text = "\n".join([
        name, f"Email: {email} | Phone: +91 {phone[:5]} {phone[5:]}", "",
        f"Summary: {family} with {years} years of experience.", "",
        "Skills: " + ", ".join(skill_words), "",
        "Experience:", *[f"- {d.capitalize()}." for d in duties], "",
        "Education: " + EDU_TEXT[edu].format(EDU_FIELD[family]),
    ])
    return {"id": rid, "family": family, "kind": kind, "text": text,
            "truth": {"email": email, "phone": phone, "experience_years": years,
                      "education_level": edu, "skills": sorted(chosen)}}


def main():
    rng = random.Random(SEED)
    titles = list(FAMILIES)
    jobs = [{"id": f"J{i + 1}", "title": t, "location": FAMILIES[t]["location"],
             "description": job_description(t, FAMILIES[t]), "min_experience": FAMILIES[t]["min_exp"],
             "min_education": FAMILIES[t]["edu"], "skills": list(FAMILIES[t]["skills"])}
            for i, t in enumerate(titles)]

    resumes, n = [], 0
    for family in titles:
        for kind, count in (("strong", 10), ("partial", 12)):
            for _ in range(count):
                n += 1
                resumes.append(make_resume(rng, f"R{n:03d}", family, kind))

    # 18 keyword-stuffed resumes: a genuine strong resume from an unrelated family
    # plus a line of keywords copied from the targeted job description.
    for target in titles:
        sources = [f for f in titles if f != target and (f, target) not in RELATED]
        for source in rng.sample(sources, 3):
            n += 1
            r = make_resume(rng, f"R{n:03d}", source, "stuffed")
            r["text"] += "\n\nKeywords: " + ", ".join(FAMILIES[target]["skills"])
            r["target"] = target
            resumes.append(r)

    # Ground-truth labels (Table 3.2)
    for r in resumes:
        r["labels"] = {}
        for job in jobs:
            t = job["title"]
            if r["family"] == t and r["kind"] in ("strong", "stuffed"):
                label = 2
            elif r["family"] == t and r["kind"] == "partial":
                label = 1
            elif (r["family"], t) in RELATED and r["kind"] in ("strong", "stuffed") and r.get("target") != t:
                label = 1
            else:
                label = 0
            r["labels"][job["id"]] = label

    OUT.mkdir(exist_ok=True)
    (OUT / "jobs.json").write_text(json.dumps(jobs, indent=2))
    (OUT / "resumes.json").write_text(json.dumps(resumes, indent=2))
    print(f"Wrote {len(jobs)} jobs and {len(resumes)} resumes to {OUT}")


if __name__ == "__main__":
    main()
