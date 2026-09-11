from langchain_ollama import ChatOllama


def get_llm():
    """
    Create the local Ollama LLM used by the travel assistant.
    """

    return ChatOllama(
        model="llama3.2:3b",
        temperature=0,
    )