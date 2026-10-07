# JobMatch AI: single-file version

The whole project in **one Python file** (`job_portal.py`), ready to paste into VS Code.

## Steps
1. Install Python 3.8+ (on Windows, tick **"Add Python to PATH"**).
2. Create an empty folder, open it in VS Code, and create a file named `job_portal.py`.
3. Paste the entire contents of `job_portal.py` into it and save.
4. Open the VS Code terminal (**Terminal → New Terminal**) and run:
   ```
   pip install flask flask-sqlalchemy flask-login scikit-learn pypdf python-docx
   python job_portal.py
   ```
5. Open http://127.0.0.1:5000

Demo data is created automatically. Password for every demo account: `password123`

| Role | Email |
| --- | --- |
| Admin | admin@jobmatch.ai |
| Employer | hr@techsoft.com |
| Candidate | priya@example.com |

To reset the demo data, stop the app, delete `jobportal.db`, and run it again.

The page styling (Bootstrap) loads from the internet. Without internet, the app still works but looks plain. For a fully offline version, use the multi-file project in the parent folder.
