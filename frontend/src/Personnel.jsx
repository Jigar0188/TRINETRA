import { useEffect, useState } from "react";
import { getPersonnel } from "./api";

function Personnel({ onPersonnelSelect }) {
  const [personnel, setPersonnel] = useState([]);
  const [filteredPersonnel, setFilteredPersonnel] = useState([]);
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getPersonnel()
      .then((data) => {
        setPersonnel(data.personnel);
        setFilteredPersonnel(data.personnel);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to load personnel directory");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    let result = personnel;

    if (search.trim()) {
      result = result.filter((person) =>
        person.personnel_id.toLowerCase().includes(search.toLowerCase()),
      );
    }

    if (riskFilter !== "All") {
      result = result.filter((person) => person.overall_risk === riskFilter);
    }

    setFilteredPersonnel(result);
  }, [search, riskFilter, personnel]);

  if (loading) {
    return (
      <div className="personnel-page">
        <div className="loading-state">Loading personnel directory...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="personnel-page">
        <div className="api-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="personnel-page">
      {/* ================= HEADER ================= */}

      <div className="personnel-header">
        <div>
          <p className="eyebrow">WELFARE MANAGEMENT</p>
          <h1>Personnel Directory</h1>
          <p>
            Current welfare status across the monitored personnel population.
          </p>
        </div>

        <div className="personnel-count-badge">
          {personnel.length} PERSONNEL
        </div>
      </div>

      {/* ================= SUMMARY ================= */}

      <div className="personnel-summary">
        <div className="personnel-summary-card">
          <span>TOTAL PERSONNEL</span>
          <strong>{personnel.length}</strong>
          <small>Current personnel snapshot</small>
        </div>

        <div className="personnel-summary-card high">
          <span>HIGH RISK</span>
          <strong>
            {
              personnel.filter((person) => person.overall_risk === "High")
                .length
            }
          </strong>
          <small>Elevated welfare-risk signal</small>
        </div>

        <div className="personnel-summary-card monitor">
          <span>MONITOR</span>
          <strong>
            {
              personnel.filter((person) => person.overall_risk === "Monitor")
                .length
            }
          </strong>
          <small>Under observation</small>
        </div>

        <div className="personnel-summary-card low">
          <span>LOW RISK</span>
          <strong>
            {personnel.filter((person) => person.overall_risk === "Low").length}
          </strong>
          <small>Within routine monitoring range</small>
        </div>
      </div>

      {/* ================= DIRECTORY ================= */}

      <div className="personnel-panel">
        <div className="personnel-toolbar">
          <div>
            <p className="eyebrow">PERSONNEL DIRECTORY</p>
            <h2>Current Personnel</h2>
          </div>

          <div className="personnel-controls">
            <input
              type="text"
              placeholder="Search personnel ID..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="personnel-search"
            />

            <select
              value={riskFilter}
              onChange={(event) => setRiskFilter(event.target.value)}
              className="personnel-filter"
            >
              <option value="All">All Risk</option>
              <option value="High">High</option>
              <option value="Monitor">Monitor</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </div>

        <div className="personnel-table-wrapper">
          <table className="cases-table personnel-table">
            <thead>
              <tr>
                <th>Personnel</th>
                <th>Role</th>
                <th>Posting</th>
                <th>Service</th>
                <th>Stress</th>
                <th>Fatigue</th>
                <th>Burnout</th>
                <th>Overall</th>
                <th>Trajectory</th>
                <th>Priority</th>
              </tr>
            </thead>

            <tbody>
              {filteredPersonnel.map((person) => (
                <tr key={person.personnel_id}>
                  <td>
                    <button
                      className="personnel-link"
                      onClick={() => onPersonnelSelect(person.personnel_id)}
                    >
                      {person.personnel_id}
                    </button>
                  </td>

                  <td>{person.role_category}</td>

                  <td>{person.posting_type}</td>

                  <td>{person.service_tenure_months} mo</td>

                  <td>
                    <span
                      className={`risk-badge ${person.stress_risk.toLowerCase()}`}
                    >
                      {person.stress_risk}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`risk-badge ${person.fatigue_risk.toLowerCase()}`}
                    >
                      {person.fatigue_risk}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`risk-badge ${person.burnout_risk.toLowerCase()}`}
                    >
                      {person.burnout_risk}
                    </span>
                  </td>

                  <td>
                    <span
                      className={`risk-badge ${person.overall_risk.toLowerCase()}`}
                    >
                      {person.overall_risk}
                    </span>
                  </td>

                  <td>{person.severity_trajectory}</td>

                  <td>
                    <span
                      className={`priority-badge ${person.welfare_priority.toLowerCase()}`}
                    >
                      {person.welfare_priority.replace("_", " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredPersonnel.length === 0 && (
            <div className="empty-state">
              No personnel match the selected filters.
            </div>
          )}
        </div>
      </div>

      {/* ================= PRIVACY ================= */}

      <div className="privacy-note">
        <strong>Authorized welfare access</strong>
        <span>
          Personnel-level welfare information is available only within the
          authorized welfare management view.
        </span>
      </div>
    </div>
  );
}

export default Personnel;
