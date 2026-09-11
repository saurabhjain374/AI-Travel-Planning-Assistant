from app.rag.service import ask_rag


def test_ask_rag_returns_grounded_answer_with_sources():
    question = "What can I do in Singapore when it rains?"

    result = ask_rag(question)

    assert result["answer"]
    assert isinstance(result["sources"], list)
    assert len(result["sources"]) > 0

    for source in result["sources"]:
        assert "title" in source
        assert "url" in source
        assert "file" in source