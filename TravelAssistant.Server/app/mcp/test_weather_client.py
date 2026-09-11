import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["app/mcp/weather_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # Initialize MCP connection
            await session.initialize()

            print("\n===== MCP CONNECTION SUCCESSFUL =====")

            # Discover available tools
            tools = await session.list_tools()

            print("\n===== AVAILABLE MCP TOOLS =====")

            for tool in tools.tools:
                print(f"- {tool.name}")
                print(f"  Description: {tool.description}")

            # Call weather tool
            print("\n===== CALLING WEATHER TOOL =====")

            result = await session.call_tool(
                "get_weather",
                arguments={},
            )

            print("\n===== WEATHER RESULT =====")

            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)


if __name__ == "__main__":
    asyncio.run(main())