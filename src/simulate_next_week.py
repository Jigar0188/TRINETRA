from datetime import timedelta
import pandas as pd
from sqlalchemy import text
from database import engine
from weekly_simulation import simulate_personnel_weeks 

PERSONNEL_ID = "P001"
SOURCE = "synthetic_simulation"

def main():
    with engine.begin() as conn:
        baseline = conn.execute(text("""
            SELECT p.personnel_id, p.role_category, p.posting_type,
                   p.service_tenure_months, b.baseline_duty_hours,
                   b.baseline_sleep_hours, b.baseline_stress,
                   b.baseline_fatigue, b.baseline_mood,
                   MAX(d.week_start) AS latest_week_start
            FROM personnel p
            JOIN personnel_baselines b ON b.personnel_id = p.personnel_id
            LEFT JOIN duty_records d ON d.personnel_id = p.personnel_id
            WHERE p.personnel_id = :personnel_id
            GROUP BY p.personnel_id, p.role_category, p.posting_type,
                     p.service_tenure_months, b.baseline_duty_hours,
                     b.baseline_sleep_hours, b.baseline_stress,
                     b.baseline_fatigue, b.baseline_mood
        """), {"personnel_id": PERSONNEL_ID}).mappings().first()
        if baseline is None:
            raise ValueError(f"{PERSONNEL_ID} was not found in PostgreSQL.")
        latest_week_start = baseline["latest_week_start"]
        if latest_week_start is None:
            raise ValueError(f"No existing duty history found for {PERSONNEL_ID}.")

    personnel_df = pd.DataFrame([{
        "personnel_id": baseline["personnel_id"],
        "role_category": baseline["role_category"],
        "posting_type": baseline["posting_type"],
        "service_tenure_months": int(baseline["service_tenure_months"]),
        "baseline_duty_hours": float(baseline["baseline_duty_hours"]),
        "baseline_sleep_hours": float(baseline["baseline_sleep_hours"]),
        "baseline_stress": float(baseline["baseline_stress"]),
        "baseline_fatigue": float(baseline["baseline_fatigue"]),
        "baseline_mood": float(baseline["baseline_mood"]) if baseline["baseline_mood"] is not None else 3.5,
    }])

    row = simulate_personnel_weeks(personnel_df, n_weeks=1).iloc[0]
    next_week_start = latest_week_start + timedelta(days=7)

    with engine.begin() as conn:
        conn.execute(text("""
            DELETE FROM wellness_checkins
            WHERE personnel_id = :personnel_id
              AND checkin_date = :week_start
              AND optional_note = 'Synthetic simulation week'
        """), {"personnel_id": PERSONNEL_ID, "week_start": next_week_start})
        conn.execute(text("""
            DELETE FROM duty_records
            WHERE personnel_id = :personnel_id
              AND week_start = :week_start
              AND source = :source
        """), {"personnel_id": PERSONNEL_ID, "week_start": next_week_start, "source": SOURCE})
        conn.execute(text("""
            INSERT INTO duty_records (
                personnel_id, week_start, duty_hours_week, overtime_hours,
                night_shifts, consecutive_duty_days, avg_rest_hours,
                training_hours, current_deployment_days,
                days_since_last_deployment, recent_deployment_count,
                leave_days_taken, days_since_last_leave, source
            ) VALUES (
                :personnel_id, :week_start, :duty_hours_week, :overtime_hours,
                :night_shifts, :consecutive_duty_days, :avg_rest_hours,
                :training_hours, :current_deployment_days,
                :days_since_last_deployment, :recent_deployment_count,
                :leave_days_taken, :days_since_last_leave, :source
            )
        """), {
            "personnel_id": PERSONNEL_ID, "week_start": next_week_start,
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
            "source": SOURCE,
        })
        conn.execute(text("""
            INSERT INTO wellness_checkins (
                personnel_id, checkin_date, avg_sleep_hours, sleep_quality,
                stress_level, fatigue_level, mood_score, recovery_feeling,
                optional_note, support_requested
            ) VALUES (
                :personnel_id, :checkin_date, :avg_sleep_hours, :sleep_quality,
                :stress_level, :fatigue_level, :mood_score, :recovery_feeling,
                'Synthetic simulation week', false
            )
        """), {
            "personnel_id": PERSONNEL_ID, "checkin_date": next_week_start,
            "avg_sleep_hours": float(row["avg_sleep_hours"]),
            "sleep_quality": float(row["sleep_quality"]),
            "stress_level": int(round(row["self_reported_stress"])),
            "fatigue_level": int(round(row["fatigue_level"])),
            "mood_score": float(row["mood_score"]),
            "recovery_feeling": float(row["recovery_feeling"]),
        })

    print("\nTRINETRA — Next Week Simulation")
    print("--------------------------------")
    print(f"Personnel:       {PERSONNEL_ID}")
    print(f"New week:        {next_week_start}")
    print(f"Week type:       {row['week_type']}")
    print(f"Duty hours:      {row['duty_hours_week']}")
    print(f"Overtime:        {row['overtime_hours']}")
    print(f"Night shifts:    {row['night_shifts']}")
    print(f"Rest hours:      {row['avg_rest_hours']}")
    print(f"Sleep hours:     {row['avg_sleep_hours']}")
    print(f"Stress:          {row['self_reported_stress']}")
    print(f"Fatigue:         {row['fatigue_level']}")
    print("\nInserted successfully into PostgreSQL.")

if __name__ == "__main__":
    main()
