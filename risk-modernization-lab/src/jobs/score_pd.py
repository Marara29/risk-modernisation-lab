import sqlite3
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"
MODEL_ARTIFACT = ROOT / "artifacts" / "pd_model_v2.joblib"
OUTPUT_PATH = ROOT / "data" / "processed" / "pd_scores.csv"


def main() -> None:
    """Score the current PD population with the saved PD v2 model."""

    if not MODEL_ARTIFACT.exists():
        raise FileNotFoundError(
            "Model artifact not found. Run src/models/models/04_logistic_pd_v2.py first."
        )

    bundle = joblib.load(MODEL_ARTIFACT)

    model = bundle["model"]
    features = bundle["features"]
    threshold = bundle.get("threshold", 0.20)

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql(
        "SELECT * FROM pd_modeling_mart",
        conn,
    )

    conn.close()

    missing = [
        feature
        for feature in features
        if feature not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required scoring features: {missing}"
        )

    scored = df.copy()

    scored["predicted_pd"] = model.predict_proba(
        scored[features]
    )[:, 1]

    scored["high_risk_flag"] = (
        scored["predicted_pd"] >= threshold
    ).astype(int)

    scored["risk_band"] = pd.cut(
        scored["predicted_pd"],
        bins=[
            -float("inf"),
            0.05,
            0.20,
            0.50,
            float("inf"),
        ],
        labels=[
            "LOW",
            "MEDIUM",
            "HIGH",
            "VERY_HIGH",
        ],
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    scored[
        [
            "entity_id",
            "predicted_pd",
            "high_risk_flag",
            "risk_band",
        ]
    ].to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Scored {len(scored):,} entities")
    print(f"Saved scores to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
