from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database import engine


# Demo scope:
# 5 synthetic personnel × 4 weeks = 20 weekly records.
PERSONNEL_COUNT = 5
WEEKS = 4
DEMO_START_DATE = date(2026, 1, 5)  # Monday; synthetic demo date convention.

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "data" / "processed" / "synthetic_full.xlsx"


def week_date(week_index: int) -> date:
    """Convert synthetic week_index to a deterministic demo date."""
    return DEMO_START_DATE + timedelta(days=(int(week_index) - 1) * 7)


def enum_cast(value: str, enum_name: str) -> str:
    """SQL helper used only to make PostgreSQL enum insertion explicit."""
    return f"CAST(:{value} AS {enum_name})"


def main():
    if not EXCEL_PATH.exists():
        raise FileNotFoundError(
            f"Excel file not found: {EXCEL_PATH}\n"
            "Put synthetic_full.xlsx inside data/processed/ first."
        )

    df = pd.read_excel(EXCEL_PATH, sheet_name="Full Synthetic Data")

    required = {
        "personnel_id",
        "week_index",
        "role_category",
        "posting_type",
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
        "self_reported_stress",
        "fatigue_level",
        "mood_score",
        "recovery_feeling",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required Excel columns: {sorted(missing)}")

    # Pick deterministic demo personnel and their first four weeks.
    personnel_ids = sorted(df["personnel_id"].dropna().unique())[:PERSONNEL_COUNT]

    demo = (
        df[df["personnel_id"].isin(personnel_ids)]
        .sort_values(["personnel_id", "week_index"])
        .groupby("personnel_id", group_keys=False)
        .head(WEEKS)
        .copy()
    )

    counts = demo.groupby("personnel_id")["week_index"].nunique()
    incomplete = counts[counts < WEEKS]
    if not incomplete.empty:
        raise ValueError(
            f"Some selected personnel do not have {WEEKS} weeks: "
            f"{incomplete.to_dict()}"
        )

    print("\nTRINETRA demo import")
    print("--------------------")
    print(f"Personnel: {personnel_ids}")
    print(f"Rows:      {len(demo)}")
    print(f"Weeks:     {WEEKS}")
    print(f"Dates:     {DEMO_START_DATE} onward")
    print("\nSelected rows:")
    print(
        demo[
            [
                "personnel_id",
                "week_index",
                "role_category",
                "posting_type",
                "duty_hours_week",
                "avg_sleep_hours",
                "self_reported_stress",
                "fatigue_level",
                "mood_score",
            ]
        ].to_string(index=False)
    )

    with engine.begin() as conn:
        # Rerunnable demo import: only clear the synthetic P001-P005 demo slice.
        # This does NOT touch TRI-001 or other personnel.
        placeholders = ", ".join(f":p{i}" for i in range(len(personnel_ids)))
        params = {f"p{i}": pid for i, pid in enumerate(personnel_ids)}

        conn.execute(
            text(
                f"DELETE FROM wellness_checkins "
                f"WHERE personnel_id IN ({placeholders})"
            ),
            params,
        )
        conn.execute(
            text(
                f"DELETE FROM duty_records "
                f"WHERE personnel_id IN ({placeholders})"
            ),
            params,
        )
        conn.execute(
            text(
                f"DELETE FROM personnel_baselines "
                f"WHERE personnel_id IN ({placeholders})"
            ),
            params,
        )
        conn.execute(
            text(
                f"DELETE FROM personnel "
                f"WHERE personnel_id IN ({placeholders})"
            ),
            params,
        )

        # 1) Personnel + 2) baseline
        for pid in personnel_ids:
            first = demo[demo["personnel_id"] == pid].iloc[0]

            conn.execute(
                text(
                    """
                    INSERT INTO personnel (
                        personnel_id,
                        full_name,
                        codename,
                        rank_post,
                        phone,
                        role_category,
                        posting_type,
                        service_tenure_months
                    )
                    VALUES (
                        :personnel_id,
                        :full_name,
                        :codename,
                        :rank_post,
                        NULL,
                        CAST(:role_category AS role_category_enum),
                        CAST(:posting_type AS posting_type_enum),
                        :service_tenure_months
                    )
                    """
                ),
                {
                    "personnel_id": pid,
                    "full_name": f"Synthetic Personnel {pid}",
                    "codename": pid,
                    "rank_post": "Synthetic Demo",
                    "role_category": str(first["role_category"]),
                    "posting_type": str(first["posting_type"]),
                    "service_tenure_months": int(first["service_tenure_months"]),
                },
            )

            conn.execute(
                text(
                    """
                    INSERT INTO personnel_baselines (
                        personnel_id,
                        baseline_duty_hours,
                        baseline_sleep_hours,
                        baseline_stress,
                        baseline_fatigue,
                        baseline_mood
                    )
                    VALUES (
                        :personnel_id,
                        :baseline_duty_hours,
                        :baseline_sleep_hours,
                        :baseline_stress,
                        :baseline_fatigue,
                        NULL
                    )
                    """
                ),
                {
                    "personnel_id": pid,
                    "baseline_duty_hours": float(first["baseline_duty_hours"]),
                    "baseline_sleep_hours": float(first["baseline_sleep_hours"]),
                    "baseline_stress": float(first["baseline_stress"]),
                    "baseline_fatigue": float(first["baseline_fatigue"]),
                },
            )

        # 3) Weekly duty records + 4) weekly wellness check-ins
        for _, row in demo.iterrows():
            pid = str(row["personnel_id"])
            d = week_date(int(row["week_index"]))

            conn.execute(
                text(
                    """
                    INSERT INTO duty_records (
                        personnel_id,
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
                        days_since_last_leave,
                        source
                    )
                    VALUES (
                        :personnel_id,
                        :week_start,
                        :duty_hours_week,
                        :overtime_hours,
                        :night_shifts,
                        :consecutive_duty_days,
                        :avg_rest_hours,
                        :training_hours,
                        :current_deployment_days,
                        :days_since_last_deployment,
                        :recent_deployment_count,
                        :leave_days_taken,
                        :days_since_last_leave,
                        'synthetic_demo'
                    )
                    """
                ),
                {
                    "personnel_id": pid,
                    "week_start": d,
                    "duty_hours_week": float(row["duty_hours_week"]),
                    "overtime_hours": float(row["overtime_hours"]),
                    "night_shifts": int(row["night_shifts"]),
                    "consecutive_duty_days": int(row["consecutive_duty_days"]),
                    "avg_rest_hours": float(row["avg_rest_hours"]),
                    "training_hours": float(row["training_hours"]),
                    "current_deployment_days": float(row["current_deployment_days"]),
                    "days_since_last_deployment": float(row["days_since_last_deployment"]),
                    "recent_deployment_count": float(row["recent_deployment_count"]),
                    "leave_days_taken": float(row["leave_days_taken"]),
                    "days_since_last_leave": float(row["days_since_last_leave"]),
                },
            )

            conn.execute(
                text(
                    """
                    INSERT INTO wellness_checkins (
                        personnel_id,
                        checkin_date,
                        avg_sleep_hours,
                        sleep_quality,
                        stress_level,
                        fatigue_level,
                        mood_score,
                        recovery_feeling,
                        optional_note,
                        support_requested
                    )
                    VALUES (
                        :personnel_id,
                        :checkin_date,
                        :avg_sleep_hours,
                        :sleep_quality,
                        :stress_level,
                        :fatigue_level,
                        :mood_score,
                        :recovery_feeling,
                        'Synthetic demo check-in',
                        false
                    )
                    """
                ),
                {
                    "personnel_id": pid,
                    "checkin_date": d,
                    "avg_sleep_hours": float(row["avg_sleep_hours"]),
                    "sleep_quality": int(round(row["sleep_quality"])),
                    "stress_level": int(round(row["self_reported_stress"])),
                    "fatigue_level": int(round(row["fatigue_level"])),
                    "mood_score": int(round(row["mood_score"])),
                    "recovery_feeling": int(round(row["recovery_feeling"])),
                },
            )

    print("\n✅ Demo data imported successfully.")
    print("PostgreSQL now contains the small TRINETRA demo slice.")
    print("No deployment/leave/training/transfer event rows were fabricated.")
    print("Hidden synthetic latent-state / target-generation columns were not imported.")


if __name__ == "__main__":
    main()
