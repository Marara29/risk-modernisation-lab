import sqlite3
import pandas as pd
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"

conn = sqlite3.connect(DB_PATH)

customers = pd.read_sql(
    """
    SELECT customer_record_id
    FROM customer_records
    """,
    conn
)

matches = pd.read_sql(
    """
    SELECT
        customer_record_id_1,
        customer_record_id_2
    FROM entity_match_decisions
    WHERE match_decision = 'MATCH'
    """,
    conn
)

# --------------------------------------------------
# Union-Find / Disjoint Set
# --------------------------------------------------

parent = {
    customer_id: customer_id
    for customer_id in customers["customer_record_id"]
}


def find(x):
    if parent[x] != x:
        parent[x] = find(parent[x])

    return parent[x]


def union(a, b):
    root_a = find(a)
    root_b = find(b)

    if root_a != root_b:
        parent[root_b] = root_a


# --------------------------------------------------
# Merge all MATCH pairs
# --------------------------------------------------

for _, row in matches.iterrows():

    union(
        row["customer_record_id_1"],
        row["customer_record_id_2"]
    )


# --------------------------------------------------
# Find connected components
# --------------------------------------------------

groups = defaultdict(list)

for customer_id in parent:
    groups[find(customer_id)].append(customer_id)


# --------------------------------------------------
# Assign clean entity IDs
# --------------------------------------------------

rows = []

for i, customer_group in enumerate(
    sorted(groups.values(), key=lambda x: min(x)),
    start=1
):

    entity_id = f"ENTITY_{i:05d}"

    for customer_record_id in customer_group:

        rows.append(
            {
                "entity_id": entity_id,
                "customer_record_id": customer_record_id
            }
        )


entity_map = pd.DataFrame(rows)


# --------------------------------------------------
# Save mapping
# --------------------------------------------------

entity_map.to_sql(
    "customer_entity_map",
    conn,
    if_exists="replace",
    index=False
)

conn.close()


print(f"Customer records: {len(entity_map):,}")
print(
    f"Resolved entities: "
    f"{entity_map['entity_id'].nunique():,}"
)

print("\nLargest entity groups:")

print(
    entity_map
    .groupby("entity_id")
    .size()
    .sort_values(ascending=False)
    .head(20)
)