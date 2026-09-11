# Development Setup

Everything you need to get the assistant running locally, in one place.

## ✅ Prerequisites

| Software | Version | Verify |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js + npm | 18+ / 9+ | `node --version` |
| Git | any | `git --version` |
| [Ollama](https://ollama.com/download) | latest | `ollama --version` |

**Disk space:** ~4–6 GB (Ollama model ~2 GB, embeddings ~90 MB, venv ~1.5 GB, node_modules ~300 MB).
**Speed:** runs on CPU only — expect answers to take **1–3 minutes** per turn.

> **Custom MCP, built from scratch.** Servers and client use the `mcp` SDK directly — no
> pre-built MCP packages. They wrap the free Open-Meteo and open.er-api.com REST APIs, and the
> client auto-spawns both servers over stdio — nothing to start manually.

## 🚀 Startup — 3 terminals

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

Verify: `curl http://localhost:8000/api/health` → `{"status":"ok"}`

### C. Frontend (port 5173)

```powershell
cd TravelAssistant.Client
npm install
npm run dev
```

Open <http://localhost:5173> — the status dot in the header should turn green.

## 🔌 API reference

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Liveness check |
| `POST` | `/api/chat` | `{ message, session_id? }` → streams `{ session_id, answer, sources, tools_used }` as Server-Sent Events |
| `DELETE` | `/api/session/{id}` | Clear a conversation |

## 🧪 Smoke tests

| Type | Question |
|---|---|
| Knowledge base | *What are the must-visit attractions in Singapore?* |
| Weather | *What is the weather in Singapore today?* |
| Currency | *Convert INR 50,000 to SGD.* |
| Combined | *Create a 3-day Singapore itinerary for next week and adjust it to the weather forecast.* |
| Multi-turn | Ask for an itinerary, then follow up: *Now add indoor alternatives if it rains.* |

Run the automated tests: `pytest tests/` (needs Ollama + a built vector store).

## 🛠️ Troubleshooting

| Symptom | Fix |
|---|---|
| UI shows "Backend offline" | Check Terminal B is running; try `curl /api/health` |
| `ConnectError` to `:11434` | Start Ollama (`ollama serve`) |
| `Model 'llama3.2:3b' not found` | `ollama pull llama3.2:3b` |
| `FileNotFoundError: index.faiss` | `python -m app.rag.vector_store` |
| `activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Port already in use | Free the port, or change it with `--port` |
| Weather/currency error in reply | Expected if internet is down — the assistant won't make up a number |

## ⚠️ Known limits

- Sessions live in memory only — they're lost when the backend restarts.
- No client-side timeout — long CPU-bound answers will complete, just slowly.

