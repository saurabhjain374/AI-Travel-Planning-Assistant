from app.llm import get_llm
from app.rag.prompt import build_rag_prompt
from app.rag.retriever import search_knowledge_base

# FAISS returns L2 distance (lower = more similar) for every query, even
# when nothing in the knowledge base is actually relevant. Empirically
# (all-MiniLM-L6-v2 on this KB):
#   - Well-formed on-topic queries top-1 ~0.5-0.7
#   - On-topic queries with typos / country-name misspellings ~1.0-1.3
#     (e.g. "Singapour natural park list" -> ~1.03 for the NParks chunk)
#   - Off-topic queries (python code, cricket, chocolate cake) ~1.45+
# Cutoff sits above the typo band but well below the off-topic band so
# real matches survive minor spelling errors without polluting answers
# for genuinely unrelated questions.
MAX_RELEVANT_DISTANCE = 1.25


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

        if score > MAX_RELEVANT_DISTANCE:
            continue

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