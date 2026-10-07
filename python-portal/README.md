# JobMatch AI — Python Edition

A Python (Flask) job portal with **AI-based resume screening and candidate
matching**. Runs fully locally: SQLite database, scikit-learn for text
similarity, no API keys needed.

## Features

- **Accounts & roles** — candidates and employers (Flask-Login, hashed passwords).
- **Job postings** — employers create, edit, close/reopen and delete jobs;
  anyone can search by keyword, location, skill, job type and experience level.
- **Resume upload & parsing** — PDF (`pypdf`), DOCX (`python-docx`) or TXT.
- **AI resume screening** — every application is scored 0–100 on submit.
- **Ranked applicants** — employers see applicants sorted by score with
  matched/missing skills, experience and education, filter by a minimum
  score, and set status (applied / shortlisted / rejected / hired).
- **AI candidate matching** — employers can rank *every* candidate with a
  resume on file against a job, including people who haven't applied.
- **AI job recommendations** — candidates see open jobs ranked by fit, plus a
  match preview on each job page before applying.
- **JSON API** — `POST /api/match` scores raw resume text against a job spec.

## How the match score works (`matcher.py`)

| Signal | Weight | How |
| --- | --- | --- |
| Skill overlap | 50% | Job skills found in the resume (curated dictionary + aliases like `js`→`javascript`, `k8s`→`kubernetes`) or the candidate's profile skills |
| Text similarity | 25% | TF-IDF (unigrams + bigrams) cosine similarity between resume and job title/description/skills |
| Experience fit | 25% | Years detected in the resume ("5 years of experience") vs. the level's minimum (entry 0, mid 2, senior 5, lead 8) |

If the resume doesn't mention years of experience, that weight is
redistributed over the other two signals rather than penalizing the
candidate. Education level (PhD / Master / Bachelor / …) is detected and
shown to employers but not scored.

## Run it

```bash
cd python-portal
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed.py      # optional demo data (password: password123)
python app.py       # http://127.0.0.1:5000
```

Demo logins after seeding: `employer@example.com`, `asha@example.com`,
`rahul@example.com`, `neha@example.com`.

Config via environment variables: `SECRET_KEY` (set this in production),
`DATABASE_URL` (defaults to `sqlite:///jobportal.db`).

### API example

```bash
curl -X POST http://127.0.0.1:5000/api/match -H 'Content-Type: application/json' -d '{
  "resume_text": "Python developer with 5 years of experience in Flask and SQL",
  "title": "Backend Engineer", "description": "Build Flask APIs",
  "skills_required": ["python", "flask", "docker"], "experience_level": "mid"}'
```

## Tests

```bash
pytest tests
```

## Layout

```
app.py             Flask app factory and all routes
models.py          SQLAlchemy models: User, Job, Application
matcher.py         AI screening / matching engine
resume_parser.py   PDF / DOCX / TXT text extraction
seed.py            demo data
templates/         Jinja2 + Bootstrap pages
tests/             pytest suite (matcher unit tests + app flow tests)
```

Note: forms have no CSRF protection; add Flask-WTF/CSRFProtect before
deploying publicly.
