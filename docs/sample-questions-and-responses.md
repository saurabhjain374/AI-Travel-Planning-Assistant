# Sample Questions & Responses

Captured verbatim from the running app (`POST /api/chat`, `llama3.2:3b`). Nothing edited.

---

### 1. RAG only

**Q:** *What indoor attractions can I visit in Singapore?*
**Tools:** none · **Sources:** Visit Singapore — Things to Do; Wikivoyage; Traveller Essentials

> The knowledge base supports indoor attractions such as: Cloud Forest and Flower Dome at Gardens by the Bay, museums, shopping centres, food courts, heritage attractions, and indoor cultural experiences. These are useful when heavy rain or hot weather makes outdoor sightseeing less comfortable.

---

### 2. MCP only — currency

**Q:** *Convert INR 50,000 to SGD.*
**Tools:** `convert_currency`

MCP result: `{ exchange_rate: 0.013406, converted_amount: 670.3, last_updated: "Mon, 07 Sep 2026" }`

> Live update: INR 50,000 = SGD 670.30 at a rate of 0.013406 (last updated 07 Sep 2026).

---

### 3. Combined RAG + MCP (required scenario)

**Q:** *Create a three-day Singapore itinerary for next week and adjust it according to the weather forecast.*
**Tools:** `get_weather` · **Sources:** Wikivoyage; Traveller Essentials; Sample Itineraries

MCP forecast: Day 1 dry · Day 2 rain 8 mm · Day 3 rain 14.6 mm

> **Day 1** — Marina Bay + Gardens by the Bay (outdoor); evening at Marina Bay.
> **Day 2** — Chinatown, Little India, Kampong Glam (mostly sheltered); local food.
> **Day 3** *(rain expected)* — Cloud Forest & Flower Dome (indoor); Botanic Gardens if it clears.
>
> Live update: rain likely on 9–10 Sep. Recommendation: swap outdoor Sentosa for indoor Gardens by the Bay on Day 3.

Demonstrates: attractions from KB, rain caveat from MCP, both cited/labelled.

---

### 4. Known failure case (documented, not hidden)

**Q:** *What is the weather forecast for the next three days?*
**Tools:** `get_weather` (returned real data)

> The knowledge base does not provide enough information to confirm the weather forecast…
>
> However, I can suggest that you check the live weather data for the current date and time to get an accurate forecast. The live weather data is available through the MCP tool.

The tool *did* return data; the small local model occasionally under-uses it. Called out per assignment requirement to handle failures honestly. See `prompt-strategy.md § Known limitation`.

---

| # | Scenario | Requirement |
|---|---|---|
| 1 | Indoor attractions | RAG-only grounded answer with sources |
| 2 | Currency | MCP tool selection + execution |
| 3 | 3-day itinerary + weather | Combined RAG + MCP (required) |
| 4 | Weather forecast | Honest failure handling |
