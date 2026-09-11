import sqlite3
import pandas as pd
from pathlib import Path
from itertools import combinations

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

candidate_pairs = set()


def add_pairs(group):
    ids = group["customer_record_id"].tolist()

    for a, b in combinations(sorted(ids), 2):
        candidate_pairs.add((a, b))


# Strong blocking key: normalized phone
for _, group in customers[
    customers["phone_normalized"].notna()
].groupby("phone_normalized"):

    if len(group) > 1:
        add_pairs(group)


# Another blocking key: normalized email
for _, group in customers[
    customers["email_normalized"].notna()
].groupby("email_normalized"):

    if len(group) > 1:
        add_pairs(group)


# Address + city + state
for _, group in customers[
    customers["address_normalized"].notna()
].groupby(
    ["address_normalized", "city", "state"]
):

    if len(group) > 1:
        add_pairs(group)

# Exact normalized name
for _, group in customers[
    customers["name_normalized"].notna()
].groupby("name_normalized"):

    if len(group) > 1:
        add_pairs(group)

candidates = pd.DataFrame(
    candidate_pairs,
    columns=[
        "customer_record_id_1",
        "customer_record_id_2"
    ]
)

candidates.to_sql(
    "entity_candidate_pairs",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print(f"Candidate pairs generated: {len(candidates):,}")
print(candidates.head(20))