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
    average_precision_score,
    classification_report,
    confusion_matrix
)


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"


# --------------------------------------------------
# Load modeling mart
# --------------------------------------------------

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql(
    "SELECT * FROM pd_modeling_mart",
    conn
)

conn.close()


# --------------------------------------------------
# Features and target
# --------------------------------------------------

features = [
    "account_count",
    "total_credit_limit",
    "total_current_balance",
    "entity_utilization",
    "max_single_account_limit",
    "max_single_account_balance",
    "missing_balance_count",
    "max_dpd_history",
    "accounts_ever_30_dpd",
    "accounts_ever_60_dpd",
    "accounts_ever_90_dpd",
    "delinquent_snapshots_30plus",
    "ever_30_dpd",
    "ever_60_dpd",
    "ever_90_dpd",
    "current_max_dpd"
]

X = df[features]

y = df["default_180d"]


# --------------------------------------------------
# Train / validation / test
# --------------------------------------------------

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


print("Train:", len(X_train))
print("Validation:", len(X_val))
print("Test:", len(X_test))


# --------------------------------------------------
# Pipeline
# --------------------------------------------------

model = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        ),
        (
            "model",
            LogisticRegression(
                max_iter=1000
            )
        )
    ]
)


# --------------------------------------------------
# Train
# --------------------------------------------------

model.fit(
    X_train,
    y_train
)


# --------------------------------------------------
# Validation predictions
# --------------------------------------------------

val_pd = model.predict_proba(X_val)[:, 1]

val_pred = (
    val_pd >= 0.50
).astype(int)


# --------------------------------------------------
# Evaluation
# --------------------------------------------------

roc_auc = roc_auc_score(
    y_val,
    val_pd
)

pr_auc = average_precision_score(
    y_val,
    val_pd
)


print("\nVALIDATION PERFORMANCE")
print("----------------------")

print(
    f"ROC-AUC: {roc_auc:.3f}"
)

print(
    f"PR-AUC : {pr_auc:.3f}"
)

print("\nConfusion Matrix:")

print(
    confusion_matrix(
        y_val,
        val_pred
    )
)

print("\nClassification Report:")

print(
    classification_report(
        y_val,
        val_pred,
        digits=3
    )
)