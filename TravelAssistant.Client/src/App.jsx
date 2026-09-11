import { useEffect, useRef, useState } from "react";
import MessageBubble from "./components/MessageBubble";
import { checkHealth, clearSession, sendChatMessage } from "./api";
import "./App.css";

const SESSION_STORAGE_KEY = "ai-travel-agent-session-id";

const SUGGESTIONS = [
  "Create a three-day Singapore itinerary for next week and adjust it according to the weather forecast.",
  "Convert INR 50,000 to SGD.",
  "What indoor attractions can I visit in Singapore?",
  "Suggest activities for a family with children.",
];

const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Hi! I'm your Singapore travel planning assistant. Ask me about attractions, itineraries, " +
    "live weather, or currency conversion — I can combine destination knowledge with real-time data.",
};

function createSessionId() {
  return crypto.randomUUID
    ? crypto.randomUUID()
    : `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M2.01 21 23 12 2.01 3 2 10l15 2-15 2z" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="23 4 23 10 17 10" />
      <polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  );
}

function App() {
  const [sessionId, setSessionId] = useState(
    () => sessionStorage.getItem(SESSION_STORAGE_KEY) || createSessionId()
  );
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendOnline, setBackendOnline] = useState(null);

  const scrollAnchorRef = useRef(null);

  useEffect(() => {
    sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }, [sessionId]);

  useEffect(() => {
    checkHealth().then(setBackendOnline);
  }, []);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  async function handleSend(text) {
    const question = text.trim();

    if (!question || isLoading) return;

    setError(null);
    setInput("");
    setMessages((previous) => [...previous, { role: "user", content: question }]);
    setIsLoading(true);

    let assistantMessageAdded = false;

    function appendToAssistantMessage(updater) {
      setMessages((previous) => {
        const next = [...previous];
        next[next.length - 1] = updater(next[next.length - 1]);
        return next;
      });
    }

    try {
      await sendChatMessage(question, sessionId, {
        onMeta: ({ session_id, sources, tools_used }) => {
          setSessionId(session_id);
          assistantMessageAdded = true;
          setMessages((previous) => [
            ...previous,
            { role: "assistant", content: "", sources, toolsUsed: tools_used, streaming: true },
          ]);
        },
        onChunk: (text) => {
          if (!assistantMessageAdded) return;
          appendToAssistantMessage((message) => ({
            ...message,
            content: message.content + text,
          }));
        },
      });
    } catch (err) {
      setError(err.message || "Something went wrong while contacting the assistant.");
    } finally {
      if (assistantMessageAdded) {
        appendToAssistantMessage((message) => ({ ...message, streaming: false }));
      }
      setIsLoading(false);
    }
  }

  async function handleNewConversation() {
    await clearSession(sessionId);

    const nextSessionId = createSessionId();
    setSessionId(nextSessionId);
    setMessages([WELCOME_MESSAGE]);
    setError(null);
  }

  function handleSubmit(event) {
    event.preventDefault();
    handleSend(input);
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-title">
          <span className="app-logo">✈️</span>
          <div>
            <h1>AI Travel Planning Assistant</h1>
            <p>Your friendly guide to Singapore, with live weather &amp; currency updates</p>
          </div>
        </div>

        <div className="app-header-actions">
          <span
            className={`status-dot ${backendOnline ? "status-online" : "status-offline"}`}
            title={backendOnline === null ? "Checking backend..." : backendOnline ? "Backend online" : "Backend offline"}
          />
          <button className="btn-secondary" onClick={handleNewConversation} title="Start a new conversation">
            <RefreshIcon />
            New chat
          </button>
        </div>
      </header>

      <main className="chat-panel">
        <div className="messages-scroll">
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}

          {isLoading && messages[messages.length - 1]?.role === "user" && (
            <div className="message-row">
              <div className="avatar avatar-assistant">🌴</div>
              <div className="bubble bubble-assistant typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          <div ref={scrollAnchorRef} />
        </div>

        {error && <div className="error-banner">⚠️ {error}</div>}

        {messages.length <= 1 && (
          <div className="suggestions">
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                className="suggestion-chip"
                onClick={() => handleSend(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        <form className="composer" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            placeholder="Ask about Singapore attractions, weather, or currency..."
            onChange={(event) => setInput(event.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={isLoading || !input.trim()} aria-label="Send message">
            <SendIcon />
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;
