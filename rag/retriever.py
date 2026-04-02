from __future__ import annotations

import math
import re
from typing import Any, Callable

from utils.compat import traceable


class HashingEmbeddings:
    """Offline-safe embedding fallback used when external embedders are unavailable."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[A-Za-z0-9_]+", (text or "").lower())

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        tokens = self._tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            index = hash(token) % self.dim
            vector[index] += 1.0

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]


class FallbackEmbeddings:
    def __init__(self, factories: list[Callable[[], Any]]):
        self._factories = factories
        self._active: Any | None = None

    def _ensure_active(self) -> Any:
        if self._active is not None:
            return self._active

        last_error: Exception | None = None
        for factory in self._factories:
            try:
                candidate = factory()
                if candidate is None:
                    continue
                self._active = candidate
                return candidate
            except Exception as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error
        self._active = HashingEmbeddings()
        return self._active

    def embed_query(self, text: str) -> list[float]:
        embeddings = self._ensure_active()
        try:
            return embeddings.embed_query(text)
        except Exception:
            self._active = HashingEmbeddings()
            return self._active.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._ensure_active()
        try:
            return embeddings.embed_documents(texts)
        except Exception:
            self._active = HashingEmbeddings()
            return self._active.embed_documents(texts)

def _create_embeddings(config: dict[str, Any]):
    rag_config = config.get("rag", {})
    provider = rag_config.get("embedder_provider", "ollama")
    model = rag_config.get("embedder_model", "nomic-embed-text:v1.5")

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return FallbackEmbeddings(
            [
                lambda: OpenAIEmbeddings(model=model),
                lambda: HashingEmbeddings(),
            ]
        )

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return FallbackEmbeddings(
            [
                lambda: OllamaEmbeddings(model=model),
                lambda: HashingEmbeddings(),
            ]
        )

    return FallbackEmbeddings([lambda: HashingEmbeddings()])


class Retriever:
    _instances: dict[tuple[str, str], "Retriever"] = {}

    @classmethod
    def get_instance(cls, config: dict[str, Any]) -> "Retriever":
        rag_config = config.get("rag", {})
        key = (
            str(rag_config.get("persist_dir", ".chroma_db")),
            str(rag_config.get("collection_name", "ai_ethics_kb")),
        )
        if key not in cls._instances:
            cls._instances[key] = cls(config)
        return cls._instances[key]

    @classmethod
    def clear_cache(cls) -> None:
        cls._instances.clear()

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.collection = None
        self.embedder = None

        rag_config = config.get("rag", {})
        persist_dir = rag_config.get("persist_dir", ".chroma_db")
        collection_name = rag_config.get("collection_name", "ai_ethics_kb")

        try:
            import chromadb

            self.embedder = _create_embeddings(config)
            client = chromadb.PersistentClient(path=persist_dir)
            self.collection = client.get_collection(collection_name)
        except Exception:
            self.collection = None
            self.embedder = None

    @traceable(name="rag_query", tags=["rag"])
    def query(self, description: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not description or self.collection is None or self.embedder is None:
            return []
        try:
            vector = self.embedder.embed_query(description)
            results = self.collection.query(query_embeddings=[vector], n_results=top_k)
        except Exception:
            return []

        documents = results.get("documents", [[]])
        metadatas = results.get("metadatas", [[]])
        distances = results.get("distances", [[]])
        chunks: list[dict[str, Any]] = []
        if not documents:
            return chunks

        for index, text in enumerate(documents[0]):
            metadata = metadatas[0][index] if metadatas and metadatas[0] else {}
            distance = distances[0][index] if distances and distances[0] else None
            chunks.append(
                {
                    "text": text,
                    "metadata": metadata or {},
                    "score": distance,
                }
            )
        return chunks
