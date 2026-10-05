"""Extract plain text from an uploaded resume file (PDF, DOCX, or TXT)."""

from __future__ import annotations

import io
import os


class ResumeParseError(ValueError):
    pass


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()

    if ext == ".pdf":
        return _extract_pdf(file_bytes)
    if ext == ".docx":
        return _extract_docx(file_bytes)
    if ext in (".txt", ".text"):
        return file_bytes.decode("utf-8", errors="ignore")

    raise ResumeParseError(f"Unsupported resume file type: {ext or 'unknown'}")


def _extract_pdf(file_bytes: bytes) -> str:
    try:
        import pdfplumber
    except ImportError as exc:
        raise ResumeParseError("PDF parsing requires the 'pdfplumber' package") from exc

    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    text = "\n".join(text_parts).strip()
    if not text:
        raise ResumeParseError("Could not extract any text from this PDF")
    return text


def _extract_docx(file_bytes: bytes) -> str:
    try:
        import docx
    except ImportError as exc:
        raise ResumeParseError("DOCX parsing requires the 'python-docx' package") from exc

    document = docx.Document(io.BytesIO(file_bytes))
    text = "\n".join(p.text for p in document.paragraphs).strip()
    if not text:
        raise ResumeParseError("Could not extract any text from this DOCX file")
    return text
