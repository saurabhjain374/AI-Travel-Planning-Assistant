import asyncio
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]


WEATHER_SERVER = PROJECT_ROOT / "app" / "mcp" / "weather_server.py"
CURRENCY_SERVER = PROJECT_ROOT / "app" / "mcp" / "currency_server.py"


async def call_mcp_tool(
    server_path: Path,
    tool_name: str,
    arguments: dict[str, Any],
) -> Any:
    """
    Start an MCP server, connect to it, and call a specific tool.
    """

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            tools = await session.list_tools()

            available_tools = {
                tool.name for tool in tools.tools
            }

            if tool_name not in available_tools:
                raise ValueError(
                    f"MCP tool '{tool_name}' is not available."
                )

            result = await session.call_tool(
                tool_name,
                arguments=arguments,
            )

            return result


async def get_weather():
    """
    Retrieve weather through the Weather MCP server.
    """

    return await call_mcp_tool(
        server_path=WEATHER_SERVER,
        tool_name="get_weather",
        arguments={},
    )


async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
):
    """
    Retrieve currency conversion through the Currency MCP server.
    """

    return await call_mcp_tool(
        server_path=CURRENCY_SERVER,
        tool_name="convert_currency",
        arguments={
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency,
        },
    )


async def main():
    print("\n===== WEATHER MCP =====")

    weather_result = await get_weather()

    for content in weather_result.content:
        if hasattr(content, "text"):
            print(content.text)

    print("\n===== CURRENCY MCP =====")

    currency_result = await convert_currency(
        amount=10000,
        from_currency="INR",
        to_currency="SGD",
    )

    for content in currency_result.content:
        if hasattr(content, "text"):
            print(content.text)


if __name__ == "__main__":
    asyncio.run(main())