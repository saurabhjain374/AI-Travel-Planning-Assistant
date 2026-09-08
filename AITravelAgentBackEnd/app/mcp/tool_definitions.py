from langchain_core.tools import StructuredTool


def get_weather_tool():
    """
    Tool definition for retrieving live Singapore weather.
    """

    async def get_weather():
        from app.mcp.client import get_weather

        result = await get_weather()

        for content in result.content:
            if hasattr(content, "text"):
                return content.text

        return "Weather information could not be retrieved."

    return StructuredTool.from_function(
        coroutine=get_weather,
        name="get_weather",
        description=(
            "Get the current weather and 3-day weather forecast for Singapore. "
            "Use this tool whenever the user asks about current or forecast "
            "weather, rain, temperature, humidity, or weather conditions."
        ),
    )


def get_currency_tool():
    """
    Tool definition for retrieving live currency conversion.
    """

    async def convert_currency(
        amount: float,
        from_currency: str,
        to_currency: str,
    ):
        from app.mcp.client import convert_currency

        result = await convert_currency(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
        )

        for content in result.content:
            if hasattr(content, "text"):
                return content.text

        return "Currency information could not be retrieved."

    return StructuredTool.from_function(
        coroutine=convert_currency,
        name="convert_currency",
        description=(
            "Convert money between currencies using the latest available "
            "exchange rate. Use this tool whenever the user asks about "
            "currency conversion, exchange rates, or travel money."
        ),
    )


def get_mcp_tools():
    """
    Return all MCP-backed tools available to the AI assistant.
    """

    return [
        get_weather_tool(),
        get_currency_tool(),
    ]