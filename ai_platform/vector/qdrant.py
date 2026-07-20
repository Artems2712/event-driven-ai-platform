import hashlib
import math
import uuid


class QdrantDocumentIndexer:
    def __init__(
        self,
        url: str,
        collection_name: str = "ai_documents",
        vector_size: int = 64,
    ) -> None:
        self.url = url
        self.collection_name = collection_name
        self.vector_size = vector_size

    async def ensure_collection(self) -> None:
        from qdrant_client import AsyncQdrantClient, models

        client = AsyncQdrantClient(url=self.url)
        collections = await client.get_collections()
        existing = {item.name for item in collections.collections}
        if self.collection_name in existing:
            return
        await client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    async def upsert_document(self, document_id: str, text: str) -> str:
        from qdrant_client import AsyncQdrantClient, models

        await self.ensure_collection()
        vector_id = str(uuid.uuid5(uuid.NAMESPACE_URL, document_id))
        client = AsyncQdrantClient(url=self.url)
        await client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=vector_id,
                    vector=hashing_vector(text, self.vector_size),
                    payload={"document_id": document_id, "text": text},
                )
            ],
        )
        return vector_id


def hashing_vector(text: str, dimensions: int = 64) -> list[float]:
    values = [0.0] * dimensions
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        values[index] += 1.0
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [round(value / norm, 6) for value in values]
