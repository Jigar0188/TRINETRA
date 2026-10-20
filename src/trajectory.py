def determine_severity_trajectory(
    workload_trend: float,
    stress_trend: float,
    fatigue_trend: float,
    sleep_trend: float,
) -> str:
    """
    Determine the current welfare trajectory from recent trend signals.

    Positive stress/fatigue/workload trends indicate deterioration.
    Negative sleep trend indicates deterioration.

    Thresholds follow the same 0.05 signal threshold already used
    by the unit-level dashboard logic.
    """
    deterioration_signals = [
        workload_trend > 0.05,
        stress_trend > 0.05,
        fatigue_trend > 0.05,
        sleep_trend < -0.05,
    ]

    improvement_signals = [
        workload_trend < -0.05,
        stress_trend < -0.05,
        fatigue_trend < -0.05,
        sleep_trend > 0.05,
    ]

    worsening_count = sum(deterioration_signals)
    improving_count = sum(improvement_signals)

    # Require at least two aligned signals so one noisy trend
    # does not determine the trajectory by itself.
    if worsening_count >= 2 and worsening_count > improving_count:
        return "Worsening"

    if improving_count >= 2 and improving_count > worsening_count:
        return "Improving"

    return "Stable"
