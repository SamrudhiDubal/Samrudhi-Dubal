"""
Talent Recruitment - Candidate Suitability Classifier
======================================================

Trains and evaluates machine learning models that predict a candidate's
suitability category (Highly Suitable / Moderately Suitable / Less Suitable)
from talent_recruitment_job_matching_dataset.csv (12,000 candidates, 26 columns).

Works two ways:
  1. Google Colab - paste this whole file into one cell and run it, or
     upload it and `%run talent_suitability_classifier.py`. Upload the CSV
     when prompted (see the DATA_PATH handling below), or edit DATA_PATH to
     point at a file already in your Colab environment / mounted Drive.
  2. Local Python - `pip install -r requirements.txt`
     then `python talent_suitability_classifier.py`, with the CSV at
     `data/talent_recruitment_job_matching_dataset.csv` relative to this
     script (or edit DATA_PATH).

Pipeline:
  1. Load & inspect the data
  2. Exploratory Data Analysis (EDA)
  3. Feature engineering (skills/certifications, salary gap, etc.)
  4. Preprocessing (encoding + scaling) with ColumnTransformer
  5. Train & compare 3 classifiers (Logistic Regression, Random Forest, Gradient Boosting)
  6. Evaluate the best model (confusion matrix, classification report, feature importance)
  7. Save the trained model and demo a prediction on a new candidate
"""

import sys

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sns.set_theme(style="whitegrid")
pd.set_option("display.max_columns", 100)

DATA_PATH = "data/talent_recruitment_job_matching_dataset.csv"
MODEL_PATH = "talent_suitability_model.joblib"
TARGET_COL = "Target_Category"

NUMERIC_COLS = [
    "Age", "CGPA", "Experience_Years", "Current_Salary_CNY_K", "Expected_Salary_CNY_K",
    "Communication_Score", "Leadership_Score", "Problem_Solving_Score", "Resume_Score",
    "Job_Applications_Count", "Interview_Attempts", "Recruiter_Rating",
]

CATEGORICAL_COLS = [
    "Gender", "Location", "Highest_Degree", "Specialization", "Current_Role",
    "Preferred_Job_Title", "Industry", "Company_Name", "Preferred_Work_Mode", "Career_Level",
]


# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
def load_data(path: str) -> pd.DataFrame:
    # In Colab without the file present yet, prompt for an upload.
    if "google.colab" in sys.modules:
        import os

        if not os.path.exists(path):
            from google.colab import files

            print(f"'{path}' not found - please upload the dataset CSV.")
            uploaded = files.upload()
            path = next(iter(uploaded))

    df = pd.read_csv(path)
    print(f"Loaded {path} -> shape {df.shape}")
    return df


# ---------------------------------------------------------------------------
# 2. EDA
# ---------------------------------------------------------------------------
def run_eda(df: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("EXPLORATORY DATA ANALYSIS")
    print("=" * 80)

    df.info()
    print("\nNumeric summary:\n", df[NUMERIC_COLS].describe().T)

    missing = df.isna().sum()
    print("\nMissing values:\n", missing[missing > 0] if missing.sum() else "None")
    print("Duplicate rows:", df.duplicated().sum())

    order = df[TARGET_COL].value_counts().index

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(data=df, x=TARGET_COL, order=order, hue=TARGET_COL, palette="viridis", legend=False, ax=ax)
    ax.set_title("Target class distribution")
    ax.set_xlabel("")
    for p in ax.patches:
        ax.annotate(int(p.get_height()), (p.get_x() + p.get_width() / 2, p.get_height()), ha="center", va="bottom")
    plt.tight_layout()
    plt.savefig("eda_target_distribution.png", dpi=150)
    plt.show()

    fig, axes = plt.subplots(3, 4, figsize=(18, 10))
    for col, ax in zip(NUMERIC_COLS, axes.ravel()):
        sns.histplot(df[col], kde=True, ax=ax, color="#4C72B0")
        ax.set_title(col)
    plt.tight_layout()
    plt.savefig("eda_numeric_distributions.png", dpi=150)
    plt.show()

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(df[NUMERIC_COLS].corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Correlation between numeric features")
    plt.tight_layout()
    plt.savefig("eda_correlation_heatmap.png", dpi=150)
    plt.show()

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for col, ax in zip(
        ["Recruiter_Rating", "Resume_Score", "Communication_Score", "Problem_Solving_Score"], axes.ravel()
    ):
        sns.boxplot(data=df, x=TARGET_COL, y=col, order=order, hue=TARGET_COL, palette="viridis", legend=False, ax=ax)
        ax.set_title(f"{col} by {TARGET_COL}")
        ax.set_xlabel("")
    plt.tight_layout()
    plt.savefig("eda_scores_by_target.png", dpi=150)
    plt.show()


# ---------------------------------------------------------------------------
# 3. Feature engineering
# ---------------------------------------------------------------------------
def multi_hot(series: pd.Series, prefix: str) -> tuple[pd.Series, pd.DataFrame]:
    """Turn a comma-separated string column into a count + multi-hot columns."""
    lists = series.fillna("").apply(lambda s: [x.strip() for x in s.split(",") if x.strip()])
    counts = lists.apply(len)
    all_values = sorted({v for lst in lists for v in lst})
    hot = pd.DataFrame(
        {f"{prefix}_{v.replace(' ', '_')}": lists.apply(lambda lst: int(v in lst)) for v in all_values},
        index=series.index,
    )
    return counts, hot


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    work_df = df.copy()

    skill_count, skill_hot = multi_hot(work_df["Technical_Skills"], "skill")
    cert_count, cert_hot = multi_hot(work_df["Certifications"], "cert")

    work_df["Num_Technical_Skills"] = skill_count
    work_df["Num_Certifications"] = cert_count
    work_df["Salary_Gap_CNY_K"] = work_df["Expected_Salary_CNY_K"] - work_df["Current_Salary_CNY_K"]

    work_df = pd.concat([work_df, skill_hot, cert_hot], axis=1)
    work_df = work_df.drop(columns=["Candidate_ID", "Technical_Skills", "Certifications"])

    print(f"\nEngineered feature set shape: {work_df.shape}")
    return work_df


# ---------------------------------------------------------------------------
# 4-5. Preprocessing + model training/comparison
# ---------------------------------------------------------------------------
def build_preprocessor(feature_cols: list[str]) -> ColumnTransformer:
    numeric_features = [c for c in feature_cols if c not in CATEGORICAL_COLS]
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLS),
        ]
    )


def train_and_compare(X_train, y_train, X_test, y_test, preprocessor):
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
    }

    results, fitted_pipelines = {}, {}
    print("\n" + "=" * 80)
    print("MODEL TRAINING & COMPARISON")
    print("=" * 80)

    for name, model in models.items():
        pipe = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", model)])
        cv_scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="accuracy", n_jobs=-1)
        pipe.fit(X_train, y_train)
        test_acc = accuracy_score(y_test, pipe.predict(X_test))

        results[name] = {"cv_mean_acc": cv_scores.mean(), "cv_std_acc": cv_scores.std(), "test_acc": test_acc}
        fitted_pipelines[name] = pipe
        print(f"{name:22s} | CV acc: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f} | Test acc: {test_acc:.4f}")

    results_df = pd.DataFrame(results).T.sort_values("test_acc", ascending=False)

    fig, ax = plt.subplots(figsize=(7, 4))
    results_df["test_acc"].plot(kind="bar", color="#4C72B0", ax=ax)
    ax.set_ylabel("Test accuracy")
    ax.set_title("Model comparison")
    ax.set_ylim(0, 1)
    for i, v in enumerate(results_df["test_acc"]):
        ax.text(i, v + 0.01, f"{v:.3f}", ha="center")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig("model_comparison.png", dpi=150)
    plt.show()

    return results_df, fitted_pipelines


# ---------------------------------------------------------------------------
# 6. Evaluation
# ---------------------------------------------------------------------------
def evaluate_best_model(best_name, best_pipe, X_test, y_test, y_classes):
    print("\n" + "=" * 80)
    print(f"BEST MODEL: {best_name}")
    print("=" * 80)

    y_pred = best_pipe.predict(X_test)
    print(classification_report(y_test, y_pred))

    labels = sorted(y_classes)
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    fig, ax = plt.subplots(figsize=(6, 6))
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    plt.title(f"Confusion Matrix - {best_name}")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig("confusion_matrix.png", dpi=150)
    plt.show()

    classifier = best_pipe.named_steps["classifier"]
    if hasattr(classifier, "feature_importances_"):
        feature_names = best_pipe.named_steps["preprocessor"].get_feature_names_out()
        importances = pd.Series(classifier.feature_importances_, index=feature_names)
        top20 = importances.sort_values(ascending=False).head(20)

        fig, ax = plt.subplots(figsize=(8, 8))
        top20.sort_values().plot(kind="barh", ax=ax, color="#55A868")
        ax.set_title(f"Top 20 feature importances - {best_name}")
        plt.tight_layout()
        plt.savefig("feature_importance.png", dpi=150)
        plt.show()
    else:
        print(f"{best_name} does not expose feature_importances_ "
              "(e.g. Logistic Regression uses coefficients instead).")


# ---------------------------------------------------------------------------
# 8. Demo prediction on a new candidate
# ---------------------------------------------------------------------------
def build_candidate_row(reference_df: pd.DataFrame, **overrides) -> pd.DataFrame:
    """Start from the column schema of reference_df (minus the target) and
    fill in the given field values; everything else defaults to 0 / the most
    common category so the row is valid input to the pipeline."""
    row = {}
    for col in reference_df.columns:
        if col == TARGET_COL:
            continue
        if col in overrides:
            row[col] = overrides[col]
        elif reference_df[col].dtype == object:
            row[col] = reference_df[col].mode().iloc[0]
        else:
            row[col] = 0
    return pd.DataFrame([row])


def demo_prediction(work_df: pd.DataFrame, model_path: str) -> None:
    new_candidate = build_candidate_row(
        work_df,
        Gender="Female",
        Age=29,
        Location="Shanghai",
        Highest_Degree="Master's",
        Specialization="Data Science",
        CGPA=8.9,
        Experience_Years=5.0,
        Current_Role="Data Analyst",
        Preferred_Job_Title="Data Scientist",
        Industry="Information Technology",
        Company_Name="Tencent",
        Current_Salary_CNY_K=35.0,
        Expected_Salary_CNY_K=45.0,
        Salary_Gap_CNY_K=10.0,
        Preferred_Work_Mode="Hybrid",
        Career_Level="Mid",
        Communication_Score=80.0,
        Leadership_Score=70.0,
        Problem_Solving_Score=88.0,
        Resume_Score=82.0,
        Job_Applications_Count=12,
        Interview_Attempts=3,
        Recruiter_Rating=4.2,
        Num_Technical_Skills=6,
        Num_Certifications=2,
    )

    print("\n" + "=" * 80)
    print("DEMO PREDICTION ON A NEW CANDIDATE")
    print("=" * 80)

    loaded_pipe = joblib.load(model_path)
    prediction = loaded_pipe.predict(new_candidate)[0]
    print(f"Predicted suitability: {prediction}")

    classifier = loaded_pipe.named_steps["classifier"]
    if hasattr(classifier, "predict_proba"):
        proba = loaded_pipe.predict_proba(new_candidate)[0]
        for cls, p in sorted(zip(loaded_pipe.classes_, proba), key=lambda x: -x[1]):
            print(f"  {cls:22s} {p:.2%}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    df = load_data(DATA_PATH)
    run_eda(df)

    work_df = engineer_features(df)

    X = work_df.drop(columns=[TARGET_COL])
    y = work_df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain: {X_train.shape}, Test: {X_test.shape}")

    preprocessor = build_preprocessor(list(X.columns))
    results_df, fitted_pipelines = train_and_compare(X_train, y_train, X_test, y_test, preprocessor)
    print("\nResults summary:\n", results_df)

    best_name = results_df.index[0]
    best_pipe = fitted_pipelines[best_name]
    evaluate_best_model(best_name, best_pipe, X_test, y_test, y.unique())

    joblib.dump(best_pipe, MODEL_PATH)
    print(f"\nSaved best model ({best_name}) to {MODEL_PATH}")

    demo_prediction(work_df, MODEL_PATH)

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)
    print(
        "Note: accuracy near 33% means this dataset's labels carry no learnable "
        "signal; see README.md. The final project uses a real resume dataset."
    )


if __name__ == "__main__":
    main()
