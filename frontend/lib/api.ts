const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const SESSION_KEY = "crate_session";

export function getSessionId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return sessionStorage.getItem(SESSION_KEY);
}

export function setSessionId(sessionId: string) {
  sessionStorage.setItem(SESSION_KEY, sessionId);
}

export function clearSessionId() {
  sessionStorage.removeItem(SESSION_KEY);
}

export function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const sessionId = getSessionId();
  if (sessionId) {
    headers.set("Authorization", `Bearer ${sessionId}`);
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers,
  });
}

export function loginUrl() {
  return `${API_URL}/auth/spotify/login`;
}
