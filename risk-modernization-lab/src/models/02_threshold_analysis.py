import sqlite3
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"

FEATURES = [
    "account_count",
    "total_credit_limit",
    "total_current_balance",
    "entity_utilization",
    "max_single_account_limit",
    "max_single_account_balance",
    "missing_balance_count",
    "max_dpd_history",
    "accounts_ever_30",
    "accounts_ever_60",
    "accounts_ever_90",
    "delinquent_snapshots_30plus",
    "ever_30_dpd",
    "ever_60_dpd",
    "ever_90_dpd",
    "current_max_dpd",
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
        transformers=[("num", numeric_pipeline, FEATURES)],
        remainder="drop",
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=1000)),
        ]
    )


def main():
    df = load_data()

    X = df[FEATURES]
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

    print(f"Train rows: {len(X_train):,}")
    print(f"Validation rows: {len(X_val):,}")
    print(f"Test rows: {len(X_test):,}")
    print()

    rows = []

    for threshold in THRESHOLDS:
        pred = (val_prob >= threshold).astype(int)

        tn, fp, fn, tp = confusion_matrix(y_val, pred).ravel()

        precision = precision_score(y_val, pred, zero_division=0)
        recall = recall_score(y_val, pred, zero_division=0)
        f1 = f1_score(y_val, pred, zero_division=0)

        rows.append(
            {
                "threshold": threshold,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
            }
        )

    result = pd.DataFrame(rows)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    print(result.to_string(index=False))

    print("\nReasonable operating-point candidate:")
    print(
        "Threshold 0.20 offers higher recall than 0.30/0.40/0.50, "
        "while 0.10 captures very few additional defaults at the cost of more false positives."
    )


if __name__ == "__main__":
    main()
