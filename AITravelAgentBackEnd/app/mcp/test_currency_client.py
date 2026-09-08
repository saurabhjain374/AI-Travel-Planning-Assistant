import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["app/mcp/currency_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            print("\n===== MCP CONNECTION SUCCESSFUL =====")

            tools = await session.list_tools()

            print("\n===== AVAILABLE MCP TOOLS =====")

            for tool in tools.tools:
                print(f"- {tool.name}")
                print(f"  Description: {tool.description}")

            print("\n===== CALLING CURRENCY TOOL =====")

            result = await session.call_tool(
                "convert_currency",
                arguments={
                    "amount": 10000,
                    "from_currency": "INR",
                    "to_currency": "SGD",
                },
            )

            print("\n===== CURRENCY RESULT =====")

            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)


if __name__ == "__main__":
    asyncio.run(main())