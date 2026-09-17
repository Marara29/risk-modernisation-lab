import sqlite3
from pathlib import Path

import pandas as pd


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


def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM pd_modeling_mart", conn)


def main():
    df = load_data()

    corr = df[FEATURES].corr(numeric_only=True)

    pairs = []
    for i, left in enumerate(FEATURES):
        for right in FEATURES[i + 1 :]:
            value = corr.loc[left, right]
            pairs.append(
                {
                    "feature_1": left,
                    "feature_2": right,
                    "correlation": value,
                    "abs_correlation": abs(value),
                }
            )

    result = (
        pd.DataFrame(pairs)
        .sort_values("abs_correlation", ascending=False)
        .reset_index(drop=True)
    )

    print("Top correlated feature pairs:\n")
    print(
        result.head(25)[
            ["feature_1", "feature_2", "correlation"]
        ].to_string(index=False)
    )

    print("\nPairs with |correlation| >= 0.80:\n")
    high = result[result["abs_correlation"] >= 0.80]
    print(high[["feature_1", "feature_2", "correlation"]].to_string(index=False))


if __name__ == "__main__":
    main()
