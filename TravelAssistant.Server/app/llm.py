from langchain_ollama import ChatOllama


def get_llm():
    """
    Create the local Ollama LLM used by the travel assistant.
    """

    return ChatOllama(
        model="llama3.2:3b",
        temperature=0,
        num_ctx=4096,
        # Cap generation length - the answers are short travel summaries,
        # not open-ended text, so an unbounded output wastes CPU time.
        num_predict=800,
        # Keep the model resident in Ollama between requests so a session
        # of several turns doesn't repeatedly pay the model-load cost.
        keep_alive="15m",
    )