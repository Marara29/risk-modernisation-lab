import sqlite3
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"

FEATURES_V2 = [
    "account_count",
    "total_credit_limit",
    "entity_utilization",
    "missing_balance_count",
    "current_max_dpd",
    "delinquent_snapshots_30plus",
    "ever_90_dpd",
]

TARGET = "default_180d"
THRESHOLDS = [0.50, 0.40, 0.30, 0.20, 0.10]


def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM pd_modeling_mart", conn)


def build_pipeline():
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[("num", numeric_pipeline, FEATURES_V2)],
        remainder="drop",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=1000)),
        ]
    )


def threshold_metrics(y_true, probabilities, threshold):
    pred = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()

    return {
        "threshold": threshold,
        "precision": precision_score(y_true, pred, zero_division=0),
        "recall": recall_score(y_true, pred, zero_division=0),
        "f1": f1_score(y_true, pred, zero_division=0),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def main():
    df = load_data()

    X = df[FEATURES_V2]
    y = df[TARGET]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X,
        y,
        test_size=0.40,
        stratify=y,
        random_state=42,
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        stratify=y_temp,
        random_state=42,
    )

    model = build_pipeline()
    model.fit(X_train, y_train)

    val_prob = model.predict_proba(X_val)[:, 1]
    test_prob = model.predict_proba(X_test)[:, 1]

    print("Validation discrimination")
    print(f"ROC-AUC: {roc_auc_score(y_val, val_prob):.3f}")
    print(f"PR-AUC:  {average_precision_score(y_val, val_prob):.3f}")
    print()

    threshold_rows = [
        threshold_metrics(y_val, val_prob, t)
        for t in THRESHOLDS
    ]

    result = pd.DataFrame(threshold_rows)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)
    print(result.to_string(index=False))

    chosen_threshold = 0.20
    test_metrics = threshold_metrics(
        y_test,
        test_prob,
        chosen_threshold,
    )

    print("\nTest-set performance at threshold 0.20")
    print(f"ROC-AUC:   {roc_auc_score(y_test, test_prob):.3f}")
    print(f"PR-AUC:    {average_precision_score(y_test, test_prob):.3f}")
    print(f"Precision: {test_metrics['precision']:.3f}")
    print(f"Recall:    {test_metrics['recall']:.3f}")
    print(f"F1:        {test_metrics['f1']:.3f}")
    print(
        f"TP={test_metrics['tp']} FP={test_metrics['fp']} "
        f"FN={test_metrics['fn']} TN={test_metrics['tn']}"
    )

    print(f"Brier score: {brier_score_loss(y_test, test_prob):.4f}")

    fitted_preprocessor = model.named_steps["preprocessor"]
    fitted_model = model.named_steps["model"]

    transformed_names = fitted_preprocessor.get_feature_names_out()
    clean_names = [name.split("__", 1)[-1] for name in transformed_names]

    coef_df = pd.DataFrame(
        {
            "feature": clean_names,
            "coefficient": fitted_model.coef_[0],
        }
    ).sort_values("coefficient", ascending=False)

    print("\nStandardized logistic coefficients")
    print(coef_df.to_string(index=False))

    scored = df.loc[X_test.index, ["entity_id", TARGET]].copy()
    scored["predicted_pd"] = test_prob

    scored["risk_band"] = pd.cut(
        scored["predicted_pd"],
        bins=[-float("inf"), 0.05, 0.20, 0.50, float("inf")],
        labels=["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
        right=False,
    )

    print("\nRisk-band summary")
    band_summary = (
        scored.groupby("risk_band", observed=False)
        .agg(
            customers=("entity_id", "count"),
            defaults=(TARGET, "sum"),
            avg_predicted_pd=("predicted_pd", "mean"),
            actual_default_rate=(TARGET, "mean"),
        )
        .reset_index()
    )
    print(band_summary.to_string(index=False))


if __name__ == "__main__":
    main()
