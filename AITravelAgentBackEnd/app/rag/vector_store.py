from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from app.rag.loader import load_and_split_documents


VECTOR_STORE_PATH = Path("data/vector_store")


def create_vector_store():
    """Create a FAISS vector store from the knowledge-base documents."""

    documents = load_and_split_documents()

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = FAISS.from_documents(
        documents,
        embeddings,
    )

    VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)

    vector_store.save_local(str(VECTOR_STORE_PATH))

    return vector_store


if __name__ == "__main__":
    vector_store = create_vector_store()

    print("FAISS vector store created successfully.")
    print(f"Location: {VECTOR_STORE_PATH}")