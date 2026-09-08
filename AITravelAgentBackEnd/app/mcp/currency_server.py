from typing import Any

import httpx
from mcp.server import MCPServer


mcp = MCPServer(
    "Currency MCP Server",
    instructions="Provides current currency exchange rates and conversions.",
)


CURRENCY_API_URL = "https://open.er-api.com/v6/latest"


@mcp.tool()
async def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> dict[str, Any]:
    """
    Convert an amount from one currency to another
    using the latest available exchange rate.
    """

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if amount <= 0:
        return {
            "error": "Amount must be greater than zero."
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{CURRENCY_API_URL}/{from_currency}"
            )

            response.raise_for_status()

            data = response.json()

        if data.get("result") != "success":
            return {
                "error": "Currency service returned an unsuccessful response."
            }

        rates = data.get("rates", {})

        if to_currency not in rates:
            return {
                "error": f"Currency '{to_currency}' is not available."
            }

        rate = rates[to_currency]
        converted_amount = amount * rate

        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
            "exchange_rate": rate,
            "converted_amount": round(converted_amount, 2),
            "last_updated": data.get("time_last_update_utc"),
        }

    except httpx.HTTPError as exc:
        return {
            "error": "Currency service is currently unavailable.",
            "details": str(exc),
        }

    except Exception as exc:
        return {
            "error": "Unexpected error while retrieving currency information.",
            "details": str(exc),
        }


if __name__ == "__main__":
    mcp.run()