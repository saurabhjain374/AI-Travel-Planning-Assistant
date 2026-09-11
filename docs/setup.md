# Development Setup

## Prerequisites

| Software | Version | Verify |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js + npm | 18+ / 9+ | `node --version` |
| Git | any | `git --version` |
| [Ollama](https://ollama.com/download) | latest | `ollama --version` |

Expect ~4–6 GB disk (Ollama model ~2 GB, embeddings ~90 MB, venv ~1.5 GB, node_modules ~300 MB). Runs on CPU; answers take **1–3 min** per turn.

> **Custom MCP:** servers and client are built from scratch with the `mcp` SDK — no pre-built MCP packages consumed. Wrap Open-Meteo and open.er-api.com REST APIs. Client auto-spawns servers over stdio; no manual start needed.

## Startup — 3 terminals

### A. Ollama (LLM host, port 11434)

```powershell
ollama serve                 # or use the desktop app
ollama pull llama3.2:3b      # ~2 GB, one-time
```

### B. Backend (port 8000)

```powershell
cd TravelAssistant.Server
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
python -m app.rag.vector_store          # build FAISS index once
uvicorn app.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/api/health` ? `{"status":"ok"}`

### C. Frontend (port 5173)

```powershell
cd TravelAssistant.Client
npm install
npm run dev
```

Open <http://localhost:5173> — status dot should show "Backend online".

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Liveness |
| `POST` | `/api/chat` | `{ message, session_id? }` ? `{ session_id, answer, sources, tools_used }` |
| `DELETE` | `/api/session/{id}` | Clear conversation |

## Smoke tests

| Type | Question |
|---|---|
| RAG | *What are the must-visit attractions in Singapore?* |
| Weather | *What is the weather in Singapore today?* |
| Currency | *Convert INR 50,000 to SGD.* |
| Combined | *Create a 3-day Singapore itinerary for next week and adjust it to the weather forecast.* |
| Multi-turn | Ask itinerary ? follow up: *Now add indoor alternatives if it rains.* |

Run tests: `pytest tests/` (needs Ollama + vector store).

## Troubleshooting

| Symptom | Fix |
|---|---|
| UI "Backend offline" | Check Terminal B; `curl /api/health` |
| `ConnectError` to `:11434` | Start Ollama (`ollama serve`) |
| `Model 'llama3.2:3b' not found` | `ollama pull llama3.2:3b` |
| `FileNotFoundError: index.faiss` | `python -m app.rag.vector_store` |
| `activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Port already in use | Free port or change with `--port` |
| Weather/currency error in reply | Expected if internet is down — no fabrication |

## Limits

- Sessions are in-memory (lost on restart).
- No client-side timeout — long LLM calls will complete, just slowly on CPU.
