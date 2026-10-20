import { useEffect, useState } from "react";
import { getPersonnelPrediction } from "./api";

function CaseDetail({ personnelId, onBack }) {
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!personnelId) return;

    setPrediction(null);
    setError(null);

    getPersonnelPrediction(personnelId)
      .then((data) => {
        setPrediction(data);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load live personnel prediction");
      });
  }, [personnelId]);

  if (error) {
    return (
      <div className="case-detail-page">
        <button className="back-button" onClick={onBack}>
          ← Welfare Cases
        </button>
        <div className="api-error">{error}</div>
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="case-detail-page">
        <button className="back-button" onClick={onBack}>
          ← Welfare Cases
        </button>
        <div className="loading-state">Loading live prediction...</div>
      </div>
    );
  }

  const riskClass = (value) => {
    if (!value) return "";
    return String(value).toLowerCase();
  };

  return (
    <div className="case-detail-page">
      <div className="case-detail-header">
        <div>
          <p className="eyebrow">WELFARE CASE</p>
          <h1>{prediction.personnel_id}</h1>
          <p>Live DB-backed AI welfare assessment</p>
        </div>

        <button className="back-button" onClick={onBack}>
          ← Welfare Cases
        </button>
      </div>

      <section className="detail-grid">
        <div className="detail-card overall-card">
          <p className="eyebrow">OVERALL RISK</p>

          <div className="overall-risk-row">
            <span
              className={`risk-badge ${riskClass(prediction.overall_risk)}`}
            >
              {prediction.overall_risk}
            </span>

            <span className="severity-value">
              Welfare Priority: {prediction.welfare_priority}
            </span>
          </div>

          <div className="case-meta">
            <div>
              <span>Trajectory</span>
              <strong>{prediction.severity_trajectory}</strong>
            </div>

            <div>
              <span>Priority</span>
              <strong>
                {String(prediction.welfare_priority).replace("_", " ")}
              </strong>
            </div>

            <div>
              <span>Persistent High</span>
              <strong>{prediction.persistent_high ? "Yes" : "No"}</strong>
            </div>
          </div>
        </div>

        <div className="detail-card">
          <p className="eyebrow">RISK DIMENSIONS</p>

          <div className="risk-dimensions">
            <div className="risk-dimension">
              <span>Stress</span>
              <span
                className={`risk-badge ${riskClass(prediction.stress_risk)}`}
              >
                {prediction.stress_risk}
              </span>
            </div>

            <div className="risk-dimension">
              <span>Fatigue</span>
              <span
                className={`risk-badge ${riskClass(prediction.fatigue_risk)}`}
              >
                {prediction.fatigue_risk}
              </span>
            </div>

            <div className="risk-dimension">
              <span>Burnout</span>
              <span
                className={`risk-badge ${riskClass(prediction.burnout_risk)}`}
              >
                {prediction.burnout_risk}
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="detail-card signals-card">
        <div className="panel-header">
          <div>
            <p className="eyebrow">MODEL OUTPUT</p>
            <h2>Prediction Probabilities</h2>
          </div>
        </div>

        <div className="signals-list">
          <div className="signal-item">
            <span className="signal-icon">◉</span>
            <span>
              Stress High probability:{" "}
              {(prediction.stress_probabilities?.High * 100 || 0).toFixed(1)}%
            </span>
          </div>

          <div className="signal-item">
            <span className="signal-icon">◉</span>
            <span>
              Fatigue High probability:{" "}
              {(prediction.fatigue_probabilities?.High * 100 || 0).toFixed(1)}%
            </span>
          </div>

          <div className="signal-item">
            <span className="signal-icon">◉</span>
            <span>
              Burnout High probability:{" "}
              {(prediction.burnout_probabilities?.High * 100 || 0).toFixed(1)}%
            </span>
          </div>
        </div>
      </section>

      <section className="detail-card human-review-card">
        <div>
          <p className="eyebrow">HUMAN-IN-THE-LOOP</p>
          <h2>AI supports — humans decide.</h2>
          <p>
            TRINETRA provides risk signals and contributing indicators. Any
            welfare intervention remains under authorized human review.
          </p>
        </div>

        <div className="review-status">
          <span className="status-dot"></span>
          Awaiting Welfare Officer Review
        </div>
      </section>
    </div>
  );
}

export default CaseDetail;
