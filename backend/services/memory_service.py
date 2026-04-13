"""Local Memory Layer — SQLite-backed + optional Chroma vector search."""
import json
import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.config import settings
from backend.db.models import MemoryEntry

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    ENCODER_AVAILABLE = True
except ImportError:
    ENCODER_AVAILABLE = False


class MemoryService:
    def __init__(self):
        self._chroma_client = None
        self._collection = None

    def _get_chroma(self):
        if not CHROMA_AVAILABLE:
            return None
        if not settings.CHROMA_ENABLED:
            return None
        if not self._chroma_client:
            self._chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._chroma_client.get_or_create_collection(
                name="adaptive_ai_memory",
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _encode(self, text: str) -> list[float]:
        if ENCODER_AVAILABLE:
            return _encoder.encode(text).tolist()
        # Fallback: simple character hash embedding (not useful for search, but won't crash)
        return [float(ord(c) % 128) / 128 for c in text[:384]]

    async def store(
        self,
        db: AsyncSession,
        key: str,
        value: str,
        user_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        source: str = "manual",
    ) -> MemoryEntry:
        # Check if key exists
        result = await db.execute(
            select(MemoryEntry).where(
                MemoryEntry.key == key,
                MemoryEntry.user_id == user_id,
            )
        )
        entry = result.scalar_one_or_none()

        embedding_id = None
        collection = self._get_chroma()
        if collection:
            embedding_id = f"{user_id or 'anon'}:{key}"
            embedding = self._encode(f"{key} {value}")
            collection.upsert(
                ids=[embedding_id],
                embeddings=[embedding],
                documents=[value],
                metadatas=[{"key": key, "user_id": user_id or "", "source": source}],
            )

        if entry:
            entry.value = value
            entry.tags = tags or []
            entry.source = source
            entry.embedding_id = embedding_id
        else:
            entry = MemoryEntry(
                user_id=user_id,
                key=key,
                value=value,
                tags=tags or [],
                source=source,
                embedding_id=embedding_id,
            )
            db.add(entry)

        await db.commit()
        await db.refresh(entry)
        return entry

    async def retrieve(
        self,
        db: AsyncSession,
        user_id: Optional[str] = None,
        key: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        q = select(MemoryEntry)
        if user_id:
            q = q.where(MemoryEntry.user_id == user_id)
        if key:
            q = q.where(MemoryEntry.key == key)
        q = q.limit(limit)
        result = await db.execute(q)
        entries = result.scalars().all()
        if tags:
            entries = [e for e in entries if any(t in (e.tags or []) for t in tags)]
        return list(entries)

    async def semantic_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        n_results: int = 5,
    ) -> list[dict]:
        collection = self._get_chroma()
        if not collection:
            return []
        embedding = self._encode(query)
        where = {"user_id": user_id} if user_id else None
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where,
        )
        out = []
        for i, doc in enumerate(results["documents"][0]):
            out.append({
                "document": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return out

    async def delete(
        self,
        db: AsyncSession,
        entry_id: str,
        user_id: Optional[str] = None,
    ) -> bool:
        result = await db.execute(
            select(MemoryEntry).where(MemoryEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if not entry:
            return False
        if user_id and entry.user_id != user_id:
            return False

        collection = self._get_chroma()
        if collection and entry.embedding_id:
            try:
                collection.delete(ids=[entry.embedding_id])
            except Exception:
                pass

        await db.execute(delete(MemoryEntry).where(MemoryEntry.id == entry_id))
        await db.commit()
        return True

    async def export(self, db: AsyncSession, user_id: Optional[str] = None) -> dict:
        entries = await self.retrieve(db, user_id=user_id, limit=10000)
        return {
            "version": "1.0",
            "user_id": user_id,
            "entries": [
                {
                    "id": e.id,
                    "key": e.key,
                    "value": e.value,
                    "tags": e.tags,
                    "source": e.source,
                    "created_at": e.created_at.isoformat(),
                }
                for e in entries
            ],
        }


memory_service = MemoryService()
