import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"

conn = sqlite3.connect(DB_PATH)

pairs = pd.read_sql(
    "SELECT * FROM entity_match_scores",
    conn
)


def classify(row):

    phone = row["phone_match"]
    email = row["email_match"]
    address = row["address_match"]
    name = row["name_match"]
    domain = row["email_domain_match"]

    # ------------------------------
    # AUTO MATCH
    # ------------------------------

    if phone and email and address:
        return "MATCH"

    if phone and email and name:
        return "MATCH"

    if phone and address and name:
        return "MATCH"

    if phone and email:
        return "MATCH"

    if phone and address:
        return "MATCH"

    if email and address and name:
        return "MATCH"

    # ------------------------------
    # MANUAL / AMBIGUOUS REVIEW
    # ------------------------------

    if phone and name:
        return "REVIEW"

    if email and address:
        return "REVIEW"

    if address and name:
        return "REVIEW"

    if email and name:
        return "REVIEW"

    # Exact name + phone is strong evidence
    if phone and name:
        return "MATCH"



# Exact address + same email domain + name
    if address and domain and name:
        return "MATCH"

    
    # ------------------------------
    # TOO WEAK
    # ------------------------------

    return "NO_MATCH"


pairs["match_decision"] = pairs.apply(
    classify,
    axis=1
)


pairs.to_sql(
    "entity_match_decisions",
    conn,
    if_exists="replace",
    index=False
)

conn.close()


print(
    pairs["match_decision"]
    .value_counts()
)

print("\nDecision by evidence pattern:\n")

print(
    pairs.groupby(
        [
            "phone_match",
            "email_match",
            "address_match",
            "name_match",
            "match_score",
            "match_decision"
        ]
    )
    .size()
    .reset_index(name="pair_count")
    .sort_values(
        ["match_decision", "match_score"],
        ascending=[True, False]
    )
)