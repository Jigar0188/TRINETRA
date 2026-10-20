"""
TRINETRA — Database -> ML feature bridge

Fetches a personnel member's weekly records from PostgreSQL and
recreates the feature-engineering logic used during model training.

This module does NOT run the ML models yet.
It only prepares the latest ML-ready feature row.
"""

import numpy as np
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session


ML_FEATURE_COLUMNS = [
    # Context
    "role_category",
    "posting_type",
    "service_tenure_months",

    # Duty / workload
    "duty_hours_week",
    "overtime_hours",
    "night_shifts",
    "consecutive_duty_days",
    "avg_rest_hours",
    "training_hours",

    # Deployment
    "current_deployment_days",
    "days_since_last_deployment",
    "recent_deployment_count",

    # Leave / stability
    "leave_days_taken",
    "days_since_last_leave",

    # Sleep / wellness
    "avg_sleep_hours",
    "sleep_quality",
    "self_reported_stress",
    "fatigue_level",
    "mood_score",
    "recovery_feeling",

    # Personal deviations
    "duty_deviation",
    "sleep_deviation",
    "stress_deviation",
    "fatigue_deviation",

    # Engineered workload
    "workload_index",

    # Temporal trends
    "workload_trend",
    "stress_trend",
    "fatigue_trend",
    "sleep_trend",

    # Signal consistency
    "signal_agreement",

    # Pressure features
    "stress_pressure",
    "fatigue_pressure",
    "stress_trend_pressure",
]


def normalize(value, lower, upper):
    return np.clip(
        (value - lower) / (upper - lower),
        0,
        1
    )


def positive_pressure(value, lower, upper):
    normalized = (value - lower) / (upper - lower)
    return np.clip(normalized, 0, 1)


def calculate_trend(series):
    if len(series) < 2:
        return np.nan

    x = np.arange(len(series))
    return np.polyfit(x, series, 1)[0]


def fetch_personnel_feature_data(
    db: Session,
    personnel_id: str
) -> pd.DataFrame:
    """
    Fetch the raw data needed to recreate the ML features.

    Returns all available weekly records for the requested personnel,
    ordered chronologically.
    """

    personnel = db.execute(
        text("""
            SELECT
                personnel_id,
                role_category,
                posting_type,
                service_tenure_months
            FROM personnel
            WHERE personnel_id = :personnel_id
        """),
        {"personnel_id": personnel_id}
    ).mappings().first()

    if personnel is None:
        raise ValueError(
            f"Personnel '{personnel_id}' was not found."
        )

    baseline = db.execute(
        text("""
            SELECT
                baseline_duty_hours,
                baseline_sleep_hours,
                baseline_stress,
                baseline_fatigue
            FROM personnel_baselines
            WHERE personnel_id = :personnel_id
        """),
        {"personnel_id": personnel_id}
    ).mappings().first()

    if baseline is None:
        raise ValueError(
            f"Baseline data for '{personnel_id}' was not found."
        )

    duty_rows = db.execute(
        text("""
            SELECT
                week_start,
                duty_hours_week,
                overtime_hours,
                night_shifts,
                consecutive_duty_days,
                avg_rest_hours,
                training_hours,
                current_deployment_days,
                days_since_last_deployment,
                recent_deployment_count,
                leave_days_taken,
                days_since_last_leave
            FROM duty_records
            WHERE personnel_id = :personnel_id
            ORDER BY week_start
        """),
        {"personnel_id": personnel_id}
    ).mappings().all()

    wellness_rows = db.execute(
        text("""
            SELECT
                checkin_date,
                avg_sleep_hours,
                sleep_quality,
                stress_level,
                fatigue_level,
                mood_score,
                recovery_feeling
            FROM wellness_checkins
            WHERE personnel_id = :personnel_id
            ORDER BY checkin_date
        """),
        {"personnel_id": personnel_id}
    ).mappings().all()

    if not duty_rows:
        raise ValueError(
            f"No duty records found for '{personnel_id}'."
        )

    if not wellness_rows:
        raise ValueError(
            f"No wellness records found for '{personnel_id}'."
        )

    duty_df = pd.DataFrame(duty_rows)
    wellness_df = pd.DataFrame(wellness_rows)

    # The demo importer uses the same weekly date for duty and wellness.
    df = duty_df.merge(
        wellness_df,
        left_on="week_start",
        right_on="checkin_date",
        how="inner"
    )

    if df.empty:
        raise ValueError(
            f"No matching duty/wellness weeks found for '{personnel_id}'."
        )

    # Add personnel context.
    for key, value in personnel.items():
        df[key] = value

    # Add baseline values.
    for key, value in baseline.items():
        df[key] = value

    # PostgreSQL NUMERIC/DECIMAL values can arrive as Decimal objects.
    # Convert all numeric ML inputs to regular Python floats so that
    # pandas/numpy arithmetic works consistently.
    numeric_columns = [
        "service_tenure_months",
        "baseline_duty_hours",
        "baseline_sleep_hours",
        "baseline_stress",
        "baseline_fatigue",
        "duty_hours_week",
        "overtime_hours",
        "night_shifts",
        "consecutive_duty_days",
        "avg_rest_hours",
        "training_hours",
        "current_deployment_days",
        "days_since_last_deployment",
        "recent_deployment_count",
        "leave_days_taken",
        "days_since_last_leave",
        "avg_sleep_hours",
        "sleep_quality",
        "stress_level",
        "fatigue_level",
        "mood_score",
        "recovery_feeling",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="raise"
            ).astype(float)

    # Reconstruct week_index from chronological records.
    df = df.sort_values("week_start").reset_index(drop=True)
    df["week_index"] = np.arange(1, len(df) + 1)

    # The database uses stress_level, while the ML dataset uses
    # self_reported_stress.
    df["self_reported_stress"] = df["stress_level"]

    return df


def build_ml_feature_history(
    db: Session,
    personnel_id: str
) -> pd.DataFrame:
    """
    Recreate the training-time feature engineering for all available
    weekly records and return the ML-ready rows with valid 4-week trends.

    The first three weeks do not have 4-week rolling trends and are
    therefore excluded from the returned ML history.
    """

    feature_df = fetch_personnel_feature_data(
        db=db,
        personnel_id=personnel_id
    )

    # ---------------------------------------------------------
    # Personal baseline deviations
    # ---------------------------------------------------------

    feature_df["duty_deviation"] = (
        feature_df["duty_hours_week"]
        - feature_df["baseline_duty_hours"]
    )

    feature_df["sleep_deviation"] = (
        feature_df["baseline_sleep_hours"]
        - feature_df["avg_sleep_hours"]
    )

    feature_df["stress_deviation"] = (
        feature_df["self_reported_stress"]
        - feature_df["baseline_stress"]
    )

    feature_df["fatigue_deviation"] = (
        feature_df["fatigue_level"]
        - feature_df["baseline_fatigue"]
    )

    # ---------------------------------------------------------
    # Workload pressure
    # ---------------------------------------------------------

    feature_df["duty_pressure"] = normalize(
        feature_df["duty_hours_week"], 35, 70
    )

    feature_df["overtime_pressure"] = normalize(
        feature_df["overtime_hours"], 0, 14
    )

    feature_df["night_pressure"] = normalize(
        feature_df["night_shifts"], 0, 5
    )

    feature_df["consecutive_pressure"] = normalize(
        feature_df["consecutive_duty_days"], 1, 10
    )

    feature_df["rest_pressure"] = 1 - normalize(
        feature_df["avg_rest_hours"], 5, 16
    )

    feature_df["training_pressure"] = normalize(
        feature_df["training_hours"], 0, 8
    )

    feature_df["deployment_pressure"] = normalize(
        feature_df["current_deployment_days"], 0, 7
    )

    feature_df["workload_index"] = (
        0.25 * feature_df["duty_pressure"]
        + 0.15 * feature_df["overtime_pressure"]
        + 0.15 * feature_df["night_pressure"]
        + 0.15 * feature_df["consecutive_pressure"]
        + 0.15 * feature_df["rest_pressure"]
        + 0.05 * feature_df["training_pressure"]
        + 0.10 * feature_df["deployment_pressure"]
    )

    # ---------------------------------------------------------
    # Rolling 4-week trends
    # ---------------------------------------------------------

    trend_columns = {
        "workload_index": "workload_trend",
        "self_reported_stress": "stress_trend",
        "fatigue_level": "fatigue_trend",
        "avg_sleep_hours": "sleep_trend",
    }

    for source_col, trend_col in trend_columns.items():
        feature_df[trend_col] = (
            feature_df
            .groupby("personnel_id")[source_col]
            .transform(
                lambda x: x.rolling(
                    window=4,
                    min_periods=4
                ).apply(calculate_trend, raw=False)
            )
        )

    # ---------------------------------------------------------
    # Signal agreement
    # ---------------------------------------------------------

    tolerance = 0.05

    feature_df["workload_deteriorating"] = (
        feature_df["workload_trend"] > tolerance
    )

    feature_df["stress_deteriorating"] = (
        feature_df["stress_trend"] > tolerance
    )

    feature_df["fatigue_deteriorating"] = (
        feature_df["fatigue_trend"] > tolerance
    )

    feature_df["sleep_deteriorating"] = (
        feature_df["sleep_trend"] < -tolerance
    )

    agreement_flags = [
        "workload_deteriorating",
        "stress_deteriorating",
        "fatigue_deteriorating",
        "sleep_deteriorating",
    ]

    feature_df["signal_agreement"] = (
        feature_df[agreement_flags].sum(axis=1) / 4
    )

    trend_cols = [
        "workload_trend",
        "stress_trend",
        "fatigue_trend",
        "sleep_trend",
    ]

    insufficient_history = feature_df[trend_cols].isna().any(axis=1)

    feature_df.loc[
        insufficient_history,
        "signal_agreement"
    ] = np.nan

    # ---------------------------------------------------------
    # Pressure features used by the trained models
    # ---------------------------------------------------------

    feature_df["stress_pressure"] = positive_pressure(
        feature_df["stress_deviation"], 0, 2
    )

    feature_df["fatigue_pressure"] = positive_pressure(
        feature_df["fatigue_deviation"], 0, 2
    )

    feature_df["stress_trend_pressure"] = positive_pressure(
        feature_df["stress_trend"], 0, 0.5
    )


    # Only rows with all required trend features can be passed to the
    # trained models. This normally means week 4 onward.
    valid = feature_df[trend_cols].notna().all(axis=1)

    history = feature_df.loc[valid, ML_FEATURE_COLUMNS].copy()

    if history.empty:
        raise ValueError(
            f"'{personnel_id}' does not have enough weekly history "
            "to calculate the 4-week ML trends."
        )

    return history.reset_index(drop=True)


def build_latest_ml_features(
    db: Session,
    personnel_id: str
) -> pd.DataFrame:
    """
    Recreate the training-time feature engineering and return
    exactly one ML-ready row for the latest available week.
    """

    history = build_ml_feature_history(
        db=db,
        personnel_id=personnel_id
    )

    return history.iloc[[-1]].reset_index(drop=True)

def build_all_latest_ml_features(db: Session) -> pd.DataFrame:
    """
    Build latest ML-ready features for all personnel in one bulk operation.

    Returns:
        DataFrame containing:
        personnel_id + 33 ML feature columns
    """

    # ---------------------------------------------------------
    # Fetch all required DB data in ONE query
    # ---------------------------------------------------------

    result = db.execute(
        text("""
            SELECT
                p.personnel_id,
                p.role_category,
                p.posting_type,
                p.service_tenure_months,

                b.baseline_duty_hours,
                b.baseline_sleep_hours,
                b.baseline_stress,
                b.baseline_fatigue,

                d.week_start,
                d.duty_hours_week,
                d.overtime_hours,
                d.night_shifts,
                d.consecutive_duty_days,
                d.avg_rest_hours,
                d.training_hours,
                d.current_deployment_days,
                d.days_since_last_deployment,
                d.recent_deployment_count,
                d.leave_days_taken,
                d.days_since_last_leave,

                w.avg_sleep_hours,
                w.sleep_quality,
                w.stress_level,
                w.fatigue_level,
                w.mood_score,
                w.recovery_feeling

            FROM personnel p

            INNER JOIN personnel_baselines b
                ON p.personnel_id = b.personnel_id

            INNER JOIN duty_records d
                ON p.personnel_id = d.personnel_id

            INNER JOIN wellness_checkins w
                ON p.personnel_id = w.personnel_id
                AND d.week_start = w.checkin_date

            ORDER BY
                p.personnel_id,
                d.week_start
        """)
    )

    rows = result.mappings().all()

    if not rows:
        raise ValueError("No personnel feature data found in database.")

    feature_df = pd.DataFrame(rows)

    # ---------------------------------------------------------
    # Numeric conversion
    # ---------------------------------------------------------

    numeric_columns = [
        "service_tenure_months",

        "baseline_duty_hours",
        "baseline_sleep_hours",
        "baseline_stress",
        "baseline_fatigue",

        "duty_hours_week",
        "overtime_hours",
        "night_shifts",
        "consecutive_duty_days",
        "avg_rest_hours",
        "training_hours",

        "current_deployment_days",
        "days_since_last_deployment",
        "recent_deployment_count",

        "leave_days_taken",
        "days_since_last_leave",

        "avg_sleep_hours",
        "sleep_quality",
        "stress_level",
        "fatigue_level",
        "mood_score",
        "recovery_feeling",
    ]

    for column in numeric_columns:
        feature_df[column] = pd.to_numeric(
            feature_df[column],
            errors="coerce"
        )

    # ---------------------------------------------------------
    # Sort + reconstruct week index
    # ---------------------------------------------------------

    feature_df = (
        feature_df
        .sort_values(
            ["personnel_id", "week_start"]
        )
        .reset_index(drop=True)
    )

    feature_df["week_index"] = (
        feature_df
        .groupby("personnel_id")
        .cumcount()
        + 1
    )

    # Same naming used during model training
    feature_df["self_reported_stress"] = (
        feature_df["stress_level"]
    )

    # ---------------------------------------------------------
    # Personal baseline deviations
    # ---------------------------------------------------------

    feature_df["duty_deviation"] = (
        feature_df["duty_hours_week"]
        - feature_df["baseline_duty_hours"]
    )

    feature_df["sleep_deviation"] = (
        feature_df["baseline_sleep_hours"]
        - feature_df["avg_sleep_hours"]
    )

    feature_df["stress_deviation"] = (
        feature_df["self_reported_stress"]
        - feature_df["baseline_stress"]
    )

    feature_df["fatigue_deviation"] = (
        feature_df["fatigue_level"]
        - feature_df["baseline_fatigue"]
    )

    # ---------------------------------------------------------
    # Workload pressure
    # ---------------------------------------------------------

    feature_df["duty_pressure"] = normalize(
        feature_df["duty_hours_week"], 35, 70
    )

    feature_df["overtime_pressure"] = normalize(
        feature_df["overtime_hours"], 0, 14
    )

    feature_df["night_pressure"] = normalize(
        feature_df["night_shifts"], 0, 5
    )

    feature_df["consecutive_pressure"] = normalize(
        feature_df["consecutive_duty_days"], 1, 10
    )

    feature_df["rest_pressure"] = (
        1 - normalize(
            feature_df["avg_rest_hours"], 5, 16
        )
    )

    feature_df["training_pressure"] = normalize(
        feature_df["training_hours"], 0, 8
    )

    feature_df["deployment_pressure"] = normalize(
        feature_df["current_deployment_days"], 0, 7
    )

    feature_df["workload_index"] = (
        0.25 * feature_df["duty_pressure"]
        + 0.15 * feature_df["overtime_pressure"]
        + 0.15 * feature_df["night_pressure"]
        + 0.15 * feature_df["consecutive_pressure"]
        + 0.15 * feature_df["rest_pressure"]
        + 0.05 * feature_df["training_pressure"]
        + 0.10 * feature_df["deployment_pressure"]
    )

    # ---------------------------------------------------------
    # 4-week rolling trends
    # ---------------------------------------------------------

    trend_columns = {
        "workload_index": "workload_trend",
        "self_reported_stress": "stress_trend",
        "fatigue_level": "fatigue_trend",
        "avg_sleep_hours": "sleep_trend",
    }

    for source_col, trend_col in trend_columns.items():
        feature_df[trend_col] = (
            feature_df
            .groupby("personnel_id")[source_col]
            .transform(
                lambda x: x.rolling(
                    window=4,
                    min_periods=4
                ).apply(
                    calculate_trend,
                    raw=False
                )
            )
        )

    # ---------------------------------------------------------
    # Signal agreement
    # ---------------------------------------------------------

    tolerance = 0.05

    feature_df["workload_deteriorating"] = (
        feature_df["workload_trend"] > tolerance
    )

    feature_df["stress_deteriorating"] = (
        feature_df["stress_trend"] > tolerance
    )

    feature_df["fatigue_deteriorating"] = (
        feature_df["fatigue_trend"] > tolerance
    )

    feature_df["sleep_deteriorating"] = (
        feature_df["sleep_trend"] < -tolerance
    )

    agreement_flags = [
        "workload_deteriorating",
        "stress_deteriorating",
        "fatigue_deteriorating",
        "sleep_deteriorating",
    ]

    feature_df["signal_agreement"] = (
        feature_df[agreement_flags].sum(axis=1) / 4
    )

    # ---------------------------------------------------------
    # Pressure features
    # ---------------------------------------------------------

    feature_df["stress_pressure"] = positive_pressure(
        feature_df["stress_deviation"],
        0,
        2
    )

    feature_df["fatigue_pressure"] = positive_pressure(
        feature_df["fatigue_deviation"],
        0,
        2
    )

    feature_df["stress_trend_pressure"] = positive_pressure(
        feature_df["stress_trend"],
        0,
        0.5
    )

    # ---------------------------------------------------------
    # Keep only latest valid week per personnel
    # ---------------------------------------------------------

    trend_cols = [
        "workload_trend",
        "stress_trend",
        "fatigue_trend",
        "sleep_trend",
    ]

    latest = (
        feature_df
        .sort_values(
            ["personnel_id", "week_start"]
        )
        .groupby(
            "personnel_id",
            as_index=False
        )
        .tail(1)
        .copy()
    )

    # Remove personnel without enough history
    latest = latest.dropna(
        subset=trend_cols
    )

    # ---------------------------------------------------------
    # Final ML dataset
    # ---------------------------------------------------------

    return latest[
        ["personnel_id"] + ML_FEATURE_COLUMNS
    ].reset_index(drop=True)


from src.predictor import (
    stress_model,
    fatigue_model,
    burnout_model
)

from src.policy_engine import (
    calculate_overall_risk,
    calculate_welfare_priority
) 

def predict_all_latest_ml(db: Session) -> pd.DataFrame:
    """
    Generate batch Stress, Fatigue and Burnout predictions
    for all personnel using the latest ML-ready features.
    """

    # Build 500 × 33 feature matrix
    feature_df = build_all_latest_ml_features(db)

    personnel_ids = feature_df["personnel_id"].copy()

    X = feature_df[ML_FEATURE_COLUMNS]

    # ---------------------------------------------------------
    # Batch ML prediction
    # ---------------------------------------------------------

    stress_predictions = stress_model.predict(X)
    fatigue_predictions = fatigue_model.predict(X)
    burnout_predictions = burnout_model.predict(X)

    # ---------------------------------------------------------
    # Prediction probabilities
    # ---------------------------------------------------------

    stress_probabilities = stress_model.predict_proba(X)
    fatigue_probabilities = fatigue_model.predict_proba(X)
    burnout_probabilities = burnout_model.predict_proba(X)

    # ---------------------------------------------------------
    # Result dataframe
    # ---------------------------------------------------------

    results = pd.DataFrame({
        "personnel_id": personnel_ids,

        "stress_risk": stress_predictions,
        "fatigue_risk": fatigue_predictions,
        "burnout_risk": burnout_predictions,

        "stress_probability": stress_probabilities.max(axis=1),
        "fatigue_probability": fatigue_probabilities.max(axis=1),
        "burnout_probability": burnout_probabilities.max(axis=1),

        "workload_trend": feature_df["workload_trend"].values,
        "stress_trend": feature_df["stress_trend"].values,
        "fatigue_trend": feature_df["fatigue_trend"].values,
        "sleep_trend": feature_df["sleep_trend"].values,
    })

    return results

def run_bulk_inference(db: Session) -> pd.DataFrame:
    """
    Run ML predictions + policy engine for all personnel.
    """

    predictions = predict_all_latest_ml(db)

    results = []

    for _, row in predictions.iterrows():

        overall_risk = calculate_overall_risk(
            stress_risk=row["stress_risk"],
            fatigue_risk=row["fatigue_risk"],
            burnout_risk=row["burnout_risk"],
            workload_trend=row["workload_trend"],
            stress_trend=row["stress_trend"],
            fatigue_trend=row["fatigue_trend"],
            sleep_trend=row["sleep_trend"],
        )

        # -----------------------------------------------------
        # Determine trajectory
        # -----------------------------------------------------

        deterioration_signals = 0
        improvement_signals = 0

        if row["workload_trend"] > 0.05:
            deterioration_signals += 1
        elif row["workload_trend"] < -0.05:
            improvement_signals += 1

        if row["stress_trend"] > 0.05:
            deterioration_signals += 1
        elif row["stress_trend"] < -0.05:
            improvement_signals += 1

        if row["fatigue_trend"] > 0.05:
            deterioration_signals += 1
        elif row["fatigue_trend"] < -0.05:
            improvement_signals += 1

        if row["sleep_trend"] < -0.05:
            deterioration_signals += 1
        elif row["sleep_trend"] > 0.05:
            improvement_signals += 1

        if (
            deterioration_signals >= 2
            and deterioration_signals > improvement_signals
        ):
            severity_trajectory = "Worsening"

        elif (
            improvement_signals >= 2
            and improvement_signals > deterioration_signals
        ):
            severity_trajectory = "Improving"

        else:
            severity_trajectory = "Stable"

        # -----------------------------------------------------
        # Persistent High
        # -----------------------------------------------------

        # Bulk latest prediction does not yet evaluate
        # historical weekly predictions.
        persistent_high = False

        welfare_priority = calculate_welfare_priority(
            overall_risk=overall_risk,
            persistent_high=persistent_high,
            severity_trajectory=severity_trajectory
        )

        results.append({
            "personnel_id": row["personnel_id"],

            "stress_risk": row["stress_risk"],
            "fatigue_risk": row["fatigue_risk"],
            "burnout_risk": row["burnout_risk"],

            "stress_probability": row["stress_probability"],
            "fatigue_probability": row["fatigue_probability"],
            "burnout_probability": row["burnout_probability"],

            "overall_risk": overall_risk,
            "welfare_priority": welfare_priority,

            "severity_trajectory": severity_trajectory,
            "persistent_high": persistent_high,

            "workload_trend": row["workload_trend"],
            "stress_trend": row["stress_trend"],
            "fatigue_trend": row["fatigue_trend"],
            "sleep_trend": row["sleep_trend"],
        })

    return pd.DataFrame(results)
if __name__ == "__main__":
    print("TRINETRA DB -> ML feature bridge")
    print(f"ML feature count: {len(ML_FEATURE_COLUMNS)}")
