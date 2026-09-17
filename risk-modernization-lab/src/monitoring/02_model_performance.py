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
    precision_score,
    recall_score
)


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"


conn = sqlite3.connect(DB_PATH)

df = pd.read_sql(
    "SELECT * FROM pd_modeling_mart",
    conn
)

conn.close()


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


# same split used during development
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


# --------------------------------------------------
# Performance monitoring
# --------------------------------------------------

test_pd = model.predict_proba(X_test)[:, 1]

THRESHOLD = 0.20

test_pred = (
    test_pd >= THRESHOLD
).astype(int)


roc_auc = roc_auc_score(
    y_test,
    test_pd
)

pr_auc = average_precision_score(
    y_test,
    test_pd
)

precision = precision_score(
    y_test,
    test_pred
)

recall = recall_score(
    y_test,
    test_pred
)


print("\nMODEL PERFORMANCE MONITORING")
print("----------------------------")

print(f"ROC-AUC   : {roc_auc:.3f}")
print(f"PR-AUC    : {pr_auc:.3f}")
print(f"Precision : {precision:.3f}")
print(f"Recall    : {recall:.3f}")
print(f"Threshold : {THRESHOLD:.2f}")

#DATA
#Did fields disappear or change?



#FEATURES
#Did utilization, delinquency, exposure, etc. shift?



#PORTFOLIO
#Did default rate change?



#MODEL
#Did ROC-AUC / PR-AUC / precision / recall deteriorate?

#In plain English, the model is ranking risky customers well, it is substantially better than the base default rate at identifying actual defaulters,
# and at the chosen threshold it catches about 65% of defaults while keeping precision around 57%.