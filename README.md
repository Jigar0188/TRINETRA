# TRINETRA — AI-Based Personnel Stress & Welfare Monitoring System

TRINETRA is an AI/ML-driven welfare monitoring project designed to identify potential stress, fatigue, and burnout risks among personnel using duty patterns, wellness indicators, personal baselines, and historical trends.

The system combines machine learning predictions with a policy-based risk classification and welfare prioritization engine to support individual case review and privacy-conscious unit-level insights.

> **Project status:** Academic / SIH 2026 prototype. The project currently uses synthetic data for development and demonstration. Predictions are intended to support welfare review, not to provide medical diagnoses or replace professional judgment.

## Key Features

- **Multi-model risk prediction:** Separate machine learning models assess stress, fatigue, and burnout risk.
- **Feature engineering:** Transforms duty, workload, sleep, wellness, baseline deviation, and temporal trend data into model-ready features.
- **Database-to-ML pipeline:** Retrieves personnel records from PostgreSQL and prepares features for inference.
- **Policy-based prioritization:** Combines model outputs and deterioration indicators to classify cases into Low, Monitor, and High risk tiers.
- **Trajectory analysis:** Evaluates changes in workload, stress, fatigue, and sleep trends.
- **Weekly simulation:** Supports development and demonstration of changing personnel records over time.
- **Dashboard integration:** Connects the backend inference workflow to a web dashboard for case review and aggregate analytics.
- **Privacy-conscious command insights:** Supports unit-level aggregate reporting without exposing individual risk records in the commander-facing view.

## System Architecture

```text
Synthetic / Personnel Data
           |
           v
      PostgreSQL
           |
           v
   Feature Engineering
           |
           v
  ML Feature DataFrame
           |
           v
  +--------+--------+
  |        |        |
Stress   Fatigue  Burnout
 Model    Model     Model
  |        |        |
  +--------+--------+
           |
           v
    Policy Engine
           |
           v
 Risk Tier & Welfare Priority
           |
           v
       FastAPI
           |
           v
    React Dashboard
```

## Technology Stack

| Component | Technologies |
|---|---|
| Programming language | Python, JavaScript |
| Machine learning | Scikit-learn, Pandas, NumPy |
| Backend API | FastAPI |
| Database | PostgreSQL |
| Frontend | React |
| Development | Jupyter Notebook, Git, GitHub |

## Machine Learning Workflow

1. **Data preparation:** Organize personnel attributes, baseline measurements, weekly duty records, and wellness check-ins.
2. **Feature engineering:** Calculate workload indicators, deviations from personal baselines, temporal trends, and pressure-related features.
3. **Inference:** Generate separate stress, fatigue, and burnout predictions using the trained models.
4. **Risk classification:** Apply policy rules to combine predicted risks and deterioration signals into an overall risk tier.
5. **Welfare prioritization:** Produce a priority category to support review and follow-up.
6. **Dashboard delivery:** Expose relevant prediction results and aggregate insights through the backend API.

## Risk Classification

The policy engine classifies cases into three tiers:

- **Low:** No significant combination of risk indicators under the configured policy.
- **Monitor:** Moderate risk indicators or emerging deterioration signals require monitoring.
- **High:** A stronger combination of predicted risks and, where applicable, deterioration signals warrants priority review.

The final tier is determined by the configured policy rules, not simply by averaging the three model outputs.

## Repository Structure

```text
TRINETRA_ML/
├── frontend/
│   └── src/
├── notebooks/
│   └── 02_feature_engineering.ipynb
├── src/
│   ├── api.py
│   ├── database.py
│   ├── db_ml_bridge.py
│   ├── import_demo_data.py
│   ├── import_full_synthetic.py
│   ├── persistence.py
│   ├── simulate_next_week.py
│   ├── trajectory.py
│   └── weekly_simulation.py
├── data/
│   └── processed/
├── .gitignore
└── README.md
```

*The repository may contain additional model, configuration, and frontend files.*

## Getting Started

### Prerequisites

- Python installed
- PostgreSQL installed and configured
- Node.js and npm installed
- Git installed

### 1. Clone the repository

```bash
git clone https://github.com/Jigar0188/TRINETRA.git
cd TRINETRA
```

### 2. Set up the Python environment

```bash
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not present in the repository, create it from the project's verified dependencies before following this step.

### 3. Configure PostgreSQL

- Create or select the PostgreSQL database used by the project.
- Configure the database connection according to the settings expected by `src/database.py`.
- Ensure the required tables and schema are available before importing data or running database-backed inference.

Do not commit database passwords, API keys, or other secrets to GitHub.

### 4. Prepare the data

The repository includes scripts for importing synthetic demonstration data. Review the relevant import script and its expected input files before running it.

For example:

```bash
python -m src.import_demo_data
```

Use the full synthetic-data importer only after confirming its input path, database requirements, and intended data scope. Avoid running multiple import scripts against the same database without checking whether they replace or append records.

### 5. Start the backend

From the repository root, if the FastAPI application is defined as `app` in `src/api.py`:

```bash
python -m uvicorn src.api:app --reload
```

Open the interactive API documentation at:

`http://127.0.0.1:8000/docs`

### 6. Start the frontend

Open a second terminal and navigate to the frontend directory:

```bash
cd frontend
npm install
npm run dev
```

Use the local URL printed by the frontend development server. Confirm that the frontend API base URL matches the backend address and that CORS is configured for the frontend origin.

## Data and Privacy

- Demonstration workflows use synthetic personnel data.
- Synthetic results should not be interpreted as evidence of real-world predictive accuracy.
- Personnel welfare information should be handled with appropriate access controls and data minimization.
- Individual risk predictions should support human review rather than automatically determine personnel decisions.

## Limitations

- Model outputs depend on the quality and representativeness of the available data.
- Synthetic-data performance does not establish effectiveness on real personnel populations.
- Risk tiers and welfare priorities depend on configured model and policy rules.
- The system is a prototype and requires appropriate validation, privacy safeguards, and operational review before any real-world deployment.

## Future Improvements

- Validate models on appropriately governed, representative datasets.
- Add model evaluation and monitoring reports.
- Improve automated testing and inference reliability.
- Strengthen access control, audit logging, and consent workflows.
- Evaluate the effectiveness of welfare recommendations with qualified stakeholders.

## Disclaimer

TRINETRA is an academic and hackathon prototype intended to explore predictive welfare monitoring. It is not a medical diagnostic system and must not be used as the sole basis for disciplinary, employment, deployment, or other high-impact decisions.
