import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db  # noqa: E402
from app.models import Job, User  # noqa: E402
from config import TestConfig  # noqa: E402


@pytest.fixture
def app(tmp_path):
    class Cfg(TestConfig):
        UPLOAD_FOLDER = str(tmp_path)

    app = create_app(Cfg)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def make_user(email, role="candidate", **kw):
    user = User(name=kw.pop("name", email.split("@")[0]), email=email, role=role, **kw)
    user.set_password("secret123")
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email):
    return client.post("/auth/login", data={"email": email, "password": "secret123"}, follow_redirects=True)


@pytest.fixture
def employer(app):
    return make_user("hr@co.com", role="employer", company="Co")


@pytest.fixture
def job(app, employer):
    job = Job(
        title="Python Developer", company="Co", location="Chennai", min_experience=2,
        required_skills="python, flask, sql, docker",
        description="Build REST APIs with Python and Flask backed by a SQL database.",
        employer_id=employer.id,
    )
    db.session.add(job)
    db.session.commit()
    return job
