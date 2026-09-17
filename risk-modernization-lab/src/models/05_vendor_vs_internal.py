import sqlite3
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
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


def load_modeling_data():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM pd_modeling_mart", conn)


def load_vendor_entity_scores():
    query = """
    SELECT
        cem.entity_id,
        AVG(vs.vendor_risk_score) AS avg_vendor_score,
        MIN(vs.vendor_risk_score) AS worst_vendor_score
    FROM vendor_scores vs
    JOIN accounts a
        ON vs.account_id = a.account_id
    JOIN customer_entity_map cem
        ON a.customer_record_id = cem.customer_record_id
    GROUP BY cem.entity_id
    """

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)


def build_internal_model():
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


def main():
    mart = load_modeling_data()
    vendor = load_vendor_entity_scores()

    df = mart.merge(vendor, on="entity_id", how="left")

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

    model = build_internal_model()
    model.fit(X_train, y_train)

    internal_prob = model.predict_proba(X_test)[:, 1]

    test_index = X_test.index
    vendor_test = df.loc[test_index, "avg_vendor_score"]

    comparison = pd.DataFrame(
        {
            "y_true": y_test,
            "internal_pd": internal_prob,
            "vendor_score": vendor_test,
        }
    ).dropna()

    # Higher vendor score means safer, so invert the sign so higher means riskier.
    comparison["vendor_risk"] = -comparison["vendor_score"]

    print(f"Comparison rows: {len(comparison):,}")
    print(f"Default rate: {comparison['y_true'].mean():.2%}")
    print()

    print("Internal model")
    print(f"ROC-AUC: {roc_auc_score(comparison['y_true'], comparison['internal_pd']):.3f}")
    print(
        f"PR-AUC:  "
        f"{average_precision_score(comparison['y_true'], comparison['internal_pd']):.3f}"
    )
    print()

    print("Vendor score benchmark")
    print(
        f"ROC-AUC: "
        f"{roc_auc_score(comparison['y_true'], comparison['vendor_risk']):.3f}"
    )
    print(
        f"PR-AUC:  "
        f"{average_precision_score(comparison['y_true'], comparison['vendor_risk']):.3f}"
    )

    print(
        "\nImportant: this vendor score is synthetic and should only be interpreted "
        "as a benchmark inside this lab project."
    )


if __name__ == "__main__":
    main()
