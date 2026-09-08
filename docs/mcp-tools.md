# MCP Tools

Two MCP servers provide current, time-sensitive data. Neither is used for
destination questions already covered by the knowledge base.

| Tool | Server | Data source | Purpose |
|---|---|---|---|
| `get_weather` | [app/mcp/weather_server.py](../AITravelAgentBackEnd/app/mcp/weather_server.py) | [Open-Meteo](https://open-meteo.com/) (`api.open-meteo.com`) | Current conditions + 3-day forecast for Singapore (lat/long fixed) |
| `convert_currency` | [app/mcp/currency_server.py](../AITravelAgentBackEnd/app/mcp/currency_server.py) | [open.er-api.com](https://www.exchangerate-api.com/) | Convert an amount between two currencies using the latest rate |

## Wiring

1. **MCP servers** (`weather_server.py`, `currency_server.py`) are standalone
   scripts built with `mcp.server.MCPServer` and `@mcp.tool()` decorators.
   Each calls its external HTTP API with `httpx` and returns a structured
   dict (or an `{"error": ...}` dict on failure — never a fabricated value).
2. **Client** ([app/mcp/client.py](../AITravelAgentBackEnd/app/mcp/client.py)) launches a server
   as a subprocess over stdio (`StdioServerParameters` + `stdio_client`),
   opens an `mcp.ClientSession`, and calls the named tool with arguments.
3. **LangChain tool definitions**
   ([app/mcp/tool_definitions.py](../AITravelAgentBackEnd/app/mcp/tool_definitions.py)) wrap each
   MCP call as a `StructuredTool`, so the LLM can bind to them via
   `llm.bind_tools([...])` and decide when/how to call them.
4. **Selection & execution** happens in
   [app/orchestrator.py](../AITravelAgentBackEnd/app/orchestrator.py):
   - `should_use_weather()` / `should_use_currency()` — keyword-based intent
     gating so MCP tools are only offered to the LLM when plausibly relevant.
   - Only the allowed tool(s) are bound to the LLM for the tool-selection
     call, so it cannot invoke an irrelevant tool.
   - `execute_mcp_tool()` runs the selected tool; results are normalised by
     `extract_mcp_result()` into plain Python objects.
   - A `MAX_TOOL_CALLS` limit and duplicate-tool guard prevent runaway loops.
   - Any exception during execution is caught and turned into a structured
     `{"error": ..., "details": ...}` result rather than a fabricated answer.

## Failure handling

If a tool raises (network error, unavailable service, bad arguments), the
orchestrator captures the exception and passes an explicit error object to
the final grounding prompt. The prompt instructs the model to state that
"live weather/currency information could not be retrieved" rather than
inventing a plausible-looking number.

## Testing

[tests/test_tool_calling.py](../AITravelAgentBackEnd/tests/test_tool_calling.py) asserts that the
LLM selects `get_weather` for a weather question when both tools are bound.
[app/mcp/test_currency_client.py](../AITravelAgentBackEnd/app/mcp/test_currency_client.py) and
[app/mcp/test_weather_client.py](../AITravelAgentBackEnd/app/mcp/test_weather_client.py) exercise
the MCP servers directly through the stdio client.
