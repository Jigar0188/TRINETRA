import { useEffect, useState } from "react";
import { getAnalytics } from "./api";

function Analytics() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAnalytics()
      .then(setData)
      .catch((err) => {
        console.error(err);
        setError("Unable to load welfare analytics");
      });
  }, []);

  if (error) {
    return (
      <div className="analytics-page">
        <div className="api-error">{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="analytics-page">
        <div className="loading-state">Loading welfare analytics...</div>
      </div>
    );
  }

  const weeks = data.weeks;

  const latest = weeks[weeks.length - 1];

  const maxHigh = Math.max(...weeks.map((week) => week.high_percentage));

  return (
    <div className="analytics-page">
      {/* HEADER */}

      <div className="analytics-header">
        <div>
          <p className="eyebrow">TRINETRA ANALYTICS</p>
          <h1>Welfare Trends</h1>
          <p>
            Longitudinal view of welfare-risk patterns across the monitored
            personnel population.
          </p>
        </div>

        <div className="analytics-period">26 WEEK WINDOW</div>
      </div>

      {/* CURRENT SNAPSHOT */}

      <section className="analytics-section">
        <div className="section-heading">
          <p className="eyebrow">CURRENT STATE</p>
          <h2>Latest Welfare Snapshot</h2>
        </div>

        <div className="analytics-stats">
          <div className="analytics-stat">
            <span>HIGH RISK</span>
            <strong>{latest.high_percentage}%</strong>
            <small>Current week</small>
          </div>

          <div className="analytics-stat">
            <span>MONITOR</span>
            <strong>{latest.monitor_percentage}%</strong>
            <small>Current week</small>
          </div>

          <div className="analytics-stat">
            <span>LOW RISK</span>
            <strong>{latest.low_percentage}%</strong>
            <small>Current week</small>
          </div>

          <div className="analytics-stat">
            <span>AVG SEVERITY</span>
            <strong>{latest.avg_severity}</strong>
            <small>Current week</small>
          </div>
        </div>
      </section>

      {/* ================= RISK EVOLUTION ================= */}

      <section className="analytics-section">
        <div className="section-heading">
          <p className="eyebrow">RISK EVOLUTION</p>
          <h2>High-Risk Population Over Time</h2>
        </div>

        <div className="risk-chart-card">
          <div className="chart-summary">
            <div>
              <span>PEAK HIGH-RISK LOAD</span>
              <strong>
                {Math.max(...weeks.map((week) => week.high_percentage)).toFixed(
                  1,
                )}
                %
              </strong>
            </div>

            <div>
              <span>PEAK WEEK</span>
              <strong>
                W
                {
                  weeks.reduce(
                    (max, week) =>
                      week.high_percentage > max.high_percentage ? week : max,
                    weeks[0],
                  ).week_index
                }
              </strong>
            </div>

            <div>
              <span>CURRENT</span>
              <strong>{latest.high_percentage}%</strong>
            </div>
          </div>

          <div className="line-chart">
            <div className="chart-grid">
              {[20, 15, 10, 5, 0].map((value) => (
                <div className="grid-row" key={value}>
                  <span>{value}%</span>
                  <div></div>
                </div>
              ))}
            </div>

            <div className="chart-bars">
              {weeks.map((week) => {
                const height = Math.min((week.high_percentage / 20) * 100, 100);

                return (
                  <div className="chart-column" key={week.week_index}>
                    <div
                      className="chart-point"
                      style={{ height: `${height}%` }}
                      title={`Week ${week.week_index}: ${week.high_percentage}%`}
                    >
                      <span></span>
                    </div>

                    <label>W{week.week_index}</label>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>
      {/* TRAJECTORY */}

      <section className="analytics-section">
        <div className="section-heading">
          <p className="eyebrow">TRAJECTORY ANALYSIS</p>
          <h2>Improving vs Worsening</h2>
        </div>

        <div className="trajectory-analytics">
          <div className="trajectory-analytics-card improving">
            <span>IMPROVING</span>

            <strong>{latest.improving}</strong>
            <small>
              {((latest.improving / latest.total) * 100).toFixed(1)}% of
              personnel
            </small>

            <small>Personnel showing improving trajectory</small>
          </div>

          <div className="trajectory-analytics-card worsening">
            <span>WORSENING</span>

            <strong>{latest.worsening}</strong>
            <small>
              {((latest.worsening / latest.total) * 100).toFixed(1)}% of
              personnel
            </small>

            <small>Personnel showing worsening trajectory</small>
          </div>
        </div>
      </section>

      {/* INTERPRETATION */}

      <section className="analytics-insight">
        <div>
          <p className="eyebrow">TRINETRA INSIGHT</p>

          <h2>Welfare risk should be interpreted as a trajectory.</h2>

          <p>
            A single high-risk observation can be noisy. TRINETRA therefore
            tracks welfare patterns across time, combining current risk with
            trajectory and persistence for a more contextual assessment.
          </p>
        </div>

        <div className="analytics-note">Longitudinal monitoring</div>
      </section>
    </div>
  );
}

export default Analytics;
