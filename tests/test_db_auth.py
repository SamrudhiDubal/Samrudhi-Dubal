import pytest

from jobmatch import db
from jobmatch.auth import hash_password, verify_password


def test_password_hash_roundtrip_and_salt():
    stored = hash_password("secret123")
    assert verify_password("secret123", stored)
    assert not verify_password("wrong", stored)
    assert hash_password("secret123") != stored  # random salt
    assert not verify_password("x", "malformed")


def test_users_register_login_and_deactivate(db_path):
    uid = db.create_user("Jane", "Jane@Example.com", "secret123", "candidate", path=db_path)
    assert db.authenticate("jane@example.com", "secret123", path=db_path)["id"] == uid
    assert db.authenticate("jane@example.com", "nope", path=db_path) is None
    assert "password_hash" not in db.authenticate("jane@example.com", "secret123", path=db_path)
    with pytest.raises(db.DuplicateError):
        db.create_user("Jane 2", "jane@example.com", "secret123", "candidate", path=db_path)
    db.set_user_active(uid, False, path=db_path)
    assert db.authenticate("jane@example.com", "secret123", path=db_path) is None


def test_user_validation(db_path):
    with pytest.raises(ValueError):
        db.create_user("X", "x@example.com", "123", "candidate", path=db_path)
    with pytest.raises(ValueError):
        db.create_user("X", "x@example.com", "secret123", "superuser", path=db_path)


def test_jobs_applications_and_stats(db_path):
    emp = db.create_user("Emp", "emp@example.com", "secret123", "employer", company="Acme", path=db_path)
    cand = db.create_user("Cand", "cand@example.com", "secret123", "candidate", path=db_path)
    db.save_resume(cand, "hr manager resume", "r.txt", "HR", {"HR": 0.9}, ["recruiting"], 5, path=db_path)
    job = db.create_job(emp, "HR Lead", "Acme", "HR", "Lead HR", ["Recruiting", " "], path=db_path)
    assert db.get_job(job, path=db_path)["skills"] == ["recruiting"]

    app = db.create_application(job, cand, 81, {"score": 81}, path=db_path)
    with pytest.raises(db.DuplicateError):
        db.create_application(job, cand, 50, {}, path=db_path)
    db.set_application_status(app, "shortlisted", path=db_path)
    with pytest.raises(ValueError):
        db.set_application_status(app, "bogus", path=db_path)

    ranked = db.list_applications_for_job(job, path=db_path)
    assert ranked[0]["candidate_name"] == "Cand" and ranked[0]["breakdown"]["score"] == 81
    assert db.list_applications_for_candidate(cand, path=db_path)[0]["job_title"] == "HR Lead"
    assert db.list_candidates_with_resumes(path=db_path)[0]["category_probs"] == {"HR": 0.9}

    assert db.application_status_counts(path=db_path) == [{"status": "shortlisted", "n": 1}]
    s = db.stats(path=db_path)
    assert (s["candidates"], s["employers"], s["open_jobs"], s["applications"], s["shortlisted"]) == (1, 1, 1, 1, 1)
    db.set_job_status(job, "closed", path=db_path)
    assert db.list_jobs("open", path=db_path) == []


def test_deleting_job_cascades_applications(db_path):
    emp = db.create_user("Emp", "emp@example.com", "secret123", "employer", path=db_path)
    cand = db.create_user("Cand", "cand@example.com", "secret123", "candidate", path=db_path)
    job = db.create_job(emp, "Chef", "Acme", "CHEF", "Cook", ["culinary"], path=db_path)
    db.create_application(job, cand, 70, {}, path=db_path)
    db.delete_job(job, path=db_path)
    assert db.list_applications_for_candidate(cand, path=db_path) == []
