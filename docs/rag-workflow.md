# RAG Workflow

## Knowledge base sources

Four public Singapore travel resources, converted to Markdown under
`data/knowledge_base/`, each carrying `source_title` / `source_url` /
`source_type` front-matter used as citation metadata:

| File | Source |
|---|---|
| `01_wikivoyage_singapore.md` | Wikivoyage — Singapore Travel Guide |
| `02_visit_singapore_essentials.md` | Visit Singapore — Essential Travel Information |
| `03_visit_singapore_itineraries.md` | Visit Singapore — Sample Itineraries |
| `04_visit_singapore_things_to_do.md` | Visit Singapore — Things to Do |

## Pipeline

1. **Load** — `app/rag/loader.py` uses `DirectoryLoader` + `TextLoader` to
   read every `*.md` file, then `extract_source_metadata()` parses the
   `source_title:` / `source_url:` / `source_type:` lines and attaches them
   to each document's metadata **before** chunking, so every resulting chunk
   keeps its citation.
2. **Chunk** — `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`,
   preferring to split on `##` headings first, then paragraphs/sentences.
3. **Embed** — `sentence-transformers/all-MiniLM-L6-v2` via
   `langchain_huggingface.HuggingFaceEmbeddings`.
4. **Store** — `app/rag/vector_store.py` builds a FAISS index with
   `FAISS.from_documents()` and persists it to `data/vector_store/`
   (`index.faiss` + `index.pkl`). Rebuild with:
   ```powershell
   python -m app.rag.vector_store
   ```
5. **Retrieve** — `app/rag/retriever.py` performs
   `similarity_search_with_score(query, k=4)` against the loaded index.
6. **Answer** —
   - `app/rag/service.py::ask_rag()` is a RAG-only helper (used by
     [tests/test_rag_service.py](../AITravelAgentBackEnd/tests/test_rag_service.py)) that builds a
     grounded prompt with `app/rag/prompt.py::RAG_SYSTEM_PROMPT` and calls the
     LLM directly — used when a question needs no live data.
   - In the full assistant flow, `app/orchestrator.py::retrieve_context()`
     performs the same retrieval, and the combined chunks are folded into the
     final grounding prompt alongside any MCP results.

## Grounding guarantees

Both the RAG-only prompt (`app/rag/prompt.py`) and the combined orchestrator
prompt (`app/orchestrator.py::build_final_prompt`) enforce the same rules:

- The knowledge base is the **only** source of destination facts — no
  pretrained/general knowledge may be added.
- An attraction, neighbourhood, or activity may only be mentioned if its
  exact name appears in the retrieved context.
- No invented opening hours, prices, travel times, restaurants, hotels, or
  events.
- If the retrieved context doesn't answer the question, the model must say:
  *"The knowledge base does not provide enough information to confirm this."*
- Every response returned by the API includes a `sources` list (`title`,
  `url`, `file`) so the caller/UI can display citations.
