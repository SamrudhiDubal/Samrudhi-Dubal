from jobmatch.experience import experience_fit, extract_experience_years
from jobmatch.skills import canonical, extract_skills, match_skills, mentions_skill
from jobmatch.text import clean_text, emphasize_headline, prepare


def test_clean_text_removes_personal_info_and_symbols():
    text = "Contact: jane.doe@mail.com, +91 98765 43210, https://linkedin.com/in/jane. Skills: C++, Node.js!"
    cleaned = clean_text(text)
    assert "jane.doe" not in cleaned and "98765" not in cleaned and "linkedin" not in cleaned
    assert "c++" in cleaned and "node.js" in cleaned and "!" not in cleaned


def test_clean_text_handles_non_strings():
    assert clean_text(None) == ""


def test_emphasize_headline_repeats_first_words():
    out = emphasize_headline("hr manager with ten years", words=2, repeat=3)
    assert out.startswith("hr manager hr manager hr manager")
    assert out.endswith("hr manager with ten years")


def test_prepare_is_clean_plus_headline():
    assert prepare("STAFF ACCOUNTANT. Summary").split()[:2] == ["staff", "accountant"]


def test_extract_skills_across_industries():
    skills = extract_skills("Experienced in payroll, GAAP, lesson planning, AutoCAD and Python.")
    assert {"payroll", "gaap", "lesson planning", "autocad", "python"} <= set(skills)


def test_extract_skills_resolves_aliases():
    assert "excel" in extract_skills("Advanced MS Excel user")
    assert canonical("Photoshop") == "adobe photoshop"


def test_skill_matching_respects_word_boundaries():
    assert not mentions_skill("javascript developer", "java")
    assert mentions_skill("java developer", "java")
    assert mentions_skill("built apps with c++", "c++")


def test_match_skills_splits_and_dedupes():
    matched, missing = match_skills("recruiting and onboarding specialist", ["Recruiting", "payroll", "recruiting"])
    assert matched == ["recruiting"] and missing == ["payroll"]


def test_extract_years_explicit_and_ranges():
    assert extract_experience_years("Over 12 years of experience, 3 yrs in banking") == 12
    assert extract_experience_years("Accountant 2010 to 2015, Senior Accountant 2015 to 2020") == 10
    assert extract_experience_years("No dates here") is None


def test_experience_fit():
    assert experience_fit(None, 3) is None
    assert experience_fit(5, 3) == 100
    assert experience_fit(1, 4) == 25
    assert experience_fit(0, 0) == 100
