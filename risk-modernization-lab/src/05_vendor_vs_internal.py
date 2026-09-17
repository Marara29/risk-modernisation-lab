import sqlite3
import pandas as pd

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score
)


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "risk_lab.db"


conn = sqlite3.connect(DB_PATH)


# --------------------------------------------------
# Load internal modeling mart
# --------------------------------------------------

mart = pd.read_sql(
    "SELECT * FROM pd_modeling_mart",
    conn
)


# --------------------------------------------------
# Build entity-level vendor score
# --------------------------------------------------

vendor = pd.read_sql(
    """
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
    """,
    conn
)

conn.close()


# --------------------------------------------------
# Join vendor scores to modeling mart
# --------------------------------------------------

df = mart.merge(
    vendor,
    on="entity_id",
    how="inner"
)


print("\nCOMPARISON POPULATION")
print("---------------------")

print(f"Entities: {len(df)}")
print(
    f"Default Rate: {df['default_180d'].mean() * 100:.2f}%"
)


# --------------------------------------------------
# Internal model
# --------------------------------------------------

features = [
    "account_count",
    "total_credit_limit",
    "entity_utilization",
    "missing_balance_count",
    "current_max_dpd",
    "delinquent_snapshots_30plus",
    "ever_90_dpd"
]


X = df[features]
y = df["default_180d"]


X_train, X_temp, y_train, y_temp = train_test_split(
    X,
    y,
    test_size=0.40,
    stratify=y,
    random_state=42
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp,
    y_temp,
    test_size=0.50,
    stratify=y_temp,
    random_state=42
)


model = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000))
    ]
)

model.fit(X_train, y_train)


internal_pd = model.predict_proba(X_test)[:, 1]


# --------------------------------------------------
# Vendor score for the SAME test entities
# --------------------------------------------------

vendor_test = df.loc[
    X_test.index,
    "avg_vendor_score"
]


# higher vendor score = safer
# so reverse sign so higher value = more risk
vendor_risk = -vendor_test


# --------------------------------------------------
# Compare ranking performance
# --------------------------------------------------

internal_roc = roc_auc_score(
    y_test,
    internal_pd
)

internal_pr = average_precision_score(
    y_test,
    internal_pd
)

vendor_roc = roc_auc_score(
    y_test,
    vendor_risk
)

vendor_pr = average_precision_score(
    y_test,
    vendor_risk
)


print("\nVENDOR VS INTERNAL")
print("------------------")

print("\nINTERNAL PD MODEL")
print(
    f"ROC-AUC: {internal_roc:.3f}"
)
print(
    f"PR-AUC : {internal_pr:.3f}"
)

print("\nVENDOR SCORE")
print(
    f"ROC-AUC: {vendor_roc:.3f}"
)
print(
    f"PR-AUC : {vendor_pr:.3f}"
)

#“We rebuilt the risk model internally using entity-level exposure and delinquency features,
# 
#  and on the same held-out population the internal model materially outperformed the existing synthetic vendor score.”