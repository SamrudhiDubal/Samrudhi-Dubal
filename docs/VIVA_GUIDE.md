# Viva and Demo Guide: JobMatch AI

## 1. Five-minute live demo script

Before the viva: start MongoDB, then run `npm run seed:demo` in `backend/`
and start both servers (see `README.md`). Every demo account uses the
password **demo1234**.

| Step | Log in as | Show | Talking point |
| --- | --- | --- | --- |
| 1 | (logged out) | Home → Browse Jobs, filter by location/type | Public job search, MongoDB text index |
| 2 | `ananya@demo.jobmatch` | **Recommended** | Same AI engine run in reverse: open jobs ranked against her resume, with a "To learn" skill gap |
| 3 | `ananya@demo.jobmatch` | Open a job she hasn't applied to, apply with `backend/tests/fixtures/sample-resume.txt` | Upload → text extraction → score shown instantly |
| 4 | `ananya@demo.jobmatch` | My Applications, Profile → upload resume | Candidate sees own score; profile resume powers recommendations |
| 5 | `techcorp@demo.jobmatch` | My Postings → Applicants on "MERN Stack Developer" | Ranked by score; expand **View AI match details**: skill %, text similarity %, experience fit, education |
| 6 | `techcorp@demo.jobmatch` | Change a status to *shortlisted* | Candidate gets an email (printed in backend console) |
| 7 | `techcorp@demo.jobmatch` | **Find Matching Candidates** tab | Proactive sourcing: whole candidate pool ranked, applied/not applied |
| 8 | `admin@demo.jobmatch` | Admin dashboard: stats, Users (deactivate one), Jobs | RBAC, moderation, cascading deletes |
| 9 | terminal | `npm test` at the project root; `python -m pytest` in `ml-service/` | 44 unit + 25 integration + 22 UI + 18 Python tests |

## 2. Explaining the score in one breath

> "Each application gets a 0 to 100 score: 50% skill overlap, 25% text
> similarity and 25% experience fit. For skills I detect them from a
> 150-word dictionary and resolve synonyms, so 'JS' counts as JavaScript.
> For text similarity I turn the resume and the job description into
> word-frequency vectors and take the cosine of the angle between them. For
> experience I read phrases like '5 years of experience' and compare them to
> the level's minimum. If experience isn't mentioned I redistribute its
> weight instead of penalising. Employers see every component, so the score
> is explainable."

## 3. Likely viva questions and answers

**Project and design**

1. **Why MERN?** One language (JavaScript) end to end. MongoDB's document
   model fits variable data like skill arrays and match breakdowns, and
   React gives a responsive SPA.
2. **Why not just use ChatGPT/Claude to score resumes?** Cost, privacy and
   explainability. The local engine is free, deterministic, keeps resumes on
   the server and can be justified line by line. An LLM layer is available
   as an opt-in add-on (`ANTHROPIC_API_KEY`) and is blended 70/30 so it
   cannot dominate.
3. **What is your architecture?** Three tiers: React SPA → Express REST API
   (JWT middleware, controllers, AI utilities) → MongoDB. The AI engine is
   pure functions, which makes it easy to unit-test.
4. **How are the collections related?** User 1–N Job (employer posts), User
   1–N Application (candidate submits), Job 1–N Application. A unique
   compound index on (job, candidate) blocks duplicate applications.

**AI / algorithm**

5. **What is cosine similarity?** `A·B / (|A||B|)` between two term-frequency
   vectors. It measures how similar the direction (topic mix) is,
   independent of document length. 1 means identical word distribution, 0
   means no shared words.
6. **Why remove stopwords?** Words like "the" or "and" appear everywhere and
   would inflate similarity between unrelated documents.
7. **Why is skill match weighted 50%?** Required skills are the strongest,
   most explicit signal a recruiter writes into a posting. Text similarity
   is noisier, so it gets less weight.
8. **Why isn't education scored?** To avoid penalising skilled candidates
   from non-traditional backgrounds. It is shown for information only.
9. **What if the resume doesn't mention years?** Experience fit is `null` and
   its 25% weight is split across skills and text in the same 2:1 ratio, so
   the score stays on a 0–100 scale.
10. **How do recommendations work?** The same `computeMatchScore` runs for
    one candidate against every open job (or one job against every
    candidate), and results are sorted by score. If there is no resume, a
    profile document is built from headline, bio and skills.
11. **Is this "real" AI?** It is classical NLP/information retrieval
    (vector space model, rule-based entity extraction): the same family of
    techniques early search engines used. It is a deliberate choice for
    explainability. Future work: sentence embeddings (SBERT), TF-IDF, and
    learning the weights from recruiter decisions.
12. **Limitations?** Dictionary coverage, no semantic understanding of
    synonyms outside the alias table, scanned PDFs, and per-request bulk
    scoring at very large scale.

13. **Your classifier only gets 33% accuracy. Why?** That is chance level
    for 3 balanced classes. I checked the feature distributions per class
    and they are nearly identical, so the labels in this dataset don't
    depend on the features; it looks synthetic. Tuning a model can't fix
    data with no signal. It is a negative result that justifies using an
    explainable engine for the live portal, and the pipeline can be retrained
    on real shortlisting data.
14. **Why two matching engines (JavaScript and Python)?** The JavaScript
    engine runs inside the web API with no extra service. The Python
    service shows the same idea with scikit-learn's TF-IDF plus
    preferred-skill and location signals, and can be plugged in as a
    microservice over HTTP.

**Security**

15. **How are passwords stored?** bcrypt hash with a salt (10 rounds),
    excluded from queries by default.
16. **How does authentication work?** On login the server signs a JWT
    containing the user id. The client sends it as `Authorization: Bearer`.
    The `protect` middleware verifies it and reloads the user (so
    deactivated or deleted users are rejected immediately), and `authorize`
    checks the role.
17. **How do you stop an employer editing someone else's job?** Every
    mutation compares `job.employer` with `req.user._id` and returns 403 on
    mismatch.
18. **File-upload risks?** Extension whitelist, 5 MB limit, sanitised
    filenames, and resumes are not served as static files.
19. **Can someone register as admin?** No. Registration rejects the admin
    role; the first admin is created with `npm run seed:admin`.

**Testing**

20. **How did you test?** Jest unit tests for the engine and middleware,
    Supertest integration tests that drive the real HTTP API against an
    in-memory MongoDB, and Vitest + React Testing Library for UI
    components.
21. **Give one integration test.** "Prevents a different employer from
    viewing applicants": register a second employer, call
    `GET /api/applications/job/:id`, expect 403.

## 4. Key files to have open

- `backend/utils/aiMatcher.js`: scoring engine
- `backend/utils/recommender.js`: two-way matching
- `backend/controllers/applicationController.js`: apply → parse → score flow
- `backend/middleware/auth.js`: JWT + RBAC
- `backend/models/*.js`: schemas
- `frontend/src/pages/Applicants.jsx`: ranked applicants + matching tab
