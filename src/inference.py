import pandas as pd

from src.predictor import predict_welfare_risk
from src.policy_engine import (
    calculate_overall_risk,
    calculate_welfare_priority
)


def run_inference(
    input_df: pd.DataFrame,
    workload_trend=None,
    stress_trend=None,
    fatigue_trend=None,
    sleep_trend=None,
    persistent_high=False,
    severity_trajectory="Stable"
):
    # ML predictions
    prediction = predict_welfare_risk(input_df)

    # Policy Engine
    overall_risk = calculate_overall_risk(
        stress_risk=prediction["stress_risk"],
        fatigue_risk=prediction["fatigue_risk"],
        burnout_risk=prediction["burnout_risk"],
        workload_trend=workload_trend,
        stress_trend=stress_trend,
        fatigue_trend=fatigue_trend,
        sleep_trend=sleep_trend
    )

    welfare_priority = calculate_welfare_priority(
        overall_risk=overall_risk,
        persistent_high=persistent_high,
        severity_trajectory=severity_trajectory
    )

    return {
        **prediction,
        "overall_risk": overall_risk,
        "welfare_priority": welfare_priority,
        "severity_trajectory": severity_trajectory,
        "persistent_high": persistent_high
    }