function Overview({ summary, cases }) {
  const totalPersonnel = summary?.total_personnel ?? 0;
  const highRisk = summary?.risk_distribution?.High ?? 0;
  const monitor = summary?.risk_distribution?.Monitor ?? 0;

  const worsening = summary?.severity_trajectory?.Worsening ?? 0;

  const priorityCases = cases.filter(
    (item) =>
      item.welfare_priority === "Priority" ||
      item.welfare_priority === "Review",
  );

  const priorityCount = cases.filter(
    (item) => item.welfare_priority === "Priority",
  ).length;

  const reviewCount = cases.filter(
    (item) => item.welfare_priority === "Review",
  ).length;

  const worseningPercentage =
    totalPersonnel > 0 ? ((worsening / totalPersonnel) * 100).toFixed(1) : 0;

  return (
    <div className="dashboard-content">
      {/* ================= WELCOME ================= */}

      <div className="welcome-banner">
        <div>
          <p className="eyebrow">TRINETRA INTELLIGENCE</p>

          <h2>Early signals. Timely support.</h2>

          <p>
            AI-assisted welfare intelligence for identifying emerging personnel
            risk and supporting timely human review.
          </p>
        </div>

        <div className="banner-icon">◈</div>
      </div>

      {/* ================= ATTENTION SNAPSHOT ================= */}

      <section className="overview-intelligence">
        <div className="overview-section-heading">
          <div>
            <p className="eyebrow">ATTENTION SNAPSHOT</p>
            <h2>What needs attention?</h2>
          </div>

          <span className="overview-live">
            <span className="status-dot"></span>
            Current snapshot
          </span>
        </div>

        <div className="attention-card">
          <div className="attention-main">
            <div className="attention-icon">⚠</div>

            <div>
              <span className="attention-label">WELFARE ATTENTION LOAD</span>

              <h3>
                {priorityCount + reviewCount} personnel require welfare review
              </h3>

              <p>
                TRINETRA has identified personnel requiring human attention
                based on risk level, trajectory and welfare-priority rules.
              </p>
            </div>
          </div>

          <div className="attention-metrics">
            <div>
              <span>PRIORITY</span>
              <strong>{priorityCount}</strong>
            </div>

            <div>
              <span>REVIEW</span>
              <strong>{reviewCount}</strong>
            </div>
          </div>
        </div>

        <div className="overview-intelligence-note">
          <span className="signal-dot"></span>

          <span>
            {highRisk} personnel are currently classified as High Risk, while{" "}
            {worseningPercentage}% of the current personnel snapshot shows a
            worsening trajectory.
          </span>
        </div>
      </section>

      {/* ================= CORE STATS ================= */}

      <section className="stats-grid">
        <div className="stat-card">
          <span>Total Personnel</span>

          <strong>{totalPersonnel}</strong>

          <small>Active personnel</small>
        </div>

        <div className="stat-card high-stat">
          <span>High Risk</span>

          <strong>{highRisk}</strong>

          <small>Requires attention</small>
        </div>

        <div className="stat-card monitor-stat">
          <span>Monitor</span>

          <strong>{monitor}</strong>

          <small>Under observation</small>
        </div>

        <div className="stat-card worsening-stat">
          <span>Worsening</span>

          <strong>{worsening}</strong>

          <small>Recent deterioration</small>
        </div>
      </section>

      {/* ================= WELFARE QUEUE ================= */}

      <section className="content-grid">
        <div className="panel welfare-queue-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">WELFARE QUEUE</p>
              <h2>Cases Requiring Attention</h2>
            </div>

            <span className="queue-count">{priorityCases.length} cases</span>
          </div>

          <div className="cases-table-wrapper">
            <table className="cases-table">
              <thead>
                <tr>
                  <th>Personnel</th>
                  <th>Stress</th>
                  <th>Fatigue</th>
                  <th>Burnout</th>
                  <th>Overall</th>
                  <th>Trajectory</th>
                  <th>Priority</th>
                </tr>
              </thead>
              <tbody>
                {priorityCases.slice(0, 6).map((caseItem) => (
                  <tr key={`${caseItem.personnel_id}-${caseItem.week_index}`}>
                    <td className="personnel-id">
                      <button
                        className="overview-personnel-link"
                        onClick={() => {
                          window.dispatchEvent(
                            new CustomEvent("open-personnel-case", {
                              detail: caseItem.personnel_id,
                            }),
                          );
                        }}
                      >
                        {caseItem.personnel_id}
                      </button>
                    </td>

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

        {/* ================= SYSTEM PRINCIPLE ================= */}

        <div className="panel intelligence-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">TRINETRA PRINCIPLE</p>
              <h2>From signal to support</h2>
            </div>
          </div>

          <div className="intelligence-flow">
            <div className="flow-step">
              <div className="flow-number">01</div>

              <div>
                <strong>Detect</strong>

                <span>
                  Identify changes across workload, recovery and wellness
                  signals.
                </span>
              </div>
            </div>

            <div className="flow-line"></div>

            <div className="flow-step">
              <div className="flow-number">02</div>

              <div>
                <strong>Assess</strong>

                <span>
                  Combine stress, fatigue and burnout risk with trajectory and
                  persistence.
                </span>
              </div>
            </div>

            <div className="flow-line"></div>

            <div className="flow-step">
              <div className="flow-number">03</div>

              <div>
                <strong>Support</strong>

                <span>
                  Route sensitive cases to authorized welfare personnel for
                  human review.
                </span>
              </div>
            </div>
          </div>

          <div className="human-loop-note">
            <span className="signal-dot"></span>

            <span>AI supports — humans decide.</span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Overview;
