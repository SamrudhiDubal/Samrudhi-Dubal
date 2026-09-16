# Talent Suitability Classifier

A single, self-contained Python script that trains and evaluates ML models
predicting a candidate's suitability category (`Highly Suitable` /
`Moderately Suitable` / `Less Suitable`) from
`data/talent_recruitment_job_matching_dataset.csv` (12,000 candidates, 26
columns).

## What it does

1. Loads and inspects the dataset
2. Exploratory data analysis (target distribution, numeric distributions,
   correlation heatmap, score breakdowns by target class) — saved as PNGs
3. Feature engineering — multi-hot encodes `Technical_Skills` and
   `Certifications`, adds skill/cert counts and a salary-gap feature
4. Preprocessing — one-hot encodes categoricals, scales numeric features,
   via a `ColumnTransformer`
5. Trains and compares three classifiers with 5-fold cross-validation:
   Logistic Regression, Random Forest, Gradient Boosting
6. Evaluates the best model — classification report, confusion matrix,
   feature importance
7. Saves the winning pipeline to `talent_suitability_model.joblib` and
   demonstrates loading it to score a new candidate

## Run it

### Google Colab

Upload `talent_suitability_classifier.py` and the CSV, or paste the script
into a cell. If the CSV isn't found at `data/talent_recruitment_job_matching_dataset.csv`,
the script will prompt you to upload it.

```python
%run talent_suitability_classifier.py
```

### Local Python

```bash
cd ml/talent-suitability-classifier
pip install -r requirements.txt
python talent_suitability_classifier.py
```

## Note on this dataset

The features (scores, experience, salary, skills, etc.) show **no
meaningful statistical relationship** with `Target_Category` in this CSV —
grouping any numeric feature (including `Recruiter_Rating`) by target class
yields nearly identical distributions, and all three models land around
33% accuracy on 3 balanced classes (i.e. chance level). This looks like a
synthetically generated/randomly labeled dataset rather than one with a
learnable suitability signal. The pipeline itself is fully functional and
will pick up a real signal automatically if you swap in a dataset where the
label actually correlates with the features.
