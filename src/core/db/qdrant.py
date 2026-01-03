"""Qdrant vector database connector for RAG system."""

from typing import List, Optional

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Batch, Distance, VectorParams

from core import get_logger, settings

logger = get_logger(__name__)


class QdrantConnector:
    """Qdrant vector database connector (similar to llm-twin-course)."""

    _instance: Optional[QdrantClient] = None

    def __init__(self):
        """Initialize Qdrant connection."""
        if QdrantConnector._instance is None:
            if settings.USE_QDRANT_CLOUD:
                QdrantConnector._instance = QdrantClient(
                    url=settings.QDRANT_CLOUD_URL,
                    api_key=settings.QDRANT_APIKEY,
                )
                logger.info("Connected to Qdrant Cloud", url=settings.QDRANT_CLOUD_URL)
            else:
                QdrantConnector._instance = QdrantClient(
                    host=settings.QDRANT_DATABASE_HOST,
                    port=settings.QDRANT_DATABASE_PORT,
                )
                logger.info("Connected to Qdrant",
                           host=settings.QDRANT_DATABASE_HOST,
                           port=settings.QDRANT_DATABASE_PORT)

        self.client = QdrantConnector._instance

    def get_collection(self, collection_name: str):
        """Get collection information."""
        return self.client.get_collection(collection_name=collection_name)

    def create_vector_collection(self, collection_name: str):
        """Create a vector collection."""
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_SIZE,
                    distance=Distance.COSINE
                ),
            )
            logger.info("Created vector collection", name=collection_name)
        except Exception as e:
            logger.warning("Collection may already exist", name=collection_name, error=str(e))

    def upsert_points(
        self,
        collection_name: str,
        points: List[models.PointStruct],
    ):
        """Insert or update points in collection."""
        try:
            self.client.upsert(collection_name=collection_name, points=points)
            logger.debug("Upserted points", collection=collection_name, count=len(points))
        except Exception as e:
            logger.error("Failed to upsert points", error=str(e))
            raise

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_filter: Optional[models.Filter] = None,
        limit: int = 5,
    ) -> List[models.ScoredPoint]:
        """Search for similar vectors."""
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
            )
            logger.debug("Search completed", collection=collection_name, results=len(results))
            return results
        except Exception as e:
            logger.error("Search failed", error=str(e))
            raise

    def scroll(
        self,
        collection_name: str,
        limit: int = 10,
        offset: Optional[int] = None,
    ):
        """Scroll through collection."""
        return self.client.scroll(
            collection_name=collection_name,
            limit=limit,
            offset=offset,
        )

    def close(self):
        """Close connection."""
        if self.client:
            self.client.close()
            logger.info("Qdrant connection closed")

