# JobMatch AI — Full-Stack Job Portal with AI-Based Resume Screening

A full-stack job portal (MERN-style: MongoDB, Express, React, Node.js) where
candidates apply to jobs and an AI resume-screening engine automatically
scores every application against the job's requirements — fully functional
with no external API key required, with an optional LLM-based layer for
richer semantic scoring.

## Features

- **Auth & roles** — JWT-based auth with `candidate`, `employer`, and `admin`
  roles. Deactivated accounts are blocked from logging in or making
  authenticated requests.
- **Job postings** — Employers create, edit, close/reopen, and delete job
  listings. Candidates search/filter jobs by keyword, location, job type,
  experience level, and required skill.
- **Resume upload & parsing** — Candidates upload a resume (`PDF`, `DOCX`,
  `DOC`, or `TXT`); the server extracts plain text server-side.
- **AI-based resume screening & candidate matching** — Every application is
  scored 0–100 by a matching engine (`backend/utils/aiMatcher.js`) that
  blends:
  1. **Skill overlap (50%)** — skills detected in the resume (via a curated
     skills dictionary **and an alias/synonym table**, e.g. "js" →
     "javascript", "k8s" → "kubernetes") plus the candidate's declared
     profile skills, compared against the job's required skills.
  2. **Semantic text similarity (25%)** — TF cosine similarity between the
     resume text and the job description, rewarding resumes that are
     topically aligned even without exact keyword matches.
  3. **Experience fit (25%)** — years of experience detected in the resume
     (e.g. "6 years of experience") compared against the job's experience
     level (entry/mid/senior/lead). Unknown is scored neutrally, not
     penalized.
  Education level (PhD/Master's/Bachelor's/Associate/High School) is also
  detected and surfaced to employers, informationally.
- **Optional LLM-based semantic layer** — If `ANTHROPIC_API_KEY` is set,
  each application also gets a qualitative fit score + plain-language
  summary from Claude (`backend/utils/semanticMatcher.js`), blended 70/30
  with the local score. Unset by default — the engine runs fully locally
  with zero external calls unless you opt in.
- **Ranked applicant view** — Employers see every applicant for a job
  sorted by AI match score, with matched/missing skills, experience fit,
  detected education, and (if enabled) the LLM summary, and can update
  each applicant's status (`applied` → `shortlisted` / `rejected` / `hired`).
- **Email notifications** — Candidates get an email when their application
  is submitted and when its status changes; employers get an email when a
  new candidate applies. Uses real SMTP when configured, otherwise logs the
  email to the console so the app works out of the box in development.
- **Admin dashboard** — Platform-wide stats, user management (search,
  filter by role, activate/deactivate, delete with cascading cleanup), job
  moderation (force close/reopen/delete any job), and a view of every
  application platform-wide.
- **Candidate dashboard** — Track submitted applications and see your own
  match score per job.
- **Automated tests** — Backend unit tests (matching engine, skill
  aliasing, experience/education parsing, auth middleware, mailer,
  semantic layer) plus an integration suite exercising the full HTTP API
  against an in-memory MongoDB; frontend component/page tests with Vitest
  + React Testing Library.

## Tech Stack

- **Backend**: Node.js, Express, MongoDB (Mongoose), JWT auth, Multer file
  uploads, `pdf-parse` / `mammoth` for resume text extraction, `nodemailer`
  for email, optional `@anthropic-ai/sdk` for LLM-based scoring.
- **Frontend**: React (Vite), React Router, Tailwind CSS, Axios.
- **Testing**: Jest + Supertest + mongodb-memory-server (backend), Vitest +
  React Testing Library (frontend).

## Project Structure

```
backend/
  config/db.js            MongoDB connection
  models/                 User, Job, Application schemas
  middleware/              auth (JWT + active-account check), role guard, multer upload, error handler
  utils/
    resumeParser.js        PDF/DOCX/TXT -> plain text extraction
    skillsDictionary.js     curated skill keyword list + extractor
    skillAliases.js         skill synonym/alias table (js -> javascript, etc.)
    experienceParser.js     years-of-experience + education level extraction
    aiMatcher.js             local AI screening/matching engine (skills + text similarity + experience fit)
    semanticMatcher.js       optional Claude-based semantic scoring layer
    mailer.js                email notifications (SMTP or console fallback)
    seed.js                  one-off script to create/promote the first admin account
  controllers/, routes/    REST API (auth, users, jobs, applications, admin)
  tests/
    unit/                  pure-function + mocked-dependency tests (Jest)
    integration/            full HTTP API tests against an in-memory MongoDB (Jest + Supertest)
  server.js                app entrypoint

frontend/
  src/
    api/axios.js            API client (attaches JWT)
    context/AuthContext.jsx auth state
    components/             Navbar, JobCard, JobForm, MatchScoreBadge, PrivateRoute
    pages/                   Home, Login, Register, Jobs, JobDetails, PostJob,
                             EditJob, EmployerJobs, Applicants, CandidateApplications,
                             Profile, AdminDashboard
    test/                    Vitest + React Testing Library component/page tests
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

Create the first admin account (admin cannot self-register):

```bash
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=change_me npm run seed:admin
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
applying, and on the employer's ranked applicants page. Log in with the
seeded admin account and visit `/admin` for the platform dashboard.

### Optional configuration

- **Email**: set `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASS`/`SMTP_FROM`
  in `backend/.env` to send real emails; otherwise notifications are logged
  to the console.
- **LLM-based semantic scoring**: set `ANTHROPIC_API_KEY` in `backend/.env`
  to blend in a Claude-generated fit score and summary for each
  application. Leave unset to run fully locally.

## Running Tests

```bash
cd backend && npm test    # Jest: unit tests + full-API integration tests
cd frontend && npm test   # Vitest: component/page tests
```

The integration suite boots a real MongoDB in-memory for the duration of
the run (via `mongodb-memory-server`), downloading a MongoDB binary on
first use (cached afterward). In network-restricted environments where that
download is blocked, the integration tests no-op with a console warning
instead of failing — unit tests are unaffected either way.

## How the AI Matching Score Is Calculated

See `backend/utils/aiMatcher.js`. For a given resume and job:

- `skillMatchPercent` = (job skills found in resume or candidate profile,
  after resolving aliases/synonyms) / (total job skills required) × 100
- `textSimilarityPercent` = cosine similarity (× 100) between the term
  frequency vectors of the resume text and the job title + description,
  after lowercasing, tokenizing, and stopword removal
- `experienceFitPercent` = candidate's detected years of experience vs. the
  minimum years typically expected for the job's experience level (null/
  neutral if the resume doesn't mention years)
- `matchScore` = round(0.5 × skillMatchPercent + 0.25 × textSimilarityPercent
  + 0.25 × experienceFitPercent), with weights redistributed over the first
  two signals when experience is unknown

Education level is detected and shown to employers but not weighted into
the score. If `ANTHROPIC_API_KEY` is configured, the final stored score is
`round(0.7 × localScore + 0.3 × semanticScore)`, where `semanticScore` comes
from Claude's read of the resume against the job.

This all runs locally by default (no external AI API calls), so it works
out of the box without any API keys; the LLM layer is purely additive and
optional.

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
| POST | `/api/applications/:jobId` | Apply with resume upload (candidate) — runs AI screening, sends email notifications |
| GET | `/api/applications/mine` | Candidate's own applications |
| GET | `/api/applications/job/:jobId` | Ranked applicants for a job (employer, owner) |
| GET | `/api/applications/:id` | Application details |
| PUT | `/api/applications/:id/status` | Update applicant status (employer, owner) — notifies the candidate |
| GET | `/api/admin/stats` | Platform-wide stats (admin) |
| GET | `/api/admin/users` | List/search all users (admin) |
| PUT | `/api/admin/users/:id` | Activate/deactivate or change a user's role (admin) |
| DELETE | `/api/admin/users/:id` | Delete a user and cascade their jobs/applications (admin) |
| GET | `/api/admin/jobs` | List all jobs platform-wide (admin) |
| PUT | `/api/admin/jobs/:id` | Force close/reopen a job (admin) |
| DELETE | `/api/admin/jobs/:id` | Delete any job (admin) |
| GET | `/api/admin/applications` | List all applications platform-wide (admin) |
