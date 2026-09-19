function WelfareCases({ cases, onBack, onCaseSelect }) {
  return (
    <div className="cases-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">WELFARE MANAGEMENT</p>
          <h1>Welfare Cases</h1>
          <p className="page-description">
            Review personnel requiring welfare attention based on AI-generated
            risk signals.
          </p>
        </div>

        <button className="back-button" onClick={onBack}>
          ← Overview
        </button>
      </div>

      <div className="case-summary">
        <div>
          <span>Personnel Snapshot</span>
          <strong>{cases.length}</strong>
        </div>

        <div>
          <span>Priority</span>
          <strong>
            {
              cases.filter((item) => item.welfare_priority === "Priority")
                .length
            }
          </strong>
        </div>

        <div>
          <span>Review</span>
          <strong>
            {cases.filter((item) => item.welfare_priority === "Review").length}
          </strong>
        </div>
      </div>

      <div className="cases-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">CASE QUEUE</p>
            <h2>Personnel Requiring Attention</h2>
          </div>

          <span className="case-count">
            Showing {Math.min(cases.length, 50)} of {cases.length}
          </span>
        </div>

        <div className="full-cases-table-wrapper">
          <table className="cases-table full-cases-table">
            <thead>
              <tr>
                <th>Personnel</th>
                <th>Week</th>
                <th>Stress</th>
                <th>Fatigue</th>
                <th>Burnout</th>
                <th>Overall</th>
                <th>Severity</th>
                <th>Trajectory</th>
                <th>Priority</th>
              </tr>
            </thead>

            <tbody>
              {cases.slice(0, 50).map((caseItem) => (
                <tr key={caseItem.case_id}>
                  <td>
                    <button
                      className="personnel-link"
                      onClick={() => onCaseSelect(caseItem.personnel_id)}
                    >
                      {caseItem.personnel_id}
                    </button>
                  </td>

                  <td>W{caseItem.week_index}</td>

                  <td>
                    <span
                      className={`risk-badge ${caseItem.stress_risk.toLowerCase()}`}
                    >
                      {caseItem.stress_risk}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`risk-badge ${caseItem.fatigue_risk.toLowerCase()}`}
                    >
                      {caseItem.fatigue_risk}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`risk-badge ${caseItem.burnout_risk.toLowerCase()}`}
                    >
                      {caseItem.burnout_risk}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`risk-badge ${caseItem.overall_risk.toLowerCase()}`}
                    >
                      {caseItem.overall_risk}
                    </span>
                  </td>

                  <td>{Number(caseItem.risk_severity_score).toFixed(2)}</td>

                  <td>{caseItem.severity_trajectory}</td>

                  <td>
                    <span
                      className={`priority-badge ${caseItem.welfare_priority.toLowerCase()}`}
                    >
                      {caseItem.welfare_priority.replace("_", " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="privacy-note">
        <strong>Privacy-aware workflow</strong>

        <span>
          Individual welfare records are visible only to authorized welfare
          personnel. Command-level views use aggregate signals.
        </span>
      </div>
    </div>
  );
}

export default WelfareCases;
