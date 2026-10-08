import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def client(tmp_path, monkeypatch):
    import app as portal
    portal.app.config.update(TESTING=True, DATABASE=str(tmp_path / "test.db"),
                             UPLOAD_FOLDER=str(tmp_path / "uploads"))
    portal.init_db()
    with portal.app.test_client() as c:
        yield c
