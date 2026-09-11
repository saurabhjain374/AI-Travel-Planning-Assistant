# MCP Tools

Both MCP servers and the client are **custom-built** using the `mcp` Python SDK. No pre-built MCP server packages are used.

| Tool | Server | External API | Purpose |
|---|---|---|---|
| `get_weather` | `app/mcp/weather_server.py` | Open-Meteo | Current + 3-day forecast for Singapore |
| `convert_currency` | `app/mcp/currency_server.py` | open.er-api.com | Convert an amount between two currencies |

## Wiring

1. Servers use `mcp.server.MCPServer` + `@mcp.tool()`; call external APIs with `httpx`; return a dict or `{"error": ...}`.
2. Client (`app/mcp/client.py`) spawns a server as a stdio subprocess (`StdioServerParameters` + `stdio_client`) and calls the tool via `ClientSession`.
3. Tools are wrapped as LangChain `StructuredTool`s (`app/mcp/tool_definitions.py`) and bound via `llm.bind_tools([...])`.
4. Orchestrator (`app/orchestrator.py`) uses keyword intent gating (`should_use_weather` / `should_use_currency`) to decide which tools are needed. `get_weather` takes no arguments and is called directly (no LLM involved); `convert_currency` still goes through an LLM call bound only to that tool, since its arguments must be parsed from the question.

## Failure handling

Any exception is caught and passed to the final prompt as `{"error": ...}`. The prompt instructs the model to say *"live weather/currency information could not be retrieved"* rather than invent a value.

## Tests

- `tests/test_tool_calling.py` — verifies correct tool selection.
- `app/mcp/test_weather_client.py`, `test_currency_client.py` — exercise servers via the stdio client.
