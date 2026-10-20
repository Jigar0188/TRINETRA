const API_BASE_URL = "http://127.0.0.1:8000";

async function fetchJSON(url, errorMessage) {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(errorMessage);
  }

  return response.json();
}

// ============================================================
// EXISTING DASHBOARD ENDPOINTS
// ============================================================

export async function getDashboardSummary() {
  return fetchJSON(
    `${API_BASE_URL}/dashboard/summary`,
    "Failed to fetch dashboard summary",
  );
}

export async function getDashboardCases() {
  return fetchJSON(
    `${API_BASE_URL}/dashboard/cases`,
    "Failed to fetch dashboard cases",
  );
}

export async function getDashboardCaseDetail(personnelId) {
  return fetchJSON(
    `${API_BASE_URL}/dashboard/cases/${personnelId}`,
    "Failed to fetch case details",
  );
}

export async function getCommanderSummary() {
  return fetchJSON(
    `${API_BASE_URL}/dashboard/commander-summary`,
    "Failed to fetch commander summary",
  );
}

export async function getAnalytics() {
  return fetchJSON(
    `${API_BASE_URL}/dashboard/analytics`,
    "Failed to fetch analytics",
  );
}

// ============================================================
// PERSONNEL + LIVE ML PREDICTION
// ============================================================
export async function getPersonnel() {
  const response = await fetch(`${API_BASE_URL}/dashboard/personnel`);

  if (!response.ok) {
    throw new Error("Failed to fetch personnel");
  }

  return response.json();
}

// ============================================================
// LIVE DB → FEATURE ENGINEERING → ML → POLICY
// ============================================================

export async function getPersonnelPrediction(personnelId) {
  return fetchJSON(
    `${API_BASE_URL}/predict/${personnelId}`,
    `Failed to fetch prediction for ${personnelId}`,
  );
}
