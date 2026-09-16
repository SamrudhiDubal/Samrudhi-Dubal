"""Location-fit scoring between a candidate and a job posting."""

from __future__ import annotations

from typing import Optional


def compute_location_match(candidate_location: Optional[str], job_location: Optional[str]) -> dict:
    if not job_location or not job_location.strip():
        return {"percent": 100, "note": "any"}

    job_loc = job_location.strip().lower()
    if "remote" in job_loc:
        return {"percent": 100, "note": "remote"}

    if not candidate_location or not candidate_location.strip():
        return {"percent": 50, "note": "unknown"}

    cand_loc = candidate_location.strip().lower()
    if "remote" in cand_loc:
        return {"percent": 80, "note": "candidate-remote"}

    if cand_loc == job_loc or cand_loc in job_loc or job_loc in cand_loc:
        return {"percent": 100, "note": "match"}

    return {"percent": 30, "note": "mismatch"}
