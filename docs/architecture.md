# Architecture

## Components

```
AITravelAgentUI/          React (Vite) chat UI
AITravelAgentBackEnd/
  app/
    main.py                 FastAPI backend (/api/chat, /api/health, /api/session/{id})
    orchestrator.py          Combines RAG + MCP into one grounded answer
    llm.py                   Local LLM (Ollama, llama3.2:3b)
    config.py                Reserved for centralized settings
    rag/                     Retrieval-Augmented Generation pipeline
    mcp/                     MCP servers, client, and tool definitions
    services/                Reserved for future service extraction
  data/
    knowledge_base/*.md      Source travel documents (with source_title/source_url metadata)
    vector_store/            Persisted FAISS index
  tests/                     Pytest suite
docs/                      This documentation set
```

## Request flow

`app/main.py` receives a chat request and calls `run_travel_assistant()` in
[app/orchestrator.py](../AITravelAgentBackEnd/app/orchestrator.py), which performs:

1. **RAG retrieval** — embed the question, retrieve top-k chunks from FAISS
   (`app/rag/service.py` → `app/rag/retriever.py` → `app/rag/vector_store.py`),
   collecting `source_title` / `source_url` metadata for citation.
2. **Intent detection** — a keyword check (`should_use_weather`,
   `should_use_currency`) decides whether weather and/or currency data is
   *relevant* to the question. Pure destination questions never trigger MCP.
3. **Tool selection** — if relevant, the LLM is bound to only the allowed
   MCP tool(s) and decides whether/how to call them.
4. **MCP execution** — the chosen tool(s) run as MCP stdio servers
   (`app/mcp/client.py` launches `weather_server.py` / `currency_server.py`);
   results (or a structured error) are captured.
5. **Grounded final answer** — a second LLM call, with no tools bound (so it
   cannot start another tool loop), receives the retrieved KB context, the
   MCP results, and recent conversation history, governed by the grounding
   prompt in `build_final_prompt()`.
6. The API returns `answer`, `sources` (KB citations), and `tools_used`
   (MCP tools invoked) so the UI can label what came from where.

## Why two separate LLM calls

Binding MCP tools to the *final* answer call would let the model keep
chaining tool calls indefinitely. Splitting tool-selection from
answer-generation keeps the loop bounded (see `MAX_TOOL_CALLS` in
`orchestrator.py`) and keeps the final prompt focused purely on grounding
rules instead of tool-calling semantics.

## Session / conversation state

`app/main.py` keeps an in-memory dictionary `SESSIONS: dict[session_id, history]`.
The React UI generates a `session_id` (via `crypto.randomUUID()`) on first load,
persists it in `sessionStorage`, and sends it with every request so follow-up
questions retain context. State is lost on backend restart — there is no
persistent store, which is acceptable for this assignment's scope.
