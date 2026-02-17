"""Vector retriever for RAG - retrieves relevant documents from Qdrant (like llm-twin-course)."""

from typing import List, Optional

from qdrant_client import models
from sentence_transformers import SentenceTransformer

from core import get_logger, settings
from core.db.qdrant import QdrantConnector
from core.rag.query_expansion import QueryExpansion
from core.rag.reranking import Reranker

logger = get_logger(__name__)


class VectorRetriever:
    """
    Retrieves relevant documents from Qdrant using vector similarity search.
    
    Similar to llm-twin-course's VectorRetriever, but adapted for moxi's use case.
    
    Process:
    1. Query Expansion - generate multiple related queries
    2. Vector Search - search Qdrant for each query
    3. Reranking - use LLM to rerank results
    """

    def __init__(self, query: str, collection_name: str = "vector_repos"):
        """
        Initialize retriever.
        
        Args:
            query: Search query
            collection_name: Qdrant collection name
        """
        self.query = query
        self.collection_name = collection_name
        self._client = QdrantConnector()
        
        # Initialize embedding model
        self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL_ID)
        
        # Initialize query expansion and reranking
        self._query_expander = QueryExpansion()
        self._reranker = Reranker()

    def retrieve_top_k(
        self,
        k: int = 10,
        to_expand_to_n_queries: int = 3,
        query_filter: Optional[models.Filter] = None,
    ) -> List[models.ScoredPoint]:
        """
        Retrieve top k documents using query expansion and vector search.
        
        Args:
            k: Number of documents to retrieve
            to_expand_to_n_queries: Number of query variations to generate
            query_filter: Optional Qdrant filter (e.g., filter by repo_name)
            
        Returns:
            List of ScoredPoint objects from Qdrant
        """
        # Step 1: Query Expansion
        generated_queries = self._query_expander.generate_response(
            self.query, to_expand_to_n=to_expand_to_n_queries
        )
        logger.info("Query expansion completed",
                   original_query=self.query,
                   expanded_queries=generated_queries)

        # Step 2: Vector Search for each query
        all_hits = []
        for query in generated_queries:
            try:
                query_vector = self._embedder.encode(query).tolist()
                
                hits = self._client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=k // len(generated_queries) + 1,  # Distribute k across queries
                )
                all_hits.extend(hits)
                
            except Exception as e:
                logger.error("Vector search failed for query",
                           query=query,
                           error=str(e))
                continue

        # Remove duplicates (by point id)
        seen_ids = set()
        unique_hits = []
        for hit in all_hits:
            if hit.id not in seen_ids:
                seen_ids.add(hit.id)
                unique_hits.append(hit)

        logger.info("Vector search completed",
                   total_hits=len(unique_hits),
                   collection=self.collection_name)

        return unique_hits

    def rerank(
        self, hits: List[models.ScoredPoint], keep_top_k: int = 5
    ) -> List[str]:
        """
        Rerank search results using LLM.
        
        Args:
            hits: List of ScoredPoint objects from Qdrant
            keep_top_k: Number of top results to keep
            
        Returns:
            List of reranked passage texts
        """
        if not hits:
            return []

        # Extract content from hits
        content_list = []
        for hit in hits:
            content = hit.payload.get("content", "")
            if content:
                content_list.append(content)

        if not content_list:
            logger.warning("No content found in hits")
            return []

        # Rerank using LLM
        reranked_passages = self._reranker.generate_response(
            query=self.query,
            passages=content_list,
            keep_top_k=keep_top_k,
        )

        logger.info("Reranking completed",
                   original_count=len(content_list),
                   reranked_count=len(reranked_passages))

        return reranked_passages

    def retrieve_and_rerank(
        self,
        k: int = 10,
        to_expand_to_n_queries: int = 3,
        keep_top_k: int = 5,
        query_filter: Optional[models.Filter] = None,
    ) -> List[str]:
        """
        Complete retrieval pipeline: expansion -> search -> rerank.
        
        Args:
            k: Number of documents to retrieve initially
            to_expand_to_n_queries: Number of query variations
            keep_top_k: Number of final results after reranking
            query_filter: Optional Qdrant filter
            
        Returns:
            List of reranked passage texts
        """
        # Retrieve documents
        hits = self.retrieve_top_k(
            k=k,
            to_expand_to_n_queries=to_expand_to_n_queries,
            query_filter=query_filter,
        )

        # Rerank
        reranked = self.rerank(hits, keep_top_k=keep_top_k)

        return reranked

