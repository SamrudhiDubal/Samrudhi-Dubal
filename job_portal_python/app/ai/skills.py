"""Skill dictionary, synonym table, and skill/experience/education extraction."""
import re

# Canonical skills the engine recognises. Extend freely.
SKILLS = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "rust", "kotlin",
    "swift", "php", "ruby", "r", "scala", "matlab", "sql", "bash",
    # Web
    "html", "css", "react", "angular", "vue", "node.js", "express", "django", "flask",
    "fastapi", "spring boot", "bootstrap", "tailwind", "rest api", "graphql", "jquery",
    # Data / AI
    "machine learning", "deep learning", "nlp", "computer vision", "data analysis",
    "data science", "statistics", "pandas", "numpy", "scikit-learn", "tensorflow",
    "pytorch", "keras", "opencv", "matplotlib", "power bi", "tableau", "excel",
    "big data", "spark", "hadoop", "llm", "generative ai",
    # Databases
    "mysql", "postgresql", "mongodb", "sqlite", "oracle", "redis", "firebase",
    # Cloud / DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "ci/cd", "git", "linux",
    "terraform", "microservices",
    # Mobile
    "android", "ios", "flutter", "react native",
    # Testing / process
    "selenium", "unit testing", "agile", "scrum", "jira",
    # Security / networking
    "cyber security", "networking",
    # Soft skills
    "communication", "leadership", "teamwork", "problem solving", "project management",
]

# Alternative spellings / abbreviations -> canonical skill.
ALIASES = {
    "js": "javascript", "es6": "javascript", "ts": "typescript",
    "reactjs": "react", "react.js": "react", "nodejs": "node.js",
    "expressjs": "express", "vuejs": "vue", "angularjs": "angular",
    "golang": "go", "cpp": "c++", "csharp": "c#",
    "ml": "machine learning", "dl": "deep learning",
    "natural language processing": "nlp",
    "sklearn": "scikit-learn", "scikit learn": "scikit-learn", "tf": "tensorflow",
    "postgres": "postgresql", "mongo": "mongodb",
    "amazon web services": "aws", "google cloud": "gcp", "microsoft azure": "azure",
    "k8s": "kubernetes", "restful": "rest api", "rest apis": "rest api",
    "powerbi": "power bi", "ms excel": "excel", "springboot": "spring boot",
    "cybersecurity": "cyber security", "large language models": "llm", "gen ai": "generative ai",
    "html5": "html", "css3": "css", "github": "git", "unit tests": "unit testing",
}

# Knowing a specific tool implies knowing the broader skill.
IMPLIES = {
    "mysql": ["sql"], "postgresql": ["sql"], "sqlite": ["sql"], "oracle": ["sql"],
    "django": ["python"], "flask": ["python"], "fastapi": ["python"], "pandas": ["python"],
    "react": ["javascript"], "angular": ["javascript"], "vue": ["javascript"],
    "node.js": ["javascript"], "express": ["javascript", "node.js"], "typescript": ["javascript"],
    "spring boot": ["java"], "tensorflow": ["deep learning"], "pytorch": ["deep learning"],
    "keras": ["deep learning"], "deep learning": ["machine learning"],
    "scikit-learn": ["machine learning"], "kubernetes": ["docker"],
}

EDUCATION_LEVELS = [
    ("PhD", r"\b(ph\.?\s?d|doctorate)\b"),
    ("Master's", r"\b(m\.?\s?tech\b|m\.e\.|m\.?\s?sc\b|mca\b|mba\b|master'?s?\b|m\.s\.)"),
    ("Bachelor's", r"\b(b\.?\s?tech\b|b\.e\.|b\.?\s?sc\b|bca\b|bba\b|bachelor'?s?\b|b\.s\.)"),
    ("Diploma", r"\bdiploma\b"),
    ("High School", r"\b(high school|12th|hsc|higher secondary)\b"),
]


AMBIGUOUS = {"c", "r", "go"}


def _pattern(term: str) -> re.Pattern:
    # Word-ish boundaries that also work for terms like "c++", "c#", "node.js".
    return re.compile(r"(?<![a-z0-9+#])" + re.escape(term) + r"(?![a-z0-9+#])")


_TERM_PATTERNS = [(t, _pattern(t), t) for t in SKILLS] + [
    (a, _pattern(a), canonical) for a, canonical in ALIASES.items()
]


def normalize_skill(skill: str) -> str:
    s = skill.strip().lower()
    return ALIASES.get(s, s)


def extract_skills(text: str) -> list[str]:
    """Return the sorted canonical skills mentioned in free text."""
    if not text:
        return []
    lowered = text.lower()
    found = set()
    for _term, pattern, canonical in _TERM_PATTERNS:
        # Ambiguous names ("c", "r", "go") only count when written in a list context
        # like "C, C++" or "Languages: R, Go" to avoid matching ordinary English.
        if _term in AMBIGUOUS:
            if not re.search(r"(?:^|[,:/|(]\s*)" + re.escape(_term) + r"\s*(?:[,/|)]|$)", lowered, re.M):
                continue
        if pattern.search(lowered):
            found.add(canonical)
    return sorted(expand_implied(found))


def expand_implied(skills) -> set:
    result = set(skills)
    pending = list(result)
    while pending:
        for implied in IMPLIES.get(pending.pop(), []):
            if implied not in result:
                result.add(implied)
                pending.append(implied)
    return result


def extract_years_experience(text: str) -> float | None:
    """Find the largest 'N years of experience' style figure in the text."""
    if not text:
        return None
    matches = re.findall(
        r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:\w+\s+){0,3}?(?:experience|exp)",
        text.lower(),
    )
    years = [float(m) for m in matches if float(m) <= 50]
    return max(years) if years else None


def extract_education(text: str) -> str | None:
    if not text:
        return None
    lowered = text.lower()
    for level, pattern in EDUCATION_LEVELS:
        if re.search(pattern, lowered):
            return level
    return None
