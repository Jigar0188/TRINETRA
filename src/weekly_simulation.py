import numpy as np
import pandas as pd

from src.baseline import generate_personnel_baselines


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 123
rng = np.random.default_rng(RANDOM_SEED)

N_WEEKS = 26


# ============================================================
# HELPER
# ============================================================

def clipped(value, lower, upper):
    """Keep a value within a realistic range."""
    return float(np.clip(value, lower, upper))


# ============================================================
# WEEK TYPE SELECTION
# ============================================================

def choose_week_type(previous_type=None):

    choices = [
        "Normal",
        "Operational_Spike",
        "Deployment",
        "Recovery"
    ]

    if previous_type == "Operational_Spike":

        probabilities = [
            0.40,
            0.25,
            0.20,
            0.15
        ]

    elif previous_type == "Deployment":

        probabilities = [
            0.45,
            0.15,
            0.25,
            0.15
        ]

    elif previous_type == "Recovery":

        probabilities = [
            0.70,
            0.10,
            0.05,
            0.15
        ]

    else:

        probabilities = [
            0.65,
            0.15,
            0.12,
            0.08
        ]

    return rng.choice(
        choices,
        p=probabilities
    )


# ============================================================
# WEEKLY SIMULATION
# ============================================================

def simulate_personnel_weeks(
    personnel_df,
    n_weeks=N_WEEKS
):

    weekly_records = []

    for _, person in personnel_df.iterrows():

        previous_week_type = None

        # ----------------------------------------------------
        # PERSON-SPECIFIC HISTORY
        # ----------------------------------------------------

        days_since_last_leave = int(
            rng.integers(14, 45)
        )

        days_since_last_deployment = int(
            rng.integers(30, 180)
        )

        # Store deployment weeks so we can calculate
        # a rolling 12-week deployment count.
        deployment_history = []

        # ----------------------------------------------------
        # WEEK LOOP
        # ----------------------------------------------------

        for week in range(1, n_weeks + 1):

            # ------------------------------------------------
            # 1. SELECT WEEK TYPE
            # ------------------------------------------------

            week_type = choose_week_type(
                previous_week_type
            )

            # ------------------------------------------------
            # 2. PERSONAL BASELINE
            # ------------------------------------------------

            duty_hours = person[
                "baseline_duty_hours"
            ]

            sleep_hours = person[
                "baseline_sleep_hours"
            ]

            stress = person[
                "baseline_stress"
            ]

            fatigue = person[
                "baseline_fatigue"
            ]

            mood = person[
                "baseline_mood"
            ]

            # ------------------------------------------------
            # 3. DEFAULT WEEKLY CONDITIONS
            # ------------------------------------------------

            overtime_hours = clipped(
                rng.normal(2.0, 1.5),
                0,
                8
            )

            night_shifts = int(
                rng.integers(0, 2)
            )

            consecutive_duty_days = int(
                rng.integers(2, 6)
            )

            avg_rest_hours = clipped(
                rng.normal(11.0, 1.5),
                7.0,
                15.0
            )

            training_hours = clipped(
                rng.normal(3.0, 1.5),
                0,
                8
            )

            current_deployment_days = 0
            leave_days_taken = 0

            # ------------------------------------------------
            # 4. EVENT EFFECTS
            # ------------------------------------------------

            if week_type == "Normal":

                duty_hours += rng.normal(
                    0,
                    2.0
                )

                sleep_hours += rng.normal(
                    0,
                    0.20
                )

            elif week_type == "Operational_Spike":

                duty_hours += rng.normal(
                    8,
                    2.5
                )

                overtime_hours = clipped(
                    rng.normal(8, 2.5),
                    4,
                    14
                )

                night_shifts = int(
                    rng.integers(2, 5)
                )

                consecutive_duty_days = int(
                    rng.integers(5, 8)
                )

                avg_rest_hours -= rng.normal(
                    2.0,
                    0.7
                )

                sleep_hours -= rng.normal(
                    0.6,
                    0.2
                )

            elif week_type == "Deployment":

                current_deployment_days = int(
                    rng.integers(5, 8)
                )

                duty_hours += rng.normal(
                    7,
                    2.0
                )

                overtime_hours = clipped(
                    rng.normal(6, 2),
                    2,
                    12
                )

                night_shifts = int(
                    rng.integers(2, 5)
                )

                consecutive_duty_days = int(
                    rng.integers(5, 8)
                )

                avg_rest_hours -= rng.normal(
                    1.8,
                    0.6
                )

                sleep_hours -= rng.normal(
                    0.5,
                    0.2
                )

                deployment_history.append(
                    week
                )

                days_since_last_deployment = 0

            elif week_type == "Recovery":

                duty_hours -= rng.normal(
                    5,
                    1.5
                )

                overtime_hours = clipped(
                    rng.normal(0.5, 0.5),
                    0,
                    2
                )

                night_shifts = 0

                consecutive_duty_days = int(
                    rng.integers(1, 4)
                )

                avg_rest_hours += rng.normal(
                    2.0,
                    0.6
                )

                sleep_hours += rng.normal(
                    0.5,
                    0.2
                )

                # Probability of taking leave during recovery.
                leave_days_taken = int(
                    rng.choice(
                        [0, 1, 2, 3, 4, 5],
                        p=[
                            0.10,
                            0.10,
                            0.15,
                            0.20,
                            0.25,
                            0.20
                        ]
                    )
                )

                if leave_days_taken > 0:
                    days_since_last_leave = 0

            # ------------------------------------------------
            # 5. CLIP OPERATIONAL VALUES
            # ------------------------------------------------

            duty_hours = clipped(
                duty_hours,
                30,
                75
            )

            sleep_hours = clipped(
                sleep_hours,
                4.5,
                9.0
            )

            avg_rest_hours = clipped(
                avg_rest_hours,
                5,
                16
            )

            consecutive_duty_days = int(
                np.clip(
                    consecutive_duty_days,
                    1,
                    10
                )
            )

            # ------------------------------------------------
            # 6. WEEKLY WELLNESS RESPONSE
            # ------------------------------------------------

            workload_pressure = max(
                duty_hours - person[
                    "baseline_duty_hours"
                ],
                0
            ) / 15

            sleep_loss = max(
                person[
                    "baseline_sleep_hours"
                ] - sleep_hours,
                0
            )

            rest_loss = max(
                10 - avg_rest_hours,
                0
            ) / 5

            stress += (
                workload_pressure * 0.8
                + sleep_loss * 0.6
                + rest_loss * 0.4
                + night_shifts * 0.08
                + rng.normal(0, 0.25)
            )

            fatigue += (
                workload_pressure * 0.7
                + sleep_loss * 1.0
                + rest_loss * 0.5
                + consecutive_duty_days * 0.05
                + rng.normal(0, 0.25)
            )

            mood += (
                max(
                    stress - person[
                        "baseline_stress"
                    ],
                    0
                ) * 0.25
                + rng.normal(0, 0.20)
            )

            # Recovery improves wellness.
            if week_type == "Recovery":

                stress -= 0.30
                fatigue -= 0.40
                mood -= 0.20

            # ------------------------------------------------
            # 7. BOUND WELLNESS VARIABLES
            # ------------------------------------------------

            stress = clipped(
                stress,
                1,
                5
            )

            fatigue = clipped(
                fatigue,
                1,
                5
            )

            mood = clipped(
                mood,
                1,
                5
            )

            # ------------------------------------------------
            # 8. SLEEP QUALITY
            # ------------------------------------------------

            sleep_quality = (
                4.5
                - max(
                    7 - sleep_hours,
                    0
                ) * 0.8
                - max(
                    duty_hours - 50,
                    0
                ) * 0.03
                + rng.normal(0, 0.35)
            )

            sleep_quality = clipped(
                sleep_quality,
                1,
                5
            )

            # ------------------------------------------------
            # 9. RECOVERY FEELING
            # ------------------------------------------------

            recovery_feeling = (
                3.5
                + (avg_rest_hours - 10) * 0.15
                + (sleep_hours - 7) * 0.35
                - (fatigue - 2) * 0.20
                + rng.normal(0, 0.30)
            )

            recovery_feeling = clipped(
                recovery_feeling,
                1,
                5
            )

            # ------------------------------------------------
            # 10. HISTORY / ROLLING VARIABLES
            # ------------------------------------------------

            if leave_days_taken > 0:
                days_since_last_leave = 0
            else:
                days_since_last_leave += 7
            if week_type != "Deployment":
                days_since_last_deployment += 7

            # Only deployments in the previous 12 weeks.
            recent_deployment_count = sum(
                1
                for deployment_week
                in deployment_history
                if week - deployment_week <= 12
            )

            # ------------------------------------------------
            # 11. SAVE RECORD
            # ------------------------------------------------

            weekly_records.append({

                "personnel_id":
                    person["personnel_id"],

                "week_index":
                    week,

                "role_category":
                    person["role_category"],

                "posting_type":
                    person["posting_type"],

                "service_tenure_months":
                    person["service_tenure_months"],

                # Generator-only variable.
                "week_type":
                    week_type,

                "duty_hours_week":
                    round(duty_hours, 1),

                "overtime_hours":
                    round(overtime_hours, 1),

                "night_shifts":
                    night_shifts,

                "consecutive_duty_days":
                    consecutive_duty_days,

                "avg_rest_hours":
                    round(avg_rest_hours, 1),

                "training_hours":
                    round(training_hours, 1),

                "current_deployment_days":
                    current_deployment_days,

                "days_since_last_deployment":
                    days_since_last_deployment,

                "recent_deployment_count":
                    recent_deployment_count,

                "leave_days_taken":
                    leave_days_taken,

                "days_since_last_leave":
                    days_since_last_leave,

                "avg_sleep_hours":
                    round(sleep_hours, 1),

                "sleep_quality":
                    round(sleep_quality, 1),

                "self_reported_stress":
                    round(stress, 1),

                "fatigue_level":
                    round(fatigue, 1),

                "mood_score":
                    round(mood, 1),

                "recovery_feeling":
                    round(recovery_feeling, 1)
            })

            previous_week_type = week_type

    return pd.DataFrame(weekly_records)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    personnel = generate_personnel_baselines(10)

    weekly_df = simulate_personnel_weeks(
        personnel,
        n_weeks=26
    )

    print("\nTRINETRA — Weekly Synthetic Data\n")

    print(
        weekly_df.head(20).to_string(index=False)
    )

    print("\nShape:")
    print(weekly_df.shape)

    print("\nWeek Type Distribution:")
    print(
        weekly_df["week_type"]
        .value_counts()
    )