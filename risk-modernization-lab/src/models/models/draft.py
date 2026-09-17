
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

brier = brier_score_loss(
    y_val,
    val_pd
)

print("\nCALIBRATION")
print("-----------")
print(f"Brier Score: {brier:.4f}")