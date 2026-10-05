"""Checks on the trained models (skipped until train.py has been run)."""

import json

import numpy as np
import pandas as pd

from conftest import models_trained
from jobmatch import config


@models_trained
def test_obvious_resumes_are_classified_correctly():
    from jobmatch.models import get_classifier

    clf = get_classifier()
    examples = {
        "ACCOUNTANT": "Staff accountant. 5 years of experience in accounts payable, general ledger, GAAP, reconciliations and QuickBooks.",
        "CHEF": "Executive chef. Menu development, food preparation, kitchen management, catering and food safety.",
        "TEACHER": "Teacher. Lesson planning, classroom management, curriculum development for elementary students.",
    }
    for category, text in examples.items():
        pred = clf.predict(text)
        assert pred["category"] == category, pred["top"]
        assert abs(sum(pred["probabilities"].values()) - 1) < 1e-3


@models_trained
def test_saved_model_reproduces_reported_test_accuracy():
    from jobmatch.models import get_classifier

    clf = get_classifier()
    metrics = json.loads(config.METRICS_PATH.read_text())
    df = pd.read_csv(config.RESUME_DATASET).drop_duplicates("Resume_str").reset_index(drop=True)
    rows = metrics["test_rows"]
    pred = clf.predict_proba(df.Resume_str[rows].tolist()).argmax(1)
    accuracy = np.mean(np.array(clf.labels)[pred] == df.Category[rows].to_numpy())
    assert abs(accuracy - metrics["deployment"]["test"]["accuracy"]) < 0.005


@models_trained
def test_embeddings_are_unit_length_and_meaningful():
    from jobmatch.models import get_classifier

    clf = get_classifier()
    v = clf.embed(["HR manager recruiting payroll", "HR generalist onboarding employee relations",
                   "Executive chef menu culinary kitchen"])
    assert np.allclose(np.linalg.norm(v, axis=1), 1, atol=1e-5)
    assert v[0] @ v[1] > v[0] @ v[2]
