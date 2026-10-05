"""AI resume screening & candidate matching.

Score (0-100) for a resume against a job is a weighted blend of three signals:

1. Skill match (50%)       - share of the job's required skills found in the resume
                             or the candidate's declared profile skills (synonym aware).
2. Text similarity (30%)   - TF-IDF cosine similarity between the resume and the job
                             title + description + skills (scikit-learn).
3. Experience fit (20%)    - detected years of experience vs. the job's minimum.

If the resume doesn't mention years of experience, the experience weight is
redistributed over the other two signals instead of penalising the candidate.
"""
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .skills import (
    expand_implied, extract_education, extract_skills, extract_years_experience, normalize_skill,
)

WEIGHTS = {"skill": 0.5, "text": 0.3, "experience": 0.2}

# Raw resume-vs-job cosine similarities rarely exceed ~0.5 even for strong
# matches (resumes contain much unrelated text), so we rescale so that a
# cosine of SIMILARITY_CEILING or above counts as a full 100%.
SIMILARITY_CEILING = 0.5


@dataclass
class MatchResult:
    score: float
    skill_score: float
    text_score: float
    experience_score: float | None
    years_experience: float | None
    education: str | None
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)
    resume_skills: list = field(default_factory=list)
    recommendation: str = ""


def recommendation_for(score: float) -> str:
    if score >= 75:
        return "Strong Match"
    if score >= 50:
        return "Good Match"
    if score >= 30:
        return "Partial Match"
    return "Low Match"


def text_similarity(resume_text: str, job_text: str) -> float:
    """TF-IDF cosine similarity (0-1) between two documents."""
    if not resume_text or not resume_text.strip() or not job_text or not job_text.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform([resume_text, job_text])
    except ValueError:  # empty vocabulary (e.g. only stopwords)
        return 0.0
    return min(1.0, max(0.0, float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])))


def experience_fit(years: float | None, required: int) -> float | None:
    if not required:
        return 100.0
    if years is None:
        return None
    return round(min(1.0, years / required) * 100, 1)


def job_document(job) -> str:
    return f"{job.title}. {job.description}. Skills: {job.required_skills}"


def score_resume(resume_text: str, job, profile_skills=None) -> MatchResult:
    """Screen a resume against a job (any object with title/description/
    required_skills/min_experience/skill_list attributes)."""
    resume_text = resume_text or ""
    resume_skills = set(extract_skills(resume_text))
    resume_skills = expand_implied(resume_skills | {normalize_skill(s) for s in (profile_skills or [])})

    job_skills = []
    for s in job.skill_list:
        canonical = normalize_skill(s)
        if canonical not in job_skills:
            job_skills.append(canonical)

    matched = [s for s in job_skills if s in resume_skills]
    missing = [s for s in job_skills if s not in resume_skills]
    skill_score = (len(matched) / len(job_skills) * 100) if job_skills else 100.0

    raw_sim = text_similarity(resume_text, job_document(job))
    text_score = min(1.0, raw_sim / SIMILARITY_CEILING) * 100

    years = extract_years_experience(resume_text)
    exp_score = experience_fit(years, job.min_experience or 0)

    if exp_score is None:
        total = WEIGHTS["skill"] + WEIGHTS["text"]
        score = (WEIGHTS["skill"] * skill_score + WEIGHTS["text"] * text_score) / total
    else:
        score = (
            WEIGHTS["skill"] * skill_score
            + WEIGHTS["text"] * text_score
            + WEIGHTS["experience"] * exp_score
        )
    score = round(score, 1)

    return MatchResult(
        score=score,
        skill_score=round(skill_score, 1),
        text_score=round(text_score, 1),
        experience_score=exp_score,
        years_experience=years,
        education=extract_education(resume_text),
        matched_skills=matched,
        missing_skills=missing,
        resume_skills=sorted(resume_skills),
        recommendation=recommendation_for(score),
    )


def rank_candidates(job, candidates):
    """Rank candidate users (with resume_text / skill_list) for a job. Talent search."""
    results = []
    for c in candidates:
        if not (c.resume_text or c.skill_list):
            continue
        results.append((c, score_resume(c.resume_text, job, c.skill_list)))
    return sorted(results, key=lambda pair: pair[1].score, reverse=True)


def recommend_jobs(candidate, jobs, limit=None):
    """Rank open jobs for a candidate based on their resume and profile skills."""
    results = [(j, score_resume(candidate.resume_text, j, candidate.skill_list)) for j in jobs]
    results.sort(key=lambda pair: pair[1].score, reverse=True)
    return results[:limit] if limit else results
