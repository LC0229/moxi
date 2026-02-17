"""Reranking for RAG - uses LLM to rerank search results (like llm-twin-course)."""

from typing import List

from langchain_openai import ChatOpenAI

from core import get_logger, settings

logger = get_logger(__name__)


class Reranker:
    """
    Reranks search results using an LLM to improve accuracy.
    
    Vector search may not always return the most relevant results.
    This class uses an LLM to rerank results based on semantic relevance.
    """

    @staticmethod
    def generate_response(
        query: str, passages: List[str], keep_top_k: int = 5
    ) -> List[str]:
        """
        Rerank passages based on relevance to the query.
        
        Args:
            query: Original query string
            passages: List of passages to rerank
            keep_top_k: Number of top passages to return
            
        Returns:
            List of reranked passages (top k)
        """
        if not passages:
            return []
        
        try:
            # Format passages with separators
            separator = "\n---PASSAGE---\n"
            passages_text = separator.join([f"{i+1}. {p}" for i, p in enumerate(passages)])
            
            prompt = f"""Given the following question, rank these passages by relevance and return the top {keep_top_k} most relevant passages.

Question: "{query}"

Passages:
{passages_text}

Return only the passage numbers (e.g., "1, 3, 5") of the top {keep_top_k} most relevant passages, separated by commas.
If a passage number is not in the list, skip it."""

            model = ChatOpenAI(
                model=settings.OPENAI_MODEL_ID,
                api_key=settings.OPENAI_API_KEY,
                temperature=0,
            )
            
            response = model.invoke(prompt)
            response_text = response.content.strip()
            
            # Parse response to get passage indices
            try:
                # Extract numbers from response
                import re
                indices = [int(i.strip()) - 1 for i in re.findall(r'\d+', response_text)]
                indices = [i for i in indices if 0 <= i < len(passages)]
                
                # Get top k
                reranked = [passages[i] for i in indices[:keep_top_k]]
                
                logger.info("Reranking completed",
                           query=query,
                           original_count=len(passages),
                           reranked_count=len(reranked))
                
                return reranked
                
            except Exception as e:
                logger.warning("Failed to parse reranking response, using original order",
                             error=str(e))
                return passages[:keep_top_k]
                
        except Exception as e:
            logger.error("Reranking failed", error=str(e), query=query)
            # Fallback to original order
            return passages[:keep_top_k]

