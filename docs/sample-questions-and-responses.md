# Sample Questions & Responses

A quick look at what the assistant actually says, in its own words.

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

> **Note:** this transcript predates the human-friendly fallback wording (RULE 8) — today the
> assistant would say something like *"I don't have information about that for Singapore yet,
> but I'm happy to help with attractions, itineraries, weather, or currency"* instead of naming
> "the knowledge base". The underlying issue (under-using returned tool data) is unchanged.

---

### 5. RAG only — nature reserves (newly added NParks KB)

**Q:** *What are Singapore's nature reserves and what can I do there?*
**Tools:** none · **Sources:** NParks — Parks, Nature Reserves and Park Connectors; Visit Singapore — Things to Do

> Singapore has four nature reserves:
>
> 1. Central Catchment Nature Reserve
> 2. Bukit Timah Nature Reserve
> 3. Sungei Buloh Wetland Reserve
> 4. Labrador Nature Reserve
>
> These nature reserves protect ecosystems and native flora and fauna. Visitors should follow posted rules and stay on designated trails.
>
> Some activities you can do at these nature reserves include:
>
> * Hiking
> * Nature walks
> * Birdwatching
> * Exploring forest trails
> * TreeTop Walk (at Central Catchment Nature Reserve)
>
> Please note that the park hours and activities may vary, so it's best to check the official website or contact the park directly for more information.

---

### 6. RAG only — public transport (newly added LTA KB)

**Q:** *How do I get around Singapore using public transport?*
**Tools:** none · **Sources:** Land Transport Authority — Getting Around Singapore; Visit Singapore — Traveller Essentials

> The MRT is one of the most convenient ways for visitors to travel around Singapore. It connects many major tourist areas and residential districts.
>
> Visitors can use MRT stations to reach areas such as Marina Bay, Chinatown, Little India, Bugis, Orchard, and other major destinations.
>
> Public buses provide extensive coverage and can complement the MRT.
>
> Buses are useful when an attraction or hotel is not located directly next to an MRT station.
>
> Taxis and ride-hailing services provide convenient alternatives when travelling with luggage, during late hours, or when a destination is less convenient to reach by public transport.
>
> Walking can be a good way to explore compact cultural districts such as Chinatown, Little India, and Kampong Glam.
>
> However, visitors should consider Singapore's heat and humidity when planning long walking routes.

---

### 7. RAG only — heritage & museums (newly added NHB KB)

**Q:** *Tell me about heritage attractions and museums in Singapore.*
**Tools:** none · **Sources:** National Heritage Board — Singapore Heritage and Museums; Visit Singapore — Traveller Essentials

> Heritage attractions and museums in Singapore are numerous and diverse, showcasing the country's rich history and cultural heritage. Here are some notable ones:
>
> 1. **National Museum of Singapore**: A premier museum that tells the story of Singapore's history and culture, from its ancient roots to the present day.
> 2. **Indian Heritage Centre**: A museum that showcases the history and culture of the Indian community in Singapore, with a focus on the Indian independence movement.
> 3. **Malay Heritage Centre**: A museum that explores the history and culture of the Malay community in Singapore, with a focus on the Malay Sultanate and the country's Islamic heritage.
> 4. **Chinatown Heritage Centre**: A museum that tells the story of the Chinese community in Singapore, from the 19th century to the present day.
> 5. **National Monuments**: Several national monuments throughout Singapore, such as the Buddha Tooth Relic Temple and the Sultan Mosque, which showcase the country's rich cultural heritage.
> 6. **Gardens by the Bay**: While not strictly a museum, Gardens by the Bay features several heritage-inspired attractions, such as the Cloud Forest and Flower Dome cooled conservatories.
> 7. **Little India Arcade**: A historic shopping arcade that showcases the vibrant culture and heritage of Little India.
> 8. **Kampong Glam**: A historic Malay village that has been preserved to showcase the country's Islamic heritage and cultural traditions.
> 9. **Singapore River**: A scenic river that has played a significant role in Singapore's history and development, with several heritage-inspired attractions and walking trails along its banks.
> 10. **Heritage Trails**: Several heritage trails throughout Singapore, such as the Singapore Heritage Trail and the Kampong Glam Heritage Trail, which take visitors on a journey through the country's rich cultural heritage.

Demonstrates: expanded KB (NHB) now returns richer, multi-source heritage answers grounded in cited files.

---

| # | Scenario | Requirement |
|---|---|---|
| 1 | Indoor attractions | RAG-only grounded answer with sources |
| 2 | Currency | MCP tool selection + execution |
| 3 | 3-day itinerary + weather | Combined RAG + MCP (required) |
| 4 | Weather forecast | Honest failure handling |
| 5 | Nature reserves | RAG-only, NParks KB |
| 6 | Public transport | RAG-only, LTA KB |
| 7 | Heritage & museums | RAG-only, NHB KB |
