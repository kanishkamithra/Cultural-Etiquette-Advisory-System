const API_BASE = "/api";
const CACHEABLE_GET_PATHS = [
  "/stats",
  "/cultures",
  "/scenarios",
  "/rules",
  "/community-tips",
  "/travel-mode/daily-tip",
];

function cacheKey(path) {
  return `ceas-cache:${path}`;
}

export async function apiRequest(path, options = {}, token = null) {
  const headers = { ...(options.headers || {}) };
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const isGet = !options.method || options.method === "GET";

  try {
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    const data = response.status === 204 ? null : await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data?.detail || "Request failed.");
    }
    if (isGet && CACHEABLE_GET_PATHS.some((entry) => path.startsWith(entry))) {
      localStorage.setItem(cacheKey(path), JSON.stringify({ data, cachedAt: Date.now() }));
    }
    return data;
  } catch (error) {
    if (isGet && CACHEABLE_GET_PATHS.some((entry) => path.startsWith(entry))) {
      const cached = localStorage.getItem(cacheKey(path));
      if (cached) {
        return JSON.parse(cached).data;
      }
    }
    throw error;
  }
}
