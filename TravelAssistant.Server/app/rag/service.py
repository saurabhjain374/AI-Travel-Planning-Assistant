from app.llm import get_llm
from app.rag.prompt import build_rag_prompt
from app.rag.retriever import search_knowledge_base


def retrieve_context(question: str, k: int = 4):
    """
    Retrieve relevant knowledge-base chunks.

    Returns:
        context: Combined retrieved content.
        sources: Source title, URL, and internal file information.
    """

    results = search_knowledge_base(question, k=k)

    context_parts = []
    sources = []

    for document, score in results:
        context_parts.append(document.page_content)

        source = {
            "title": document.metadata.get(
                "source_title",
                "Unknown source"
            ),
            "url": document.metadata.get(
                "source_url",
                ""
            ),
            "file": document.metadata.get(
                "source",
                "Unknown source"
            ),
        }

        if source not in sources:
            sources.append(source)

    context = "\n\n---\n\n".join(context_parts)

    return context, sources


def prepare_rag_prompt(question: str, k: int = 4):
    """
    Retrieve relevant context and prepare the grounded RAG prompt.
    """

    context, sources = retrieve_context(question, k)

    prompt = build_rag_prompt(
        context=context,
        question=question,
    )

    return prompt, sources


def ask_rag(question: str, k: int = 4):
    """
    Retrieve knowledge, build a grounded prompt,
    and generate an answer using the local LLM.
    """

    prompt, sources = prepare_rag_prompt(question, k)

    llm = get_llm()

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "sources": sources,
    }