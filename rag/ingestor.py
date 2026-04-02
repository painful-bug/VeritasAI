from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.compat import traceable



def _get_splitter(config: dict[str, Any]):
    rag_config = config.get("rag", {})
    chunk_size = int(rag_config.get("chunk_size", 800))
    chunk_overlap = int(rag_config.get("chunk_overlap", 120))
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception:
        from langchain.text_splitter import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


@traceable(name="rag_needs_ingestion", tags=["rag"])
def needs_ingestion(config: dict[str, Any]) -> bool:
    rag_config = config.get("rag", {})
    persist_dir = rag_config.get("persist_dir", ".chroma_db")
    collection_name = rag_config.get("collection_name", "ai_ethics_kb")
    try:
        import chromadb

        client = chromadb.PersistentClient(path=persist_dir)
        collection = client.get_collection(collection_name)
        return collection.count() == 0
    except Exception:
        return True


@traceable(name="rag_ingest", tags=["rag", "setup"])
def ingest(config: dict[str, Any]) -> int:
    rag_config = config.get("rag", {})
    pdf_path = rag_config.get("knowledge_base_pdf", "knowledge/ai_ethics_knowledge_base.pdf")
    persist_dir = rag_config.get("persist_dir", ".chroma_db")
    collection_name = rag_config.get("collection_name", "ai_ethics_kb")

    import chromadb
    import fitz

    from rag.retriever import Retriever, _create_embeddings

    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"Knowledge base PDF not found: {pdf_file}")

    document = fitz.open(str(pdf_file))
    pages = [{"text": page.get_text("text"), "page": page_number + 1} for page_number, page in enumerate(document)]

    splitter = _get_splitter(config)
    chunks: list[str] = []
    metadatas: list[dict[str, Any]] = []
    ids: list[str] = []
    for page in pages:
        for chunk_index, chunk in enumerate(splitter.split_text(page["text"])):
            chunk_id = f"p{page['page']}_c{chunk_index}"
            chunks.append(chunk)
            ids.append(chunk_id)
            metadatas.append({"page": page["page"], "source": pdf_path, "chunk_id": chunk_id})

    if not chunks:
        raise RuntimeError(f"No text extracted from {pdf_path}")

    embedder = _create_embeddings(config)
    vectors = embedder.embed_documents(chunks)

    client = chromadb.PersistentClient(path=persist_dir)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.get_or_create_collection(collection_name)
    collection.add(documents=chunks, embeddings=vectors, metadatas=metadatas, ids=ids)
    Retriever.clear_cache()
    return int(collection.count())
