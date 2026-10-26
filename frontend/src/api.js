const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 25000;

function formatDetail(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc)
          ? item.loc.filter((part) => part !== "body").join(" ")
          : "";
        const msg = item.msg || JSON.stringify(item);
        return field ? `${field}: ${msg}` : msg;
      })
      .join(" ");
  }
  return JSON.stringify(detail);
}

async function readError(response) {
  const payload = await response.json().catch(() => null);
  const detail = formatDetail(payload?.detail);
  return detail || `Request failed (${response.status})`;
}

async function request(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(await readError(response));
    return response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The request timed out. Confirm the FastAPI server is running.");
    }
    if (error instanceof TypeError) {
      throw new Error("Cannot reach the API. Start the FastAPI server on port 8000.");
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchStatus() {
  return request("/api/status");
}

export async function generateItinerary(body) {
  return request("/api/itineraries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
