import sqlite3
import pandas as pd

from pathlib import Path


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


corr = df[features].corr()


pairs = []

for i in range(len(features)):
    for j in range(i + 1, len(features)):

        feature_1 = features[i]
        feature_2 = features[j]

        correlation = corr.loc[
            feature_1,
            feature_2
        ]

        pairs.append({
            "feature_1": feature_1,
            "feature_2": feature_2,
            "correlation": correlation,
            "abs_correlation": abs(correlation)
        })


pairs_df = pd.DataFrame(pairs)

pairs_df = pairs_df.sort_values(
    "abs_correlation",
    ascending=False
)


print("\nHIGHLY CORRELATED FEATURE PAIRS")
print("--------------------------------")

print(
    pairs_df[
        pairs_df["abs_correlation"] >= 0.60
    ][
        ["feature_1", "feature_2", "correlation"]
    ].to_string(index=False)
)