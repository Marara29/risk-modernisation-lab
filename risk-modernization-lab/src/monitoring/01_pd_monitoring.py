import sqlite3
import pandas as pd

from pathlib import Path

from sklearn.metrics import roc_auc_score, average_precision_score


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"


conn = sqlite3.connect(DB_PATH)

df = pd.read_sql(
    "SELECT * FROM pd_modeling_mart",
    conn
)

conn.close()


# --------------------------------------------------
# 1. DATA QUALITY MONITORING
# --------------------------------------------------

monitor_features = [
    "account_count",
    "total_credit_limit",
    "entity_utilization",
    "missing_balance_count",
    "current_max_dpd",
    "delinquent_snapshots_30plus",
    "ever_90_dpd"
]


print("\nDATA QUALITY")
print("------------")

for feature in monitor_features:

    missing_pct = (
        df[feature].isna().mean() * 100
    )

    print(
        f"{feature:30s} missing={missing_pct:.2f}%"
    )


# --------------------------------------------------
# 2. FEATURE DISTRIBUTION SNAPSHOT
# --------------------------------------------------

print("\nFEATURE SNAPSHOT")
print("----------------")

for feature in monitor_features:

    print(
        f"\n{feature}"
    )

    print(
        df[feature].describe()[
            ["mean", "std", "min", "max"]
        ]
    )


# --------------------------------------------------
# 3. TARGET / PORTFOLIO MONITORING
# --------------------------------------------------

default_rate = (
    df["default_180d"].mean() * 100
)

print("\nPORTFOLIO")
print("---------")

print(
    f"Entities: {len(df)}"
)

print(
    f"Default Rate: {default_rate:.2f}%"
)

##The idea is that later, every new scoring period, you compare the new population against your original baseline.
#Did the data, customers, or model behavior change compared with what we originally built the model on?”

#Portfolio size          = 3,231
#Default rate            = 10.68%
#Avg utilization         = 42.1%
#Avg current DPD         = 5.99
#Avg delinquent snapshots= 1.46