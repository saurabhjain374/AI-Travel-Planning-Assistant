from typing import Any

import httpx
from mcp.server import MCPServer


mcp = MCPServer(
    "Singapore Weather MCP Server",
    instructions="Provides current and forecast weather information for Singapore.",
)


SINGAPORE_LATITUDE = 1.3521
SINGAPORE_LONGITUDE = 103.8198
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"


@mcp.tool()
async def get_weather() -> dict[str, Any]:
    """
    Get current and 3-day weather forecast for Singapore.

    Returns temperature, precipitation, rain, weather code,
    humidity, and wind information.
    """

    params = {
        "latitude": SINGAPORE_LATITUDE,
        "longitude": SINGAPORE_LONGITUDE,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum,"
            "rain_sum"
        ),
        "forecast_days": 3,
        "timezone": "Asia/Singapore",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                WEATHER_API_URL,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

        return {
            "location": "Singapore",
            "timezone": data.get("timezone"),
            "current": data.get("current"),
            "daily": data.get("daily"),
        }

    except httpx.HTTPError as exc:
        return {
            "error": "Weather service is currently unavailable.",
            "details": str(exc),
        }

    except Exception as exc:
        return {
            "error": "Unexpected error while retrieving weather.",
            "details": str(exc),
        }


if __name__ == "__main__":
    mcp.run()