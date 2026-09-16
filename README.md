# JobMatch AI — Full-Stack Job Portal with AI-Based Resume Screening

A full-stack job portal (MERN-style: MongoDB, Express, React, Node.js) where
candidates apply to jobs and an AI resume-screening engine automatically
scores every application against the job's requirements — no external API
key required.

## Features

- **Auth & roles** — JWT-based auth with `candidate` and `employer` roles.
- **Job postings** — Employers create, edit, close/reopen, and delete job
  listings. Candidates search/filter jobs by keyword, location, job type,
  experience level, and required skill.
- **Resume upload & parsing** — Candidates upload a resume (`PDF`, `DOCX`,
  `DOC`, or `TXT`); the server extracts plain text server-side.
- **AI-based resume screening & candidate matching** — Every application is
  scored 0–100 by a matching engine (`backend/utils/aiMatcher.js`) that
  blends two signals:
  1. **Skill overlap** — skills detected in the resume (via a curated
     skills dictionary) plus the candidate's declared profile skills,
     compared against the job's required skills.
  2. **Semantic text similarity** — TF cosine similarity between the resume
     text and the job description, so resumes that are topically aligned
     score well even without exact keyword matches.
- **Ranked applicant view** — Employers see every applicant for a job
  sorted by AI match score, with matched/missing skills and a similarity
  breakdown, and can update each applicant's status
  (`applied` → `shortlisted` / `rejected` / `hired`).
- **Candidate dashboard** — Track submitted applications and see your own
  match score per job.

## Tech Stack

- **Backend**: Node.js, Express, MongoDB (Mongoose), JWT auth, Multer file
  uploads, `pdf-parse` / `mammoth` for resume text extraction.
- **Frontend**: React (Vite), React Router, Tailwind CSS, Axios.
- **ML service** (`ml-service/`): a standalone Python AI matching engine
  (FastAPI + scikit-learn) — see [`ml-service/README.md`](ml-service/README.md).

## Project Structure

```
backend/
  config/db.js            MongoDB connection
  models/                 User, Job, Application schemas
  middleware/              auth (JWT), role guard, multer upload, error handler
  utils/
    resumeParser.js        PDF/DOCX/TXT -> plain text extraction
    skillsDictionary.js     curated skill keyword list + extractor
    aiMatcher.js             AI screening/matching engine (skills + TF cosine similarity)
  controllers/, routes/    REST API
  server.js                app entrypoint

frontend/
  src/
    api/axios.js            API client (attaches JWT)
    context/AuthContext.jsx auth state
    components/             Navbar, JobCard, JobForm, MatchScoreBadge, PrivateRoute
    pages/                   Home, Login, Register, Jobs, JobDetails, PostJob,
                             EditJob, EmployerJobs, Applicants, CandidateApplications, Profile

ml-service/                 standalone Python AI matching engine (FastAPI + scikit-learn)
  matcher/                  core.py, skills.py, experience.py, location.py,
                             text_similarity.py, resume_parser.py
  app.py                    REST API (match / rank-candidates / recommend-jobs / parse-resume)
  cli.py                    command-line interface
  tests/test_matcher.py     pytest suite
```

## Getting Started

### Prerequisites

- Node.js 18+
- A running MongoDB instance (local or hosted, e.g. MongoDB Atlas)

### Backend

```bash
cd backend
cp .env.example .env   # edit MONGO_URI / JWT_SECRET as needed
npm install
npm run dev             # starts on http://localhost:5000
```

### Frontend

```bash
cd frontend
cp .env.example .env   # points VITE_API_URL at the backend
npm install
npm run dev             # starts on http://localhost:5173
```

Open `http://localhost:5173`, register as an **employer** to post jobs, and
register as a **candidate** (in another browser/incognito window) to browse
jobs and apply with a resume — the AI match score appears immediately after
applying, and on the employer's ranked applicants page.

## How the AI Matching Score Is Calculated

See `backend/utils/aiMatcher.js`. For a given resume and job:

- `skillMatchPercent` = (job skills found in resume or candidate profile) /
  (total job skills required) × 100
- `textSimilarityPercent` = cosine similarity (× 100) between the term
  frequency vectors of the resume text and the job title + description,
  after lowercasing, tokenizing, and stopword removal
- `matchScore` = round(0.65 × skillMatchPercent + 0.35 × textSimilarityPercent)

This runs entirely locally (no external AI API calls), so it works out of
the box without any API keys.

## API Overview

| Method | Route | Description |
| --- | --- | --- |
| POST | `/api/auth/register` | Register as candidate or employer |
| POST | `/api/auth/login` | Log in |
| GET | `/api/auth/me` | Current user |
| PUT | `/api/users/me` | Update own profile |
| GET | `/api/jobs` | Search/list open jobs |
| GET | `/api/jobs/:id` | Job details |
| GET | `/api/jobs/employer/mine` | Employer's own postings |
| POST | `/api/jobs` | Create job (employer) |
| PUT | `/api/jobs/:id` | Update job (owner) |
| DELETE | `/api/jobs/:id` | Delete job (owner) |
| POST | `/api/applications/:jobId` | Apply with resume upload (candidate) — runs AI screening |
| GET | `/api/applications/mine` | Candidate's own applications |
| GET | `/api/applications/job/:jobId` | Ranked applicants for a job (employer, owner) |
| GET | `/api/applications/:id` | Application details |
| PUT | `/api/applications/:id/status` | Update applicant status (employer, owner) |
