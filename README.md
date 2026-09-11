# AI Travel Planning Assistant — Singapore

A context-aware travel assistant that combines a document-based knowledge base (RAG) with
live weather and currency data retrieved through MCP (Model Context Protocol) tools, wrapped
in a FastAPI backend and a React chat UI.

> **Custom-built MCP servers and client.** Both MCP servers
> (`app/mcp/weather_server.py`, `app/mcp/currency_server.py`) and the MCP client
> (`app/mcp/client.py`) are implemented from scratch using the
> official `mcp` Python SDK. No pre-built / ready-made MCP server packages are consumed.
> The servers wrap two free public REST APIs (Open-Meteo, open.er-api.com) and are
> spawned automatically by the client over stdio — no manual server start required.

## Project layout

```
TravelAssistant.Client/  React (Vite) chat UI
TravelAssistant.Server/  FastAPI backend, RAG pipeline, MCP servers/client, orchestrator, tests
docs/                    Full project documentation (see below)
```

## Documentation

Detailed documentation lives in [docs/](docs/):

- [docs/architecture.md](docs/architecture.md) — components, request flow, session handling
- [docs/rag-workflow.md](docs/rag-workflow.md) — knowledge-base sources, chunking, embeddings, retrieval, grounding
- [docs/mcp-tools.md](docs/mcp-tools.md) — weather & currency MCP servers, tool selection, failure handling
- [docs/prompt-strategy.md](docs/prompt-strategy.md) — two-stage prompting, grounding rules, multi-turn context
- [docs/setup.md](docs/setup.md) — full setup instructions for backend, frontend, and tests
- [docs/sample-questions-and-responses.md](docs/sample-questions-and-responses.md) — real, unedited sample Q&A covering RAG-only, MCP-only, and combined RAG+MCP scenarios

## Quick start (development mode)

> Full step-by-step guide, prerequisites, verification, and troubleshooting are
> in **[docs/setup.md](docs/setup.md)**. This section is the fast path.

**Prerequisites:** Python 3.11+, Node 18+, Git, and [Ollama](https://ollama.com/download)
installed locally.

### Terminal A — Ollama (LLM host)

```powershell
ollama serve                 # leave running (or use the Ollama desktop app)
ollama pull llama3.2:3b      # ~2 GB, one-time
```

### Terminal B — Backend (FastAPI)

```powershell
cd TravelAssistant.Server
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python -m app.rag.vector_store       # build FAISS index once (downloads ~90 MB embedding model)
uvicorn app.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/api/health` → `{"status":"ok"}`.

### Terminal C — Frontend (React + Vite)

```powershell
cd TravelAssistant.Client
npm install
npm run dev
```

Open <http://localhost:5173>. The status dot should read **"Backend online"**.

### Try it

- **RAG only:** *"What are the must-visit attractions in Singapore?"*
- **MCP weather:** *"What is the weather in Singapore today?"*
- **MCP currency:** *"Convert INR 50,000 to SGD."*
- **Combined RAG + MCP:** *"Create a three-day Singapore itinerary for next week and adjust it according to the weather forecast."*

See [docs/setup.md](docs/setup.md) for full details and
[docs/sample-questions-and-responses.md](docs/sample-questions-and-responses.md) for
example interactions.

