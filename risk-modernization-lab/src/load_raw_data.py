
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

db_path = ROOT / "database" / "risk_lab.db"
raw_path = ROOT / "data" / "raw"

tables = [
    "customer_records",
    "accounts",
    "applications",
    "transactions",
    "payments",
    "delinquencies",
    "vendor_scores",
]

conn = sqlite3.connect(db_path)

for table in tables:
    csv_path = raw_path / f"{table}.csv"

    print(f"Loading {csv_path.name} ...")

    df = pd.read_csv(csv_path)

    df.to_sql(
        table,
        conn,
        if_exists="replace",
        index=False
    )

    print(f"  loaded {len(df):,} rows")

conn.close()

print("\nDone.")
print(f"Database created at: {db_path}")
