# Prompt & Context Strategy

## Two-stage prompting

1. **Tool-selection call** — sees only the question and the intent-gated MCP tools. Instructed to call each tool at most once, and only when needed.
2. **Final grounding call** — **no tools bound**. Receives KB context + MCP results (as plain-text summaries, not raw JSON) + conversation history + question.

This bounds the tool loop (`MAX_TOOL_CALLS = 2`) and keeps the answer prompt focused purely on grounding.

## Grounding rules (final prompt)

- **Closed world** — KB = only source of destination facts; MCP = only source of live weather/currency.
- **Exact-name matching** — attractions/neighbourhoods must appear verbatim in retrieved context.
- **No invention** — hours, prices, travel times, restaurants, events must come from the context.
- **Weather honesty** — only report numeric fields present in the payload; forecast covers today + 3 days only.
- **Three-way labelling** — plain sentences = KB facts; `"Live update:"` = MCP data; `"Recommendation:"` = model suggestion.
- **Fallback** — if neither KB nor MCP answers the question: *"The knowledge base does not provide enough information to confirm this."*
- **No leakage** — never mention RAG, MCP, embeddings, or prompts to the user.

## Requirement checklist (assignment §5)

| Requirement | Satisfied by |
|---|---|
| KB for destination facts | Closed-world + exact-name rules |
| MCP for current information | Weather/currency routed only through MCP summaries |
| Avoid unsupported claims | No-invention rule + final self-check |
| State when info unavailable | Fixed fallback sentence |
| Structured recommendations | Day-by-day itinerary + `Recommendation:` prefix |
| Source references | `sources` array populated from retriever metadata (not model-generated) |
| Distinguish fact vs. suggestion | Three-way labelling |
| Preserve user preferences | `CONVERSATION HISTORY` block in every final prompt |

## Multi-turn context

Per-session `{role, content}` list in `app/main.py`, capped at 10 turns, passed into every request.

## Known limitation

`llama3.2:3b` is a small local model; with a long rule-dense prompt it occasionally under-uses supplied MCP data or leaks raw context formatting. Prompts are model-agnostic — a larger hosted model (GPT-4o-mini, Claude Haiku) follows them more reliably. See `sample-questions-and-responses.md` for real examples.
