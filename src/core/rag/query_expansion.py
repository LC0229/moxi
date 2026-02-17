"""Query expansion for RAG - generates multiple related queries (like llm-twin-course)."""

from typing import List

from langchain_openai import ChatOpenAI

from core import get_logger, settings

logger = get_logger(__name__)


class QueryExpansion:
    """
    Expands a single query into multiple semantically similar queries.
    
    This improves recall by searching with multiple query variations.
    
    Example:
        Input: "How do I get started?"
        Output: ["How do I get started?", "Getting started guide", "Setup instructions", "Quick start"]
    """

    @staticmethod
    def generate_response(query: str, to_expand_to_n: int = 3) -> List[str]:
        """
        Generate multiple related queries from a single query.
        
        Args:
            query: Original query string
            to_expand_to_n: Number of queries to generate
            
        Returns:
            List of expanded queries
        """
        try:
            prompt = f"""Generate {to_expand_to_n} different queries that are semantically similar to the following query.
Each query should be a variation that might retrieve different but relevant documents.

Original query: "{query}"

Return only the queries, one per line, without numbering or bullets.
Separate each query with a newline character."""

            model = ChatOpenAI(
                model=settings.OPENAI_MODEL_ID,
                api_key=settings.OPENAI_API_KEY,
                temperature=0,
            )
            
            response = model.invoke(prompt)
            response_text = response.content.strip()
            
            # Split by newlines and clean
            queries = [q.strip() for q in response_text.split("\n") if q.strip()]
            
            # Always include original query
            if query not in queries:
                queries.insert(0, query)
            
            # Limit to requested number
            queries = queries[:to_expand_to_n]
            
            logger.info("Query expansion completed",
                       original_query=query,
                       expanded_count=len(queries))
            
            return queries
            
        except Exception as e:
            logger.error("Query expansion failed", error=str(e), query=query)
            # Fallback to original query
            return [query]

