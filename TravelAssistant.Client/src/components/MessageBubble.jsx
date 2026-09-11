import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const TOOL_LABELS = {
  get_weather: { icon: "⛅", label: "Live Weather" },
  convert_currency: { icon: "💱", label: "Live Currency" },
};

// Give the model's "Live update:" / "Recommendation:" prefixes (see the
// grounding rules in orchestrator.py) a small icon so they stand out
// visually from plain knowledge-base facts.
function decorateAnswer(content) {
  return content
    .replace(/Live update:/g, "🔴 **Live update:**")
    .replace(/Recommendation:/g, "💡 **Recommendation:**");
}

function ToolBadge({ toolName }) {
  const meta = TOOL_LABELS[toolName] || { icon: "🔧", label: toolName };

  return (
    <span className="badge badge-tool">
      {meta.icon} {meta.label}
    </span>
  );
}

function SourceChip({ source }) {
  const label = source.title || source.file || "Knowledge base";

  const content = (
    <span className="badge badge-source">📖 {label}</span>
  );

  if (source.url) {
    return (
      <a
        className="source-link"
        href={source.url}
        target="_blank"
        rel="noreferrer"
      >
        {content}
      </a>
    );
  }

  return content;
}

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "message-row-user" : ""}`}>
      <div className={`avatar ${isUser ? "avatar-user" : "avatar-assistant"}`}>
        {isUser ? "🧳" : "🌴"}
      </div>

      <div className={`bubble ${isUser ? "bubble-user" : "bubble-assistant"}`}>
        <div className="bubble-text">
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {decorateAnswer(message.content)}
            </ReactMarkdown>
          )}
          {!isUser && message.streaming && <span className="streaming-cursor" aria-label="Generating response" />}
        </div>

        {!isUser && message.toolsUsed && message.toolsUsed.length > 0 && (
          <div className="badge-row">
            {message.toolsUsed.map((tool) => (
              <ToolBadge key={tool} toolName={tool} />
            ))}
          </div>
        )}

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="sources-block">
            <div className="sources-label">Sources</div>
            <div className="badge-row">
              {message.sources.map((source, index) => (
                <SourceChip key={`${source.file}-${index}`} source={source} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
