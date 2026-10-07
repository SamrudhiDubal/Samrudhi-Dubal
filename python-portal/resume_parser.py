"""Extract plain text from uploaded resumes (PDF, DOCX, TXT)."""

import os

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text(path):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext == "pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == "docx":
        import docx

        document = docx.Document(path)
        return "\n".join(p.text for p in document.paragraphs)
    if ext == "txt":
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    raise ValueError(f"Unsupported resume format: .{ext}")
