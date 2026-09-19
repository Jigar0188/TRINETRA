from pathlib import Path

import joblib
import pandas as pd


# ==========================================
# TRINETRA — ML Predictor
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "models" / "trained_models"


# Load trained models
stress_model = joblib.load(
    MODEL_DIR / "stress_model.joblib"
)

fatigue_model = joblib.load(
    MODEL_DIR / "fatigue_model.joblib"
)

burnout_model = joblib.load(
    MODEL_DIR / "burnout_model.joblib"
)


def predict_welfare_risk(input_df: pd.DataFrame):
    """
    Generate Stress, Fatigue and Burnout predictions
    from the trained TRINETRA ML models.
    """

    stress_prediction = stress_model.predict(input_df)[0]
    fatigue_prediction = fatigue_model.predict(input_df)[0]
    burnout_prediction = burnout_model.predict(input_df)[0]

    stress_probabilities = stress_model.predict_proba(input_df)[0]
    fatigue_probabilities = fatigue_model.predict_proba(input_df)[0]
    burnout_probabilities = burnout_model.predict_proba(input_df)[0]

    return {
        "stress_risk": stress_prediction,
        "fatigue_risk": fatigue_prediction,
        "burnout_risk": burnout_prediction,
"stress_probabilities": {
    key: float(value)
    for key, value in zip(
        stress_model.classes_,
        stress_probabilities
    )
},

"fatigue_probabilities": {
    key: float(value)
    for key, value in zip(
        fatigue_model.classes_,
        fatigue_probabilities
    )
},

        "burnout_probabilities": {
    key: float(value)
    for key, value in zip(
        burnout_model.classes_,
        burnout_probabilities
    )
}
    }


if __name__ == "__main__":
    print("TRINETRA ML Predictor")
    print("Models loaded successfully.")