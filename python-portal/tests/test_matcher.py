from matcher import (
    canonical_skill, compute_match, experience_fit, extract_education_level, extract_skills,
    extract_years_of_experience, text_similarity,
)

RESUME = """Jane Doe - Backend Engineer
6 years of experience building REST APIs with Python, Flask and Django.
Deployed services on AWS with Docker and k8s. Strong SQL and PostgreSQL skills.
Master of Science in Computer Science."""


def test_aliases_resolve_to_canonical():
    assert canonical_skill("JS") == "javascript"
    assert canonical_skill("k8s") == "kubernetes"
    assert canonical_skill("python") == "python"


def test_extract_skills_uses_dictionary_and_aliases():
    skills = extract_skills(RESUME)
    for s in ["python", "flask", "django", "amazon web services", "docker", "kubernetes",
              "sql", "postgresql", "rest"]:
        assert s in skills
    assert "java" not in skills


def test_symbol_skills_not_confused():
    assert "c++" in extract_skills("Expert in C++ and C#")
    assert "c++" not in extract_skills("Wrote C code")


def test_experience_and_education():
    assert extract_years_of_experience(RESUME) == 6
    assert extract_years_of_experience("no numbers here") is None
    assert extract_education_level(RESUME) == "master"
    assert extract_education_level("PhD in physics; B.Sc earlier") == "phd"


def test_experience_fit():
    assert experience_fit(None, "senior") is None
    assert experience_fit(6, "senior") == 100
    assert experience_fit(1, "mid") == 50
    assert experience_fit(0, "entry") == 100


def test_text_similarity_bounds():
    assert text_similarity("", "anything") == 0.0
    assert text_similarity("python flask api", "python flask api") > 0.99
    assert text_similarity("python flask api", "oil painting watercolor") == 0.0


def test_strong_candidate_outscores_weak_candidate():
    job = dict(title="Senior Python Backend Engineer",
               description="Build REST APIs in Python and Flask, deploy on AWS with Docker.",
               skills_required=["python", "flask", "aws", "docker", "postgresql"],
               experience_level="senior")
    strong = compute_match(RESUME, **job)
    weak = compute_match("Graphic designer skilled in Photoshop and Figma. 1 year in design.", **job)
    assert strong.score > 70
    assert weak.score < 25
    assert strong.missing_skills == []
    assert set(weak.missing_skills) == {"python", "flask", "amazon web services", "docker",
                                        "postgresql"}


def test_declared_skills_count_and_unknown_experience_redistributes():
    result = compute_match("I like building things.", "Dev", "Write Go code", ["go"],
                           "mid", declared_skills=["golang"])
    assert result.matched_skills == ["go"]
    assert result.experience_fit_percent is None
    assert result.score >= 66  # 2/3 weight on 100% skill match
