# Prompt & Context Strategy

## Two-stage prompting

The assistant deliberately splits "decide which tool to call" from
"write the final answer" into two separate LLM calls:

1. **Tool-selection prompt** (`run_travel_assistant`, STEP 4 in
   `app/orchestrator.py`) — only sees the question and the subset of MCP
   tools that intent-detection judged relevant. It is instructed to:
   - call `get_weather` only for current/forecast weather questions,
   - call `convert_currency` only for currency/budget questions,
   - never call a tool that isn't needed, and never call the same tool twice.
2. **Final grounding prompt** (`build_final_prompt`) — has **no tools bound**,
   so it cannot start another tool-call loop. It only sees:
   - the retrieved knowledge-base context,
   - any MCP tool results, rendered as plain-text summaries
     (`build_weather_summary` / `build_currency_summary`) rather than raw
     JSON, so the model doesn't have to parse structure and can't quote
     fields that don't exist,
   - a plain-text transcript of prior conversation turns,
   - the current question.

This separation keeps tool selection simple and bounded (`MAX_TOOL_CALLS = 2`)
while keeping the answer-writing prompt focused purely on grounding
discipline instead of tool semantics.

## Grounding rules (final prompt)

The final prompt encodes the assignment's prompt-engineering requirements
directly as numbered rules:

- **Closed world** — knowledge base = only source of destination facts; MCP
  data = only source of current weather/currency. No pretrained knowledge.
- **Exact-name matching** — an attraction/neighbourhood/activity may only be
  mentioned if its exact name appears in the retrieved context.
- **No invented details** — opening hours, prices, travel times, events,
  restaurants, hotels, etc. must come from the supplied context, never be
  guessed.
- **Weather rules** — only report the numeric fields actually present in the
  MCP payload; never translate a weather code into a descriptive condition
  that wasn't explicitly supplied.
- **Weather-aware planning** — combine KB-supported planning advice (start
  early, take breaks, use Cloud Forest/Flower Dome as indoor alternatives,
  etc.) with the live forecast, without inventing new advice.
- **Facts vs. recommendations vs. live data** — three kinds of statement must
  stay visibly distinct in the answer: plain sentences for stable
  knowledge-base facts, a `"Live update:"` prefix for anything drawn from
  the weather/currency MCP summaries, and a `"Recommendation:"` prefix for
  suggestions the model itself generates. A recommendation must not
  introduce a new destination fact.
- **Insufficient information** — if neither the KB nor MCP data answers the
  question, respond with a fixed fallback sentence instead of guessing.
- **Forecast-window honesty** — the weather summary explicitly tells the
  model it only covers today + 3 days, so it doesn't silently overclaim
  coverage of a further-out "next week" request.
- **Source priority** — for destination facts, KB > general knowledge; for
  current data, MCP > KB (a static KB sentence is never treated as "current").
- **Conversation context** — a dedicated "CONVERSATION HISTORY" section
  preserves user preferences (budget, dates, travel party, interests) stated
  earlier in the session, but is explicitly *not* treated as a source of
  destination/weather/currency facts — only live MCP/KB data are used for
  those.
- **No internal leakage** — the model is told not to mention RAG, MCP,
  embeddings, vector stores, or prompts to the end user.

## Section 5 requirement checklist

| Requirement | How it's satisfied |
|---|---|
| Use KB content for destination facts | Rule 1 ("Closed world") + Rule 2 ("Exact-name matching") restrict destination facts to the retrieved context |
| Use MCP responses for current information | Rule 4/9/10 route weather/currency exclusively through the MCP summaries, never the KB |
| Avoid presenting unsupported information as fact | Rule 3 ("No invented details") + "Final validation" checklist the model runs before answering |
| State when information is unavailable | Rule 8 fixed fallback sentence: *"The knowledge base does not provide enough information to confirm this."* |
| Produce clear, structured recommendations | Rule 6 (day-by-day itinerary structure) + Rule 7A recommendation prefix |
| Include source references where applicable | Handled outside the free-text prompt: `retrieve_context` returns the KB chunk's `source_title`/`source_url` metadata directly from the retriever (not model-generated), returned by the API and rendered as clickable chips in the UI — this avoids the model hallucinating a citation |
| Distinguish factual info from AI-generated suggestions | Rule 7A's three-way labelling ("plain sentence" / `"Live update:"` / `"Recommendation:"`) |
| Preserve relevant user preferences | Rule 9A + the `CONVERSATION HISTORY` transcript passed into every final prompt |

## Multi-turn context

`app/main.py` keeps a per-session list of `{role, content}` turns. Each
request passes the *prior* history into `run_travel_assistant(question,
history=...)`; after the answer is generated, both the user question and the
assistant answer are appended so the next turn can reference them. History is
capped (`MAX_HISTORY_TURNS = 10` exchanges) to bound prompt size.

## Known limitation

`llama3.2:3b` is a small, locally-hosted model. With this length of grounding
prompt it does not always follow every rule perfectly — see
[sample-questions-and-responses.md](sample-questions-and-responses.md) for
real (unedited) examples, including cases where it under-uses supplied
weather data or leaks raw context formatting into the answer. A larger hosted
model (e.g. GPT-4o-mini, Claude Haiku) would follow the same prompts more
reliably; the prompts themselves are model-agnostic.
