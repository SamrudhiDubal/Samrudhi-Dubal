"""AI-based resume screening and candidate matching engine.

Three independent signals are blended into a single 0-100 match score:

1. Skill overlap (50%) - fraction of the job's required skills found in the
   resume (curated dictionary + alias table, e.g. "js" -> "javascript") or in
   the candidate's declared profile skills.
2. Semantic text similarity (25%) - TF-IDF cosine similarity (scikit-learn)
   between the resume text and the job title/description/skills.
3. Experience fit (25%) - years of experience detected in the resume compared
   against the minimum typically expected for the job's experience level.
   Unknown experience is scored neutrally: its weight is redistributed over
   the other two signals.

Education level is detected and surfaced to employers but not weighted.
Everything runs locally; no external API calls are made.
"""

import re
from dataclasses import dataclass, field, asdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SKILL_WEIGHT = 0.5
TEXT_WEIGHT = 0.25
EXPERIENCE_WEIGHT = 0.25

EXPERIENCE_LEVEL_MIN_YEARS = {"entry": 0, "mid": 2, "senior": 5, "lead": 8}

SKILLS_DICTIONARY = [
    # Languages
    "javascript", "typescript", "python", "java", "c++", "c#", "go", "rust", "ruby", "php",
    "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css",
    # Frontend
    "react.js", "redux", "vue.js", "angular", "next.js", "svelte", "jquery", "tailwind",
    "bootstrap",
    # Backend
    "node.js", "express.js", "django", "flask", "fastapi", "spring", "spring boot", ".net",
    "laravel", "ruby on rails", "graphql", "rest", "grpc", "microservices",
    # Databases
    "mongodb", "mysql", "postgresql", "sqlite", "redis", "elasticsearch", "cassandra",
    "dynamodb", "firebase", "oracle",
    # Cloud / DevOps
    "amazon web services", "azure", "google cloud", "docker", "kubernetes", "terraform",
    "jenkins", "continuous integration", "ansible", "linux", "nginx", "git", "devops",
    # Data / AI
    "machine learning", "deep learning", "natural language processing", "computer vision",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", "data analysis",
    "data science", "data engineering", "spark", "hadoop", "tableau", "power bi", "etl",
    "llm", "generative ai", "artificial intelligence",
    # Mobile
    "android", "ios", "react native", "flutter",
    # Testing
    "jest", "cypress", "selenium", "junit", "pytest", "test automation",
    # Process / soft skills
    "agile", "scrum", "jira", "project management", "leadership", "communication",
    # Design
    "figma", "ui/ux", "photoshop",
    # Security
    "cybersecurity", "penetration testing", "oauth", "jwt",
]

SKILL_ALIASES = {
    "javascript": ["js", "es6", "ecmascript"],
    "typescript": ["ts"],
    "node.js": ["node", "nodejs"],
    "react.js": ["react", "reactjs"],
    "vue.js": ["vue", "vuejs"],
    "next.js": ["nextjs"],
    "express.js": ["express", "expressjs"],
    "mongodb": ["mongo"],
    "postgresql": ["postgres", "psql"],
    "kubernetes": ["k8s"],
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "natural language processing": ["nlp"],
    "artificial intelligence": ["ai"],
    "continuous integration": ["ci/cd"],
    "ui/ux": ["ux", "ui", "ux/ui"],
    "google cloud": ["gcp"],
    "amazon web services": ["aws"],
    "go": ["golang"],
    "c#": ["csharp"],
    "c++": ["cpp"],
    "ruby on rails": ["rails"],
    "rest": ["restful", "rest api", "restful api"],
    "scikit-learn": ["sklearn"],
}

ALIAS_TO_CANONICAL = {
    alias: canonical for canonical, aliases in SKILL_ALIASES.items() for alias in aliases
}

YEARS_PATTERNS = [
    re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:professional\s*)?experience", re.I),
    re.compile(r"experience\s*(?:of)?\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.I),
    re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s*(?:in|as|working)", re.I),
]

# Ordered highest to lowest so the first match wins.
EDUCATION_LEVELS = [
    ("phd", ["ph.d", "phd", "doctorate", "doctoral"]),
    ("master", ["master of", "master's", "msc", "m.sc", "mba", "m.tech", "mtech"]),
    ("bachelor", ["bachelor of", "bachelor's", "bsc", "b.sc", "b.tech", "btech", "b.e.",
                  "bachelor degree"]),
    ("associate", ["associate degree", "associate of"]),
    ("high_school", ["high school"]),
]


def canonical_skill(skill):
    normalized = skill.lower().strip()
    return ALIAS_TO_CANONICAL.get(normalized, normalized)


def _contains_term(text, term):
    # Word-boundary match that also works for terms like "c++", ".net", "ui/ux".
    pattern = r"(?:^|[^a-z0-9])" + re.escape(term) + r"(?:$|[^a-z0-9+#])"
    return re.search(pattern, text) is not None


def extract_skills(text):
    """Detect skills in free-form text, returning canonical skill names."""
    if not text:
        return []
    normalized = text.lower()
    found = {skill for skill in SKILLS_DICTIONARY if _contains_term(normalized, skill)}
    for alias, canonical in ALIAS_TO_CANONICAL.items():
        if _contains_term(normalized, alias):
            found.add(canonical)
    return sorted(found)


def extract_years_of_experience(text):
    """Maximum years-of-experience figure mentioned in the text, or None."""
    if not text:
        return None
    years = [
        int(m.group(1))
        for pattern in YEARS_PATTERNS
        for m in pattern.finditer(text)
        if 0 <= int(m.group(1)) <= 50
    ]
    return max(years) if years else None


def extract_education_level(text):
    if not text:
        return None
    normalized = text.lower()
    for level, keywords in EDUCATION_LEVELS:
        if any(kw in normalized for kw in keywords):
            return level
    return None


def text_similarity(resume_text, job_text):
    """TF-IDF cosine similarity between two documents, in [0, 1]."""
    if not resume_text or not resume_text.strip() or not job_text or not job_text.strip():
        return 0.0
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform([resume_text, job_text])
    except ValueError:  # empty vocabulary, e.g. only stopwords
        return 0.0
    return float(cosine_similarity(matrix[0], matrix[1])[0][0])


def experience_fit(candidate_years, experience_level):
    if candidate_years is None:
        return None
    required = EXPERIENCE_LEVEL_MIN_YEARS.get(experience_level, 0)
    if required == 0 or candidate_years >= required:
        return 100
    return round(candidate_years / required * 100)


@dataclass
class MatchResult:
    score: int
    skill_match_percent: int
    text_similarity_percent: int
    experience_fit_percent: int | None
    candidate_years: int | None
    education_level: str | None
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)
    extracted_skills: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def compute_match(resume_text, title, description, skills_required, experience_level="entry",
                  declared_skills=None):
    """Score a resume against a job. Returns a MatchResult."""
    job_skills = sorted({canonical_skill(s) for s in skills_required or [] if s.strip()})
    candidate_skills = set(extract_skills(resume_text))
    candidate_skills |= {canonical_skill(s) for s in declared_skills or [] if s.strip()}

    matched = [s for s in job_skills if s in candidate_skills]
    missing = [s for s in job_skills if s not in candidate_skills]
    skill_pct = 100 if not job_skills else round(len(matched) / len(job_skills) * 100)

    job_text = f"{title} {description} {' '.join(job_skills)}"
    text_pct = round(text_similarity(resume_text, job_text) * 100)

    years = extract_years_of_experience(resume_text)
    exp_pct = experience_fit(years, experience_level)

    if exp_pct is None:
        # Redistribute the experience weight proportionally over the other signals.
        total = SKILL_WEIGHT + TEXT_WEIGHT
        score = (SKILL_WEIGHT / total) * skill_pct + (TEXT_WEIGHT / total) * text_pct
    else:
        score = SKILL_WEIGHT * skill_pct + TEXT_WEIGHT * text_pct + EXPERIENCE_WEIGHT * exp_pct

    return MatchResult(
        score=max(0, min(100, round(score))),
        skill_match_percent=skill_pct,
        text_similarity_percent=text_pct,
        experience_fit_percent=exp_pct,
        candidate_years=years,
        education_level=extract_education_level(resume_text),
        matched_skills=matched,
        missing_skills=missing,
        extracted_skills=sorted(candidate_skills),
    )
