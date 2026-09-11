const API_BASE_URL = "http://localhost:8000";

async function parseErrorMessage(response) {
  try {
    const data = await response.json();
    return data.detail || `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

export async function sendChatMessage(message, sessionId) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json();
}

export async function clearSession(sessionId) {
  if (!sessionId) return;

  await fetch(`${API_BASE_URL}/api/session/${sessionId}`, {
    method: "DELETE",
  }).catch(() => {});
}

export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}
