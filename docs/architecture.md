# Architecture

```
React UI (5173) ──► FastAPI /api/chat (8000) ──► Orchestrator
                                                    ├─► RAG: FAISS + HuggingFace embeddings
                                                    ├─► MCP client ──► weather_server.py ──► Open-Meteo
                                                    ├─► MCP client ──► currency_server.py ──► open.er-api.com
                                                    └─► LLM: Ollama llama3.2:3b
```

## Request flow (`app/orchestrator.py :: run_travel_assistant`)

1. **Retrieve** top-4 KB chunks from FAISS (with `source_title`/`source_url` metadata).
2. **Detect intent** by keyword — `should_use_weather` / `should_use_currency`. Pure destination questions skip MCP.
3. **Tool-selection LLM call** — only the relevant tool(s) are bound, capped by `MAX_TOOL_CALLS = 2`.
4. **Execute MCP tools** via stdio (`app/mcp/client.py` spawns servers). Errors become `{"error": ...}` — never fabricated.
5. **Final grounding LLM call** — no tools bound; receives KB context + MCP summaries + history + question.
6. Return `{ answer, sources, tools_used }`.

Two separate LLM calls keep the tool loop bounded and the answer prompt focused purely on grounding.

## Sessions

`app/main.py` holds `SESSIONS: dict[session_id, history]` in memory. UI generates a UUID (persisted in `sessionStorage`) and sends it every turn. History is capped at 10 turns; lost on restart.
