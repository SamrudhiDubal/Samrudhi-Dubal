import os
import sys
import tempfile
from pathlib import Path

import pytest

# Point the app at a throwaway database before any project module is imported.
_tmp = tempfile.mkdtemp()
os.environ["JOBMATCH_DB"] = str(Path(_tmp) / "test.db")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jobmatch import config  # noqa: E402

models_trained = pytest.mark.skipif(not config.ML_MODEL_PATH.exists(), reason="run python train.py first")


@pytest.fixture
def db_path(tmp_path):
    from jobmatch import db

    path = tmp_path / "jobmatch.db"
    db.init_db(path)
    return path
