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
2. **Detect intent** by keyword — `should_use_weather` / `should_use_currency`. Pure destination questions skip MCP entirely.
3. **Execute MCP tools** via stdio (`app/mcp/client.py` spawns servers):
   - `get_weather` takes no arguments, so it is called **directly** — no LLM round trip needed to "select" it.
   - `convert_currency` needs amount/from/to parsed from free text, so a **tool-selection LLM call** (bound only to that tool) still extracts its arguments.
   - Errors become `{"error": ...}` — never fabricated.
4. **Final grounding LLM call** — no tools bound; receives KB context + MCP summaries + history + question.
5. Return `{ answer, sources, tools_used }`.

Skipping the LLM call for weather (which never needs argument extraction) roughly halves response time for weather-only questions, since local CPU inference is the dominant cost. The final grounding prompt is also kept as concise as possible (while preserving every grounding rule) to reduce prefill time on every request.

## Sessions

`app/main.py` holds `SESSIONS: dict[session_id, history]` in memory. The client generates a UUID (persisted in `sessionStorage`) and sends it every turn. History is capped at 10 turns; lost on restart.
