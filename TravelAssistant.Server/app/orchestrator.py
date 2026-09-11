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

def _levenshtein_distance(a: str, b: str) -> int:
    """
    Edit distance between two strings (single-character
    insert/delete/substitute cost).
    """

    if a == b:
        return 0

    previous_row = list(range(len(b) + 1))

    for i, char_a in enumerate(a, start=1):

        current_row = [i]

        for j, char_b in enumerate(b, start=1):

            insert_cost = current_row[j - 1] + 1
            delete_cost = previous_row[j] + 1
            substitute_cost = previous_row[j - 1] + (
                char_a != char_b
            )

            current_row.append(
                min(insert_cost, delete_cost, substitute_cost)
            )

        previous_row = current_row

    return previous_row[-1]


def contains_fuzzy_keyword(
    text: str,
    keywords: list[str],
    max_distance: int = 1,
) -> bool:
    """
    Check whether any word in `text` is a near-typo (within
    `max_distance` edits) of one of `keywords`.

    Used to catch misspellings such as "temprature" without
    false-positive matching unrelated words such as "temple".
    """

    words = "".join(
        char if char.isalnum() else " "
        for char in text
    ).split()

    for word in words:

        for keyword in keywords:

            if abs(len(word) - len(keyword)) > max_distance:
                continue

            if _levenshtein_distance(word, keyword) <= max_distance:
                return True

    return False


def should_use_weather(question: str) -> bool:
    """
    Determine whether live weather information is relevant.
    """

    question_lower = question.lower()

    weather_keywords = [
        "weather",
        "weath",
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

    if any(
        keyword in question_lower
        for keyword in weather_keywords
    ):
        return True

    # Catch common misspellings (e.g. "temprature") without
    # false-positive matching unrelated words like "temple".
    return contains_fuzzy_keyword(
        question_lower,
        ["weather", "temperature", "forecast", "humidity", "climate"],
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

    if any(
        keyword in question_lower
        for keyword in currency_keywords
    ):
        return True

    return contains_fuzzy_keyword(
        question_lower,
        ["currency", "exchange", "convert", "budget"],
    )


def mentions_destination_topic(question: str) -> bool:
    """
    Determine whether the question is actually asking about
    destination knowledge (attractions, neighbourhoods, food,
    transportation, itineraries, activities, etc.).

    Used only to decide whether knowledge-base sources should be
    shown alongside the answer - a pure "what's the weather" or
    "convert X to Y" question doesn't need KB sources attached,
    since the answer wasn't actually grounded in the knowledge base.
    """

    question_lower = question.lower()

    destination_keywords = [
        "attraction",
        "neighbourhood",
        "neighborhood",
        "itinerary",
        "visit",
        "things to do",
        "activity",
        "activities",
        "food",
        "restaurant",
        "hawker",
        "transport",
        "mrt",
        "bus",
        "taxi",
        "culture",
        "cultural",
        "museum",
        "temple",
        "garden",
        "park",
        "shopping",
        "beach",
        "indoor",
        "outdoor",
        "family",
        "families",
        "children",
        "trip",
        "plan",
        "sightseeing",
        "tour",
        "place",
        "district",
    ]

    return any(
        keyword in question_lower
        for keyword in destination_keywords
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

        lines.append(
            "\nNote: this forecast only covers today plus the "
            "next 3 days. It does not cover a full week ahead. "
            "If the user asked about a date beyond this window "
            "(for example, 'next week'), use this forecast as the "
            "closest available guidance and state that only a "
            "3-day forecast is available."
        )

    return "\n".join(lines)


# ============================================================
# CURRENCY SUMMARY
# ============================================================

def build_currency_summary(currency_result: Any) -> str:
    """
    Create a simple factual currency summary from MCP data.
    """

    if not isinstance(currency_result, dict):
        return str(currency_result)

    if "error" in currency_result:
        return (
            "Live currency conversion could not be retrieved."
        )

    from_currency = currency_result.get("from_currency")
    to_currency = currency_result.get("to_currency")
    amount = currency_result.get("amount")
    exchange_rate = currency_result.get("exchange_rate")
    converted_amount = currency_result.get("converted_amount")
    last_updated = currency_result.get("last_updated")

    lines = []

    if amount is not None and from_currency and to_currency:
        lines.append(
            f"Current conversion: {amount} {from_currency} = "
            f"{converted_amount} {to_currency}"
        )

    if exchange_rate is not None and from_currency and to_currency:
        lines.append(
            f"Current exchange rate: 1 {from_currency} = "
            f"{exchange_rate} {to_currency}"
        )

    if last_updated is not None:
        lines.append(
            f"Rate last updated: {last_updated}"
        )

    if not lines:
        return "Live currency conversion could not be retrieved."

    return "\n".join(lines)


# ============================================================
# FINAL GROUNDED PROMPT
# ============================================================

def build_history_transcript(
    history: list[dict[str, str]] | None,
) -> str:
    """
    Render prior conversation turns as a plain transcript.

    Each turn is capped in length - full itinerary-length answers
    stored across several turns would otherwise bloat the prompt past
    the model's context window, which was silently truncating answers
    and causing the model to lose track of the current question.
    """

    if not history:
        return "(no prior conversation)"

    max_chars_per_turn = 500

    lines = []

    for turn in history:

        role = turn.get("role", "user")
        content = turn.get("content", "")

        if len(content) > max_chars_per_turn:
            content = content[:max_chars_per_turn].rstrip() + " [...]"

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

    # Retrieval already filters out chunks that aren't relevant enough
    # (see MAX_RELEVANT_DISTANCE in rag/service.py), so an empty context
    # here means nothing relevant was found - make that explicit instead
    # of showing a blank section, to make RULE 8 trigger reliably.
    context = context.strip() or (
        "No relevant knowledge base content was found for this question."
    )

    weather_summary = ""

    if WEATHER_TOOL in mcp_results:

        weather_summary = build_weather_summary(
            mcp_results[WEATHER_TOOL]
        )

    weather_data_available = bool(weather_summary)

    if not weather_data_available:
        weather_summary = (
            "No live weather data was retrieved for this request."
        )

    currency_result = ""

    if CURRENCY_TOOL in mcp_results:

        currency_result = build_currency_summary(
            mcp_results[CURRENCY_TOOL]
        )

    currency_data_available = bool(currency_result)

    if not currency_data_available:
        currency_result = (
            "No live currency data was retrieved for this request."
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
The knowledge base is the ONLY source for Singapore destination
information. MCP data is the ONLY source for current weather and
currency information. Do not use anything not contained in these
supplied sources.

RULE 2 - EXACT DESTINATION INFORMATION
Mention a destination, attraction, activity, neighbourhood, food
experience, transportation method, or facility ONLY if that exact
name appears in the knowledge base above (e.g. you may say "Marina
Bay Sands" or "Singapore Flyer" if present, but must NOT say
"Buddha Tooth Relic Temple" if it is not). Do not add famous
Singapore attractions from your own knowledge.

RULE 3 - NO INVENTED DETAILS
Do NOT invent opening hours, ticket prices, costs, travel times,
distances, restaurant/hotel names, events, shows, attraction
facilities, historical/architectural claims, transportation
prices, exact routes/MRT stations, landmarks, or activities unless
explicitly present in the knowledge base.

RULE 4 - WEATHER
Use ONLY the supplied live weather data. You may report numeric
fields (temperature, apparent temperature, humidity, precipitation,
rain, wind speed, daily min/max, daily precipitation/rain). Never
invent a descriptive condition (e.g. "partly cloudy") or translate
a weather code into words unless the data explicitly gives that
meaning.

RULE 4B - NO LIVE DATA AVAILABLE
If LIVE WEATHER DATA or LIVE CURRENCY DATA says it was not
retrieved for this request, do NOT use the "Live update:" prefix
for it and do NOT state any number for it (temperature, humidity,
rain, forecast, exchange rate, converted amount - even an
approximate one). Say plainly that it could not be checked. A
missing live-data section is never a licence to invent a
plausible-sounding number from general knowledge.

RULE 5 - WEATHER-AWARE PLANNING
When asked for a weather-aware itinerary, choose activities from
the knowledge base and use the live weather data to adjust them.
The knowledge base explicitly supports: starting outdoor
sightseeing earlier, taking breaks, drinking water, using shade,
combining outdoor and indoor attractions, avoiding overly packed
schedules, using Cloud Forest and Flower Dome as indoor
alternatives, and rearranging outdoor activities when rain occurs.
Use these only when appropriate - do NOT invent additional weather
advice.

RULE 6 - ITINERARY LENGTH AND STRUCTURE
For a 3-day Singapore itinerary, prefer this structure when
supported by the knowledge base context above:
- Day 1 (Marina Bay and Gardens): Marina Bay, Gardens by the Bay,
  Marina Bay Sands, Singapore Flyer, Esplanade area, Singapore
  River, Cloud Forest, Flower Dome.
- Day 2 (Heritage and Food): Chinatown, Little India, Kampong
  Glam, Bugis, food experiences.
- Day 3 (Nature and Leisure): Sentosa, Singapore Botanic Gardens,
  Mandai wildlife attractions, East Coast, Southern Ridges.
If the user asks for a different number of days, produce exactly
that many days - cycle through these same three themes (repeating
or combining supported items across the extra days) rather than
inventing new attractions. Keep each day's entry brief (a short
list of items, not long paragraphs) so a longer itinerary still
fits comfortably in the answer. Only use an item if the knowledge
base context actually supports it.

RULE 6B - STAY ON THE CURRENT QUESTION
Answer only the USER QUESTION (current turn) shown above. The
CONVERSATION HISTORY is background for preferences only - never
copy, continue, or restart a previous assistant answer from it,
and never let an earlier turn's topic (e.g. a currency conversion)
leak into an unrelated new answer (e.g. an itinerary).

RULE 7 - FACTS VS RECOMMENDATIONS
FACTS are directly supported by the knowledge base or MCP.
RECOMMENDATIONS are your own suggestions for organizing supported
activities - prefix these with "Recommendation:" and never
introduce a new destination fact this way.

RULE 7A - LABEL EACH TYPE OF INFORMATION
Plain sentences (no prefix) = stable destination facts from the
knowledge base. Every sentence built from LIVE WEATHER DATA or LIVE
CURRENCY DATA must start with "Live update:" (e.g. "Live update:
the current temperature is 31°C." / "Live update: 60,000 INR is
approximately 980 SGD at the current exchange rate."). Your own
planning suggestions start with "Recommendation:". Never blend a
live figure into a fact sentence without the "Live update:" prefix,
and never use that prefix for knowledge-base-only facts.

RULE 8 - INSUFFICIENT INFORMATION
If requested information is not present in the knowledge base or
MCP data, say so in plain, friendly language a traveller would
understand, for example: "I don't have information about that for
Singapore yet, but I'm happy to help with attractions, itineraries,
weather, or currency." Do not use technical terms like "knowledge
base" or "MCP" in this message. Do not guess.

RULE 9 - CURRENT INFORMATION AND CONVERSATION CONTEXT
Current weather and exchange rates must come from MCP, never from
static knowledge - use MCP data whenever supplied, and never say
weather is unavailable when live weather data was provided. Use
CONVERSATION HISTORY only to preserve stated user preferences
(budget, dates, travel party, interests) and stay consistent with
earlier turns - it is NOT a source of destination, weather, or
currency facts.

RULE 10 - SOURCE PRIORITY
For destination facts: KNOWLEDGE BASE > general knowledge. For
current weather and currency: MCP > KNOWLEDGE BASE, always. Never
override live MCP data with static knowledge.

FINAL VALIDATION
Before answering, check every destination name/fact against the
knowledge base and every weather/currency figure against MCP;
remove unsupported claims; do not add famous attractions just
because they're commonly associated with Singapore; do not invent
prices, hours, events, shows, restaurants, or hotels. The goal is a
grounded answer, not a maximally detailed one. Never mention RAG,
MCP, embeddings, vector stores, LLMs, prompts, or other internal
implementation details to the user.
"""


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

async def _prepare_answer_context(
    question: str,
    history: list[dict[str, str]] | None = None,
):
    """
    Run RAG retrieval and MCP tool execution - the steps shared by
    both the blocking and streaming final-answer paths.
    """

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

    mcp_results = {}

    tools_used = []

    # ========================================================
    # STEP 4 - WEATHER EXECUTION (NO AI SELECTION NEEDED)
    # ========================================================

    # get_weather takes no arguments. Once keyword-based intent
    # detection (should_use_weather) has already decided it's needed,
    # there is nothing left for an LLM to "select" - calling it
    # directly skips a full LLM round trip and its CPU cost.
    if weather_required:

        print(
            "\n===== MCP TOOL EXECUTION ====="
        )

        print(
            "Tool: get_weather (direct call, no AI selection needed)"
        )

        try:

            mcp_result = await execute_mcp_tool(
                WEATHER_TOOL,
                {},
            )

            mcp_results[WEATHER_TOOL] = extract_mcp_result(
                mcp_result
            )

            tools_used.append(WEATHER_TOOL)

            print(
                "\n===== MCP RESULT ====="
            )

            print(
                json.dumps(
                    mcp_results[WEATHER_TOOL],
                    indent=2,
                    default=str,
                )
            )

        except Exception as exc:

            print(
                "\n===== MCP ERROR ====="
            )

            print(str(exc))

            mcp_results[WEATHER_TOOL] = {
                "error": (
                    "The requested live "
                    "travel service "
                    "could not be reached."
                ),
                "details": str(exc),
            }

    # ========================================================
    # STEP 5 - CURRENCY AI ARGUMENT EXTRACTION + EXECUTION
    # ========================================================

    # convert_currency needs amount/from_currency/to_currency parsed
    # out of free text, so the LLM is still needed here - but only
    # bound to this one tool, instead of a generic tool-selection
    # call that used to run even when only weather was required.
    if currency_required:

        currency_tool = next(
            tool
            for tool in all_tools
            if tool.name == CURRENCY_TOOL
        )

        print(
            "\n===== AI TOOL SELECTION ====="
        )

        llm = get_llm()

        tool_enabled_llm = llm.bind_tools(
            [currency_tool]
        )

        selection_prompt = f"""
You are the currency argument-extraction component of a
Singapore travel assistant.

User question:

{question}

Call convert_currency with the amount, from_currency, and
to_currency implied by the question, using ISO currency
codes (e.g. INR, SGD, USD). Do not invent values that are
not implied by the question. Call it at most once.
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

        if response and response.tool_calls:

            tool_call = response.tool_calls[0]

            tool_name = tool_call["name"]

            arguments = tool_call.get(
                "args",
                {},
            )

            if tool_name != CURRENCY_TOOL:

                print(
                    f"\nSkipping unexpected "
                    f"tool: {tool_name}"
                )

            else:

                print(
                    "\n===== MCP TOOL EXECUTION ====="
                )

                print(
                    f"Tool: {tool_name}"
                )

                print(
                    f"Arguments: {arguments}"
                )

                try:

                    mcp_result = (
                        await execute_mcp_tool(
                            tool_name,
                            arguments,
                        )
                    )

                    mcp_results[tool_name] = (
                        extract_mcp_result(
                            mcp_result
                        )
                    )

                    tools_used.append(
                        tool_name
                    )

                    print(
                        "\n===== MCP RESULT ====="
                    )

                    print(
                        json.dumps(
                            mcp_results[tool_name],
                            indent=2,
                            default=str,
                        )
                    )

                except Exception as exc:

                    print(
                        "\n===== MCP ERROR ====="
                    )

                    print(str(exc))

                    mcp_results[tool_name] = {
                        "error": (
                            "The requested live "
                            "travel service "
                            "could not be reached."
                        ),
                        "details": str(exc),
                    }

    if not weather_required and not currency_required:

        print(
            "\n===== MCP ====="
        )

        print(
            "No live MCP tool required."
        )

    # Only attach KB sources when the question actually needed
    # destination knowledge. A pure weather/currency-only question
    # is answered entirely from MCP, so showing unrelated KB
    # sources would misleadingly suggest they were used.
    is_pure_live_data_question = (
        (weather_required or currency_required)
        and not mentions_destination_topic(question)
    )

    visible_sources = (
        [] if is_pure_live_data_question else sources
    )

    return {
        "context": context,
        "sources": visible_sources,
        "mcp_results": mcp_results,
        "tools_used": tools_used,
    }


# ============================================================
# BLOCKING (NON-STREAMING) ANSWER
# ============================================================

async def run_travel_assistant(
    question: str,
    history: list[dict[str, str]] | None = None,
):

    prepared = await _prepare_answer_context(question, history)

    # ========================================================
    # STEP 6 - FINAL GROUNDED LLM
    # ========================================================

    print(
        "\n===== FINAL GROUNDED RESPONSE ====="
    )

    final_prompt = build_final_prompt(
        question=question,
        context=prepared["context"],
        mcp_results=prepared["mcp_results"],
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

    return {
        "answer": answer,
        "sources": prepared["sources"],
        "tools_used": prepared["tools_used"],
        "mcp_results": prepared["mcp_results"],
    }


# ============================================================
# STREAMING ANSWER
# ============================================================

async def run_travel_assistant_stream(
    question: str,
    history: list[dict[str, str]] | None = None,
):
    """
    Same pipeline as `run_travel_assistant`, but yields the final
    answer token-by-token so the UI can render it as it is
    generated instead of waiting for the whole response.

    Yields dicts:
      {"type": "meta", "sources": [...], "tools_used": [...]}
      {"type": "chunk", "text": "..."}
    """

    prepared = await _prepare_answer_context(question, history)

    yield {
        "type": "meta",
        "sources": prepared["sources"],
        "tools_used": prepared["tools_used"],
    }

    print(
        "\n===== FINAL GROUNDED RESPONSE (STREAMING) ====="
    )

    final_prompt = build_final_prompt(
        question=question,
        context=prepared["context"],
        mcp_results=prepared["mcp_results"],
        history=history,
    )

    final_llm = get_llm()

    try:

        async for token in final_llm.astream(
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
        ):

            if token.content:
                yield {"type": "chunk", "text": token.content}

    except Exception as exc:

        print(
            "\n===== FINAL LLM ERROR ====="
        )

        print(str(exc))

        yield {
            "type": "chunk",
            "text": (
                "I’m sorry, but I was unable to "
                "generate the travel recommendation "
                "at this time."
            ),
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