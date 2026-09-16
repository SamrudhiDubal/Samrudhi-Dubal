"""Years-of-experience extraction and experience-level matching."""

from __future__ import annotations

import re
from typing import Optional

# e.g. "5 years", "5+ years", "5.5 yrs of experience"
_EXPERIENCE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\b", re.IGNORECASE)

EXPERIENCE_LEVEL_RANGES = {
    "entry": (0, 2),
    "mid": (2, 5),
    "senior": (5, 9),
    "lead": (9, float("inf")),
}


def extract_experience_years(text: str) -> Optional[float]:
    """Best-effort extraction of total years of experience from resume text.

    Returns the largest plausible figure mentioned (e.g. "5+ years of
    experience in backend development, 2 years with Kubernetes" -> 5.0),
    since resumes usually lead with overall tenure. Returns None when no
    figure is found.
    """
    if not text:
        return None
    matches = [float(m.group(1)) for m in _EXPERIENCE_RE.finditer(text)]
    matches = [m for m in matches if m <= 60]  # discard nonsense (dates, phone numbers, etc.)
    return max(matches) if matches else None


def compute_experience_match(candidate_years: Optional[float], experience_level: str) -> dict:
    """Score how well a candidate's experience fits a job's experience level."""
    min_years, _max_years = EXPERIENCE_LEVEL_RANGES.get(experience_level, EXPERIENCE_LEVEL_RANGES["entry"])

    if candidate_years is None:
        return {"percent": 50, "note": "unknown"}

    if candidate_years >= min_years:
        return {"percent": 100, "note": "meets"}

    if min_years == 0:
        return {"percent": 100, "note": "meets"}

    percent = round((candidate_years / min_years) * 100)
    return {"percent": max(0, min(100, percent)), "note": "below"}
