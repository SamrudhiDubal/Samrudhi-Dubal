from jobmatch.matcher import WEIGHTS, compute_match, scale_semantic

JOB = {"title": "HR Generalist", "description": "HR role", "category": "HR",
       "skills": ["recruiting", "payroll", "onboarding", "hris"], "min_experience": 4}
RESUME = "HR specialist with 6 years of experience in recruiting, onboarding and payroll."


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1) < 1e-9


def test_full_match_breakdown():
    m = compute_match(RESUME, JOB, category_prob=0.9, semantic=0.8)
    assert m["matched_skills"] == ["recruiting", "payroll", "onboarding"] and m["missing_skills"] == ["hris"]
    assert m["skill_match"] == 75 and m["experience_fit"] == 100 and m["years_detected"] == 6
    expected = 0.4 * 0.9 + 0.3 * 0.75 + 0.2 * 0.8 + 0.1 * 1.0
    assert abs(m["score"] - expected * 100) <= 0.5 + 1e-9


def test_unknown_experience_weight_is_redistributed():
    m = compute_match("recruiting payroll onboarding hris", JOB, category_prob=1.0, semantic=1.0)
    assert m["experience_fit"] is None
    assert m["score"] == 100
    assert abs(sum(m["weights_used"].values()) - 1) < 0.01 and "experience" not in m["weights_used"]


def test_missing_semantic_signal_is_handled():
    m = compute_match(RESUME, JOB, category_prob=0.5, semantic=None)
    assert m["semantic_similarity"] is None and 0 <= m["score"] <= 100


def test_scores_are_bounded():
    assert compute_match("nothing relevant", JOB, 0.0, 0.0)["score"] == 0


def test_scale_semantic():
    assert scale_semantic(0.2) == 0 and scale_semantic(1.0) == 1 and scale_semantic(None) is None
    assert 0 < scale_semantic(0.7) < 1
