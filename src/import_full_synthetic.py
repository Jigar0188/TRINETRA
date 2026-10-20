from datetime import date, timedelta

from sqlalchemy import text

from baseline import generate_personnel_baselines
from weekly_simulation import simulate_personnel_weeks
from database import engine


# ============================================================
# TRINETRA — FULL SYNTHETIC DATABASE IMPORT
# ============================================================
# 500 personnel × 26 weeks = 13,000 weekly records.
# This replaces only the synthetic P001-P500 slice.
# TRI-001 and any other non-P001-P500 personnel are preserved.
# ============================================================

PERSONNEL_COUNT = 500
WEEKS = 26
START_DATE = date(2026, 1, 5)  # Monday


def week_date(week_index: int) -> date:
    return START_DATE + timedelta(days=(int(week_index) - 1) * 7)


def main():
    print("\nTRINETRA — Full Synthetic DB Import")
    print("====================================")
    print(f"Personnel : {PERSONNEL_COUNT}")
    print(f"Weeks     : {WEEKS}")
    print(f"Weekly rows: {PERSONNEL_COUNT * WEEKS}")

    # --------------------------------------------------------
    # 1. Generate the same synthetic population used by the ML
    #    data-generation pipeline.
    # --------------------------------------------------------
    personnel_df = generate_personnel_baselines(PERSONNEL_COUNT)

    # --------------------------------------------------------
    # 2. Generate 26 weeks of temporal duty + wellness data.
    # --------------------------------------------------------
    weekly_df = simulate_personnel_weeks(
        personnel_df,
        n_weeks=WEEKS,
    )

    expected_rows = PERSONNEL_COUNT * WEEKS
    if len(weekly_df) != expected_rows:
        raise ValueError(
            f"Expected {expected_rows} weekly rows, "
            f"but generated {len(weekly_df)}."
        )

    # --------------------------------------------------------
    # 3. Prepare database rows.
    # --------------------------------------------------------
    personnel_rows = []
    baseline_rows = []

    for _, person in personnel_df.iterrows():
        pid = str(person["personnel_id"])

        personnel_rows.append({
            "personnel_id": pid,
            "full_name": f"Synthetic Personnel {pid}",
            "codename": pid,
            "rank_post": "Synthetic Demo",
            "role_category": str(person["role_category"]),
            "posting_type": str(person["posting_type"]),
            "service_tenure_months": int(person["service_tenure_months"]),
        })

        baseline_rows.append({
            "personnel_id": pid,
            "baseline_duty_hours": float(person["baseline_duty_hours"]),
            "baseline_sleep_hours": float(person["baseline_sleep_hours"]),
            "baseline_stress": float(person["baseline_stress"]),
            "baseline_fatigue": float(person["baseline_fatigue"]),
            "baseline_mood": float(person["baseline_mood"]),
        })

    duty_rows = []
    wellness_rows = []

    for _, row in weekly_df.iterrows():
        pid = str(row["personnel_id"])
        d = week_date(int(row["week_index"]))

        duty_rows.append({
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
        })

        wellness_rows.append({
            "personnel_id": pid,
            "checkin_date": d,
            "avg_sleep_hours": float(row["avg_sleep_hours"]),
            "sleep_quality": int(round(row["sleep_quality"])),
            "stress_level": int(round(row["self_reported_stress"])),
            "fatigue_level": int(round(row["fatigue_level"])),
            "mood_score": int(round(row["mood_score"])),
            "recovery_feeling": int(round(row["recovery_feeling"])),
        })

    # --------------------------------------------------------
    # 4. Replace only the P001-P500 synthetic slice.
    #    TRI-001 is intentionally preserved.
    # --------------------------------------------------------
    pids = [f"P{i:03d}" for i in range(1, PERSONNEL_COUNT + 1)]

    with engine.begin() as conn:
        conn.execute(
            text("""
                DELETE FROM wellness_checkins
                WHERE personnel_id LIKE 'P%'
                  AND personnel_id ~ '^P[0-9]{3}$'
                  AND CAST(SUBSTRING(personnel_id FROM 2) AS INTEGER)
                      BETWEEN 1 AND 500
            """)
        )

        conn.execute(
            text("""
                DELETE FROM duty_records
                WHERE personnel_id LIKE 'P%'
                  AND personnel_id ~ '^P[0-9]{3}$'
                  AND CAST(SUBSTRING(personnel_id FROM 2) AS INTEGER)
                      BETWEEN 1 AND 500
            """)
        )

        conn.execute(
            text("""
                DELETE FROM personnel_baselines
                WHERE personnel_id LIKE 'P%'
                  AND personnel_id ~ '^P[0-9]{3}$'
                  AND CAST(SUBSTRING(personnel_id FROM 2) AS INTEGER)
                      BETWEEN 1 AND 500
            """)
        )

        conn.execute(
            text("""
                DELETE FROM personnel
                WHERE personnel_id LIKE 'P%'
                  AND personnel_id ~ '^P[0-9]{3}$'
                  AND CAST(SUBSTRING(personnel_id FROM 2) AS INTEGER)
                      BETWEEN 1 AND 500
            """)
        )

        # Personnel
        conn.execute(
            text("""
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
            """),
            personnel_rows,
        )

        # Baselines
        conn.execute(
            text("""
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
                    :baseline_mood
                )
            """),
            baseline_rows,
        )

        # Duty history
        conn.execute(
            text("""
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
                    'synthetic_full'
                )
            """),
            duty_rows,
        )

        # Wellness history
        conn.execute(
            text("""
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
                    'Synthetic full-population demo check-in',
                    false
                )
            """),
            wellness_rows,
        )

        # ----------------------------------------------------
        # 5. Verify what is actually in PostgreSQL.
        # ----------------------------------------------------
        personnel_count = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM personnel
                WHERE personnel_id ~ '^P[0-9]{3}$'
                  AND CAST(SUBSTRING(personnel_id FROM 2) AS INTEGER)
                      BETWEEN 1 AND 500
            """)
        ).scalar_one()

        duty_count = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM duty_records
                WHERE personnel_id ~ '^P[0-9]{3}$'
                  AND CAST(SUBSTRING(personnel_id FROM 2) AS INTEGER)
                      BETWEEN 1 AND 500
            """)
        ).scalar_one()

        wellness_count = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM wellness_checkins
                WHERE personnel_id ~ '^P[0-9]{3}$'
                  AND CAST(SUBSTRING(personnel_id FROM 2) AS INTEGER)
                      BETWEEN 1 AND 500
            """)
        ).scalar_one()

    print("\n✅ FULL SYNTHETIC DATA IMPORTED")
    print(f"Personnel : {personnel_count}")
    print(f"Duty rows : {duty_count}")
    print(f"Wellness  : {wellness_count}")
    print("TRI-001 and other non-P001-P500 records were preserved.")
    print("\nNext: test /predict/P001 and /predict/P500 before changing dashboard endpoints.")


if __name__ == "__main__":
    main()
