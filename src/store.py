from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:

    def __init__(self, collection_name="documents", embedding_fn=None):
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._store = []
        self._next_index = 0

    def _make_record(self, doc: Document):
        return {
            "id": f"{doc.id}_{self._next_index}",
            "doc_id": doc.id,
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": doc.metadata or {},
        }

    def _search_records(self, query, records, top_k):
        query_emb = self._embedding_fn(query)

        scored = []
        for r in records:
            score = _dot(query_emb, r["embedding"])
            scored.append({
                "content": r["content"],
                "score": score,
                "metadata": r["metadata"]
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs):
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)
            self._next_index += 1

    def search(self, query, top_k=5):
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self):
        return len(self._store)

    def search_with_filter(self, query, top_k=3, metadata_filter=None):
        filtered = self._store

        if metadata_filter:
            def match(meta):
                return all(meta.get(k) == v for k, v in metadata_filter.items())

            filtered = [r for r in self._store if match(r["metadata"])]

        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id):
        before = len(self._store)
        self._store = [r for r in self._store if r["doc_id"] != doc_id]
        return len(self._store) < before