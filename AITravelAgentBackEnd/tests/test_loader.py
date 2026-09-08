from app.rag.loader import load_and_split_documents


def test_load_and_split_documents_returns_chunks():
    chunks = load_and_split_documents()

    assert len(chunks) > 0

    for chunk in chunks:
        assert chunk.page_content.strip()
        assert chunk.metadata.get("source_title")