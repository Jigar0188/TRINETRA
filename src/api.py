from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import pandas as pd

from src.inference import run_inference


app = FastAPI(
    title="TRINETRA ML API",
    description="AI-based personnel stress and welfare risk prediction",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    role_category: str
    posting_type: str

    service_tenure_months: float
    duty_hours_week: float
    overtime_hours: float
    night_shifts: float
    consecutive_duty_days: float
    avg_rest_hours: float
    training_hours: float
    current_deployment_days: float
    days_since_last_deployment: float
    recent_deployment_count: float
    leave_days_taken: float
    days_since_last_leave: float

    avg_sleep_hours: float
    sleep_quality: float
    self_reported_stress: float
    fatigue_level: float
    mood_score: float
    recovery_feeling: float

    duty_deviation: float
    sleep_deviation: float
    stress_deviation: float
    fatigue_deviation: float

    workload_index: float
    workload_trend: float
    stress_trend: float
    fatigue_trend: float
    sleep_trend: float
    signal_agreement: float

    stress_pressure: float
    fatigue_pressure: float
    stress_trend_pressure: float


@app.get("/")
def root():
    return {
        "system": "TRINETRA",
        "status": "online"
    }


@app.post("/predict")
def predict(request: PredictionRequest):

    input_df = __import__("pandas").DataFrame(
        [request.model_dump()]
    )

    result = run_inference(
        input_df=input_df,
        workload_trend=request.workload_trend,
        stress_trend=request.stress_trend,
        fatigue_trend=request.fatigue_trend,
        sleep_trend=request.sleep_trend
    )

    return result

# ============================================
# DASHBOARD DATA
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"

DASHBOARD_LATEST = DATA_DIR / "dashboard_latest.csv"
DASHBOARD_HISTORY = DATA_DIR / "dashboard_history.csv"


def load_dashboard_data():
    if not DASHBOARD_LATEST.exists():
        raise FileNotFoundError(
            "dashboard_latest.csv not found. "
            "Run the dashboard export cell in the notebook first."
        )

    return pd.read_csv(DASHBOARD_LATEST)


def clean_records(df):
    """
    Convert pandas/numpy values into JSON-safe Python values.
    """
    df = df.copy()
    df = df.replace({float("nan"): None})

    return df.to_dict(orient="records")


@app.get("/dashboard/summary")
def dashboard_summary():

    df = load_dashboard_data()

    total_personnel = len(df)

    risk_counts = (
        df["overall_risk"]
        .value_counts()
        .to_dict()
    )

    priority_counts = (
        df["welfare_priority"]
        .value_counts()
        .to_dict()
    )

    trajectory_counts = (
        df["severity_trajectory"]
        .value_counts()
        .to_dict()
    )

    return {
        "total_personnel": total_personnel,

        "risk_distribution": {
            "Low": risk_counts.get("Low", 0),
            "Monitor": risk_counts.get("Monitor", 0),
            "High": risk_counts.get("High", 0)
        },

        "welfare_priority": {
            "Routine_Monitoring":
                priority_counts.get("Routine_Monitoring", 0),

            "Review":
                priority_counts.get("Review", 0),

            "Priority":
                priority_counts.get("Priority", 0)
        },

        "severity_trajectory": {
            "Improving":
                trajectory_counts.get("Improving", 0),

            "Stable":
                trajectory_counts.get("Stable", 0),

            "Worsening":
                trajectory_counts.get("Worsening", 0),

            "No_History":
                trajectory_counts.get("No_History", 0)
        }
    }


@app.get("/dashboard/cases")
def dashboard_cases(
    priority: str | None = None,
    risk: str | None = None
):

    df = load_dashboard_data()
    df = df[
    df["welfare_priority"].isin(["Priority", "Review"])
].copy()

    if priority:
        df = df[df["welfare_priority"] == priority]

    if risk:
        df = df[df["overall_risk"] == risk]

    # Highest priority first
    priority_order = {
        "Priority": 0,
        "Review": 1,
        "Routine_Monitoring": 2
    }

    df["_priority_order"] = (
        df["welfare_priority"]
        .map(priority_order)
        .fillna(99)
    )

    df = (
        df
        .sort_values(
            ["_priority_order", "risk_severity_score"],
            ascending=[True, False]
        )
        .drop(columns=["_priority_order"])
    )

    display_columns = [
        "personnel_id",
        "week_index",
        "stress_risk",
        "fatigue_risk",
        "burnout_risk",
        "overall_risk",
        "risk_severity_score",
        "severity_trajectory",
        "persistent_high",
        "welfare_priority",
        "explanation_signals"
    ]

    existing_columns = [
        col for col in display_columns
        if col in df.columns
    ]

    return {
        "count": len(df),
        "cases": clean_records(
            df[existing_columns]
        )
    }

@app.get("/dashboard/personnel")
def dashboard_personnel():
    df = load_dashboard_data()

    df = df.sort_values(
        ["personnel_id", "week_index"]
    ).groupby(
        "personnel_id",
        as_index=False
    ).tail(1).copy()

    personnel_columns = [
        "personnel_id",
        "role_category",
        "posting_type",
        "service_tenure_months",
        "stress_risk",
        "fatigue_risk",
        "burnout_risk",
        "overall_risk",
        "risk_severity_score",
        "severity_trajectory",
        "welfare_priority",
        "persistent_high",
    ]

    df = df[personnel_columns]

    return {
        "total_personnel": len(df),
        "personnel": clean_records(df)
    }

@app.get("/dashboard/cases/{personnel_id}")
def dashboard_case_detail(personnel_id: str):

    df = load_dashboard_data()

    person = df[
        df["personnel_id"] == personnel_id
    ]

    if person.empty:
        return {
            "error": "Personnel record not found"
        }

    # Latest available record
    person = (
        person
        .sort_values("week_index")
        .iloc[-1]
    )

    return {
        "personnel_id": person["personnel_id"],
        "week_index": int(person["week_index"]),

        "risk": {
            "stress": person["stress_risk"],
            "fatigue": person["fatigue_risk"],
            "burnout": person["burnout_risk"],
            "overall": person["overall_risk"]
        },

        "severity": float(
            person["risk_severity_score"]
        ),

        "trajectory": person["severity_trajectory"],

        "persistent_high": bool(
            person["persistent_high"]
        ),

        "welfare_priority": person["welfare_priority"],

        "explanation_signals":
            person["explanation_signals"]
    }


@app.get("/dashboard/commander-summary")
def commander_summary():
    df = load_dashboard_data()

    total = len(df)

    risk_counts = df["overall_risk"].value_counts()
    trajectory_counts = df["severity_trajectory"].value_counts()

    def percentage(value):
        if total == 0:
            return 0

        return round((value / total) * 100, 1)

    # -----------------------------------------
    # Aggregate welfare signals
    # -----------------------------------------

    avg_workload = float(df["workload_index"].mean())
    avg_sleep_deviation = float(df["sleep_deviation"].mean())
    avg_stress_deviation = float(df["stress_deviation"].mean())
    avg_fatigue_deviation = float(df["fatigue_deviation"].mean())

    workload_trend = float(df["workload_trend"].mean())
    stress_trend = float(df["stress_trend"].mean())
    fatigue_trend = float(df["fatigue_trend"].mean())
    sleep_trend = float(df["sleep_trend"].mean())

    # -----------------------------------------
    # Interpret aggregate signals
    # -----------------------------------------

    if avg_workload >= 0.50:
        workload_status = "Elevated"
    elif avg_workload >= 0.35:
        workload_status = "Moderate"
    else:
        workload_status = "Within range"

    if sleep_trend < -0.05:
        recovery_status = "Declining"
    elif sleep_trend > 0.05:
        recovery_status = "Improving"
    else:
        recovery_status = "Stable"

    if stress_trend > 0.05:
        stress_status = "Increasing"
    elif stress_trend < -0.05:
        stress_status = "Improving"
    else:
        stress_status = "Stable"

    if fatigue_trend > 0.05:
        fatigue_status = "Increasing"
    elif fatigue_trend < -0.05:
        fatigue_status = "Improving"
    else:
        fatigue_status = "Stable"

    # -----------------------------------------
    # Overall unit situation
    # -----------------------------------------

    worsening_percentage = percentage(
        trajectory_counts.get("Worsening", 0)
    )

    high_percentage = percentage(
        risk_counts.get("High", 0)
    )

    if worsening_percentage >= 40 or high_percentage >= 15:
        situation = "Elevated & Worsening"
    elif worsening_percentage >= 25 or high_percentage >= 10:
        situation = "Elevated"
    else:
        situation = "Within Routine Range"

    # -----------------------------------------
    # Command considerations
    # -----------------------------------------

    considerations = []

    if worsening_percentage >= 40:
        considerations.append(
        "Review recent unit-level welfare trajectory and accumulated changes"
    )
    elif worsening_percentage >= 25:
        considerations.append(
        "Monitor unit-level welfare trajectory for continued deterioration"
    )

    if workload_status == "Elevated":
        considerations.append(
        "Review unit-level workload distribution"
    )

    if recovery_status == "Declining":
        considerations.append(
        "Review recovery and leave patterns"
    )

    if stress_status == "Increasing":
        considerations.append(
        "Monitor operational tempo and emerging stress signals"
    )

    if fatigue_status == "Increasing":
        considerations.append(
        "Review sustained duty and fatigue pressure"
    )

    if not considerations:
        considerations.append(
        "Continue routine welfare monitoring"
    )
    return {
        "scope": "unit_level_aggregate",
        "total_personnel": total,

        "risk_load": {
            "Low": percentage(risk_counts.get("Low", 0)),
            "Monitor": percentage(risk_counts.get("Monitor", 0)),
            "High": percentage(risk_counts.get("High", 0))
        },

        "trajectory": {
            "Improving": percentage(
                trajectory_counts.get("Improving", 0)
            ),
            "Stable": percentage(
                trajectory_counts.get("Stable", 0)
            ),
            "Worsening": percentage(
                trajectory_counts.get("Worsening", 0)
            )
        },

        "unit_situation": {
            "status": situation,
            "worsening_percentage": worsening_percentage,
            "high_risk_percentage": high_percentage
        },

        "key_signals": {
            "workload": {
                "status": workload_status,
                "value": round(avg_workload, 2)
            },
            "recovery": {
                "status": recovery_status,
                "value": round(sleep_trend, 3)
            },
            "stress": {
                "status": stress_status,
                "value": round(stress_trend, 3)
            },
            "fatigue": {
                "status": fatigue_status,
                "value": round(fatigue_trend, 3)
            }
        },

        "command_considerations": considerations,

        "privacy": {
            "individual_identity_visible": False,
            "individual_risk_records_visible": False
        }
    }
    
@app.get("/dashboard/analytics")
def dashboard_analytics():
    df = pd.read_csv(DASHBOARD_HISTORY)

    weekly = (
        df.groupby("week_index")
        .agg(
            high_risk=("overall_risk", lambda x: (x == "High").sum()),
            monitor=("overall_risk", lambda x: (x == "Monitor").sum()),
            low_risk=("overall_risk", lambda x: (x == "Low").sum()),
            avg_severity=("risk_severity_score", "mean"),
            worsening=("severity_trajectory", lambda x: (x == "Worsening").sum()),
            improving=("severity_trajectory", lambda x: (x == "Improving").sum()),
        )
        .reset_index()
    )

    total_per_week = (
        df.groupby("week_index")["personnel_id"]
        .nunique()
        .reset_index(name="total")
    )

    weekly = weekly.merge(total_per_week, on="week_index")

    weekly["high_percentage"] = (
        weekly["high_risk"] / weekly["total"] * 100
    ).round(1)

    weekly["monitor_percentage"] = (
        weekly["monitor"] / weekly["total"] * 100
    ).round(1)

    weekly["low_percentage"] = (
        weekly["low_risk"] / weekly["total"] * 100
    ).round(1)

    weekly["avg_severity"] = weekly["avg_severity"].round(3)

    return {
        "weeks": weekly.to_dict(orient="records")
    }