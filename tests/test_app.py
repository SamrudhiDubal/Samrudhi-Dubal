"""Smoke tests that run the Streamlit app and every page headlessly."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from conftest import models_trained

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run_page(module: str, page: str, email: str | None):
    """Run one page function as its own Streamlit script, logged in as `email`."""

    def script(module, page):
        import importlib
        import sys

        sys.path.insert(0, ".")
        getattr(importlib.import_module(module), page)()

    at = AppTest.from_function(script, args=(module, page), default_timeout=120)
    if email:
        from jobmatch import db

        at.session_state["user"] = db.authenticate(email, "demo1234")
    return at.run()


@pytest.fixture(scope="module", autouse=True)
def seeded_app():
    """Starting the full app once creates and seeds the test database."""
    if Path(APP).exists():
        AppTest.from_file(APP, default_timeout=180).run()


@models_trained
def test_app_starts_on_resume_analyzer():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    assert at.title[0].value == "AI Resume Analyzer"


@models_trained
def test_analyzer_predicts_a_pasted_resume():
    at = AppTest.from_file(APP, default_timeout=120).run()
    at.text_area(key="analyzer_text").input(
        "HR MANAGER. 8 years of experience in recruiting, onboarding, payroll, HRIS and employee relations.").run()
    at.button[0].click().run()
    assert not at.exception
    assert any(m.value == "HR" for m in at.metric)


PAGES = [
    ("ui.public", "browse_jobs", None),
    ("ui.public", "model_performance", None),
    ("ui.public", "login", None),
    ("ui.public", "register", None),
    ("ui.candidate", "my_resume", "ananya@example.com"),
    ("ui.candidate", "recommended_jobs", "ananya@example.com"),
    ("ui.candidate", "my_applications", "ananya@example.com"),
    ("ui.employer", "applicants", "talent@nimbus.example.com"),
    ("ui.employer", "find_candidates", "talent@nimbus.example.com"),
    ("ui.employer", "post_job", "talent@nimbus.example.com"),
    ("ui.admin", "dashboard", "admin@example.com"),
]


@models_trained
@pytest.mark.parametrize("module,page,email", PAGES)
def test_page_renders_without_errors(module, page, email):
    at = _run_page(module, page, email)
    assert not at.exception, at.exception
    assert not at.warning or email is None, [w.value for w in at.warning]


@models_trained
def test_role_pages_are_protected():
    at = _run_page("ui.employer", "applicants", "ananya@example.com")  # a candidate
    assert any("log in" in w.value.lower() for w in at.warning)


@models_trained
def test_candidate_sees_ranked_recommendations():
    at = _run_page("ui.candidate", "recommended_jobs", "ananya@example.com")
    assert any("match" in m.value for m in at.markdown if "badge" in m.value)
