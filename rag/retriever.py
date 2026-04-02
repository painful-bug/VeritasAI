from __future__ import annotations

import math
import re
from typing import Any

import chromadb

from config_loader import load_config
from rag.storage import create_persistent_client
from utils.compat import traceable


class HashingEmbeddings:
    def __init__(self, dim: int = 384):
        self.dim = dim

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[A-Za-z0-9_]+", (text or "").lower())

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in self._tokenize(text):
            vector[hash(token) % self.dim] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]


def _create_embeddings(config: dict[str, Any]):
    model_name = config.get("rag", {}).get("embedding_model", "all-MiniLM-L6-v2")
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except Exception:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except Exception:
            return HashingEmbeddings()

    try:
        return HuggingFaceEmbeddings(model_name=model_name, model_kwargs={"local_files_only": True})
    except Exception:
        return HashingEmbeddings()


class Retriever:
    _instances: dict[tuple[str, str], "Retriever"] = {}

    @classmethod
    def get_instance(cls, config: dict[str, Any] | None = None) -> "Retriever":
        effective = config or load_config()
        rag_config = effective.get("rag", {})
        key = (
            str(rag_config.get("chroma_persist_dir", ".chroma_db")),
            str(rag_config.get("collection_name", "ai_ethics_kb")),
        )
        if key not in cls._instances:
            cls._instances[key] = cls(effective)
        return cls._instances[key]

    @classmethod
    def clear_cache(cls) -> None:
        cls._instances.clear()

    def __init__(self, config: dict[str, Any]):
        self.config = config
        rag_config = config.get("rag", {})
        persist_dir = rag_config.get("chroma_persist_dir", ".chroma_db")
        collection_name = rag_config.get("collection_name", "ai_ethics_kb")
        self.embedder = _create_embeddings(config)
        try:
            client = create_persistent_client(persist_dir)
            self.collection = client.get_collection(collection_name)
        except Exception:
            self.collection = None

    @traceable(name="rag_query", tags=["rag"])
    def query(self, description: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not description.strip() or self.collection is None:
            return []
        vector = self.embedder.embed_query(description)
        results = self.collection.query(query_embeddings=[vector], n_results=top_k)
        chunks: list[dict[str, Any]] = []
        documents = results.get("documents", [[]])
        metadatas = results.get("metadatas", [[]])
        distances = results.get("distances", [[]])
        for index, text in enumerate(documents[0] if documents else []):
            metadata = metadatas[0][index] if metadatas and metadatas[0] else {}
            score = distances[0][index] if distances and distances[0] else None
            chunks.append({"text": text, "metadata": metadata or {}, "score": score})
        return chunks
