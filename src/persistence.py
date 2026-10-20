"""TRINETRA persistent-high risk detection."""

import pandas as pd
from sqlalchemy.orm import Session

from src.db_ml_bridge import build_ml_feature_history
from src.predictor import predict_welfare_risk
from src.policy_engine import calculate_overall_risk


def is_persistent_high(
    db: Session,
    personnel_id: str,
    consecutive_weeks: int = 2,
) -> bool:
    """
    Return True when overall welfare risk is High for the latest
    `consecutive_weeks` valid ML history rows.

    The rule is intentionally simple for the TRINETRA prototype:
    two consecutive High overall-risk weeks = persistent high risk.
    """
    if consecutive_weeks < 1:
        raise ValueError("consecutive_weeks must be at least 1")

    history = build_ml_feature_history(db, personnel_id)

    if len(history) < consecutive_weeks:
        return False

    overall_risks = []

    for _, row in history.iterrows():
        row_df = pd.DataFrame([row])
        prediction = predict_welfare_risk(row_df)

        overall = calculate_overall_risk(
            stress_risk=prediction["stress_risk"],
            fatigue_risk=prediction["fatigue_risk"],
            burnout_risk=prediction["burnout_risk"],
            workload_trend=float(row["workload_trend"]),
            stress_trend=float(row["stress_trend"]),
            fatigue_trend=float(row["fatigue_trend"]),
            sleep_trend=float(row["sleep_trend"]),
        )

        overall_risks.append(overall)

    recent = overall_risks[-consecutive_weeks:]
    return all(risk == "High" for risk in recent)
