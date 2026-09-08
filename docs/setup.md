# Setup Instructions

## Prerequisites

- Python 3.11+ with a virtual environment
- [Ollama](https://ollama.com/) installed and running locally
- Node.js 18+ and npm (for the React UI)

## 1. Backend

```powershell
cd AITravelAgentBackEnd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Pull the local LLM used by app/llm.py
ollama pull llama3.2:3b

# Build the FAISS vector store from data/knowledge_base (only needed once,
# or after editing/adding knowledge-base documents)
python -m app.rag.vector_store

# Start the API (reload enabled for development)
uvicorn app.main:app --reload --port 8000
```

The backend exposes:

- `POST /api/chat` — `{ "message": "...", "session_id": "..." }` →
  `{ session_id, answer, sources, tools_used }`
- `GET /api/health`
- `DELETE /api/session/{session_id}` — clears a conversation's history

## 2. Frontend (AITravelAgentUI/)

```powershell
cd AITravelAgentUI
npm install
npm run dev
```

Open http://localhost:5173. The UI calls the backend at
`http://localhost:8000` (see `AITravelAgentUI/src/api.js`); CORS for
`localhost:5173` is already allowed in `app/main.py`.

## 3. Tests

```powershell
cd AITravelAgentBackEnd
pytest tests/
```

`tests/test_rag_service.py` and `tests/test_tool_calling.py` require the
vector store to exist and Ollama to be running (they make real LLM calls).

## Notes / limitations

- Conversation history is kept **in memory** on the backend; it resets on
  server restart and does not scale across multiple worker processes.
- `llama3.2:3b` on CPU is slow — a single grounded response can take one to a
  few minutes. There is no client-side timeout in the React UI, so requests
  will complete, just not quickly.
- MCP servers (`weather_server.py`, `currency_server.py`) call public APIs
  over the internet; without connectivity they return a structured error
  rather than fabricated data.
