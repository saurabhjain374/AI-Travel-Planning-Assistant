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

    try {
      const result = await sendChatMessage(question, sessionId);

      setSessionId(result.session_id);
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: result.answer,
          sources: result.sources,
          toolsUsed: result.tools_used,
        },
      ]);
    } catch (err) {
      setError(err.message || "Something went wrong while contacting the assistant.");
    } finally {
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
          <span className="app-logo">🇸🇬</span>
          <div>
            <h1>AI Travel Planning Assistant</h1>
            <p>Singapore · Knowledge base + live weather &amp; currency</p>
          </div>
        </div>

        <div className="app-header-actions">
          <span className={`status-dot ${backendOnline ? "status-online" : "status-offline"}`} />
          <span className="status-label">
            {backendOnline === null ? "Checking..." : backendOnline ? "Backend online" : "Backend offline"}
          </span>
          <button className="btn-secondary" onClick={handleNewConversation}>
            New conversation
          </button>
        </div>
      </header>

      <main className="chat-panel">
        <div className="messages-scroll">
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}

          {isLoading && (
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
          <button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>
      </main>
    </div>
  );
}

export default App;
