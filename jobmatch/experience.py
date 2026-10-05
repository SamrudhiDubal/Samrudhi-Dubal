"""Years-of-experience extraction from resume text."""

from __future__ import annotations

import re
from typing import Optional

# "5 years", "5+ years", "5.5 yrs of experience", "over 20 years"
_EXPERIENCE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\b", re.IGNORECASE)
_YEAR_RANGE_RE = re.compile(r"\b(19[6-9]\d|20[0-4]\d)\s*(?:to|-|–)\s*(19[6-9]\d|20[0-4]\d|current|present)\b", re.IGNORECASE)
CURRENT_YEAR = 2026


def extract_experience_years(text: str) -> Optional[float]:
    """Best-effort estimate of total years of experience.

    Uses the largest explicit "N years" figure if there is one (resumes
    usually lead with overall tenure). Otherwise estimates the span between
    the earliest and latest years in date ranges such as "2014 to 2019" or
    "2018 - Current". Returns None when nothing usable is found.
    """
    if not text:
        return None
    explicit = [float(m.group(1)) for m in _EXPERIENCE_RE.finditer(text)]
    explicit = [y for y in explicit if y <= 50]
    if explicit:
        return max(explicit)

    starts, ends = [], []
    for start, end in _YEAR_RANGE_RE.findall(text):
        starts.append(int(start))
        ends.append(CURRENT_YEAR if not end.isdigit() else int(end))
    if starts:
        span = max(ends) - min(starts)
        if 0 <= span <= 50:
            return float(span)
    return None


def experience_fit(candidate_years: Optional[float], min_years: float) -> Optional[int]:
    """0-100 fit of the candidate's experience against the job minimum.

    Returns None when the candidate's experience is unknown, so the caller
    can treat it neutrally instead of penalising the candidate.
    """
    if candidate_years is None:
        return None
    if not min_years or candidate_years >= min_years:
        return 100
    return max(0, min(100, round(candidate_years / min_years * 100)))
