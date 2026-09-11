import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "database" / "risk_lab.db"

FN_PATH = (
    ROOT
    / "data"
    / "processed"
    / "entity_false_negative_pairs.csv"
)

fn = pd.read_csv(FN_PATH)

conn = sqlite3.connect(DB_PATH)

scores = pd.read_sql(
    """
    SELECT *
    FROM entity_match_decisions
    """,
    conn
)

customers = pd.read_sql(
    """
    SELECT
        customer_record_id,
        name,
        phone,
        email,
        address,
        city,
        state,
        name_normalized,
        phone_normalized,
        email_normalized,
        address_normalized
    FROM customer_identity_normalized
    """,
    conn
)

conn.close()

diag = fn.merge(
    scores,
    on=[
        "customer_record_id_1",
        "customer_record_id_2"
    ],
    how="left"
)

left = customers.add_suffix("_1")
right = customers.add_suffix("_2")

diag = (
    diag
    .merge(
        left,
        left_on="customer_record_id_1",
        right_on="customer_record_id_1",
        how="left"
    )
    .merge(
        right,
        left_on="customer_record_id_2",
        right_on="customer_record_id_2",
        how="left"
    )
)

cols = [
    "customer_record_id_1",
    "customer_record_id_2",
    "phone_match",
    "email_match",
    "address_match",
    "name_match",
    "match_score",
    "match_decision",

    "name_1",
    "name_2",

    "phone_1",
    "phone_2",

    "email_1",
    "email_2",

    "address_1",
    "address_2",
]

print(
    diag[cols]
    .sort_values(
        "match_score",
        ascending=False
    )
    .to_string(index=False)
)


# further review and investigation is needed to see if we cant promote some rules to match ,, esp that some data are just typo or etc ,, and trying to avoid these duplicates 
# we found 47 duplicates ,and some really were flagged just beacuse its a name typo or email typo ,, or having one phone number under two customers