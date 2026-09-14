"""A curated dictionary of common skills/technologies used to detect
structured skills from free-form resume text. Extend as needed."""

import re

SKILLS_DICTIONARY = [
    # Languages
    "javascript", "typescript", "python", "java", "c++", "c#", "golang", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl", "dart", "sql", "html",
    "css", "sass", "less",
    # Frontend
    "react", "react.js", "redux", "vue", "vue.js", "angular", "next.js", "nextjs", "nuxt",
    "svelte", "jquery", "tailwind", "tailwindcss", "bootstrap", "material-ui", "webpack",
    "vite", "babel",
    # Backend
    "node", "node.js", "express", "express.js", "django", "flask", "fastapi", "spring",
    "spring boot", ".net", "asp.net", "laravel", "ruby on rails", "rails", "graphql", "rest",
    "restful api", "grpc", "microservices", "websocket",
    # Databases
    "mongodb", "mysql", "postgresql", "postgres", "sqlite", "redis", "elasticsearch",
    "cassandra", "dynamodb", "firebase", "oracle", "mariadb", "neo4j",
    # Cloud/DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s", "terraform",
    "jenkins", "ci/cd", "ansible", "linux", "nginx", "git", "github", "gitlab", "bitbucket",
    "devops",
    # Data/AI
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "data analysis", "data science", "data engineering", "spark", "hadoop", "tableau",
    "power bi", "etl", "llm", "generative ai", "ai",
    # Mobile
    "android", "ios", "react native", "flutter", "xamarin",
    # Testing
    "jest", "mocha", "chai", "cypress", "selenium", "junit", "pytest", "testing",
    "test automation", "qa",
    # Soft/PM
    "agile", "scrum", "kanban", "jira", "project management", "product management",
    "leadership", "communication", "team management", "stakeholder management",
    # Design
    "figma", "sketch", "adobe xd", "ui/ux", "ux design", "ui design", "photoshop", "illustrator",
    # Security
    "cybersecurity", "penetration testing", "security", "oauth", "jwt",
]

_ALNUM_START = re.compile(r"^[a-z0-9]")


def _skill_pattern(skill: str) -> re.Pattern:
    escaped = re.escape(skill)
    if _ALNUM_START.match(skill):
        return re.compile(rf"(?:^|[^a-z0-9]){escaped}(?:$|[^a-z0-9])", re.IGNORECASE)
    return re.compile(escaped, re.IGNORECASE)


_SKILL_PATTERNS = [(skill, _skill_pattern(skill)) for skill in SKILLS_DICTIONARY]


def extract_skills(text: str) -> list[str]:
    """Detect known skills mentioned in free-form text (case-insensitive)."""
    if not text:
        return []
    found = []
    for skill, pattern in _SKILL_PATTERNS:
        if pattern.search(text):
            found.append(skill)
    return found


def normalize_skills(skills) -> list[str]:
    """Lowercase, trim, dedupe, drop empties, preserve order."""
    seen = set()
    result = []
    for skill in skills or []:
        cleaned = (skill or "").strip().lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result
