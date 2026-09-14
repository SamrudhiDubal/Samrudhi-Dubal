"""AI-based intelligent candidate <-> job matching engine.

Blends five independent, explainable signals into a single 0-100 match
score instead of relying on keyword search alone:

  1. Required-skill overlap  (40%) - concrete, verifiable must-haves.
  2. Preferred-skill overlap (10%) - "nice to have" bonus skills.
  3. Experience fit          (15%) - years of experience vs. job level.
  4. Location fit            (10%) - remote-friendliness / geography.
  5. Semantic text similarity(25%) - TF-IDF cosine similarity between the
                                     resume and the job description, so
                                     topically-aligned resumes score well
                                     even without exact keyword matches.

Every score comes with a plain-English explanation so the ranking is
transparent to both recruiters and candidates, not a black box.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .experience import compute_experience_match, extract_experience_years
from .location import compute_location_match
from .skills import extract_skills, normalize_skills
from .text_similarity import tfidf_cosine_similarity

WEIGHTS = {
    "required_skills": 0.40,
    "preferred_skills": 0.10,
    "experience": 0.15,
    "location": 0.10,
    "text_similarity": 0.25,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


@dataclass
class Job:
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    experience_level: str = "entry"  # entry | mid | senior | lead
    location: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            required_skills=data.get("required_skills") or data.get("skillsRequired") or [],
            preferred_skills=data.get("preferred_skills") or data.get("preferredSkills") or [],
            experience_level=data.get("experience_level") or data.get("experienceLevel") or "entry",
            location=data.get("location"),
        )


@dataclass
class Candidate:
    id: Optional[str] = None
    name: Optional[str] = None
    resume_text: str = ""
    declared_skills: list[str] = field(default_factory=list)
    experience_years: Optional[float] = None
    location: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Candidate":
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            resume_text=data.get("resume_text") or data.get("resumeText") or "",
            declared_skills=data.get("declared_skills") or data.get("skills") or [],
            experience_years=data.get("experience_years") or data.get("experienceYears"),
            location=data.get("location"),
        )


def _skill_overlap(required: list[str], candidate_skills: set[str]) -> dict:
    if not required:
        return {"percent": 100, "matched": [], "missing": []}
    matched = [s for s in required if s in candidate_skills]
    missing = [s for s in required if s not in candidate_skills]
    percent = round((len(matched) / len(required)) * 100)
    return {"percent": percent, "matched": matched, "missing": missing}


def _build_explanation(skill_result, preferred_result, experience_result, location_result,
                        text_similarity_percent) -> list[str]:
    notes = []

    total_required = len(skill_result["matched"]) + len(skill_result["missing"])
    if total_required:
        notes.append(
            f"Matches {len(skill_result['matched'])}/{total_required} required skills"
            + (f": {', '.join(skill_result['matched'])}." if skill_result["matched"] else ".")
        )
    if skill_result["missing"]:
        notes.append(f"Missing required skills: {', '.join(skill_result['missing'])}.")

    if preferred_result["matched"]:
        notes.append(
            f"Also has {len(preferred_result['matched'])} preferred skill(s): "
            f"{', '.join(preferred_result['matched'])}."
        )

    if experience_result["note"] == "meets":
        notes.append("Meets the experience level required for this role.")
    elif experience_result["note"] == "below":
        notes.append("Has less experience than typically expected for this role.")
    else:
        notes.append("Could not determine years of experience from the resume.")

    if location_result["note"] == "remote":
        notes.append("Job is remote-friendly.")
    elif location_result["note"] == "match":
        notes.append("Candidate location matches the job location.")
    elif location_result["note"] == "mismatch":
        notes.append("Candidate location differs from the job location.")

    notes.append(f"Resume content is {text_similarity_percent}% textually aligned with the job description.")
    return notes


def compute_match(job: Job, candidate: Candidate) -> dict:
    """Score a single candidate against a single job. Returns a full
    breakdown (0-100 overall score plus each signal and an explanation)."""

    required_skills = normalize_skills(job.required_skills)
    preferred_skills = normalize_skills(job.preferred_skills)

    resume_detected_skills = extract_skills(candidate.resume_text)
    candidate_skill_set = set(normalize_skills([*resume_detected_skills, *candidate.declared_skills]))

    skill_result = _skill_overlap(required_skills, candidate_skill_set)
    preferred_result = _skill_overlap(preferred_skills, candidate_skill_set)

    resume_experience_years = extract_experience_years(candidate.resume_text)
    effective_experience_years = (
        candidate.experience_years if candidate.experience_years is not None else resume_experience_years
    )
    experience_result = compute_experience_match(effective_experience_years, job.experience_level)

    location_result = compute_location_match(candidate.location, job.location)

    job_text = " ".join([job.title, job.description, *required_skills, *preferred_skills])
    text_similarity_percent = round(tfidf_cosine_similarity(candidate.resume_text, job_text) * 100)

    score = round(
        WEIGHTS["required_skills"] * skill_result["percent"]
        + WEIGHTS["preferred_skills"] * preferred_result["percent"]
        + WEIGHTS["experience"] * experience_result["percent"]
        + WEIGHTS["location"] * location_result["percent"]
        + WEIGHTS["text_similarity"] * text_similarity_percent
    )

    return {
        "candidate_id": candidate.id,
        "candidate_name": candidate.name,
        "score": max(0, min(100, score)),
        "skill_match_percent": skill_result["percent"],
        "preferred_skill_match_percent": preferred_result["percent"],
        "experience_match_percent": experience_result["percent"],
        "location_match_percent": location_result["percent"],
        "text_similarity_percent": text_similarity_percent,
        "matched_skills": skill_result["matched"],
        "missing_skills": skill_result["missing"],
        "matched_preferred_skills": preferred_result["matched"],
        "missing_preferred_skills": preferred_result["missing"],
        "candidate_experience_years": effective_experience_years,
        "extracted_skills": sorted(candidate_skill_set),
        "explanation": _build_explanation(
            skill_result, preferred_result, experience_result, location_result, text_similarity_percent
        ),
    }


def rank_candidates(job: Job, candidates: list[Candidate]) -> list[dict]:
    """Score every candidate against a job and return them ranked best-first."""
    results = [compute_match(job, c) for c in candidates]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def recommend_jobs(candidate: Candidate, jobs: list[Job]) -> list[dict]:
    """Score every job against a candidate and return them ranked best-first
    (job-recommendation direction of the same matching engine)."""
    results = []
    for job in jobs:
        result = compute_match(job, candidate)
        result["job_id"] = job.id
        result["job_title"] = job.title
        results.append(result)
    results.sort(key=lambda r: r["score"], reverse=True)
    return results
