import { useEffect, useState } from "react";
import { getDashboardCaseDetail } from "./api";

function CaseDetail({ personnelId, onBack }) {
  const [caseDetail, setCaseDetail] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!personnelId) return;

    setCaseDetail(null);
    setError(null);

    getDashboardCaseDetail(personnelId)
      .then((data) => {
        if (data.error) {
          throw new Error(data.error);
        }

        setCaseDetail(data);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load personnel case details");
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

  if (!caseDetail) {
    return (
      <div className="case-detail-page">
        <button className="back-button" onClick={onBack}>
          ← Welfare Cases
        </button>

        <div className="loading-state">Loading case details...</div>
      </div>
    );
  }

  const riskClass = (value) => {
    if (!value) return "";

    return String(value).toLowerCase();
  };

  // explanation_signals can arrive from CSV as a string.
  // Convert it into an array before rendering.
  let signals = caseDetail.explanation_signals;

  if (typeof signals === "string") {
    try {
      signals = JSON.parse(signals.replace(/'/g, '"'));
    } catch {
      signals = signals
        .replace(/^\[|\]$/g, "")
        .split(",")
        .map((signal) => signal.trim().replace(/^['"]|['"]$/g, ""))
        .filter(Boolean);
    }
  }

  if (!Array.isArray(signals)) {
    signals = [];
  }

  return (
    <div className="case-detail-page">
      {/* ================= HEADER ================= */}

      <div className="case-detail-header">
        <div>
          <p className="eyebrow">WELFARE CASE</p>

          <h1>{caseDetail.personnel_id}</h1>

          <p>Week {caseDetail.week_index} · AI-assisted welfare assessment</p>
        </div>

        <button className="back-button" onClick={onBack}>
          ← Welfare Cases
        </button>
      </div>

      {/* ================= OVERALL + DIMENSIONS ================= */}

      <section className="detail-grid">
        <div className="detail-card overall-card">
          <p className="eyebrow">OVERALL RISK</p>

          <div className="overall-risk-row">
            <span
              className={`risk-badge ${riskClass(caseDetail.risk.overall)}`}
            >
              {caseDetail.risk.overall}
            </span>

            <span className="severity-value">
              Severity {Number(caseDetail.severity).toFixed(2)}
            </span>
          </div>

          <div className="case-meta">
            <div>
              <span>Trajectory</span>
              <strong>{caseDetail.trajectory}</strong>
            </div>

            <div>
              <span>Priority</span>
              <strong>{caseDetail.welfare_priority}</strong>
            </div>

            <div>
              <span>Persistent High</span>
              <strong>{caseDetail.persistent_high ? "Yes" : "No"}</strong>
            </div>
          </div>
        </div>

        <div className="detail-card">
          <p className="eyebrow">RISK DIMENSIONS</p>

          <div className="risk-dimensions">
            <div className="risk-dimension">
              <span>Stress</span>

              <span
                className={`risk-badge ${riskClass(caseDetail.risk.stress)}`}
              >
                {caseDetail.risk.stress}
              </span>
            </div>

            <div className="risk-dimension">
              <span>Fatigue</span>

              <span
                className={`risk-badge ${riskClass(caseDetail.risk.fatigue)}`}
              >
                {caseDetail.risk.fatigue}
              </span>
            </div>

            <div className="risk-dimension">
              <span>Burnout</span>

              <span
                className={`risk-badge ${riskClass(caseDetail.risk.burnout)}`}
              >
                {caseDetail.risk.burnout}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ================= EXPLAINABILITY ================= */}

      <section className="detail-card signals-card">
        <div className="panel-header">
          <div>
            <p className="eyebrow">EXPLAINABILITY</p>
            <h2>Contributing Signals</h2>
          </div>
        </div>

        <div className="signals-list">
          {signals.length > 0 ? (
            signals.map((signal, index) => (
              <div className="signal-item" key={index}>
                <span className="signal-icon">◉</span>

                <span>{signal}</span>
              </div>
            ))
          ) : (
            <p>No significant contributing signals identified.</p>
          )}
        </div>
      </section>

      {/* ================= HUMAN REVIEW ================= */}

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
