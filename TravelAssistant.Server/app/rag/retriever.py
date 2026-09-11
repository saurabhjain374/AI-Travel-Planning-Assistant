from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


VECTOR_STORE_PATH = Path("data/vector_store")


def get_vector_store():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return FAISS.load_local(
        str(VECTOR_STORE_PATH),
        embeddings,
        allow_dangerous_deserialization=True,
    )


def search_knowledge_base(query: str, k: int = 4):
    vector_store = get_vector_store()

    results = vector_store.similarity_search_with_score(
        query,
        k=k,
    )

    return results


if __name__ == "__main__":
    query = "What can I do in Singapore when it rains?"

    results = search_knowledge_base(query)

    print(f"\nQuery: {query}")
    print(f"Results found: {len(results)}")

    for index, (document, score) in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print(f"Score: {score:.4f}")
        print(f"Source: {document.metadata.get('source')}")
        print(document.page_content[:500])