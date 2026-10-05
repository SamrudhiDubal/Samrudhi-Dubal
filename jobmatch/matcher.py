"""Explainable job <-> candidate matching.

Each (resume, job) pair gets a 0-100 score from four signals:

| Signal              | Weight | Source                                                        |
|---------------------|--------|---------------------------------------------------------------|
| Category fit        | 40%    | Classifier probability that the resume belongs to the job's category |
| Skill match         | 30%    | Share of the job's required skills mentioned in the resume    |
| Semantic similarity | 20%    | Cosine similarity of deep-learning (CNN) embeddings           |
| Experience fit      | 10%    | Detected years of experience vs. the job's minimum            |

When the resume does not reveal years of experience, that 10% is spread
proportionally over the other three signals, so the candidate is not
penalised for missing information.

On 497 unseen test resumes and 24 jobs, this blend puts a resume from the
job's own category in 87% of top-10 positions (see evaluate_matching.py).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .experience import experience_fit, extract_experience_years
from .skills import match_skills
from .text import clean_text

WEIGHTS = {"category": 0.40, "skills": 0.30, "semantic": 0.20, "experience": 0.10}

# Cosine similarities of CNN embeddings fall between about 0.4 (unrelated)
# and 0.95 (same role) on validation data; rescale that band to 0-1.
SEMANTIC_LOW, SEMANTIC_HIGH = 0.40, 0.95


def scale_semantic(cosine: Optional[float]) -> Optional[float]:
    if cosine is None:
        return None
    return float(np.clip((cosine - SEMANTIC_LOW) / (SEMANTIC_HIGH - SEMANTIC_LOW), 0, 1))


def job_text(job: dict) -> str:
    return f"{job['title']}. {job['description']} Skills: {', '.join(job.get('skills', []))}"


def compute_match(resume_text: str, job: dict, category_prob: float, semantic: Optional[float],
                  years: Optional[float] = None) -> dict:
    """Score one resume against one job.

    category_prob: classifier probability for the job's category (0-1)
    semantic: rescaled embedding similarity (0-1), or None if unavailable
    years: candidate's years of experience (extracted from the resume if None)
    """
    text = clean_text(resume_text)
    matched, missing = match_skills(text, job.get("skills", []))
    skill_score = len(matched) / (len(matched) + len(missing)) if (matched or missing) else 1.0
    if years is None:
        years = extract_experience_years(resume_text)
    exp = experience_fit(years, job.get("min_experience", 0))

    parts = {
        "category": float(category_prob),
        "skills": skill_score,
        "semantic": semantic,
        "experience": None if exp is None else exp / 100,
    }
    available = {k: v for k, v in parts.items() if v is not None}
    total_weight = sum(WEIGHTS[k] for k in available)
    score = sum(WEIGHTS[k] * v for k, v in available.items()) / total_weight

    return {
        "score": int(round(score * 100)),
        "category_fit": round(parts["category"] * 100),
        "skill_match": round(skill_score * 100),
        "semantic_similarity": None if semantic is None else round(semantic * 100),
        "experience_fit": exp,
        "years_detected": years,
        "matched_skills": matched,
        "missing_skills": missing,
        "weights_used": {k: round(WEIGHTS[k] / total_weight, 3) for k in available},
    }


class MatchingService:
    """Batches model calls so ranking many resumes or jobs stays fast."""

    def __init__(self, classifier):
        self.clf = classifier
        self.index = {label: i for i, label in enumerate(classifier.labels)}

    def _semantic(self, resume_texts: list[str], job_texts: list[str]) -> np.ndarray | None:
        if not self.clf.dl_available:
            return None
        sims = self.clf.embed(job_texts) @ self.clf.embed(resume_texts).T
        return np.vectorize(scale_semantic)(sims)

    def match_matrix(self, resume_texts: list[str], jobs: list[dict], probs: np.ndarray | None = None,
                     years: list | None = None) -> list[list[dict]]:
        """result[j][r] is the match of resume r against job j."""
        if not resume_texts or not jobs:
            return [[] for _ in jobs]
        probs = self.clf.predict_proba(resume_texts) if probs is None else probs
        sem = self._semantic(resume_texts, [job_text(j) for j in jobs])
        years = years or [None] * len(resume_texts)
        out = []
        for j, job in enumerate(jobs):
            col = self.index.get(job["category"])
            row = []
            for r, text in enumerate(resume_texts):
                cat = float(probs[r][col]) if col is not None else 0.0
                row.append(compute_match(text, job, cat, None if sem is None else float(sem[j][r]), years[r]))
            out.append(row)
        return out

    def recommend_jobs(self, resume_text: str, jobs: list[dict], limit: int = 10) -> list[tuple[dict, dict]]:
        matches = [row[0] for row in self.match_matrix([resume_text], jobs)]
        ranked = sorted(zip(jobs, matches), key=lambda jm: jm[1]["score"], reverse=True)
        return ranked[:limit]

    def rank_candidates(self, job: dict, candidates: list[dict], limit: int = 50) -> list[tuple[dict, dict]]:
        """candidates need 'text'; stored 'category_probs' and 'experience_years' are reused if present."""
        if not candidates:
            return []
        texts = [c["text"] for c in candidates]
        if all(c.get("category_probs") for c in candidates):
            probs = np.array([[c["category_probs"].get(l, 0.0) for l in self.clf.labels] for c in candidates])
        else:
            probs = None
        years = [c.get("experience_years") for c in candidates]
        matches = self.match_matrix(texts, [job], probs=probs, years=years)[0]
        ranked = sorted(zip(candidates, matches), key=lambda cm: cm[1]["score"], reverse=True)
        return ranked[:limit]
