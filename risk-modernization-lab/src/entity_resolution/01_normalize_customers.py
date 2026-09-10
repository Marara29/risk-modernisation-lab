import re
import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"


def normalize_text(value):
    if pd.isna(value):
        return None

    value = str(value).lower().strip()

    value = re.sub(r"[^a-z0-9\s]", "", value)
    value = re.sub(r"\s+", " ", value)

    return value


def normalize_phone(value):
    if pd.isna(value):
        return None

    digits = re.sub(r"\D", "", str(value))

    if len(digits) == 10:
        return digits

    return digits if digits else None


def normalize_email(value):
    if pd.isna(value):
        return None

    return str(value).lower().strip()


def normalize_address(value):
    if pd.isna(value):
        return None

    value = str(value).lower().strip()

    replacements = {
        " street": " st",
        " road": " rd",
        " avenue": " ave",
        " boulevard": " blvd",
        " drive": " dr",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = re.sub(r"[^a-z0-9\s]", "", value)
    value = re.sub(r"\s+", " ", value)

    return value


conn = sqlite3.connect(DB_PATH)

customers = pd.read_sql(
    "SELECT * FROM customer_records",
    conn
)

customers["name_normalized"] = (
    customers["name"].apply(normalize_text)
)

customers["phone_normalized"] = (
    customers["phone"].apply(normalize_phone)
)

customers["email_normalized"] = (
    customers["email"].apply(normalize_email)
)

customers["address_normalized"] = (
    customers["address"].apply(normalize_address)
)


customers.to_sql(
    "customer_identity_normalized",
    conn,
    if_exists="replace",
    index=False
)

conn.close()

print(
    customers[
        [
            "customer_record_id",
            "name",
            "name_normalized",
            "phone",
            "phone_normalized",
            "address",
            "address_normalized",
        ]
    ].head(20)
)

## this Normalization step  is a very important first step in entity resolution because you want to compare the meaning of values, not differences in formatting.
## you might have multiple rows for same client , just because one has upper case address and other lower case address ,
# Note if u see many records for one acc ,, it dont necessarily mean its duplicates ,, we jump to another step called candidate generation and match scoring

