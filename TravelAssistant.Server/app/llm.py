from langchain_ollama import ChatOllama


def get_llm():
    """
    Create the local Ollama LLM used by the travel assistant.
    """

    return ChatOllama(
        model="llama3.2:3b",
        temperature=0,
        # Large enough to hold KB context + trimmed history + rules + a
        # multi-day itinerary answer without silently truncating the
        # prompt (which was cutting answers short and causing the model
        # to lose track of the current question).
        num_ctx=8192,
        # Cap generation length, but leave enough headroom for longer
        # itineraries (5+ days) to finish instead of stopping mid-answer.
        num_predict=1536,
        # Keep the model resident in Ollama between requests so a session
        # of several turns doesn't repeatedly pay the model-load cost.
        keep_alive="15m",
    )