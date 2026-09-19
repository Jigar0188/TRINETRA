import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clipped_normal(mean, std, lower, upper):
    """
    Generate a normally distributed value but keep it
    within realistic bounds.
    """
    value = rng.normal(mean, std)
    return float(np.clip(value, lower, upper))


def bounded_scale(value, lower, upper):
    """
    Convert a value to approximately 0-1 scale.
    """
    return np.clip(
        (value - lower) / (upper - lower),
        0.0,
        1.0
    )


# ============================================================
# PERSONNEL BASELINE GENERATOR
# ============================================================

def generate_personnel_baselines(n_personnel=10):

    personnel = []

    for i in range(1, n_personnel + 1):

        # ----------------------------------------------------
        # 1. PERSONAL CHARACTERISTICS
        # ----------------------------------------------------

        role = rng.choice(
            ["Field", "Administrative", "Technical", "Support"],
            p=[0.40, 0.20, 0.20, 0.20]
        )

        posting = rng.choice(
            ["Routine", "High_Operational", "Remote"],
            p=[0.50, 0.30, 0.20]
        )

        service_tenure = int(
            rng.integers(12, 241)
        )

        # ----------------------------------------------------
        # 2. INDIVIDUAL DIFFERENCES
        # ----------------------------------------------------
        # These are hidden synthetic traits used only to make
        # different people naturally behave differently.
        #
        # They are NOT ML features.

        workload_tolerance = clipped_normal(
            mean=0.50,
            std=0.15,
            lower=0.15,
            upper=0.85
        )

        sleep_propensity = clipped_normal(
            mean=0.50,
            std=0.15,
            lower=0.15,
            upper=0.85
        )

        wellness_sensitivity = clipped_normal(
            mean=0.50,
            std=0.15,
            lower=0.15,
            upper=0.85
        )

        # ----------------------------------------------------
        # 3. BASELINE DUTY HOURS
        # ----------------------------------------------------

        role_effect = {
            "Field": 3.0,
            "Administrative": -2.0,
            "Technical": 0.5,
            "Support": -1.0
        }

        posting_effect = {
            "Routine": 0.0,
            "High_Operational": 5.0,
            "Remote": 2.5
        }

        duty_mean = (
            45
            + role_effect[role]
            + posting_effect[posting]
        )

        # Individual workload tolerance introduces variation.
        duty_mean += (0.50 - workload_tolerance) * 6

        baseline_duty_hours = clipped_normal(
            mean=duty_mean,
            std=3.5,
            lower=35,
            upper=60
        )

        # ----------------------------------------------------
        # 4. BASELINE SLEEP
        # ----------------------------------------------------

        sleep_mean = (
            7.0
            + (sleep_propensity - 0.50) * 1.0
        )

        # Higher normal workload slightly reduces normal sleep.
        sleep_mean -= max(
            baseline_duty_hours - 45,
            0
        ) * 0.025

        # Remote/high-operational context may affect recovery,
        # but only modestly in the synthetic population.
        if posting == "High_Operational":
            sleep_mean -= 0.15
        elif posting == "Remote":
            sleep_mean -= 0.05

        baseline_sleep_hours = clipped_normal(
            mean=sleep_mean,
            std=0.30,
            lower=5.5,
            upper=8.5
        )

        # ----------------------------------------------------
        # 5. BASELINE STRESS
        # ----------------------------------------------------

        stress_mean = 2.2

        # Workload above typical reference level.
        stress_mean += max(
            baseline_duty_hours - 45,
            0
        ) * 0.025

        # Lower sleep contributes modestly.
        stress_mean += max(
            7.0 - baseline_sleep_hours,
            0
        ) * 0.30

        # Individual wellness sensitivity.
        stress_mean += (
            wellness_sensitivity - 0.50
        ) * 0.8

        baseline_stress = clipped_normal(
            mean=stress_mean,
            std=0.30,
            lower=1.0,
            upper=5.0
        )

        # ----------------------------------------------------
        # 6. BASELINE FATIGUE
        # ----------------------------------------------------

        fatigue_mean = 2.1

        fatigue_mean += max(
            baseline_duty_hours - 45,
            0
        ) * 0.025

        fatigue_mean += max(
            7.0 - baseline_sleep_hours,
            0
        ) * 0.45

        fatigue_mean += (
            wellness_sensitivity - 0.50
        ) * 0.7

        baseline_fatigue = clipped_normal(
            mean=fatigue_mean,
            std=0.30,
            lower=1.0,
            upper=5.0
        )

        # ----------------------------------------------------
        # 7. BASELINE MOOD
        # ----------------------------------------------------
        # Higher score = worse mood.
        # Therefore workload/stress/sleep have a small
        # positive effect on this score.

        mood_mean = 2.0

        mood_mean += (
            baseline_stress - 2.0
        ) * 0.25

        mood_mean += max(
            7.0 - baseline_sleep_hours,
            0
        ) * 0.25

        baseline_mood = clipped_normal(
            mean=mood_mean,
            std=0.30,
            lower=1.0,
            upper=5.0
        )

        # ----------------------------------------------------
        # 8. STORE PERSON
        # ----------------------------------------------------

        person = {
            "personnel_id": f"P{i:03d}",
            "role_category": role,
            "service_tenure_months": service_tenure,
            "posting_type": posting,

            "baseline_duty_hours": round(
                baseline_duty_hours, 1
            ),

            "baseline_sleep_hours": round(
                baseline_sleep_hours, 1
            ),

            "baseline_stress": round(
                baseline_stress, 1
            ),

            "baseline_fatigue": round(
                baseline_fatigue, 1
            ),

            "baseline_mood": round(
                baseline_mood, 1
            )
        }

        personnel.append(person)

    return pd.DataFrame(personnel)


# ============================================================
# TEST RUN
# ============================================================

if __name__ == "__main__":

    df = generate_personnel_baselines(10)

    print("\nTRINETRA — Personnel Baselines\n")

    print(
        df.to_string(index=False)
    )