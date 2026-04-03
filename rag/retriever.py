from __future__ import annotations

import math
import re
from collections import OrderedDict
from typing import Any

from config_loader import load_config
from rag.storage import create_persistent_client
from utils.compat import traceable

REGULATORY_TERMS = {
    "eu ai act",
    "gdpr",
    "nist",
    "ai rmf",
    "article",
    "transparency",
    "governance",
    "high-risk",
    "prohibited",
    "biometric",
    "discrimination",
    "fairness",
}

QUERY_EXPANSIONS = {
    "hiring": ["employment", "recruitment", "candidate screening"],
    "biometric": ["facial recognition", "fingerprint", "identity verification"],
    "surveillance": ["tracking", "monitoring", "watchlist"],
    "dataset": ["data governance", "data minimization", "sensitive attributes"],
    "discrimination": ["bias", "fairness", "protected attributes"],
    "model": ["automated decision", "inference", "classifier"],
}


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


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9_]{3,}", (text or "").lower()))


def _expand_query(query: str) -> list[str]:
    lowered = (query or "").lower()
    expanded = [query]
    for seed, variants in QUERY_EXPANSIONS.items():
        if seed in lowered:
            expanded.extend(f"{query}. {variant}" for variant in variants)

    if not any(term in lowered for term in REGULATORY_TERMS):
        expanded.append(f"{query}. EU AI Act GDPR NIST AI RMF governance transparency")

    deduped: "OrderedDict[str, None]" = OrderedDict()
    for candidate in expanded:
        normalized = candidate.strip()
        if normalized:
            deduped.setdefault(normalized, None)
    return list(deduped.keys())[:5]


def _confidence_from_distance(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return 1.0 / (1.0 + max(0.0, float(distance)))


def _trust_score(query: str, text: str, metadata: dict[str, Any], distance: float | None) -> tuple[float, float]:
    confidence = _confidence_from_distance(distance)
    query_tokens = _tokenize(query)
    text_tokens = _tokenize(text)
    overlap = 0.0
    if query_tokens:
        overlap = len(query_tokens & text_tokens) / len(query_tokens)

    reg_tokens = {term for term in REGULATORY_TERMS if term in (text or "").lower()}
    reg_bonus = min(1.0, len(reg_tokens) / 4)
    metadata_bonus = 0.0
    if metadata.get("chunk_id"):
        metadata_bonus += 0.04
    if metadata.get("page"):
        metadata_bonus += 0.04
    if metadata.get("jurisdiction"):
        metadata_bonus += 0.04

    trust = 0.65 * confidence + 0.2 * overlap + 0.1 * reg_bonus + metadata_bonus
    return confidence, min(1.0, max(0.0, trust))


def _dedupe_key(metadata: dict[str, Any], text: str) -> str:
    chunk_id = str(metadata.get("chunk_id") or "").strip()
    if chunk_id:
        return f"chunk:{chunk_id}"
    return f"text:{hash(text.strip().lower())}"


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
        agentic_config = config.get("agentic", {})
        persist_dir = rag_config.get("chroma_persist_dir", ".chroma_db")
        collection_name = rag_config.get("collection_name", "ai_ethics_kb")
        self.embedder = _create_embeddings(config)
        self.default_top_k = int(agentic_config.get("retrieval_top_k", rag_config.get("top_k", 3)))
        self.default_min_trust = float(agentic_config.get("retrieval_trust_min", 0.3))
        try:
            client = create_persistent_client(persist_dir)
            self.collection = client.get_collection(collection_name)
        except Exception:
            self.collection = None

    def _collection_query(self, query: str, n_results: int) -> list[dict[str, Any]]:
        if self.collection is None:
            return []
        vector = self.embedder.embed_query(query)
        results = self.collection.query(query_embeddings=[vector], n_results=n_results)

        chunks: list[dict[str, Any]] = []
        documents = results.get("documents", [[]])
        metadatas = results.get("metadatas", [[]])
        distances = results.get("distances", [[]])
        for index, text in enumerate(documents[0] if documents else []):
            metadata = metadatas[0][index] if metadatas and metadatas[0] else {}
            distance = distances[0][index] if distances and distances[0] else None
            confidence, trust_score = _trust_score(query, text, metadata or {}, distance)
            chunks.append(
                {
                    "text": text,
                    "metadata": metadata or {},
                    "score": distance,
                    "confidence": confidence,
                    "trust_score": trust_score,
                    "query": query,
                }
            )
        return chunks

    @staticmethod
    def _merge_hits(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            metadata = candidate.get("metadata", {}) or {}
            key = _dedupe_key(metadata, str(candidate.get("text", "")))
            current = deduped.get(key)
            if current is None or float(candidate.get("trust_score", 0.0)) > float(current.get("trust_score", 0.0)):
                deduped[key] = candidate
        return list(deduped.values())

    @traceable(name="rag_query", tags=["rag"])
    def query(
        self,
        description: str,
        top_k: int | None = None,
        min_trust: float | None = None,
        expand_query: bool = True,
    ) -> list[dict[str, Any]]:
        if not description.strip() or self.collection is None:
            return []

        requested_k = int(top_k or self.default_top_k)
        effective_min_trust = float(self.default_min_trust if min_trust is None else min_trust)
        n_candidates = max(requested_k * 3, requested_k)

        queries = _expand_query(description) if expand_query else [description]
        candidates: list[dict[str, Any]] = []
        for query in queries:
            candidates.extend(self._collection_query(query, n_results=n_candidates))

        merged = self._merge_hits(candidates)
        merged.sort(key=lambda item: (float(item.get("trust_score", 0.0)), float(item.get("confidence", 0.0))), reverse=True)

        trusted = [item for item in merged if float(item.get("trust_score", 0.0)) >= effective_min_trust]
        if trusted:
            return trusted[:requested_k]
        return merged[:requested_k]

    @traceable(name="rag_query_compliance", tags=["rag", "compliance"])
    def query_for_compliance(self, description: str, top_k: int | None = None) -> list[dict[str, Any]]:
        return self.query(description, top_k=top_k, min_trust=self.default_min_trust, expand_query=True)
