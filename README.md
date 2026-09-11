# AI Travel Planning Assistant - Singapore

**Your friendly AI travel buddy for Singapore** — ask about attractions, itineraries, live weather,
or currency conversion, and get a grounded, easy-to-read answer in a chat UI.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-llama3.2%3A3b-black?logo=ollama&logoColor=white)

## ✨ What it does

| You ask about... | It answers using... |
|---|---|
| 🏙️ Attractions, itineraries, food, neighbourhoods | A curated **knowledge base** (RAG) — never made-up facts |
| 🌦️ Today's or the next 3 days' weather | **Live data** from Open-Meteo |
| 💱 Currency conversion (e.g. INR → SGD) | **Live rates** from open.er-api.com |
| 🗺️ A weather-aware multi-day plan | Both, combined into one grounded answer |

If the answer isn't in the knowledge base or live data, the assistant says so plainly instead of guessing.

## 🧩 How it's built

```
TravelAssistant.Client/   React (Vite) chat UI — streams answers as they're generated
TravelAssistant.Server/   FastAPI backend — RAG pipeline, MCP tools, LLM orchestration, tests
docs/                     Full technical documentation (see table below)
```

> **Custom-built MCP, from scratch.** Both MCP servers (`weather_server.py`, `currency_server.py`)
> and the MCP client (`client.py`) are hand-built with the official `mcp` Python SDK — no
> ready-made MCP packages. They wrap two free public APIs and are auto-started by the client;
> nothing to run manually.

## 🚀 Quick start

**Prerequisites:** Python 3.11+, Node 18+, Git, and [Ollama](https://ollama.com/download).

| # | Terminal | Command |
|---|---|---|
| 1 | Ollama | `ollama serve` then `ollama pull llama3.2:3b` (~2 GB, one-time) |
| 2 | Backend | `cd TravelAssistant.Server` → create venv → `pip install -r requirements.txt` → `python -m app.rag.vector_store` → `uvicorn app.main:app --reload --port 8000` |
| 3 | Frontend | `cd TravelAssistant.Client` → `npm install` → `npm run dev` |

Then open **http://localhost:5173** — the status dot should turn green once the backend is reachable.

👉 Full step-by-step instructions, verification checks, and troubleshooting: **[docs/setup.md](docs/setup.md)**

## 💬 Try asking

| Type | Example |
|---|---|
| Knowledge base | *"What are the must-visit attractions in Singapore?"* |
| Live weather | *"What is the weather in Singapore today?"* |
| Live currency | *"Convert INR 50,000 to SGD."* |
| Combined | *"Create a three-day Singapore itinerary for next week and adjust it to the weather forecast."* |

More real, unedited examples: **[docs/sample-questions-and-responses.md](docs/sample-questions-and-responses.md)**

## 📚 Documentation

| Doc | What's inside |
|---|---|
| [docs/setup.md](docs/setup.md) | Full setup, prerequisites, API reference, troubleshooting |
| [docs/architecture.md](docs/architecture.md) | Components, request flow, how a session works |
| [docs/rag-workflow.md](docs/rag-workflow.md) | Knowledge base, chunking, embeddings, retrieval |
| [docs/mcp-tools.md](docs/mcp-tools.md) | Weather & currency tools, how they're wired, failure handling |
| [docs/prompt-strategy.md](docs/prompt-strategy.md) | How the assistant stays grounded and avoids making things up |
| [docs/sample-questions-and-responses.md](docs/sample-questions-and-responses.md) | Real Q&A examples, unedited |


