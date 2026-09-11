import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"

conn = sqlite3.connect(DB_PATH)

customers = pd.read_sql(
    """
    SELECT
        customer_record_id,
        name_normalized,
        phone_normalized,
        email_normalized,
        address_normalized,
        email_domain,
        city,
        state
    FROM customer_identity_normalized
    """,
    conn
)

candidates = pd.read_sql(
    "SELECT * FROM entity_candidate_pairs",
    conn
)

left = customers.add_suffix("_1")
right = customers.add_suffix("_2")

pairs = (
    candidates
    .merge(
        left,
        left_on="customer_record_id_1",
        right_on="customer_record_id_1"
    )
    .merge(
        right,
        left_on="customer_record_id_2",
        right_on="customer_record_id_2"
    )
)


pairs["phone_match"] = (
    pairs["phone_normalized_1"].notna()
    &
    (
        pairs["phone_normalized_1"]
        ==
        pairs["phone_normalized_2"]
    )
).astype(int)


pairs["email_match"] = (
    pairs["email_normalized_1"].notna()
    &
    (
        pairs["email_normalized_1"]
        ==
        pairs["email_normalized_2"]
    )
).astype(int)


pairs["address_match"] = (
    pairs["address_normalized_1"].notna()
    &
    (
        pairs["address_normalized_1"]
        ==
        pairs["address_normalized_2"]
    )
    &
    (
        pairs["city_1"]
        ==
        pairs["city_2"]
    )
    &
    (
        pairs["state_1"]
        ==
        pairs["state_2"]
    )
).astype(int)


pairs["name_match"] = (
    pairs["name_normalized_1"].notna()
    &
    (
        pairs["name_normalized_1"]
        ==
        pairs["name_normalized_2"]
    )
).astype(int)


pairs["match_score"] = (
      4 * pairs["phone_match"]
    + 3 * pairs["email_match"]
    + 2 * pairs["address_match"]
    + 1 * pairs["name_match"]
)

pairs["email_domain_match"] = (
    pairs["email_domain_1"].notna()
    &
    (
        pairs["email_domain_1"]
        ==
        pairs["email_domain_2"]
    )
).astype(int)

output_cols = [
    "customer_record_id_1",
    "customer_record_id_2",
    "phone_match",
    "email_match",
    "address_match",
    "name_match",
    "email_domain_match",
    "match_score"
    
]

pairs[output_cols].to_sql(
    "entity_match_scores",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print(
    pairs[output_cols]
    .sort_values("match_score", ascending=False)
    .head(30)
)