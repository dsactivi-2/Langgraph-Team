from __future__ import annotations

import hashlib
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.http import models

from .settings import get_settings

VECTOR_SIZE = 128


class VectorMemoryUnavailable(RuntimeError):
    pass


def embed_text(text: str, size: int = VECTOR_SIZE) -> list[float]:
    vector = [0.0] * size
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % size
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = sum(value * value for value in vector) ** 0.5 or 1.0
    return [value / norm for value in vector]


class QdrantMemory:
    def __init__(self, url: str | None = None, collection: str | None = None) -> None:
        settings = get_settings()
        self.url = url or settings.qdrant_url
        self.collection = collection or settings.project_memory_collection
        self.client = QdrantClient(url=self.url, timeout=2, check_compatibility=False)

    def setup(self) -> None:
        try:
            collections = self.client.get_collections().collections
            if not any(item.name == self.collection for item in collections):
                self.client.create_collection(
                    collection_name=self.collection,
                    vectors_config=models.VectorParams(
                        size=VECTOR_SIZE,
                        distance=models.Distance.COSINE,
                    ),
                )
        except Exception as exc:  # pragma: no cover - network fallback
            raise VectorMemoryUnavailable(str(exc)) from exc

    def upsert(self, project_id: str, text: str, metadata: dict[str, Any] | None = None) -> str:
        self.setup()
        point_id = str(uuid5(NAMESPACE_URL, f"{project_id}:{text}"))
        payload = {"project_id": project_id, "text": text, **(metadata or {})}
        try:
            self.client.upsert(
                collection_name=self.collection,
                points=[
                    models.PointStruct(
                        id=point_id,
                        vector=embed_text(text),
                        payload=payload,
                    )
                ],
            )
        except Exception as exc:  # pragma: no cover - network fallback
            raise VectorMemoryUnavailable(str(exc)) from exc
        return point_id

    def search(
        self,
        query: str,
        project_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        self.setup()
        query_filter = None
        if project_id:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="project_id",
                        match=models.MatchValue(value=project_id),
                    )
                ]
            )
        try:
            result = self.client.query_points(
                collection_name=self.collection,
                query=embed_text(query),
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
        except Exception as exc:  # pragma: no cover - network fallback
            raise VectorMemoryUnavailable(str(exc)) from exc
        return [
            {"id": str(point.id), "score": point.score, "payload": point.payload}
            for point in result.points
        ]


class HybridMemory:
    def __init__(self, memory: QdrantMemory | None = None) -> None:
        self.memory = memory or QdrantMemory()
        self._fallback: list[dict[str, Any]] = []
        self.last_error: str | None = None

    def upsert(self, project_id: str, text: str, metadata: dict[str, Any] | None = None) -> str:
        try:
            point_id = self.memory.upsert(project_id, text, metadata)
            self.last_error = None
            return point_id
        except VectorMemoryUnavailable as exc:
            self.last_error = str(exc)
            point_id = str(uuid5(NAMESPACE_URL, f"{project_id}:{text}"))
            self._fallback.append(
                {
                    "id": point_id,
                    "project_id": project_id,
                    "text": text,
                    "metadata": metadata or {},
                    "vector": embed_text(text),
                }
            )
            return point_id

    def search(
        self,
        query: str,
        project_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        try:
            results = self.memory.search(query, project_id, limit)
            self.last_error = None
            return results
        except VectorMemoryUnavailable as exc:
            self.last_error = str(exc)
            query_vector = embed_text(query)
            scored = []
            for item in self._fallback:
                if project_id and item["project_id"] != project_id:
                    continue
                score = sum(a * b for a, b in zip(query_vector, item["vector"], strict=True))
                scored.append(
                    {
                        "id": item["id"],
                        "score": score,
                        "payload": {
                            "project_id": item["project_id"],
                            "text": item["text"],
                            **item["metadata"],
                        },
                    }
                )
            return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]
