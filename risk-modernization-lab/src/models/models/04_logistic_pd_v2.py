
#---------------------------------------------------

## this time we reduce features to 7 features from 16 ,, just to see if simple model might outperform the previous one .. I noticed a lot redudancy after running feature correlation

import sqlite3
import pandas as pd

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "database" / "risk_lab.db"


# --------------------------------------------------
# Load modeling mart
# --------------------------------------------------

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql(
    "SELECT * FROM pd_modeling_mart",
    conn
)

conn.close()


# --------------------------------------------------
# Cleaner feature set
# --------------------------------------------------

features_v2 = [
    "account_count",
    "total_credit_limit",
    "entity_utilization",
    "missing_balance_count",
    "current_max_dpd",
    "delinquent_snapshots_30plus",
    "ever_90_dpd"
]


X = df[features_v2]
y = df["default_180d"]


# --------------------------------------------------
# Same split as Model v1
# --------------------------------------------------

X_train, X_temp, y_train, y_temp = train_test_split(
    X,
    y,
    test_size=0.40,
    stratify=y,
    random_state=42
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp,
    y_temp,
    test_size=0.50,
    stratify=y_temp,
    random_state=42
)


# --------------------------------------------------
# Model
# --------------------------------------------------

model = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000))
    ]
)

model.fit(X_train, y_train)


# --------------------------------------------------
# Validation evaluation
# --------------------------------------------------

val_pd = model.predict_proba(X_val)[:, 1]


print("\nMODEL V2 - VALIDATION")
print("---------------------")

print(
    f"ROC-AUC: {roc_auc_score(y_val, val_pd):.3f}"
)

print(
    f"PR-AUC : {average_precision_score(y_val, val_pd):.3f}"
)


# --------------------------------------------------
# Threshold analysis
# --------------------------------------------------

thresholds = [
    0.50,
    0.40,
    0.30,
    0.20,
    0.10
]

for threshold in thresholds:

    pred = (
        val_pd >= threshold
    ).astype(int)

    precision = precision_score(
        y_val,
        pred,
        zero_division=0
    )

    recall = recall_score(
        y_val,
        pred
    )

    f1 = f1_score(
        y_val,
        pred
    )

    tn, fp, fn, tp = confusion_matrix(
        y_val,
        pred
    ).ravel()

    print(
        f"\nThreshold: {threshold:.2f}"
    )

    print(
        f"Precision: {precision:.3f}"
    )

    print(
        f"Recall   : {recall:.3f}"
    )

    print(
        f"F1       : {f1:.3f}"
    )

    print(
        f"TP={tp} FP={fp} FN={fn} TN={tn}"
    )


# --------------------------------------------------
# Coefficients
# --------------------------------------------------

logistic_model = model.named_steps["model"]

coefficients = pd.DataFrame({
    "feature": features_v2,
    "coefficient": logistic_model.coef_[0]
})

coefficients["abs_coefficient"] = (
    coefficients["coefficient"].abs()
)

coefficients = coefficients.sort_values(
    "abs_coefficient",
    ascending=False
)

print("\nMODEL V2 COEFFICIENTS")
print("---------------------")

print(
    coefficients[
        ["feature", "coefficient"]
    ].to_string(index=False)
)

##Calibration asks:

#“When the model says someone has a 20% PD, do about 20% of similar customers actually default?”

from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss


brier = brier_score_loss(
    y_val,
    val_pd
)

print("\nCALIBRATION")
print("-----------")
print(f"Brier Score: {brier:.4f}")


prob_true, prob_pred = calibration_curve(
    y_val,
    val_pd,
    n_bins=5,
    strategy="quantile"
)

calibration_df = pd.DataFrame({
    "predicted_pd": prob_pred,
    "actual_default_rate": prob_true
})

print("\nCalibration by risk bucket:")
print(
    calibration_df.to_string(
        index=False
    )
)
## we want our predicted pd close to actual defaults ,, thats a good calibration .. otherwise if one is bigger that other ,, we might be having overestimating or underestimating risk

print (val_pd.mean())
print (y_val.mean())

print("Validation default rate:", y_val.mean())
print("Brier Score:", brier)

## Now Risk bands on untouched test population

# --------------------------------------------------





test_pd = model.predict_proba(X_test)[:, 1]

risk_results = pd.DataFrame({
    "actual_default": y_test.values,
    "predicted_pd": test_pd
})


risk_results["risk_band"] = pd.cut(
    risk_results["predicted_pd"],
    bins=[
        -float("inf"),
        0.05,
        0.20,
        0.50,
        float("inf")
    ],
    labels=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "VERY_HIGH"
    ]
)


risk_band_summary = (
    risk_results
    .groupby(
        "risk_band",
        observed=False
    )
    .agg(
        customers=("actual_default", "count"),
        defaults=("actual_default", "sum"),
        avg_predicted_pd=("predicted_pd", "mean"),
        actual_default_rate=("actual_default", "mean")
    )
    .reset_index()
)


risk_band_summary["avg_predicted_pd"] *= 100
risk_band_summary["actual_default_rate"] *= 100


print("\nRISK BAND SUMMARY")
print("-----------------")

print(
    risk_band_summary.to_string(
        index=False
    )
)

#-------------END OF PD MODELLING ----------

#We built a point-in-time PD modeling mart, trained an interpretable logistic model, simplified correlated features,
#  validated discrimination, selected a business threshold, checked calibration, and converted PDs into practical risk
#  bands with clear separation in observed default rates.