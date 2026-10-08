from screening.matcher import rank_candidates
from screening.parser import extract_education, extract_experience, extract_skills, parse_resume


def test_synonyms_map_to_canonical_skills():
    skills = extract_skills("Worked with k8s, PostgreSQL and Talent Acquisition")
    assert {"kubernetes", "sql", "recruitment"} <= skills


def test_whole_word_matching():
    assert "java" not in extract_skills("javascript developer")
    assert "javascript" in extract_skills("javascript developer")


def test_experience_and_education():
    assert extract_experience("3 years at X, total 5.5 years of experience") == 5.5
    assert extract_education("MBA in HR, B.Com") == 3
    assert extract_education("Diploma in Mechanical") == 1
    assert extract_education("Please contact me") == 0


def test_contact_fields():
    p = parse_resume("a.b@mail.com  +91 98765 43210")
    assert p["email"] == "a.b@mail.com" and p["phone"] == "9876543210"


def test_hybrid_score_ranks_and_explains():
    jd = "Required skills: python, django, sql, docker. Minimum 2 years of experience. B.Tech."
    res = rank_candidates(jd, {
        "good": "Python, Django, MySQL, Docker. 4 years of experience. B.Tech",
        "bad": "Sales and marketing. 1 year of experience. Diploma",
    })
    assert res[0].candidate_id == "good" and res[0].score > res[1].score
    assert res[0].missing_skills == [] and 0 <= res[1].score <= 100
    assert set(res[1].missing_skills) == {"python", "django", "sql", "docker"}
