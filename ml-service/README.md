# AI Candidate Matching Service (Python)

An explainable, AI-based candidate-matching engine written in Python. It
scores how well a candidate fits a job (and vice versa) by blending five
independent signals into one 0-100 match score, and exposes the engine as
a standalone library, a CLI, and a REST API — so it can run on its own or
be called from the existing Node/Express job portal in this repo.

## How matching works

`matcher/core.py` blends:

| Signal | Weight | What it measures |
| --- | --- | --- |
| Required-skill overlap | 40% | Job's must-have skills found in the resume or candidate profile |
| Preferred-skill overlap | 10% | "Nice to have" skills found, as a bonus |
| Experience fit | 15% | Candidate's years of experience vs. the job's experience level |
| Location fit | 10% | Remote-friendliness / geographic match |
| Semantic text similarity | 25% | TF-IDF cosine similarity between resume and job description, so topically-aligned resumes score well even without exact keyword matches |

Every result includes a plain-English `explanation` list (matched/missing
skills, experience fit, location fit) so the score is transparent, not a
black box. Skills are detected from free-form resume text against a
curated skills dictionary (`matcher/skills.py`), and years of experience
are extracted with regex heuristics (`matcher/experience.py`) when not
explicitly provided.

The same engine works in both directions:
- **`rank_candidates(job, candidates)`** — an employer's ranked-applicants view.
- **`recommend_jobs(candidate, jobs)`** — a candidate's job-recommendations view.

## Project layout

```
ml-service/
  matcher/
    core.py             Job/Candidate models + compute_match/rank_candidates/recommend_jobs
    skills.py           Curated skills dictionary + extraction
    experience.py        Years-of-experience extraction + experience-level scoring
    location.py          Location-fit scoring
    text_similarity.py   TF-IDF cosine similarity (falls back to plain TF cosine)
    resume_parser.py     PDF/DOCX/TXT -> plain text extraction
  app.py                 FastAPI REST service
  cli.py                 Command-line interface
  tests/test_matcher.py  pytest suite
  requirements.txt
  requirements-dev.txt
```

## Setup

```bash
cd ml-service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Running the tests

```bash
python -m pytest tests/ -v
```

## Using the CLI

```bash
python cli.py match --job job.json --candidate candidate.json
python cli.py rank --job job.json --candidates candidates.json      # candidates.json is a JSON array
python cli.py recommend --candidate candidate.json --jobs jobs.json  # jobs.json is a JSON array
```

Example `job.json`:

```json
{
  "id": "job1",
  "title": "Backend Engineer",
  "description": "Build and scale REST APIs for a growing fintech product.",
  "required_skills": ["python", "django", "postgresql"],
  "preferred_skills": ["docker", "aws"],
  "experience_level": "mid",
  "location": "Remote"
}
```

Example `candidate.json`:

```json
{
  "id": "c1",
  "name": "Asha",
  "resume_text": "Backend engineer with 4 years of experience building REST APIs in Python using Django and PostgreSQL. Deployed services with Docker on AWS.",
  "declared_skills": ["python", "django"],
  "location": "Remote"
}
```

## Running the API

```bash
uvicorn app:app --reload --port 8000
```

| Method | Route | Description |
| --- | --- | --- |
| GET | `/health` | Liveness check |
| POST | `/api/match` | Score one candidate against one job |
| POST | `/api/rank-candidates` | Rank many candidates for one job |
| POST | `/api/recommend-jobs` | Rank many jobs for one candidate |
| POST | `/api/parse-resume` | Upload a resume file (PDF/DOCX/TXT); returns extracted text + detected skills |

`POST /api/match` request body:

```json
{
  "job": { "title": "...", "description": "...", "required_skills": ["python"], "experience_level": "mid", "location": "Remote" },
  "candidate": { "resume_text": "...", "declared_skills": ["python"], "location": "Remote" }
}
```

## Integrating with the Node/Express backend in this repo

This service is independent of `backend/` (which already has a JavaScript
matching engine in `backend/utils/aiMatcher.js`). To use this Python engine
instead — e.g. to take advantage of scikit-learn's TF-IDF vectorizer or to
extend it with heavier NLP/ML models later — call it as an HTTP microservice
from the Node backend (e.g. with `axios.post('http://ml-service:8000/api/match', ...)`
inside `applicationController.js`) rather than merging the two codebases.
