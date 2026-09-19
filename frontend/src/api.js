const API_BASE_URL = "http://127.0.0.1:8000";

export async function getDashboardSummary() {
  const response = await fetch(`${API_BASE_URL}/dashboard/summary`);

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard summary");
  }

  return response.json();
}
export async function getDashboardCases() {
  const response = await fetch(`${API_BASE_URL}/dashboard/cases`);

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard cases");
  }

  return response.json();
}
export async function getDashboardCaseDetail(personnelId) {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/cases/${personnelId}`,
  );

  if (!response.ok) {
    throw new Error("Failed to fetch case details");
  }

  return response.json();
}

export async function getCommanderSummary() {
  const response = await fetch(`${API_BASE_URL}/dashboard/commander-summary`);

  if (!response.ok) {
    throw new Error("Failed to fetch commander summary");
  }

  return response.json();
}

export async function getAnalytics() {
  const response = await fetch(`${API_BASE_URL}/dashboard/analytics`);

  if (!response.ok) {
    throw new Error("Failed to fetch analytics");
  }

  return response.json();
}

export async function getPersonnel() {
  const response = await fetch(`${API_BASE_URL}/dashboard/personnel`);

  if (!response.ok) {
    throw new Error("Failed to fetch personnel");
  }

  return response.json();
}
