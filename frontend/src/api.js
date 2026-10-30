const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const REQUEST_TIMEOUT_MS = 120000;

function formatDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      const field = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(" ") : "";
      const msg = item.msg || JSON.stringify(item);
      return field ? `${field}: ${msg}` : msg;
    }).join(" ");
  }
  return JSON.stringify(detail);
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_URL}${path}`, { ...options, signal: controller.signal });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = formatDetail(payload?.detail);
      throw new Error(detail || `Request failed (${response.status})`);
    }
    return payload;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("The request took longer than 120 seconds. Please retry.");
    if (error instanceof TypeError) throw new Error("Cannot reach the backend. Check the API URL and CORS configuration.");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function fetchStatus() { return request("/api/status"); }

export function generateItinerary(body) {
  return request("/api/itineraries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
