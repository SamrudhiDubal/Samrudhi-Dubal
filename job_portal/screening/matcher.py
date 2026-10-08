"""Hybrid screening model (Sections 3.7.4 - 3.7.6) and the baseline methods (Section 3.8)."""

import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .parser import parse_job, parse_resume
from .skills import SKILL_TAXONOMY

DEFAULT_WEIGHTS = {"text": 0.35, "skills": 0.40, "experience": 0.15, "education": 0.10}
SHORTLIST_THRESHOLD = 60  # best balance of precision and recall (Table 4.6)


@dataclass
class MatchResult:
    candidate_id: str
    score: float            # 0 - 100
    text_score: float       # 0 - 1 for each component
    skill_score: float
    experience_score: float
    education_score: float
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)

    def breakdown(self):
        return {
            "text": self.text_score,
            "skills": self.skill_score,
            "experience": self.experience_score,
            "education": self.education_score,
            "matched": self.matched_skills,
            "missing": self.missing_skills,
        }


def experience_fit(years, required):
    """Candidate years / required years, capped at 1."""
    if not required:
        return 1.0
    return min(years / required, 1.0)


def education_fit(level, required):
    """1 if the candidate meets the required level, proportionally lower otherwise."""
    if not required:
        return 1.0
    return min(level / required, 1.0)


def rank_candidates(job_description, resumes, weights=None, **job_kwargs):
    """resumes: dict {candidate_id: resume_text}. Returns results sorted by score."""
    weights = weights or DEFAULT_WEIGHTS   # text 0.35, skills 0.40, exp 0.15, edu 0.10
    job = parse_job(job_description, **job_kwargs)
    parsed = {cid: parse_resume(txt) for cid, txt in resumes.items()}
    if not parsed:
        return []

    ids = list(parsed)
    corpus = [job["clean_text"]] + [parsed[c]["clean_text"] for c in ids]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    matrix = vec.fit_transform(corpus)
    sims = cosine_similarity(matrix[0:1], matrix[1:]).ravel()

    results = []
    for i, cid in enumerate(ids):
        p = parsed[cid]
        cand_skills = set(p["skills"])
        matched = sorted(job["skills"] & cand_skills)
        missing = sorted(job["skills"] - cand_skills)
        skill_score = len(matched) / len(job["skills"]) if job["skills"] else 0.0
        exp_score = experience_fit(p["experience_years"], job["min_experience"])
        edu_score = education_fit(p["education_level"], job["min_education"])
        text_score = min(sims[i] / 0.5, 1.0)
        total = (weights["text"] * text_score + weights["skills"] * skill_score
                 + weights["experience"] * exp_score + weights["education"] * edu_score)
        results.append(MatchResult(cid, round(total * 100, 2), round(float(text_score), 4),
                                   round(skill_score, 4), round(exp_score, 4),
                                   round(edu_score, 4), matched, missing))
    return sorted(results, key=lambda r: r.score, reverse=True)


# ---------------------------------------------------------------------------
# Baseline methods used for comparison in Chapter IV
# ---------------------------------------------------------------------------

def keyword_scores(job_skills, resumes):
    """Method A - Boolean keyword: share of the job's skill words found exactly as written."""
    scores = {}
    for cid, text in resumes.items():
        low = f" {text.lower()} "
        hits = sum(1 for s in job_skills
                   if re.search(rf"(?<![a-z0-9]){re.escape(s.lower())}(?![a-z0-9])", low))
        scores[cid] = 100 * hits / len(job_skills) if job_skills else 0.0
    return scores


def tfidf_scores(job_description, resumes):
    """Method B - TF-IDF only: cosine similarity between the job and each resume."""
    from .parser import normalise
    ids = list(resumes)
    corpus = [normalise(job_description)] + [normalise(resumes[c]) for c in ids]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    matrix = vec.fit_transform(corpus)
    sims = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    return {cid: 100 * float(s) for cid, s in zip(ids, sims)}


def skill_scores(job_skills, resumes):
    """Method C - skill match only, using the synonym taxonomy."""
    from .parser import extract_skills
    job_skills = set(job_skills)
    return {cid: 100 * len(job_skills & extract_skills(t)) / len(job_skills) if job_skills else 0.0
            for cid, t in resumes.items()}


def known_skills():
    return sorted(SKILL_TAXONOMY)
