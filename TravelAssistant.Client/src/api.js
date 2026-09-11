const API_BASE_URL = "http://localhost:8000";

async function parseErrorMessage(response) {
  try {
    const data = await response.json();
    return data.detail || `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

// Streams the chat answer as Server-Sent Events so the UI can render
// tokens as they're generated instead of waiting for the full answer.
export async function sendChatMessage(message, sessionId, { onMeta, onChunk } = {}) {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const rawEvent of events) {
      const line = rawEvent.trim();
      if (!line.startsWith("data:")) continue;

      const payload = JSON.parse(line.slice("data:".length).trim());

      if (payload.type === "meta") {
        onMeta?.(payload);
      } else if (payload.type === "chunk") {
        onChunk?.(payload.text);
      }
    }
  }
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

