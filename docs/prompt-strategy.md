# Prompt & Context Strategy

How the assistant decides what to say — and, just as importantly, what *not* to say.

## Two-stage prompting

1. **Tool-selection call** — only used for `convert_currency`, which needs an amount/from/to
   parsed from free text. `get_weather` takes no arguments, so it's called directly once intent
   detection flags it, skipping this call entirely.
2. **Final grounding call** — **no tools bound**. Receives KB context + MCP results (as
   plain-text summaries, not raw JSON) + conversation history + the question.

Skipping the tool-selection call whenever it isn't needed (weather-only questions) roughly halves
response time, since local CPU inference is the dominant cost per turn. The final prompt's
grounding rules are also kept as concise as possible while preserving every rule, to reduce
prefill time on every request.

## Grounding rules (final prompt)

| Rule | What it means |
|---|---|
| 🔒 Closed world | Knowledge base = only source of destination facts; live data = only source of weather/currency |
| 🎯 Exact-name matching | Attractions/neighbourhoods must appear verbatim in the retrieved context |
| 🚫 No invention | Hours, prices, travel times, restaurants, events must come from the context |
| 🌦️ Weather honesty | Only numeric fields present in the payload are reported; forecast covers today + 3 days |
| 🏷️ Three-way labelling | Plain sentences = KB facts · `Live update:` = live data · `Recommendation:` = model suggestion |
| 🤷 Honest fallback | If neither source answers the question, it says so in plain language — never a technical excuse |
| 🤐 No leakage | Never mentions "RAG", "MCP", "knowledge base", "embeddings", or prompts to the user |

## Requirement checklist (assignment §5)

| Requirement | Satisfied by |
|---|---|
| KB for destination facts | Closed-world + exact-name rules |
| Live data for current information | Weather/currency routed only through MCP summaries |
| Avoid unsupported claims | No-invention rule + final self-check |
| State when info unavailable | Fixed, human-friendly fallback message |
| Structured recommendations | Day-by-day itinerary + `Recommendation:` prefix |
| Source references | `sources` array populated from retriever metadata (not model-generated) |
| Distinguish fact vs. suggestion | Three-way labelling |
| Preserve user preferences | `CONVERSATION HISTORY` block in every final prompt |

## Multi-turn context

A per-session `{role, content}` list lives in `app/main.py`, capped at 10 turns, and is passed
into every request so the assistant remembers what you've already told it.

## Known limitation

`llama3.2:3b` is a small local model; with a long, rule-dense prompt it occasionally under-uses
supplied live data or leaks raw context formatting. The prompts themselves are model-agnostic —
a larger hosted model (GPT-4o-mini, Claude Haiku) follows them more reliably. See
[sample-questions-and-responses.md](sample-questions-and-responses.md) for real examples.

