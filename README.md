# AI Travel Planning Assistant — Singapore

A context-aware travel assistant that combines a document-based knowledge base (RAG) with
live weather and currency data retrieved through MCP (Model Context Protocol) tools, wrapped
in a FastAPI backend and a React chat UI.

## Project layout

```
AITravelAgentUI/       React (Vite) chat UI
AITravelAgentBackEnd/  FastAPI backend, RAG pipeline, MCP servers/client, orchestrator, tests
docs/                  Full project documentation (see below)
```

## Documentation

Detailed documentation lives in [docs/](docs/):

- [docs/architecture.md](docs/architecture.md) — components, request flow, session handling
- [docs/rag-workflow.md](docs/rag-workflow.md) — knowledge-base sources, chunking, embeddings, retrieval, grounding
- [docs/mcp-tools.md](docs/mcp-tools.md) — weather & currency MCP servers, tool selection, failure handling
- [docs/prompt-strategy.md](docs/prompt-strategy.md) — two-stage prompting, grounding rules, multi-turn context
- [docs/setup.md](docs/setup.md) — full setup instructions for backend, frontend, and tests
- [docs/sample-questions-and-responses.md](docs/sample-questions-and-responses.md) — real, unedited sample Q&A covering RAG-only, MCP-only, and combined RAG+MCP scenarios

## Quick start

```powershell
# Backend
cd AITravelAgentBackEnd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
ollama pull llama3.2:3b
python -m app.rag.vector_store   # build the vector store once
uvicorn app.main:app --reload --port 8000
```

```powershell
# Frontend (separate terminal)
cd AITravelAgentUI
npm install
npm run dev
```

Open http://localhost:5173. See [docs/setup.md](docs/setup.md) for full details and
[docs/sample-questions-and-responses.md](docs/sample-questions-and-responses.md) for
example interactions.

