# Complete Setup Guide: Running JobMatch AI on Your Laptop

This guide takes you from nothing installed to the full project running on
your laptop, then shows how to package it for submission. It is written for
Windows; Mac/Linux differences are noted where they matter.

---

## 0. Where your code lives

| Place | What it is for |
| --- | --- |
| **GitHub** (`github.com/SamrudhiDubal/Samrudhi-Dubal`) | The master copy and backup. Examiners can view it online. |
| **Your laptop** (e.g. `C:\Projects\Samrudhi-Dubal`) | Where you run, demo and edit the project. |
| **VS Code** | The editor you open that folder in. |
| **Google Colab** | Where you run `AI_Job_Assistance.ipynb`, optional. |

The complete project is on the branch
**`claude/job-portal-ai-resume-screening-atzfzi`**. Always pick this branch on
GitHub (branch dropdown at the top-left of the file list) until it is merged
into the default branch. Other branches hold older, partial versions.

### What is in the folder

```
Samrudhi-Dubal/
├── backend/        Node.js + Express REST API, AI matching engine, tests
├── frontend/       React website (what users see)
├── ml-service/     Python AI matching service (FastAPI + scikit-learn)
├── ml/             Python ML classifier trained on a recruitment dataset
├── docs/           Project report, viva guide, this guide, screenshots
├── scripts/        One-command setup script
├── AI_Job_Assistance.ipynb   Colab notebook (data analysis)
├── package.json    Root commands: setup / seed / dev / test
└── README.md       Technical overview + API reference
```

---

## 1. Install the tools (one time, about 20 minutes)

| Tool | Why | Download | Check it worked (in a new terminal) |
| --- | --- | --- | --- |
| **Node.js 20 LTS** | Runs the backend and frontend | https://nodejs.org (LTS button) | `node -v` shows v20+ |
| **Git** | Downloads the code from GitHub | https://git-scm.com/downloads | `git --version` |
| **VS Code** | Code editor | https://code.visualstudio.com | |
| **MongoDB** | Database; pick ONE option below | | |
| **Python 3.10+** *(optional)* | Only for `ml-service/` and `ml/` | https://www.python.org/downloads (tick **"Add Python to PATH"**) | `python --version` |

### MongoDB: choose one

**Option A: MongoDB Atlas (cloud, free, easiest; recommended)**
1. Sign up at https://www.mongodb.com/cloud/atlas/register.
2. Create a **free M0 cluster**.
3. *Database Access* → add a user with a password.
4. *Network Access* → **Add IP Address** → *Allow access from anywhere*
   (`0.0.0.0/0`). This is fine for a student project.
5. *Connect* → *Drivers* → copy the connection string. It looks like
   `mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/`
6. You will paste it into `backend/.env` in step 3. Add `job_portal` after
   the final `/`.

**Option B: MongoDB Community Server (installed on your laptop)**
1. Download from https://www.mongodb.com/try/download/community and install
   with "Install MongoDB as a Service" ticked.
2. It then runs automatically at `mongodb://127.0.0.1:27017`. That is
   already the default in `backend/.env`, so there is nothing to change.

> Atlas needs internet during the demo. If the exam room's Wi-Fi is
> unreliable, use Option B.

---

## 2. Get the code onto your laptop

Open **VS Code → Terminal → New Terminal** and run:

```bash
cd C:\                      # or wherever you keep projects (Mac: cd ~)
mkdir Projects
cd Projects
git clone -b claude/job-portal-ai-resume-screening-atzfzi https://github.com/SamrudhiDubal/Samrudhi-Dubal.git
cd Samrudhi-Dubal
code .                      # opens the folder in VS Code
```

*No Git?* On GitHub, select the branch above, then **Code → Download ZIP**,
and extract it to `C:\Projects\Samrudhi-Dubal`.

---

## 3. Set up and run the web app (3 commands)

From the `Samrudhi-Dubal` folder:

```bash
npm install          # installs the root helper (one time)
npm run setup        # installs backend + frontend, creates .env files (one time)
```

**If you chose Atlas:** open `backend/.env` and replace the `MONGO_URI` line:

```
MONGO_URI=mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/job_portal
```

Also change `JWT_SECRET` to any long random text.

Then:

```bash
npm run seed         # loads demo users, jobs and applications (re-run any time)
npm run dev          # starts backend (port 5000) + frontend (port 5173)
```

Open **http://localhost:5173** in your browser. Log in with any demo account;
the password is `demo1234`:

| Role | Email |
| --- | --- |
| Admin | `admin@demo.jobmatch` |
| Employer | `techcorp@demo.jobmatch` |
| Candidate | `ananya@demo.jobmatch` |

Press **Ctrl + C** in the terminal to stop the servers. Next time, you only
need `npm run dev`.

Run all automated tests with `npm test`.

---

## 4. Run the Python parts (optional, but good to show)

### 4a. Python AI matching service (`ml-service/`)

```bash
cd ml-service
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests/ -v      # 18 tests should pass
uvicorn app:app --reload --port 8000
```

Open **http://localhost:8000/docs**. FastAPI generates an interactive page
where you can try `/api/match` live in front of the examiner.

### 4b. Talent suitability classifier (`ml/`)

```bash
cd ml\talent-suitability-classifier
pip install -r requirements.txt
python talent_suitability_classifier.py
```

This trains Logistic Regression, Random Forest and Gradient Boosting models,
saves charts as PNGs and saves the best model.

> **Be ready to explain the accuracy.** All three models score about **33%**
> on this dataset, which is chance level for 3 classes. The dataset's labels
> do not correlate with its features; it appears to be synthetic or randomly
> labelled. Present this honestly as a finding: "the pipeline works, but this
> dataset has no learnable signal, which is why the main portal uses an
> explainable rule-plus-similarity engine instead." Do not claim the
> classifier is accurate.

### 4c. Colab notebook

Open `AI_Job_Assistance.ipynb` on GitHub and click **Open in Colab** at the
top, or upload it at https://colab.research.google.com.

---

## 5. Prepare your submission

### Checklist
- [ ] Fill in your register number, department, guide and year at the top of
      `docs/PROJECT_REPORT.md`.
- [ ] Take your own screenshots if you change anything; the current ones are
      in `docs/screenshots/`.
- [ ] Convert the report to PDF/Word. In VS Code, install the **Markdown PDF**
      extension, open `PROJECT_REPORT.md`, right-click → *Markdown PDF:
      Export (pdf)*. For the diagrams, paste each ```` ```mermaid ```` block
      into https://mermaid.live and download a PNG.
- [ ] Prepare a 10–12 slide presentation: problem, objectives, architecture,
      AI algorithm, demo screenshots, testing, results, limitations, future
      work.
- [ ] Practise the 5-minute demo in `docs/VIVA_GUIDE.md`.

### Making a ZIP for upload
Never include `node_modules` (hundreds of MB, and examiners reinstall it
anyway). The easiest clean ZIP is GitHub's: select the branch → **Code →
Download ZIP**. It contains only the source code.

### On demo day
1. Start MongoDB (Option B starts automatically; Atlas needs internet).
2. `npm run seed`, then `npm run dev`.
3. Open http://localhost:5173 *before* the examiner arrives.
4. Keep `backend/utils/aiMatcher.js` open in VS Code to explain the algorithm.

---

## 6. Troubleshooting

| Problem | Fix |
| --- | --- |
| `'npm' is not recognized` | Reinstall Node.js, then **close and reopen** VS Code |
| `MongooseServerSelectionError` / `ECONNREFUSED 127.0.0.1:27017` | MongoDB isn't running. Option B: open *Services* and start "MongoDB Server". Atlas: check `MONGO_URI`, your password, and that Network Access allows your IP |
| `bad auth : authentication failed` | Wrong Atlas username/password in `MONGO_URI`. Special characters in the password must be URL-encoded (`@` → `%40`) |
| `Port 5000 already in use` | Change `PORT=5001` in `backend/.env` and `VITE_API_URL=http://localhost:5001/api` in `frontend/.env` (macOS often uses port 5000 for AirPlay) |
| Login fails right after seeding | Make sure you ran `npm run seed` against the same database the server uses |
| PowerShell blocks `.venv\Scripts\activate` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once |
| Emails aren't arriving | Expected. Without SMTP settings they are printed in the backend terminal instead |
