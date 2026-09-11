import sqlite3
import pandas as pd
from pathlib import Path
from itertools import combinations

ROOT = Path(__file__).resolve().parents[2]

DB_PATH = ROOT / "database" / "risk_lab.db"

TRUTH_PATH = (
    ROOT
    / "data"
    / "reference"
    / "entity_truth_DO_NOT_USE_FOR_MODELING.csv"
)


# --------------------------------------------------
# Load our decisions
# --------------------------------------------------

conn = sqlite3.connect(DB_PATH)

decisions = pd.read_sql(
    """
    SELECT *
    FROM entity_match_decisions
    """,
    conn
)

conn.close()


# --------------------------------------------------
# Load hidden synthetic truth
# --------------------------------------------------

truth = pd.read_csv(TRUTH_PATH)


# --------------------------------------------------
# Build all true duplicate pairs
# --------------------------------------------------

true_pairs = set()

for entity_id, group in truth.groupby("entity_id"):

    ids = sorted(
        group["customer_record_id"].tolist()
    )

    for a, b in combinations(ids, 2):

        true_pairs.add((a, b))


print(
    f"True duplicate pairs: "
    f"{len(true_pairs):,}"
)


# --------------------------------------------------
# Pairs we predicted as MATCH
# --------------------------------------------------

predicted_matches = set()

for _, row in decisions[
    decisions["match_decision"] == "MATCH"
].iterrows():

    pair = tuple(
        sorted(
            [
                row["customer_record_id_1"],
                row["customer_record_id_2"]
            ]
        )
    )

    predicted_matches.add(pair)


print(
    f"Predicted MATCH pairs: "
    f"{len(predicted_matches):,}"
)


# --------------------------------------------------
# Confusion-style counts
# --------------------------------------------------

true_positives = (
    predicted_matches
    & true_pairs
)

false_positives = (
    predicted_matches
    - true_pairs
)

false_negatives = (
    true_pairs
    - predicted_matches
)


tp = len(true_positives)
fp = len(false_positives)
fn = len(false_negatives)


precision = (
    tp / (tp + fp)
    if (tp + fp) > 0
    else 0
)

recall = (
    tp / (tp + fn)
    if (tp + fn) > 0
    else 0
)

f1 = (
    2 * precision * recall
    / (precision + recall)
    if (precision + recall) > 0
    else 0
)


print("\nENTITY RESOLUTION PERFORMANCE")
print("-----------------------------")

print(f"True positives : {tp:,}")
print(f"False positives: {fp:,}")
print(f"False negatives: {fn:,}")

print(
    f"Precision: {precision:.3f}"
)

print(
    f"Recall   : {recall:.3f}"
)

print(
    f"F1       : {f1:.3f}"
)


# --------------------------------------------------
# Save errors for inspection
# --------------------------------------------------

fp_df = pd.DataFrame(
    false_positives,
    columns=[
        "customer_record_id_1",
        "customer_record_id_2"
    ]
)

fn_df = pd.DataFrame(
    false_negatives,
    columns=[
        "customer_record_id_1",
        "customer_record_id_2"
    ]
)


fp_df.to_csv(
    ROOT
    / "data"
    / "processed"
    / "entity_false_positive_pairs.csv",
    index=False
)

fn_df.to_csv(
    ROOT
    / "data"
    / "processed"
    / "entity_false_negative_pairs.csv",
    index=False
)