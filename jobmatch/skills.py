"""Skill detection in free-form resume text.

Two jobs:
1. `extract_skills` finds known skills (from a curated, multi-industry
   dictionary) to show on a candidate's profile.
2. `match_skills` checks a job's own required skills against a resume, so
   any skill an employer types works, even if it is not in the dictionary.
"""

from __future__ import annotations

import re

# Grouped by domain so the dictionary covers all 24 resume categories.
SKILL_GROUPS: dict[str, list[str]] = {
    "Software & IT": [
        "python", "java", "javascript", "typescript", "c++", "c#", "sql", "html", "css", "php",
        "react", "angular", "node.js", "django", "flask", ".net", "asp.net", "spring",
        "aws", "azure", "google cloud", "docker", "kubernetes", "linux", "git", "devops",
        "mysql", "oracle", "sql server", "mongodb", "networking", "cybersecurity",
        "active directory", "vmware", "help desk", "technical support", "troubleshooting",
        "sharepoint", "salesforce", "sap", "erp",
    ],
    "Data & AI": [
        "machine learning", "deep learning", "data analysis", "data science", "statistics",
        "tableau", "power bi", "excel", "pandas", "tensorflow", "nlp", "big data", "hadoop",
        "data visualization", "business intelligence", "forecasting",
    ],
    "Finance & Accounting": [
        "accounting", "accounts payable", "accounts receivable", "general ledger", "gaap",
        "financial analysis", "financial reporting", "budgeting", "auditing", "tax",
        "payroll", "quickbooks", "reconciliation", "bookkeeping", "cpa", "risk management",
        "credit analysis", "underwriting", "investment", "compliance", "loan processing",
    ],
    "Business & Management": [
        "project management", "business development", "strategic planning", "operations management",
        "process improvement", "six sigma", "lean", "consulting", "change management",
        "stakeholder management", "vendor management", "contract negotiation", "pmp", "agile", "scrum",
    ],
    "Sales & Marketing": [
        "sales", "account management", "lead generation", "crm", "cold calling", "negotiation",
        "marketing", "digital marketing", "social media", "seo", "content marketing",
        "market research", "brand management", "public relations", "media relations",
        "advertising", "copywriting", "event planning", "customer service", "retail",
    ],
    "HR & Administration": [
        "recruiting", "talent acquisition", "onboarding", "employee relations", "benefits administration",
        "hris", "performance management", "training and development", "labor law",
        "office management", "scheduling", "data entry", "call center",
    ],
    "Engineering & Construction": [
        "autocad", "solidworks", "matlab", "mechanical engineering", "electrical engineering",
        "civil engineering", "quality control", "quality assurance", "manufacturing",
        "construction management", "estimating", "osha", "safety", "blueprints", "hvac",
        "maintenance", "inspection", "automotive", "diagnostics",
    ],
    "Healthcare & Fitness": [
        "patient care", "nursing", "cpr", "medical terminology", "ehr", "hipaa", "pharmacy",
        "clinical", "personal training", "nutrition", "fitness", "wellness", "physical therapy",
    ],
    "Education & Legal": [
        "teaching", "curriculum development", "lesson planning", "classroom management",
        "tutoring", "special education", "litigation", "legal research", "contracts",
        "paralegal", "case management",
    ],
    "Creative & Media": [
        "graphic design", "adobe photoshop", "adobe illustrator", "indesign", "ui/ux", "figma",
        "photography", "video editing", "web design", "fashion design", "merchandising",
        "textile", "illustration", "art direction", "writing", "editing",
    ],
    "Hospitality, Aviation & Agriculture": [
        "culinary", "food safety", "menu development", "catering", "food preparation",
        "aviation", "aircraft maintenance", "faa", "flight operations", "logistics",
        "supply chain", "inventory management", "agriculture", "crop management", "farming",
    ],
    "Soft skills": [
        "leadership", "communication", "teamwork", "problem solving", "time management",
        "team management", "mentoring", "presentation",
    ],
}

SKILLS_DICTIONARY: list[str] = sorted({s for group in SKILL_GROUPS.values() for s in group})

# Common alternative spellings mapped to one canonical name.
ALIASES = {
    "js": "javascript",
    "node": "node.js",
    "nodejs": "node.js",
    "reactjs": "react",
    "ml": "machine learning",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "photoshop": "adobe photoshop",
    "illustrator": "adobe illustrator",
    "powerbi": "power bi",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "human resources information system": "hris",
    "customer relationship management": "crm",
    "search engine optimization": "seo",
    "a/p": "accounts payable",
    "a/r": "accounts receivable",
}


def canonical(skill: str) -> str:
    skill = (skill or "").strip().lower()
    return ALIASES.get(skill, skill)


def _pattern(term: str) -> re.Pattern:
    # Word-boundary match that still works for terms like "c++" or ".net".
    return re.compile(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", re.IGNORECASE)


_DICTIONARY_PATTERNS = [(s, _pattern(s)) for s in SKILLS_DICTIONARY]
_ALIAS_PATTERNS = [(alias, target, _pattern(alias)) for alias, target in ALIASES.items()]


def extract_skills(text: str) -> list[str]:
    """Known skills mentioned in the text, in dictionary order."""
    if not text:
        return []
    found = {skill for skill, pat in _DICTIONARY_PATTERNS if pat.search(text)}
    found |= {target for _alias, target, pat in _ALIAS_PATTERNS if pat.search(text)}
    return sorted(found)


def mentions_skill(text: str, skill: str) -> bool:
    """True if the text mentions the skill or one of its aliases."""
    skill = canonical(skill)
    if not skill or not text:
        return False
    if _pattern(skill).search(text):
        return True
    return any(target == skill and pat.search(text) for _a, target, pat in _ALIAS_PATTERNS)


def match_skills(text: str, required: list[str]) -> tuple[list[str], list[str]]:
    """Split a job's required skills into (matched, missing) for this resume."""
    matched, missing = [], []
    for skill in dict.fromkeys(canonical(s) for s in required if s and s.strip()):
        (matched if mentions_skill(text, skill) else missing).append(skill)
    return matched, missing
