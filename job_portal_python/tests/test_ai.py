import io
from types import SimpleNamespace

import docx

from app.ai.matcher import rank_candidates, recommend_jobs, recommendation_for, score_resume, text_similarity
from app.ai.resume_parser import extract_text
from app.ai.skills import extract_education, extract_skills, extract_years_experience


def fake_job(skills, min_exp=0, title="Python Developer", description="Build Flask APIs in Python."):
    return SimpleNamespace(
        title=title, description=description, required_skills=skills, min_experience=min_exp,
        skill_list=[s.strip() for s in skills.split(",")],
    )


def test_extract_skills_handles_aliases_and_symbols():
    skills = extract_skills("Worked with ReactJS, k8s, sklearn, C++ and Node.js on AWS")
    for expected in ["react", "kubernetes", "scikit-learn", "c++", "node.js", "aws"]:
        assert expected in skills


def test_implied_skills():
    skills = extract_skills("Built apps with Django and PostgreSQL")
    assert {"django", "python", "postgresql", "sql"} <= set(skills)


def test_ambiguous_short_names_need_list_context():
    assert "go" not in extract_skills("I go to the gym and want to grow.")
    assert "c" not in extract_skills("See section C of the report.")
    assert {"c", "go"} <= set(extract_skills("Languages: Python, C, Go"))


def test_extract_years_and_education():
    text = "Software engineer with 4+ years of experience. B.Tech in CSE. Also 2 years experience in QA."
    assert extract_years_experience(text) == 4
    assert extract_years_experience("No numbers here") is None
    assert extract_education(text) == "Bachelor's"
    assert extract_education("M.Tech, SRM University") == "Master's"
    assert extract_education("Please contact me") is None


def test_text_similarity_bounds():
    assert text_similarity("", "anything") == 0.0
    same = text_similarity("python flask developer", "python flask developer")
    assert 0.99 <= same <= 1.0
    assert text_similarity("python flask developer", "chef cooking recipes") == 0.0


def test_strong_resume_beats_weak_resume():
    job = fake_job("python, flask, sql, docker", min_exp=2)
    strong = score_resume("Python developer, 3 years of experience with Flask, MySQL and Docker.", job)
    weak = score_resume("Graphic designer skilled in Photoshop and illustration.", job)
    assert strong.score > weak.score
    assert strong.matched_skills == ["python", "flask", "sql", "docker"]
    assert weak.missing_skills == ["python", "flask", "sql", "docker"]
    assert strong.recommendation in ("Strong Match", "Good Match")


def test_unknown_experience_is_not_penalised():
    job = fake_job("python", min_exp=3)
    result = score_resume("python python developer", job)
    assert result.experience_score is None
    assert result.years_experience is None
    # skill (100) and text weights are redistributed, so the score stays high
    assert result.score >= 60


def test_experience_fit_partial_and_profile_skills():
    job = fake_job("python, aws", min_exp=4)
    result = score_resume("2 years of experience in python", job, profile_skills=["AWS"])
    assert result.experience_score == 50.0
    assert result.missing_skills == []


def test_recommendation_thresholds():
    assert recommendation_for(80) == "Strong Match"
    assert recommendation_for(60) == "Good Match"
    assert recommendation_for(35) == "Partial Match"
    assert recommendation_for(5) == "Low Match"


def test_rank_candidates_and_recommend_jobs():
    job = fake_job("python, flask")
    good = SimpleNamespace(resume_text="Python Flask developer", skill_list=[])
    bad = SimpleNamespace(resume_text="Accountant with Tally", skill_list=[])
    empty = SimpleNamespace(resume_text="", skill_list=[])
    ranked = rank_candidates(job, [bad, empty, good])
    assert [c for c, _ in ranked] == [good, bad]

    jobs = [fake_job("excel, tally", title="Accountant", description="Accounts"), job]
    recs = recommend_jobs(good, jobs, limit=1)
    assert recs[0][0] is job


def test_parse_txt_and_docx():
    assert "Python" in extract_text(b"I know Python", "cv.txt")
    document = docx.Document()
    document.add_paragraph("Skilled in Django and Docker")
    buf = io.BytesIO()
    document.save(buf)
    assert "Django" in extract_text(buf.getvalue(), "cv.docx")
