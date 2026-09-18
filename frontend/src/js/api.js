/* API Wrapper & Streaming Service */
export const API_URL = window.__VERINEWS_API_URL__ ||
  (typeof localStorage !== "undefined" && localStorage.getItem("verinews_api_url")) ||
  (location.hostname === 'localhost' || location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:8000'
    : 'https://verinewsai-1.onrender.com');

export async function fetchVerification(claimText) {
  const response = await fetch(`${API_URL}/search?query=${encodeURIComponent(claimText)}`);
  if (!response.ok) {
    throw new Error(`Verification API HTTP Error: ${response.status}`);
  }
  return await response.json();
}

export async function fetchAdminStats() {
  const res = await fetch(`${API_URL}/api/admin/stats`);
  if (!res.ok) throw new Error("Failed to fetch admin stats");
  return await res.json();
}

export async function fetchAnalyticsSummary() {
  const res = await fetch(`${API_URL}/api/analytics/summary`);
  if (!res.ok) throw new Error("Failed to fetch analytics");
  return await res.json();
}

export async function saveAdminConfig(configObj) {
  const res = await fetch(`${API_URL}/api/admin/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(configObj)
  });
  return res.ok;
}
