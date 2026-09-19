import { useEffect, useState } from "react";
import { getCommanderSummary } from "./api";

function CommanderDashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getCommanderSummary()
      .then((data) => {
        setSummary(data);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load commander dashboard");
      });
  }, []);

  if (error) {
    return (
      <div className="commander-page">
        <div className="api-error">{error}</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="commander-page">
        <div className="loading-state">Loading commander dashboard...</div>
      </div>
    );
  }

  const risk = summary.risk_load;
  const trajectory = summary.trajectory;
  const situation = summary.unit_situation;
  const signals = summary.key_signals;
  const considerations = summary.command_considerations;

  const getSignalClass = (status) => {
    if (!status) return "neutral";

    const value = status.toLowerCase();

    if (
      value.includes("increasing") ||
      value.includes("declining") ||
      value.includes("elevated")
    ) {
      return "warning";
    }

    if (value.includes("improving")) {
      return "positive";
    }

    return "neutral";
  };

  return (
    <div className="commander-page">
      {/* ================= HEADER ================= */}

      <div className="commander-header">
        <div>
          <p className="eyebrow">COMMAND LEVEL INTELLIGENCE</p>

          <h1>Commander Overview</h1>

          <p>
            Unit-level welfare intelligence without exposing individual
            personnel identities.
          </p>
        </div>

        <div className="commander-access">
          <span className="status-dot"></span>
          Aggregate Access
        </div>
      </div>

      {/* ================= PRIVACY ================= */}

      <div className="privacy-banner">
        <div className="privacy-icon">🔒</div>

        <div>
          <strong>Privacy-protected command view</strong>

          <p>
            Individual identities and individual welfare-risk records are
            intentionally hidden. Command decisions are supported using
            aggregate welfare signals.
          </p>
        </div>
      </div>

      {/* ================= UNIT SITUATION ================= */}

      <section className="commander-section">
        <div className="section-heading">
          <p className="eyebrow">UNIT WELFARE STATUS</p>
          <h2>Current Situation</h2>
        </div>

        <div className="situation-card">
          <div className="situation-main">
            <span className="situation-label">Current welfare situation</span>

            <h2>{situation.status}</h2>

            <p>
              {situation.worsening_percentage}% of personnel currently show a
              worsening welfare trajectory.
            </p>
          </div>

          <div className="situation-metric">
            <span>WORSENING</span>

            <strong>{situation.worsening_percentage}%</strong>

            <small>Current unit trajectory</small>
          </div>
        </div>

        {/* IMPORTANT EXPLANATION */}

        <div className="situation-note explanation-note">
          <span className="signal-dot"></span>

          <span>
            Worsening trajectory reflects accumulated changes over time; current
            aggregate signals are presently stable.
          </span>
        </div>
      </section>

      {/* ================= KEY SIGNALS ================= */}

      <section className="commander-section">
        <div className="section-heading">
          <p className="eyebrow">TRINETRA INTELLIGENCE</p>
          <h2>Key Welfare Signals</h2>
        </div>

        <div className="signal-grid">
          {/* WORKLOAD */}

          <div
            className={`commander-signal-card ${getSignalClass(
              signals.workload.status,
            )}`}
          >
            <div className="signal-card-header">
              <span>WORKLOAD PRESSURE</span>

              <span className="signal-indicator"></span>
            </div>

            <strong>{signals.workload.status}</strong>

            <small>Aggregate workload index: {signals.workload.value}</small>
          </div>

          {/* RECOVERY */}

          <div
            className={`commander-signal-card ${getSignalClass(
              signals.recovery.status,
            )}`}
          >
            <div className="signal-card-header">
              <span>RECOVERY</span>

              <span className="signal-indicator"></span>
            </div>

            <strong>{signals.recovery.status}</strong>

            <small>
              Sleep / recovery trend is currently{" "}
              {signals.recovery.status.toLowerCase()}.
            </small>
          </div>

          {/* STRESS */}

          <div
            className={`commander-signal-card ${getSignalClass(
              signals.stress.status,
            )}`}
          >
            <div className="signal-card-header">
              <span>STRESS</span>

              <span className="signal-indicator"></span>
            </div>

            <strong>{signals.stress.status}</strong>

            <small>
              Aggregate stress trend is currently{" "}
              {signals.stress.status.toLowerCase()}.
            </small>
          </div>

          {/* FATIGUE */}

          <div
            className={`commander-signal-card ${getSignalClass(
              signals.fatigue.status,
            )}`}
          >
            <div className="signal-card-header">
              <span>FATIGUE</span>

              <span className="signal-indicator"></span>
            </div>

            <strong>{signals.fatigue.status}</strong>

            <small>
              Aggregate fatigue trend is currently{" "}
              {signals.fatigue.status.toLowerCase()}.
            </small>
          </div>
        </div>
      </section>

      {/* ================= PERSONNEL SNAPSHOT ================= */}

      <section className="commander-section">
        <div className="section-heading">
          <p className="eyebrow">UNIT SNAPSHOT</p>
          <h2>Personnel Welfare Load</h2>
        </div>

        <div className="commander-stats">
          <div className="commander-stat-card">
            <span>Total Personnel</span>

            <strong>{summary.total_personnel}</strong>

            <small>Personnel in current unit view</small>
          </div>

          <div className="commander-stat-card high-card">
            <span>High Risk</span>

            <strong>{risk.High}%</strong>

            <small>Elevated welfare-risk load</small>
          </div>

          <div className="commander-stat-card monitor-card">
            <span>Monitor</span>

            <strong>{risk.Monitor}%</strong>

            <small>Personnel under observation</small>
          </div>

          <div className="commander-stat-card low-card">
            <span>Low Risk</span>

            <strong>{risk.Low}%</strong>

            <small>Within routine monitoring range</small>
          </div>
        </div>
      </section>

      {/* ================= RISK DISTRIBUTION ================= */}

      <section className="commander-section">
        <div className="section-heading">
          <p className="eyebrow">RISK DISTRIBUTION</p>
          <h2>Current Welfare Load</h2>
        </div>

        <div className="risk-load-panel">
          <div className="risk-load-row">
            <div className="risk-load-label">
              <span>High Risk</span>
              <strong>{risk.High}%</strong>
            </div>

            <div className="risk-bar">
              <div
                className="risk-bar-fill high"
                style={{ width: `${risk.High}%` }}
              ></div>
            </div>
          </div>

          <div className="risk-load-row">
            <div className="risk-load-label">
              <span>Monitor</span>
              <strong>{risk.Monitor}%</strong>
            </div>

            <div className="risk-bar">
              <div
                className="risk-bar-fill monitor"
                style={{ width: `${risk.Monitor}%` }}
              ></div>
            </div>
          </div>

          <div className="risk-load-row">
            <div className="risk-load-label">
              <span>Low Risk</span>
              <strong>{risk.Low}%</strong>
            </div>

            <div className="risk-bar">
              <div
                className="risk-bar-fill low"
                style={{ width: `${risk.Low}%` }}
              ></div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= TRAJECTORY ================= */}

      <section className="commander-section">
        <div className="section-heading">
          <p className="eyebrow">WELFARE TRAJECTORY</p>
          <h2>Unit-Level Trend</h2>
        </div>

        <div className="trajectory-grid">
          <div className="trajectory-card improving">
            <span className="trajectory-icon">↘</span>

            <div>
              <span>Improving</span>
              <strong>{trajectory.Improving}%</strong>
            </div>
          </div>

          <div className="trajectory-card stable">
            <span className="trajectory-icon">→</span>

            <div>
              <span>Stable</span>
              <strong>{trajectory.Stable}%</strong>
            </div>
          </div>

          <div className="trajectory-card worsening">
            <span className="trajectory-icon">↗</span>

            <div>
              <span>Worsening</span>
              <strong>{trajectory.Worsening}%</strong>
            </div>
          </div>
        </div>
      </section>

      {/* ================= COMMAND CONSIDERATION ================= */}

      <section className="commander-guidance">
        <div>
          <p className="eyebrow">COMMAND CONSIDERATION</p>

          <h2>AI supports — command responds.</h2>

          <p>
            TRINETRA provides aggregate welfare signals to support command-level
            awareness. It does not make personnel decisions or determine
            individual interventions.
          </p>

          <div className="consideration-list">
            {considerations.map((item, index) => (
              <div className="consideration-item" key={index}>
                <span>→</span>
                {item}
              </div>
            ))}
          </div>
        </div>

        <div className="guidance-badge">
          <span className="status-dot"></span>
          No Individual Data Exposed
        </div>
      </section>
    </div>
  );
}

export default CommanderDashboard;
