import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from matcher.core import Candidate, Job, WEIGHTS, compute_match, rank_candidates, recommend_jobs
from matcher.experience import compute_experience_match, extract_experience_years
from matcher.location import compute_location_match
from matcher.skills import extract_skills, normalize_skills


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_extract_skills_finds_known_terms():
    text = "Built REST APIs with Node.js, Express and MongoDB; deployed via Docker on AWS."
    skills = extract_skills(text)
    for expected in ["node.js", "express", "mongodb", "docker", "aws", "rest"]:
        assert expected in skills


def test_extract_skills_avoids_substring_false_positives():
    # "java" should not match inside "javascript"
    skills = extract_skills("Experienced JavaScript developer.")
    assert "javascript" in skills
    assert "java" not in skills


def test_normalize_skills_dedupes_and_lowercases():
    assert normalize_skills(["React", " react ", "Node.js", ""]) == ["react", "node.js"]


def test_extract_experience_years_picks_largest_figure():
    assert extract_experience_years("3 years with Kubernetes, 6+ years overall experience") == 6.0


def test_extract_experience_years_returns_none_when_absent():
    assert extract_experience_years("Skilled engineer with a passion for clean code.") is None


def test_experience_match_meets_requirement():
    result = compute_experience_match(6, "senior")
    assert result["percent"] == 100
    assert result["note"] == "meets"


def test_experience_match_below_requirement_is_proportional():
    result = compute_experience_match(1, "mid")  # mid requires >= 2 years
    assert result["note"] == "below"
    assert 0 < result["percent"] < 100


def test_experience_match_unknown_is_neutral():
    result = compute_experience_match(None, "mid")
    assert result["percent"] == 50
    assert result["note"] == "unknown"


def test_location_match_remote_job_always_matches():
    assert compute_location_match("Pune, India", "Remote")["percent"] == 100


def test_location_match_same_city():
    assert compute_location_match("Pune, India", "Pune")["percent"] == 100


def test_location_match_different_cities_scores_low():
    result = compute_location_match("Pune, India", "Berlin, Germany")
    assert result["note"] == "mismatch"
    assert result["percent"] < 50


def _sample_job(**overrides):
    base = dict(
        title="Backend Engineer",
        description="Build and scale REST APIs for a growing fintech product.",
        required_skills=["python", "django", "postgresql"],
        preferred_skills=["docker", "aws"],
        experience_level="mid",
        location="Remote",
    )
    base.update(overrides)
    return Job.from_dict(base)


def _sample_candidate(**overrides):
    base = dict(
        id="c1",
        name="Asha",
        resume_text=(
            "Backend engineer with 4 years of experience building REST APIs in Python "
            "using Django and PostgreSQL. Deployed services with Docker on AWS."
        ),
        declared_skills=["python", "django"],
        experience_years=None,
        location="Remote",
    )
    base.update(overrides)
    return Candidate.from_dict(base)


def test_strong_candidate_scores_high():
    result = compute_match(_sample_job(), _sample_candidate())
    assert result["score"] >= 80
    assert set(result["matched_skills"]) == {"python", "django", "postgresql"}
    assert result["missing_skills"] == []
    assert result["candidate_experience_years"] == 4.0


def test_weak_candidate_scores_lower_and_lists_missing_skills():
    weak_candidate = _sample_candidate(
        resume_text="Frontend developer skilled in React and CSS.",
        declared_skills=["react", "css"],
    )
    result = compute_match(_sample_job(), weak_candidate)
    assert result["score"] < 50
    assert "python" in result["missing_skills"]
    assert "django" in result["missing_skills"]


def test_score_is_bounded_between_0_and_100():
    job = _sample_job(required_skills=[], preferred_skills=[])
    candidate = _sample_candidate(resume_text="", declared_skills=[], location=None)
    result = compute_match(job, candidate)
    assert 0 <= result["score"] <= 100


def test_rank_candidates_orders_best_first():
    strong = _sample_candidate(id="strong")
    weak = _sample_candidate(
        id="weak",
        resume_text="Marketing specialist with social media experience.",
        declared_skills=[],
    )
    ranked = rank_candidates(_sample_job(), [weak, strong])
    assert [r["candidate_id"] for r in ranked] == ["strong", "weak"]
    assert ranked[0]["score"] >= ranked[1]["score"]


def test_recommend_jobs_orders_best_first_and_tags_job_identity():
    good_fit = _sample_job(id="good-fit")
    bad_fit = _sample_job(
        id="bad-fit",
        title="Frontend Designer",
        description="Design pixel-perfect UI in Figma and implement with CSS.",
        required_skills=["figma", "css", "ui/ux"],
        preferred_skills=[],
    )
    ranked = recommend_jobs(_sample_candidate(), [bad_fit, good_fit])
    assert ranked[0]["job_id"] == "good-fit"
    assert ranked[0]["score"] >= ranked[1]["score"]


def test_explanation_mentions_missing_skills():
    weak_candidate = _sample_candidate(resume_text="Sales associate.", declared_skills=[])
    result = compute_match(_sample_job(), weak_candidate)
    assert any("Missing required skills" in note for note in result["explanation"])
