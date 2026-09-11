from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


KNOWLEDGE_BASE_PATH = Path("data/knowledge_base")


def extract_source_metadata(file_path: str):
    """
    Extract source metadata from a Markdown file.
    """

    source_title = "Unknown source"
    source_url = ""
    source_type = "public_travel_resource"

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line.startswith("source_title:"):
                source_title = line.split(":", 1)[1].strip()

            elif line.startswith("source_url:"):
                source_url = line.split(":", 1)[1].strip()

            elif line.startswith("source_type:"):
                source_type = line.split(":", 1)[1].strip()

    return source_title, source_url, source_type


def load_and_split_documents():
    """
    Load all Markdown files from the knowledge base,
    attach source metadata, and split them into meaningful chunks.
    """

    loader = DirectoryLoader(
        str(KNOWLEDGE_BASE_PATH),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()

    # Attach metadata BEFORE chunking so every chunk retains it.
    for document in documents:
        source_file = document.metadata.get("source", "")

        source_title, source_url, source_type = extract_source_metadata(
            source_file
        )

        document.metadata["source_title"] = source_title
        document.metadata["source_url"] = source_url
        document.metadata["source_type"] = source_type

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=[
            "\n## ",
            "\n\n",
            "\n",
            ". ",
            " ",
        ],
    )

    chunks = splitter.split_documents(documents)

    return chunks