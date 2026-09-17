
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

db_path = ROOT / "database" / "risk_lab.db"
raw_path = ROOT / "data" / "raw"
schema_path = ROOT / "sql" / "schemas" / "001_raw_tables.sql"

tables = [
    "customer_records",
    "accounts",
    "applications",
    "transactions",
    "payments",
    "delinquencies",
    "vendor_scores",
]

with sqlite3.connect(db_path) as conn:
    for table in tables:
        conn.execute(f'DROP TABLE IF EXISTS "{table}"')

    conn.executescript(schema_path.read_text())

    for table in tables:
        csv_path = raw_path / f"{table}.csv"

        print(f"Loading {csv_path.name} ...")

        df = pd.read_csv(csv_path)
        schema_columns = [
            row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')
        ]

        if list(df.columns) != schema_columns:
            raise ValueError(
                f"{table}.csv columns do not match {schema_path.name}: "
                f"expected {schema_columns}, received {list(df.columns)}"
            )

        df.to_sql(
            table,
            conn,
            if_exists="append",
            index=False
        )

        print(f"  loaded {len(df):,} rows")

print("\nDone.")
print(f"Database created at: {db_path}")
