from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz

from config_loader import load_config
from rag.storage import create_persistent_client_with_recovery
from utils.compat import traceable


def _resolve_pdf_path(config: dict[str, Any]) -> Path:
    configured = Path(config.get("rag", {}).get("knowledge_base_pdf", "knowledge/ai_ethics_knowledge_base.pdf"))
    if configured.exists():
        return configured

    repo_root = Path(__file__).resolve().parents[1]
    fallbacks = [
        repo_root / "knowledge" / "ai_ethics_knowledge_base.pdf",
        repo_root / "ai_ethics_knowledge_base.pdf",
    ]
    for candidate in fallbacks:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Knowledge base PDF not found: {configured}")


def _create_splitter(config: dict[str, Any]):
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception:
        from langchain.text_splitter import RecursiveCharacterTextSplitter

    rag_config = config.get("rag", {})
    return RecursiveCharacterTextSplitter(
        chunk_size=int(rag_config.get("chunk_size", 800)),
        chunk_overlap=int(rag_config.get("chunk_overlap", 100)),
    )


@traceable(name="rag_needs_ingestion", tags=["rag"])
def needs_ingestion(config: dict[str, Any] | None = None) -> bool:
    effective = config or load_config()
    rag_config = effective.get("rag", {})
    persist_dir = rag_config.get("chroma_persist_dir", ".chroma_db")
    collection_name = rag_config.get("collection_name", "ai_ethics_kb")
    try:
        client, archived = create_persistent_client_with_recovery(persist_dir)
        if archived is not None:
            return True
        collection = client.get_collection(collection_name)
        return collection.count() == 0
    except Exception:
        return True


@traceable(name="rag_ingest", tags=["rag", "setup"])
def ingest(config: dict[str, Any] | None = None) -> int:
    effective = config or load_config()
    rag_config = effective.get("rag", {})
    pdf_path = _resolve_pdf_path(effective)
    persist_dir = rag_config.get("chroma_persist_dir", ".chroma_db")
    collection_name = rag_config.get("collection_name", "ai_ethics_kb")

    from rag.retriever import Retriever, _create_embeddings

    document = fitz.open(str(pdf_path))
    pages = [{"text": page.get_text("text"), "page": page_number + 1} for page_number, page in enumerate(document)]
    splitter = _create_splitter(effective)

    chunks: list[str] = []
    metadatas: list[dict[str, Any]] = []
    ids: list[str] = []
    for page in pages:
        for chunk_index, chunk in enumerate(splitter.split_text(page["text"])):
            if not chunk.strip():
                continue
            chunk_id = f"p{page['page']}_c{chunk_index}"
            chunks.append(chunk)
            metadatas.append({"page": page["page"], "source": str(pdf_path), "chunk_id": chunk_id})
            ids.append(chunk_id)

    if not chunks:
        raise RuntimeError(f"No text extracted from {pdf_path}")

    embedder = _create_embeddings(effective)
    vectors = embedder.embed_documents(chunks)

    client, archived = create_persistent_client_with_recovery(persist_dir)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.get_or_create_collection(collection_name)
    collection.add(documents=chunks, embeddings=vectors, metadatas=metadatas, ids=ids)
    Retriever.clear_cache()
    count = int(collection.count())
    if count <= 0:
        raise RuntimeError("Ingestion produced zero chunks.")
    if archived is not None:
        print(f"Recovered corrupt Chroma store by moving it to {archived}")
    return count
