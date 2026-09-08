import asyncio
import json
from typing import Any

from app.llm import get_llm
from app.mcp.client import convert_currency, get_weather
from app.mcp.tool_definitions import get_mcp_tools
from app.rag.service import retrieve_context


# ============================================================
# CONFIGURATION
# ============================================================

MAX_TOOL_CALLS = 2

WEATHER_TOOL = "get_weather"
CURRENCY_TOOL = "convert_currency"


# ============================================================
# MCP TOOL EXECUTION
# ============================================================

async def execute_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
):
    """
    Execute an MCP tool selected by the AI.
    """

    if tool_name == WEATHER_TOOL:
        return await get_weather()

    if tool_name == CURRENCY_TOOL:
        return await convert_currency(
            amount=float(arguments["amount"]),
            from_currency=arguments["from_currency"],
            to_currency=arguments["to_currency"],
        )

    raise ValueError(
        f"Unknown MCP tool: {tool_name}"
    )


# ============================================================
# MCP RESULT EXTRACTION
# ============================================================

def extract_mcp_result(result):
    """
    Convert an MCP result into a normal Python object.
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

    return {
        "error": "No result returned by MCP tool."
    }


# ============================================================
# INTENT DETECTION
# ============================================================

def should_use_weather(question: str) -> bool:
    """
    Determine whether live weather information is relevant.
    """

    question_lower = question.lower()

    weather_keywords = [
        "weather",
        "rain",
        "raining",
        "temperature",
        "forecast",
        "humidity",
        "humid",
        "hot",
        "cold",
        "sunny",
        "cloudy",
        "climate",
        "outdoor",
        "rainy",
        "weather-aware",
    ]

    return any(
        keyword in question_lower
        for keyword in weather_keywords
    )


def should_use_currency(question: str) -> bool:
    """
    Determine whether currency information is relevant.
    """

    question_lower = question.lower()

    currency_keywords = [
        "currency",
        "exchange rate",
        "exchange",
        "convert",
        "conversion",
        "money",
        "budget",
        "cost",
        "price",
        "inr",
        "sgd",
        "usd",
        "rupee",
        "rupees",
        "dollar",
    ]

    return any(
        keyword in question_lower
        for keyword in currency_keywords
    )


# ============================================================
# WEATHER SUMMARY
# ============================================================

def build_weather_summary(weather_result: Any) -> str:
    """
    Create a simple factual weather summary from MCP data.

    We deliberately do not translate weather codes into
    descriptive weather conditions unless explicitly supported.
    """

    if not isinstance(weather_result, dict):
        return str(weather_result)

    if "error" in weather_result:
        return (
            "Live weather information could not be retrieved."
        )

    current = weather_result.get(
        "current",
        {},
    )

    daily = weather_result.get(
        "daily",
        {},
    )

    lines = []

    if current:

        current_time = current.get(
            "time"
        )

        temperature = current.get(
            "temperature_2m"
        )

        apparent_temperature = current.get(
            "apparent_temperature"
        )

        humidity = current.get(
            "relative_humidity_2m"
        )

        precipitation = current.get(
            "precipitation"
        )

        rain = current.get(
            "rain"
        )

        wind = current.get(
            "wind_speed_10m"
        )

        if current_time is not None:
            lines.append(
                f"Current observation time: {current_time}"
            )

        if temperature is not None:
            lines.append(
                f"Current temperature: {temperature}°C"
            )

        if apparent_temperature is not None:
            lines.append(
                f"Apparent temperature: "
                f"{apparent_temperature}°C"
            )

        if humidity is not None:
            lines.append(
                f"Relative humidity: {humidity}%"
            )

        if precipitation is not None:
            lines.append(
                f"Current precipitation: "
                f"{precipitation} mm"
            )

        if rain is not None:
            lines.append(
                f"Current rain: {rain} mm"
            )

        if wind is not None:
            lines.append(
                f"Wind speed: {wind} km/h"
            )

    daily_dates = daily.get(
        "time",
        [],
    )

    daily_max = daily.get(
        "temperature_2m_max",
        [],
    )

    daily_min = daily.get(
        "temperature_2m_min",
        [],
    )

    daily_precipitation = daily.get(
        "precipitation_sum",
        [],
    )

    daily_rain = daily.get(
        "rain_sum",
        [],
    )

    if daily_dates:

        lines.append(
            "\n3-day forecast:"
        )

        for index, date in enumerate(
            daily_dates
        ):

            parts = [
                f"- {date}"
            ]

            if index < len(daily_min):
                parts.append(
                    f"min {daily_min[index]}°C"
                )

            if index < len(daily_max):
                parts.append(
                    f"max {daily_max[index]}°C"
                )

            if index < len(daily_precipitation):
                parts.append(
                    f"precipitation "
                    f"{daily_precipitation[index]} mm"
                )

            if index < len(daily_rain):
                parts.append(
                    f"rain "
                    f"{daily_rain[index]} mm"
                )

            lines.append(
                ", ".join(parts)
            )

    return "\n".join(lines)


# ============================================================
# FINAL GROUNDED PROMPT
# ============================================================

def build_history_transcript(
    history: list[dict[str, str]] | None,
) -> str:
    """
    Render prior conversation turns as a plain transcript.
    """

    if not history:
        return "(no prior conversation)"

    lines = []

    for turn in history:

        role = turn.get("role", "user")
        content = turn.get("content", "")

        speaker = "User" if role == "user" else "Assistant"

        lines.append(f"{speaker}: {content}")

    return "\n".join(lines)


def build_final_prompt(
    question: str,
    context: str,
    mcp_results: dict[str, Any],
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    Build the final answer prompt.

    The final LLM receives no tools.
    Therefore it cannot create another MCP loop.
    """

    history_transcript = build_history_transcript(history)

    weather_summary = ""

    if WEATHER_TOOL in mcp_results:

        weather_summary = build_weather_summary(
            mcp_results[WEATHER_TOOL]
        )

    currency_result = ""

    if CURRENCY_TOOL in mcp_results:

        currency_result = json.dumps(
            mcp_results[CURRENCY_TOOL],
            indent=2,
            default=str,
        )

    return f"""
You are a Singapore travel planning assistant.

Your job is to answer the user's question using ONLY
the supplied knowledge base and supplied live MCP data.

Do NOT use general knowledge or pretrained knowledge
to add information.

==================================================
CONVERSATION HISTORY (earlier turns, oldest first)
==================================================

{history_transcript}

==================================================
USER QUESTION (current turn)
==================================================

{question}

==================================================
KNOWLEDGE BASE
==================================================

{context}

==================================================
LIVE WEATHER DATA
==================================================

{weather_summary}

==================================================
LIVE CURRENCY DATA
==================================================

{currency_result}

==================================================
GROUNDING RULES
==================================================

RULE 1 - CLOSED WORLD

The knowledge base is the ONLY source for Singapore
destination information.

The MCP data is the ONLY source for current weather
and currency information.

Do not use any information that is not contained
in these supplied sources.

--------------------------------------------------
RULE 2 - EXACT DESTINATION INFORMATION
--------------------------------------------------

You may use a destination, attraction, activity,
neighbourhood, food experience, transportation
method, or facility ONLY when it appears in the
knowledge base.

The exact name must be supported by the context.

For example:

If the context contains:

"Marina Bay Sands"

then you may mention Marina Bay Sands.

If the context contains:

"Singapore Flyer"

then you may mention Singapore Flyer.

However, if the context does NOT contain:

"Buddha Tooth Relic Temple"

you must NOT mention it.

Do not add famous Singapore attractions from
your own knowledge.

--------------------------------------------------
RULE 3 - NO INVENTED DETAILS
--------------------------------------------------

Do NOT invent:

- opening hours
- ticket prices
- costs
- travel times
- distances
- restaurant names
- hotel names
- events
- shows
- light shows
- attraction facilities
- historical claims
- architectural claims
- transportation prices
- exact routes
- exact MRT stations
- landmarks
- activities

unless the information is explicitly present
in the knowledge base.

--------------------------------------------------
RULE 4 - WEATHER
--------------------------------------------------

Use ONLY the supplied live weather data.

You may report numeric weather information such as:

- temperature
- apparent temperature
- humidity
- precipitation
- rain
- wind speed
- daily minimum temperature
- daily maximum temperature
- daily precipitation
- daily rain

Do not invent descriptive weather conditions.

Do not convert a weather code into words unless
the supplied information explicitly provides the
meaning of that code.

For example, do NOT say:

"partly cloudy"

just because a weather code exists.

--------------------------------------------------
RULE 5 - WEATHER-AWARE PLANNING
--------------------------------------------------

When the user requests a weather-aware itinerary:

Use the knowledge base to identify suitable
activities.

Use the live weather data to influence the
recommendation.

The knowledge base explicitly supports:

- starting outdoor sightseeing earlier
- taking breaks
- drinking water
- using shade where available
- combining outdoor and indoor attractions
- avoiding overly packed schedules
- using Cloud Forest and Flower Dome as indoor
  alternatives
- rearranging outdoor activities when rain occurs

Use these recommendations only when appropriate.

Do NOT invent additional weather advice.

--------------------------------------------------
RULE 6 - THREE DAY ITINERARY
--------------------------------------------------

For a 3-day Singapore itinerary, prefer the
three-day structure from the knowledge base.

DAY 1:
Marina Bay and Gardens

DAY 2:
Heritage and Food

DAY 3:
Nature and Leisure

Supported examples include:

Day 1:
- Marina Bay
- Gardens by the Bay
- Marina Bay Sands
- Singapore Flyer
- Esplanade area
- Singapore River
- Cloud Forest
- Flower Dome

Day 2:
- Chinatown
- Little India
- Kampong Glam
- Bugis
- food experiences

Day 3:
- Sentosa
- Singapore Botanic Gardens
- Mandai wildlife attractions
- East Coast
- Southern Ridges

Only use an item if it is supported by the
knowledge base context supplied above.

--------------------------------------------------
RULE 7 - FACTS VS RECOMMENDATIONS
--------------------------------------------------

Separate facts from recommendations.

FACTS are information directly supported by
the knowledge base or MCP.

RECOMMENDATIONS are suggestions about how to
organize supported activities.

Use:

"Recommendation:"

when giving a planning suggestion.

A recommendation must not introduce a new
destination fact.

--------------------------------------------------
RULE 8 - INSUFFICIENT INFORMATION
--------------------------------------------------

If information requested by the user is not
present in the knowledge base or MCP data, say:

"The knowledge base does not provide enough
information to confirm this."

Do not guess.

--------------------------------------------------
RULE 9A - CONVERSATION CONTEXT
--------------------------------------------------

Use the CONVERSATION HISTORY only to preserve user
preferences already stated (such as budget, dates,
travel party, or interests) and to keep answers
consistent with earlier turns.

The conversation history is NOT a source of
destination facts, weather, or currency data.

--------------------------------------------------
RULE 9 - CURRENT INFORMATION
--------------------------------------------------

Current weather must come from MCP.

Current exchange rates must come from MCP.

Never claim a static knowledge-base statement
is current.

If MCP data is available, use it.

Do NOT say that weather information is unavailable
when live weather data has been supplied.

--------------------------------------------------
RULE 10 - SOURCE PRIORITY
--------------------------------------------------

For destination facts:

KNOWLEDGE BASE > GENERAL KNOWLEDGE

For current weather:

MCP > KNOWLEDGE BASE

For current currency:

MCP > KNOWLEDGE BASE

Never override live MCP data with static knowledge.

--------------------------------------------------
FINAL VALIDATION
--------------------------------------------------

Before producing your answer:

1. Check every destination name against the
   knowledge base.

2. Check every destination fact against the
   knowledge base.

3. Check every weather number against MCP.

4. Check every currency value against MCP.

5. Remove unsupported claims.

6. Do not add famous attractions just because
   they are commonly associated with Singapore.

7. Do not invent prices or opening hours.

8. Do not invent events or shows.

9. Do not invent restaurants or hotels.

10. Do not mention information outside the supplied
    knowledge base and MCP data.

The goal is a grounded answer, not a maximally
detailed answer.

Do not mention RAG, MCP, embeddings, vector stores,
LLMs, prompts, or internal implementation details
to the user.
"""


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

async def run_travel_assistant(
    question: str,
    history: list[dict[str, str]] | None = None,
):

    print(
        "\n=================================================="
    )

    print(
        "AI TRAVEL PLANNING ASSISTANT"
    )

    print(
        "=================================================="
    )

    print(
        "\n===== USER QUESTION ====="
    )

    print(question)

    # ========================================================
    # STEP 1 - RAG
    # ========================================================

    print(
        "\n===== RAG RETRIEVAL ====="
    )

    context, sources = retrieve_context(
        question,
        k=4,
    )

    print(
        f"Retrieved context characters: "
        f"{len(context)}"
    )

    print(
        f"Sources retrieved: "
        f"{len(sources)}"
    )

    # ========================================================
    # STEP 2 - INTENT
    # ========================================================

    weather_required = should_use_weather(
        question
    )

    currency_required = should_use_currency(
        question
    )

    print(
        "\n===== TOOL REQUIREMENT ====="
    )

    print(
        f"Weather required: "
        f"{weather_required}"
    )

    print(
        f"Currency required: "
        f"{currency_required}"
    )

    # ========================================================
    # STEP 3 - PREPARE AVAILABLE TOOLS
    # ========================================================

    all_tools = get_mcp_tools()

    allowed_tool_names = set()

    if weather_required:

        allowed_tool_names.add(
            WEATHER_TOOL
        )

    if currency_required:

        allowed_tool_names.add(
            CURRENCY_TOOL
        )

    tools = [
        tool
        for tool in all_tools
        if tool.name in allowed_tool_names
    ]

    mcp_results = {}

    tools_used = []

    # ========================================================
    # STEP 4 - AI TOOL SELECTION
    # ========================================================

    if tools:

        print(
            "\n===== AI TOOL SELECTION ====="
        )

        llm = get_llm()

        tool_enabled_llm = llm.bind_tools(
            tools
        )

        selection_prompt = f"""
You are the MCP tool-selection component of a
Singapore travel assistant.

User question:

{question}

Available tools:

{", ".join(
    tool.name
    for tool in tools
)}

Rules:

- Use get_weather only when the user needs current
  or forecast weather information.

- Use convert_currency only when the user asks about
  currency, exchange rates, money conversion, budget,
  or currency-related cost information.

- Do not call unnecessary tools.

- Do not call the same tool more than once.

- Do not invent arguments.

- If no live information is required, do not call
  any tool.
"""

        try:

            response = (
                await tool_enabled_llm.ainvoke(
                    [
                        (
                            "system",
                            selection_prompt,
                        ),
                        (
                            "human",
                            question,
                        ),
                    ]
                )
            )

            print(
                "\n===== AI SELECTED MCP TOOLS ====="
            )

            if response.tool_calls:

                for tool_call in response.tool_calls:

                    print(
                        f"Tool: "
                        f"{tool_call['name']}"
                    )

                    print(
                        f"Arguments: "
                        f"{tool_call['args']}"
                    )

            else:

                print(
                    "No MCP tool selected."
                )

        except Exception as exc:

            print(
                "\n===== AI TOOL SELECTION ERROR ====="
            )

            print(str(exc))

            response = None

        # ====================================================
        # STEP 5 - CONTROLLED MCP EXECUTION
        # ====================================================

        if response and response.tool_calls:

            executed_tool_names = set()

            for tool_call in response.tool_calls:

                # --------------------------------------------
                # Maximum tool protection
                # --------------------------------------------

                if (
                    len(executed_tool_names)
                    >= MAX_TOOL_CALLS
                ):

                    print(
                        "\nMaximum MCP tool-call "
                        "limit reached."
                    )

                    break

                tool_name = tool_call[
                    "name"
                ]

                arguments = tool_call.get(
                    "args",
                    {},
                )

                # --------------------------------------------
                # Duplicate protection
                # --------------------------------------------

                if (
                    tool_name
                    in executed_tool_names
                ):

                    print(
                        f"\nSkipping duplicate "
                        f"tool: {tool_name}"
                    )

                    continue

                # --------------------------------------------
                # Allowed-tool protection
                # --------------------------------------------

                if (
                    tool_name
                    not in allowed_tool_names
                ):

                    print(
                        f"\nSkipping unexpected "
                        f"tool: {tool_name}"
                    )

                    continue

                executed_tool_names.add(
                    tool_name
                )

                print(
                    "\n===== MCP TOOL EXECUTION ====="
                )

                print(
                    f"Tool: {tool_name}"
                )

                print(
                    f"Arguments: {arguments}"
                )

                # --------------------------------------------
                # Execute MCP
                # --------------------------------------------

                try:

                    mcp_result = (
                        await execute_mcp_tool(
                            tool_name,
                            arguments,
                        )
                    )

                    tool_result = (
                        extract_mcp_result(
                            mcp_result
                        )
                    )

                    mcp_results[
                        tool_name
                    ] = tool_result

                    if (
                        tool_name
                        not in tools_used
                    ):

                        tools_used.append(
                            tool_name
                        )

                    print(
                        "\n===== MCP RESULT ====="
                    )

                    print(
                        json.dumps(
                            tool_result,
                            indent=2,
                            default=str,
                        )
                    )

                except Exception as exc:

                    print(
                        "\n===== MCP ERROR ====="
                    )

                    print(str(exc))

                    error_result = {
                        "error": (
                            "The requested live "
                            "travel service "
                            "could not be reached."
                        ),
                        "details": str(exc),
                    }

                    mcp_results[
                        tool_name
                    ] = error_result

    else:

        print(
            "\n===== MCP ====="
        )

        print(
            "No live MCP tool required."
        )

    # ========================================================
    # STEP 6 - FINAL GROUNDED LLM
    # ========================================================

    print(
        "\n===== FINAL GROUNDED RESPONSE ====="
    )

    final_prompt = build_final_prompt(
        question=question,
        context=context,
        mcp_results=mcp_results,
        history=history,
    )

    # IMPORTANT:
    #
    # No MCP tools are bound here.
    #
    # This is intentionally a normal LLM call.
    # It prevents another tool-call loop.

    final_llm = get_llm()

    try:

        final_response = (
            await final_llm.ainvoke(
                [
                    (
                        "system",
                        final_prompt,
                    ),
                    (
                        "human",
                        question,
                    ),
                ]
            )
        )

        answer = final_response.content

    except Exception as exc:

        print(
            "\n===== FINAL LLM ERROR ====="
        )

        print(str(exc))

        answer = (
            "I’m sorry, but I was unable to "
            "generate the travel recommendation "
            "at this time."
        )

    print(answer)

    # ========================================================
    # STEP 7 - STRUCTURED RESULT
    # ========================================================

    return {
        "answer": answer,
        "sources": sources,
        "tools_used": tools_used,
        "mcp_results": mcp_results,
    }


# ============================================================
# DEMO
# ============================================================

async def main():

    question = (
        "Plan a 3-day trip to Singapore covering "
        "the main attractions and consider the "
        "current weather."
    )

    result = await run_travel_assistant(
        question
    )

    # ========================================================
    # SOURCES
    # ========================================================

    print(
        "\n=================================================="
    )

    print(
        "SOURCES"
    )

    print(
        "=================================================="
    )

    for source in result["sources"]:

        print(
            f"- {source['title']}"
        )

        print(
            f"  {source['url']}"
        )

    # ========================================================
    # TOOLS USED
    # ========================================================

    print(
        "\n=================================================="
    )

    print(
        "TOOLS USED"
    )

    print(
        "=================================================="
    )

    if result["tools_used"]:

        for tool in result["tools_used"]:

            print(
                f"- {tool}"
            )

    else:

        print(
            "- None"
        )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())