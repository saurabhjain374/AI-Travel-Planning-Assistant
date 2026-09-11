import asyncio
import json

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage

from app.llm import get_llm
from app.mcp.client import convert_currency, get_weather
from app.mcp.tool_definitions import get_mcp_tools


async def execute_tool(tool_name: str, arguments: dict):
    """
    Execute the MCP tool selected by the LLM.
    """

    if tool_name == "get_weather":
        return await get_weather()

    if tool_name == "convert_currency":
        return await convert_currency(
            amount=float(arguments["amount"]),
            from_currency=arguments["from_currency"],
            to_currency=arguments["to_currency"],
        )

    raise ValueError(f"Unknown tool: {tool_name}")


def extract_tool_result(result):
    """
    Extract useful text/structured content from an MCP result.
    """

    if hasattr(result, "structured_content"):
        if result.structured_content:
            return result.structured_content

    if hasattr(result, "content"):
        for content in result.content:
            if hasattr(content, "text"):
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return content.text

    return "No result returned by the MCP tool."


async def run_agent(question: str):
    """
    Complete AI + MCP tool execution loop:

    1. Send user question to LLM
    2. LLM selects a tool
    3. Execute selected MCP tool
    4. Send tool result back to LLM
    5. LLM generates final response
    """

    llm = get_llm()
    tools = get_mcp_tools()

    tool_enabled_llm = llm.bind_tools(tools)

    messages: list[BaseMessage] = [
        SystemMessage(
            content="""
You are an AI travel assistant specializing in Singapore.

Use MCP tools when the user asks for current weather,
weather forecasts, currency conversion, or exchange rates.

Do not invent live weather or currency information.

After receiving a tool result, use that result to answer
the user's question clearly and concisely.
"""
        ),
        HumanMessage(content=question),
    ]

    # ---------------------------------------------------------
    # STEP 1: Ask LLM to decide whether a tool is required
    # ---------------------------------------------------------

    response = await tool_enabled_llm.ainvoke(messages)

    print("\n===== INITIAL LLM RESPONSE =====")
    print(response)

    # ---------------------------------------------------------
    # STEP 2: Check whether LLM selected a tool
    # ---------------------------------------------------------

    if not response.tool_calls:
        return response.content

    messages.append(response)

    # ---------------------------------------------------------
    # STEP 3: Execute selected MCP tool(s)
    # ---------------------------------------------------------

    for tool_call in response.tool_calls:

        tool_name = tool_call["name"]
        arguments = tool_call["args"]

        print("\n===== AI SELECTED TOOL =====")
        print(f"Tool: {tool_name}")
        print(f"Arguments: {arguments}")

        try:
            mcp_result = await execute_tool(
                tool_name,
                arguments,
            )

            tool_result = extract_tool_result(mcp_result)

        except Exception as exc:
            tool_result = {
                "error": "The requested MCP tool could not be executed.",
                "details": str(exc),
            }

        print("\n===== MCP TOOL RESULT =====")
        print(tool_result)

        # -----------------------------------------------------
        # STEP 4: Send MCP result back to LLM
        # -----------------------------------------------------

        messages.append(
            ToolMessage(
                content=json.dumps(
                    tool_result,
                    default=str,
                ),
                tool_call_id=tool_call["id"],
            )
        )

    # ---------------------------------------------------------
    # STEP 5: Ask LLM for final natural-language answer
    # ---------------------------------------------------------

    final_response = await tool_enabled_llm.ainvoke(messages)

    print("\n===== FINAL AI RESPONSE =====")
    print(final_response.content)

    return final_response.content


async def main():

    question = "How much is 10000 Indian Rupees in Singapore Dollars?"

    await run_agent(question)


if __name__ == "__main__":
    asyncio.run(main())