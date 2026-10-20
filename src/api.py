from fastapi import FastAPI,Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import pandas as pd

from src.inference import run_inference
from src.db_ml_bridge import run_bulk_inference
from src.db_ml_bridge import build_latest_ml_features
from src.persistence import is_persistent_high
from src.trajectory import determine_severity_trajectory
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import get_db
from src.db_ml_bridge import build_latest_ml_features


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

@app.get("/db/personnel")
def get_db_personnel(db: Session = Depends(get_db)):
    result = db.execute(
        text("""
            SELECT
                personnel_id,
                role_category,
                posting_type,
                service_tenure_months
            FROM personnel
            ORDER BY personnel_id
        """)
    )

    return [dict(row._mapping) for row in result]

@app.get("/db/personnel/{personnel_id}/history")
def get_personnel_history(
    personnel_id: str,
    db: Session = Depends(get_db)
):
    personnel = db.execute(
        text("""
            SELECT
                personnel_id,
                full_name,
                role_category,
                posting_type,
                service_tenure_months
            FROM personnel
            WHERE personnel_id = :personnel_id
        """),
        {"personnel_id": personnel_id}
    ).mappings().first()

    if personnel is None:
        return {"error": "Personnel not found"}

    duty = db.execute(
        text("""
            SELECT
                week_start,
                duty_hours_week,
                overtime_hours,
                night_shifts,
                consecutive_duty_days,
                avg_rest_hours,
                training_hours
            FROM duty_records
            WHERE personnel_id = :personnel_id
            ORDER BY week_start
        """),
        {"personnel_id": personnel_id}
    ).mappings().all()

    wellness = db.execute(
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

    return {
        "personnel": dict(personnel),
        "duty_history": [dict(row) for row in duty],
        "wellness_history": [dict(row) for row in wellness]
    }

@app.post("/predict")
def predict(request: PredictionRequest):

    input_df = pd.DataFrame(
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


@app.get("/predict/{personnel_id}")
def predict_from_database(
    personnel_id: str,
    db: Session = Depends(get_db)
):
    """Build the latest ML features directly from PostgreSQL and run inference."""

    try:
        input_df = build_latest_ml_features(db, personnel_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    row = input_df.iloc[0]

    workload_trend = float(row["workload_trend"])
    stress_trend = float(row["stress_trend"])
    fatigue_trend = float(row["fatigue_trend"])
    sleep_trend = float(row["sleep_trend"])

    severity_trajectory = determine_severity_trajectory(
        workload_trend=workload_trend,
        stress_trend=stress_trend,
        fatigue_trend=fatigue_trend,
        sleep_trend=sleep_trend
    )

    persistent_high = is_persistent_high(
        db=db,
        personnel_id=personnel_id,
        consecutive_weeks=2
    )

    result = run_inference(
        input_df=input_df,
        workload_trend=workload_trend,
        stress_trend=stress_trend,
        fatigue_trend=fatigue_trend,
        sleep_trend=sleep_trend,
        persistent_high=persistent_high,
        severity_trajectory=severity_trajectory
    )

    return {
        "personnel_id": personnel_id,
        **result
    }

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

# def get_live_prediction(db: Session, personnel_id: str):
#     df = build_latest_ml_features(db, personnel_id)

#     if df.empty:
#         return None

#     latest = df.iloc[0]

#     result = run_inference(
#         input_df=df,
#         workload_trend=float(latest["workload_trend"]),
#         stress_trend=float(latest["stress_trend"]),
#         fatigue_trend=float(latest["fatigue_trend"]),
#         sleep_trend=float(latest["sleep_trend"]),
#     )

#     return result
@app.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):

    # Live DB → Feature Engineering → ML → Policy Engine
    df = run_bulk_inference(db)

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

            "No_History": 0
        }
    }

@app.get("/dashboard/cases")
def dashboard_cases(
    priority: str | None = None,
    risk: str | None = None,
    db: Session = Depends(get_db)
):
    df = run_bulk_inference(db)

    # Only actionable welfare cases
    df = df[
        df["welfare_priority"].isin(["Priority", "Review"])
    ].copy()

    # Optional filters
    if priority:
        df = df[df["welfare_priority"] == priority]

    if risk:
        df = df[df["overall_risk"] == risk]

    # Priority first, then High risk
    priority_order = {
        "Priority": 0,
        "Review": 1,
        "Routine_Monitoring": 2
    }

    risk_order = {
        "High": 0,
        "Monitor": 1,
        "Low": 2
    }

    df["_priority_order"] = (
        df["welfare_priority"]
        .map(priority_order)
        .fillna(99)
    )

    df["_risk_order"] = (
        df["overall_risk"]
        .map(risk_order)
        .fillna(99)
    )

    df = df.sort_values(
        ["_priority_order", "_risk_order"],
        ascending=[True, True]
    )

    cases = []

    for _, row in df.iterrows():

        cases.append({
            "personnel_id": row["personnel_id"],
            "stress_risk": row["stress_risk"],
            "fatigue_risk": row["fatigue_risk"],
            "burnout_risk": row["burnout_risk"],
            "overall_risk": row["overall_risk"],
            "severity_trajectory": row["severity_trajectory"],
            "persistent_high": bool(row["persistent_high"]),
            "welfare_priority": row["welfare_priority"]
        })

    return {
        "count": len(cases),
        "cases": cases
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
def dashboard_case_detail(
    personnel_id: str,
    db: Session = Depends(get_db)
):
    # Run live inference for all personnel
    df = run_bulk_inference(db)

    person = df[
        df["personnel_id"] == personnel_id
    ]

    if person.empty:
        return {
            "error": "Personnel record not found"
        }

    row = person.iloc[0]

    # Fetch basic personnel information
    personnel = db.execute(
        text("""
            SELECT
                personnel_id,
                full_name,
                role_category,
                posting_type,
                service_tenure_months
            FROM personnel
            WHERE personnel_id = :personnel_id
        """),
        {"personnel_id": personnel_id}
    ).mappings().first()

    if personnel is None:
        return {
            "error": "Personnel record not found"
        }

    return {
        "personnel_id": personnel_id,

        "personnel": dict(personnel),

        "risk": {
            "stress": row["stress_risk"],
            "fatigue": row["fatigue_risk"],
            "burnout": row["burnout_risk"],
            "overall": row["overall_risk"]
        },

        "trajectory": row["severity_trajectory"],

        "persistent_high": bool(
            row["persistent_high"]
        ),

        "welfare_priority": row["welfare_priority"],

        "signals": {
            "workload_trend": float(row["workload_trend"]),
            "stress_trend": float(row["stress_trend"]),
            "fatigue_trend": float(row["fatigue_trend"]),
            "sleep_trend": float(row["sleep_trend"])
        }
    }


@app.get("/dashboard/commander-summary")
def commander_summary(db: Session = Depends(get_db)):

    df = run_bulk_inference(db)

    total = len(df)

    if total == 0:
        return {
            "scope": "unit_level_aggregate",
            "total_personnel": 0,
            "risk_load": {
                "Low": 0,
                "Monitor": 0,
                "High": 0
            },
            "trajectory": {
                "Improving": 0,
                "Stable": 0,
                "Worsening": 0
            },
            "unit_situation": {
                "status": "No Data",
                "worsening_percentage": 0,
                "high_risk_percentage": 0
            },
            "key_signals": {},
            "command_considerations": [],
            "privacy": {
                "individual_identity_visible": False,
                "individual_risk_records_visible": False
            }
        }

    risk_counts = df["overall_risk"].value_counts()
    trajectory_counts = df["severity_trajectory"].value_counts()

    def percentage(value):
        return round((value / total) * 100, 1)

    # ==========================================
    # AGGREGATE WELFARE SIGNALS
    # ==========================================

    avg_workload = float(df["workload_trend"].mean())

    workload_trend = float(
        df["workload_trend"].mean()
    )

    stress_trend = float(
        df["stress_trend"].mean()
    )

    fatigue_trend = float(
        df["fatigue_trend"].mean()
    )

    sleep_trend = float(
        df["sleep_trend"].mean()
    )

    # ==========================================
    # INTERPRET SIGNALS
    # ==========================================

    if workload_trend >= 0.50:
        workload_status = "Elevated"
    elif workload_trend >= 0.35:
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

    # ==========================================
    # UNIT SITUATION
    # ==========================================

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

    # ==========================================
    # COMMAND CONSIDERATIONS
    # ==========================================

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

    # ==========================================
    # AGGREGATE RESPONSE ONLY
    # ==========================================

    return {
        "scope": "unit_level_aggregate",

        "total_personnel": total,

        "risk_load": {
            "Low": percentage(
                risk_counts.get("Low", 0)
            ),
            "Monitor": percentage(
                risk_counts.get("Monitor", 0)
            ),
            "High": percentage(
                risk_counts.get("High", 0)
            )
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