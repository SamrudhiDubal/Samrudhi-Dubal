# Setup Guide: Running JobMatch AI on Your Laptop

This takes you from nothing installed to the app running, then shows how to prepare your submission.
It is written for Windows; Mac/Linux differences are noted.

---

## 1. Install the tools (one time)

| Tool | Why | Download | Check (in a new terminal) |
| --- | --- | --- | --- |
| **Python 3.11 or 3.12** | Runs everything | https://www.python.org/downloads/ (tick **"Add python.exe to PATH"** during install) | `python --version` |
| **Git** | Downloads the code | https://git-scm.com/downloads | `git --version` |
| **VS Code** | Code editor | https://code.visualstudio.com (then install the **Python** and **Jupyter** extensions) | |

> Use Python **3.11 or 3.12**. TensorFlow does not support the newest Python releases straight away; if
> `pip install` fails on TensorFlow, a too-new Python is the usual reason.

No database server is needed. The app uses **SQLite**, which is built into Python.

---

## 2. Get the code

Open **VS Code → Terminal → New Terminal**:

```bash
cd C:\                 # Mac: cd ~
mkdir Projects
cd Projects
git clone -b claude/job-portal-ai-resume-screening-atzfzi https://github.com/SamrudhiDubal/Samrudhi-Dubal.git
cd Samrudhi-Dubal
code .
```

No Git? On GitHub choose the branch `claude/job-portal-ai-resume-screening-atzfzi` in the branch dropdown,
click **Code → Download ZIP** and extract it.

---

## 3. Install the Python libraries (one time, about 5 minutes)

```bash
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Your terminal prompt now starts with `(.venv)`. Activate it again whenever you open a new terminal.

> PowerShell says scripts are disabled? Run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

---

## 4. Run the app

```bash
streamlit run app.py
```

Your browser opens **http://localhost:8501**. On the first start the app creates its database and loads
demo data (about 20 seconds). The trained models are already included in `models/`, so there is no need
to train first.

**Demo accounts** (password `demo1234` for all):

| Role | Email |
| --- | --- |
| Candidate | `ananya@example.com`, `rahul@example.com`, `sneha@example.com` |
| Employer | `talent@nimbus.example.com`, `hiring@crestview.example.com` |
| Admin | `admin@example.com` |

Stop the app with **Ctrl + C**.

To start again with fresh demo data: `python -m jobmatch.seed --reset`

---

## 5. Retrain the models (optional, for the demo or to show you can)

```bash
python train.py              # all 7 models, 3 seeds each: about 10–15 minutes
python train.py --quick      # faster version: about 4 minutes
python evaluate_matching.py  # matching evaluation (about 1 minute)
```

This rewrites `models/`, `reports/metrics.json` and the charts in `reports/figures/`. Numbers may differ
very slightly between computers because of floating-point differences in TensorFlow.

Run the tests with `python -m pytest`.

---

## 6. The notebook

Open `notebooks/Resume_Screening_ML_DL.ipynb` in VS Code (select the `.venv` kernel) or in Jupyter
(`jupyter notebook`). It already contains outputs, so you can read it without running anything.

**In Google Colab:** go to https://colab.research.google.com → **GitHub** tab → paste
`SamrudhiDubal/Samrudhi-Dubal`, choose the branch above and open the notebook. Run the first cell; it
downloads the project and installs the libraries.

---

## 7. Prepare your submission

- [ ] Fill in your register number, guide and academic year at the top of `docs/PROJECT_REPORT.md`.
- [ ] Convert the report to PDF: in VS Code install **Markdown PDF**, open the report, right-click →
      *Markdown PDF: Export (pdf)*. Charts are in `reports/figures/`; for the diagrams, paste each
      `mermaid` block into https://mermaid.live and download a PNG.
- [ ] Make your slides (problem, dataset, models, results table, charts, app screenshots, limitations).
- [ ] Practise the demo in `docs/VIVA_GUIDE.md`.
- [ ] For a ZIP upload, use GitHub's **Code → Download ZIP** on the branch. It leaves out `.venv/`, which
      you should never include.

### On demo day

1. Open the project folder, activate `.venv`, run `streamlit run app.py` **before** the examiner arrives
   (the first model load takes a few seconds).
2. Keep `jobmatch/matcher.py` and the notebook open to explain the method.
3. The app works fully offline.

---

## 8. Troubleshooting

| Problem | Fix |
| --- | --- |
| `'python' is not recognized` | Reinstall Python with "Add to PATH" ticked, then reopen VS Code. On Mac use `python3` |
| `No matching distribution found for tensorflow` | Your Python is too new or 32-bit. Install 64-bit Python 3.11 or 3.12 |
| `streamlit: command not found` | The virtual environment isn't active: run the activate command from step 3 |
| Error loading `ml_model.joblib` / `InconsistentVersionWarning` | Different scikit-learn version. Run `pip install -r requirements.txt` again, or retrain with `python train.py` |
| App says models are not trained | `models/` is missing. Re-download the project or run `python train.py` |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |
| Wrong or stale demo data | `python -m jobmatch.seed --reset` |
