import pandas as pd


TREND_TOLERANCE = 0.05


def calculate_overall_risk(
    stress_risk,
    fatigue_risk,
    burnout_risk,
    workload_trend=None,
    stress_trend=None,
    fatigue_trend=None,
    sleep_trend=None
):
    risks = [
        stress_risk,
        fatigue_risk,
        burnout_risk
    ]

    high_count = risks.count("High")
    moderate_count = risks.count("Moderate")

    deterioration_count = 0

    if pd.notna(workload_trend) and workload_trend > TREND_TOLERANCE:
        deterioration_count += 1

    if pd.notna(stress_trend) and stress_trend > TREND_TOLERANCE:
        deterioration_count += 1

    if pd.notna(fatigue_trend) and fatigue_trend > TREND_TOLERANCE:
        deterioration_count += 1

    if pd.notna(sleep_trend) and sleep_trend < -TREND_TOLERANCE:
        deterioration_count += 1

    # High risk
    if high_count >= 2:
        return "High"

    if high_count == 1 and deterioration_count >= 2:
        return "High"

    # Monitor
    if high_count == 1:
        return "Monitor"

    if moderate_count >= 1:
        return "Monitor"

    if deterioration_count >= 2:
        return "Monitor"

    return "Low"


def calculate_welfare_priority(
    overall_risk,
    persistent_high=False,
    severity_trajectory="Stable"
):
    if overall_risk == "High":

        if persistent_high:
            return "Priority"

        if severity_trajectory == "Worsening":
            return "Priority"

        return "Review"

    if overall_risk == "Monitor":

        if severity_trajectory == "Worsening":
            return "Review"

        return "Routine_Monitoring"

    return "Routine_Monitoring"