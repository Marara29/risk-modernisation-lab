import sqlite3
import pandas as pd

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "database" / "risk_lab.db"


conn = sqlite3.connect(DB_PATH)

df = pd.read_sql(
    "SELECT * FROM pd_modeling_mart",
    conn
)

conn.close()


features = [
    "account_count",
    "total_credit_limit",
    "total_current_balance",
    "entity_utilization",
    "max_single_account_limit",
    "max_single_account_balance",
    "missing_balance_count",
    "max_dpd_history",
    "accounts_ever_30_dpd",
    "accounts_ever_60_dpd",
    "accounts_ever_90_dpd",
    "delinquent_snapshots_30plus",
    "ever_30_dpd",
    "ever_60_dpd",
    "ever_90_dpd",
    "current_max_dpd"
]


X = df[features]
y = df["default_180d"]


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


model = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000))
    ]
)


model.fit(X_train, y_train)

val_pd = model.predict_proba(X_val)[:, 1] ## Use the trained model to calculate the probability of default for every row in the validation set and return second column only([:,1])

thresholds = [
    0.50,
    0.40,
    0.30,
    0.20,
    0.10
]


for threshold in thresholds:

    pred = (
        val_pd >= threshold ## takes the predicted probabilities in val_pd and converts them into true/false if its equal or more than the threshold and as.type(int) makes it 1 or 0
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
# Final evaluation on untouched test set
# --------------------------------------------------

TEST_THRESHOLD = 0.20

test_pd = model.predict_proba(X_test)[:, 1]

test_pred = (
    test_pd >= TEST_THRESHOLD
).astype(int)

test_precision = precision_score(
    y_test,
    test_pred,
    zero_division=0
)

test_recall = recall_score(
    y_test,
    test_pred
)

test_f1 = f1_score(
    y_test,
    test_pred
)

tn, fp, fn, tp = confusion_matrix(
    y_test,
    test_pred
).ravel()

print("\nFINAL TEST PERFORMANCE")
print("----------------------")

print(f"Threshold : {TEST_THRESHOLD:.2f}")
print(f"Precision : {test_precision:.3f}")
print(f"Recall    : {test_recall:.3f}")
print(f"F1        : {test_f1:.3f}")

print(
    f"TP={tp} FP={fp} FN={fn} TN={tn}"
)

#Business story would be ,,At a 20% PD threshold, we catch about 2 out of every 3 future defaults, while incorrectly flagging about 6% of the non-defaulters.”



# --------------------------------------------------
### Model coefficients (understand why the model predicts risk)


logistic_model = model.named_steps["model"]

coefficients = pd.DataFrame({
    "feature": features,
    "coefficient": logistic_model.coef_[0]
})

coefficients["abs_coefficient"] = (
    coefficients["coefficient"].abs()
)

coefficients = coefficients.sort_values(
    "abs_coefficient",
    ascending=False
)

print("\nMODEL COEFFICIENTS")
print("------------------")

print(
    coefficients[
        ["feature", "coefficient"]
    ].to_string(index=False)
)

# explanation ------

# positive coefficient
#→ pushes predicted default risk UP

#negative coefficient
#→ pushes predicted default risk DOWN

#larger absolute coefficient
#→ stronger influence in this logistic model