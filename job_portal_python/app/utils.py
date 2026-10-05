import os
import uuid
from functools import wraps

from flask import abort, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from .ai.resume_parser import extract_text


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def allowed_resume(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_RESUME_EXTENSIONS"]


def save_resume(file_storage):
    """Validate, store and parse an uploaded resume. Returns (stored_name, text).

    Raises ValueError with a user-facing message on bad input."""
    if not file_storage or not file_storage.filename:
        raise ValueError("Please choose a resume file.")
    if not allowed_resume(file_storage.filename):
        raise ValueError("Resume must be a PDF, DOCX or TXT file.")

    data = file_storage.read()
    try:
        text = extract_text(data, file_storage.filename)
    except Exception as exc:  # corrupt / unreadable file
        raise ValueError("Could not read that resume file.") from exc
    if not text.strip():
        raise ValueError("No text found in the resume (scanned images aren't supported).")

    stored = f"{uuid.uuid4().hex}_{secure_filename(file_storage.filename)}"
    with open(os.path.join(current_app.config["UPLOAD_FOLDER"], stored), "wb") as fh:
        fh.write(data)
    return stored, text
