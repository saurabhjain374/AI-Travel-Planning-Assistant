import asyncio

from app.llm import get_llm
from app.mcp.tool_definitions import get_mcp_tools


def test_llm_selects_weather_tool_for_weather_question():
    async def ask():
        llm = get_llm().bind_tools(get_mcp_tools())

        return await llm.ainvoke(
            [
                (
                    "system",
                    "You are a travel assistant. "
                    "Use the weather tool when asked about current weather.",
                ),
                (
                    "human",
                    "What is the current weather in Singapore?",
                ),
            ]
        )

    response = asyncio.run(ask())

    assert response.tool_calls
    assert response.tool_calls[0]["name"] == "get_weather"