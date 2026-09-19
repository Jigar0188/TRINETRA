import "./App.css";
import { useEffect, useState } from "react";

import { getDashboardSummary, getDashboardCases } from "./api";

import CommanderDashboard from "./CommanderDashboard";
import Analytics from "./Analytics";
import WelfareCases from "./WelfareCases";
import Overview from "./Overview";
import CaseDetail from "./CaseDetail";
import Personnel from "./Personnel";

function App() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [cases, setCases] = useState([]);
  const [activeView, setActiveView] = useState("overview");
  const [selectedPersonnel, setSelectedPersonnel] = useState(null);

  // ================= LOAD DASHBOARD DATA =================

  useEffect(() => {
    Promise.all([getDashboardSummary(), getDashboardCases()])
      .then(([summaryData, casesData]) => {
        setSummary(summaryData);
        setCases(casesData.cases);
      })
      .catch((err) => {
        console.error(err);
        setError("Unable to connect to TRINETRA API");
      });
  }, []);

  // ================= OPEN CASE EVENT =================

  useEffect(() => {
    const handleOpenCase = (event) => {
      setSelectedPersonnel(event.detail);
      setActiveView("detail");
    };

    window.addEventListener("open-personnel-case", handleOpenCase);

    return () => {
      window.removeEventListener("open-personnel-case", handleOpenCase);
    };
  }, []);

  // ================= VIEW RENDERING =================

  const renderView = () => {
    switch (activeView) {
      case "overview":
        return (
          <>
            <header className="topbar">
              <div>
                <p className="eyebrow">WELFARE MANAGEMENT</p>
                <h1>Personnel Overview</h1>
              </div>

              <div className="topbar-right">
                <span className="live-indicator">
                  <span className="status-dot"></span>
                  Live
                </span>

                <div className="topbar-avatar">WO</div>
              </div>
            </header>

            {error && <div className="api-error">{error}</div>}

            <Overview summary={summary} cases={cases} />
          </>
        );

      case "cases":
        return (
          <WelfareCases
            cases={cases}
            onBack={() => setActiveView("overview")}
            onCaseSelect={(personnelId) => {
              setSelectedPersonnel(personnelId);
              setActiveView("detail");
            }}
          />
        );

      case "personnel":
        return (
          <Personnel
            onPersonnelSelect={(personnelId) => {
              setSelectedPersonnel(personnelId);
              setActiveView("detail");
            }}
          />
        );

      case "detail":
        return (
          <CaseDetail
            personnelId={selectedPersonnel}
            onBack={() => setActiveView("cases")}
          />
        );

      case "analytics":
        return <Analytics />;

      case "commander":
        return <CommanderDashboard />;

      default:
        return <Overview summary={summary} cases={cases} />;
    }
  };

  // ================= MAIN APP =================

  return (
    <div className="app">
      {/* ================= SIDEBAR ================= */}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">T</div>

          <div>
            <h2>TRINETRA</h2>
            <span>Beyond Duty, We Care</span>
          </div>
        </div>

        <nav className="navigation">
          {/* OVERVIEW */}

          <button
            className={`nav-item ${activeView === "overview" ? "active" : ""}`}
            onClick={() => setActiveView("overview")}
          >
            <span>◉</span>
            Overview
          </button>

          {/* WELFARE CASES */}

          <button
            className={`nav-item ${
              activeView === "cases" || activeView === "detail" ? "active" : ""
            }`}
            onClick={() => setActiveView("cases")}
          >
            <span>⚠</span>
            Welfare Cases
          </button>

          {/* PERSONNEL */}

          <button
            className={`nav-item ${activeView === "personnel" ? "active" : ""}`}
            onClick={() => setActiveView("personnel")}
          >
            <span>◌</span>
            Personnel
          </button>

          {/* ANALYTICS */}

          <button
            className={`nav-item ${activeView === "analytics" ? "active" : ""}`}
            onClick={() => setActiveView("analytics")}
          >
            <span>▣</span>
            Analytics
          </button>

          {/* COMMANDER VIEW */}

          <button
            className={`nav-item ${activeView === "commander" ? "active" : ""}`}
            onClick={() => setActiveView("commander")}
          >
            <span>▤</span>
            Commander View
          </button>
        </nav>

        {/* ================= SIDEBAR BOTTOM ================= */}

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot"></span>

            <div>
              <strong>System Online</strong>
              <small>AI services operational</small>
            </div>
          </div>

          <div className="user-profile">
            <div className="avatar">WO</div>

            <div>
              <strong>Welfare Officer</strong>
              <small>Authorized Access</small>
            </div>
          </div>
        </div>
      </aside>

      {/* ================= MAIN CONTENT ================= */}

      <main className="main-content">{renderView()}</main>
    </div>
  );
}

export default App;
